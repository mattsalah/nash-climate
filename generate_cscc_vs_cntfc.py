
import pandas as pd
import json

###### COUNTRY LEVEL SCCS #######

scc_df = pd.read_csv('country_scc/41558_2018_282_MOESM2_ESM.csv')

# Filter the data
# for now let's just take bhm_lr, bootstrap, uncertain, SSP2, rcp45, prtp = 2
# rename 'iso3' to n
# after filtering, just take the three values for 16.7%,50%,83.3% as save them as scc_low, scc_mid, scc_high
filtered_scc = scc_df[(scc_df['run'] == 'bhm_lr') & 
                     (scc_df['dmgfuncpar'] == 'bootstrap') & 
                     (scc_df['climate'] == 'uncertain') & 
                     (scc_df['SSP'] == 'SSP2') & 
                     (scc_df['RCP'] == 'rcp45') & 
                     (scc_df['prtp'] == 2)]

# Rename ISO3 to n
filtered_scc = filtered_scc.rename(columns={'ISO3': 'n'})

# Select and rename columns
pivoted_df = filtered_scc[['n', '16.7%', '50%', '83.3%']].rename(columns={'16.7%': 'scc_low', '50%': 'scc_mid', '83.3%': 'scc_high'})
pivoted_df['n'] = pivoted_df['n'].apply(lambda x: x.lower())

# global SCC 
global_scc = pivoted_df['scc_mid'].sum()
pivoted_df['global_scc_mid'] = global_scc

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
pct_diff_year = pct_diff_df[pct_diff_df['year'] == 2020][['id', 'pct_diff', 'ci_lower_pct', 'ci_upper_pct']]

# Map the country names to codes
pct_diff_year['n'] = pct_diff_year['id'].map(country_mapping)

# Drop rows where mapping is not found
pct_diff_year = pct_diff_year.dropna(subset=['n'])

# Merge the pct_diff into the pivoted_df on 'n', rename to policy_int_cntfc
pivoted_df = pd.merge(pivoted_df, pct_diff_year[['n', 'pct_diff', 'ci_lower_pct', 'ci_upper_pct']], on='n', how='left')

# Rename pct_diff to policy_int_cntfc
pivoted_df.rename(columns={
    'pct_diff': 'policy_int_cntfc',
    'ci_lower_pct': 'policy_int_cntfc_low',
    'ci_upper_pct': 'policy_int_cntfc_high',
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
        mu_solution = fsolve(equation, mu_init)[0]
        # Ensure mu is between 0 and 1 
        if 0 <= mu_solution <= 1:
            return mu_solution
        else:
            return np.nan
    except:
        return np.nan
    
def solve_coop_opt(row):
    return 100*solve_optimal_mu(row['global_scc_mid'], row['macc_a'], row['macc_d'])

def solve_noncoop_opt(row):
    return 100*solve_optimal_mu(row['scc_mid'], row['macc_a'], row['macc_d'])


# Apply the solver to each row
pivoted_df['coop_optimal_mu'] = pivoted_df.apply(solve_coop_opt, axis=1)
pivoted_df['noncoop_optimal_mu'] = pivoted_df.apply(solve_noncoop_opt, axis=1)

# save the output
output_filename = f'output/data/mitigation_cscc_v_cntfc_2020.csv'
pivoted_df.to_csv(output_filename, index=False)

print(f"Transformation complete. Output saved to {output_filename}")
