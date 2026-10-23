import os
import glob
import pandas as pd
import statsmodels.api as sm

# Kitchen sink: each carbon pricing / climate policy outcome is regressed jointly on one size measure,
#   scc_mid_spec2      own country SCC (Ricke et al.), spec 2, $/tCO2 (size 'cscc'), or
#   pop_share          population as a % of world population, 2020 (size 'pop')
# (population is largely a proxy for own CSCC, so the two aren't included together), plus all of
#   vdem_corruption    V-Dem political corruption index (2020, 0-1, higher = more corrupt)
#   vdem_democracy     V-Dem electoral democracy index (2020, 0-1, higher = more democratic)
#   gini               Gini index, latest year 2010-2020
#   ff_assets_1995     oil + natural gas + coal subsoil assets (trillion real 2019 US$, 1995;
#                      CWON WB_CWON_SAOI/SAGA/SACO)
#   land_area          land area (million sq. km, 2020)
#   gdppc              GDP per capita (current US$, 2020)
# (spec 'main'). As a sensitivity check, spec 'interactions' adds (each the product of the
# standardised terms, itself standardised)
#   corruption_x_ff_assets   vdem_corruption x ff_assets_1995
#   gini_x_ff_assets         gini x ff_assets_1995
# Robust (HC1) standard errors. The outcome and all regressors are standardised (mean 0, SD 1)
# within each estimation sample, so coefficients are the SDs of outcome change per 1 SD of the
# regressor (with interactions, main effects are their effects at the mean of the interacted terms)

output_filename = 'output/regressions/kitchen_sink_regressions.csv'
data_filename = 'output/data/kitchen_sink_inputs.csv'

OUTCOMES = {
    'carbon_price_dolphin_ghg': 'Dolphin & Merkle effective carbon price, all GHG ($/tCO2e, 2020)',
    'carbon_price_effective': 'OECD effective carbon rate (EUR/tCO2e, 2021)',
    'eps_climate': 'OECD EPS climate policy stringency (0-6, 2020)',
}
SIZE = {'cscc': 'scc_mid_spec2', 'pop': 'pop_share'}
CONTROLS = ['vdem_corruption', 'vdem_democracy', 'gini', 'ff_assets_1995', 'land_area', 'gdppc']
INTERACTIONS = {
    'corruption_x_ff_assets': ('vdem_corruption', 'ff_assets_1995'),
    'gini_x_ff_assets': ('gini', 'ff_assets_1995'),
}
SPECS = {'main': False, 'interactions': True}
# (excluded countries, positive prices only); most countries have no carbon price, so the
# positive samples drop zero prices for the two carbon price outcomes (EPS is never filtered)
SAMPLES = {
    'full': ([], False),
    'no_us_chn_ind': (['usa', 'chn', 'ind'], False),
    'positive_price': ([], True),
    'positive_price_no_us_chn_ind': (['usa', 'chn', 'ind'], True),
}
PRICES = ['carbon_price_dolphin_ghg', 'carbon_price_effective']

###### DATA #######

df = pd.read_csv('output/data/mitigation_cscc_v_cntfc_2020.csv')
world_pop = df.loc[df['n'] == 'wld', 'pop'].iloc[0]
df['pop_share'] = 100 * df['pop'] / world_pop
df = df[~df['n'].isin(['eu', 'wld'])]
df = df[['n', 'pop_share', 'scc_mid_spec2', 'gdppc', 'carbon_price_dolphin_ghg', 'carbon_price_effective']]

eps_df = pd.read_csv('output/data/eps_stringency_2020.csv')[['n', 'eps_climate']]
df = df.merge(eps_df, on='n', how='left')

for name in ['vdem_corruption', 'vdem_democracy']:
    vdem = pd.read_csv(f'input/kitchen_sink/{name}.csv')
    df = df.merge(vdem[vdem['year'] == 2020][['n', name]], on='n', how='left')

wb = pd.read_csv('input/kitchen_sink/wb_indicators.csv')

def wb_year(indicator, year):
    return wb[(wb['indicator'] == indicator) & (wb['year'] == year)].set_index('n')['value']

gini = wb[(wb['indicator'] == 'SI.POV.GINI') & wb['year'].between(2010, 2020)]
gini = gini.sort_values('year').groupby('n')['value'].last()

# Fossil fuel rents (% of GDP) are kept in the saved inputs but not used as a regressor: they are
# noisy and move with fuel prices, so subsoil assets measure fossil-fuel wealth instead.
# A fuel a country doesn't produce is sometimes missing rather than zero (e.g. Swedish oil rents,
# and subsoil assets generally), so a missing fuel counts as zero when any of the three is present
# Rents from the WDI bulk downloads, assets from the Data360 CWON export (total, real chained 2019 US$)
rents = pd.concat([
    pd.read_csv(glob.glob(f'input/fossil_rents/**/API_{code}_DS2_*.csv', recursive=True)[0], skiprows=4)
    .assign(n=lambda x: x['Country Code'].str.lower()).set_index('n')['1995']
    for code in ['NY.GDP.PETR.RT.ZS', 'NY.GDP.NGAS.RT.ZS', 'NY.GDP.COAL.RT.ZS']
], axis=1)

cwon = pd.read_csv('input/fossil_rents/WB_CWON.csv', usecols=['REF_AREA', 'UNIT_MEASURE', 'COMP_BREAKDOWN_1',
                                                               'COMP_BREAKDOWN_2', 'TIME_PERIOD', 'OBS_VALUE'])
cwon = cwon[(cwon['TIME_PERIOD'] == 1995)
            & cwon['UNIT_MEASURE'].str.startswith('USD_REAL_CHAINED_2019', na=False)
            & cwon['COMP_BREAKDOWN_1'].str.startswith('WB_CWON_TO', na=False)
            & cwon['COMP_BREAKDOWN_2'].str.match(r'WB_CWON_(SAOI|SAGA|SACO):', na=False)]
cwon['n'] = cwon['REF_AREA'].str.split(':').str[0].str.lower()
assets = cwon.pivot_table(index='n', columns='COMP_BREAKDOWN_2', values='OBS_VALUE')

df['gini'] = df['n'].map(gini)
df['ff_rents_1995'] = df['n'].map(rents.sum(axis=1, min_count=1))
df['ff_assets_1995'] = df['n'].map(assets.sum(axis=1, min_count=1) / 1e12)
df['land_area'] = df['n'].map(wb_year('AG.LND.TOTL.K2', 2020) / 1e6)

os.makedirs(os.path.dirname(data_filename), exist_ok=True)
df.to_csv(data_filename, index=False)

###### REGRESSIONS #######

rows = []
for size, size_col in SIZE.items():
    X_COLS = [size_col] + CONTROLS
    for spec, with_interactions in SPECS.items():
        for y_col, y_label in OUTCOMES.items():
            for sample, (excluded, positive_only) in SAMPLES.items():
                if positive_only and y_col not in PRICES:
                    continue
                data = df[~df['n'].isin(excluded)][['n', y_col] + X_COLS].dropna()
                if positive_only:
                    data = data[data[y_col] > 0]
                standardise = lambda x: (x - x.mean()) / x.std()
                X = standardise(data[X_COLS])
                if with_interactions:
                    for name, (a, b) in INTERACTIONS.items():
                        X[name] = standardise(X[a] * X[b])
                y = standardise(data[y_col])
                model = sm.OLS(y, sm.add_constant(X)).fit(cov_type='HC1')
                for x_col in X.columns:
                    rows.append({
                        'size': size,
                        'spec': spec,
                        'y_column': y_col,
                        'y_label': y_label,
                        'sample': sample,
                        'x_column': x_col,
                        'n': int(model.nobs),
                        'std_coef': model.params[x_col],
                        'robust_se': model.bse[x_col],
                        'p_value': model.pvalues[x_col],
                        'x_sd': data[x_col].std() if x_col in data else None,
                        'y_sd': data[y_col].std(),
                        'r_squared': model.rsquared,
                        'countries': ' '.join(sorted(data['n'])),
                    })

###### SAVE ################

report = pd.DataFrame(rows)
os.makedirs(os.path.dirname(output_filename), exist_ok=True)
report.to_csv(output_filename, index=False)

pd.set_option('display.width', 250)
print(report.drop(columns=['y_label', 'countries']).to_string(index=False, float_format='{:.3g}'.format))
print(f"\nSaved CSV to {output_filename}")
