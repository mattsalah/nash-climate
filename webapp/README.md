# MAC/MAB comparison web app

An interactive version of the chart `plot_MAC_MAB.py` produces: for a given
country, where does its **realized, policy-driven abatement** sit relative to
the abatement implied by the **non-cooperative (Nash)** and **cooperative
(global)** optima?

Pick a country, year, damage specification and abatement measure from the
dropdowns and the chart plus an over/under-abatement verdict update immediately.

## Running it

```
python webapp/server.py            # reads output/data/, opens on :8000
python webapp/server.py --demo     # synthetic sample data, no pipeline needed
python webapp/server.py --port 8080 --host 0.0.0.0
```

Then open <http://127.0.0.1:8000/>.

Standard library only — no Flask, pandas, GAMS or Stata. Anything Python 3.8+
can run it.

## Data

The app reads the same files `generate_cscc_vs_cntfc.py` writes:

```
output/data/mitigation_cscc_v_cntfc_<year>.csv
```

The **Year** dropdown lists every year for which such a file exists. Today the
generator hardcodes 2020, so a fresh checkout offers only 2020 — generate more
files and they appear in the dropdown without any change to the app. Files are
re-read when their mtime changes, so regenerating a CSV while the server runs
is picked up on the next request.

Columns consumed per country row (`n`):

| Column | Used for |
|---|---|
| `macc_a`, `macc_d` | the MAC curve `a·μ + d·μ⁴` |
| `scc_mid_spec<1-4>` | local MAB line (country SCC) |
| `global_scc_mid_spec<1-4>` | global MAB line |
| `noncoop_optimal_mu_spec<1-4>` | Nash optimum marker |
| `coop_optimal_mu_spec<1-4>` | cooperative optimum marker |
| `policy_den_cntfc[_low/_high]` | realized abatement, policy density |
| `policy_strng_cntfc[_low/_high]` | realized abatement, policy stringency |

Zero MACC coefficients mean missing Enerdata coverage, not zero cost — those
countries are shown as *(incomplete data)* and cannot be charted. If the
`*_optimal_mu_*` columns are missing the app re-solves `MAC(μ) = SCC` itself, so
older CSVs still work. Country display names come from
`input/policy_int_to_iso3.json`.

### Demo data

`--demo` serves `webapp/sample_data/`, written by
`webapp/sample_data/make_demo_data.py`. **Those numbers are synthetic** (seeded
RNG, plausible magnitudes only) and exist so the interface can be run, reviewed
and tested without GAMS, Stata and the licensed input datasets. The UI shows a
banner in this mode. Never use them for analysis.

## Controls

* **Country** / **Year** / **Specification** — spec labels match
  `plot_MAC_MAB.py`: 1 Baseline, 2 High Damages, 3 Low Damages, 4 Fixed
  Discounting.
* **Realized abatement measure** — policy density, policy stringency, or both.
  Both are percentage emissions reductions relative to a counterfactual holding
  policy at its 2015 level, from `policy_intensity_counterfactuals.do`.
* **Benchmarks** — show the Nash line/marker, the cooperative one, or both.
* **Axis scale** — the cooperative optimum is often an order of magnitude above
  realized abatement, which squashes the Nash comparison against the left edge.
  *Zoom to Nash* scales the axes to the Nash and realized markers instead;
  series outside the window are labelled *off scale* rather than dropped.

Each measure × benchmark pair gets a verdict card: over-abating, under-abating
or on target (within 0.5 percentage points), with the gap, the ratio to the
optimum, and the **forgone net benefit** — the net benefit at the benchmark
minus the net benefit at realized abatement, in $ per tonne of BAU emissions:

```
NB(μ) = SCC·μ − (a·μ²/2 + d·μ⁵/5)
```

which is the integral form of the MAC curve, matching the `ABATECOST` equation
documented in the top-level README.

## HTTP API

| Endpoint | Parameters | Returns |
|---|---|---|
| `/api/meta` | – | available years, specs, measures, benchmarks, focus modes |
| `/api/countries` | `year`, `spec`, `measure` | country codes/names with a completeness flag |
| `/api/chart` | `country`, `year`, `spec`, `measure`, `benchmark`, `focus` | curve, lines, markers, verdicts |

`measure` and `benchmark` accept comma-separated lists. Unknown values fall back
to defaults; a missing country is a 404 and a chartable-but-incomplete country
is a 422 with an explanation.

## Layout

```
webapp/
  server.py            HTTP server, routing, CLI
  macmab.py            data loading + MAC/MAB/verdict maths (no HTTP)
  static/              index.html, app.js, styles.css (hand-rolled SVG chart)
  sample_data/         synthetic demo CSVs + the script that writes them
  tests/test_webapp.py unit + end-to-end API tests
```

## Tests

```
python -m unittest discover -s webapp/tests
```

Covers the MAC arithmetic (including that `abatement_cost` really is the
integral of `mac`, and that the solver inverts the curve), CSV parsing and
cache invalidation, the over/under verdicts, axis framing, and the HTTP API
including its error codes and static-path traversal handling.
