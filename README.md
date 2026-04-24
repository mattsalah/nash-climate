# Installation

1. Clone the RICE50xmodel into this directory (https://github.com/witch-team/RICE50xmodel/tree/main).
2. Install GAMS from the website (https://www.gams.com/download/).
3. Download the data_ed58 folder and place it into RICE50xmodel directory (https://github.com/witch-team/RICE50xmodel/releases/tag/v2.6.0).
4. Configure environment:
```
source setup.sh 
```
5. Download results from the Gazzotti et al 2021 (https://github.com/witch-team/RICE50xmodel/releases/download/v1.0.0/NC2021_results_dataset.zip), and place the NC2021_results_dataset in the repo directory.
- This is temporary, because I can't run the model myself unti I get the license.
6. Download annual-co2-emissions from Our World in Data (https://ourworldindata.org/explorers/co2)
- Settings: CO2, Territorial, All fossil emissions, Per country
7. Download replication package for (https://www.nature.com/articles/s41467-026-68577-z#Sec9) and place it in a folder called "policy_intensity".
8. Download replication package for (https://pmc.ncbi.nlm.nih.gov/articles/PMC11717907) and place it in a folder called "structural_breaks".
9. Download results dataset for (https://www.nature.com/articles/s41558-018-0282-y#MOESM1) and place it in "country_scc"

# Usage

## Extracting MACC Values

We don't necessarily want to run the whole thing just to figure out what the MACC outputs look like. So we can simply run the script I've written for this purpose:

```
gams extract_macc.gms 
```

This produces macc_extract.gdx which has all the information the full model uses, including SSP scaling. We don't actually care about the SSP scaling since we are just looking at cost curves for 2015, 2020, and 2025. So the script also outputs two simple csvs called `macc_ed_early.csv` and `emi_bau_early.csv`.

### macc_ed_early.csc

The coefficients in the script define the MAC curve for each region:

    MAC(μ) = a·μ + d·μ⁴

where μ is the abatement rate (0 = no abatement, 1 = full abatement) and
MAC is the marginal cost of abatement in $/tCO2.

The total abatement cost is the integral of this curve:

    ABATECOST(μ) = emi_bau · (a·μ²/2 + d·μ⁵/5)

#### Columns

| Column  | Description |
|---------|-------------|
| `sector` | Emissions sector. All rows are `Total_CO2`, the economy-wide aggregate used in the RICE50+ cost equation. |
| `Dim2`  | Polynomial coefficient label. `a` is the linear term (c1); `d` is the quartic term (c4). Together they shape the curvature of the MAC curve — `a` governs the cost of early/cheap abatement, `d` governs how steeply costs rise at high abatement rates. |
| `t`     | Time period index. `1` = 2015, `2` = 2020, `3` = 2025. Each period is a 5-year step. |
| `n`     | Region code. 58 regions following the RICE50+ `ed58` mapping (e.g. `usa`, `chn`, `deu`). Some regions are individual countries; others are aggregates (e.g. `rsam` = Rest of South America, `noap` = Non-OECD Asia Pacific). |
| `Val`   | Coefficient value in $/tCO2. A value of 0 indicates missing Enerdata coverage for that region-period. Note that coverage is denser for European countries and sparser for African, South-East Asian, and Latin American aggregates. |

#### Example rows

| sector     | Dim2 | t | n   | Val              |
|------------|------|---|-----|------------------|
| Total_CO2  | a    | 1 | arg | 564.82           |
| Total_CO2  | d    | 1 | arg | 312.45           |
| Total_CO2  | a    | 2 | usa | 489.13           |
| Total_CO2  | d    | 2 | usa | 201.67           |

#### Notes

- These are the **raw** Enerdata coefficients before any SSP scenario scaling.
  They reflect actual modeled abatement costs and are appropriate for
  backward-looking analysis (e.g. comparing observed abatement to Nash
  equilibrium predictions for 2015–2025).
- The `a` coefficient is typically larger than `d` for most regions, meaning
  the linear term dominates at low abatement rates. The `d` term becomes
  important only at high abatement rates (μ > 0.5).
- Zero values should be treated as missing, not as zero cost.

### Visualizing MACCs

At low levels of abatement, the `a` term dominates, so for our purposes, we are mainly interested in the dispersion of `a` across the countries / regions. We can use the following script to make a simple bar chart showing these values for different years:

```
Rscript plot_macc.R
```

## Results from Gazotti 2021

These come straight from the replication package, which prevents me having to re-run RICE from scratch.

## Counterfactual 1: Policy Intensity

Run `policy_intensity_counterfactuals.do' in STATA.

## Combining Counterfactuals and RICE Outputs

The `generate_dataset.py` script processes the `CBA_regional_data.csv` file from the NC2021 results dataset. It filters the data for a specified year (default 2022), policy 'CBA', and cooperation 'noncoop-pop' and 'coop-pop', then pivots the table to create one row per country (region) with columns for each combination of baseline (ssp1-ssp5), impacts (BHM-LR, BHM-LRdiff, BHM-SR, BHM-SRdiff, DJO, KAHN), and prstp (0.001, 0.015, 0.03) for noncoop, and additionally disnt for coop. The values in these columns are the `mitigation` (abatement rate) for each specification.

It additionally merges the policy intensity counterfactuals from the processed STATA output (`output/data/country_year_counterfactual_CO2.csv`), and structural breaks data.

To run the script (for 2020):
```
python generate_dataset.py 2020
```

This produces `output/data/mitigation_rice_v_cntfc_{year}.csv`, which can be used for further analysis of abatement under different scenarios.

## Charts

The `plot_pred_vs_policy.py` script visualizes the relationship between predicted abatement from RICE model scenarios and policy intensity counterfactuals. It reads `output/data/mitigation_rice_v_cntfc_{year}.csv`, and creates scatter plots with error bars comparing abatement outcomes against policy intensity measures, including best-fit lines and R-squared values. It saves plots such as `output/charts/policy_int_scenario_vs_cntfc_noncoop_plot_{year}.png` and bar charts comparing coop vs noncoop scenarios.

To run the script (for 2020):
```
python plot_pred_vs_policy.py 2020
```

## Running BAU

```
gams run_rice50x.gms --policy=bau
```

# TODO

- Run with maxiso3 and latest version rather than just using 2021 results
- Policy index counterfactual
- Integrate empirical emissions