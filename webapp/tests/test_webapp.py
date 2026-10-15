"""Tests for the MAC/MAB web app: model arithmetic, data loading and HTTP API.

    python -m unittest discover -s webapp/tests
"""

from __future__ import annotations

import json
import math
import os
import sys
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

WEBAPP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WEBAPP_DIR)

import macmab  # noqa: E402
import server  # noqa: E402


def write_csv(directory: str, year: int, rows) -> str:
    """Write a minimal dataset with the columns build_chart consumes."""
    columns = [
        "n",
        "scc_mid_spec1",
        "global_scc_mid_spec1",
        "macc_a",
        "macc_d",
        "noncoop_optimal_mu_spec1",
        "coop_optimal_mu_spec1",
        "policy_den_cntfc",
        "policy_den_cntfc_low",
        "policy_den_cntfc_high",
        "policy_strng_cntfc",
        "policy_strng_cntfc_low",
        "policy_strng_cntfc_high",
    ]
    path = os.path.join(directory, f"mitigation_cscc_v_cntfc_{year}.csv")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(",".join(columns) + "\n")
        for row in rows:
            handle.write(",".join(str(row.get(column, "")) for column in columns) + "\n")
    return path


BASE_ROW = {
    "n": "usa",
    "scc_mid_spec1": 50.0,
    "global_scc_mid_spec1": 418.0,
    "macc_a": 500.0,
    "macc_d": 300.0,
    "noncoop_optimal_mu_spec1": 9.9,
    "coop_optimal_mu_spec1": 70.0,
    "policy_den_cntfc": 4.0,
    "policy_den_cntfc_low": 2.0,
    "policy_den_cntfc_high": 6.0,
    "policy_strng_cntfc": 12.0,
    "policy_strng_cntfc_low": 8.0,
    "policy_strng_cntfc_high": 16.0,
}


class MacArithmeticTests(unittest.TestCase):
    def test_mac_matches_the_repo_formula(self):
        # plot_MAC_MAB.py: mc = a * (mu/100) + d * (mu/100) ** 4
        self.assertAlmostEqual(macmab.mac(0, 500, 300), 0.0)
        self.assertAlmostEqual(macmab.mac(100, 500, 300), 800.0)
        self.assertAlmostEqual(macmab.mac(50, 500, 300), 500 * 0.5 + 300 * 0.5**4)

    def test_abatement_cost_is_the_integral_of_mac(self):
        a, d, mu = 480.0, 260.0, 37.0
        steps = 20000
        width = (mu / steps) / 100.0  # step width on the fraction axis
        approx = sum(  # midpoint rule
            macmab.mac(mu * (i + 0.5) / steps, a, d) * width for i in range(steps)
        )
        self.assertAlmostEqual(approx, macmab.abatement_cost(mu, a, d), places=6)

    def test_solve_optimal_mu_inverts_mac(self):
        a, d = 620.0, 410.0
        for scc in (5.0, 50.0, 418.0, 1200.0):
            mu = macmab.solve_optimal_mu(scc, a, d)
            self.assertIsNotNone(mu)
            self.assertAlmostEqual(macmab.mac(mu, a, d), scc, places=6)

    def test_solve_optimal_mu_edge_cases(self):
        self.assertEqual(macmab.solve_optimal_mu(0.0, 500, 300), 0.0)
        self.assertEqual(macmab.solve_optimal_mu(-10.0, 500, 300), 0.0)
        self.assertIsNone(macmab.solve_optimal_mu(float("nan"), 500, 300))
        self.assertIsNone(macmab.solve_optimal_mu(50.0, 0.0, 0.0))

    def test_net_benefit_peaks_at_the_optimum(self):
        a, d, scc = 500.0, 300.0, 50.0
        best = macmab.solve_optimal_mu(scc, a, d)
        peak = macmab.net_benefit(best, scc, a, d)
        for offset in (-3.0, -0.5, 0.5, 3.0):
            self.assertLess(macmab.net_benefit(best + offset, scc, a, d), peak)


class DatasetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = self.tmp.name

    def test_discover_years_ignores_other_files(self):
        write_csv(self.dir, 2020, [BASE_ROW])
        write_csv(self.dir, 2015, [BASE_ROW])
        open(os.path.join(self.dir, "mitigation_rice_v_cntfc_2022.csv"), "w").close()
        open(os.path.join(self.dir, "notes.txt"), "w").close()
        self.assertEqual(macmab.discover_years(self.dir), [2015, 2020])

    def test_discover_years_on_missing_directory(self):
        self.assertEqual(macmab.discover_years(os.path.join(self.dir, "nope")), [])

    def test_blank_and_nan_cells_become_none(self):
        row = dict(BASE_ROW, n="fra", policy_strng_cntfc="", policy_den_cntfc="nan")
        write_csv(self.dir, 2020, [row])
        dataset = macmab.load_dataset(self.dir, 2020)
        self.assertIsNone(dataset.get("fra")["policy_strng_cntfc"])
        self.assertIsNone(dataset.get("fra")["policy_den_cntfc"])

    def test_lookup_is_case_insensitive(self):
        write_csv(self.dir, 2020, [BASE_ROW])
        dataset = macmab.load_dataset(self.dir, 2020)
        self.assertIsNotNone(dataset.get("USA"))
        self.assertIsNotNone(dataset.get(" usa "))

    def test_cache_reloads_when_the_file_changes(self):
        write_csv(self.dir, 2020, [BASE_ROW])
        cache = macmab.DatasetCache(self.dir)
        self.assertEqual(cache.get(2020).get("usa")["policy_den_cntfc"], 4.0)

        path = write_csv(self.dir, 2020, [dict(BASE_ROW, policy_den_cntfc=8.0)])
        stat = os.stat(path)
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
        self.assertEqual(cache.get(2020).get("usa")["policy_den_cntfc"], 8.0)


class BuildChartTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        write_csv(
            self.tmp.name,
            2020,
            [
                BASE_ROW,
                dict(BASE_ROW, n="isl", macc_a=0.0, macc_d=0.0),
                dict(BASE_ROW, n="col", policy_strng_cntfc="", policy_strng_cntfc_low="",
                     policy_strng_cntfc_high=""),
                dict(BASE_ROW, n="nor", noncoop_optimal_mu_spec1="", coop_optimal_mu_spec1=""),
            ],
        )
        self.dataset = macmab.load_dataset(self.tmp.name, 2020)

    def chart(self, country="usa", spec="1", measures=("den",), benchmarks=("nash", "coop"),
              focus="all"):
        return macmab.build_chart(
            self.dataset, country, spec, list(measures), list(benchmarks), None, focus
        )

    def test_under_abatement_is_detected(self):
        # realized density 4.0% against a 9.9% Nash optimum
        chart = self.chart(measures=["den"], benchmarks=["nash"])
        verdict = chart["verdicts"][0]
        self.assertEqual(verdict["status"], "under")
        self.assertAlmostEqual(verdict["gap"], 4.0 - 9.9)
        self.assertAlmostEqual(verdict["ratio"], 4.0 / 9.9)
        self.assertGreater(verdict["forgone_net_benefit"], 0)

    def test_over_abatement_is_detected(self):
        # realized stringency 12.0% against the same 9.9% Nash optimum
        chart = self.chart(measures=["strng"], benchmarks=["nash"])
        verdict = chart["verdicts"][0]
        self.assertEqual(verdict["status"], "over")
        self.assertGreater(verdict["gap"], 0)
        self.assertGreater(verdict["forgone_net_benefit"], 0)

    def test_on_target_within_tolerance(self):
        write_csv(self.tmp.name, 2021, [dict(BASE_ROW, policy_den_cntfc=9.95)])
        dataset = macmab.load_dataset(self.tmp.name, 2021)
        chart = macmab.build_chart(dataset, "usa", "1", ["den"], ["nash"])
        self.assertEqual(chart["verdicts"][0]["status"], "on_target")

    def test_every_measure_benchmark_pair_gets_a_verdict(self):
        chart = self.chart(measures=["den", "strng"], benchmarks=["nash", "coop"])
        pairs = {(v["measure"], v["benchmark"]) for v in chart["verdicts"]}
        self.assertEqual(
            pairs, {("den", "nash"), ("den", "coop"), ("strng", "nash"), ("strng", "coop")}
        )

    def test_missing_macc_coefficients_raise(self):
        with self.assertRaises(ValueError):
            self.chart(country="isl")

    def test_unknown_country_raises_keyerror(self):
        with self.assertRaises(KeyError):
            self.chart(country="zzz")

    def test_missing_measure_is_warned_not_fatal(self):
        chart = self.chart(country="col", measures=["den", "strng"])
        self.assertEqual([m["key"] for m in chart["measures"]], ["den"])
        self.assertTrue(chart["warnings"])

    def test_a_country_missing_one_of_two_measures_is_still_chartable(self):
        # 'col' has no stringency counterfactual but does have density
        self.assertTrue(
            macmab.country_summary(self.dataset, "col", "1", ["den", "strng"])["has_data"]
        )
        self.assertFalse(
            macmab.country_summary(self.dataset, "col", "1", ["strng"])["has_data"]
        )
        # 'isl' has no MACC coverage at all
        self.assertFalse(
            macmab.country_summary(self.dataset, "isl", "1", ["den"])["has_data"]
        )

    def test_optimal_mu_is_resolved_when_the_column_is_absent(self):
        chart = self.chart(country="nor", benchmarks=["nash"])
        nash = chart["benchmarks"][0]
        self.assertAlmostEqual(macmab.mac(nash["mu"], 500.0, 300.0), 50.0, places=6)

    def test_curve_spans_the_reported_x_range(self):
        chart = self.chart(measures=["den", "strng"])
        x_min, x_max = chart["x_range"]
        self.assertAlmostEqual(chart["curve"][0]["mu"], x_min)
        self.assertAlmostEqual(chart["curve"][-1]["mu"], x_max)
        # every marker, including CI upper bounds, must be inside the window
        for marker in chart["benchmarks"] + chart["measures"]:
            self.assertLessEqual(marker["mu"], x_max)
            self.assertGreaterEqual(marker["mu"], x_min)
        for measure in chart["measures"]:
            self.assertLessEqual(measure["high"], x_max)

    def test_focus_nash_ignores_the_cooperative_optimum_when_scaling(self):
        wide = self.chart(focus="all")
        zoomed = self.chart(focus="nash")
        self.assertLess(zoomed["x_range"][1], wide["x_range"][1])
        # the Nash optimum (9.9%) still fits, the cooperative one (70%) does not
        by_key = {b["key"]: b for b in zoomed["benchmarks"]}
        self.assertFalse(by_key["nash"]["off_scale"])
        self.assertTrue(by_key["coop"]["off_scale"])
        # both verdicts survive; only the drawing window changes
        self.assertEqual(len(zoomed["verdicts"]), len(wide["verdicts"]))

    def test_focus_nash_falls_back_when_no_nash_point_is_shown(self):
        chart = self.chart(benchmarks=["coop"], focus="nash")
        self.assertFalse(chart["benchmarks"][0]["off_scale"])

    def test_y_range_covers_the_curve_and_flags_off_scale_benefit_lines(self):
        zoomed = self.chart(focus="nash")
        y_min, y_max = zoomed["y_range"]
        for point in zoomed["curve"]:
            self.assertLessEqual(point["mac"], y_max + 1e-9)
            self.assertGreaterEqual(point["mac"], y_min - 1e-9)
        by_key = {line["key"]: line for line in zoomed["benefit_lines"]}
        self.assertFalse(by_key["nash"]["off_scale"])   # $50 local SCC
        self.assertTrue(by_key["coop"]["off_scale"])    # $418 global SCC

    def test_negative_realized_abatement_extends_the_axis_left_of_zero(self):
        # a counterfactual can come out negative when policy is associated with
        # higher emissions; the window has to include it rather than clip it
        write_csv(
            self.tmp.name,
            2022,
            [dict(BASE_ROW, policy_den_cntfc=-3.0, policy_den_cntfc_low=-5.0,
                  policy_den_cntfc_high=-1.0)],
        )
        dataset = macmab.load_dataset(self.tmp.name, 2022)
        chart = macmab.build_chart(dataset, "usa", "1", ["den"], ["nash"])
        self.assertLess(chart["x_range"][0], -3.0)
        self.assertFalse(chart["measures"][0]["off_scale"])
        self.assertEqual(chart["verdicts"][0]["status"], "under")
        self.assertLessEqual(chart["y_range"][0], 0.0)
        json.dumps(chart, allow_nan=False)

    def test_unknown_focus_mode_raises(self):
        with self.assertRaises(ValueError):
            self.chart(focus="sideways")

    def test_curve_values_match_the_mac_formula(self):
        chart = self.chart()
        for point in chart["curve"][::37]:
            self.assertAlmostEqual(point["mac"], macmab.mac(point["mu"], 500.0, 300.0))

    def test_payload_is_json_serialisable_without_nan(self):
        chart = self.chart(country="col", measures=["den", "strng"])
        json.dumps(chart, allow_nan=False)

    def test_bad_arguments_raise(self):
        with self.assertRaises(ValueError):
            self.chart(spec="9")
        with self.assertRaises(ValueError):
            self.chart(measures=["bogus"])
        with self.assertRaises(ValueError):
            self.chart(benchmarks=["bogus"])


class ApiTests(unittest.TestCase):
    """End-to-end checks against a real server bound to an ephemeral port."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        write_csv(cls.tmp.name, 2020, [BASE_ROW, dict(BASE_ROW, n="isl", macc_a=0.0, macc_d=0.0)])
        write_csv(cls.tmp.name, 2025, [BASE_ROW])
        state = server.AppState(data_dir=cls.tmp.name, demo=True)
        cls.httpd = server.make_server("127.0.0.1", 0, state)
        cls.base = "http://127.0.0.1:%d" % cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.thread.join(timeout=5)
        cls.httpd.server_close()
        cls.tmp.cleanup()

    def get(self, path):
        with urlopen(self.base + path) as response:
            return json.loads(response.read().decode("utf-8"))

    def test_meta(self):
        payload = self.get("/api/meta")
        self.assertEqual(payload["years"], [2020, 2025])
        self.assertEqual(payload["default_year"], 2020)
        self.assertTrue(payload["demo"])
        self.assertEqual([s["key"] for s in payload["specs"]], ["1", "2", "3", "4"])

    def test_countries_flags_incomplete_rows(self):
        payload = self.get("/api/countries?year=2020&spec=1&measure=den")
        flags = {c["code"]: c["has_data"] for c in payload["countries"]}
        self.assertTrue(flags["usa"])
        self.assertFalse(flags["isl"])

    def test_country_names_come_from_the_repo_mapping(self):
        payload = self.get("/api/countries?year=2020")
        names = {c["code"]: c["name"] for c in payload["countries"]}
        self.assertEqual(names["usa"], "United States of America")

    def test_chart_defaults_to_2020(self):
        payload = self.get("/api/chart?country=usa")
        self.assertEqual(payload["year"], 2020)
        self.assertEqual(payload["spec"], "1")
        self.assertEqual([m["key"] for m in payload["measures"]], ["den"])

    def test_chart_honours_selected_measures_and_benchmarks(self):
        payload = self.get("/api/chart?country=usa&year=2025&measure=den,strng&benchmark=nash")
        self.assertEqual(payload["year"], 2025)
        self.assertEqual([m["key"] for m in payload["measures"]], ["den", "strng"])
        self.assertEqual([b["key"] for b in payload["benchmarks"]], ["nash"])
        self.assertEqual([l["key"] for l in payload["benefit_lines"]], ["nash"])

    def test_unknown_country_returns_404(self):
        with self.assertRaises(HTTPError) as ctx:
            self.get("/api/chart?country=zzz")
        self.assertEqual(ctx.exception.code, 404)

    def test_unknown_year_returns_404(self):
        with self.assertRaises(HTTPError) as ctx:
            self.get("/api/chart?country=usa&year=1999")
        self.assertEqual(ctx.exception.code, 404)

    def test_missing_macc_returns_422(self):
        with self.assertRaises(HTTPError) as ctx:
            self.get("/api/chart?country=isl")
        self.assertEqual(ctx.exception.code, 422)

    def test_missing_country_parameter_returns_400(self):
        with self.assertRaises(HTTPError) as ctx:
            self.get("/api/chart")
        self.assertEqual(ctx.exception.code, 400)

    def test_unknown_spec_returns_400(self):
        for path in ("/api/chart?country=usa&spec=9", "/api/countries?spec=9"):
            with self.assertRaises(HTTPError) as ctx:
                self.get(path)
            self.assertEqual(ctx.exception.code, 400)

    def test_unknown_values_fall_back_to_defaults(self):
        payload = self.get("/api/chart?country=usa&measure=bogus&benchmark=bogus&focus=bogus")
        self.assertEqual([m["key"] for m in payload["measures"]], ["den"])
        self.assertEqual([b["key"] for b in payload["benchmarks"]], ["nash", "coop"])
        self.assertEqual(payload["focus"], "all")

    def test_focus_parameter_is_applied(self):
        wide = self.get("/api/chart?country=usa&focus=all")
        zoomed = self.get("/api/chart?country=usa&focus=nash")
        self.assertEqual(zoomed["focus"], "nash")
        self.assertLess(zoomed["x_range"][1], wide["x_range"][1])

    def test_index_and_assets_are_served(self):
        for path in ("/", "/index.html", "/app.js", "/styles.css"):
            with urlopen(self.base + path) as response:
                self.assertEqual(response.status, 200)
                self.assertTrue(response.read())

    def test_static_paths_cannot_escape_the_static_directory(self):
        for path in ("/../server.py", "/%2e%2e/server.py", "/../../etc/passwd"):
            with self.assertRaises(HTTPError) as ctx:
                self.get(path)
            self.assertEqual(ctx.exception.code, 404)


class DemoDataTests(unittest.TestCase):
    """The bundled demo dataset must actually drive the app."""

    def test_bundled_demo_data_renders(self):
        demo_dir = os.path.join(WEBAPP_DIR, "sample_data")
        years = macmab.discover_years(demo_dir)
        self.assertIn(2020, years)
        dataset = macmab.load_dataset(demo_dir, 2020)
        rendered = 0
        for code in dataset.countries():
            try:
                chart = macmab.build_chart(dataset, code, "1", ["den", "strng"], ["nash", "coop"])
            except ValueError:
                continue  # countries seeded without MACC coverage
            json.dumps(chart, allow_nan=False)
            self.assertTrue(chart["verdicts"])
            for point in chart["curve"]:
                self.assertFalse(math.isnan(point["mac"]))
            rendered += 1
        self.assertGreater(rendered, 30)

    def test_demo_optimal_mu_columns_are_consistent_with_the_mac_curve(self):
        dataset = macmab.load_dataset(os.path.join(WEBAPP_DIR, "sample_data"), 2020)
        row = dataset.get("usa")
        self.assertAlmostEqual(
            macmab.mac(row["noncoop_optimal_mu_spec1"], row["macc_a"], row["macc_d"]),
            row["scc_mid_spec1"],
            places=3,
        )


if __name__ == "__main__":
    unittest.main()
