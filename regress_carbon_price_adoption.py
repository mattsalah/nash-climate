import os
import numpy as np
import pandas as pd
import statsmodels.api as sm

# When does a country first price carbon? Discrete-time hazard model on the country-year panel
# (generate_policy_panel.py): each country is at risk from 1990 until the first year with a
# positive Dolphin & Merkle price (the event year is kept, later years dropped). A complementary
# log-log GLM is the discrete-time analogue of a Cox proportional hazards model, so exp(coef) is a
# hazard ratio. Standard errors are clustered by country
#
# Regressors (standardised; time-invariant ones across countries, time-varying ones across
# country-years in the risk set):
#   slim   own CSCC (spec 1-4), log GDP per capita (t-1), V-Dem corruption (t-1)
#   full   slim + Gini, 1995 fossil assets, land area, population share
# plus a cubic in calendar time (the baseline hazard) and an EU ETS coverage dummy
#
# 19 of the 47 adoptions are EU members in 2005, which came with the EU ETS rather than a national
# decision, so samples drop ever-EU members:
#   all         all countries, with the EU ETS dummy
#   non_eu      excluding EU members (the UK included)
#   non_eu_no_us_chn_ind

output_filename = 'output/regressions/carbon_price_adoption_hazard.csv'

EVER_EU = ['bel', 'fra', 'deu', 'ita', 'lux', 'nld', 'dnk', 'irl', 'gbr', 'grc', 'esp', 'prt', 'aut',
           'fin', 'swe', 'cyp', 'cze', 'est', 'hun', 'lva', 'ltu', 'mlt', 'pol', 'svk', 'svn', 'bgr',
           'rou', 'hrv']
TIME_VARYING = ['log_gdppc_lag', 'vdem_corruption_lag']
FULL_EXTRA = ['gini', 'ff_assets_1995', 'land_area', 'pop_share']
SAMPLES = {
    'all': [],
    'non_eu': EVER_EU,
    'non_eu_no_us_chn_ind': EVER_EU + ['usa', 'chn', 'ind'],
}
START_YEAR, END_YEAR = 1990, 2024

###### DATA #######

panel = pd.read_csv('output/data/policy_panel.csv').sort_values(['n', 'year'])
panel = panel[panel['dolphin_price'].notna()]
for col in ['log_gdppc', 'vdem_corruption']:
    panel[f'{col}_lag'] = panel.groupby('n')[col].shift(1)

# risk set: years up to and including the first priced year
panel['ever_priced_before'] = panel.groupby('n')['priced'].transform(lambda p: p.shift(1, fill_value=0).cummax())
risk = panel[panel['year'].between(START_YEAR, END_YEAR) & (panel['ever_priced_before'] == 0)].copy()
risk['event'] = risk['priced']

t = (risk['year'] - 2007) / 10
risk['t1'], risk['t2'], risk['t3'] = t, t ** 2, t ** 3

###### REGRESSIONS #######

rows = []
for spec_num in range(1, 5):
    scc = f'scc_mid_spec{spec_num}'
    for covariates, extra in [('slim', []), ('full', FULL_EXTRA)]:
        for sample, excluded in SAMPLES.items():
            invariant = [scc] + extra
            cols = ['n', 'year', 'event', 'eu_ets', 't1', 't2', 't3'] + invariant + TIME_VARYING
            data = risk[~risk['n'].isin(excluded)][cols].dropna().copy()
            countries = data.groupby('n')[invariant].first()
            for c in invariant:
                data[c] = (data[c] - countries[c].mean()) / countries[c].std()
            for c in TIME_VARYING:
                data[c] = (data[c] - data[c].mean()) / data[c].std()

            X_cols = invariant + TIME_VARYING + ['t1', 't2', 't3']
            if data['eu_ets'].any():
                X_cols.append('eu_ets')
            X = sm.add_constant(data[X_cols])
            model = sm.GLM(data['event'], X, family=sm.families.Binomial(link=sm.families.links.CLogLog()))
            result = model.fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(data['n'])[0]})
            for x_col in invariant + TIME_VARYING:
                rows.append({
                    'scc_spec': spec_num, 'covariates': covariates, 'sample': sample,
                    'x_column': 'scc' if x_col == scc else x_col,
                    'coef': result.params[x_col], 'robust_se': result.bse[x_col], 'p_value': result.pvalues[x_col],
                    'hazard_ratio': np.exp(result.params[x_col]),
                    'n_country_years': int(result.nobs), 'n_countries': data['n'].nunique(),
                    'n_events': int(data['event'].sum()),
                })

###### SAVE ################

report = pd.DataFrame(rows)
os.makedirs(os.path.dirname(output_filename), exist_ok=True)
report.to_csv(output_filename, index=False)

pd.set_option('display.width', 250)
pd.set_option('display.max_rows', 500)
print(report[report['scc_spec'] == 2].to_string(index=False, float_format='{:.3g}'.format))
print(f"\nSaved CSV to {output_filename}")
