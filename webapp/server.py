"""Small web app for comparing realized abatement to the Nash / cooperative optimum.

Interactive version of the ``plot_MAC_MAB.py`` chart: pick a country, a year, a
damage specification and an empirical abatement measure, and see where observed
abatement sits relative to where the marginal abatement cost curve crosses the
country-level and global marginal abatement benefit.

Run it with::

    python webapp/server.py                 # reads output/data/
    python webapp/server.py --demo          # synthetic data, no pipeline needed
    python webapp/server.py --port 8080

Standard library only - no Flask, pandas or GAMS required.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import posixpath
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import macmab  # noqa: E402  (after sys.path tweak so the script runs from anywhere)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
STATIC_DIR = os.path.join(HERE, "static")
DEMO_DATA_DIR = os.path.join(HERE, "sample_data")
DEFAULT_DATA_DIR = os.path.join(REPO_ROOT, "output", "data")
COUNTRY_NAMES_PATH = os.path.join(REPO_ROOT, "input", "policy_int_to_iso3.json")


class AppState:
    """Everything the request handler needs, resolved once at startup."""

    def __init__(self, data_dir: str, demo: bool):
        self.data_dir = os.path.abspath(data_dir)
        self.demo = demo
        self.cache = macmab.DatasetCache(self.data_dir)
        self.country_names = macmab.load_country_names(COUNTRY_NAMES_PATH)


class ApiError(Exception):
    def __init__(self, status: HTTPStatus, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def _one(params, key, default=None):
    values = params.get(key)
    return values[0] if values else default


def _many(params, key, allowed, default):
    """Repeated or comma-separated query values, filtered to ``allowed``."""
    raw = []
    for value in params.get(key, []):
        raw.extend(part for part in value.split(",") if part)
    picked = [value for value in raw if value in allowed]
    return picked or list(default)


def _dataset(state: AppState, params):
    years = state.cache.years()
    if not years:
        raise ApiError(
            HTTPStatus.NOT_FOUND,
            f"No datasets found in {state.data_dir}. Run generate_cscc_vs_cntfc.py "
            "first, or start the server with --demo to explore synthetic data.",
        )
    raw_year = _one(params, "year")
    if raw_year is None:
        year = macmab.DEFAULT_YEAR if macmab.DEFAULT_YEAR in years else years[0]
    else:
        try:
            year = int(raw_year)
        except ValueError:
            raise ApiError(HTTPStatus.BAD_REQUEST, f"Invalid year: {raw_year!r}")
        if year not in years:
            raise ApiError(
                HTTPStatus.NOT_FOUND,
                f"No dataset for {year}. Available: {', '.join(map(str, years))}.",
            )
    try:
        return state.cache.get(year)
    except OSError as exc:
        raise ApiError(HTTPStatus.NOT_FOUND, f"Could not read dataset for {year}: {exc}")


def handle_meta(state: AppState, params):
    years = state.cache.years()
    default_year = None
    if years:
        default_year = macmab.DEFAULT_YEAR if macmab.DEFAULT_YEAR in years else years[0]
    return {
        "years": years,
        "default_year": default_year,
        "specs": [{"key": key, "label": label} for key, label in macmab.SPECS.items()],
        "measures": [
            {"key": key, "label": cfg["label"], "description": cfg["description"]}
            for key, cfg in macmab.MEASURES.items()
        ],
        "benchmarks": [
            {"key": key, "label": cfg["label"], "description": cfg["description"]}
            for key, cfg in macmab.BENCHMARKS.items()
        ],
        "focus_modes": [
            {"key": key, "label": label} for key, label in macmab.FOCUS_MODES.items()
        ],
        "demo": state.demo,
        "data_dir": state.data_dir,
    }


def handle_countries(state: AppState, params):
    dataset = _dataset(state, params)
    spec = _one(params, "spec", "1")
    if spec not in macmab.SPECS:
        raise ApiError(HTTPStatus.BAD_REQUEST, f"Unknown spec: {spec!r}")
    measures = _many(params, "measure", macmab.MEASURES, ["den"])

    countries = []
    for code in dataset.countries():
        summary = macmab.country_summary(dataset, code, spec, measures)
        if summary is None:
            continue
        summary["name"] = state.country_names.get(code, code.upper())
        countries.append(summary)
    countries.sort(key=lambda item: (not item["has_data"], item["name"]))
    return {"year": dataset.year, "countries": countries}


def handle_chart(state: AppState, params):
    dataset = _dataset(state, params)
    country = _one(params, "country")
    if not country:
        raise ApiError(HTTPStatus.BAD_REQUEST, "Missing 'country' parameter.")
    spec = _one(params, "spec", "1")
    if spec not in macmab.SPECS:
        raise ApiError(HTTPStatus.BAD_REQUEST, f"Unknown spec: {spec!r}")
    measures = _many(params, "measure", macmab.MEASURES, ["den"])
    benchmarks = _many(params, "benchmark", macmab.BENCHMARKS, ["nash", "coop"])
    focus = _one(params, "focus", "all")
    if focus not in macmab.FOCUS_MODES:
        focus = "all"
    try:
        return macmab.build_chart(
            dataset, country, spec, measures, benchmarks, state.country_names, focus
        )
    except KeyError:
        raise ApiError(
            HTTPStatus.NOT_FOUND, f"Country {country!r} is not in the {dataset.year} dataset."
        )
    except ValueError as exc:
        raise ApiError(HTTPStatus.UNPROCESSABLE_ENTITY, str(exc))


ROUTES = {
    "/api/meta": handle_meta,
    "/api/countries": handle_countries,
    "/api/chart": handle_chart,
}


class Handler(BaseHTTPRequestHandler):
    server_version = "NashClimateWebapp/1.0"
    state: AppState  # set by :func:`make_server`

    def do_GET(self):  # noqa: N802 (BaseHTTPRequestHandler API)
        parsed = urlparse(self.path)
        path = parsed.path
        if path in ROUTES:
            self._serve_api(ROUTES[path], parse_qs(parsed.query))
        else:
            self._serve_static(path)

    def _serve_api(self, handler, params):
        try:
            payload = handler(self.state, params)
        except ApiError as exc:
            self._send_json({"error": exc.message}, status=exc.status)
        except Exception as exc:  # pragma: no cover - unexpected failure
            self.log_error("Unhandled error for %s: %r", self.path, exc)
            self._send_json(
                {"error": f"Internal error: {exc}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
        else:
            self._send_json(payload)

    def _send_json(self, payload, status=HTTPStatus.OK):
        # allow_nan=False keeps invalid JSON (NaN/Infinity) from reaching the
        # browser; the data layer already maps missing values to null.
        body = json.dumps(payload, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _resolve_static(self, path: str):
        """Map a URL path to a file inside STATIC_DIR, or ``None`` if outside it."""
        if path in ("", "/"):
            path = "/index.html"
        # Normalise on the URL side first, then confirm the result really is
        # under STATIC_DIR before touching the filesystem.
        clean = posixpath.normpath(path).lstrip("/")
        candidate = os.path.abspath(os.path.join(STATIC_DIR, clean))
        if candidate != STATIC_DIR and not candidate.startswith(STATIC_DIR + os.sep):
            return None
        return candidate

    def _serve_static(self, path: str):
        candidate = self._resolve_static(path)
        if candidate is None or not os.path.isfile(candidate):
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return
        content_type, _ = mimetypes.guess_type(candidate)
        with open(candidate, "rb") as handle:
            body = handle.read()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):  # keep the console readable
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def make_server(host: str, port: int, state: AppState) -> ThreadingHTTPServer:
    handler = type("BoundHandler", (Handler,), {"state": state})
    return ThreadingHTTPServer((host, port), handler)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    parser.add_argument(
        "--data-dir",
        default=None,
        help=f"Directory holding mitigation_cscc_v_cntfc_<year>.csv (default: {DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Serve the bundled synthetic sample data instead of output/data.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.demo and args.data_dir:
        print("--demo and --data-dir are mutually exclusive.", file=sys.stderr)
        return 2
    data_dir = args.data_dir or (DEMO_DATA_DIR if args.demo else DEFAULT_DATA_DIR)
    state = AppState(data_dir=data_dir, demo=args.demo)

    years = state.cache.years()
    if not years:
        print(
            f"Warning: no mitigation_cscc_v_cntfc_<year>.csv found in {state.data_dir}.\n"
            "Generate one with `python generate_cscc_vs_cntfc.py`, or run this "
            "server with --demo to explore synthetic data.",
            file=sys.stderr,
        )
    else:
        print(f"Datasets found for: {', '.join(map(str, years))}")
    if args.demo:
        print("DEMO MODE: serving synthetic sample data, not research output.")

    httpd = make_server(args.host, args.port, state)
    print(f"Serving on http://{args.host}:{httpd.server_address[1]}/  (Ctrl-C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
