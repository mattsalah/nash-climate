import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse
import json

# Parse command line arguments
parser = argparse.ArgumentParser(description='Generate dataset for a specific year.')
parser.add_argument('year', type=int, help='The year to process (e.g., 2022)')
parser.add_argument('--dataset', choices=['rice', 'cscc'], default='rice', help='Dataset to use: rice or cscc')
parser.add_argument('--exclude', nargs='*', default=[], help='List of country codes to exclude from the plot (e.g., usa chn ind)')
args = parser.parse_args()

year = args.year
dataset = args.dataset
exclude_countries = args.exclude

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
def create_plot(outcome_cols, title, filename, exclude_countries=[]):
    # Convert to numeric and compute values for the chosen scenario
    outcomes = df[outcome_cols].apply(pd.to_numeric, errors='coerce')
    df_temp = df.copy()
    if len(outcome_cols) == 1:
        plot_df = df_temp[['n', 'policy_int_cntfc', 'policy_int_cntfc_low', 'policy_int_cntfc_high']].copy()
        plot_df['x_value'] = outcomes.iloc[:, 0]
        x_label = outcome_cols[0].replace('_', ' ')
    else:
        df_temp['min_outcome'] = outcomes.min(axis=1)
        df_temp['max_outcome'] = outcomes.max(axis=1)
        df_temp['mean_outcome'] = outcomes.mean(axis=1)
        plot_df = df_temp[['n', 'min_outcome', 'max_outcome', 'mean_outcome', 'policy_int_cntfc', 'policy_int_cntfc_low', 'policy_int_cntfc_high']].copy()
        plot_df['x_value'] = plot_df['mean_outcome']
        x_label = f'Outcome range across {title.split()[-1]} columns'

    plot_df = plot_df.sort_values('policy_int_cntfc').dropna()

    # Exclude specified countries
    if exclude_countries:
        plot_df = plot_df[~plot_df['n'].isin(exclude_countries)]

    # Compute y error bars
    yerr = [plot_df['policy_int_cntfc'] - plot_df['policy_int_cntfc_low'], plot_df['policy_int_cntfc_high'] - plot_df['policy_int_cntfc']]

    # Fit a line of best fit
    slope, intercept = np.polyfit(plot_df['x_value'], plot_df['policy_int_cntfc'], 1)

    # Calculate R^2
    pred = slope * plot_df['x_value'] + intercept
    ss_res = np.sum((plot_df['policy_int_cntfc'] - pred) ** 2)
    ss_tot = np.sum((plot_df['policy_int_cntfc'] - np.mean(plot_df['policy_int_cntfc'])) ** 2)
    r_squared = 1 - (ss_res / ss_tot)

    # Create the plot
    plt.figure(figsize=(10, 8))
    xerr = None
    if len(outcome_cols) != 1:
        xerr = [plot_df['x_value'] - plot_df['min_outcome'], plot_df['max_outcome'] - plot_df['x_value']]

    plt.errorbar(
        plot_df['x_value'],
        plot_df['policy_int_cntfc'],
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
    y_min_data = plot_df['policy_int_cntfc'].min()
    y_max_data = plot_df['policy_int_cntfc'].max()
    line_min = min(x_min_data, y_min_data)
    line_max = max(x_max_data, y_max_data)
    plt.plot([line_min, line_max], [line_min, line_max], 'r--', label='45-degree line')

    # Plot the best fit line
    plt.plot(plot_df['x_value'], pred, 'b-', label=f'Best fit (slope={slope:.2f}, R²={r_squared:.2f})')

    # Label key countries
    for code, label in [('usa', 'US'), ('chn', 'China'), ('ind', 'India')]:
        row = plot_df[plot_df['n'] == code]
        if not row.empty:
            x_val = row['x_value'].values[0]
            y_val = row['policy_int_cntfc'].values[0]
            plt.annotate(label, xy=(x_val, y_val), xytext=(5, -5), textcoords='offset points',
                         fontsize=10, fontweight='bold', color='black',
                         bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.8))

    plt.xlabel(x_label)
    plt.ylabel('Policy Intensity Counterfatual')
    plt.title(title)
    plt.legend()
    plt.grid(False)
    plt.tight_layout()
    plt.savefig(filename)
    print(f"Plot saved to {filename}")
    plt.close()

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

# Create scenario-specific NONCOOP scatter plot
scenario_choice = 'ssp2_BHM-LR_0.015'

if year<=2022:
    if dataset == 'cscc':
        create_plot(['noncoop_optimal_mu'], f'Noncoop optimal mu vs policy_int_cntfc ({year})', f'output/charts/policy_int_noncoop_optimal_mu_vs_cntfc_{year}_no_{"_".join(exclude_countries)}.png', exclude_countries)
    else:
        create_plot([f'NONCOOP_{scenario_choice}'], f'Noncoop scenario {scenario_choice} vs policy_int_cntfc ({year})', f'output/charts/policy_int_scenario_vs_cntfc_noncoop_plot_{year}_no_{"_".join(exclude_countries)}.png', exclude_countries)

# Create a scenario-specific COOP vs NONCOOP bar chart
if dataset == 'rice':
    create_scenario_bar_chart(scenario_choice, f'output/charts/coop_vs_noncoop_{scenario_choice}_bar_{year}.png')
