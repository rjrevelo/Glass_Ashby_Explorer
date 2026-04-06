"""MVP: diagrama Ashby ligereza rígida (E vs ρ), log–log, por familia + envolventes."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import PathPatch

from glass_ashby.ashby import log_log_convex_hull, records_frame_for_stiffness_lightness, region_path_from_hull
from glass_ashby.families import canonical_family, family_color


def plot_stiffness_lightness(
    df: pd.DataFrame,
    *,
    out_path: Path | None = None,
    title: str = "Ashby: rigidez vs ligereza (vidrios)",
) -> Path:
    """
    E [Pa] vs ρ [kg/m³] en escala log–log.
    Incluye puntos por familia y envolvente convexa (en espacio log) por familia.
    """
    d = records_frame_for_stiffness_lightness(df)
    if d.empty:
        raise ValueError("No hay filas con E_Pa y rho_kg_m3 válidos")

    d = d.copy()
    d["_family"] = d["family"].map(canonical_family)

    fig, ax = plt.subplots(figsize=(8, 6), dpi=120)
    rho = d["rho_kg_m3"].to_numpy()
    E = d["E_Pa"].to_numpy()

    for fam in sorted(d["_family"].unique()):
        sub = d[d["_family"] == fam]
        xr = sub["rho_kg_m3"].to_numpy()
        ye = sub["E_Pa"].to_numpy()
        c = family_color(fam)
        ax.scatter(xr, ye, s=55, alpha=0.85, color=c, edgecolors="white", linewidths=0.6, label=fam)

        if len(sub) >= 3:
            hi = log_log_convex_hull(xr, ye)
            path = region_path_from_hull(xr, ye, hi)
            patch = PathPatch(
                path, facecolor=c, alpha=0.12, edgecolor=c, linewidth=1.0, linestyle="--"
            )
            ax.add_patch(patch)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"Densidad $\rho$ [kg/m³]")
    ax.set_ylabel(r"Módulo elástico $E$ [Pa]")
    ax.set_title(title)
    ax.grid(True, which="both", linestyle=":", alpha=0.5)
    ax.legend(title="Familia", loc="lower right", framealpha=0.92)

    # Anotar mejores en E/rho (indicador de rigidez específica en orden de magnitud)
    ratio = E / rho
    top = d.iloc[np.argsort(-ratio)[:3]]
    for _, row in top.iterrows():
        ax.annotate(
            row["source_id"],
            (row["rho_kg_m3"], row["E_Pa"]),
            textcoords="offset points",
            xytext=(6, 6),
            fontsize=8,
            alpha=0.9,
        )

    fig.tight_layout()
    if out_path is None:
        out_path = Path("data/processed/mvp_stiffness_lightness.png")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path
