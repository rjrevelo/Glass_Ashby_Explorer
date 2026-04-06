#!/usr/bin/env python3
"""
Exporta SciGK.csv (o SciGK.csv.zip del fork drcassar) a CSV listo para el pipeline
Glass_Ashby: *_mol_frac, E_GPa, rho_kg_m3, Tg_K, alpha_1e6_K, m_fragility (si existen).

Ejemplos:
  python scripts/export_sciglass_scigk.py --scigk %USERPROFILE%\\.cache\\SciGK.csv.zip --limit 10000
  python scripts/export_sciglass_scigk.py --scigk data/raw/sciglass_drcassar/select/SciGK.csv --require-e-rho
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from glass_ashby.classify import infer_family_from_composition  # noqa: E402
from glass_ashby.sciglass_scigk import (  # noqa: E402
    detect_mol_sources_from_path,
    iter_scigk_chunks,
    scigk_row_to_pipeline,
)


def main() -> None:
    p = argparse.ArgumentParser(description="SciGK → CSV Glass_Ashby")
    p.add_argument("--scigk", type=Path, required=True, help="SciGK.csv o SciGK.csv.zip")
    p.add_argument(
        "--out",
        type=Path,
        default=ROOT / "data/processed/sciglass_scigk_for_pipeline.csv",
    )
    p.add_argument("--limit", type=int, default=0, help="Máx. filas exportadas (0 = sin límite)")
    p.add_argument("--chunksize", type=int, default=50_000)
    p.add_argument("--infer-family", action="store_true")
    p.add_argument(
        "--require-e-rho",
        action="store_true",
        help="Solo filas con MOD_UNG y DENSITY válidos (útil para Ashby E–ρ)",
    )
    args = p.parse_args()

    if not args.scigk.is_file():
        raise SystemExit(f"No existe: {args.scigk}")

    mol_sources = detect_mol_sources_from_path(args.scigk)
    rows_out: list[dict] = []
    total_in = 0

    for chunk in iter_scigk_chunks(args.scigk, chunksize=args.chunksize):
        for _, row in chunk.iterrows():
            total_in += 1
            if args.limit and len(rows_out) >= args.limit:
                break
            d = scigk_row_to_pipeline(row, mol_sources)
            if args.require_e_rho and (d.get("E_GPa") is None or d.get("rho_kg_m3") is None):
                continue
            if args.infer_family:
                comp = {k: v for k, v in d.items() if k.endswith("_mol_frac")}
                d["family"] = infer_family_from_composition(comp, explicit_label="other")
            else:
                d["family"] = "other"
            rows_out.append(d)
        if args.limit and len(rows_out) >= args.limit:
            break

    if not rows_out:
        raise SystemExit("No se exportó ninguna fila (revisa filtros o archivo).")

    out_df = pd.DataFrame(rows_out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(args.out, index=False)
    print(f"Leídas ~{total_in} filas procesadas en bucle; exportadas: {len(out_df)}")
    print(f"Columnas: {len(out_df.columns)} -> {args.out}")


if __name__ == "__main__":
    main()
