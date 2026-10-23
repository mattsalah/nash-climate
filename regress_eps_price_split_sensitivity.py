import os
import numpy as np
import pandas as pd
import statsmodels.api as sm

# Sensitivity checks for the EPS carbon price vs non-price split (regress_eps_price_split.py).
# Each outcome is regressed on one damages or size measure at a time, standardised, HC1 SEs:
#   eps_2015_2020   EPS scores averaged over 2015-2020 or 2010-2020 instead of 2020 (the EPS ends
#   eps_2010_2020   in 2020); own CSCC specs 1-4 and population share
#   extra_controls  the kitchen sink controls plus, one at a time and all together,
#                     eu_member      EU member in 2020 (the UK left in January 2020)
#                     log_co2_pc     log territorial CO2 per capita, 2020 (OWID)
#                     macc_a         RICE50x MAC curve linear coefficient, 2020 (abatement cost)
#                   own CSCC specs 1-4 and population share
#   chiani          Chiani et al. (2026) national SCC for 2020, RICE50+ and WITCH at 2%, 2.5%
#                   and 3% discounting (6 measures)
#   ricke_all       every Ricke et al. (2018) configuration (damage function x damage and
#                   climate uncertainty x SSP x RCP x discounting, 486 in all), median CSCC
# The chiani and ricke_all tests use the 2020 EPS with no controls, GDP per capita, or the
# kitchen sink controls. All tests run on the full sample and without the US, China and India

output_filename = 'output/regressions/eps_price_split_sensitivity.csv'

OUTCOMES = ['eps_climate', 'eps_carbon_price', 'eps_nonprice']
SPECS = [f'scc_mid_spec{spec}' for spec in range(1, 5)] + ['pop_share']
KITCHEN_SINK = ['vdem_corruption', 'vdem_democracy', 'gini', 'ff_assets_1995', 'land_area', 'gdppc']
EXTRA = ['eu_member', 'log_co2_pc', 'macc_a']
CONTROLS = {'none': [], 'gdppc': ['gdppc'], 'kitchen_sink': KITCHEN_SINK}
EXTRA_CONTROLS = {f'kitchen_sink+{c}': KITCHEN_SINK + [c] for c in EXTRA}
EXTRA_CONTROLS['kitchen_sink+all_extra'] = KITCHEN_SINK + EXTRA
SAMPLES = {
    'full': [],
    'no_us_chn_ind': ['usa', 'chn', 'ind'],
}
EU_2020 = ['aut', 'bel', 'bgr', 'hrv', 'cyp', 'cze', 'dnk', 'est', 'fin', 'fra', 'deu', 'grc', 'hun', 'irl',
           'ita', 'lva', 'ltu', 'lux', 'mlt', 'nld', 'pol', 'prt', 'rou', 'svk', 'svn', 'esp', 'swe']
CHIANI_COLUMNS = ['RICE50+_2', 'WITCH_2', 'RICE50+_2.5', 'WITCH_2.5', 'RICE50+_3', 'WITCH_3']
RICKE_KEYS = ['run', 'dmgfuncpar', 'climate', 'SSP', 'RCP', 'discounting']

###### DATA #######

df = pd.read_csv('output/data/mitigation_cscc_v_cntfc_2020.csv')
world_pop = df.loc[df['n'] == 'wld', 'pop'].iloc[0]
df['pop_share'] = 100 * df['pop'] / world_pop
# a zero MAC coefficient means no Enerdata coverage
df['macc_a'] = df['macc_a'].where(df['macc_a'] > 0)
df = df[['n', 'pop', 'macc_a'] + SPECS]

controls = pd.read_csv('output/data/kitchen_sink_inputs.csv')[['n'] + KITCHEN_SINK]
df = df.merge(controls, on='n', how='left')

df['eu_member'] = df['n'].isin(EU_2020).astype(int)

co2 = pd.read_csv('input/annual-co2-emissions/annual-co2-emissions.csv')
co2 = co2[(co2['Year'] == 2020) & co2['Code'].notna()]
co2 = co2.set_index(co2['Code'].str.lower())['Annual CO₂ emissions']
df['log_co2_pc'] = np.log(df['n'].map(co2) / df['pop'])

# Table C.1: three header rows, then RICE50+ / WITCH pairs at 2%, 2.5% and 3%
chiani = pd.read_csv('input/country_scc/chiani_et_al_2026_national.csv', skiprows=4, header=None,
                     names=['year', 'n'] + CHIANI_COLUMNS)
chiani = chiani[chiani['year'] == 2020].drop(columns='year')
chiani['n'] = chiani['n'].str.lower()
chiani = chiani.rename(columns={c: f'chiani_{c}' for c in CHIANI_COLUMNS})
df = df.merge(chiani, on='n', how='left')

ricke = pd.read_csv('input/country_scc/41558_2018_282_MOESM2_ESM.csv')
ricke['discounting'] = np.where(ricke['dr'].notna(), 'dr' + ricke['dr'].astype(str).str.replace('.0', '', regex=False),
                                'prtp' + ricke['prtp'].astype(str).str.replace('.0', '', regex=False) + '_eta' + ricke['eta'].astype(str))
ricke['config'] = ricke[RICKE_KEYS].astype(str).agg('|'.join, axis=1)
ricke_configs = ricke[['config'] + RICKE_KEYS].drop_duplicates().set_index('config')
ricke_wide = ricke.pivot_table(index=ricke['ISO3'].str.lower(), columns='config', values='50%')
ricke_wide.columns = [f'ricke:{c}' for c in ricke_wide.columns]
df = df.merge(ricke_wide, left_on='n', right_index=True, how='left')

eps_2020 = pd.read_csv('output/data/eps_stringency_2020.csv')[['n'] + OUTCOMES]
data_2020 = eps_2020.merge(df, on='n', how='left')
data_mean = {period: pd.read_csv(f'output/data/eps_stringency_{period}_mean.csv')[['n'] + OUTCOMES].merge(df, on='n', how='left')
             for period in ['2015_2020', '2010_2020']}

###### REGRESSIONS #######

def fit(data, y_col, x_col, control_cols, excluded):
    d = data[~data['n'].isin(excluded)][[y_col, x_col] + control_cols].dropna()
    standardise = lambda x: (x - x.mean()) / x.std()
    X = sm.add_constant(standardise(d[[x_col] + control_cols]))
    model = sm.OLS(standardise(d[y_col]), X).fit(cov_type='HC1')
    return {'n': int(model.nobs), 'std_coef': model.params[x_col], 'robust_se': model.bse[x_col],
            'p_value': model.pvalues[x_col]}

TESTS = [
    # (test, data, size measures, control sets)
    ('eps_2015_2020', data_mean['2015_2020'], SPECS, CONTROLS),
    ('eps_2010_2020', data_mean['2010_2020'], SPECS, CONTROLS),
    ('extra_controls', data_2020, SPECS, EXTRA_CONTROLS),
    ('chiani', data_2020, [f'chiani_{c}' for c in CHIANI_COLUMNS], CONTROLS),
    ('ricke_all', data_2020, list(ricke_wide.columns), CONTROLS),
]

rows = []
for test, data, x_cols, control_sets in TESTS:
    for x_col in x_cols:
        for controls_name, control_cols in control_sets.items():
            for sample, excluded in SAMPLES.items():
                for y_col in OUTCOMES:
                    rows.append({'test': test, 'x_column': x_col, 'controls': controls_name, 'sample': sample,
                                 'y_column': y_col, **fit(data, y_col, x_col, control_cols, excluded)})

###### SAVE ################

report = pd.DataFrame(rows)
config = report['x_column'].str.removeprefix('ricke:')
report = report.join(ricke_configs, on=config)
os.makedirs(os.path.dirname(output_filename), exist_ok=True)
report.to_csv(output_filename, index=False)

# summary: share of regressions with the main finding's sign (price < 0, non-price > 0)
pd.set_option('display.width', 250)
pd.set_option('display.max_rows', 500)
split = report[report['y_column'] != 'eps_climate'].copy()
split['expected_sign'] = np.where(split['y_column'] == 'eps_carbon_price', split['std_coef'] < 0, split['std_coef'] > 0)
split['significant'] = split['expected_sign'] & (split['p_value'] < 0.1)
summary = split.groupby(['test', 'sample', 'controls', 'y_column']).agg(
    regressions=('std_coef', 'size'), min_coef=('std_coef', 'min'), median_coef=('std_coef', 'median'),
    max_coef=('std_coef', 'max'), share_expected_sign=('expected_sign', 'mean'), share_significant=('significant', 'mean'))
print(summary.to_string(float_format='{:.2f}'.format))
print(f"\nSaved CSV to {output_filename}")
