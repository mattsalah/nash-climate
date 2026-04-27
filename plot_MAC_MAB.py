
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys

# Parse command line arguments
parser = argparse.ArgumentParser(description='Plot MAC and MAB curves for a country and spec')
parser.add_argument('country', nargs='?', default='aus', help='Country code or name (default: aus)')
parser.add_argument('spec', nargs='?', default='1', help='Specification number (default: 1)')
parser.add_argument('--include-global-scc', dest='include_global_scc', action='store_true', default=True,
                    help='Include the global SCC/MAB line in the plot (default)')
parser.add_argument('--no-global-scc', dest='include_global_scc', action='store_false',
                    help='Do not include the global SCC/MAB line in the plot')
args = parser.parse_args()

country = args.country.lower()
spec = args.spec.lower()
include_global_scc = args.include_global_scc

# Read the data
df = pd.read_csv('output/data/mitigation_cscc_v_cntfc_2020.csv')

# Filter for the selected country
country_data = df[df['n'].str.lower() == country]

if country_data.empty:
    print(f"Country '{country}' not found in data.")
    sys.exit(1)

# Extract parameters
row = country_data.iloc[0]
scc_mid = row[f'scc_mid_spec{spec}']
global_scc_mid = row[f'global_scc_mid_spec{spec}']
a = row['macc_a']
d = row['macc_d']
coop_optimal_mu = row[f'coop_optimal_mu_spec{spec}']
noncoop_optimal_mu = row[f'noncoop_optimal_mu_spec{spec}']
policy_int_cntfc = row['policy_int_cntfc']

# Check for missing values
if pd.isna(scc_mid) or pd.isna(a) or pd.isna(d):
    print(f"Missing parameters for country '{country}'")
    sys.exit(1)

# Create mu range for plotting
if include_global_scc:
    mu_range = np.linspace(min(0, noncoop_optimal_mu)*1.2, max(coop_optimal_mu, policy_int_cntfc)*1.2, 1000)
else:
    mu_range = np.linspace(min(0, noncoop_optimal_mu)*1.2, max(noncoop_optimal_mu, policy_int_cntfc)*1.2, 1000)

# Calculate MAB and MC
mab_loc = scc_mid * np.ones(len(mu_range))
mc = a * (mu_range/100) + d * ((mu_range/100) ** 4)
if include_global_scc:
    mab_glob = global_scc_mid * np.ones(len(mu_range))

# Create the plot
fig, ax = plt.subplots(figsize=(10, 6))

# Plot MAB and MC curves
ax.plot(mu_range, mab_loc, label='Local MAB', linewidth=2, color='blue')
if include_global_scc:
    ax.plot(mu_range, mab_glob, label='Global MAB', linewidth=2, color='purple')
ax.plot(mu_range, mc, label='MC', linewidth=2, color='red')

# Add vertical line at non-coop optimal mu
if not pd.isna(noncoop_optimal_mu):
    ax.axvline(x=noncoop_optimal_mu, color='green', linestyle='--', linewidth=2, label=f'Non-Coop Optimal μ = {noncoop_optimal_mu:.4f}')
    # Mark the intersection point
    ax.plot(noncoop_optimal_mu, scc_mid, 'go', markersize=8)

if include_global_scc:
    # Add vertical line at coop optimal mu
    if not pd.isna(coop_optimal_mu):
        ax.axvline(x=coop_optimal_mu, color='purple', linestyle='-.', linewidth=2, label=f'Coop Optimal μ = {coop_optimal_mu:.4f}')
        # Mark the intersection point
        ax.plot(coop_optimal_mu, global_scc_mid, 'o', color='purple', markersize=8)

# Add vertical line at policy intensity counterfactual
if not pd.isna(policy_int_cntfc):
    ax.axvline(x=policy_int_cntfc, color='orange', linestyle=':', linewidth=2, label=f'Policy Intensity μ = {policy_int_cntfc:.4f}')
    # Mark the intersection point
    ax.plot(policy_int_cntfc, scc_mid, 'o', color='orange', markersize=8)

# Labels and title
ax.set_xlabel('Abatement Fraction (μ)', fontsize=12)
ax.set_ylabel('Benefit/Cost ($)', fontsize=12)
ax.set_title(f'{country.upper()} - Specification {spec}', fontsize=14, fontweight='bold')
ax.legend(fontsize=11, loc='best')
ax.grid(True, alpha=0.3)

# Save and show
output_filename = f'output/charts/mac_mab_{country}_spec{spec}.png'
plt.tight_layout()
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
print(f"Plot saved to {output_filename}")

plt.show()
