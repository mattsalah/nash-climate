import os
import pandas as pd
import numpy as np
import statsmodels.api as sm
from scipy import stats

# Do countries with higher own climate damages run more green subsidy programs? Each World Bank
# Green Subsidies Database outcome from generate_green_subsidies.py is regressed, one at a time, on
#   scc_mid_spec{1-4}   own country SCC (Ricke et al.), $/tCO2
#   pop_share           population as a % of world population
# with robust (HC1) standard errors. Alongside the slope, reports the Spearman rank correlation,
# since counts are dominated by the US and China

output_filename = 'output/regressions/green_subsidies_regressions.csv'

OUTCOMES = {
    'gs_n_all': 'Green subsidy programs, all (2022)',
    'gs_n_central': 'Green subsidy programs, central government (2022)',
    'gs_n_rnd': 'Green subsidy programs, R&D/innovation (2022)',
    'gs_n_all_per_gdp': 'Green subsidy programs per $1tn GDP (2022)',
    'gs_n_rnd_per_gdp': 'R&D/innovation green subsidy programs per $1tn GDP (2022)',
}
X_COLS = [f'scc_mid_spec{spec}' for spec in range(1, 5)] + ['pop_share']
SAMPLES = {
    'full': [],
    'no_us_chn_ind': ['usa', 'chn', 'ind'],
}

###### DATA #######

df = pd.read_csv('output/data/mitigation_cscc_v_cntfc_2020.csv')
world_pop = df.loc[df['n'] == 'wld', 'pop'].iloc[0]
df['pop_share'] = 100 * df['pop'] / world_pop
df = df[['n'] + X_COLS]

# Drop the EU-level programs row, only individual countries
gs_df = pd.read_csv('output/data/green_subsidies.csv')
gs_df = gs_df[gs_df['n'] != 'eu']
df = gs_df.merge(df, on='n', how='left')

###### REGRESSIONS #######

rows = []
for y_col, y_label in OUTCOMES.items():
    for x_col in X_COLS:
        for sample, excluded in SAMPLES.items():
            data = df[~df['n'].isin(excluded)][[y_col, x_col]].dropna()
            model = sm.OLS(data[y_col], sm.add_constant(data[x_col])).fit(cov_type='HC1')
            rho, rho_p = stats.spearmanr(data[x_col], data[y_col])
            rows.append({
                'y_column': y_col,
                'y_label': y_label,
                'x_column': x_col,
                'sample': sample,
                'n': int(model.nobs),
                'slope': model.params[x_col],
                'robust_se': model.bse[x_col],
                'p_value': model.pvalues[x_col],
                'intercept': model.params['const'],
                'r_squared': model.rsquared,
                'spearman_rho': rho,
                'spearman_p': rho_p,
            })

###### SAVE ################

report = pd.DataFrame(rows)
os.makedirs(os.path.dirname(output_filename), exist_ok=True)
report.to_csv(output_filename, index=False)

pd.set_option('display.width', 250)
print(report.drop(columns='y_label').to_string(index=False, float_format='{:.3g}'.format))
print(f"\nSaved CSV to {output_filename}")
