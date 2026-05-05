import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm


MAKE_PLOTS = False

SPEC_MAP = {
    "1": "ssp2_BHM-SR_0.015",
    "2": "ssp2_BHM-LR_0.001",
    "3": "ssp1_BHM-SRdiff_0.03",
    "4": "ssp2_DJO_0.015",
}

EU_ISO3 = [ "aut", "bel", "bgr", "hrv", "cyp", "cze", "dnk", "est", "fin", "fra", 
           "deu", "grc", "hun", "irl", "ita", "lva", "ltu", "lux", "mlt", "nld",
            "pol", "prt", "rou", "svk", "svn", "esp", "swe",
]

EXCLUDE_GROUPS = [
    ("full", []),
    ("no_us_chn_ind", ["usa", "chn", "ind"]),
    ("no_eu", EU_ISO3)
]

OUTCOME_COLS = ["policy_den_cntfc", "policy_strng_cntfc", "pol_dens_cum", "pol_dens_cum_diff", "strng_wght_ind", "strng_wght_ind_diff"]

CONTROLS = [
    [], ["gdppc"], ["log_gdppc"]
]

Y_COL_DISP = {
    "policy_den_cntfc":     "Policy Density Counterfactual",
    "policy_strng_cntfc":   "Policy Stringency Counterfactual",
    "pol_dens_cum":         "Policy Density",
    "pol_dens_cum_diff":    "Policy Density Change from 2015",
    "strng_wght_ind":       "Policy Stringency",
    "strng_wght_ind_diff":  "Policy Stringency Change from 2015",
    "carbon_price_effective": "Effective Carbon Price"
}

X_COL_DISP = {
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

def save_regression_plot(
    model,
    data,
    dataset,
    year,
    spec,
    sample,
    x_col,
    y_col,
    controls=None,
    X_COL_DISP=None,
    Y_COL_DISP=None,
    output_dir="output/regressions"
):
    """
    Saves a scatter plot with fitted regression line and robust inference stats.
    If controls are provided, produces a partial regression (added-variable) plot.
    """

    controls = controls or []
    X_COL_DISP = X_COL_DISP or {}
    Y_COL_DISP = Y_COL_DISP or {}

    os.makedirs(output_dir, exist_ok=True)

    fig = plt.figure()

    # --------------------------------------------------
    # Case 1: No controls (simple scatter + fit line)
    # --------------------------------------------------
    if not controls:

        x = data[x_col].values
        y = data[y_col].values

        plt.scatter(x, y)

        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = model.params["const"] + model.params[x_col] * x_line
        plt.plot(x_line, y_line)

    # --------------------------------------------------
    # Case 2: With controls (partial regression plot)
    # --------------------------------------------------
    else:
        # Residualize y on controls
        y_resid = sm.OLS(
            data[y_col],
            sm.add_constant(data[controls])
        ).fit().resid

        # Residualize x on controls
        x_resid = sm.OLS(
            data[x_col],
            sm.add_constant(data[controls])
        ).fit().resid

        plt.scatter(x_resid, y_resid)

        x_line = np.linspace(x_resid.min(), x_resid.max(), 100)
        y_line = model.params[x_col] * x_line
        plt.plot(x_line, y_line)

        plt.xlabel(f"{x_col} (residualized)")
        plt.ylabel(f"{y_col} (residualized)")

    # --------------------------------------------------
    # Labels and title
    # --------------------------------------------------
    if not controls:
        plt.xlabel(X_COL_DISP.get(x_col, x_col))
        plt.ylabel(Y_COL_DISP.get(y_col, y_col))

    plt.title(f"{dataset} {year} spec{spec} ({sample})")

    # --------------------------------------------------
    # Robust stats annotation
    # --------------------------------------------------
    annotation = (
        f"slope = {model.params[x_col]:.3f}\n"
        f"robust SE = {model.bse[x_col]:.3f}\n"
        f"R² = {model.rsquared:.3f}\n"
        f"p = {model.pvalues[x_col]:.3g}\n"
        f"n = {int(model.nobs)}"
    )

    plt.text(
        0.05,
        0.95,
        annotation,
        transform=plt.gca().transAxes,
        verticalalignment="top"
    )

    # --------------------------------------------------
    # Save
    # --------------------------------------------------
    filename = (
        f"{dataset}_{year}_spec{spec}_{sample}_{x_col}_vs_{y_col}.png"
        .replace("/", "_")
        .replace(" ", "_")
    )

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename))
    plt.close(fig)


def add_regression_row(
    dataset,
    year,
    spec,
    x_col,
    y_col,
    df,
    controls=None,
    exclude_group=None
):
    controls = controls or []

    # ----------------------------------
    # Check required columns
    # ----------------------------------
    required_cols = [x_col, y_col] + controls
    missing_columns = [col for col in required_cols if col not in df.columns]

    if missing_columns:
        REPORT_ROWS.append({
            "dataset": dataset,
            "year": year,
            "spec": spec,
            "sample": "full",
            "x_column": x_col,
            "y_column": y_col,
            "controls": controls,
            "n": 0,
            "slope": None,
            "robust_se": None,
            "intercept": None,
            "r_squared": None,
            "p_value": None,
            "note": "missing column(s): " + ", ".join(missing_columns),
        })
        return

    # ----------------------------------
    # Subset sample
    # ----------------------------------
    df_sub = df.copy()
    sample = "full"
    note = ""

    if exclude_group:
        sample = exclude_group[0]
        df_sub = df_sub[
            ~df_sub["n"].astype(str).str.lower().isin(
                [code.lower() for code in exclude_group[1]]
            )
        ]

    # ----------------------------------
    # Clean data
    # ----------------------------------
    reg_cols = required_cols
    data = df_sub[reg_cols].apply(pd.to_numeric, errors="coerce").dropna()

    if data.empty:
        REPORT_ROWS.append({
            "dataset": dataset,
            "year": year,
            "spec": spec,
            "sample": sample,
            "x_column": x_col,
            "y_column": y_col,
            "controls": controls,
            "n": 0,
            "slope": None,
            "robust_se": None,
            "intercept": None,
            "r_squared": None,
            "p_value": None,
            "note": note or "no valid rows",
        })
        return

    # ----------------------------------
    # Run regression with robust SEs
    # ----------------------------------
    y = data[y_col]
    X = data[[x_col] + controls]
    X = sm.add_constant(X)

    model = sm.OLS(y, X).fit(cov_type="HC1")  # robust SEs

    # ----------------------------------
    # Store results (main coefficient)
    # ----------------------------------
    REPORT_ROWS.append({
        "dataset": dataset,
        "year": year,
        "spec": spec,
        "sample": sample,
        "x_column": x_col,
        "y_column": y_col,
        "controls": controls,
        "n": int(model.nobs),
        "slope": model.params.get(x_col),
        "robust_se": model.bse.get(x_col),
        "intercept": model.params.get("const"),
        "r_squared": model.rsquared,
        "p_value": model.pvalues.get(x_col),
        "note": note,
    })

    if MAKE_PLOTS:
        save_regression_plot(
            model=model,
            data=data,
            dataset=dataset,
            year=year,
            spec=spec,
            sample=sample,
            x_col=x_col,
            y_col=y_col,
            controls=controls
        )


for exclude_group in EXCLUDE_GROUPS:

    # CSCC 2020: noncoop_optimal_mu_spec{spec}
    filename = "output/data/mitigation_cscc_v_cntfc_2020.csv"
    df = pd.read_csv(filename)
    for spec in ["1", "2", "3", "4"]:
        x_col = f"noncoop_optimal_mu_spec{spec}"
        for controls in CONTROLS:
            for y_col in OUTCOME_COLS:
                add_regression_row(
                    dataset="cscc",
                    year=2020,
                    spec=spec,
                    x_col=x_col,
                    y_col=y_col,
                    controls=controls,
                    df=df,
                    exclude_group=exclude_group,
                )

            # also regress carbon prices on cscc
            for carbon_price in ['carbon_price_effective', 'carbon_price_dolphin_ghg', 'carbon_price_dolphin_co2',
                                 'carbon_price_effective_no_zeros', 'carbon_price_dolphin_ghg_no_zeros', 'carbon_price_dolphin_co2_no_zeros'
                                 ]:

                for x_col2 in [f'scc_mid_spec{spec}', f'scc_mid_spec{spec}_pc']:
                    add_regression_row(
                                dataset="cscc",
                                year=2020,
                                spec=spec,
                                x_col=x_col2,
                                y_col=carbon_price,
                                controls=controls,
                                df=df,
                                exclude_group=exclude_group
                            )
                    if controls and x_col2.endswith("_pc"): # also run controlling for log_pop
                        add_regression_row(
                                dataset="cscc",
                                year=2020,
                                spec=spec,
                                x_col=x_col2,
                                y_col=carbon_price,
                                controls=controls+["log_pop"],
                                df=df,
                                exclude_group=exclude_group
                            )

    # RICE 2022: NONCOOP_{scenario}
    rice_filename = "output/data/mitigation_rice_v_cntfc_2022.csv"
    df_rice = pd.read_csv(rice_filename)
    country_mapping = pd.read_json("input/policy_int_to_iso3.json", typ="series")
    df_rice = df_rice[df_rice["n"].isin(country_mapping.values)]
    
    for spec in ["1", "2", "3", "4"]:
        scenario = SPEC_MAP[spec]
        x_col = f"NONCOOP_{scenario}"
        for controls in CONTROLS:
            for y_col in OUTCOME_COLS:
                    add_regression_row(
                        dataset="rice",
                        year=2022,
                        spec=spec,
                        x_col=x_col,
                        y_col=y_col,
                        controls=controls,
                        df=df_rice,
                        exclude_group=exclude_group,
                    )

report = pd.DataFrame(REPORT_ROWS)
report = report[
    ["dataset", "year", "spec", "sample", "x_column", "y_column", "controls", "n", "slope", "robust_se", "intercept", "r_squared", "p_value", "note"]
]

output_dir = "output/regressions"
os.makedirs(output_dir, exist_ok=True)
output_csv = os.path.join(output_dir, "_regression_coefficients_table.csv")
report.to_csv(output_csv, index=False)

print("Regression coefficients table")
print(report.to_string(index=False, float_format="{:.6g}".format))
print(f"\nSaved CSV to {output_csv}")
