import os
import pandas as pd

# Counts green subsidy programs per country from the World Bank Green Subsidies Database (GSD).
# The GSD is an inventory of programs with environmental objectives (name, form, sector,
# objective) for 20 economies and reference years 2017, 2018, 2021 and 2022. It reports no
# amounts, so the measures here are program counts, in total and scaled by GDP
#
# Outcomes, for one reference year:
#   gs_n_all            all green subsidy programs (central + subnational)
#   gs_n_central        central government programs only (subnational coverage is uneven:
#                       mostly US, China, Australia, UK)
#   gs_n_rnd            programs whose primary objective is R&D/Innovation
#   gs_n_all_per_gdp    gs_n_all per $1tn of GDP (2020 WDI, current USD)
#   gs_n_rnd_per_gdp    gs_n_rnd per $1tn of GDP

input_filename = 'input/green_subsidies/wb_green_subsidies.xlsx'
output_filename = 'output/data/green_subsidies.csv'
REFYEAR = 2022

GSD_TO_ISO3 = {
    'Australia': 'aus', 'Belgium': 'bel', 'Brazil': 'bra', 'Canada': 'can', 'China': 'chn',
    'France': 'fra', 'India': 'ind', 'Israel': 'isr', 'Japan': 'jpn', 'Korea, Rep.': 'kor',
    'Mexico': 'mex', 'Netherlands': 'nld', 'Norway': 'nor', 'Philippines': 'phl',
    'Switzerland': 'che', 'Turkey': 'tur', 'United Kingdom': 'gbr', 'United States': 'usa',
    'Vietnam': 'vnm', 'European Union': 'eu',
}

###### DATA #######

gsd = pd.read_excel(input_filename)
gsd = gsd[gsd['refyear'] == REFYEAR]
gsd['n'] = gsd['country'].map(GSD_TO_ISO3)
unmapped = gsd.loc[gsd['n'].isna(), 'country'].unique().tolist()
assert not unmapped, f"unmapped GSD countries: {unmapped}"

counts = pd.DataFrame({
    'gs_n_all': gsd.groupby('n').size(),
    'gs_n_central': gsd[gsd['level'] == 'Central Government'].groupby('n').size(),
    'gs_n_rnd': gsd[gsd['objective_l1'] == 'R&D/Innovation'].groupby('n').size(),
}).fillna(0).astype(int).reset_index()

# Population and GDP per capita from the merged CSCC dataset (WB WDI, 2020)
controls = pd.read_csv('output/data/mitigation_cscc_v_cntfc_2020.csv')[['n', 'pop', 'gdppc']]
df = counts.merge(controls, on='n', how='left')
gdp_tn = df['pop'] * df['gdppc'] / 1e12
df['gs_n_all_per_gdp'] = df['gs_n_all'] / gdp_tn
df['gs_n_rnd_per_gdp'] = df['gs_n_rnd'] / gdp_tn
df = df.drop(columns=['pop', 'gdppc'])
df.insert(1, 'refyear', REFYEAR)

###### SAVE ################

os.makedirs(os.path.dirname(output_filename), exist_ok=True)
df.to_csv(output_filename, index=False)

print(df.sort_values('gs_n_all', ascending=False).to_string(index=False, float_format='{:.3g}'.format))
print(f"\nSaved CSV to {output_filename}")
