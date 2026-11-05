import os
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

# Has the size gradient in climate policy changed over time? Section 6a finds that in 2020 larger
# economies (by population share or own CSCC) score higher on non-price support and lower on
# carbon prices. Read as a prisoner's dilemma, a steeper non-price gradient means the subsidy
# game is intensifying (large players act, small ones free ride) and a flatter price gradient
# means the carbon price game is loosening
#
# Each outcome is averaged over four 5-year periods, 2001-2005, 2006-2010, 2011-2015, 2016-2020
# (the EPS ends in 2020; generate_eps_stringency.py panel), and regressed per period on one size or
# damages measure at a time,
#   scc_mid_spec{1-4}   own country SCC (Ricke et al.), $/tCO2 (2020 values, fixed across periods)
#   pop_share           population as a % of world population (2020)
# under three control sets:
#   none
#   gdppc               GDP per capita, constant 2015 US$, period mean (WB NY.GDP.PCAP.KD)
#   kitchen_sink        corruption, democracy, Gini, 1995 fossil assets, land area (regress_kitchen_sink.py,
#                       ~2020 values) plus period-mean GDP per capita
# Outcomes: eps_climate, eps_carbon_price, eps_nonprice (0-6). The same 40 countries in every period.
# Two coefficients per regression, HC1 SEs:
#   slope      EPS points per 1 SD of the size measure (controls standardised, outcome in points).
#              Comparable across periods, so a rising |slope| is a steepening gradient
#   std_coef   outcome also standardised within the period (SDs per SD), the scale of section 6a.
#              The cross-country SD of both outcomes roughly triples from 2001 to 2020, so this
#              can stay flat while the slope grows
# Trend test: country x period panel, outcome on size x period index (0-3) with period fixed effects
# and the controls interacted with period, SEs clustered by country. trend = change in slope per
# 5-year period

output_filename = 'output/regressions/eps_period_gradient.csv'

PERIODS = {'2001_2005': range(2001, 2006), '2006_2010': range(2006, 2011),
           '2011_2015': range(2011, 2016), '2016_2020': range(2016, 2021)}
OUTCOMES = ['eps_climate', 'eps_carbon_price', 'eps_nonprice']
X_COLS = [f'scc_mid_spec{spec}' for spec in range(1, 5)] + ['pop_share']
FIXED = ['vdem_corruption', 'vdem_democracy', 'gini', 'ff_assets_1995', 'land_area']
CONTROLS = {'none': [], 'gdppc': ['gdppc_period'], 'kitchen_sink': FIXED + ['gdppc_period']}
SAMPLES = {
    'full': [],
    'no_us_chn_ind': ['usa', 'chn', 'ind'],
}

###### DATA #######

panel = pd.read_csv('output/data/eps_stringency_panel.csv')
wb = pd.read_csv('input/kitchen_sink/wb_indicators.csv')
gdppc = wb[wb['indicator'] == 'NY.GDP.PCAP.KD'][['n', 'year', 'value']].rename(columns={'value': 'gdppc_period'})
panel = panel.merge(gdppc, on=['n', 'year'], how='left')
panel['period'] = None
for period, years in PERIODS.items():
    panel.loc[panel['year'].isin(years), 'period'] = period
panel = panel.dropna(subset=['period']).groupby(['n', 'period'])[OUTCOMES + ['gdppc_period']].mean().reset_index()
panel['t'] = panel['period'].map({p: i for i, p in enumerate(PERIODS)})

size = pd.read_csv('output/data/mitigation_cscc_v_cntfc_2020.csv')
world_pop = size.loc[size['n'] == 'wld', 'pop'].iloc[0]
size['pop_share'] = 100 * size['pop'] / world_pop
controls = pd.read_csv('output/data/kitchen_sink_inputs.csv')[['n'] + FIXED]
panel = panel.merge(size[['n'] + X_COLS], on='n', how='left').merge(controls, on='n', how='left')

###### REGRESSIONS #######

standardise = lambda x: (x - x.mean()) / x.std()
rows = []
for sample, excluded in SAMPLES.items():
    for x_col in X_COLS:
        for controls_name, control_cols in CONTROLS.items():
            cols = ['n', 't', x_col] + control_cols
            # the same countries in every period: drop any country missing a value in any period
            data = panel[~panel['n'].isin(excluded)][cols + OUTCOMES].dropna()
            data = data[data.groupby('n')['t'].transform('size') == len(PERIODS)]
            for y_col in OUTCOMES:
                for period, t in zip(PERIODS, range(len(PERIODS))):
                    d = data[data['t'] == t]
                    X = sm.add_constant(standardise(d[[x_col] + control_cols]))
                    slope = sm.OLS(d[y_col], X).fit(cov_type='HC1')
                    std = sm.OLS(standardise(d[y_col]), X).fit(cov_type='HC1')
                    rows.append({'sample': sample, 'x_column': x_col, 'controls': controls_name, 'y_column': y_col,
                                 'period': period, 'n': int(slope.nobs), 'y_mean': d[y_col].mean(), 'y_sd': d[y_col].std(),
                                 'slope': slope.params[x_col], 'slope_se': slope.bse[x_col], 'slope_p': slope.pvalues[x_col],
                                 'std_coef': std.params[x_col], 'std_se': std.bse[x_col], 'std_p': std.pvalues[x_col]})
                # trend in the slope: size and controls standardised on the pooled sample (size and fixed
                # controls don't vary over time, so this is the same scale as the per-period slopes)
                d = data.copy()
                d[[x_col] + control_cols] = standardise(d[[x_col] + control_cols])
                terms = ' + '.join([f'{x_col} + {x_col}:t'] + [f'{c} * C(t)' for c in control_cols])
                model = smf.ols(f'{y_col} ~ C(t) + {terms}', data=d).fit(cov_type='cluster',
                                                                       cov_kwds={'groups': d['n']})
                rows.append({'sample': sample, 'x_column': x_col, 'controls': controls_name, 'y_column': y_col,
                             'period': 'trend', 'n': int(model.nobs), 'slope': model.params[f'{x_col}:t'],
                             'slope_se': model.bse[f'{x_col}:t'], 'slope_p': model.pvalues[f'{x_col}:t']})

###### SAVE ################

report = pd.DataFrame(rows)
os.makedirs(os.path.dirname(output_filename), exist_ok=True)
report.to_csv(output_filename, index=False)

star = lambda p: '***' if p < 0.01 else '**' if p < 0.05 else '*' if p < 0.1 else ''
report['cell'] = report['slope'].map('{:+.2f}'.format) + report['slope_p'].map(star)
pd.set_option('display.width', 250)
for sample in SAMPLES:
    print(f"\nSlope (EPS points per SD of size), sample {sample}")
    print(report[report['sample'] == sample].pivot_table(
        index=['y_column', 'controls', 'x_column'], columns='period', values='cell', aggfunc='first').to_string())
print(f"\nSaved CSV to {output_filename}")
