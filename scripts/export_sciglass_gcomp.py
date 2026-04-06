#!/usr/bin/env python3
"""
Exporta composiciones SciGlass (Gcomp.csv del fork drcassar) a CSV ancho
compatible con columnas *_mol_frac del proyecto Glass_Ashby.

Requisito: descomprimir sciglass/select/Gcomp.csv.zip y pasar la ruta a Gcomp.csv.

Ejemplo:
  python scripts/export_sciglass_gcomp.py ^
    --gcomp data/raw/sciglass_drcassar/select/Gcomp.csv ^
    --limit 50000 ^
    --out data/processed/sciglass_gcomp_wide.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from glass_ashby.classify import infer_family_from_composition  # noqa: E402
from glass_ashby.sciglass_gcomp import parse_gcomp_composition_field  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="SciGlass Gcomp → CSV ancho (_mol_frac)")
    p.add_argument("--gcomp", type=Path, required=True, help="Ruta a Gcomp.csv (sin zip)")
    p.add_argument("--out", type=Path, default=ROOT / "data/processed/sciglass_gcomp_wide.csv")
    p.add_argument("--limit", type=int, default=0, help="Máx. filas (0 = todas)")
    p.add_argument("--infer-family", action="store_true", help="Añadir columna family inferida")
    args = p.parse_args()

    if not args.gcomp.is_file():
        raise SystemExit(f"No existe Gcomp.csv: {args.gcomp}")

    df = pd.read_csv(args.gcomp, sep="\t", dtype=str, encoding="utf-8", encoding_errors="replace")
    if args.limit and args.limit > 0:
        df = df.head(args.limit)

    if "Kod" not in df.columns or "GlasNo" not in df.columns or "Composition" not in df.columns:
        raise SystemExit(
            f"Columnas esperadas: Kod, GlasNo, Composition. Encontradas: {list(df.columns)}"
        )

    rows: list[dict] = []
    for _, row in df.iterrows():
        comp = parse_gcomp_composition_field(row["Composition"])
        if not comp:
            continue
        sid = f"SG-{row['Kod']}-{row['GlasNo']}"
        rec: dict = {
            "source_id": sid,
            "material_label": sid,
            "sciglass_kod": row["Kod"],
            "sciglass_glasno": row["GlasNo"],
            "notes": "SciGlass drcassar Gcomp; verify license before publishing derivatives",
        }
        rec.update(comp)
        if args.infer_family:
            rec["family"] = infer_family_from_composition(comp, explicit_label="other")
        rows.append(rec)

    out_df = pd.DataFrame(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(args.out, index=False)
    print(f"Rows: {len(out_df)}, columns: {len(out_df.columns)}")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
