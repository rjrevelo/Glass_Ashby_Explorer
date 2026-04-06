# Cómo ampliar composiciones y familias (datos más representativos)

## 1. Ampliar el CSV de entrada

- Cada **fila** es un material con `source_id` único (trazabilidad).
- Añade columnas **`NombreOxido_mol_frac`** para cualquier óxido (o convención que documentes). El código incluye **automáticamente** en la composición toda columna cuyo nombre termine en `_mol_frac`.
- Columnas de propiedades habituales: `E_GPa`, `rho_kg_m3`, `alpha_1e6_K`, `a_mm2_s`, `sigma_y_MPa`, `cost_vol_eur_m3`, `Tg_K`, `m_fragility`, `notes`.
- Columna **`family`**: etiqueta manual en **inglés** (`silicate`, `borate`, `phosphate`, `aluminosilicate`, …) o en español (`silicato`, `borato`, …); el visor las unifica. Si no estás seguro de la etiqueta, rellena composición y usa `--infer-family` (ver abajo).

## 2. Inferencia automática de familia

```bash
python scripts/run_mvp.py --infer-family
```

Sobrescribe `family` con reglas basadas en fracciones mol (fluoruros, calcogenuros, tellurito, germanato, fosfato/borato/silicato, aluminosilicato, plomo-silicato, fluorofosfato). Ajusta umbrales en `src/glass_ashby/classify.py` si tu dominio lo requiere.

## 3. Nuevas familias en gráficos y web

- Colores: `src/glass_ashby/families.py` (`COLORS`).
- Dashboard HTML: objeto `FAMILY_COLORS` en `web/dashboard_template.html` (regenerar con `scripts/build_dashboard.py`).

## 4. Fuentes abiertas (ejemplos de estrategia)

| Enfoque | Comentario |
|--------|------------|
| **SciGlass en GitHub** | `SciGK` + `Gcomp`: ver **`data/SCIGLASS_GITHUB.md`** y `scripts/export_sciglass_scigk.py` / `export_sciglass_gcomp.py`. |
| **Artículos con datos suplementarios** | CSV/Excel de composición + propiedades; copiar columnas al esquema anterior. |
| **Repositorios GitHub** (vidrio, materiales) | Revisar licencia; documentar en `provenance` vía columna `notes` o manifiesto futuro. |
| **GlassPy** | Usar como *herramienta* y/o citar papers; no asumir que su base comercial es redistribuible. |

## 5. Regenerar artefactos

```bash
python scripts/run_mvp.py
python scripts/build_dashboard.py
```

Abre `web/ashby_dashboard.html` en el navegador.

## 6. Calidad y representatividad

- **Más filas** ≠ mejor si están sesgadas: anota procedencia en `notes` o en un manifiesto por dataset.
- Para **cobertura por familia**, vigila el conteo por `family` en el dashboard y equilibra cuando integres datos reales.
- Valores faltantes: déjalos vacíos; los gráficos solo usan filas con ambas magnitudes válidas para el eje elegido.
