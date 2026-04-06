"""Limpieza, unidades y conversión desde tablas tabulares (CSV)."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from glass_ashby.schema import GlassRecord


def composition_from_row(row: pd.Series, columns: pd.Index) -> dict[str, float]:
    """Todas las columnas que terminen en _mol_frac (extensible a nuevos óxidos)."""
    comp: dict[str, float] = {}
    for col in columns:
        if isinstance(col, str) and col.endswith("_mol_frac"):
            v = row.get(col)
            if pd.notna(v):
                comp[col] = float(v)
    return comp


def _row_provenance(row: pd.Series, source_name: str) -> dict[str, Any]:
    return {
        "dataset": source_name,
        "row_index": int(row.name) if isinstance(row.name, int) else str(row.name),
        "notes": row.get("notes"),
    }


def dataframe_to_records(df: pd.DataFrame, *, source_name: str = "ingest") -> list[GlassRecord]:
    """Convierte un DataFrame tabular (propiedades + columnas *_mol_frac) en GlassRecord."""
    records: list[GlassRecord] = []
    for idx, row in df.iterrows():
        comp = composition_from_row(row, df.columns)
        alpha = row.get("alpha_1e6_K")
        alpha_k = float(alpha) * 1e-6 if pd.notna(alpha) else None
        a_mm2 = row.get("a_mm2_s")
        a_m2 = float(a_mm2) * 1e-6 if pd.notna(a_mm2) else None
        e_gpa = row.get("E_GPa")
        e_pa = float(e_gpa) * 1e9 if pd.notna(e_gpa) else None
        sy = row.get("sigma_y_MPa")
        sy_pa = float(sy) * 1e6 if pd.notna(sy) else None

        fam_cell = row.get("family")
        family_val = str(fam_cell).strip() if pd.notna(fam_cell) else "other"

        rec = GlassRecord(
            source_id=str(row["source_id"]),
            material_label=row.get("material_label"),
            family=family_val,
            composition=comp,
            E_Pa=e_pa,
            rho_kg_m3=float(row["rho_kg_m3"]) if pd.notna(row.get("rho_kg_m3")) else None,
            alpha_1_K=alpha_k,
            a_m2_s=a_m2,
            sigma_y_Pa=sy_pa,
            cost_vol=float(row["cost_vol_eur_m3"]) if pd.notna(row.get("cost_vol_eur_m3")) else None,
            cost_currency="EUR" if pd.notna(row.get("cost_vol_eur_m3")) else None,
            Tg_K=float(row["Tg_K"]) if pd.notna(row.get("Tg_K")) else None,
            m_fragility=float(row["m_fragility"]) if pd.notna(row.get("m_fragility")) else None,
            provenance=_row_provenance(row, source_name),
        )
        records.append(rec)
    return records


def records_to_dataframe(records: list[GlassRecord]) -> pd.DataFrame:
    """Serializa a tabla para trazabilidad y export."""
    rows = []
    for r in records:
        rows.append(
            {
                "source_id": r.source_id,
                "material_label": r.material_label,
                "family": r.family,
                "composition_json": json.dumps(r.composition, sort_keys=True),
                "E_Pa": r.E_Pa,
                "rho_kg_m3": r.rho_kg_m3,
                "alpha_1_K": r.alpha_1_K,
                "a_m2_s": r.a_m2_s,
                "sigma_y_Pa": r.sigma_y_Pa,
                "cost_vol": r.cost_vol,
                "cost_currency": r.cost_currency,
                "Tg_K": r.Tg_K,
                "m_fragility": r.m_fragility,
                "provenance_json": json.dumps(r.provenance, ensure_ascii=False),
            }
        )
    return pd.DataFrame(rows)
