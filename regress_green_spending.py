import os
import pandas as pd
import numpy as np
import statsmodels.api as sm
from scipy import stats

# Do countries with higher own climate damages spend more on green technology? Each measure from
# generate_green_spending.py (OECD EPS R&D and technology support scores, IEA public energy RD&D,
# IEA Government Energy Spending Tracker), in each cross-section year, is regressed one at a time on
#   scc_mid_spec{1-4}   own country SCC (Ricke et al.), $/tCO2
#   pop_share           population as a % of world population (2020)
# with robust (HC1) standard errors, plus the Spearman rank correlation. Each is also run with a
# GDP per capita control (2020), reporting the partial Spearman correlation (ranks residualised)

output_filename = 'output/regressions/green_spending_regressions.csv'

X_COLS = [f'scc_mid_spec{spec}' for spec in range(1, 5)] + ['pop_share']
CONTROLS = [[], ['gdppc']]
SAMPLES = {
    'full': [],
    'no_us_chn_ind': ['usa', 'chn', 'ind'],
}

###### DATA #######

df = pd.read_csv('output/data/mitigation_cscc_v_cntfc_2020.csv')
world_pop = df.loc[df['n'] == 'wld', 'pop'].iloc[0]
df['pop_share'] = 100 * df['pop'] / world_pop
df = df[['n', 'gdppc'] + X_COLS]

# Drop the EU budget row, only individual countries
spending = pd.read_csv('output/data/green_spending.csv')
spending = spending[spending['n'] != 'eu']
spending = spending.merge(df, on='n', how='left')

###### REGRESSIONS #######

def partial_spearman(data, x_col, y_col, controls):
    # Pearson on ranks after removing the controls' ranks from both, losing one dof per control
    ranks = data.rank()
    if controls:
        Z = sm.add_constant(ranks[controls])
        ranks = pd.DataFrame({c: sm.OLS(ranks[c], Z).fit().resid for c in [x_col, y_col]})
    r = ranks[x_col].corr(ranks[y_col])
    dof = len(data) - 2 - len(controls)
    return r, 2 * stats.t.sf(abs(r) * np.sqrt(dof / (1 - r ** 2)), dof)

rows = []
for (measure, year), group in spending.groupby(['measure', 'year']):
    for x_col in X_COLS:
        for controls in CONTROLS:
            for sample, excluded in SAMPLES.items():
                data = group[~group['n'].isin(excluded)][['value', x_col] + controls].dropna()
                model = sm.OLS(data['value'], sm.add_constant(data[[x_col] + controls])).fit(cov_type='HC1')
                rho, rho_p = partial_spearman(data, x_col, 'value', controls)
                rows.append({
                    'measure': measure,
                    'year': year,
                    'x_column': x_col,
                    'controls': '+'.join(controls) or 'none',
                    'sample': sample,
                    'n': int(model.nobs),
                    'slope': model.params[x_col],
                    'robust_se': model.bse[x_col],
                    'p_value': model.pvalues[x_col],
                    'r_squared': model.rsquared,
                    'spearman_rho': rho,
                    'spearman_p': rho_p,
                })

###### SAVE ################

report = pd.DataFrame(rows)
os.makedirs(os.path.dirname(output_filename), exist_ok=True)
report.to_csv(output_filename, index=False)

pd.set_option('display.width', 250)
pd.set_option('display.max_rows', 1000)
print(report.to_string(index=False, float_format='{:.3g}'.format))
print(f"\nSaved CSV to {output_filename}")
