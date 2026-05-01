import pandas as pd
import argparse
import json

year = 2022

###### RICE PREDICTED ABATEMENT #########

# Read the CSV file
df = pd.read_csv('NC2021_results_dataset/CBA_regional_data.csv')

# Get unique years
years = sorted(df['year'].unique())

if year in years:
    # Filter for year, policy CBA, cooperation noncoop-pop and coop-pop
    coop_noncoop_df = df[(df['year'] == year) & (df['policy'] == 'CBA') & (df['cooperation'].isin(['noncoop-pop', 'coop-pop']))]

    # Separate into noncoop and coop dataframes
    noncoop_df = coop_noncoop_df[coop_noncoop_df['cooperation'] == 'noncoop-pop']
    coop_df = coop_noncoop_df[coop_noncoop_df['cooperation'] == 'coop-pop']

    # Create spec columns with prefixes
    noncoop_df['spec'] = 'NONCOOP_' + noncoop_df['baseline'] + '_' + noncoop_df['impacts'] + '_' + noncoop_df['prstp'].astype(str)
    coop_df['spec'] = 'COOP_' + coop_df['baseline'] + '_' + coop_df['impacts'] + '_' + coop_df['disnt'].astype(str) + '_' + coop_df['prstp'].astype(str)

    # Pivot the data for noncoop: index by country (n), columns by spec, values emi_ind
    pivoted_noncoop = noncoop_df.pivot(index='n', columns='spec', values='mitigation')

    # Reset index to make country a column
    pivoted_noncoop.reset_index(inplace=True)

    # Pivot the data for coop: index by country (n), columns by spec, values emi_ind
    pivoted_coop = coop_df.pivot(index='n', columns='spec', values='mitigation')

    # Reset index to make country a column
    pivoted_coop.reset_index(inplace=True)

else:
    # Interpolate between two closest years
    y1 = max(y for y in years if y <= year)
    y2 = min(y for y in years if y >= year)
    weight1 = (y2 - year) / (y2 - y1)
    weight2 = (year - y1) / (y2 - y1)

    # Filter for y1
    coop_noncoop_df_y1 = df[(df['year'] == y1) & (df['policy'] == 'CBA') & (df['cooperation'].isin(['noncoop-pop', 'coop-pop']))]
    noncoop_df_y1 = coop_noncoop_df_y1[coop_noncoop_df_y1['cooperation'] == 'noncoop-pop']
    coop_df_y1 = coop_noncoop_df_y1[coop_noncoop_df_y1['cooperation'] == 'coop-pop']
    noncoop_df_y1['spec'] = 'NONCOOP_' + noncoop_df_y1['baseline'] + '_' + noncoop_df_y1['impacts'] + '_' + noncoop_df_y1['prstp'].astype(str)
    coop_df_y1['spec'] = 'COOP_' + coop_df_y1['baseline'] + '_' + coop_df_y1['impacts'] + '_' + coop_df_y1['disnt'].astype(str) + '_' + coop_df_y1['prstp'].astype(str)
    pivoted_noncoop_y1 = noncoop_df_y1.pivot(index='n', columns='spec', values='mitigation').reset_index()
    pivoted_coop_y1 = coop_df_y1.pivot(index='n', columns='spec', values='mitigation').reset_index()

    # Filter for y2
    coop_noncoop_df_y2 = df[(df['year'] == y2) & (df['policy'] == 'CBA') & (df['cooperation'].isin(['noncoop-pop', 'coop-pop']))]
    noncoop_df_y2 = coop_noncoop_df_y2[coop_noncoop_df_y2['cooperation'] == 'noncoop-pop']
    coop_df_y2 = coop_noncoop_df_y2[coop_noncoop_df_y2['cooperation'] == 'coop-pop']
    noncoop_df_y2['spec'] = 'NONCOOP_' + noncoop_df_y2['baseline'] + '_' + noncoop_df_y2['impacts'] + '_' + noncoop_df_y2['prstp'].astype(str)
    coop_df_y2['spec'] = 'COOP_' + coop_df_y2['baseline'] + '_' + coop_df_y2['impacts'] + '_' + coop_df_y2['disnt'].astype(str) + '_' + coop_df_y2['prstp'].astype(str)
    pivoted_noncoop_y2 = noncoop_df_y2.pivot(index='n', columns='spec', values='mitigation').reset_index()
    pivoted_coop_y2 = coop_df_y2.pivot(index='n', columns='spec', values='mitigation').reset_index()

    # Interpolate
    pivoted_noncoop = pivoted_noncoop_y1.copy()
    pivoted_coop = pivoted_coop_y1.copy()
    spec_cols_noncoop = [col for col in pivoted_noncoop.columns if col != 'n']
    spec_cols_coop = [col for col in pivoted_coop.columns if col != 'n']
    for col in spec_cols_noncoop:
        pivoted_noncoop[col] = weight1 * pivoted_noncoop_y1[col] + weight2 * pivoted_noncoop_y2[col]
    for col in spec_cols_coop:
        pivoted_coop[col] = weight1 * pivoted_coop_y1[col] + weight2 * pivoted_coop_y2[col]

# Merge the two pivoted dataframes on 'n'
pivoted_df = pd.merge(pivoted_noncoop, pivoted_coop, on='n', how='outer')

# rename 'n' to the iso3 codes
rice_to_iso3 = json.load(open('rice_to_iso3.json'))
pivoted_df['n'] = pivoted_df['n'].apply(lambda x: rice_to_iso3[x] if x in rice_to_iso3 else x)

###### POLICY INTENSITY COUNTERFACUTALS #########

# Mapping from full country names to region codes
country_mapping = json.load(open('policy_int_to_iso3.json'))

# Read the CSV
policy_int_df = pd.read_csv('output/data/country_year_counterfactual_CO2.csv')

# For each country, calculate the difference from its 2015 value for pol_dens_cum and strng_wght_ind columns
for col in ['pol_dens_cum', 'strng_wght_ind']:
    # Create a mapping of id to its 2015 value
    val_2015 = policy_int_df[policy_int_df['year'] == 2015].set_index('id')[col]
    policy_int_df[f'{col}_diff'] = policy_int_df[col] - policy_int_df['id'].map(val_2015)

# Filter for the year
policy_int_year = policy_int_df[policy_int_df['year'] == 2022]

# Map the country names to codes
policy_int_year['n'] = policy_int_year['id'].map(country_mapping)

# Drop rows where mapping is not found
policy_int_year = policy_int_year.dropna(subset=['n'])

cntfc_cols = ['n', 'pol_dens_cum', 'strng_wght_ind', 
              'pol_dens_cum_diff', 'strng_wght_ind_diff', 
              'pct_diff_2015', 'ci_lower_pct_2015', 'ci_upper_pct_2015', 
              'pct_diff_2015_strng', 'ci_lower_pct_2015_strng', 'ci_upper_pct_2015_strng']

# Merge the pct_diff into the pivoted_df on 'n', rename to policy_den_cntfc
pivoted_df = pd.merge(pivoted_df, policy_int_year[cntfc_cols], on='n', how='left')

# Rename pct_diff to policy_den_cntfc
pivoted_df.rename(columns={
    'pct_diff_2015': 'policy_den_cntfc',
    'ci_lower_pct_2015': 'policy_den_cntfc_low',
    'ci_upper_pct_2015': 'policy_den_cntfc_high',
    'pct_diff_2015_strng': 'policy_strng_cntfc',
    'ci_lower_pct_2015_strng': 'policy_strng_cntfc_low',
    'ci_upper_pct_2015_strng': 'policy_strng_cntfc_high',
    }, inplace=True)


################ CARBON PRICING ################

# read carbon_pricing.csv
# take REF_AREA, OBS_VALUE filtering for (TIME_PERIOD=2021, STRUCTURE_ID=OECD.CTP.TPS:DSD_NECR@DF_NECRS(1.1))
# rename OBS_VALUE to a column called carbon_price_effective
# merge with pivoted df on REF_AREA = 'n'
carbon_price_df = pd.read_csv('carbon_pricing/carbon_pricing.csv')

# Filter for relevant data
carbon_price_df = carbon_price_df[
    (carbon_price_df['TIME_PERIOD'] == year+1) &
    (carbon_price_df['STRUCTURE_ID'] == 'OECD.CTP.TPS:DSD_NECR@DF_NECRS(1.1)')
]

# Select and rename columns
carbon_price_df = carbon_price_df[['REF_AREA', 'OBS_VALUE']].rename(columns={
    'REF_AREA': 'n',
    'OBS_VALUE': 'carbon_price_effective'
})

# Convert 'n' to lowercase for merging
carbon_price_df['n'] = carbon_price_df['n'].str.lower()

# Remove duplicate country codes, keeping the first entry
carbon_price_df = carbon_price_df.drop_duplicates(subset='n', keep='first')

# Merge with pivoted_df
pivoted_df = pd.merge(pivoted_df, carbon_price_df, on='n', how='left')

################ SAVE ################

output_filename = f'output/data/mitigation_rice_v_cntfc_{year}.csv'
pivoted_df.to_csv(output_filename, index=False)

print(f"Transformation complete. Output saved to {output_filename}")

