import os
import urllib.request
import numpy as np
import pandas as pd
import rdata

# Abatement from emission breaks attributed to climate policy
# (Stechemesser et al. 2024, "Climate policies that achieved major emission reductions: Global
# evidence from two decades", Science 385:884-892, replication package zenodo.org/records/12773811)
#
# The paper detects country-specific step reductions in sectoral CO2 (buildings, electricity &
# heat, industry, transport; 41 countries in a developed and a developing sample, 2000-2021):
#   log(sector CO2) ~ log GDP + log GDP^2 + log pop + HDD + CDD + EU policy dummies
#                     + country FE + year FE + country step and impulse indicators (GETS, p = 0.01)
# Only negative breaks are kept. Each break is then matched to OECD CAPMF (and IPAC for the US)
# policy adoptions or tightenings in the same country and sector within the break's confidence
# interval ('stat'), or within +/- 2 years ('2y'). A break with no matching policy (e.g. a plant
# closure or recession) is not attributed to policy.
#
# Aggregation, as in generate_structural_break_abatement.py, per country and sector with C_t the
# sum of the break coefficients up to year t:
#   counterfactual E_cf = E_t * exp(-C_t),   abatement A_t = E_cf - E_t
# summed over sectors, reported in kt CO2, as % of actual 4-sector CO2, and as mu = A / (E + A)

input_dir = 'input/stechemesser'
zenodo_url = 'https://zenodo.org/api/records/12773811/files/{}/content'
output_filename = 'output/data/policy_break_abatement.csv'

YEARS = [2020, 2021]  # the emissions data end in 2021
WINDOWS = {'all': 1999, 'since_2015': 2015}  # breaks after this year

# 'none': every negative break, policy-matched or not
# 'stat': a matching policy within the break's statistical confidence interval (the paper's main)
# '2y':   a matching policy within +/- 2 years of the break
MATCHES = ['none', 'stat', '2y']

SECTOR_COLS = {
    'Buildings': 'buildings_co2',
    'Electricity': 'electricity_heat_co2',
    'Industry': 'industry_co2',
    'Transport': 'transport_co2',
}

###### DATA #######

os.makedirs(input_dir, exist_ok=True)
for f in ['Policy_out.RDS', 'break_detection_regression_input.RDS']:
    path = os.path.join(input_dir, f)
    if not os.path.exists(path):
        print(f"Downloading {f}")
        urllib.request.urlretrieve(zenodo_url.format(f), path)

# Policy_out.RDS is a tibble with one row per sample x sector, holding nested tables of breaks
# ('out') and matched policies ('policy_match', 'policy_match_2y'). The 'is' column holds fitted
# model objects that rdata can't convert, so convert the other columns one by one
parsed = rdata.parser.parse_file(os.path.join(input_dir, 'Policy_out.RDS'))


def convert(obj):
    return rdata.conversion.convert(
        rdata.parser.RData(parsed.versions, parsed.extra, obj), default_encoding='utf8')


cols = dict(zip(['country_sample', 'sector', 'out', 'is', 'stat', '2y'], parsed.object.value))
samples, sectors = convert(cols['country_sample']), convert(cols['sector'])
outs, matches = convert(cols['out']), {m: convert(cols[m]) for m in ['stat', '2y']}

frames = []
for i, (sample, sector) in enumerate(zip(samples, sectors)):
    b = outs[i][['country_code', 'time', 'coef', 'sd', 'tci']].copy()
    b['sample'] = 'developed' if sample == 'AC1' else 'developing'
    b['sector'] = sector
    # matched policy rows carry the break's country and coefficient
    for m, tables in matches.items():
        pol = tables[i]
        b[f'n_policies_{m}'] = [((pol['ISO'] == r.country_code) & np.isclose(pol['coeff'], r.coef)).sum()
                                for r in b.itertuples()]
    frames.append(b)
breaks = pd.concat(frames, ignore_index=True)
breaks['n'] = breaks['country_code'].str.lower()
breaks['year'] = breaks['time'].astype(int)
breaks['n_policies_none'] = 1
print(f"{len(breaks)} breaks, {(breaks['n_policies_stat'] > 0).sum()} policy-matched (stat), "
      f"{(breaks['n_policies_2y'] > 0).sum()} (2y)")

panel = rdata.read_rds(os.path.join(input_dir, 'break_detection_regression_input.RDS'), default_encoding='utf8')
panel = panel[['country', 'year'] + list(SECTOR_COLS.values())].copy()
panel['year'] = panel['year'].astype(int)
# country names to ISO3 (all 50 countries in the panel)
iso = {'Argentina': 'arg', 'Australia': 'aus', 'Austria': 'aut', 'Belgium': 'bel', 'Brazil': 'bra',
       'Bulgaria': 'bgr', 'Canada': 'can', 'Chile': 'chl', 'China': 'chn', 'Colombia': 'col',
       'Costa Rica': 'cri', 'Croatia': 'hrv', 'Czech Republic': 'cze', 'Denmark': 'dnk', 'Estonia': 'est',
       'Finland': 'fin', 'France': 'fra', 'Germany': 'deu', 'Greece': 'grc', 'Hungary': 'hun',
       'Iceland': 'isl', 'India': 'ind', 'Indonesia': 'idn', 'Ireland': 'irl', 'Italy': 'ita',
       'Japan': 'jpn', 'Latvia': 'lva', 'Lithuania': 'ltu', 'Luxembourg': 'lux', 'Malta': 'mlt',
       'Mexico': 'mex', 'Netherlands': 'nld', 'New Zealand': 'nzl', 'Norway': 'nor', 'Peru': 'per',
       'Poland': 'pol', 'Portugal': 'prt', 'Romania': 'rou', 'Russia': 'rus', 'Saudi Arabia': 'sau',
       'Slovak Republic': 'svk', 'Slovenia': 'svn', 'South Africa': 'zaf', 'South Korea': 'kor',
       'Spain': 'esp', 'Sweden': 'swe', 'Switzerland': 'che', 'Turkey': 'tur',
       'United Kingdom': 'gbr', 'United States': 'usa'}
panel['n'] = panel['country'].map(iso)
assert panel['n'].notna().all(), "unmapped country"
assert breaks['n'].isin(panel['n']).all(), "break country missing from emissions panel"

# kt CO2 by country x sector x year
emissions = panel.melt(id_vars=['n', 'year'], value_vars=list(SECTOR_COLS.values()), var_name='col')
emissions['sector'] = emissions['col'].map({v: k for k, v in SECTOR_COLS.items()})
emissions = emissions.set_index(['n', 'sector', 'year'])['value']

###### ABATEMENT #######

rows = []
for year in YEARS:
    actual = emissions.xs(year, level='year').groupby('n').sum()
    for window, after in WINDOWS.items():
        for match in MATCHES:
            b = breaks[(breaks[f'n_policies_{match}'] > 0) & (breaks['year'] > after) & (breaks['year'] <= year)]
            cum = b.groupby(['n', 'sector'])['coef'].sum()
            sector_actual = pd.Series([emissions[(n, s, year)] for n, s in cum.index], index=cum.index)
            abated = (sector_actual * (np.exp(-cum) - 1)).groupby('n').sum()
            n_breaks = b.groupby('n').size()
            for n, e in actual.items():
                a = abated.get(n, 0.0)
                rows.append({
                    'year': year, 'window': window, 'match': match, 'n': n,
                    'n_breaks': int(n_breaks.get(n, 0)),
                    'actual_kt': e, 'abated_kt': a,
                    'abated_pct_of_actual': 100 * a / e,
                    'mu_pct': 100 * a / (e + a),
                })

###### SAVE ################

out = pd.DataFrame(rows)
os.makedirs(os.path.dirname(output_filename), exist_ok=True)
out.to_csv(output_filename, index=False)

pd.set_option('display.width', 200)
totals = out.groupby(['year', 'window', 'match'])[['n_breaks', 'actual_kt', 'abated_kt']].sum()
totals['abated_pct_of_actual'] = 100 * totals['abated_kt'] / totals['actual_kt']
totals['mu_pct'] = 100 * totals['abated_kt'] / (totals['actual_kt'] + totals['abated_kt'])
print("\nTotal across the 50 countries")
print(totals.to_string(float_format='{:,.1f}'.format))

top = out[(out['year'] == 2020) & (out['window'] == 'all') & (out['match'] == 'stat') & (out['n_breaks'] > 0)]
print("\nPolicy-matched (stat) abatement by country, 2020")
print(top.sort_values('abated_kt', ascending=False)[['n', 'n_breaks', 'abated_kt', 'mu_pct']]
      .to_string(index=False, float_format='{:,.1f}'.format))
print(f"\nSaved to {output_filename}")
