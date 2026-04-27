import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse
import json
from scipy import stats

# Parse command line arguments
parser = argparse.ArgumentParser(description='Generate dataset for a specific year.')
parser.add_argument('year', type=int, help='The year to process (e.g., 2022)')
parser.add_argument('--dataset', choices=['rice', 'cscc'], default='rice', help='Dataset to use: rice or cscc')
parser.add_argument('--exclude', nargs='*', default=[], help='List of country codes to exclude from the plot (e.g., usa chn ind)')
parser.add_argument('--spec', choices=["1", "2", "3", "4"], default='1', help='Specification')
parser.add_argument('--outcome', choices=['strng', 'den'], default='den', help='Policy outcome to plot: stringency (strng) or density (den)')

args = parser.parse_args()

year = args.year
dataset = args.dataset
exclude_countries = args.exclude
spec = args.spec
outcome = args.outcome

# Read the CSV file based on dataset
if dataset == 'cscc':
    df = pd.read_csv(f'output/data/mitigation_cscc_v_cntfc_{year}.csv')
    # For cscc, countries are already iso3, no need for mapping
else:
    df = pd.read_csv(f'output/data/mitigation_rice_v_cntfc_{year}.csv')
    # only keep countries that have counterfactuals if any do
    country_mapping = json.load(open('policy_int_to_iso3.json'))
    df = df[df['n'].isin(country_mapping.values())]


# Separate outcome columns
if dataset == 'cscc':
    outcome_cols = ['noncoop_optimal_mu']
else:
    coop_cols = [c for c in df.columns if c.startswith('COOP_')]

# Function to create plot for a specific scenario
def create_plot(outcome_cols, title, filename, exclude_countries=[], outcome='den'):
    # Determine policy columns based on outcome
    if outcome == 'den':
        policy_col = 'policy_den_cntfc'
        policy_low = 'policy_den_cntfc_low'
        policy_high = 'policy_den_cntfc_high'
        y_label = 'Policy Density Counterfactual'
    elif outcome == 'strng':
        policy_col = 'policy_strng_cntfc'
        policy_low = 'policy_strng_cntfc_low'
        policy_high = 'policy_strng_cntfc_high'
        y_label = 'Policy Stringency Counterfactual'
    else:
        raise ValueError("Invalid outcome")

    # Convert to numeric and compute values for the chosen scenario
    outcomes = df[outcome_cols].apply(pd.to_numeric, errors='coerce')
    df_temp = df.copy()
    if len(outcome_cols) == 1:
        plot_df = df_temp[['n', policy_col, policy_low, policy_high]].copy()
        plot_df['x_value'] = outcomes.iloc[:, 0]
        x_label = outcome_cols[0].replace('_', ' ')
    else:
        df_temp['min_outcome'] = outcomes.min(axis=1)
        df_temp['max_outcome'] = outcomes.max(axis=1)
        df_temp['mean_outcome'] = outcomes.mean(axis=1)
        plot_df = df_temp[['n', 'min_outcome', 'max_outcome', 'mean_outcome', policy_col, policy_low, policy_high]].copy()
        plot_df['x_value'] = plot_df['mean_outcome']
        x_label = f'Outcome range across {title.split()[-1]} columns'

    plot_df = plot_df.sort_values(policy_col).dropna()

    # Exclude specified countries
    if exclude_countries:
        plot_df = plot_df[~plot_df['n'].isin(exclude_countries)]

    # Compute y error bars
    yerr = [plot_df[policy_col] - plot_df[policy_low], plot_df[policy_high] - plot_df[policy_col]]

    # Fit a line of best fit and compute slope significance
    lr = stats.linregress(plot_df['x_value'], plot_df[policy_col])
    slope = lr.slope
    intercept = lr.intercept
    r_squared = lr.rvalue ** 2
    p_value = lr.pvalue
    pred = slope * plot_df['x_value'] + intercept

    # Create the plot
    plt.figure(figsize=(10, 8))
    xerr = None
    if len(outcome_cols) != 1:
        xerr = [plot_df['x_value'] - plot_df['min_outcome'], plot_df['max_outcome'] - plot_df['x_value']]

    plt.errorbar(
        plot_df['x_value'],
        plot_df[policy_col],
        xerr=xerr,
        yerr=yerr,
        fmt='o',
        ecolor='gray',
        capsize=3,
        alpha=0.7
    )

    # Add a 45-degree reference line
    x_min_data = plot_df['x_value'].min()
    x_max_data = plot_df['x_value'].max()
    plt.plot([x_min_data, x_max_data], [x_min_data, x_max_data], 'r--', label='45-degree line')

    # Plot the best fit line
    plt.plot(plot_df['x_value'], pred, 'b-', label=f'Best fit (slope={slope:.2f}, R²={r_squared:.2f}, p={p_value:.3g})')

    # Label key countries
    for code, label in [('usa', 'US'), ('chn', 'China'), ('ind', 'India')]:
        row = plot_df[plot_df['n'] == code]
        if not row.empty:
            x_val = row['x_value'].values[0]
            y_val = row[policy_col].values[0]
            plt.annotate(label, xy=(x_val, y_val), xytext=(5, -5), textcoords='offset points',
                         fontsize=10, fontweight='bold', color='black',
                         bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.8))

    plt.xlabel("Non-Cooperative Nash")
    plt.ylabel(y_label)
    plt.title(title)
    plt.legend()
    plt.grid(False)
    plt.tight_layout()
    plt.savefig(filename)
    print(f"Plot saved to {filename}")
    plt.close()


if dataset == 'cscc':
    outfile = f'output/charts/cscc_plot_{year}_spec{spec}_{outcome}.png'
    if exclude_countries:
        outfile = outfile.replace('.png', f'_no_{"_".join(exclude_countries)}')
    create_plot([f'noncoop_optimal_mu_spec{spec}'], f'Non-Cooperative Nash Equilbrium (CSCC) vs Counterfactual ({year}) - Spec {spec}', outfile, exclude_countries, outcome)
else:
    spec_map = {
        "1": "ssp2_BHM-SR_0.015", # standard
        "2": "ssp2_BHM-LR_0.001", # high scc
        "3": "ssp1_BHM-SRdiff_0.03", # low scc
        "4": "ssp2_DJO_0.015" # DJO
    }
    scenario = spec_map[spec]
    outfile = f'output/charts/rice_spec{spec}_plot_{year}_{outcome}.png'
    if exclude_countries:
        outfile = outfile.replace('.png', f'_no_{"_".join(exclude_countries)}')
    create_plot([f'NONCOOP_{scenario}'], f'Non-Cooperative Nash Equilbrium (RICE) vs Counterfactual ({year}) - Spec {spec}', outfile, exclude_countries, outcome)
