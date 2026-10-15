import os
import pandas as pd
import statsmodels.api as sm

# Does OECD EPS climate policy stringency (2020) line up with predicted abatement or country size?
# Each EPS spec from generate_eps_stringency.py is regressed, one at a time, on
#   noncoop_optimal_mu_spec2   Nash abatement (%) at own CSCC, spec 2
#   coop_optimal_mu_spec2      cooperative abatement (%) at the global SCC, spec 2
#   pop_share                  population as a % of world population
# with robust (HC1) standard errors

output_filename = 'output/regressions/eps_stringency_regressions.csv'

EPS_SPECS = ['eps', 'eps_no_air', 'eps_climate', 'eps_carbon_price']
X_COLS = ['noncoop_optimal_mu_spec2', 'coop_optimal_mu_spec2', 'pop_share']
SAMPLES = {
    'full': [],
    'no_us_chn_ind': ['usa', 'chn', 'ind'],
}

###### DATA #######

df = pd.read_csv('output/data/mitigation_cscc_v_cntfc_2020.csv')
world_pop = df.loc[df['n'] == 'wld', 'pop'].iloc[0]
df['pop_share'] = 100 * df['pop'] / world_pop
df = df[['n'] + X_COLS]

# EPS covers individual EU members, so no EU aggregate row
eps_df = pd.read_csv('output/data/eps_stringency_2020.csv')[['n'] + EPS_SPECS]
df = eps_df.merge(df, on='n', how='left')
missing = df.loc[df[X_COLS].isna().any(axis=1), 'n'].tolist()
print(f"{len(df)} EPS countries, missing a regressor: {missing}")

###### REGRESSIONS #######

rows = []
for y_col in EPS_SPECS:
    for x_col in X_COLS:
        for sample, excluded in SAMPLES.items():
            data = df[~df['n'].isin(excluded)][[y_col, x_col]].dropna()
            model = sm.OLS(data[y_col], sm.add_constant(data[x_col])).fit(cov_type='HC1')
            rows.append({
                'y_column': y_col,
                'x_column': x_col,
                'sample': sample,
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

pd.set_option('display.width', 200)
print(report.to_string(index=False, float_format='{:.4g}'.format))
print(f"\nSaved CSV to {output_filename}")
