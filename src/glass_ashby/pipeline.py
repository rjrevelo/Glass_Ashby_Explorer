"""Orquestación reproducible: CSV → normalización → tabla trazable → artefactos."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from glass_ashby.classify import infer_family_for_record
from glass_ashby.normalize import dataframe_to_records, records_to_dataframe
from glass_ashby.plot_mvp import plot_stiffness_lightness


def run_from_csv(
    csv_path: Path,
    *,
    processed_dir: Path | None = None,
    infer_family: bool = False,
) -> dict[str, Path]:
    csv_path = Path(csv_path)
    processed_dir = processed_dir or Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    raw_name = csv_path.stem
    df_raw = pd.read_csv(csv_path)
    records = dataframe_to_records(df_raw, source_name=raw_name)
    if infer_family:
        records = [
            r.model_copy(update={"family": infer_family_for_record(r)}) for r in records
        ]
    df_norm = records_to_dataframe(records)
    csv_out = processed_dir / f"{raw_name}_normalized.csv"
    df_norm.to_csv(csv_out, index=False)

    fig_path = plot_stiffness_lightness(df_norm, out_path=processed_dir / "mvp_stiffness_lightness.png")
    return {"normalized_csv": csv_out, "figure": fig_path}
