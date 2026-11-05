import os
import numpy as np
import pandas as pd
import statsmodels.api as sm

# Is the EPS result an artifact of aggregation? The same own CSCC and population regressions as
# regress_eps_price_split.py, run on every piece of the OECD EPS: the headline and climate
# aggregates, the three official pillars and all 13 instruments (generate_eps_stringency.py)
#   scc_mid_spec{1-4}   own country SCC (Ricke et al.), $/tCO2
#   pop_share           population as a % of world population (2020)
# Controls: none, GDP per capita, kitchen sink (regress_kitchen_sink.py). Robust (HC1) SEs.
#
# Two outputs:
#   1. eps_subindex_regressions.csv: standardised coefficients (SD of outcome per SD of
#      regressor, both standardised within the estimation sample), comparable across pieces
#   2. eps_subindex_decomposition.csv: an aggregate is a fixed weighted sum of instruments, so
#      on a common sample its unstandardised OLS slope is exactly sum_k w_k * b_k. Each row is
#      one instrument's contribution w_k * b_k, so offsetting pieces show up directly

reg_filename = 'output/regressions/eps_subindex_regressions.csv'
decomp_filename = 'output/regressions/eps_subindex_decomposition.csv'

# official EPS hierarchy, as in generate_eps_stringency.py
PILLARS = {
    'market': {'TAXCO2': 1, 'TAXNOX': 1, 'TAXSOX': 1, 'TAXDIESEL': 1, 'TRADESCH_CO2': 1, 'TRADESCH_RENEW': 1},
    'nonmkt': {'ELV_NOX': 1, 'ELV_SOX': 1, 'ELV_PM': 1, 'ELV_DIESELSO': 1},
    'techsup': {'RD_SUB': 2, 'FIT_SOLAR': 1, 'FIT_WIND': 1},
}
INSTRUMENTS = [k for w in PILLARS.values() for k in w]
CLIMATE = ['TAXCO2', 'TRADESCH_CO2', 'TRADESCH_RENEW', 'RD_SUB', 'FIT_SOLAR', 'FIT_WIND']

def aggregate_weights(kept):
    """Instrument weights in an EPS-style index built from the instruments in `kept`."""
    pillars = {p: {k: w for k, w in ws.items() if k in kept} for p, ws in PILLARS.items()}
    pillars = {p: ws for p, ws in pillars.items() if ws}
    return {k: w / sum(ws.values()) / len(pillars) for ws in pillars.values() for k, w in ws.items()}

AGGREGATES = {'eps': aggregate_weights(INSTRUMENTS), 'eps_climate': aggregate_weights(CLIMATE)}

OUTCOMES = ['eps', 'eps_climate', 'eps_carbon_price', 'eps_nonprice'] + \
           [f'pillar_{p}' for p in PILLARS] + INSTRUMENTS
X_COLS = [f'scc_mid_spec{spec}' for spec in range(1, 5)] + ['pop_share']
KITCHEN_SINK = ['vdem_corruption', 'vdem_democracy', 'gini', 'ff_assets_1995', 'land_area', 'gdppc']
CONTROLS = {'none': [], 'gdppc': ['gdppc'], 'kitchen_sink': KITCHEN_SINK}
SAMPLES = {
    'full': [],
    'no_us_chn_ind': ['usa', 'chn', 'ind'],
}

###### DATA #######

df = pd.read_csv('output/data/mitigation_cscc_v_cntfc_2020.csv')
world_pop = df.loc[df['n'] == 'wld', 'pop'].iloc[0]
df['pop_share'] = 100 * df['pop'] / world_pop
df = df[['n'] + X_COLS]

controls = pd.read_csv('output/data/kitchen_sink_inputs.csv')[['n'] + KITCHEN_SINK]
df = df.merge(controls, on='n', how='left')

eps_df = pd.read_csv('output/data/eps_stringency_2020.csv')
for p, ws in PILLARS.items():
    eps_df[f'pillar_{p}'] = sum(eps_df[k] * w for k, w in ws.items()) / sum(ws.values())
for agg, ws in AGGREGATES.items():
    assert np.allclose(eps_df[agg], sum(eps_df[k] * w for k, w in ws.items())), f"{agg} weights are wrong"
df = eps_df[['n'] + OUTCOMES].merge(df, on='n', how='left')

###### REGRESSIONS #######

standardise = lambda x: (x - x.mean()) / x.std()

def fit(y, X):
    return sm.OLS(y, sm.add_constant(X)).fit(cov_type='HC1')

reg_rows, decomp_rows = [], []
for x_col in X_COLS:
    for controls_name, control_cols in CONTROLS.items():
        for sample, excluded in SAMPLES.items():
            # one common sample per regressor/controls/sample, so pieces are comparable and the
            # decomposition is exact (EPS outcomes have no missing values)
            data = df[~df['n'].isin(excluded)][['n', x_col] + control_cols + OUTCOMES].dropna()
            Xs = standardise(data[[x_col] + control_cols])
            Xr = data[[x_col] + control_cols]
            key = {'x_column': x_col, 'controls': controls_name, 'sample': sample, 'n': len(data)}

            raw = {}
            for y_col in OUTCOMES:
                if data[y_col].std() == 0:
                    continue
                m = fit(standardise(data[y_col]), Xs)
                reg_rows.append({'y_column': y_col, **key, 'std_coef': m.params[x_col],
                                 'robust_se': m.bse[x_col], 'p_value': m.pvalues[x_col],
                                 'r_squared': m.rsquared})
                raw[y_col] = fit(data[y_col], Xr)

            for agg, ws in AGGREGATES.items():
                total = raw[agg].params[x_col]
                parts = {k: w * raw[k].params[x_col] if k in raw else 0.0 for k, w in ws.items()}
                assert np.isclose(total, sum(parts.values())), f"{agg} decomposition doesn't add up"
                for k, c in parts.items():
                    decomp_rows.append({'aggregate': agg, 'instrument': k, **key, 'weight': ws[k],
                                        'contribution': c, 'share_of_total': c / total,
                                        'aggregate_slope': total})

###### SAVE ################

reg = pd.DataFrame(reg_rows)
decomp = pd.DataFrame(decomp_rows)
os.makedirs(os.path.dirname(reg_filename), exist_ok=True)
reg.to_csv(reg_filename, index=False)
decomp.to_csv(decomp_filename, index=False)

pd.set_option('display.width', 250)
pd.set_option('display.max_rows', 500)
for sample in SAMPLES:
    for controls_name in CONTROLS:
        sub = reg[(reg['sample'] == sample) & (reg['controls'] == controls_name)]
        coef = sub.pivot(index='y_column', columns='x_column', values='std_coef')
        p = sub.pivot(index='y_column', columns='x_column', values='p_value')
        stars = p.map(lambda v: '***' if v < 0.01 else '**' if v < 0.05 else '*' if v < 0.1 else '')
        table = coef.map('{:+.2f}'.format) + stars
        print(f"\nStandardised coefficients, sample={sample}, controls={controls_name}")
        print(table.loc[OUTCOMES, X_COLS].to_string())
print(f"\nSaved CSVs to {reg_filename} and {decomp_filename}")
