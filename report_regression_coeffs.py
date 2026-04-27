import os

import pandas as pd
from scipy import stats

SPEC_MAP = {
    "1": "ssp2_BHM-SR_0.015",
    "2": "ssp2_BHM-LR_0.001",
    "3": "ssp1_BHM-SRdiff_0.03",
    "4": "ssp2_DJO_0.015",
}

EXCLUDE_GROUPS = [
    ("full", []),
    ("no_us_chn_ind", ["usa", "chn", "ind"]),
]

REPORT_ROWS = []


def add_regression_row(dataset, year, spec, x_col, y_col, df, exclude_codes=None):
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
    if exclude_codes:
        sample = "no_us_chn_ind"
        note = "excluded US, CHN, IND"
        df_sub = df_sub[~df_sub["n"].astype(str).str.lower().isin([code.lower() for code in exclude_codes])]

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
        "note": note,
    })


# CSCC 2020: noncoop_optimal_mu_spec{spec}
for spec in ["1", "2", "3", "4"]:
    filename = "output/data/mitigation_cscc_v_cntfc_2020.csv"
    df = pd.read_csv(filename)
    x_col = f"noncoop_optimal_mu_spec{spec}"
    for y_col in ["policy_den_cntfc", "policy_strng_cntfc"]:
        for group_name, exclude_codes in EXCLUDE_GROUPS:
            add_regression_row(
                dataset="cscc",
                year=2020,
                spec=spec,
                x_col=x_col,
                y_col=y_col,
                df=df,
                exclude_codes=exclude_codes,
            )

# RICE 2022: NONCOOP_{scenario}
rice_filename = "output/data/mitigation_rice_v_cntfc_2022.csv"
if os.path.exists(rice_filename):
    df_rice = pd.read_csv(rice_filename)
    country_mapping = pd.read_json("policy_den_to_iso3.json", typ="series")
    df_rice = df_rice[df_rice["n"].isin(country_mapping.values)]

    for spec in ["1", "2", "3", "4"]:
        scenario = SPEC_MAP[spec]
        x_col = f"NONCOOP_{scenario}"
        for y_col in ["policy_den_cntfc", "policy_strng_cntfc"]:
            for group_name, exclude_codes in EXCLUDE_GROUPS:
                add_regression_row(
                    dataset="rice",
                    year=2022,
                    spec=spec,
                    x_col=x_col,
                    y_col=y_col,
                    df=df_rice,
                    exclude_codes=exclude_codes,
                )
else:
    for spec in ["1", "2", "3", "4"]:
        for y_col in ["policy_den_cntfc", "policy_strng_cntfc"]:
            REPORT_ROWS.append({
                "dataset": "rice",
                "year": 2022,
                "spec": spec,
                "sample": "full",
                "x_column": f"NONCOOP_{SPEC_MAP[spec]}",
                "y_column": y_col,
                "n": 0,
                "slope": None,
                "intercept": None,
                "r_squared": None,
                "p_value": None,
                "note": "rice data file missing",
            })

report = pd.DataFrame(REPORT_ROWS)
report = report[
    ["dataset", "year", "spec", "sample", "x_column", "y_column", "n", "slope", "intercept", "r_squared", "p_value", "note"]
]

output_dir = "output/charts"
os.makedirs(output_dir, exist_ok=True)
output_csv = os.path.join(output_dir, "regression_coefficients_table.csv")
report.to_csv(output_csv, index=False)

print("Regression coefficients table")
print(report.to_string(index=False, float_format="{:.6g}".format))
print(f"\nSaved CSV to {output_csv}")
