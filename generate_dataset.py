import pandas as pd

# RICE: 2015-2100
# Policy Intensity: 2015-2022
# Structural Breaks: ??
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


###### POLICY INTENSITY COUNTERFACUTALS #########

# Mapping from full country names to region codes
country_mapping = {
    'Australia': 'aus',
    'Argentina': 'arg',
    'Austria': 'aut',
    'Belgium': 'bel',
    'Brazil': 'bra',
    'Canada': 'can',
    'Chile': 'chl',
    'China': 'chn',
    'Colombia': 'col',
    'Czech Republic': 'rcz', # not standard
    'Denmark': 'dnk',
    'Estonia': 'est',
    'Finland': 'fin',
    'France': 'fra',
    'Germany': 'rfa',
    'Greece': 'grc',
    'Hungary': 'hun',
    'Iceland': 'isl',
    'India': 'nde',  # not standard
    'Indonesia': 'idn',
    'Ireland': 'irl',
    'Israel': 'isr',
    'Italy': 'ita',
    'Japan': 'jpn',
    'Korea': 'cor',  # not standard
    'Latvia': 'lva',
    'Lithuania': 'ltu',
    'Luxembourg': 'lux',
    'Mexico': 'mex',
    'Netherlands': 'nld',
    'New Zealand': 'nzl',
    'Norway': 'nor',
    'Poland': 'pol',
    'Portugal': 'prt',
    'Russia': 'rus',
    'Slovak Republic': 'rsl', # not standard
    'Slovenia': 'slo', # not standard
    'South Africa': 'zaf',
    'Spain': 'esp',
    'Sweden': 'sui', # not standard
    'Switzerland': 'che',
    'Turkey': 'tur',
    'United Kingdom': 'gbr',
    'United States of America': 'usa',
}

# Read the pct_diff CSV
pct_diff_df = pd.read_csv('output/data/country_year_counterfactual_CO2.csv')

# Filter for the year
pct_diff_year = pct_diff_df[pct_diff_df['year'] == year][['id', 'pct_diff', 'ci_lower_pct', 'ci_upper_pct']]

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

# Save the transformed data to a new CSV file
output_filename = f'output/data/mitigation_rice_v_cntfc_{year}.csv'
pivoted_df.to_csv(output_filename, index=False)

print(f"Transformation complete. Output saved to {output_filename}")

