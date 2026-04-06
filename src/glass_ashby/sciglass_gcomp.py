"""Parser del campo Composition de SciGlass (export texto/CSV del fork drcassar)."""

from __future__ import annotations

import re

# Delimitador interno del campo Composition en Gcomp.csv (ASCII 127).
SEP = "\x7f"


def parse_gcomp_composition_field(raw: str) -> dict[str, float]:
    """
    Descompone el texto Composition en bloques de 4 tokens:
    (óxido, masa molar aparente, %masa, %mol).
    Devuelve { 'SiO2_mol_frac': 0.4535, ... } con fracciones mol (0–1).
    """
    if raw is None or (isinstance(raw, float) and str(raw) == "nan"):
        return {}
    s = str(raw).strip().strip('"')
    parts = [p for p in s.split(SEP) if p.strip()]
    out: dict[str, float] = {}
    i = 0
    while i + 3 < len(parts):
        oxide = parts[i].strip()
        if not oxide or not re.match(r"^[A-Za-z0-9().+\-]+$", oxide):
            i += 1
            continue
        try:
            _mw = float(parts[i + 1])
            _w = float(parts[i + 2])
            mol_pct = float(parts[i + 3])
        except ValueError:
            i += 1
            continue
        key = f"{oxide}_mol_frac"
        out[key] = max(0.0, min(1.0, mol_pct / 100.0))
        i += 4
    return out


def col_name_for_oxide(oxide_token: str) -> str:
    return f"{oxide_token.strip()}_mol_frac"
