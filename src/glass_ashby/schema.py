"""Esquema de datos unificado (trazabilidad + propiedades clave)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class GlassRecord(BaseModel):
    """Un registro de vidrio tras normalización; enlaza al dato fuente."""

    source_id: str = Field(..., description="ID estable en el dataset de origen")
    material_label: str | None = None
    family: str = Field(..., description="silicato | borato | fosfato | otro")

    # Composición (fracciones mol o masa según convención documentada en meta)
    composition: dict[str, float] = Field(default_factory=dict)

    E_Pa: float | None = Field(None, description="Módulo de Young [Pa]")
    rho_kg_m3: float | None = Field(None, description="Densidad [kg/m³]")
    alpha_1_K: float | None = Field(None, description="CTE lineal [1/K]")
    a_m2_s: float | None = Field(None, description="Difusividad térmica [m²/s]")
    sigma_y_Pa: float | None = Field(None, description="Límite elástico [Pa]")
    cost_vol: float | None = Field(None, description="Coste por volumen [moneda/m³]")
    cost_currency: str | None = None
    Tg_K: float | None = None
    m_fragility: float | None = None

    provenance: dict[str, Any] = Field(
        default_factory=dict,
        description="dataset, versión, URL, licencia, transformaciones aplicadas",
    )

    @field_validator("family")
    @classmethod
    def family_lower(cls, v: str) -> str:
        return v.strip().lower()

    def trace_key(self) -> str:
        return self.source_id
