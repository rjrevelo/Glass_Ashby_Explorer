# Usar SciGlass de GitHub (licencia abierta / datos libres)

## Repositorios relevantes

| Recurso | Contenido | Enlace |
|--------|-----------|--------|
| **EPAM (oficial en GitHub)** | Base Access `.mdb` (`select.mdb`, `property.mdb`) en *Releases*; documentación de uso con MS Access | [github.com/epam/SciGlass](https://github.com/epam/SciGlass) |
| **Fork drcassar** | Misma base convertida a **CSV dentro de ZIP** (`sciglass/select/*.csv.zip`, `sciglass/property/*.csv`); citable vía Zenodo | [github.com/drcassar/SciGlass](https://github.com/drcassar/SciGlass) · [DOI 10.5281/zenodo.8287159](https://doi.org/10.5281/zenodo.8287159) |

En el fork, las composiciones están en **`sciglass/select/Gcomp.csv.zip`**: al descomprimir obtienes `Gcomp.csv` (TSV) con columnas `Kod`, `GlasNo`, `Composition`. El campo `Composition` usa el carácter ASCII **127** (`0x7F`) como separador entre trozos `óxido · masa molar · %masa · %mol`.

## Licencia: léela y cúmplela

- GitHub muestra el repositorio EPAM con licencia tipo **MIT** en los metadatos; el archivo `LICENSE` en el repo puede incluir también referencia a **ODbL (Open Database License)**. **No asumas** que es dominio público: atribución, compartir igual en bases derivadas y restricciones de ODbL pueden aplicar según cómo uses y redistribuyas los datos.
- Cualquier **publicación o producto** que incluya datos o una base derivada debe **citación** a SciGlass y cumplir la licencia vigente del archivo que aceptes al clonar/descargar.

## Pasos prácticos para “todas las composiciones”

### 1. Obtener los archivos (sin subirlos al repo si son muy pesados)

```text
git clone https://github.com/drcassar/SciGlass.git
cd SciGlass/sciglass/select
# Descomprime al menos Gcomp.csv.zip → Gcomp.csv
```

Copia `Gcomp.csv` a tu proyecto, por ejemplo:

`Glass_Ashby/data/raw/sciglass_drcassar/select/Gcomp.csv`

(Añade `data/raw/sciglass_drcassar/` al `.gitignore` si no quieres versionar cientos de MB.)

### 2. Exportar a columnas `*_mol_frac` (formato Glass_Ashby)

Desde la raíz del proyecto **Glass_Ashby**:

```bash
python scripts/export_sciglass_gcomp.py --gcomp data/raw/sciglass_drcassar/select/Gcomp.csv --limit 0 --infer-family --out data/processed/sciglass_gcomp_wide.csv
```

- `--limit 0` = procesar **todas** las filas (puede tardar y generar un CSV muy grande).
- `--infer-family` rellena `family` con la heurística del proyecto (inglés canónico).

Ese CSV ya tiene `source_id` estable (`SG-{Kod}-{GlasNo}`) y muchas columnas dinámicas `SiO2_mol_frac`, etc., que el módulo `normalize.composition_from_row` recoge automáticamente.

### 3. Propiedades + composición en un solo archivo (`SciGK`)

En el fork, **`sciglass/select/SciGK.csv.zip`** contiene una tabla ancha: mismas claves `KOD`/`GLASNO`, columnas de **% mol** (`SIO2`…`FemOn`), **% masa** (`WSIO2`…), y propiedades (`MOD_UNG` ≈ Young en GPa, `DENSITY` en g/cm³, `TG` en °C, `TEC55`/`ANY_TEC` con factor 10⁷ según `LISTPROP.csv`, etc.).

**Export directo al pipeline (implementado):**

```bash
python scripts/export_sciglass_scigk.py --scigk data/raw/sciglass_drcassar/select/SciGK.csv.zip --out data/processed/sciglass_scigk_for_pipeline.csv --infer-family
```

Opciones útiles:

- `--require-e-rho` — solo filas con módulo de Young y densidad (para Ashby E–ρ).
- `--limit N` — prueba rápida o muestras; para **toda** la base omite `--limit`.
- Lee desde **`.zip` o `.csv`** descomprimido.

Mapeo en código: `src/glass_ashby/sciglass_scigk.py` (α en 10⁻⁶/K ≈ `ANY_TEC`/`TEC55`/… dividido entre 10; `m_fragility` desde `Mg` si está entre 10 y 250).

Si solo necesitas composición sin propiedades, sigue siendo válido `export_sciglass_gcomp.py` sobre `Gcomp.csv`.

### 4. Alternativa: base `.mdb` oficial (EPAM)

1. Descarga el ZIP desde [Releases · epam/SciGlass](https://github.com/epam/SciGlass/releases).
2. Abre con **Microsoft Access** (o exporta tablas con herramientas que lean Jet/ACE).
3. Exporta las tablas necesarias a CSV y aplica el mismo criterio de join y unidades.

## Script incluido en este proyecto

- `scripts/export_sciglass_gcomp.py` — solo composiciones desde `Gcomp.csv`.
- `scripts/export_sciglass_scigk.py` — composición + propiedades desde `SciGK.csv` o `.zip`.
- `src/glass_ashby/sciglass_gcomp.py`, `src/glass_ashby/sciglass_scigk.py`.

Regenerar figura y dashboard con tu export:

```bash
python scripts/run_mvp.py --csv data/processed/sciglass_scigk_for_pipeline.csv --infer-family
```

(Usa `--infer-family` solo si quieres recalcular familia en el pipeline; el export ya puede llevar `family` con `--infer-family` en el propio `export_sciglass_scigk.py`.)

### Pipeline completo (muchas filas + dashboard)

Un solo comando exporta SciGK, normaliza y genera el HTML (con JSON externo automático si hay ≥ 8000 filas):

```bash
python scripts/pipeline_sciglass_web.py --scigk ruta/a/SciGK.csv.zip --require-e-rho --max-records 120000
```

- `--limit 50000` — corta el export tras N filas válidas (prueba rápida).
- `--max-records` — submuestreo **estratificado por familia** para que Plotly siga fluido (p. ej. 80k–150k).
- Sin `--require-e-rho` entran más composiciones, pero muchas sin E o ρ no verán puntos en ejes que los exijan.

**Modo JSON externo:** si el dashboard usa `glasses_data.json`, el navegador debe abrir la página vía HTTP:

```bash
python scripts/serve_dashboard.py
```

Luego: http://127.0.0.1:8765/ashby_dashboard.html

**Solo regenerar el dashboard** desde un CSV ya normalizado:

```bash
python scripts/build_dashboard.py --csv data/processed/tu_normalizado.csv --mode auto
python scripts/build_dashboard.py --help   # --max-records, --mode embed|external
```

- `auto`: incrusta JSON en el HTML si hay pocas filas; si hay muchas, escribe `web/glasses_data.json` y el HTML hace `fetch()`.
- `embed` fuerza todo inline (útil para abrir el `.html` con doble clic).
- `external` siempre genera `glasses_data.json` (recomendado para cientos de miles de puntos).
