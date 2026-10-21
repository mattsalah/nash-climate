import os
import requests
import pandas as pd

# Downloads the extra country characteristics for regress_kitchen_sink.py (fossil fuel rents and
# subsoil assets are downloaded by hand into input/fossil_rents/, see README):
#   World Bank API (api.worldbank.org/v2), all years 1990-2024:
#     SI.POV.GINI                       Gini index
#     AG.LND.TOTL.K2                    land area (sq. km)
#     NY.GDP.PCAP.KD                    GDP per capita (constant 2015 US$), for the panels
#   V-Dem political corruption index (v2x_corr, 0-1, higher = more corrupt), via Our World in Data

output_dir = 'input/kitchen_sink'

WB_INDICATORS = {
    'SI.POV.GINI': None,
    'AG.LND.TOTL.K2': None,
    'NY.GDP.PCAP.KD': None,
}
VDEM_URL = 'https://ourworldindata.org/grapher/political-corruption-index.csv?v=1&csvType=full&useColumnShortNames=true'

###### FETCH #######

rows = []
for indicator, source in WB_INDICATORS.items():
    print(f"Fetching {indicator}")
    params = {'format': 'json', 'date': '1990:2024', 'per_page': 20000}
    if source:
        params['source'] = source
    r = requests.get(f'https://api.worldbank.org/v2/country/all/indicator/{indicator}', params=params, timeout=300)
    r.raise_for_status()
    meta, data = r.json()
    assert meta['pages'] == 1, f"{indicator} has more than one page"
    rows += [{'n': d['countryiso3code'].lower(), 'year': int(d['date']), 'indicator': indicator, 'value': d['value']}
             for d in data if d['value'] is not None and d['countryiso3code']]

wb = pd.DataFrame(rows)

print("Fetching V-Dem corruption")
vdem = pd.read_csv(VDEM_URL)
vdem = vdem[vdem['code'].notna()]
vdem = vdem[~vdem['code'].str.startswith('OWID')]
vdem = vdem.rename(columns={'code': 'n', 'corruption_vdem__estimate_best': 'vdem_corruption'})
vdem['n'] = vdem['n'].str.lower()

###### SAVE ################

os.makedirs(output_dir, exist_ok=True)
wb.to_csv(f'{output_dir}/wb_indicators.csv', index=False)
vdem[['n', 'year', 'vdem_corruption']].to_csv(f'{output_dir}/vdem_corruption.csv', index=False)
print(wb.groupby('indicator')['n'].nunique())
print(f"Saved to {output_dir}/")
