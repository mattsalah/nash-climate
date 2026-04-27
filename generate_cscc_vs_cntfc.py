
import pandas as pd
import json

output_filename = 'output/data/mitigation_cscc_v_cntfc_2020.csv'

###### COUNTRY LEVEL SCCS #######

scc_df = pd.read_csv('country_scc/41558_2018_282_MOESM2_ESM.csv')

# Rename ISO3 to n
scc_df = scc_df.rename(columns={'ISO3': 'n'})

# Filter the data for spec 1 [global scc ~ 400]
filtered_scc = scc_df[(scc_df['run'] == 'bhm_sr') & 
                     (scc_df['dmgfuncpar'] == 'bootstrap') & 
                     (scc_df['climate'] == 'uncertain') & 
                     (scc_df['SSP'] == 'SSP2') & 
                     (scc_df['RCP'] == 'rcp60') & 
                     (scc_df['prtp'] == 2)]


# Select and rename columns
pivoted_df = filtered_scc[['n', '16.7%', '50%', '83.3%']].rename(columns={'16.7%': 'scc_low_spec1', '50%': 'scc_mid_spec1', '83.3%': 'scc_high_spec1'})
pivoted_df['n'] = pivoted_df['n'].apply(lambda x: x.lower())

# Filter the data for spec 2 - high damages [global scc 781]
filtered_scc = scc_df[(scc_df['run'] == 'bhm_lr') & 
                     (scc_df['dmgfuncpar'] == 'bootstrap') & 
                     (scc_df['climate'] == 'uncertain') & 
                     (scc_df['SSP'] == 'SSP2') & 
                     (scc_df['RCP'] == 'rcp60') & 
                     (scc_df['prtp'] == 2)]

# add to pivoted_df
pivoted_df_new = filtered_scc[['n', '16.7%', '50%', '83.3%']].rename(columns={'16.7%': 'scc_low_spec2', '50%': 'scc_mid_spec2', '83.3%': 'scc_high_spec2'})
pivoted_df_new['n'] = pivoted_df_new['n'].apply(lambda x: x.lower())
pivoted_df = pd.merge(pivoted_df, pivoted_df_new, on='n', how='left')

# Filter the data for spec 3 - optimistic [global scc 131]
filtered_scc = scc_df[(scc_df['run'] == 'bhm_richpoor_sr') & 
                     (scc_df['dmgfuncpar'] == 'bootstrap') & 
                     (scc_df['climate'] == 'uncertain') & 
                     (scc_df['SSP'] == 'SSP1') & 
                     (scc_df['RCP'] == 'rcp45') & 
                     (scc_df['prtp'] == 2)]

# add to pivoted_df
pivoted_df_new = filtered_scc[['n', '16.7%', '50%', '83.3%']].rename(columns={'16.7%': 'scc_low_spec3', '50%': 'scc_mid_spec3', '83.3%': 'scc_high_spec3'})
pivoted_df_new['n'] = pivoted_df_new['n'].apply(lambda x: x.lower())
pivoted_df = pd.merge(pivoted_df, pivoted_df_new, on='n', how='left')


# Filter the data for spec 4 - fixed discounting [global scc ~400 but order of countries changes]
filtered_scc = scc_df[(scc_df['run'] == 'bhm_sr') & 
                     (scc_df['dmgfuncpar'] == 'bootstrap') & 
                     (scc_df['climate'] == 'uncertain') & 
                     (scc_df['SSP'] == 'SSP2') & 
                     (scc_df['RCP'] == 'rcp60') & 
                     (scc_df['dr'] == 3)]
# add to pivoted_df
pivoted_df_new = filtered_scc[['n', '16.7%', '50%', '83.3%']].rename(columns={'16.7%': 'scc_low_spec4', '50%': 'scc_mid_spec4', '83.3%': 'scc_high_spec4'})
pivoted_df_new['n'] = pivoted_df_new['n'].apply(lambda x: x.lower())
pivoted_df = pd.merge(pivoted_df, pivoted_df_new, on='n', how='left')

# Rename ISO3 to n
filtered_scc = filtered_scc.rename(columns={'ISO3': 'n'})


# global SCCs
global_scc1 = pivoted_df['scc_mid_spec1'].sum()
pivoted_df['global_scc_mid_spec1'] = global_scc1
global_scc2 = pivoted_df['scc_mid_spec2'].sum()
pivoted_df['global_scc_mid_spec2'] = global_scc2
global_scc3 = pivoted_df['scc_mid_spec3'].sum()
pivoted_df['global_scc_mid_spec3'] = global_scc3
global_scc4 = pivoted_df['scc_mid_spec4'].sum()
pivoted_df['global_scc_mid_spec4'] = global_scc4


########## MACC parameters ##########

# pull from data/macc_ed_early.csv
# get the a and the d for each country with t=2

macc_df = pd.read_csv('output/data/macc_ed_early.csv')

# Filter for t=2 and sector Total_CO2, then pivot so a and d become separate columns
macc_filtered = macc_df[(macc_df['t'].astype(str).str.strip() == '2') & 
                        (macc_df['sector'] == 'Total_CO2') & 
                        (macc_df['Dim2'].isin(['a', 'd']))]

# Pivot to get 'a' and 'd' as columns
macc_pivoted = macc_filtered.pivot_table(index='n', columns='Dim2', values='Val', aggfunc='first').reset_index()
macc_pivoted.columns.name = None
macc_pivoted.columns = ['n', 'macc_a', 'macc_d']

# Convert n to iso3
macc_pivoted['n'] = macc_pivoted['n'].apply(lambda x: x.strip().lower())
rice_to_iso3 = json.load(open('rice_to_iso3.json'))
macc_pivoted['n'] = macc_pivoted['n'].apply(lambda x: rice_to_iso3[x] if x in rice_to_iso3 else x)

# Merge MACC parameters into pivoted_df
pivoted_df = pd.merge(pivoted_df, macc_pivoted, on='n', how='left')


###### POLICY INTENSITY COUNTERFACUTALS #########

# Mapping from full country names to region codes
country_mapping = json.load(open('policy_int_to_iso3.json'))

# Read the pct_diff CSV
pct_diff_df = pd.read_csv('output/data/country_year_counterfactual_CO2.csv')


# Filter for the year
pct_diff_year = pct_diff_df[pct_diff_df['year'] == 2020]

# Map the country names to codes
pct_diff_year['n'] = pct_diff_year['id'].map(country_mapping)

# Drop rows where mapping is not found
pct_diff_year = pct_diff_year.dropna(subset=['n'])

cntfc_cols = ['n', 'pct_diff_zero', 'ci_lower_pct_zero', 'ci_upper_pct_zero', 'pct_diff_zero_strng', 'ci_lower_pct_zero_strng', 'ci_upper_pct_zero_strng']

# Merge the pct_diff into the pivoted_df on 'n', rename to policy_den_cntfc
pivoted_df = pd.merge(pivoted_df, pct_diff_year[cntfc_cols], on='n', how='left')

# Rename pct_diff to policy_den_cntfc
pivoted_df.rename(columns={
    'pct_diff_zero': 'policy_den_cntfc',
    'ci_lower_pct_zero': 'policy_den_cntfc_low',
    'ci_upper_pct_zero': 'policy_den_cntfc_high',
    'pct_diff_zero_strng': 'policy_strng_cntfc',
    'ci_lower_pct_zero_strng': 'policy_strng_cntfc_low',
    'ci_upper_pct_zero_strng': 'policy_strng_cntfc_high',
    }, inplace=True)


#### CALCULATE OPTIMAL ABATEMENT FROM COUNTERFACTUAL EMISSIONS

# MB = scc_mid
# MC = a*mu + d*mu^4
# solve for mu and save to a new column called "noncoop_optimal_mu"

import numpy as np
from scipy.optimize import fsolve

def solve_optimal_mu(scc, a, d):
    """
    Solve for mu where MB = MC
    MB = scc 
    MC = a*mu + d*mu^4
    """
    # Check for missing values
    if pd.isna(scc) or pd.isna(a) or pd.isna(d):
        return np.nan
    
    # Define the equation to solve: MC - MB = 0
    def equation(mu):
        return a * mu + d * (mu ** 4) - scc
    
    # Initial guess
    mu_init = 0.5
    
    # Solve using fsolve
    try:
        mu_opt = fsolve(equation, mu_init)[0]
        if mu_opt < 0: 
            return 0 # no negative abatement
        else:
            return mu_opt
    except:
        return np.nan
    
def solve_coop_opt(row, spec):
    return 100*solve_optimal_mu(row[f'global_scc_mid_spec{spec}'], row['macc_a'], row['macc_d'])

def solve_noncoop_opt(row, spec):
    return 100*solve_optimal_mu(row[f'scc_mid_spec{spec}'], row['macc_a'], row['macc_d'])

for spec in range(1,5):
    # Apply the solver to each row
    pivoted_df[f'coop_optimal_mu_spec{spec}'] = pivoted_df.apply(solve_coop_opt, args=(spec,), axis=1)
    pivoted_df[f'noncoop_optimal_mu_spec{spec}'] = pivoted_df.apply(solve_noncoop_opt, args=(spec,), axis=1)

# save the output
pivoted_df.to_csv(output_filename, index=False)

print(f"Transformation complete. Output saved to {output_filename}")
