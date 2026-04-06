#!/usr/bin/env python3
"""Build web/ashby_dashboard.html from normalized CSV (embed or external JSON for large sets)."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Literal

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from glass_ashby.families import canonical_family  # noqa: E402

TEMPLATE = ROOT / "web" / "dashboard_template.html"
OUT_HTML = ROOT / "web" / "ashby_dashboard.html"
DEFAULT_JSON = "glasses_data.json"
AUTO_EXTERNAL_MIN = 8000


def row_to_record(row: pd.Series) -> dict:
    fam_cell = row.get("family")
    fam_en = canonical_family(str(fam_cell) if pd.notna(fam_cell) else None)

    def num(key: str) -> float | None:
        v = row.get(key)
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return None
        try:
            x = float(v)
            if math.isnan(x):
                return None
            return x
        except (TypeError, ValueError):
            return None

    E_Pa = num("E_Pa")
    rho = num("rho_kg_m3")
    E_over_rho = (E_Pa / rho) if E_Pa and rho else None

    return {
        "source_id": str(row["source_id"]),
        "material_label": row.get("material_label") if pd.notna(row.get("material_label")) else None,
        "family": fam_en,
        "E_Pa": E_Pa,
        "E_GPa": E_Pa / 1e9 if E_Pa else None,
        "rho_kg_m3": rho,
        "alpha_1_K": num("alpha_1_K"),
        "alpha_1e6_K": num("alpha_1_K") * 1e6 if num("alpha_1_K") is not None else None,
        "a_m2_s": num("a_m2_s"),
        "a_mm2_s": num("a_m2_s") * 1e6 if num("a_m2_s") is not None else None,
        "sigma_y_Pa": num("sigma_y_Pa"),
        "sigma_y_MPa": num("sigma_y_Pa") / 1e6 if num("sigma_y_Pa") else None,
        "cost_vol_eur_m3": num("cost_vol"),
        "Tg_K": num("Tg_K"),
        "m_fragility": num("m_fragility"),
        "E_over_rho_GPa_m3_kg": E_over_rho / 1e9 if E_over_rho else None,
    }


def stratified_sample_df(df: pd.DataFrame, n_max: int, family_col: str = "family") -> pd.DataFrame:
    """Roughly proportional sample per family (keeps rare families visible)."""
    if len(df) <= n_max:
        return df
    df = df.copy()
    if family_col in df.columns:
        fam = df[family_col].fillna("other")
    else:
        fam = pd.Series(["other"] * len(df), index=df.index)
    df["_f"] = fam
    parts: list[pd.DataFrame] = []
    n_total = len(df)
    for _, g in df.groupby("_f", sort=False):
        n_g = len(g)
        share = n_g / n_total
        k = max(1, min(n_g, int(round(n_max * share))))
        parts.append(g.sample(n=min(k, n_g), random_state=42))
    out = pd.concat(parts, ignore_index=True)
    if len(out) > n_max:
        out = out.sample(n=n_max, random_state=42).reset_index(drop=True)
    return out.drop(columns=["_f"], errors="ignore")


def records_from_dataframe(df: pd.DataFrame) -> list[dict]:
    return [row_to_record(r) for _, r in df.iterrows()]


def build(
    csv_path: Path | None = None,
    *,
    mode: Literal["auto", "embed", "external"] = "auto",
    max_records: int | None = None,
    stratified: bool = True,
    json_filename: str = DEFAULT_JSON,
) -> tuple[Path, int, str]:
    """
    Returns (html_path, record_count, mode_used).
    External mode writes web/{json_filename} and HTML that fetch()s it (needs local HTTP server).
    """
    csv_path = Path(csv_path or ROOT / "data" / "processed" / "sample_glasses_normalized.csv")
    df = pd.read_csv(csv_path)

    if max_records is not None and len(df) > max_records:
        if stratified and "family" in df.columns:
            df = stratified_sample_df(df, max_records)
        else:
            df = df.sample(n=max_records, random_state=42).reset_index(drop=True)

    records = records_from_dataframe(df)
    n = len(records)

    used_mode: Literal["embed", "external"] = "embed"
    if mode == "auto":
        used_mode = "external" if n >= AUTO_EXTERNAL_MIN else "embed"
    elif mode == "external":
        used_mode = "external"
    else:
        used_mode = "embed"

    html = TEMPLATE.read_text(encoding="utf-8")
    if "__DASHBOARD_BOOTSTRAP__" not in html:
        raise SystemExit("dashboard_template.html missing __DASHBOARD_BOOTSTRAP__ placeholder")

    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)

    if used_mode == "external":
        json_path = OUT_HTML.parent / json_filename
        json_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
        jname = json.dumps(json_filename)
        bootstrap = f"""document.getElementById("footer-info").textContent = "Loading " + {jname} + "...";
fetch({jname})
  .then((r) => {{ if (!r.ok) throw new Error(r.status + " " + r.statusText); return r.json(); }})
  .then((d) => {{ RAW_DATA = d; document.getElementById("footer-info").textContent = ""; initDashboard(); }})
  .catch((e) => {{
    document.getElementById("footer-info").textContent =
      "Could not load " + {jname} + " (" + e.message + "). Run: py -3 scripts/serve_dashboard.py";
  }});"""
    else:
        payload = json.dumps(records, ensure_ascii=False)
        bootstrap = f"RAW_DATA = {payload};\ninitDashboard();"

    html = html.replace("__DASHBOARD_BOOTSTRAP__", bootstrap)
    OUT_HTML.write_text(html, encoding="utf-8")
    return OUT_HTML, n, used_mode


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Build ashby_dashboard.html from normalized CSV")
    ap.add_argument("--csv", type=Path, default=None, help="Normalized CSV")
    ap.add_argument(
        "--mode",
        choices=("auto", "embed", "external"),
        default="auto",
        help="auto: external JSON if >= %d rows; embed otherwise" % AUTO_EXTERNAL_MIN,
    )
    ap.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Cap rows (stratified by family when possible); keeps Plotly responsive",
    )
    ap.add_argument("--no-stratified", action="store_true", help="Random sample instead of stratified")
    ap.add_argument("--json-name", default=DEFAULT_JSON, help="Sidecar filename for external mode")
    args = ap.parse_args()

    p, n, used = build(
        args.csv,
        mode=args.mode,
        max_records=args.max_records,
        stratified=not args.no_stratified,
        json_filename=args.json_name,
    )
    extra = f" + {args.json_name}" if used == "external" else ""
    print(f"Wrote {p} ({n} records, mode={used}{extra})")
    if used == "external":
        print("Open with: py -3 scripts/serve_dashboard.py")
        print("Then browse: http://localhost:8765/ashby_dashboard.html")
