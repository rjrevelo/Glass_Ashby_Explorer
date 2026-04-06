"""Clasificación de familia a partir de composición (extensible)."""

from __future__ import annotations

from glass_ashby.families import canonical_family
from glass_ashby.schema import GlassRecord


def _g(comp: dict[str, float], key: str) -> float:
    return float(comp.get(key, 0.0) or 0.0)


def infer_family_from_composition(
    composition: dict[str, float],
    *,
    explicit_label: str | None = None,
) -> str:
    """
    Heurística por formadores de red y vidrios especiales.
    Devuelve etiqueta canónica en inglés (silicate, borate, ...).
    Si no aplica regla, usa explicit_label normalizado o 'other'.
    """
    c = composition
    sio2 = _g(c, "SiO2_mol_frac")
    b2o3 = _g(c, "B2O3_mol_frac")
    p2o5 = _g(c, "P2O5_mol_frac")
    al2o3 = _g(c, "Al2O3_mol_frac")
    pbo = _g(c, "PbO_mol_frac")
    teo2 = _g(c, "TeO2_mol_frac")
    geo2 = _g(c, "GeO2_mol_frac")
    zrf4 = _g(c, "ZrF4_mol_frac")
    alf3 = _g(c, "AlF3_mol_frac")
    se_frac = _g(c, "Se_mol_frac")
    as2se3 = _g(c, "As2Se3_mol_frac")

    glass_formers = sio2 + b2o3 + p2o5 + teo2 + geo2 + zrf4 * 0.5

    if zrf4 >= 0.12 or alf3 >= 0.15:
        return "fluoride"
    if se_frac >= 0.2 or as2se3 >= 0.25:
        return "chalcogenide"
    if glass_formers < 1e-6 and explicit_label:
        return canonical_family(explicit_label)

    if teo2 >= 0.3 and teo2 >= max(sio2, b2o3, p2o5):
        return "tellurite"
    if geo2 >= 0.28 and geo2 > sio2 * 0.85:
        return "germanate"
    if p2o5 >= max(sio2, b2o3) and p2o5 >= 0.18:
        if _g(c, "AlF3_mol_frac") >= 0.05 or _g(c, "NaF_mol_frac") >= 0.08:
            return "fluorophosphate"
        return "phosphate"
    if b2o3 >= sio2 and b2o3 >= 0.18:
        return "borate"
    if sio2 >= 0.35:
        if pbo >= 0.1:
            return "lead_silicate"
        if al2o3 >= 0.06:
            return "aluminosilicate"
        return "silicate"

    if explicit_label:
        return canonical_family(explicit_label)
    return "other"


def infer_family_for_record(r: GlassRecord) -> str:
    return infer_family_from_composition(r.composition, explicit_label=r.family)
