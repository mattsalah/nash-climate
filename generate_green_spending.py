import os
import json
import pandas as pd

# Builds cross-country measures of green technology support, in long format (n, year, measure, value):
#
# OECD EPS technology support (0-6 scores, 2015 and 2020; EPS ends in 2020)
#   eps_rd_sub              low-carbon public R&D expenditure, scored by its size relative to GDP
#   eps_techsup             technology support sub-index (R&D plus solar and wind support)
#
# IEA Energy Technology RD&D Budgets (fetch_iea_rdd.py; 2015, 2020, 2024, 2025; 2025 is provisional)
#   rdd_total               total public energy RD&D, million USD (y-1 prices and PPP)
#   rdd_low_carbon          total minus fossil fuels (incl. nuclear, efficiency, renewables,
#                           hydrogen, power and storage, CCS, cross-cutting)
#   rdd_renewables          renewable energy sources
#   *_pct_gdp               the same as % of GDP, with GDP backed out of the IEA's own RD&D per
#                           thousand GDP ratio (PPP, the same price basis as the budgets)
#
# IEA Government Energy Spending Tracker (budget commitments since 2020, snapshot of Sept 2024)
#   gest_clean              clean energy investment support (everything except consumer energy
#                           affordability measures), billion USD (the explorer labels them
#                           millions, but e.g. IRA Sec. 13101 is 51.06)
#   gest_innovation         the "Fuels and technology innovation" category (hydrogen, CCUS,
#                           batteries, biofuels, critical minerals, other innovation)
#   *_pct_gdp               the same as % of GDP (WB WDI, current USD)
#   year 2020 is commitments starting in 2020 (% of 2020 GDP); year 2024 is all commitments
#   since 2020 as of the Sept 2024 snapshot, including later tranches (% of 2023 GDP)

output_filename = 'output/data/green_spending.csv'
RDD_YEARS = [2015, 2020, 2024, 2025]
EPS_YEARS = [2015, 2020]

iea_to_iso3 = json.load(open('input/iea_to_iso3.json'))

wb = pd.read_csv('input/wb_controls/pop_gdp_2015_2025.csv',
                 usecols=['country', 'year', 'WB_WDI_SP_POP_TOTL', 'WB_WDI_NY_GDP_PCAP_CD'])
wb['n'] = wb['country'].str.lower()
wb['gdp_musd'] = wb['WB_WDI_SP_POP_TOTL'] * wb['WB_WDI_NY_GDP_PCAP_CD'] / 1e6
wb_gdp = wb.set_index(['n', 'year'])['gdp_musd']

frames = []

def add(df, measure, year, value_col='value'):
    frames.append(pd.DataFrame({'n': df['n'], 'year': year, 'measure': measure, 'value': df[value_col]}))

###### OECD EPS #######

eps = pd.read_csv('input/policy_stringency/oecd_eps.csv', usecols=['REF_AREA', 'CLIM_POL', 'TIME_PERIOD', 'OBS_VALUE'])
eps['n'] = eps['REF_AREA'].str.lower()
for code, measure in [('RD_SUB', 'eps_rd_sub'), ('TECHSUP', 'eps_techsup')]:
    for year in EPS_YEARS:
        add(eps[(eps['CLIM_POL'] == code) & (eps['TIME_PERIOD'] == year)], measure, year, 'OBS_VALUE')

###### IEA RD&D #######

rdd = pd.read_csv('input/iea_rdd/iea_rdd_public.csv')
rdd = rdd.pivot_table(index=['country', 'year'], columns='technology_code', values='value').reset_index()
rdd = rdd[rdd['TOTAL'] > 0]
rdd['rdd_total'] = rdd['TOTAL']
rdd['rdd_low_carbon'] = rdd['TOTAL'] - rdd['B'].fillna(0)
rdd['rdd_renewables'] = rdd['C']

ratio = pd.read_csv('input/iea_rdd/iea_rdd_gdp.csv')
rdd = rdd.merge(ratio, on=['country', 'year'], how='left')
gdp_ppp = rdd['TOTAL'] / (rdd['rdd_per_thousand_gdp'] / 1000)
gdp_ppp = gdp_ppp.where(rdd['rdd_per_thousand_gdp'] > 0)
rdd['n'] = rdd['country'].map(iea_to_iso3)
assert rdd['n'].notna().all(), rdd.loc[rdd['n'].isna(), 'country'].unique()

for measure in ['rdd_total', 'rdd_low_carbon', 'rdd_renewables']:
    rdd[f'{measure}_pct_gdp'] = 100 * rdd[measure] / gdp_ppp
    for year in RDD_YEARS:
        add(rdd[rdd['year'] == year], measure, year, measure)
        add(rdd[rdd['year'] == year], f'{measure}_pct_gdp', year, f'{measure}_pct_gdp')

###### IEA GOVERNMENT ENERGY SPENDING TRACKER #######

# The first record is a header row. Following the tracker's own totals, keep records with a start
# year, technology and budget, and sum budgets
gest = pd.DataFrame(json.load(open('input/iea_spending_tracker/policies.json'))[1:])
gest = gest[gest['startYear'].notna() & gest['tech'].notna() & gest['budgetUSD'].notna()]
gest = gest[gest['fundingType'] == 'Government']
gest['startYear'] = gest['startYear'].astype(int)
gest['n'] = gest['country'].map(iea_to_iso3)
assert gest['n'].notna().all(), gest.loc[gest['n'].isna(), 'country'].unique()

INNOVATION = ['Advanced biofuels', 'Biogas', 'Biofuels', 'Other innovation', 'Other Innovation', 'Hydrogen',
              'CCUS', 'Batteries', 'Methane abatement', 'Critical minerals', 'Thermal storage', 'Fuels']
gest['gest_clean'] = gest['budgetUSD'].where(gest['tech'] != 'Energy affordability', 0)
gest['gest_innovation'] = gest['budgetUSD'].where(gest['tech'].isin(INNOVATION), 0)

all_countries = pd.Index(gest['n'].unique(), name='n')
for year, rows, gdp_year in [(2020, gest[gest['startYear'] == 2020], 2020), (2024, gest, 2023)]:
    totals = rows.groupby('n')[['gest_clean', 'gest_innovation']].sum().reindex(all_countries, fill_value=0).reset_index()
    gdp = totals['n'].map(lambda n: wb_gdp.get((n, gdp_year)))
    for measure in ['gest_clean', 'gest_innovation']:
        totals[f'{measure}_pct_gdp'] = 100 * 1000 * totals[measure] / gdp
        add(totals, measure, year, measure)
        add(totals, f'{measure}_pct_gdp', year, f'{measure}_pct_gdp')

###### SAVE ################

df = pd.concat(frames, ignore_index=True).dropna(subset=['value'])
os.makedirs(os.path.dirname(output_filename), exist_ok=True)
df.to_csv(output_filename, index=False)

pd.set_option('display.width', 250)
summary = df.groupby(['measure', 'year'])['value'].agg(['count', 'sum', 'median', 'max'])
print(summary.to_string(float_format='{:.4g}'.format))
print(f"\nSaved CSV to {output_filename}")
