"""Nombres canónicos de familia (inglés) y colores para gráficos / web."""

from __future__ import annotations

ALIASES_TO_CANONICAL: dict[str, str] = {
    "silicato": "silicate",
    "borato": "borate",
    "fosfato": "phosphate",
    "otro": "other",
}

DEFAULT_COLOR = "#8b949e"

COLORS: dict[str, str] = {
    "silicate": "#58a6ff",
    "borate": "#d29922",
    "phosphate": "#3fb950",
    "other": "#8b949e",
    "aluminosilicate": "#a371f7",
    "lead_silicate": "#f778ba",
    "tellurite": "#79c0ff",
    "germanate": "#56d364",
    "fluoride": "#39d353",
    "chalcogenide": "#ff7b72",
    "fluorophosphate": "#ffa657",
}


def canonical_family(label: str | None) -> str:
    if label is None or (isinstance(label, float) and str(label) == "nan"):
        return "other"
    s = str(label).strip().lower()
    if not s or s == "nan":
        return "other"
    return ALIASES_TO_CANONICAL.get(s, s)


def family_color(label: str | None) -> str:
    return COLORS.get(canonical_family(label), DEFAULT_COLOR)
