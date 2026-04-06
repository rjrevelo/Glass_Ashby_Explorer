#!/usr/bin/env python3
"""Ejecuta el pipeline MVP sobre data/sample_glasses.csv."""

import argparse
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from glass_ashby.pipeline import run_from_csv  # noqa: E402


def _build_dashboard(csv_normalized: Path) -> Path:
    spec = importlib.util.spec_from_file_location(
        "build_dashboard", ROOT / "scripts" / "build_dashboard.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    html_path, n, mode = mod.build(csv_normalized)
    if mode == "external":
        print(f"  dashboard: {n} records -> external JSON (use scripts/serve_dashboard.py)")
    return html_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Glass Ashby MVP pipeline")
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="CSV de entrada (por defecto data/sample_glasses.csv)",
    )
    parser.add_argument(
        "--infer-family",
        action="store_true",
        help="Override CSV family using composition heuristics (English canonical names)",
    )
    args = parser.parse_args()

    csv_path = args.csv or (ROOT / "data" / "sample_glasses.csv")
    out = run_from_csv(
        csv_path,
        processed_dir=ROOT / "data" / "processed",
        infer_family=args.infer_family,
    )
    dash = _build_dashboard(out["normalized_csv"])
    print("Artefactos generados:")
    for k, v in out.items():
        print(f"  {k}: {v}")
    print(f"  dashboard_html: {dash}")


if __name__ == "__main__":
    main()
