import os
import pandas as pd
import numpy as np
import statsmodels.api as sm
from scipy import stats

# Is carbon pricing higher where the own country SCC (Ricke et al.) is higher, as a Nash model
# predicts? Each carbon pricing measure is regressed on own CSCC for every spec, overall, within
# Europe and outside Europe, with and without a GDP per capita control (HC1 SEs)
#
# Alongside the slope, reports the (partial) correlation: Pearson on the residuals after
# removing the controls from both variables, and the same on ranks (a partial Spearman)

output_filename = 'output/regressions/carbon_price_cscc_regressions.csv'

PRICES = {
    'carbon_price_effective': 'OECD effective carbon rate (EUR/tCO2e, 2021)',
    'carbon_price_dolphin_ghg': 'Dolphin & Merkle effective carbon price, all GHG ($/tCO2e, 2020)',
    'eps_carbon_price': 'OECD EPS carbon pricing score (CO2 tax + CO2 ETS, 0-6, 2020)',
}
CONTROLS = [[], ['gdppc']]

EU27 = ['aut', 'bel', 'bgr', 'hrv', 'cyp', 'cze', 'dnk', 'est', 'fin',
        'fra', 'deu', 'grc', 'hun', 'irl', 'ita', 'lva', 'ltu', 'lux',
        'mlt', 'nld', 'pol', 'prt', 'rou', 'svk', 'svn', 'esp', 'swe']
EUROPE = EU27 + ['gbr', 'che', 'nor', 'isl']
REGIONS = {
    'all': lambda n: np.ones(len(n), dtype=bool),
    'europe': lambda n: n.isin(EUROPE),
    'non_europe': lambda n: ~n.isin(EUROPE),
}

###### DATA #######

df = pd.read_csv('output/data/mitigation_cscc_v_cntfc_2020.csv')
df = df[~df['n'].isin(['eu', 'wld'])]
eps_df = pd.read_csv('output/data/eps_stringency_2020.csv')[['n', 'eps_carbon_price']]
df = df.merge(eps_df, on='n', how='left')

###### REGRESSIONS #######

def partial_corr(data, x_col, y_col, controls):
    if not controls:
        return data[x_col].corr(data[y_col])
    Z = sm.add_constant(data[controls])
    x_resid = sm.OLS(data[x_col], Z).fit().resid
    y_resid = sm.OLS(data[y_col], Z).fit().resid
    return x_resid.corr(y_resid)


def corr_p_value(r, n, n_controls):
    # t-test for a (partial) correlation, losing one degree of freedom per control
    dof = n - 2 - n_controls
    return 2 * stats.t.sf(abs(r) * np.sqrt(dof / (1 - r ** 2)), dof)


rows = []
for y_col, y_label in PRICES.items():
    for spec in range(1, 5):
        x_col = f'scc_mid_spec{spec}'
        for region, in_region in REGIONS.items():
            for controls in CONTROLS:
                data = df[in_region(df['n'])][[x_col, y_col] + controls].dropna()
                model = sm.OLS(data[y_col], sm.add_constant(data[[x_col] + controls])).fit(cov_type='HC1')
                r = partial_corr(data, x_col, y_col, controls)
                rho = partial_corr(data.rank(), x_col, y_col, controls)
                rows.append({
                    'y_column': y_col,
                    'y_label': y_label,
                    'spec': spec,
                    'region': region,
                    'controls': '+'.join(controls) or 'none',
                    'n': int(model.nobs),
                    'slope': model.params[x_col],
                    'robust_se': model.bse[x_col],
                    'p_value': model.pvalues[x_col],
                    'r_squared': model.rsquared,
                    'partial_r': r,
                    'partial_r_p': corr_p_value(r, len(data), len(controls)),
                    'partial_rho': rho,
                    'partial_rho_p': corr_p_value(rho, len(data), len(controls)),
                })

###### SAVE ################

report = pd.DataFrame(rows)
os.makedirs(os.path.dirname(output_filename), exist_ok=True)
report.to_csv(output_filename, index=False)

pd.set_option('display.width', 250)
print(report.to_string(index=False, float_format='{:.3g}'.format))
print(f"\nSaved CSV to {output_filename}")
