import os
import requests
import pandas as pd

# Downloads public energy RD&D budgets from the API behind the IEA Energy Technology RD&D Budgets
# data explorer (https://www.iea.org/data-and-statistics/data-tools/energy-technology-rdd-budgets-data-explorer).
# The zipped database needs an IEA login, the explorer API doesn't
#
#   iea_rdd_public.csv   budget by country, year and level-1 technology group, million USD
#                        (previous year's prices and PPPs)
#   iea_rdd_gdp.csv      total budget per thousand units of GDP, by country and year (IEA's own
#                        ratio, used to back out the GDP denominator for each technology group)

API = 'https://api.iea.org/rdd'
PRODUCT = 'Public RD&D in million USD (y-1 prices and PPP)'
output_dir = 'input/iea_rdd'

###### FETCH #######

def get(path='', **params):
    r = requests.get(f'{API}{path}', params=params, timeout=120)
    r.raise_for_status()
    return r.json()

technologies = [t['codeTech'] for t in get('/technologies') if t['level'] <= 1]
years = get('/list/TIME')
countries = [c for group in get('/list/COUNTRY') if group['label'] == 'Countries' for c in group['options']]
# the country list omits some countries that do report (e.g. Latvia), so add any found in the totals
gdp_rows = []
for year in years:
    gdp_rows += get('/sum', TIME=year, type='gdp')
countries = sorted(set(countries) | {row['COUNTRY'] for row in gdp_rows})

budget_rows = []
for country in countries:
    print(f"Fetching {country}")
    budget_rows += get(COUNTRY=country, PRODUCT=PRODUCT, TECHNOLOGY=','.join(technologies), isRegion='false')

###### SAVE ################

budget = pd.DataFrame(budget_rows).rename(columns=str.lower)
budget = budget[['country', 'time', 'technology_code', 'technology_name', 'value']].rename(columns={'time': 'year'})
gdp = pd.DataFrame(gdp_rows).rename(columns={'COUNTRY': 'country', 'TIME': 'year', 'VALUE': 'rdd_per_thousand_gdp'})

os.makedirs(output_dir, exist_ok=True)
budget.to_csv(f'{output_dir}/iea_rdd_public.csv', index=False)
gdp.to_csv(f'{output_dir}/iea_rdd_gdp.csv', index=False)
print(f"Saved {len(budget)} budget rows for {budget['country'].nunique()} countries to {output_dir}/")
