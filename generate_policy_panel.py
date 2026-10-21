import os
import json
import numpy as np
import pandas as pd

# Country-year panel for regress_carbon_price_adoption.py:
#   dolphin_price      Dolphin & Merkle effective carbon price, all GHG ($/tCO2e), 1989-2024
#   priced             dolphin_price > 0
#   log_gdppc          log GDP per capita (constant 2015 US$)
#   vdem_corruption    V-Dem political corruption index
#   eu_member          EU member that year (the UK until 2020)
#   eu_ets             covered by the EU ETS that year: EU members from 2005, and Norway, Iceland
#                      and Liechtenstein from 2008
# plus the time-invariant kitchen sink characteristics (output/data/kitchen_sink_inputs.csv) and
# own CSCC for all four specs

output_filename = 'output/data/policy_panel.csv'

# accession year (founding members and pre-1990 joiners as 1958)
EU_ACCESSION = {
    'bel': 1958, 'fra': 1958, 'deu': 1958, 'ita': 1958, 'lux': 1958, 'nld': 1958,
    'dnk': 1973, 'irl': 1973, 'gbr': 1973, 'grc': 1981, 'esp': 1986, 'prt': 1986,
    'aut': 1995, 'fin': 1995, 'swe': 1995,
    'cyp': 2004, 'cze': 2004, 'est': 2004, 'hun': 2004, 'lva': 2004, 'ltu': 2004, 'mlt': 2004,
    'pol': 2004, 'svk': 2004, 'svn': 2004,
    'bgr': 2007, 'rou': 2007, 'hrv': 2013,
}
EU_EXIT = {'gbr': 2020}
EEA_ETS = ['nor', 'isl', 'lie']

###### DOLPHIN #######

dolphin_to_iso3 = json.load(open('input/dolphin_to_iso3.json'))
dolphin = pd.read_csv('input/carbon_pricing/carbon_pricing_dolphin.csv')
dolphin = dolphin[dolphin['jurisdiction'].isin(dolphin_to_iso3.keys())]
dolphin['n'] = dolphin['jurisdiction'].map(dolphin_to_iso3).str.lower()
panel = dolphin[['n', 'year', 'ecp_all_jurGHG_usd_k']].rename(columns={'ecp_all_jurGHG_usd_k': 'dolphin_price'})
panel['priced'] = (panel['dolphin_price'] > 0).astype(int)

###### TIME-VARYING CONTROLS #######

wb = pd.read_csv('input/kitchen_sink/wb_indicators.csv')
gdppc = wb[wb['indicator'] == 'NY.GDP.PCAP.KD'][['n', 'year', 'value']]
gdppc['log_gdppc'] = np.log(gdppc['value'])
panel = panel.merge(gdppc[['n', 'year', 'log_gdppc']], on=['n', 'year'], how='left')

vdem = pd.read_csv('input/kitchen_sink/vdem_corruption.csv')
panel = panel.merge(vdem, on=['n', 'year'], how='left')

accession = panel['n'].map(EU_ACCESSION)
exit_year = panel['n'].map(EU_EXIT).fillna(np.inf)
panel['eu_member'] = ((panel['year'] >= accession) & (panel['year'] < exit_year)).astype(int)
panel['eu_ets'] = (((panel['eu_member'] == 1) & (panel['year'] >= 2005))
                   | (panel['n'].isin(EEA_ETS) & (panel['year'] >= 2008))).astype(int)

###### TIME-INVARIANT #######

cross = pd.read_csv('output/data/kitchen_sink_inputs.csv')[['n', 'pop_share', 'gini', 'ff_assets_1995', 'land_area']]
scc = pd.read_csv('output/data/mitigation_cscc_v_cntfc_2020.csv')[['n'] + [f'scc_mid_spec{s}' for s in range(1, 5)]]
panel = panel.merge(cross, on='n', how='left').merge(scc, on='n', how='left')
panel = panel[~panel['n'].isin(['eu', 'wld'])].sort_values(['n', 'year'])

###### SAVE ################

os.makedirs(os.path.dirname(output_filename), exist_ok=True)
panel.to_csv(output_filename, index=False)
print(panel.groupby('year')[['dolphin_price', 'log_gdppc', 'vdem_corruption']].count().loc[[1990, 2005, 2015, 2020, 2024]])
print(f"Saved {len(panel)} country-years for {panel['n'].nunique()} countries to {output_filename}")
