
import pandas as pd
import json

output_filename = 'output/data/mitigation_cscc_v_cntfc_2020.csv'

###### COUNTRY LEVEL SCCS #######

scc_df = pd.read_csv('input/country_scc/41558_2018_282_MOESM2_ESM.csv')

# Rename ISO3 to n
scc_df = scc_df.rename(columns={'ISO3': 'n'})

# Filter the data for spec 1 [global scc ~ 400]
filtered_scc = scc_df[(scc_df['run'] == 'bhm_sr') & 
                     (scc_df['dmgfuncpar'] == 'bootstrap') & 
                     (scc_df['climate'] == 'uncertain') & 
                     (scc_df['SSP'] == 'SSP2') & 
                     (scc_df['RCP'] == 'rcp60') & 
                     (scc_df['prtp'] == 2)]


# Select and rename columns
pivoted_df = filtered_scc[['n', '16.7%', '50%', '83.3%']].rename(columns={'16.7%': 'scc_low_spec1', '50%': 'scc_mid_spec1', '83.3%': 'scc_high_spec1'})
pivoted_df['n'] = pivoted_df['n'].apply(lambda x: x.lower())

# Filter the data for spec 2 - high damages [global scc 781]
filtered_scc = scc_df[(scc_df['run'] == 'bhm_lr') & 
                     (scc_df['dmgfuncpar'] == 'bootstrap') & 
                     (scc_df['climate'] == 'uncertain') & 
                     (scc_df['SSP'] == 'SSP2') & 
                     (scc_df['RCP'] == 'rcp60') & 
                     (scc_df['prtp'] == 2)]

# add to pivoted_df
pivoted_df_new = filtered_scc[['n', '16.7%', '50%', '83.3%']].rename(columns={'16.7%': 'scc_low_spec2', '50%': 'scc_mid_spec2', '83.3%': 'scc_high_spec2'})
pivoted_df_new['n'] = pivoted_df_new['n'].apply(lambda x: x.lower())
pivoted_df = pd.merge(pivoted_df, pivoted_df_new, on='n', how='left')

# Filter the data for spec 3 - optimistic [global scc 131]
filtered_scc = scc_df[(scc_df['run'] == 'bhm_richpoor_sr') & 
                     (scc_df['dmgfuncpar'] == 'bootstrap') & 
                     (scc_df['climate'] == 'uncertain') & 
                     (scc_df['SSP'] == 'SSP1') & 
                     (scc_df['RCP'] == 'rcp45') & 
                     (scc_df['prtp'] == 2)]

# add to pivoted_df
pivoted_df_new = filtered_scc[['n', '16.7%', '50%', '83.3%']].rename(columns={'16.7%': 'scc_low_spec3', '50%': 'scc_mid_spec3', '83.3%': 'scc_high_spec3'})
pivoted_df_new['n'] = pivoted_df_new['n'].apply(lambda x: x.lower())
pivoted_df = pd.merge(pivoted_df, pivoted_df_new, on='n', how='left')


# Filter the data for spec 4 - fixed discounting [global scc ~400 but order of countries changes]
filtered_scc = scc_df[(scc_df['run'] == 'bhm_sr') & 
                     (scc_df['dmgfuncpar'] == 'bootstrap') & 
                     (scc_df['climate'] == 'uncertain') & 
                     (scc_df['SSP'] == 'SSP2') & 
                     (scc_df['RCP'] == 'rcp60') & 
                     (scc_df['dr'] == 3)]
# add to pivoted_df
pivoted_df_new = filtered_scc[['n', '16.7%', '50%', '83.3%']].rename(columns={'16.7%': 'scc_low_spec4', '50%': 'scc_mid_spec4', '83.3%': 'scc_high_spec4'})
pivoted_df_new['n'] = pivoted_df_new['n'].apply(lambda x: x.lower())
pivoted_df = pd.merge(pivoted_df, pivoted_df_new, on='n', how='left')

# Rename ISO3 to n
filtered_scc = filtered_scc.rename(columns={'ISO3': 'n'})


# global SCCs
pivoted_df['global_scc_mid_spec1'] = 418
pivoted_df['global_scc_mid_spec2'] = 781
pivoted_df['global_scc_mid_spec3'] = 135
pivoted_df['global_scc_mid_spec4'] = 406



########## MACC parameters ##########

# pull from data/macc_ed_early.csv
# get the a and the d for each country with t=2

macc_df = pd.read_csv('output/data/macc_ed_early.csv')

# Filter for t=2 and sector Total_CO2, then pivot so a and d become separate columns
macc_filtered = macc_df[(macc_df['t'].astype(str).str.strip() == '2') & 
                        (macc_df['sector'] == 'Total_CO2') & 
                        (macc_df['Dim2'].isin(['a', 'd']))]

# Pivot to get 'a' and 'd' as columns
macc_pivoted = macc_filtered.pivot_table(index='n', columns='Dim2', values='Val', aggfunc='first').reset_index()
macc_pivoted.columns.name = None
macc_pivoted.columns = ['n', 'macc_a', 'macc_d']

# Convert n to iso3
macc_pivoted['n'] = macc_pivoted['n'].apply(lambda x: x.strip().lower())
rice_to_iso3 = json.load(open('input/rice_to_iso3.json'))
macc_pivoted['n'] = macc_pivoted['n'].apply(lambda x: rice_to_iso3[x] if x in rice_to_iso3 else x)

# Merge MACC parameters into pivoted_df
pivoted_df = pd.merge(pivoted_df, macc_pivoted, on='n', how='left')


###### POLICY INTENSITY COUNTERFACUTALS #########

# Mapping from full country names to region codes
country_mapping = json.load(open('input/policy_int_to_iso3.json'))

# Read the CSV
policy_int_df = pd.read_csv('output/data/country_year_counterfactual_CO2.csv')

# For each country, calculate the difference from its 2015 value for pol_dens_cum and strng_wght_ind columns
for col in ['pol_dens_cum', 'strng_wght_ind']:
    # Create a mapping of id to its 2015 value
    val_2015 = policy_int_df[policy_int_df['year'] == 2015].set_index('id')[col]
    policy_int_df[f'{col}_diff'] = policy_int_df[col] - policy_int_df['id'].map(val_2015)

# Filter for the year
policy_int_year = policy_int_df[policy_int_df['year'] == 2020]

# Map the country names to codes
policy_int_year['n'] = policy_int_year['id'].map(country_mapping)

# Drop rows where mapping is not found
policy_int_year = policy_int_year.dropna(subset=['n'])

cntfc_cols = ['n', 'pol_dens_cum', 'strng_wght_ind', 
              'pol_dens_cum_diff', 'strng_wght_ind_diff', 
              'pct_diff_2015', 'ci_lower_pct_2015', 'ci_upper_pct_2015', 
              'pct_diff_2015_strng', 'ci_lower_pct_2015_strng', 'ci_upper_pct_2015_strng']

# Merge the pct_diff into the pivoted_df on 'n', rename to policy_den_cntfc
pivoted_df = pd.merge(pivoted_df, policy_int_year[cntfc_cols], on='n', how='left').sort_values('n')

# Rename pct_diff to policy_den_cntfc
pivoted_df.rename(columns={
    'pct_diff_2015': 'policy_den_cntfc',
    'ci_lower_pct_2015': 'policy_den_cntfc_low',
    'ci_upper_pct_2015': 'policy_den_cntfc_high',
    'pct_diff_2015_strng': 'policy_strng_cntfc',
    'ci_lower_pct_2015_strng': 'policy_strng_cntfc_low',
    'ci_upper_pct_2015_strng': 'policy_strng_cntfc_high',
    }, inplace=True)


#### CALCULATE OPTIMAL ABATEMENT FROM COUNTERFACTUAL EMISSIONS

# MB = scc_mid
# MC = a*mu + d*mu^4
# solve for mu and save to a new column called "noncoop_optimal_mu"

import numpy as np
from scipy.optimize import fsolve

def solve_optimal_mu(scc, a, d):
    """
    Solve for mu where MB = MC
    MB = scc 
    MC = a*mu + d*mu^4
    """
    # Check for missing values
    if pd.isna(scc) or pd.isna(a) or pd.isna(d):
        return np.nan
    
    # Define the equation to solve: MC - MB = 0
    def equation(mu):
        return a * mu + d * (mu ** 4) - scc
    
    # Initial guess
    mu_init = 0.5
    
    # Solve using fsolve
    try:
        mu_opt = fsolve(equation, mu_init)[0]
        if mu_opt < 0: 
            return 0 # no negative abatement
        else:
            return mu_opt
    except:
        return np.nan
    
def solve_coop_opt(row, spec):
    return 100*solve_optimal_mu(row[f'global_scc_mid_spec{spec}'], row['macc_a'], row['macc_d'])

def solve_noncoop_opt(row, spec):
    return 100*solve_optimal_mu(row[f'scc_mid_spec{spec}'], row['macc_a'], row['macc_d'])

for spec in range(1,5):
    # Apply the solver to each row
    pivoted_df[f'coop_optimal_mu_spec{spec}'] = pivoted_df.apply(solve_coop_opt, args=(spec,), axis=1)
    pivoted_df[f'noncoop_optimal_mu_spec{spec}'] = pivoted_df.apply(solve_noncoop_opt, args=(spec,), axis=1)


################ OECD CARBON PRICING ################

# read carbon_pricing_oecd.csv
# take REF_AREA, OBS_VALUE filtering for (TIME_PERIOD=2021, STRUCTURE_ID=OECD.CTP.TPS:DSD_NECR@DF_NECRS(1.1))
# rename OBS_VALUE to a column called carbon_price_effective
# merge with pivoted df on REF_AREA = 'n'
carbon_price_df = pd.read_csv('input/carbon_pricing/carbon_pricing_oecd.csv')

# Filter for relevant data
carbon_price_df = carbon_price_df[
    (carbon_price_df['TIME_PERIOD'] == 2021) &
    (carbon_price_df['STRUCTURE_ID'] == 'OECD.CTP.TPS:DSD_NECR@DF_NECRS(1.1)')
]

# Select and rename columns
carbon_price_df = carbon_price_df[['REF_AREA', 'OBS_VALUE']].rename(columns={
    'REF_AREA': 'n',
    'OBS_VALUE': 'carbon_price_effective'
})

# Convert 'n' to lowercase for merging
carbon_price_df['n'] = carbon_price_df['n'].str.lower()

# Remove duplicate country codes, keeping the first entry
carbon_price_df = carbon_price_df.drop_duplicates(subset='n', keep='first')

# Merge with pivoted_df
pivoted_df = pd.merge(pivoted_df, carbon_price_df, on='n', how='left')

################ DOLPHIN CARBON PRICING ################

# read carbon_pricing_dolphin.csv
# take jurisdiction, ecp_all_jurGHG_usd_k, ecp_tax_jurCO2_usd_k filtering for (year=2021, country in our list)
carbon_price_df_dolphin = pd.read_csv('input/carbon_pricing/carbon_pricing_dolphin.csv')

dolphin_to_iso3 = json.load(open('input/dolphin_to_iso3.json'))

# Filter for relevant data
carbon_price_df_dolphin = carbon_price_df_dolphin[
    (carbon_price_df_dolphin['year'] == 2020) &
    (carbon_price_df_dolphin['jurisdiction'].isin(dolphin_to_iso3.keys()))
]

# Select and rename columns
carbon_price_df_dolphin = carbon_price_df_dolphin[['jurisdiction', 'ecp_all_jurGHG_usd_k', 'ecp_tax_jurCO2_usd_k']].rename(columns={
    'jurisdiction': 'n',
    'ecp_all_jurGHG_usd_k': 'carbon_price_dolphin_ghg',
    'ecp_tax_jurCO2_usd_k': 'carbon_price_dolphin_co2'
})

# Convert jurisdictions to iso3
carbon_price_df_dolphin['n'] = carbon_price_df_dolphin['n'].map(dolphin_to_iso3).str.lower()

# Merge with pivoted_df
pivoted_df = pd.merge(pivoted_df, carbon_price_df_dolphin, on='n', how='left')

# create versions with no zeros
for carbon_price in ['carbon_price_effective', 'carbon_price_dolphin_ghg', 'carbon_price_dolphin_co2']:
    # set 0 to NA in new column
    pivoted_df[f"{carbon_price}_no_zeros"] = pivoted_df[carbon_price].apply(lambda x: np.nan if x == 0 else x)

################ World Bank Controls ################

wb_df = pd.read_csv('input/wb_controls/pop_gdp_2015_2025.csv')

# filter for year = 2015
wb_df = wb_df[wb_df['year'] == 2020]
wb_df = wb_df[["country", "WB_WDI_SP_POP_TOTL", "WB_WDI_NY_GDP_PCAP_CD"]]


# rename columns
wb_df.rename(columns={
    'country': 'n',
    'WB_WDI_SP_POP_TOTL': 'pop',
    'WB_WDI_NY_GDP_PCAP_CD': 'gdppc'
}, inplace=True)

wb_df['log_gdppc'] = np.log(wb_df['gdppc'])
wb_df['log_pop'] = np.log(wb_df['pop'])
wb_df['n'] = wb_df['n'].str.lower()

pivoted_df = pd.merge(pivoted_df, wb_df, on='n', how='left')

# add per capita measures
for spec in ["1", "2", "3", "4"]:
    pivoted_df[f'scc_mid_spec{spec}_pc'] = pivoted_df[f'scc_mid_spec{spec}'] / pivoted_df['pop']

################ EU AGGREGATE PSEUDO-ROW ################

# Treat the EU as a single player, saved as row n = 'eu'.
# Members are the EU27 countries with both a policy counterfactual and MACC parameters.
#   damages:  bloc SCC = sum of member SCCs (sum of medians, so approximate)
#   costs:    horizontal sum of the member MAC curves. At a common carbon price each member
#             abates until its own MAC hits that price (lowest cost abatement happens first),
#             and bloc mu is the emissions-weighted mean of member mu
#   realized: total avoided emissions over total emissions
EU_CODE = 'eu'
EU27 = ['aut', 'bel', 'bgr', 'hrv', 'cyp', 'cze', 'dnk', 'est', 'fin',
        'fra', 'deu', 'grc', 'hun', 'irl', 'ita', 'lva', 'ltu', 'lux',
        'mlt', 'nld', 'pol', 'prt', 'rou', 'svk', 'svn', 'esp', 'swe']

eu_df = pd.merge(pivoted_df[pivoted_df['n'].isin(EU27)],
                 policy_int_year[['n', 'CO2_mt', 'co2_cntfc_2015']], on='n', how='left')
eu_df = eu_df[eu_df['policy_den_cntfc'].notna() & (eu_df['macc_a'] > 0)]
print(f"EU aggregate: {len(eu_df)} members, missing {sorted(set(EU27) - set(eu_df['n']))}")

# BAU (counterfactual) emission shares weight the cost side, actual emissions weight the
# realized side because the counterfactual columns are percentages of actual emissions
bau_share = eu_df['co2_cntfc_2015'] / eu_df['co2_cntfc_2015'].sum()
actual_share = eu_df['CO2_mt'] / eu_df['CO2_mt'].sum()

eu_row = {'n': EU_CODE}

for spec in range(1, 5):
    eu_scc = eu_df[f'scc_mid_spec{spec}'].sum()
    global_scc = eu_df[f'global_scc_mid_spec{spec}'].iloc[0]
    eu_row[f'scc_mid_spec{spec}'] = eu_scc
    eu_row[f'global_scc_mid_spec{spec}'] = global_scc
    # every member abates up to the common price, so no aggregate curve is needed here
    for name, price in [('noncoop', eu_scc), ('coop', global_scc)]:
        member_mu = eu_df.apply(lambda row: solve_optimal_mu(price, row['macc_a'], row['macc_d']), axis=1)
        eu_row[f'{name}_optimal_mu_spec{spec}'] = 100 * (bau_share * member_mu).sum()

# The aggregate curve is not exactly a*mu + d*mu^4. These match it in both limits (mu -> 0,
# where the linear term dominates, and large mu) and stay within 5% of it in between.
# Only used to draw the curve, the optimal mus above are exact.
eu_row['macc_a'] = 1 / (bau_share / eu_df['macc_a']).sum()
eu_row['macc_d'] = (bau_share * eu_df['macc_d'] ** -0.25).sum() ** -4

# The confidence bounds come from one regression coefficient shared by all countries,
# so the member bounds move together and can be averaged like the point estimate
for col in ['policy_den_cntfc', 'policy_den_cntfc_low', 'policy_den_cntfc_high',
            'policy_strng_cntfc', 'policy_strng_cntfc_low', 'policy_strng_cntfc_high']:
    eu_row[col] = (actual_share * eu_df[col]).sum()

eu_row['pop'] = eu_df['pop'].sum()
eu_row['gdppc'] = (eu_df['gdppc'] * eu_df['pop']).sum() / eu_df['pop'].sum()
eu_row['log_gdppc'] = np.log(eu_row['gdppc'])
eu_row['log_pop'] = np.log(eu_row['pop'])
for spec in ["1", "2", "3", "4"]:
    eu_row[f'scc_mid_spec{spec}_pc'] = eu_row[f'scc_mid_spec{spec}'] / eu_row['pop']

pivoted_df = pd.concat([pivoted_df, pd.DataFrame([eu_row])], ignore_index=True)

################ OPTIMAL RANGES AND TESTS ################

# add column for highest and lowest coop and noncoop optimal mu across specs
# (done after the EU row is appended so it gets a range and test result too)
pivoted_df['coop_optimal_mu_max'] = pivoted_df[[f'coop_optimal_mu_spec{spec}' for spec in range(1,5)]].max(axis=1)
pivoted_df['coop_optimal_mu_min'] = pivoted_df[[f'coop_optimal_mu_spec{spec}' for spec in range(1,5)]].min(axis=1)
pivoted_df['noncoop_optimal_mu_max'] = pivoted_df[[f'noncoop_optimal_mu_spec{spec}' for spec in range(1,5)]].max(axis=1)
pivoted_df['noncoop_optimal_mu_min'] = pivoted_df[[f'noncoop_optimal_mu_spec{spec}' for spec in range(1,5)]].min(axis=1)

# test the null that the counterfactual is in each range, treating the range bounds as fixed
# reject when the 95% CI is entirely outside the range. Each side is a 2.5% one-sided test,
# so this is conservative at p<0.05
for cntfc in ['policy_den_cntfc', 'policy_strng_cntfc']:
    for name in ['noncoop', 'coop']:
        test_cols = [f'{cntfc}_low', f'{cntfc}_high', f'{name}_optimal_mu_min', f'{name}_optimal_mu_max']
        result = pd.Series('not_rejected', index=pivoted_df.index, dtype=object)
        result[pivoted_df[f'{cntfc}_high'] < pivoted_df[f'{name}_optimal_mu_min']] = 'below'
        result[pivoted_df[f'{cntfc}_low'] > pivoted_df[f'{name}_optimal_mu_max']] = 'above'
        result[pivoted_df[test_cols].isna().any(axis=1)] = np.nan
        pivoted_df[f'{cntfc}_vs_{name}_range'] = result

################ MONTE CARLO TEST WITH UNCERTAIN BOUNDS ################

# Same null as above, but the range bounds are uncertain too. Each draw takes
#   - an SCC for every spec from a distribution fitted to its 16.7 / 50 / 83.3% quantiles,
#     pushed through the MAC curve to get that draw's optimal mu range (min and max over specs)
#   - a counterfactual from its 95% CI, independent of the SCC
# and the null is rejected when the counterfactual is inside the range in under 5% of draws.

from scipy.stats import norm

N_DRAWS = 50_000
# True: one quantile draw is shared by all specs (and all countries), so the specs differ only
# in how they map the same underlying climate / damage uncertainty to an SCC.
# False: every spec gets its own draw, which widens the range and makes the test more conservative.
SHARED_SCC_DRAW_ACROSS_SPECS = True

Z_SCC = norm.ppf(0.833)
Z_CI = norm.ppf(0.975)
rng = np.random.default_rng(0)
z_scc = rng.standard_normal((4, N_DRAWS))
if SHARED_SCC_DRAW_ACROSS_SPECS:
    z_scc = np.tile(z_scc[0], (4, 1))
z_cntfc = rng.standard_normal(N_DRAWS)

def draw_scc(low, mid, high, z):
    """
    Draws from a shifted lognormal passing exactly through the three SCC quantiles.
    A plain lognormal cannot be used because many country SCCs are negative, so the
    distribution is shifted, and mirrored when the quantiles are left skewed.
    """
    up, down = high - mid, mid - low
    log_ratio = np.log(up / down)
    if abs(log_ratio) < 1e-6:
        return mid + up / Z_SCC * z  # symmetric quantiles, the lognormal limit is a normal
    sign = np.sign(log_ratio)
    sigma = abs(log_ratio) / Z_SCC
    scale = min(up, down) / (1 - np.exp(-sigma * Z_SCC))
    return mid + sign * scale * (np.exp(sign * sigma * z) - 1)

def draw_cntfc(low, mid, high, z):
    # split normal through the point estimate and both ends of the 95% CI
    return mid + z * np.where(z > 0, high - mid, mid - low) / Z_CI

def solve_optimal_mu_vec(scc, a, d):
    """Vectorized solve_optimal_mu. Newton from above the root, where MC is increasing and convex."""
    scc_pos = np.clip(scc, 0, None)
    mu = np.minimum(scc_pos / a, (scc_pos / d) ** 0.25)
    for _ in range(30):
        mu = mu - (a * mu + d * mu ** 4 - scc_pos) / (a + 4 * d * mu ** 3)
    return mu  # zero wherever scc <= 0, no negative abatement

def optimal_mu_draws(price, members):
    # members is a list of (a, d, weight). A country is one member, the EU is its member states
    return 100 * sum(w * solve_optimal_mu_vec(price, a, d) for a, d, w in members)

# The global SCC keeps its hardcoded median and takes its spread from the WLD row
wld = pivoted_df[pivoted_df['n'] == 'wld'].iloc[0]
global_scc_draws = {
    spec: wld[f'global_scc_mid_spec{spec}'] / wld[f'scc_mid_spec{spec}'] * draw_scc(
        wld[f'scc_low_spec{spec}'], wld[f'scc_mid_spec{spec}'], wld[f'scc_high_spec{spec}'], z_scc[spec - 1])
    for spec in range(1, 5)
}

def own_scc_draws(row, spec):
    return draw_scc(row[f'scc_low_spec{spec}'], row[f'scc_mid_spec{spec}'], row[f'scc_high_spec{spec}'], z_scc[spec - 1])

eu_members = list(zip(eu_df['macc_a'], eu_df['macc_d'], bau_share))

mc_results = {}
for idx, row in pivoted_df.iterrows():
    is_eu = row['n'] == EU_CODE
    if pd.isna(row['policy_den_cntfc']) or not (is_eu or (row['macc_a'] > 0 and row['macc_d'] > 0)):
        continue
    members = eu_members if is_eu else [(row['macc_a'], row['macc_d'], 1)]

    mu_draws = {'noncoop': [], 'coop': []}
    for spec in range(1, 5):
        if is_eu:
            # bloc SCC = sum of member SCCs, as in the point estimate
            own_scc = sum(own_scc_draws(member, spec) for _, member in eu_df.iterrows())
        else:
            own_scc = own_scc_draws(row, spec)
        mu_draws['noncoop'].append(optimal_mu_draws(own_scc, members))
        mu_draws['coop'].append(optimal_mu_draws(global_scc_draws[spec], members))

    mc_results[idx] = {}
    for cntfc in ['policy_den_cntfc', 'policy_strng_cntfc']:
        if pd.isna(row[cntfc]):
            continue
        cntfc_draws = draw_cntfc(row[f'{cntfc}_low'], row[cntfc], row[f'{cntfc}_high'], z_cntfc)
        for name in ['noncoop', 'coop']:
            p_below = (cntfc_draws < np.min(mu_draws[name], axis=0)).mean()
            p_above = (cntfc_draws > np.max(mu_draws[name], axis=0)).mean()
            if 1 - p_below - p_above >= 0.05:
                result = 'not_rejected'
            else:
                result = 'below' if p_below > p_above else 'above'
            mc_results[idx][f'{cntfc}_p_below_{name}_range'] = p_below
            mc_results[idx][f'{cntfc}_p_above_{name}_range'] = p_above
            mc_results[idx][f'{cntfc}_vs_{name}_range_mc'] = result

pivoted_df = pivoted_df.join(pd.DataFrame.from_dict(mc_results, orient='index'))

################ SAVE ################

pivoted_df.to_csv(output_filename, index=False)

print(f"Transformation complete. Output saved to {output_filename}")
