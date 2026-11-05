import os
import numpy as np
import pandas as pd

# Stringency of national ambient air quality standards (AQS), from the WHO Air Quality Standards
# database (3rd edition, Jan 2026; one cross-section, no adoption years). A country gets all the
# benefit of cleaner local air, so this measures general environmental stringency without the
# free-riding problem of climate policy. Used as a control in regress_kitchen_sink.py
#
# Each standard is compared with the WHO guideline for the same pollutant and averaging time:
#   gap = ln(standard / WHO guideline)   (0 = at the guideline, ln 2 = twice the guideline)
# A pollutant's gap is the mean over the averaging times the country sets, and the index is minus
# the mean over pollutants, so higher = stricter. A missing standard ('Data not available', or
# none for that averaging time) is skipped, not counted as lax
#   aqs_local   CO, NO2, PM10, PM2.5: pollutants whose damage is mostly at home
#   aqs_all     also O3 and SO2, which travel further (ozone forms downwind, SO2 causes acid rain)
# aqs_n_local / aqs_n_all count the pollutants with at least one standard

input_filename = 'input/local_air/aqs_clean_v2.3_webpage.csv'
output_filename = 'output/data/local_air_standards.csv'

# WHO guidelines, ug/m3: 2021 AQG levels, plus the earlier guidelines the 2021 update kept for
# NO2 (1h), SO2 (10 min) and CO (15 min, 1h, 8h)
WHO_AQG = {
    ('PM25', 'yr'): 5, ('PM25', '24h'): 15,
    ('PM10', 'yr'): 15, ('PM10', '24h'): 45,
    ('NO2', 'yr'): 10, ('NO2', '24h'): 25, ('NO2', '1h'): 200,
    ('CO', '24h'): 4000, ('CO', '8h'): 10000, ('CO', '1h'): 35000, ('CO', '15m'): 100000,
    ('O3', '8h'): 100,
    ('SO2', '24h'): 40, ('SO2', '10m'): 500,
}
LOCAL = ['CO', 'NO2', 'PM10', 'PM25']
ALL = LOCAL + ['O3', 'SO2']

###### DATA #######

aqs = pd.read_csv(input_filename, encoding='utf-8-sig')
aqs['n'] = aqs['iso3'].str.lower()
aqs = aqs.rename(columns={'pollutant_name': 'pollutant', 'aqs_numeric_ug/m3': 'standard'})
assert set(zip(aqs['pollutant'], aqs['duration'])) == set(WHO_AQG), "averaging times don't match WHO guidelines"

aqs['who_aqg'] = [WHO_AQG[k] for k in zip(aqs['pollutant'], aqs['duration'])]
aqs['gap'] = np.log(aqs['standard'] / aqs['who_aqg'])
gap = aqs.groupby(['n', 'pollutant'])['gap'].mean().unstack('pollutant')

###### INDEX #######

out = pd.DataFrame(index=gap.index)
out['aqs_local'] = -gap[LOCAL].mean(axis=1)
out['aqs_all'] = -gap[ALL].mean(axis=1)
out['aqs_n_local'] = gap[LOCAL].notna().sum(axis=1)
out['aqs_n_all'] = gap[ALL].notna().sum(axis=1)
out = out.join(gap.add_prefix('gap_')).dropna(subset=['aqs_all']).reset_index()

###### SAVE ################

os.makedirs(os.path.dirname(output_filename), exist_ok=True)
out.to_csv(output_filename, index=False)

eps = pd.read_csv('output/data/eps_stringency_2020.csv')[['n', 'eps_local_air', 'eps_climate']]
in_eps = out.merge(eps, on='n')
pd.set_option('display.width', 200)
print(f"WHO AQS: {len(out)} countries with at least one standard, {in_eps['n'].nunique()} of them in the EPS")
print(in_eps.sort_values('aqs_local', ascending=False).drop(columns=['aqs_n_all'])
      .to_string(index=False, float_format='%.2f'))
print("\nRank correlations, EPS countries")
print(in_eps[['aqs_local', 'aqs_all', 'eps_local_air', 'eps_climate']].corr(method='spearman').round(2).to_string())
print(f"\nSaved to {output_filename}")
