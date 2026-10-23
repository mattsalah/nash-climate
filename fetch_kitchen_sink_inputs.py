import io
import os
import requests
import pandas as pd

# Downloads the extra country characteristics for regress_kitchen_sink.py (fossil fuel rents and
# subsoil assets are downloaded by hand into input/fossil_rents/, see README):
#   World Bank API (api.worldbank.org/v2), all years 1990-2024:
#     SI.POV.GINI                       Gini index
#     AG.LND.TOTL.K2                    land area (sq. km)
#     NY.GDP.PCAP.KD                    GDP per capita (constant 2015 US$), for the panels
#   V-Dem, via Our World in Data:
#     political corruption index (v2x_corr, 0-1, higher = more corrupt)
#     electoral democracy index (v2x_polyarchy, 0-1, higher = more democratic)

output_dir = 'input/kitchen_sink'

WB_INDICATORS = {
    'SI.POV.GINI': None,
    'AG.LND.TOTL.K2': None,
    'NY.GDP.PCAP.KD': None,
}
OWID_URL = 'https://ourworldindata.org/grapher/{}.csv?v=1&csvType=full&useColumnShortNames=true'
VDEM = {
    # output name: (OWID grapher, OWID column)
    'vdem_corruption': ('political-corruption-index', 'corruption_vdem__estimate_best'),
    'vdem_democracy': ('electoral-democracy-index', 'electdem_vdem__estimate_best'),
}

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

vdem = {}
for name, (grapher, column) in VDEM.items():
    print(f"Fetching {name}")
    # OWID refuses urllib's default user agent, so fetch with requests
    r = requests.get(OWID_URL.format(grapher), headers={'User-Agent': 'Mozilla/5.0'}, timeout=300)
    r.raise_for_status()
    v = pd.read_csv(io.StringIO(r.text))
    v = v[v['code'].notna()]
    v = v[~v['code'].str.startswith('OWID')]
    v = v.rename(columns={'code': 'n', column: name})
    v['n'] = v['n'].str.lower()
    vdem[name] = v[['n', 'year', name]]

###### SAVE ################

os.makedirs(output_dir, exist_ok=True)
wb.to_csv(f'{output_dir}/wb_indicators.csv', index=False)
for name, v in vdem.items():
    v.to_csv(f'{output_dir}/{name}.csv', index=False)
print(wb.groupby('indicator')['n'].nunique())
print(f"Saved to {output_dir}/")
