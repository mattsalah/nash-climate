import io
import zipfile
import pandas as pd
import numpy as np

# Implied policy abatement from structural breaks in emissions
# (Tebecis & Crespo Cuaresma 2025, "A dataset of structural breaks in greenhouse gas emissions
# for climate policy evaluation", Scientific Data 12:42)
#
# The paper estimates, separately for each gas x IPCC sector x country sample x p-value,
#   log(emissions per capita) ~ log GDP + log GDP^2 + log pop + country FE + year FE
# saturated with country-specific step indicators, kept by general-to-specific search. A break
# is a permanent level shift in log emissions from its year onward, relative to the other
# countries in the sample. Sectors are leaf IPCC categories (not nested), so they add up.
#
# Aggregation, per country and sector, with C_t = sum of the break coefficients up to year t:
#   counterfactual (no breaks)  E_cf = E_t * exp(-C_t)
#   abatement                   A_t  = E_cf - E_t
# summed across sectors and reported in kt, as % of actual emissions, and as mu = A / (E + A),
# the share of counterfactual (BAU) emissions abated, comparable with the MAC curves

input_filename = 'input/structural_breaks/all_structural_breaks.csv'
edgar_zip = 'input/structural_breaks/structural_breaks_code.zip'
output_filename = 'output/data/structural_break_abatement.csv'

GAS_FILES = {
    'co2': 'Data/IEA_EDGAR_CO2_1970_2022.xlsx',  # kt CO2
    'all_ghg': 'Data/EDGAR_AR5_GHG_1970_2022.xlsx',  # kt CO2e (GWP100, AR5)
}
SAMPLE = 'OECD'  # 38 countries; the EU15 sample only covers 15 of them
P_VALUES = [0.05, 0.01, 0.001]
YEARS = [2020, 2022]

# 'all': every break since 1996. 'since_2015': only breaks after 2015, i.e. relative to
# emissions with 2015 policy, the same baseline as the policy intensity counterfactuals
WINDOWS = {'all': 1995, 'since_2015': 2015}

# 'net': negative and positive breaks. 'negative': reductions only, the policy-like breaks
DIRECTIONS = ['net', 'negative']

# The replication code replaces zero emissions with 1e-6 before taking logs, so a sector moving
# to or from ~0 produces huge coefficients (up to +/-20 log points) that would imply absurd
# counterfactuals. Drop breaks where the sector emits less than this in the break year or the
# year before
ZERO_THRESHOLD_KT = 1.0

ISO2_TO_ISO3 = {
    'AT': 'aut', 'AU': 'aus', 'BE': 'bel', 'CA': 'can', 'CH': 'che', 'CL': 'chl', 'CO': 'col',
    'CR': 'cri', 'CZ': 'cze', 'DE': 'deu', 'DK': 'dnk', 'EE': 'est', 'ES': 'esp', 'FI': 'fin',
    'FR': 'fra', 'GB': 'gbr', 'GR': 'grc', 'HU': 'hun', 'IE': 'irl', 'IL': 'isr', 'IS': 'isl',
    'IT': 'ita', 'JP': 'jpn', 'KR': 'kor', 'LT': 'ltu', 'LU': 'lux', 'LV': 'lva', 'MX': 'mex',
    'NL': 'nld', 'NO': 'nor', 'NZ': 'nzl', 'PL': 'pol', 'PT': 'prt', 'SE': 'swe', 'SI': 'svn',
    'SK': 'svk', 'TR': 'tur', 'US': 'usa',
}

###### DATA #######

breaks = pd.read_csv(input_filename, encoding='utf-8-sig')
breaks = breaks[breaks['sample'] == SAMPLE].rename(columns={'IPCC code': 'sector', 'target p-value': 'p_value_target'})
breaks['n'] = breaks['country code'].map(ISO2_TO_ISO3)
assert breaks['n'].notna().all(), "unmapped country code"


def load_emissions(path):
    # EDGAR sector emissions by country, from the replication package (kt per year)
    with zipfile.ZipFile(edgar_zip) as z:
        df = pd.read_excel(io.BytesIO(z.read(path)), sheet_name='IPCC 2006', skiprows=9)
    df['n'] = df['Country_code_A3'].str.lower()
    df = df[df['n'].isin(ISO2_TO_ISO3.values())]
    year_cols = [c for c in df.columns if str(c).startswith('Y_')]
    df = df.groupby(['n', 'ipcc_code_2006_for_standard_report'])[year_cols].sum()
    df.columns = [int(c[2:]) for c in year_cols]
    df.index.names = ['n', 'sector']
    return df

###### ABATEMENT #######

def is_zero_artefact(row, emissions):
    if (row['n'], row['sector']) not in emissions.index:
        return True
    series = emissions.loc[(row['n'], row['sector'])]
    return min(series.get(row['year'] - 1, 0), series.get(row['year'], 0)) < ZERO_THRESHOLD_KT


rows = []
for gas, path in GAS_FILES.items():
    emissions = load_emissions(path)
    gas_breaks = breaks[breaks['gas'] == gas].copy()
    gas_breaks['zero_artefact'] = gas_breaks.apply(is_zero_artefact, axis=1, emissions=emissions)

    for p in P_VALUES:
        p_breaks = gas_breaks[np.isclose(gas_breaks['p_value_target'], p)]
        usable = p_breaks[~p_breaks['zero_artefact']]
        print(f"{gas} p={p}: {len(p_breaks)} breaks, dropped {p_breaks['zero_artefact'].sum()} zero artefacts")

        for year in YEARS:
            actual = emissions[year].groupby('n').sum()
            for window, after in WINDOWS.items():
                for direction in DIRECTIONS:
                    b = usable[(usable['year'] > after) & (usable['year'] <= year)]
                    if direction == 'negative':
                        b = b[b['coef'] < 0]
                    # cumulative log shift per country-sector, then abatement against that
                    # sector's actual emissions
                    cum = b.groupby(['n', 'sector'])['coef'].sum()
                    sector_actual = emissions[year].reindex(cum.index).fillna(0)
                    abated = (sector_actual * (np.exp(-cum) - 1)).groupby('n').sum()
                    n_breaks = b.groupby('n').size()

                    for n in ISO2_TO_ISO3.values():
                        a = abated.get(n, 0.0)
                        e = actual.get(n, np.nan)
                        rows.append({
                            'gas': gas, 'p_value': p, 'year': year, 'window': window,
                            'direction': direction, 'n': n,
                            'n_breaks': int(n_breaks.get(n, 0)),
                            'actual_kt': e, 'abated_kt': a,
                            'abated_pct_of_actual': 100 * a / e,
                            'mu_pct': 100 * a / (e + a),
                        })

###### SAVE ################

out = pd.DataFrame(rows)
out.to_csv(output_filename, index=False)

# Totals across all 38 countries
totals = out.groupby(['gas', 'p_value', 'year', 'window', 'direction'])[['n_breaks', 'actual_kt', 'abated_kt']].sum()
totals['abated_pct_of_actual'] = 100 * totals['abated_kt'] / totals['actual_kt']
totals['mu_pct'] = 100 * totals['abated_kt'] / (totals['actual_kt'] + totals['abated_kt'])
pd.set_option('display.width', 200)
print("\nTotal across the OECD sample")
print(totals.to_string(float_format='{:,.1f}'.format))
print(f"\nSaved to {output_filename}")
