"""Cálculo de envolventes y preparación de series para diagramas Ashby (log–log)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib.path import Path


def records_frame_for_stiffness_lightness(df: pd.DataFrame) -> pd.DataFrame:
    """Filas válidas para E vs ρ (Pa y kg/m³)."""
    out = df.dropna(subset=["E_Pa", "rho_kg_m3"]).copy()
    out = out[(out["E_Pa"] > 0) & (out["rho_kg_m3"] > 0)]
    return out


def log_log_convex_hull(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """
    Índices ordenados del contorno convexo en el plano log(x)-log(y).
    Devuelve índices en el orden del polígono cerrado.
    """
    if len(x) < 3:
        return np.arange(len(x))

    lx = np.log10(x)
    ly = np.log10(y)
    pts = np.column_stack([lx, ly])

    # Monotonic chain para envolvente convexa (Andrew)
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    sorted_idx = np.lexsort((pts[:, 1], pts[:, 0]))
    pts = pts[sorted_idx]

    lower: list[int] = []
    for i in range(len(pts)):
        while len(lower) >= 2 and cross(pts[lower[-2]], pts[lower[-1]], pts[i]) <= 0:
            lower.pop()
        lower.append(i)
    upper: list[int] = []
    for i in range(len(pts) - 1, -1, -1):
        while len(upper) >= 2 and cross(pts[upper[-2]], pts[upper[-1]], pts[i]) <= 0:
            upper.pop()
        upper.append(i)
    hull_idx = lower[:-1] + upper[:-1]
    return sorted_idx[np.array(hull_idx)]


def pareto_upper_right_mask(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Materiales no dominados maximizando ambas magnitudes (referencia rápida)."""
    n = len(x)
    mask = np.ones(n, dtype=bool)
    for i in range(n):
        if not mask[i]:
            continue
        for j in range(n):
            if i == j or not mask[j]:
                continue
            if x[j] >= x[i] and y[j] >= y[i] and (x[j] > x[i] or y[j] > y[i]):
                mask[i] = False
                break
    return mask


def region_path_from_hull(x: np.ndarray, y: np.ndarray, hull_indices: np.ndarray) -> Path:
    """Path matplotlib para sombrear envolvente en datos originales (no log)."""
    xh = x[hull_indices]
    yh = y[hull_indices]
    verts = list(zip(xh.tolist(), yh.tolist()))
    if verts and verts[0] != verts[-1]:
        verts.append(verts[0])
    return Path(verts)
