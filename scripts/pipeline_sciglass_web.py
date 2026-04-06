#!/usr/bin/env python3
"""
Full path: SciGK (zip/csv) -> export_sciglass_scigk -> normalize -> dashboard.

Large sets use external glasses_data.json + HTTP server (auto when >= 8000 rows).

Example:
  py -3 scripts/pipeline_sciglass_web.py --scigk path/to/SciGK.csv.zip --require-e-rho --max-records 100000

Then:
  py -3 scripts/serve_dashboard.py
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def _load_build_dashboard():
    spec = importlib.util.spec_from_file_location(
        "build_dashboard", ROOT / "scripts" / "build_dashboard.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


def main() -> None:
    ap = argparse.ArgumentParser(description="SciGK -> CSV -> normalized -> dashboard")
    ap.add_argument("--scigk", type=Path, required=True, help="SciGK.csv or SciGK.csv.zip")
    ap.add_argument(
        "--export-out",
        type=Path,
        default=ROOT / "data" / "processed" / "sciglass_web_export.csv",
    )
    ap.add_argument(
        "--require-e-rho",
        action="store_true",
        help="Only rows with E and density (recommended for Ashby E vs rho)",
    )
    ap.add_argument("--infer-family", action="store_true", default=True)
    ap.add_argument("--no-infer-family", action="store_true")
    ap.add_argument("--chunksize", type=int, default=50_000)
    ap.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max rows in export (0 = no cap; full file can take a long time)",
    )
    ap.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Cap rows in dashboard (stratified by family); e.g. 120000",
    )
    ap.add_argument(
        "--dashboard-mode",
        choices=("auto", "embed", "external"),
        default="auto",
    )
    args = ap.parse_args()

    if not args.scigk.is_file():
        raise SystemExit(f"Not found: {args.scigk}")

    infer = args.infer_family and not args.no_infer_family

    cmd = [
        PY,
        str(ROOT / "scripts" / "export_sciglass_scigk.py"),
        "--scigk",
        str(args.scigk),
        "--out",
        str(args.export_out),
        "--chunksize",
        str(args.chunksize),
    ]
    if args.require_e_rho:
        cmd.append("--require-e-rho")
    if infer:
        cmd.append("--infer-family")
    if args.limit and args.limit > 0:
        cmd.extend(["--limit", str(args.limit)])

    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

    from glass_ashby.pipeline import run_from_csv

    norm = run_from_csv(
        args.export_out,
        processed_dir=ROOT / "data" / "processed",
        infer_family=False,
    )
    print(f"Normalized -> {norm['normalized_csv']}")

    bd = _load_build_dashboard()
    html_path, n, mode = bd.build(
        norm["normalized_csv"],
        mode=args.dashboard_mode,
        max_records=args.max_records,
        stratified=True,
    )
    print(f"Dashboard: {html_path} ({n} records, mode={mode})")
    if mode == "external":
        print("Run: py -3 scripts/serve_dashboard.py")
        print("Open: http://127.0.0.1:8765/ashby_dashboard.html")


if __name__ == "__main__":
    main()
