import os
import pandas as pd
import statsmodels.api as sm

# Simple cross-country check, no climate modelling: does country size (population) predict
# observed climate policy? Each outcome is regressed on population as a % of world population,
# with robust (HC1) standard errors

output_filename = 'output/regressions/population_regressions.csv'

OUTCOMES = {
    'pol_dens_cum': 'Policy density (cumulative policy count, 2020)',
    'strng_wght_ind': 'Policy stringency (weighted index, 2020)',
    'carbon_price_dolphin_ghg': 'Dolphin effective carbon price, all GHG ($/tCO2e, 2020)',
}

SAMPLES = {
    'full': [],
    'no_us_chn_ind': ['usa', 'chn', 'ind'],
}

###### DATA #######

# Merged country dataset from generate_cscc_vs_cntfc.py: population is WB WDI, policy density
# and stringency are from the policy intensity replication data, carbon price is Dolphin & Merkle
df = pd.read_csv('output/data/mitigation_cscc_v_cntfc_2020.csv')

world_pop = df.loc[df['n'] == 'wld', 'pop'].iloc[0]
df['pop_share'] = 100 * df['pop'] / world_pop

# drop the EU and World aggregate rows, only individual countries
df = df[~df['n'].isin(['eu', 'wld'])]

###### REGRESSIONS #######

rows = []
x_col = 'pop_share'
for y_col, y_label in OUTCOMES.items():
    for sample, excluded in SAMPLES.items():
        data = df[~df['n'].isin(excluded)][[y_col, x_col]].dropna()
        model = sm.OLS(data[y_col], sm.add_constant(data[x_col])).fit(cov_type='HC1')
        rows.append({
            'outcome': y_col,
            'outcome_label': y_label,
            'sample': sample,
            'x_column': x_col,
            'n': int(model.nobs),
            'slope': model.params[x_col],
            'robust_se': model.bse[x_col],
            'p_value': model.pvalues[x_col],
            'intercept': model.params['const'],
            'r_squared': model.rsquared,
        })

###### SAVE ################

report = pd.DataFrame(rows)
os.makedirs(os.path.dirname(output_filename), exist_ok=True)
report.to_csv(output_filename, index=False)

print(report.drop(columns='outcome_label').to_string(index=False, float_format='{:.4g}'.format))
print(f"\nSaved CSV to {output_filename}")
