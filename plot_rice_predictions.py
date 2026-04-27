
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse
import json

# Parse command line arguments
parser = argparse.ArgumentParser(description='Generate dataset for a specific year.')
parser.add_argument('year', type=int, help='The year to process (e.g., 2022)')

args = parser.parse_args()
year = args.year

df = pd.read_csv(f'output/data/mitigation_rice_v_cntfc_{year}.csv')
# only keep countries that have counterfactuals if any do
country_mapping = json.load(open('policy_int_to_iso3.json'))
df = df[df['n'].isin(country_mapping.values())]


# Function to create a bar chart for a specific scenario comparing COOP vs NONCOOP
def create_scenario_bar_chart(scenario, filename):

    """Create a grouped bar chart comparing one noncoop scenario to matching coop scenarios."""
    noncoop_col = f'NONCOOP_{scenario}'
    if noncoop_col not in df.columns:
        raise ValueError(f"Noncoop column not found: {noncoop_col}")

    scenario_parts = scenario.split('_')
    prstp = scenario_parts[-1]
    scenario_prefix = '_'.join(scenario_parts[:-1])
    coop_cols = [
        c for c in df.columns
        if c.startswith(f'COOP_{scenario_prefix}_') and c.endswith(f'_{prstp}')
    ]

    if not coop_cols:
        raise ValueError(f"No matching COOP columns found for scenario {scenario}")

    coop_values = df[coop_cols].apply(pd.to_numeric, errors='coerce')
    coop_mean = coop_values.mean(axis=1)
    noncoop_values = pd.to_numeric(df[noncoop_col], errors='coerce')

    bar_df = pd.DataFrame({
        'n': df['n'],
        'Noncoop': noncoop_values,
        'Coop': coop_mean,
    }).dropna()

    bar_df = bar_df.sort_values('Noncoop', ascending=False)

    x = np.arange(len(bar_df))
    width = 0.35

    fig, ax = plt.subplots(figsize=(14, 8))
    ax.bar(x - width/2, bar_df['Noncoop'], width, label='Noncoop')
    ax.bar(x + width/2, bar_df['Coop'], width, label='Coop mean')

    ax.set_xticks(x)
    ax.set_xticklabels(bar_df['n'], rotation=45, ha='right')
    ax.set_ylabel('Outcome value')
    ax.set_title(f'COOP vs NONCOOP for scenario {scenario}')
    ax.legend()
    ax.grid(False)

    plt.tight_layout()
    plt.savefig(filename)
    print(f"Plot saved to {filename}")
    plt.close()


scenario_choice = "ssp2_BHM-LR_0.015"
create_scenario_bar_chart(scenario_choice, f'output/charts/coop_vs_noncoop_{scenario_choice}_bar_{year}.png')
