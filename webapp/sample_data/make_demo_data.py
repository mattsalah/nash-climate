"""Generate the synthetic dataset used by ``server.py --demo``.

The real dataset (``output/data/mitigation_cscc_v_cntfc_<year>.csv``) needs
GAMS, Stata and several licensed/downloaded inputs, and is git-ignored. This
script writes a file with the same schema and plausible-looking magnitudes so
the web app can be run, reviewed and tested without that toolchain.

THE NUMBERS ARE MADE UP. They are drawn from a seeded RNG and must never be
used for analysis.

    python webapp/sample_data/make_demo_data.py [year ...]
"""

from __future__ import annotations

import csv
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(HERE))

from macmab import solve_optimal_mu  # noqa: E402

# Global SCC per specification, matching generate_cscc_vs_cntfc.py.
GLOBAL_SCC = {"1": 418.0, "2": 781.0, "3": 135.0, "4": 406.0}

# Country-SCC multipliers per specification, roughly tracking the global ones.
SPEC_SCALE = {"1": 1.0, "2": 1.9, "3": 0.32, "4": 0.97}

# Countries with deliberately missing pieces, so the UI's "incomplete data"
# and warning paths get exercised in the demo.
NO_MACC = {"isl", "lux"}
NO_STRINGENCY = {"col"}

COLUMNS = (
    ["n"]
    + [f"scc_{band}_spec{spec}" for spec in "1234" for band in ("low", "mid", "high")]
    + [f"global_scc_mid_spec{spec}" for spec in "1234"]
    + ["macc_a", "macc_d"]
    + [f"{kind}_optimal_mu_spec{spec}" for spec in "1234" for kind in ("coop", "noncoop")]
    + [
        "policy_den_cntfc",
        "policy_den_cntfc_low",
        "policy_den_cntfc_high",
        "policy_strng_cntfc",
        "policy_strng_cntfc_low",
        "policy_strng_cntfc_high",
        "pop",
        "gdppc",
    ]
)


def country_codes():
    path = os.path.join(REPO_ROOT, "input", "policy_int_to_iso3.json")
    with open(path, encoding="utf-8") as handle:
        return sorted(set(json.load(handle).values()))


def build_row(code: str, year: int, rng: random.Random) -> dict:
    row = {"n": code}

    # Country-level SCC: heavy-tailed, a handful of large-damage countries.
    base_scc = round(rng.lognormvariate(1.8, 1.1), 2)
    for spec, scale in SPEC_SCALE.items():
        mid = round(base_scc * scale, 2)
        row[f"scc_mid_spec{spec}"] = mid
        row[f"scc_low_spec{spec}"] = round(mid * 0.45, 2)
        row[f"scc_high_spec{spec}"] = round(mid * 2.1, 2)
        row[f"global_scc_mid_spec{spec}"] = GLOBAL_SCC[spec]

    if code in NO_MACC:
        # Matches the real data, where absent Enerdata coverage shows up as 0.
        row["macc_a"] = 0.0
        row["macc_d"] = 0.0
    else:
        row["macc_a"] = round(rng.uniform(180, 950), 2)
        row["macc_d"] = round(rng.uniform(80, 520), 2)

    a, d = row["macc_a"], row["macc_d"]
    for spec in "1234":
        for kind, scc in (
            ("coop", row[f"global_scc_mid_spec{spec}"]),
            ("noncoop", row[f"scc_mid_spec{spec}"]),
        ):
            mu = None if (a == 0 and d == 0) else solve_optimal_mu(scc, a, d)
            row[f"{kind}_optimal_mu_spec{spec}"] = "" if mu is None else round(mu, 4)

    # Realized abatement (percent of emissions avoided vs. a frozen-policy
    # counterfactual), drifting upwards with the year as the real series does.
    drift = 1.0 + 0.06 * (year - 2020)
    density = max(0.0, round(rng.gammavariate(2.0, 3.2) * drift, 3))
    row["policy_den_cntfc"] = density
    row["policy_den_cntfc_low"] = round(density * 0.55, 3)
    row["policy_den_cntfc_high"] = round(density * 1.45, 3)

    if code in NO_STRINGENCY:
        row["policy_strng_cntfc"] = ""
        row["policy_strng_cntfc_low"] = ""
        row["policy_strng_cntfc_high"] = ""
    else:
        stringency = max(0.0, round(density * rng.uniform(0.5, 1.6), 3))
        row["policy_strng_cntfc"] = stringency
        row["policy_strng_cntfc_low"] = round(stringency * 0.5, 3)
        row["policy_strng_cntfc_high"] = round(stringency * 1.5, 3)

    row["pop"] = int(rng.uniform(3e5, 1.4e9))
    row["gdppc"] = round(rng.uniform(1500, 95000), 2)
    return row


def write_year(year: int, out_dir: str = HERE) -> str:
    # Seeded on the year so re-running reproduces the file byte for byte.
    rng = random.Random(20200 + year)
    path = os.path.join(out_dir, f"mitigation_cscc_v_cntfc_{year}.csv")
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for code in country_codes():
            writer.writerow(build_row(code, year, rng))
    return path


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    years = [int(value) for value in argv] or [2015, 2020, 2025]
    for year in years:
        print(f"wrote {write_year(year)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
