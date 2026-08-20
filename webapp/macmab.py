"""Model and data-access layer for the MAC/MAB comparison web app.

This mirrors the calculations in ``plot_MAC_MAB.py`` so that the interactive
charts show exactly what the static matplotlib charts show, but as data the
browser can draw.

Conventions (kept identical to the rest of the repo):

* ``mu`` is an abatement rate expressed in **percent** (0-100) everywhere it is
  exposed to the UI, matching the ``*_optimal_mu_*`` and ``policy_*_cntfc``
  columns produced by ``generate_cscc_vs_cntfc.py``.
* The marginal abatement cost curve is defined on the **fraction** mu/100:

      MAC(mu) = a * (mu/100) + d * (mu/100)**4          [$/tCO2]

* Its integral is the total abatement cost per tonne of BAU emissions:

      AC(mu) = a * (mu/100)**2 / 2 + d * (mu/100)**5 / 5   [$/tCO2 of BAU]

Deliberately dependency-free (standard library only) so the app runs with a
bare Python install, without the GAMS/pandas/Stata toolchain the analysis
pipeline needs.
"""

from __future__ import annotations

import csv
import json
import math
import os
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

# --------------------------------------------------------------------------
# Static configuration
# --------------------------------------------------------------------------

#: Filenames written by ``generate_cscc_vs_cntfc.py``.
DATA_FILE_RE = re.compile(r"^mitigation_cscc_v_cntfc_(\d{4})\.csv$")

DEFAULT_YEAR = 2020

#: Damage/discounting specifications, same labels as ``plot_MAC_MAB.py``.
SPECS = {
    "1": "Baseline",
    "2": "High Damages",
    "3": "Low Damages",
    "4": "Fixed Discounting",
}

#: The empirical "realized abatement" measures available in the dataset.
MEASURES = {
    "den": {
        "label": "Policy density",
        "description": (
            "Emissions avoided relative to a counterfactual holding cumulative "
            "policy count at its 2015 level (Eskander & Fankhauser style)."
        ),
        "value": "policy_den_cntfc",
        "low": "policy_den_cntfc_low",
        "high": "policy_den_cntfc_high",
    },
    "strng": {
        "label": "Policy stringency",
        "description": (
            "Emissions avoided relative to a counterfactual holding the "
            "weighted policy stringency index at its 2015 level."
        ),
        "value": "policy_strng_cntfc",
        "low": "policy_strng_cntfc_low",
        "high": "policy_strng_cntfc_high",
    },
}

#: Benchmarks the realized abatement is compared against.
BENCHMARKS = {
    "nash": {
        "label": "Non-cooperative (Nash) optimum",
        "description": (
            "Abatement where the country's own marginal abatement cost equals "
            "its country-level SCC - the best response if it ignores damages "
            "it imposes on others."
        ),
        "mu_col": "noncoop_optimal_mu_spec{spec}",
        "scc_col": "scc_mid_spec{spec}",
    },
    "coop": {
        "label": "Cooperative (global) optimum",
        "description": (
            "Abatement where marginal abatement cost equals the global SCC - "
            "the globally efficient level."
        ),
        "mu_col": "coop_optimal_mu_spec{spec}",
        "scc_col": "global_scc_mid_spec{spec}",
    },
}

#: How far past the right-most marker the curve is drawn, as in plot_MAC_MAB.py.
X_PADDING = 1.2

#: X-axis framing. The cooperative optimum is often an order of magnitude above
#: realized abatement, which squashes the Nash comparison into the left edge;
#: "nash" scales the axis to the Nash and realized markers instead.
FOCUS_MODES = {
    "all": "Fit every marker",
    "nash": "Zoom to Nash and realized abatement",
}

#: Abatement points below this (percent) are treated as "on target".
VERDICT_TOLERANCE_PCT = 0.5


# --------------------------------------------------------------------------
# MAC / benefit arithmetic
# --------------------------------------------------------------------------


def mac(mu_pct: float, a: float, d: float) -> float:
    """Marginal abatement cost ($/tCO2) at abatement rate ``mu_pct`` percent."""
    mu = mu_pct / 100.0
    return a * mu + d * mu**4


def abatement_cost(mu_pct: float, a: float, d: float) -> float:
    """Total abatement cost per tonne of BAU emissions ($/tCO2 of BAU)."""
    mu = mu_pct / 100.0
    return a * mu**2 / 2.0 + d * mu**5 / 5.0


def net_benefit(mu_pct: float, scc: float, a: float, d: float) -> float:
    """Net benefit of abating ``mu_pct`` percent, per tonne of BAU emissions.

    Benefit is ``scc * mu`` (avoided damage valued at the relevant SCC) and
    cost is :func:`abatement_cost`, both in $/tCO2 of BAU emissions.
    """
    return scc * (mu_pct / 100.0) - abatement_cost(mu_pct, a, d)


def solve_optimal_mu(scc: float, a: float, d: float) -> Optional[float]:
    """Abatement rate (percent) where MAC equals ``scc``.

    ``MAC`` is strictly increasing in ``mu`` for non-negative ``a``/``d``, so a
    bisection is both robust and exact enough here. Used only as a fallback:
    the dataset normally carries the pre-solved columns written by
    ``generate_cscc_vs_cntfc.py``.
    """
    if any(v is None or math.isnan(v) for v in (scc, a, d)):
        return None
    if scc <= 0:
        return 0.0
    if a <= 0 and d <= 0:
        return None

    lo, hi = 0.0, 1.0
    # Expand the bracket until MAC(hi) exceeds the SCC (abatement can exceed
    # 100% in principle; the curve is defined for mu > 1 too).
    for _ in range(80):
        if mac(hi * 100.0, a, d) >= scc:
            break
        hi *= 2.0
    else:
        return None

    for _ in range(200):
        mid = (lo + hi) / 2.0
        if mac(mid * 100.0, a, d) < scc:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0 * 100.0


# --------------------------------------------------------------------------
# Dataset loading
# --------------------------------------------------------------------------


def _to_float(raw: Optional[str]) -> Optional[float]:
    """Parse a CSV cell into a float, mapping blanks and NaNs to ``None``."""
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    if math.isnan(value) or math.isinf(value):
        return None
    return value


@dataclass
class Dataset:
    """One ``mitigation_cscc_v_cntfc_<year>.csv`` file, indexed by country."""

    year: int
    path: str
    rows: Dict[str, Dict[str, Optional[float]]]

    def get(self, country: str) -> Optional[Dict[str, Optional[float]]]:
        return self.rows.get(country.strip().lower())

    def countries(self) -> List[str]:
        return sorted(self.rows)


def discover_years(data_dir: str) -> List[int]:
    """Years for which a generated CSV exists in ``data_dir``."""
    try:
        names = os.listdir(data_dir)
    except OSError:
        return []
    years = [int(m.group(1)) for m in map(DATA_FILE_RE.match, names) if m]
    return sorted(years)


def data_path(data_dir: str, year: int) -> str:
    return os.path.join(data_dir, f"mitigation_cscc_v_cntfc_{year}.csv")


def load_dataset(data_dir: str, year: int) -> Dataset:
    """Read one year's dataset. Raises ``FileNotFoundError`` if not generated."""
    path = data_path(data_dir, year)
    rows: Dict[str, Dict[str, Optional[float]]] = {}
    with open(path, newline="", encoding="utf-8-sig") as handle:
        for record in csv.DictReader(handle):
            code = (record.get("n") or "").strip().lower()
            if not code:
                continue
            rows[code] = {
                key: _to_float(value)
                for key, value in record.items()
                if key and key != "n"
            }
    return Dataset(year=year, path=path, rows=rows)


class DatasetCache:
    """Loads datasets on demand and reloads them when the file changes.

    Regenerating a CSV while the server is running therefore shows up on the
    next request instead of requiring a restart.
    """

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self._cache: Dict[int, tuple] = {}

    def years(self) -> List[int]:
        return discover_years(self.data_dir)

    def get(self, year: int) -> Dataset:
        path = data_path(self.data_dir, year)
        stamp = os.stat(path).st_mtime_ns  # FileNotFoundError propagates.
        cached = self._cache.get(year)
        if cached is None or cached[0] != stamp:
            cached = (stamp, load_dataset(self.data_dir, year))
            self._cache[year] = cached
        return cached[1]


def load_country_names(mapping_path: str) -> Dict[str, str]:
    """Invert ``input/policy_int_to_iso3.json`` into code -> display name."""
    try:
        with open(mapping_path, encoding="utf-8") as handle:
            name_to_code = json.load(handle)
    except (OSError, ValueError):
        return {}
    return {
        str(code).strip().lower(): str(name)
        for name, code in name_to_code.items()
        if isinstance(code, str)
    }


# --------------------------------------------------------------------------
# Chart assembly
# --------------------------------------------------------------------------


def _benchmark_mu(
    row: Dict[str, Optional[float]], key: str, spec: str, a: float, d: float
) -> Optional[float]:
    """Pre-solved optimal mu for a benchmark, re-solving it if the column is absent."""
    config = BENCHMARKS[key]
    mu = row.get(config["mu_col"].format(spec=spec))
    if mu is not None:
        return mu
    scc = row.get(config["scc_col"].format(spec=spec))
    if scc is None:
        return None
    return solve_optimal_mu(scc, a, d)


def _verdict(realized: float, target: float) -> str:
    gap = realized - target
    if abs(gap) <= VERDICT_TOLERANCE_PCT:
        return "on_target"
    return "over" if gap > 0 else "under"


def has_macc(row: Dict[str, Optional[float]]) -> bool:
    """Whether a row carries usable MACC coefficients (0 means missing coverage)."""
    a, d = row.get("macc_a"), row.get("macc_d")
    return a is not None and d is not None and not (a == 0 and d == 0)


def country_summary(
    dataset: Dataset, country: str, spec: str, measure_keys: Iterable[str]
) -> Optional[Dict]:
    """Compact per-country status used for the country picker.

    ``has_data`` marks a country as chartable: MACC coefficients, a country
    SCC, and *at least one* of the selected realized-abatement measures. A
    country missing one of two selected measures still charts fine - the
    missing series just comes back as a warning.
    """
    row = dataset.get(country)
    if row is None:
        return None
    complete = (
        has_macc(row)
        and row.get(f"scc_mid_spec{spec}") is not None
        and any(row.get(MEASURES[key]["value"]) is not None for key in measure_keys)
    )
    return {"code": country, "has_data": complete}


def build_chart(
    dataset: Dataset,
    country: str,
    spec: str,
    measure_keys: List[str],
    benchmark_keys: List[str],
    country_names: Optional[Dict[str, str]] = None,
    focus: str = "all",
) -> Dict:
    """Build the JSON payload the browser draws.

    Returns a dict with the MAC curve, the flat marginal-benefit lines, the
    vertical markers (benchmarks plus realized abatement measures) and, for
    every (measure, benchmark) pair, an over/under-abatement verdict.
    """
    if spec not in SPECS:
        raise ValueError(f"Unknown spec: {spec}")
    if focus not in FOCUS_MODES:
        raise ValueError(f"Unknown focus mode: {focus}")
    for key in measure_keys:
        if key not in MEASURES:
            raise ValueError(f"Unknown measure: {key}")
    for key in benchmark_keys:
        if key not in BENCHMARKS:
            raise ValueError(f"Unknown benchmark: {key}")

    code = country.strip().lower()
    row = dataset.get(code)
    if row is None:
        raise KeyError(country)

    if not has_macc(row):
        raise ValueError(
            f"No MACC coefficients for '{code}' - Enerdata coverage is missing "
            "for this region (zero coefficients are missing, not zero cost)."
        )

    a, d = row["macc_a"], row["macc_d"]
    names = country_names or {}
    warnings: List[str] = []

    # --- marginal benefit lines (flat: the SCC does not vary with mu) -------
    benefit_lines = []
    for key in benchmark_keys:
        scc = row.get(BENCHMARKS[key]["scc_col"].format(spec=spec))
        if scc is None:
            warnings.append(f"No SCC for the {BENCHMARKS[key]['label'].lower()}.")
            continue
        benefit_lines.append(
            {
                "key": key,
                "label": "Local MAB (country SCC)" if key == "nash" else "Global MAB (global SCC)",
                "value": scc,
            }
        )

    # --- vertical markers --------------------------------------------------
    benchmarks = []
    for key in benchmark_keys:
        mu = _benchmark_mu(row, key, spec, a, d)
        if mu is None:
            continue
        scc = row.get(BENCHMARKS[key]["scc_col"].format(spec=spec))
        benchmarks.append(
            {
                "key": key,
                "label": BENCHMARKS[key]["label"],
                "description": BENCHMARKS[key]["description"],
                "mu": mu,
                "scc": scc,
                "mac": mac(mu, a, d),
            }
        )

    measures = []
    for key in measure_keys:
        config = MEASURES[key]
        mu = row.get(config["value"])
        if mu is None:
            warnings.append(f"No {config['label'].lower()} counterfactual for this country.")
            continue
        measures.append(
            {
                "key": key,
                "label": config["label"],
                "description": config["description"],
                "mu": mu,
                "low": row.get(config["low"]),
                "high": row.get(config["high"]),
                "mac": mac(mu, a, d),
            }
        )

    # --- verdicts ----------------------------------------------------------
    verdicts = []
    for measure in measures:
        for benchmark in benchmarks:
            scc = benchmark["scc"]
            loss = None
            if scc is not None:
                loss = net_benefit(benchmark["mu"], scc, a, d) - net_benefit(
                    measure["mu"], scc, a, d
                )
            ratio = measure["mu"] / benchmark["mu"] if benchmark["mu"] else None
            verdicts.append(
                {
                    "measure": measure["key"],
                    "measure_label": measure["label"],
                    "benchmark": benchmark["key"],
                    "benchmark_label": benchmark["label"],
                    "realized_mu": measure["mu"],
                    "target_mu": benchmark["mu"],
                    "gap": measure["mu"] - benchmark["mu"],
                    "ratio": ratio,
                    "status": _verdict(measure["mu"], benchmark["mu"]),
                    # Forgone net benefit from sitting off the optimum, in
                    # dollars per tonne of BAU emissions.
                    "forgone_net_benefit": loss,
                }
            )

    # --- x range and MAC curve --------------------------------------------
    framing = benchmarks
    if focus == "nash":
        nash_only = [b for b in benchmarks if b["key"] == "nash"]
        framing = nash_only or benchmarks  # fall back if there is no Nash point

    marker_mus = [m["mu"] for m in framing] + [m["mu"] for m in measures]
    marker_mus += [m["high"] for m in measures if m["high"] is not None]
    if not marker_mus:
        raise ValueError(f"Nothing to plot for '{code}' under specification {spec}.")

    x_max = max(marker_mus) * X_PADDING
    if x_max <= 0:
        x_max = 1.0
    x_min = min(0.0, min(marker_mus) * X_PADDING)

    steps = 400
    curve = []
    for i in range(steps + 1):
        mu = x_min + (x_max - x_min) * i / steps
        curve.append({"mu": mu, "mac": mac(mu, a, d)})

    # The MAC curve is monotone, so the visible window is bounded by its ends.
    # Anything above it (typically the global MAB when zoomed to Nash) is
    # flagged rather than allowed to stretch the axis.
    y_min = min(0.0, mac(x_min, a, d))
    y_top = mac(x_max, a, d)
    y_max = y_min + (y_top - y_min) * 1.08 if y_top > y_min else y_min + 1.0

    for line in benefit_lines:
        line["off_scale"] = not (y_min <= line["value"] <= y_max)
    for marker in benchmarks + measures:
        marker["off_scale"] = not (x_min <= marker["mu"] <= x_max)

    return {
        "country": code,
        "country_name": names.get(code, code.upper()),
        "year": dataset.year,
        "spec": spec,
        "spec_label": SPECS[spec],
        "focus": focus,
        "macc": {"a": a, "d": d},
        "x_range": [x_min, x_max],
        "y_range": [y_min, y_max],
        "curve": curve,
        "benefit_lines": benefit_lines,
        "benchmarks": benchmarks,
        "measures": measures,
        "verdicts": verdicts,
        "warnings": warnings,
    }
