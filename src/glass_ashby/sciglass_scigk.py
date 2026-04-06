"""Mapeo SciGK.csv (fork drcassar/epam) → columnas del pipeline Glass_Ashby."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import BinaryIO, Iterator

import pandas as pd

# Bloque SIO2…FemOn = % mol en SciGK. Solo añadimos óxidos claros fuera de ese bloque;
# códigos tipo RHal/RF/RmOn pueden no ser % mol homogéneo — no mapearlos por defecto.
EXTRA_MOL_PCT_COLS = ("Bi2O3", "WO3")

# SciGK suele usar símbolos en mayúsculas → claves canónicas *_mol_frac del proyecto.
SCIGK_TO_MOL_FRAC: dict[str, str] = {
    "SIO2": "SiO2_mol_frac",
    "AL2O3": "Al2O3_mol_frac",
    "B2O3": "B2O3_mol_frac",
    "CAO": "CaO_mol_frac",
    "K2O": "K2O_mol_frac",
    "NA2O": "Na2O_mol_frac",
    "PBO": "PbO_mol_frac",
    "Li2O": "Li2O_mol_frac",
    "MgO": "MgO_mol_frac",
    "SRO": "SrO_mol_frac",
    "BAO": "BaO_mol_frac",
    "ZNO": "ZnO_mol_frac",
    "P2O5": "P2O5_mol_frac",
    "GEO2": "GeO2_mol_frac",
    "ZRO2": "ZrO2_mol_frac",
    "TIO2": "TiO2_mol_frac",
    "TEO2": "TeO2_mol_frac",
    "RO": "RO_mol_frac",
    "FemOn": "FemOn_mol_frac",
    "Bi2O3": "Bi2O3_mol_frac",
    "WO3": "WO3_mol_frac",
}


def detect_mol_source_columns(columns: pd.Index) -> list[str]:
    cols = list(columns)
    i0 = cols.index("SIO2")
    i1 = cols.index("WSIO2")
    primary = cols[i0:i1]
    extra = [c for c in EXTRA_MOL_PCT_COLS if c in columns]
    seen = set()
    out: list[str] = []
    for c in primary + extra:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _num(row: pd.Series, key: str) -> float | None:
    v = row.get(key)
    if v is None or (isinstance(v, str) and not str(v).strip()):
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    if pd.isna(x):
        return None
    return x


def scigk_row_to_pipeline(row: pd.Series, mol_sources: list[str]) -> dict:
    """Una fila SciGK → dict alineado con sample_glasses.csv + columnas extra."""
    kod = int(float(row["KOD"]))
    glas = int(float(row["GLASNO"]))
    sid = f"SG-{kod}-{glas}"

    out: dict = {
        "source_id": sid,
        "material_label": sid,
        "notes": "SciGlass SciGK.csv; cite EPAM/drcassar + license",
    }

    for src in mol_sources:
        tgt = SCIGK_TO_MOL_FRAC.get(src)
        if not tgt:
            continue
        x = _num(row, src)
        if x is None or x <= 0:
            continue
        out[tgt] = max(0.0, min(1.0, x / 100.0))

    e = _num(row, "MOD_UNG")
    if e is not None and e > 0:
        out["E_GPa"] = e

    d = _num(row, "DENSITY")
    if d is not None and d > 0:
        out["rho_kg_m3"] = d * 1000.0

    tg = _num(row, "TG")
    if tg is not None:
        out["Tg_K"] = tg + 273.15

    # LISTPROP: TEC almacenado con factor 1e7 → α [1/K] = val/1e7, α·10^6 = val/10
    tec = None
    for col in ("ANY_TEC", "TEC100", "TEC55", "TEC160", "TEC210", "TEC350"):
        tec = _num(row, col)
        if tec is not None:
            break
    if tec is not None and tec > 0:
        out["alpha_1e6_K"] = tec / 10.0

    m = _num(row, "Mg")
    if m is not None and 10.0 <= m <= 250.0:
        out["m_fragility"] = m

    k = _num(row, "cond220")
    if k is not None and k > 0:
        out["notes"] = (out.get("notes") or "") + f"; k_W_mK={k}"

    return out


def open_scigk_binary(path: Path) -> tuple[BinaryIO, zipfile.ZipFile | None]:
    path = Path(path)
    if path.suffix.lower() == ".zip":
        zf = zipfile.ZipFile(path, "r")
        inner = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
        return zf.open(inner, "r"), zf
    f = open(path, "rb")
    return f, None


def detect_mol_sources_from_path(path: Path) -> list[str]:
    bio, zf = open_scigk_binary(path)
    try:
        df = pd.read_csv(bio, sep="\t", nrows=0)
        return detect_mol_source_columns(df.columns)
    finally:
        bio.close()
        if zf is not None:
            zf.close()


def iter_scigk_chunks(
    path: Path,
    *,
    chunksize: int = 50_000,
) -> Iterator[pd.DataFrame]:
    """Lee SciGK desde .csv o .zip (primer .csv dentro del zip)."""
    bio, zf = open_scigk_binary(path)
    try:
        for chunk in pd.read_csv(bio, sep="\t", chunksize=chunksize, low_memory=False):
            yield chunk
    finally:
        bio.close()
        if zf is not None:
            zf.close()
