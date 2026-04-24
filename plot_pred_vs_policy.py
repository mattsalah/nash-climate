import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

year = 2022

# Read the CSV file
df = pd.read_csv(f'output/data/mitigation_rice_v_cntfc_{year}.csv')
# only keep countries that have counterfactuals
df = df[df['policy_int_cntfc_low'].notna()]


# Separate outcome columns
coop_cols = [c for c in df.columns if c.startswith('COOP_')]

# Function to create plot for a specific scenario
def create_plot(outcome_cols, title, filename):
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

    # Add text label
    plt.text(0.05, 0.95, f'Slope: {slope:.2f}\nR²: {r_squared:.2f}', transform=plt.gca().transAxes, fontsize=12, verticalalignment='top')

    # Label key countries
    for code, label in [('usa', 'US'), ('chn', 'China'), ('nde', 'India')]:
        row = plot_df[plot_df['n'] == code]
        if not row.empty:
            x_val = row['x_value'].values[0]
            y_val = row['policy_int_cntfc'].values[0]
            plt.annotate(label, xy=(x_val, y_val), xytext=(5, -5), textcoords='offset points',
                         fontsize=10, fontweight='bold', color='black',
                         bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.8))

    plt.xlabel(x_label)
    plt.ylabel('policy_int_cntfc')
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
create_plot([f'NONCOOP_{scenario_choice}'], f'Noncoop scenario {scenario_choice} vs policy_int_cntfc ({year})', f'output/charts/policy_int_scenario_vs_cntfc_noncoop_plot_{year}.png')

# Create a scenario-specific COOP vs NONCOOP bar chart
create_scenario_bar_chart(scenario_choice, f'output/charts/coop_vs_noncoop_{scenario_choice}_bar_{year}.png')
