import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the CSV file
df = pd.read_csv('output/data/transformed_emi_ind_2020_with_policy_int_cntfc.csv')

# Select all outcome columns except the region and policy intensity column
outcome_cols = [c for c in df.columns if c not in ['n', 'policy_int_cntfc']]

# Convert to numeric and compute range per row
outcomes = df[outcome_cols].apply(pd.to_numeric, errors='coerce')
df['min_outcome'] = outcomes.min(axis=1)
df['max_outcome'] = outcomes.max(axis=1)
df['mean_outcome'] = outcomes.mean(axis=1)

# Sort by policy_int_cntfc for nicer plotting
plot_df = df.sort_values('policy_int_cntfc')
plot_df = plot_df[['n', 'min_outcome', 'max_outcome', 'mean_outcome', 'policy_int_cntfc']].dropna()

# Fit a line of best fit
slope, intercept = np.polyfit(plot_df['mean_outcome'], plot_df['policy_int_cntfc'], 1)

# Calculate R^2
pred = slope * plot_df['mean_outcome'] + intercept
ss_res = np.sum((plot_df['policy_int_cntfc'] - pred)**2)
ss_tot = np.sum((plot_df['policy_int_cntfc'] - np.mean(plot_df['policy_int_cntfc']))**2)
r_squared = 1 - (ss_res / ss_tot)

# Create the plot using horizontal interval bars
plt.figure(figsize=(10, 8))
plt.errorbar(
    plot_df['mean_outcome'],
    plot_df['policy_int_cntfc'],
    xerr=[plot_df['mean_outcome'] - plot_df['min_outcome'], plot_df['max_outcome'] - plot_df['mean_outcome']],
    fmt='o',
    ecolor='gray',
    capsize=3,
    alpha=0.7
)

# Add a 45-degree reference line
min_val = min(plot_df['mean_outcome'].min(), plot_df['policy_int_cntfc'].min())
max_val = max(plot_df['mean_outcome'].max(), plot_df['policy_int_cntfc'].max())
plt.plot([min_val, max_val], [min_val, max_val], 'r--', label='45-degree line')

# Calculate R^2
pred = slope * plot_df['mean_outcome'] + intercept
ss_res = np.sum((plot_df['policy_int_cntfc'] - pred)**2)
ss_tot = np.sum((plot_df['policy_int_cntfc'] - np.mean(plot_df['policy_int_cntfc']))**2)
r_squared = 1 - (ss_res / ss_tot)

# Plot the best fit line
plt.plot(plot_df['mean_outcome'], pred, 'b-', label=f'Best fit (slope={slope:.2f}, R²={r_squared:.2f})')

# Add text label
plt.text(0.05, 0.95, f'Slope: {slope:.2f}\nR²: {r_squared:.2f}', transform=plt.gca().transAxes, fontsize=12, verticalalignment='top')

# Add region labels for over/under abatement
plt.text(min_val + 0.1 * (max_val - min_val), max_val - 0.1 * (max_val - min_val), 'over abatement',
         color='red', fontsize=10, ha='left', va='top')
plt.text(max_val - 0.1 * (max_val - min_val), min_val + 0.1 * (max_val - min_val), 'under abatement',
         color='red', fontsize=10, ha='right', va='bottom')

# Label key countries by region code
for code, label in [('usa', 'US'), ('chn', 'China'), ('ind', 'India')]:
    row = plot_df[plot_df['n'] == code]
    if not row.empty:
        x_val = row['mean_outcome'].values[0]
        y_val = row['policy_int_cntfc'].values[0]
        plt.annotate(label, xy=(x_val, y_val), xytext=(5, -5), textcoords='offset points',
                     fontsize=10, fontweight='bold', color='black',
                     bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.8))

plt.xlabel('Outcome range across non-policy_int columns')
plt.ylabel('policy_int_cntfc')
plt.title('Outcome range vs policy_int_cntfc (2020)')
plt.legend()
plt.grid(True)
plt.tight_layout()
output_path = 'output/charts/policy_int_range_vs_outcomes_plot.png'
plt.savefig(output_path)
print(f"Plot saved to {output_path}")
