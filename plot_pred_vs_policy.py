import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse
import json
from scipy import stats
import seaborn as sns

# FiveThirtyEight-ish style
plt.style.use('fivethirtyeight')

# Tweak a few defaults to make it cleaner
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "axes.facecolor": "white",
    "figure.facecolor": "white",
    "grid.color": "#E5E5E5",
    "grid.linestyle": "-",
    "grid.linewidth": 1.0,
    "axes.edgecolor": "#CCCCCC",
    "axes.labelcolor": "#333333",
    "xtick.color": "#333333",
    "ytick.color": "#333333",
})

cscc_spec_map = {
    "1": "Baseline",
    "2": "High Damages",
    "3": "Low Damages",
    "4": "Fixed Discounting",
}

rice_spec_map = {
    "1": "Baseline",
    "2": "High Damages",
    "3": "Low Damages",
    "4": "DJO",
}

EU_COUNTRIES = {
    "aut", "bel", "bgr", "hrv", "cyp", "cze", "dnk", "est",
    "fin", "fra", "deu", "grc", "hun", "irl", "ita", "lva",
    "ltu", "lux", "mlt", "nld", "pol", "prt", "rou", "svk",
    "svn", "esp", "swe"
}

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
    country_mapping = json.load(open('input/policy_int_to_iso3.json'))
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
    fig, ax = plt.subplots(figsize=(10, 8))

    # Colors (538-like palette)
    point_color = "#4C78A8"   # muted blue
    line_color = "#F58518"    # muted orange (fit line)
    ref_color = "#E45756"     # muted red (45-degree line)

    xerr = None
    if len(outcome_cols) != 1:
        xerr = [
            plot_df['x_value'] - plot_df['min_outcome'],
            plot_df['max_outcome'] - plot_df['x_value']
        ]

    eu_mask = plot_df['n'].isin(EU_COUNTRIES)

    eu_color = "#59A14F"  
    non_eu_color = "#4C78A8" # 538 blue

    # Split data
    eu_df = plot_df[eu_mask]
    non_eu_df = plot_df[~eu_mask]

    # EU points
    ax.errorbar(
        eu_df['x_value'],
        eu_df[policy_col],
        xerr=None if len(outcome_cols) == 1 else [
            eu_df['x_value'] - eu_df['min_outcome'],
            eu_df['max_outcome'] - eu_df['x_value']
        ],
        yerr=[eu_df[policy_col] - eu_df[policy_low],
            eu_df[policy_high] - eu_df[policy_col]],
        fmt='o',
        color=eu_color,
        ecolor="#BBBBBB",
        elinewidth=1,
        capsize=2,
        alpha=0.85,
        markersize=8,
        markeredgecolor="white",
        markeredgewidth=0.5,
        label="EU"
    )

    # Non-EU points
    ax.errorbar(
        non_eu_df['x_value'],
        non_eu_df[policy_col],
        xerr=None if len(outcome_cols) == 1 else [
            non_eu_df['x_value'] - non_eu_df['min_outcome'],
            non_eu_df['max_outcome'] - non_eu_df['x_value']
        ],
        yerr=[non_eu_df[policy_col] - non_eu_df[policy_low],
            non_eu_df[policy_high] - non_eu_df[policy_col]],
        fmt='o',
        color=non_eu_color,
        ecolor="#DDDDDD",
        elinewidth=1,
        capsize=2,
        alpha=0.6,
        markersize=8,
        markeredgecolor="white",
        markeredgewidth=0.5,
        label="Non-EU"
    )

    # 45-degree line
    x = plot_df['x_value']
    y = plot_df[policy_col]
    x_min, x_max = x.min(), x.max()
    y_min, y_max = y.min(), y.max()

    # small padding so points don't touch edges
    x_pad = (x_max - x_min) * 0.05
    y_pad = (y_max - y_min) * 0.05

    ax.set_xlim(x_min - x_pad, x_max + x_pad)
    ax.set_ylim(y_min - y_pad, y_max + y_pad)

    lims = [
        max(ax.get_xlim()[0], ax.get_ylim()[0]),
        min(ax.get_xlim()[1], ax.get_ylim()[1])
    ]
    ax.plot(
        lims,
        lims,
        linestyle="--",
        color=ref_color,
        linewidth=1.5,
        alpha=0.8,
        label="45-degree line"
    )
    
    # Best fit line
    ax.plot(
        plot_df['x_value'],
        pred,
        color=line_color,
        linewidth=2.5,
        label=f"Best fit (β={slope:.2f}, R²={r_squared:.2f}, p={p_value:.3g})"
    )

    # Key country labels (slightly cleaner)
    for code, label in [('usa', 'US'), ('chn', 'China'), ('ind', 'India')]:
        row = plot_df[plot_df['n'] == code]
        if not row.empty:
            x_val = row['x_value'].values[0]
            y_val = row[policy_col].values[0]
            ax.text(
                x_val, y_val, label,
                fontsize=12,
                fontweight='bold',
                color=non_eu_color,
                bbox=None
            )

    ax.set_xlabel("Non-Cooperative Nash", fontsize=12)
    ax.set_ylabel(y_label, fontsize=12)
    ax.set_title(title, fontsize=14, weight='bold')

    ax.legend(frameon=False)
    ax.grid(True, axis='y', alpha=0.3)
    ax.grid(False, axis='x')

    # Remove top/right spines (key 538 aesthetic)
    sns.despine(ax=ax)

    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close()


if dataset == 'cscc':
    outfile = f'output/charts/cscc_plot_{year}_spec{spec}_{outcome}.png'
    if exclude_countries:
        outfile = outfile.replace('.png', f'_no_{"_".join(exclude_countries)}')
    spec_name = cscc_spec_map[spec]
    create_plot([f'noncoop_optimal_mu_spec{spec}'], f'Non-Cooperative Nash Equilbrium (CSCC) vs Counterfactual ({year}) - {spec_name}', outfile, exclude_countries, outcome)
else:
    spec_map = {
        "1": "ssp2_BHM-SR_0.015", # standard
        "2": "ssp2_BHM-LR_0.001", # high scc
        "3": "ssp1_BHM-SRdiff_0.03", # low scc
        "4": "ssp2_DJO_0.015" # DJO
    }
    scenario = spec_map[spec]
    outfile = f'output/charts/rice_spec{spec}_plot_{year}_{outcome}.png'
    spec_name = rice_spec_map[spec]
    if exclude_countries:
        outfile = outfile.replace('.png', f'_no_{"_".join(exclude_countries)}')
    create_plot([f'NONCOOP_{scenario}'], f'Non-Cooperative Nash Equilbrium (RICE) vs Counterfactual ({year}) - {spec_name}', outfile, exclude_countries, outcome)
