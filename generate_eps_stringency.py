import pandas as pd
import numpy as np

# Cross-country climate policy stringency in 2020 from the OECD Environmental Policy Stringency
# (EPS) index. The headline EPS covers local air pollution too, so the specs below rebuild it
# from its instruments, progressively dropping everything that isn't directly carbon policy
#
# Official EPS structure (all instruments scored 0-6):
#   EPS      = mean of 3 pillars
#   market   = TAXCO2, TAXNOX, TAXSOX, TAXDIESEL, TRADESCH_CO2, TRADESCH_RENEW   (1/6 each)
#   nonmkt   = ELV_NOX, ELV_SOX, ELV_PM, ELV_DIESELSO                             (1/4 each)
#   techsup  = RD_SUB (1/2), FIT_SOLAR (1/4), FIT_WIND (1/4)
# A spec keeps this hierarchy: pillars stay equally weighted, instruments keep their relative
# weights within a pillar, and a pillar with no instruments left drops out

input_filename = 'input/policy_stringency/oecd_eps.csv'
output_filename = 'output/data/eps_stringency_2020.csv'
YEAR = 2020
# multi-year averages for sensitivity checks; the EPS ends in 2020
MEAN_PERIODS = {'2015_2020': range(2015, 2021), '2010_2020': range(2010, 2021)}
mean_filename = 'output/data/eps_stringency_{}_mean.csv'

PILLARS = {
    'market': {'TAXCO2': 1, 'TAXNOX': 1, 'TAXSOX': 1, 'TAXDIESEL': 1, 'TRADESCH_CO2': 1, 'TRADESCH_RENEW': 1},
    'nonmkt': {'ELV_NOX': 1, 'ELV_SOX': 1, 'ELV_PM': 1, 'ELV_DIESELSO': 1},
    'techsup': {'RD_SUB': 2, 'FIT_SOLAR': 1, 'FIT_WIND': 1},
}

AIR_POLLUTION = ['TAXNOX', 'TAXSOX', 'ELV_NOX', 'ELV_SOX', 'ELV_PM', 'ELV_DIESELSO']

# spec -> instruments dropped. Specs 1-4 each drop more than the last
SPECS = {
    # 1. headline EPS, everything
    'eps': [],
    # 2. drop local air pollutant policies (NOx/SOx taxes, NOx/SOx/PM/diesel sulphur limits),
    #    which removes the whole non-market pillar
    'eps_no_air': AIR_POLLUTION,
    # 3. also drop the diesel tax, a fuel excise rather than a carbon price. What's left is all
    #    climate policy: carbon pricing, renewable trading schemes, renewable support, low-carbon R&D
    'eps_climate': AIR_POLLUTION + ['TAXDIESEL'],
    # 4. also drop technology support and renewable trading schemes, leaving only explicit carbon
    #    prices (CO2 tax and CO2 emissions trading)
    'eps_carbon_price': AIR_POLLUTION + ['TAXDIESEL', 'TRADESCH_RENEW', 'RD_SUB', 'FIT_SOLAR', 'FIT_WIND'],
    # 5. the complement of 4 within eps_climate: drop the carbon prices instead, leaving non-price
    #    support (renewable trading schemes, low-carbon R&D, solar and wind support)
    'eps_nonprice': AIR_POLLUTION + ['TAXDIESEL', 'TAXCO2', 'TRADESCH_CO2'],
}

###### DATA #######

raw = pd.read_csv(input_filename)
raw['REF_AREA'] = raw['REF_AREA'].str.lower()

def instruments(years):
    df = raw[raw['TIME_PERIOD'].isin(years)].pivot_table(index=['REF_AREA', 'TIME_PERIOD'], columns='CLIM_POL',
                                                         values='OBS_VALUE')
    df.index.names = ['n', 'year']
    return df

eps_df = instruments([YEAR]).droplevel('year')

###### SPECS #######

def stringency(df, dropped):
    pillar_scores = []
    for weights in PILLARS.values():
        kept = {k: w for k, w in weights.items() if k not in dropped}
        if kept:
            pillar_scores.append(sum(df[k] * w for k, w in kept.items()) / sum(kept.values()))
    return sum(pillar_scores) / len(pillar_scores)


INSTRUMENTS = [k for weights in PILLARS.values() for k in weights]

def build(df):
    out = pd.DataFrame(index=df.index)
    for spec, dropped in SPECS.items():
        out[spec] = stringency(df, dropped)
    # rebuilding the headline index should reproduce the official one
    assert np.allclose(out['eps'], df['EPS']), "EPS weights don't reproduce the official index"
    # keep the instruments so other groupings can be built downstream
    return out.join(df[INSTRUMENTS])

out = build(eps_df).reset_index()

# country means over each period of each year's specs and instruments
mean_outs = {}
for period, years in MEAN_PERIODS.items():
    yearly = instruments(years)
    mean_out = build(yearly).groupby('n').mean()
    mean_out.insert(0, 'n_years', yearly.groupby('n').size())
    mean_outs[period] = mean_out.reset_index()

###### SAVE ################

out.to_csv(output_filename, index=False)
for period, mean_out in mean_outs.items():
    mean_out.to_csv(mean_filename.format(period), index=False)

pd.set_option('display.width', 200)
print(f"OECD EPS {YEAR}: {len(out)} countries")
print(out[['n'] + list(SPECS)].sort_values('eps', ascending=False).to_string(index=False, float_format='%.2f'))
print("\nCorrelation between specs")
print(out[list(SPECS)].corr().round(2).to_string())
print(f"\nSaved to {output_filename} and " + ', '.join(mean_filename.format(p) for p in MEAN_PERIODS))
