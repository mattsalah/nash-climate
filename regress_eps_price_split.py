import os
import pandas as pd
import statsmodels.api as sm

# EPS climate stringency mixes explicit carbon prices with non-price support, which may respond
# to size or damages in opposite directions. Each part (generate_eps_stringency.py), and each
# non-price instrument, is regressed on one size or damages measure at a time,
#   scc_mid_spec{1-4}   own country SCC (Ricke et al.), $/tCO2
#   pop_share           population as a % of world population (2020)
# under three control sets: none, GDP per capita, and the kitchen sink controls
# (regress_kitchen_sink.py). Outcomes:
#   eps_climate        all climate instruments
#   eps_carbon_price   CO2 tax and CO2 trading scheme
#   eps_nonprice       renewable trading schemes, low-carbon R&D, solar and wind support
#   TRADESCH_RENEW     renewable trading schemes (certificates / portfolio standards)
#   RD_SUB             low-carbon public R&D, scored by its size relative to GDP
#   eps_fit            solar and wind support (mean of FIT_SOLAR, FIT_WIND)
# All scored 0-6. Robust (HC1) standard errors. Outcome and regressors are standardised within
# each estimation sample, so coefficients are SDs of outcome per 1 SD of the regressor

output_filename = 'output/regressions/eps_price_split_regressions.csv'

OUTCOMES = ['eps_climate', 'eps_carbon_price', 'eps_nonprice', 'TRADESCH_RENEW', 'RD_SUB', 'eps_fit']
X_COLS = [f'scc_mid_spec{spec}' for spec in range(1, 5)] + ['pop_share']
KITCHEN_SINK = ['vdem_corruption', 'vdem_democracy', 'gini', 'ff_assets_1995', 'land_area', 'gdppc']
CONTROLS = {'none': [], 'gdppc': ['gdppc'], 'kitchen_sink': KITCHEN_SINK}
SAMPLES = {
    'full': [],
    'no_us_chn_ind': ['usa', 'chn', 'ind'],
}

###### DATA #######

df = pd.read_csv('output/data/mitigation_cscc_v_cntfc_2020.csv')
world_pop = df.loc[df['n'] == 'wld', 'pop'].iloc[0]
df['pop_share'] = 100 * df['pop'] / world_pop
df = df[['n'] + X_COLS]

controls = pd.read_csv('output/data/kitchen_sink_inputs.csv')[['n'] + KITCHEN_SINK]
df = df.merge(controls, on='n', how='left')

eps_df = pd.read_csv('output/data/eps_stringency_2020.csv')
eps_df['eps_fit'] = eps_df[['FIT_SOLAR', 'FIT_WIND']].mean(axis=1)
df = eps_df[['n'] + OUTCOMES].merge(df, on='n', how='left')

###### REGRESSIONS #######

rows = []
for y_col in OUTCOMES:
    for x_col in X_COLS:
        for controls_name, control_cols in CONTROLS.items():
            for sample, excluded in SAMPLES.items():
                data = df[~df['n'].isin(excluded)][['n', y_col, x_col] + control_cols].dropna()
                standardise = lambda x: (x - x.mean()) / x.std()
                X = standardise(data[[x_col] + control_cols])
                model = sm.OLS(standardise(data[y_col]), sm.add_constant(X)).fit(cov_type='HC1')
                rows.append({
                    'y_column': y_col,
                    'x_column': x_col,
                    'controls': controls_name,
                    'sample': sample,
                    'n': int(model.nobs),
                    'std_coef': model.params[x_col],
                    'robust_se': model.bse[x_col],
                    'p_value': model.pvalues[x_col],
                    'r_squared': model.rsquared,
                })

###### SAVE ################

report = pd.DataFrame(rows)
os.makedirs(os.path.dirname(output_filename), exist_ok=True)
report.to_csv(output_filename, index=False)

pd.set_option('display.width', 250)
pd.set_option('display.max_rows', 500)
print(report.to_string(index=False, float_format='{:.3g}'.format))
print(f"\nSaved CSV to {output_filename}")
