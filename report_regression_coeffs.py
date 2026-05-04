import os

import pandas as pd
from scipy import stats
import numpy as np
import matplotlib.pyplot as plt

SPEC_MAP = {
    "1": "ssp2_BHM-SR_0.015",
    "2": "ssp2_BHM-LR_0.001",
    "3": "ssp1_BHM-SRdiff_0.03",
    "4": "ssp2_DJO_0.015",
}

eu_iso3 = [ "aut", "bel", "bgr", "hrv", "cyp", "cze", "dnk", "est", "fin", "fra", 
           "deu", "grc", "hun", "irl", "ita", "lva", "ltu", "lux", "mlt", "nld",
            "pol", "prt", "rou", "svk", "svn", "esp", "swe",
]

EXCLUDE_GROUPS = [
    ("full", []),
    ("no_us_chn_ind", ["usa", "chn", "ind"]),
    ("no_eu", eu_iso3)
]

outcome_cols = ["policy_den_cntfc", "policy_strng_cntfc", "pol_dens_cum", "pol_dens_cum_diff", "strng_wght_ind", "strng_wght_ind_diff"]

y_col_disp = {
    "policy_den_cntfc":     "Policy Density Counterfactual",
    "policy_strng_cntfc":   "Policy Stringency Counterfactual",
    "pol_dens_cum":         "Policy Density",
    "pol_dens_cum_diff":    "Policy Density Change from 2015",
    "strng_wght_ind":       "Policy Stringency",
    "strng_wght_ind_diff":  "Policy Stringency Change from 2015",
    "carbon_price_effective": "Effective Carbon Price"
}

x_col_disp = {
    "scc_mid_spec1": "CSCC Spec 1",
    "scc_mid_spec2": "CSCC Spec 2",
    "scc_mid_spec3": "CSCC Spec 3",
    "scc_mid_spec4": "CSCC Spec 4",
    "noncoop_optimal_mu_spec1": "CSCC Optimal Abatement Spec 1",
    "noncoop_optimal_mu_spec2": "CSCC Optimal Abatement Spec 2",
    "noncoop_optimal_mu_spec3": "CSCC Optimal Abatement Spec 3",
    "noncoop_optimal_mu_spec4": "CSCC Optimal Abatement Spec 4",
    "NONCOOP_ssp2_BHM-SR_0.015": "RICE50x Optimal Abatement Spec 1",
    "NONCOOP_ssp2_BHM-LR_0.001": "RICE50x Optimal Abatement Spec 2",
    "NONCOOP_ssp1_BHM-SRdiff_0.03": "RICE50x Optimal Abatement Spec 3",
    "NONCOOP_ssp2_DJO_0.015": "RICE50x Optimal Abatement Spec 4",
}

REPORT_ROWS = []


def add_regression_row(dataset, year, spec, x_col, y_col, df, exclude_group=None):
    missing_columns = [col for col in (x_col, y_col) if col not in df.columns]
    if missing_columns:
        REPORT_ROWS.append({
            "dataset": dataset,
            "year": year,
            "spec": spec,
            "sample": "full",
            "x_column": x_col,
            "y_column": y_col,
            "n": 0,
            "slope": None,
            "intercept": None,
            "r_squared": None,
            "p_value": None,
            "note": "missing column(s): " + ", ".join(missing_columns),
        })
        return

    df_sub = df.copy()
    sample = "full"
    note = ""
    if exclude_group:
        sample = exclude_group[0]
        df_sub = df_sub[~df_sub["n"].astype(str).str.lower().isin([code.lower() for code in exclude_group[1]])]

    data = df_sub[[x_col, y_col]].apply(pd.to_numeric, errors="coerce").dropna()
    if data.empty:
        REPORT_ROWS.append({
            "dataset": dataset,
            "year": year,
            "spec": spec,
            "sample": sample,
            "x_column": x_col,
            "y_column": y_col,
            "n": 0,
            "slope": None,
            "intercept": None,
            "r_squared": None,
            "p_value": None,
            "note": note or "no valid rows",
        })
        return

    lr = stats.linregress(data[x_col], data[y_col])
    REPORT_ROWS.append({
        "dataset": dataset,
        "year": year,
        "spec": spec,
        "sample": sample,
        "x_column": x_col,
        "y_column": y_col,
        "n": int(len(data)),
        "slope": lr.slope,
        "intercept": lr.intercept,
        "r_squared": lr.rvalue ** 2,
        "p_value": lr.pvalue,
        "note": note
    })

    # for each regression, save a chart showing x, y, and best fit line (p value, r^2, slope written in corner)
    os.makedirs("output/regressions", exist_ok=True)

    x = data[x_col].values
    y = data[y_col].values

    fig = plt.figure()
    plt.scatter(x, y)

    # Best fit line
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = lr.intercept + lr.slope * x_line
    plt.plot(x_line, y_line)

    plt.xlabel(x_col_disp[x_col] if x_col in x_col_disp else x_col)
    plt.ylabel(y_col_disp[y_col] if y_col in y_col_disp else y_col)
    plt.title(f"{dataset} {year} spec{spec} ({sample})")

    # Annotate stats in upper left
    annotation = (
        f"slope = {lr.slope:.3f}\n"
        f"R² = {lr.rvalue**2:.3f}\n"
        f"p = {lr.pvalue:.3g}\n"
        f"n = {len(data)}"
    )

    plt.text(
        0.05, 0.95,
        annotation,
        transform=plt.gca().transAxes,
        verticalalignment="top"
    )

    filename = (
        f"{dataset}_{year}_spec{spec}_{sample}_{x_col}_vs_{y_col}.png"
        .replace("/", "_")
        .replace(" ", "_")
    )

    plt.tight_layout()
    plt.savefig(os.path.join("output/regressions", filename))
    plt.close(fig)

# CSCC 2020: noncoop_optimal_mu_spec{spec}
for spec in ["1", "2", "3", "4"]:
    filename = "output/data/mitigation_cscc_v_cntfc_2020.csv"
    df = pd.read_csv(filename)
    x_col = f"noncoop_optimal_mu_spec{spec}"
    for y_col in outcome_cols:
        for exclude_group in EXCLUDE_GROUPS:
            add_regression_row(
                dataset="cscc",
                year=2020,
                spec=spec,
                x_col=x_col,
                y_col=y_col,
                df=df,
                exclude_group=exclude_group,
            )
    # also regress carbon prices on cscc
    add_regression_row(
                dataset="cscc",
                year=2020,
                spec=spec,
                x_col=f'scc_mid_spec{spec}',
                y_col='carbon_price_effective',
                df=df,
            )

    # also regress carbon prices on cscc
    for carbon_price in ['carbon_price_effective', 'carbon_price_dolphin_ghg', 'carbon_price_dolphin_co2']:
        add_regression_row(
                    dataset="cscc",
                    year=2020,
                    spec=spec,
                    x_col=f'scc_mid_spec{spec}',
                    y_col=carbon_price,
                    df=df,
                )

# RICE 2022: NONCOOP_{scenario}
rice_filename = "output/data/mitigation_rice_v_cntfc_2022.csv"
if os.path.exists(rice_filename):
    df_rice = pd.read_csv(rice_filename)
    country_mapping = pd.read_json("policy_int_to_iso3.json", typ="series")
    df_rice = df_rice[df_rice["n"].isin(country_mapping.values)]

    for spec in ["1", "2", "3", "4"]:
        scenario = SPEC_MAP[spec]
        x_col = f"NONCOOP_{scenario}"
        for y_col in outcome_cols:
            for exclude_group in EXCLUDE_GROUPS:
                add_regression_row(
                    dataset="rice",
                    year=2022,
                    spec=spec,
                    x_col=x_col,
                    y_col=y_col,
                    df=df_rice,
                    exclude_group=exclude_group,
                )
else:
    print("FAILED TO FIND RICE DATA FILE")

report = pd.DataFrame(REPORT_ROWS)
report = report[
    ["dataset", "year", "spec", "sample", "x_column", "y_column", "n", "slope", "intercept", "r_squared", "p_value", "note"]
]

output_dir = "output/regressions"
os.makedirs(output_dir, exist_ok=True)
output_csv = os.path.join(output_dir, "regression_coefficients_table.csv")
report.to_csv(output_csv, index=False)

print("Regression coefficients table")
print(report.to_string(index=False, float_format="{:.6g}".format))
print(f"\nSaved CSV to {output_csv}")
