import pandas as pd

year = 2020

# Read the CSV file
df = pd.read_csv('NC2021_results_dataset/CBA_regional_data.csv')

# Filter for year, policy CBA, cooperation noncoop-pop
filtered_df = df[(df['year'] == year) & (df['policy'] == 'CBA') & (df['cooperation'] == 'noncoop-pop')]

# Create a specification column combining baseline, impacts, and prstp
filtered_df['spec'] = filtered_df['baseline'] + '_' + filtered_df['impacts'] + '_' + filtered_df['prstp'].astype(str)

# Pivot the data: index by country (n), columns by spec, values emi_ind
pivoted_df = filtered_df.pivot(index='n', columns='spec', values='emi_ind')

# Reset index to make country a column
pivoted_df.reset_index(inplace=True)

# If year is 2020, merge pct_diff and rename to policy_int_cntfc
if year == 2020:
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
    pct_diff_year = pct_diff_df[pct_diff_df['year'] == year][['id', 'pct_diff']]

    # Map the country names to codes
    pct_diff_year['n'] = pct_diff_year['id'].map(country_mapping)

    # Drop rows where mapping is not found
    pct_diff_year = pct_diff_year.dropna(subset=['n'])

    # Merge the pct_diff into the pivoted_df on 'n', rename to policy_int_cntfc
    pivoted_df = pd.merge(pivoted_df, pct_diff_year[['n', 'pct_diff']], on='n', how='left')

    # Rename pct_diff to policy_int_cntfc
    pivoted_df.rename(columns={'pct_diff': 'policy_int_cntfc'}, inplace=True)

# Save the transformed data to a new CSV file
output_filename = f'output/data/transformed_emi_ind_{year}.csv' if year != 2020 else f'output/data/transformed_emi_ind_{year}_with_policy_int_cntfc.csv'
pivoted_df.to_csv(output_filename, index=False)

print(f"Transformation complete. Output saved to {output_filename}")