import os
import json
import pandas as pd
import numpy as np
from scipy.optimize import brentq
from scipy import stats

# Reverse of the optimal-abatement approach: instead of asking how much a country should abate
# at its SCC, take the abatement its policies actually delivered and ask what carbon price would
# justify it. On the MAC curve the implied price is just MAC(mu) = a*mu + d*mu^4
#
# Compares the implied price against
#   own CSCC     (Ricke et al. 2018, the non-cooperative / Nash benchmark)
#   global SCC   (the cooperative benchmark)
#   Dolphin & Merkle effective carbon price actually in place in 2020
# and correlates it with population and own CSCC
#
# Run for 2020 and, as a sensitivity check, 2022 (the last year of the policy counterfactuals).
# The MAC coefficients are identical across the 2015/2020/2025 periods so only abatement changes

YEARS = [2020, 2022]
CNTFCS = ['policy_den_cntfc', 'policy_strng_cntfc']
CNTFC_SOURCE = {  # counterfactual columns in country_year_counterfactual_CO2.csv
    'policy_den_cntfc': '',
    'policy_strng_cntfc': '_strng',
}
EU_CODE = 'eu'
EU27 = ['aut', 'bel', 'bgr', 'hrv', 'cyp', 'cze', 'dnk', 'est', 'fin',
        'fra', 'deu', 'grc', 'hun', 'irl', 'ita', 'lva', 'ltu', 'lux',
        'mlt', 'nld', 'pol', 'prt', 'rou', 'svk', 'svn', 'esp', 'swe']

###### TIME-INVARIANT INPUTS #######

# own and global SCC (Ricke et al.) and the 2020 Dolphin carbon price
scc_cols = [f'scc_mid_spec{s}' for s in range(1, 5)] + [f'global_scc_mid_spec{s}' for s in range(1, 5)]
base_df = pd.read_csv('output/data/mitigation_cscc_v_cntfc_2020.csv')
base_df = base_df[base_df['n'] != EU_CODE][['n'] + scc_cols + ['carbon_price_dolphin_ghg']]

# MAC coefficients, 2020 period (t = 2)
rice_to_iso3 = json.load(open('input/rice_to_iso3.json'))
macc_df = pd.read_csv('output/data/macc_ed_early.csv')
macc_df = macc_df[(macc_df['t'] == 2) & (macc_df['sector'] == 'Total_CO2') & macc_df['Dim2'].isin(['a', 'd'])]
macc_df = macc_df.pivot_table(index='n', columns='Dim2', values='Val').reset_index()
macc_df.columns = ['n', 'macc_a', 'macc_d']
macc_df['n'] = macc_df['n'].str.strip().str.lower().map(lambda x: rice_to_iso3.get(x, x))

policy_mapping = json.load(open('input/policy_int_to_iso3.json'))
policy_df = pd.read_csv('output/data/country_year_counterfactual_CO2.csv')
policy_df['n'] = policy_df['id'].map(policy_mapping)

wb_df = pd.read_csv('input/wb_controls/pop_gdp_2015_2025.csv')
wb_df = wb_df[['country', 'year', 'WB_WDI_SP_POP_TOTL']].rename(columns={'WB_WDI_SP_POP_TOTL': 'pop'})
wb_df['n'] = wb_df['country'].str.lower()

###### IMPLIED CARBON PRICE #######

def mac(mu, a, d):
    return a * mu + d * mu ** 4


def mu_at_price(price, a, d):
    # MAC is increasing in mu, so invert it on [0, 1] (full abatement above MAC(1))
    if price <= 0:
        return 0.0
    if price >= mac(1, a, d):
        return 1.0
    return brentq(lambda mu: mac(mu, a, d) - price, 0, 1)


def eu_implied_price(members, avoided_col, cntfc_col):
    # The EU's implied price is the common price at which its members' abatement, each read off
    # its own MAC curve, adds up to the abatement the EU actually achieved
    bau = members[cntfc_col]
    eu_mu = members[avoided_col].sum() / bau.sum()
    total = lambda p: sum(w * mu_at_price(p, a, d) for w, a, d in
                          zip(bau / bau.sum(), members['macc_a'], members['macc_d'])) - eu_mu
    return brentq(total, 0, (members['macc_a'] + members['macc_d']).max()) if eu_mu > 0 else 0.0


def build(year):
    df = policy_df[(policy_df['year'] == year) & policy_df['n'].notna()].copy()
    df = df.merge(macc_df, on='n', how='left')
    df = df[df['macc_a'] > 0]

    for cntfc, src in CNTFC_SOURCE.items():
        # The counterfactuals are avoided emissions as a % of ACTUAL emissions, but the MAC curve
        # is in terms of mu = abatement as a share of BAU (counterfactual) emissions:
        #   BAU = actual + avoided  =>  mu = pct / (100 + pct)
        for suffix, pct_col in [('', f'pct_diff_2015{src}'),
                                ('_low', f'ci_lower_pct_2015{src}'),
                                ('_high', f'ci_upper_pct_2015{src}')]:
            df[f'{cntfc}{suffix}'] = df[pct_col]
            mu = df[pct_col] / (100 + df[pct_col])
            df[f'implied_price_{cntfc}{suffix}'] = mac(mu, df['macc_a'], df['macc_d'])

    # EU pseudo-row (point estimate only)
    members = df[df['n'].isin(EU27)]
    eu_row = {'n': EU_CODE}
    for cntfc, src in CNTFC_SOURCE.items():
        m = members.dropna(subset=[f'avoided_CO2_2015{src}'])
        eu_row[cntfc] = 100 * m[f'avoided_CO2_2015{src}'].sum() / m['CO2_mt'].sum()
        eu_row[f'implied_price_{cntfc}'] = eu_implied_price(m, f'avoided_CO2_2015{src}', f'co2_cntfc_2015{src}')
    print(f"{year} EU aggregate: {len(members)} members, missing {sorted(set(EU27) - set(members['n']))}")
    df = pd.concat([df, pd.DataFrame([eu_row])], ignore_index=True)

    df = df.merge(base_df, on='n', how='left')
    df = df.merge(wb_df[wb_df['year'] == year][['n', 'pop']], on='n', how='left')
    df.loc[df['n'] == EU_CODE, 'pop'] = df.loc[df['n'].isin(EU27), 'pop'].sum()
    df.loc[df['n'] == EU_CODE, [c for c in scc_cols if c.startswith('scc')]] = \
        df.loc[df['n'].isin(EU27), [c for c in scc_cols if c.startswith('scc')]].sum().values
    df.loc[df['n'] == EU_CODE, [c for c in scc_cols if c.startswith('global')]] = \
        df[[c for c in scc_cols if c.startswith('global')]].dropna().iloc[0].values
    # % of world population, a rescaling of raw population so correlations are unchanged
    world_pop = wb_df.loc[(wb_df['n'] == 'wld') & (wb_df['year'] == year), 'pop'].iloc[0]
    df['pop_share'] = 100 * df['pop'] / world_pop

    ###### COMPARE TO BENCHMARKS #######

    for cntfc in CNTFCS:
        price = df[f'implied_price_{cntfc}']
        df[f'implied_price_{cntfc}_vs_dolphin'] = price - df['carbon_price_dolphin_ghg']
        for spec in range(1, 5):
            own, glob = df[f'scc_mid_spec{spec}'], df[f'global_scc_mid_spec{spec}']
            # below Nash: less action than even self-interest justifies
            # nash_to_coop: more than self-interest, less than the cooperative optimum
            # above coop: more than even the global SCC justifies
            df[f'implied_price_{cntfc}_regime_spec{spec}'] = np.select(
                [price.isna(), price < own, price <= glob],
                [None, 'below_nash', 'nash_to_coop'],
                default='above_coop',
            )

    keep = ['n', 'pop', 'pop_share', 'macc_a', 'macc_d', 'carbon_price_dolphin_ghg'] + scc_cols + \
           [f'{c}{s}' for c in CNTFCS for s in ['', '_low', '_high']] + \
           [c for c in df.columns if c.startswith('implied_price_')]
    return df[keep].sort_values('n')

###### CORRELATIONS #######

SAMPLES = {
    'full': [],
    'no_us_chn_ind': ['usa', 'chn', 'ind'],
}
X_COLS = ['pop_share'] + [f'scc_mid_spec{s}' for s in range(1, 5)]


def correlate(df, year):
    rows = []
    countries = df[df['n'] != EU_CODE]
    for cntfc in CNTFCS:
        y_col = f'implied_price_{cntfc}'
        for sample, excluded in SAMPLES.items():
            for x_col in X_COLS:
                data = countries[~countries['n'].isin(excluded)][[x_col, y_col]].dropna()
                pearson = stats.pearsonr(data[x_col], data[y_col])
                spearman = stats.spearmanr(data[x_col], data[y_col])
                rows.append({
                    'year': year, 'outcome': y_col, 'sample': sample, 'x_column': x_col, 'n': len(data),
                    'pearson_r': pearson[0], 'pearson_p': pearson[1],
                    'spearman_rho': spearman[0], 'spearman_p': spearman[1],
                })
    return rows

###### RUN & SAVE ################

corr_rows = []
for year in YEARS:
    df = build(year)
    df.to_csv(f'output/data/implied_carbon_price_{year}.csv', index=False)
    corr_rows += correlate(df, year)

    print(f"\n{year} countries by regime (excludes the EU pseudo-row)")
    countries = df[df['n'] != EU_CODE]
    for cntfc in CNTFCS:
        for spec in range(1, 5):
            counts = countries[f'implied_price_{cntfc}_regime_spec{spec}'].value_counts()
            print(f"  {cntfc} spec {spec}: " + ", ".join(f"{k} {counts.get(k, 0)}" for k in ['below_nash', 'nash_to_coop', 'above_coop']))

corr = pd.DataFrame(corr_rows)
os.makedirs('output/regressions', exist_ok=True)
corr.to_csv('output/regressions/implied_price_correlations.csv', index=False)
print()
print(corr.to_string(index=False, float_format='{:.3g}'.format))
print("\nSaved output/data/implied_carbon_price_{year}.csv and output/regressions/implied_price_correlations.csv")
