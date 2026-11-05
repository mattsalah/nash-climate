import pandas as pd
import numpy as np
import json

output_filename = 'output/data/lobbymap_country_scores.csv'

###### ORGANIZATION SCORES #######

# One row per company / industry association, from fetch_lobbymap.py.
#   score:       LobbyMap organization score, 0-100, higher = more Paris-aligned (pro-climate)
#   band:        letter grade, 5-point bins of score (A+ >= 95 ... E- >= 25, F < 25)
#   engagement:  engagement intensity, 0-100, how actively the org lobbies on climate policy
lobby_df = pd.read_csv('input/lobbymap/lobbymap_scores.csv')
lobby_df['score'] = pd.to_numeric(lobby_df['score'], errors='coerce')
lobby_df['engagement'] = pd.to_numeric(lobby_df['engagement'], errors='coerce')

# Profile page has no headquarters listed
lobby_df.loc[lobby_df['name'] == 'Braskem', 'headquarters'] = 'Sao Paulo, Brazil'

###### MATCH TO COUNTRY #######

# Assume each organization lobbies only where it is headquartered
with open('input/lobbymap/lobbymap_country_to_iso3.json') as f:
    country_to_iso3 = json.load(f)

lobby_df['hq_country'] = lobby_df['headquarters'].str.split(',').str[-1].str.strip()
lobby_df['n'] = lobby_df['hq_country'].map(country_to_iso3)
unmatched = lobby_df.loc[lobby_df['n'].isna(), 'hq_country'].unique()
assert len(unmatched) == 0, f"No iso3 for {unmatched}"

EU_CODE = 'eu'
EU27 = ['aut', 'bel', 'bgr', 'hrv', 'cyp', 'cze', 'dnk', 'est', 'fin',
        'fra', 'deu', 'grc', 'hun', 'irl', 'ita', 'lva', 'ltu', 'lux',
        'mlt', 'nld', 'pol', 'prt', 'rou', 'svk', 'svn', 'esp', 'swe']

# Brussels-based European associations (BusinessEurope, Cefic, ACEA, ...) lobby the EU, not Belgium
eu_level = (lobby_df['area'] == 'influencer') & (lobby_df['n'] == 'bel') & (lobby_df['region'] == 'Europe')
lobby_df.loc[eu_level, 'n'] = EU_CODE

# Global associations (IIF, Ipieca, World Steel, ...) don't lobby any one country
global_level = (lobby_df['area'] == 'influencer') & (lobby_df['region'] == 'Global')
lobby_df = lobby_df[~global_level]

# Can't weight orgs that are unscored or have no engagement intensity
scored_df = lobby_df[lobby_df['score'].notna() & lobby_df['engagement'].notna()]
print(f"LobbyMap: {len(scored_df)} scored orgs used, dropped {global_level.sum()} global associations "
      f"and {len(lobby_df) - len(scored_df)} orgs without a score or engagement intensity")

###### COUNTRY SCORES #######

def score_to_band(score):
    bands = ['E-', 'E', 'E+', 'D-', 'D', 'D+', 'C-', 'C', 'C+', 'B-', 'B', 'B+', 'A-', 'A', 'A+']
    if np.isnan(score):
        return np.nan
    if score < 25:
        return 'F'
    return bands[min(int((score - 25) // 5), len(bands) - 1)]


def aggregate(group):
    weights = group['engagement']
    return pd.Series({
        # engagement-weighted, so orgs that lobby harder count for more
        'lobby_score': np.average(group['score'], weights=weights) if weights.sum() > 0 else np.nan,
        'lobby_score_unweighted': group['score'].mean(),
        'lobby_engagement_total': weights.sum(),
        'lobby_engagement_mean': weights.mean(),
        'lobby_n_orgs': len(group),
        'lobby_n_companies': (group['area'] == 'company').sum(),
        'lobby_n_associations': (group['area'] == 'influencer').sum(),
    })


country_df = scored_df.groupby('n')[['score', 'engagement', 'area']].apply(aggregate).reset_index()

# EU composite, matching the 'eu' row in generate_cscc_vs_cntfc.py: EU-level associations
# plus every org headquartered in a member state
eu_row = aggregate(scored_df[scored_df['n'].isin(EU27 + [EU_CODE])])
eu_row['n'] = EU_CODE
country_df = pd.concat([country_df[country_df['n'] != EU_CODE], pd.DataFrame([eu_row])], ignore_index=True)

country_df['lobby_grade'] = country_df['lobby_score'].apply(score_to_band)
for col in ['lobby_n_orgs', 'lobby_n_companies', 'lobby_n_associations']:
    country_df[col] = country_df[col].astype(int)
country_df = country_df.sort_values('lobby_engagement_total', ascending=False)

###### SAVE ################

country_df.to_csv(output_filename, index=False)
print(country_df.to_string(index=False, float_format='%.1f'))
