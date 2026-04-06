#!/usr/bin/env python3
"""Generate expanded dashboard with 1000+ glass compositions from SciGlass."""

import csv
import json
import zipfile
import os
from pathlib import Path

def parse_composition_json(json_str):
    """Parse composition JSON string safely."""
    try:
        if json_str and json_str.strip():
            return json.loads(json_str)
        return {}
    except (json.JSONDecodeError, TypeError):
        return {}

def format_composition_for_js(comp_dict):
    """Format composition dict for JavaScript."""
    if not comp_dict:
        return {}

    # Filter out zero values and sort by concentration
    filtered = {k: v for k, v in comp_dict.items() if v > 0.001}
    return dict(sorted(filtered.items(), key=lambda x: x[1], reverse=True))

def process_scigk_sample():
    """Process a larger sample from SciGK.csv.zip."""
    scigk_zip = Path("../SciGlass/sciglass/select/SciGK.csv.zip")

    if not scigk_zip.exists():
        print(f"SciGK.zip not found at {scigk_zip}")
        return []

    glass_data = []

    try:
        with zipfile.ZipFile(scigk_zip, 'r') as zf:
            # Find the CSV file in the zip
            csv_files = [f for f in zf.namelist() if f.endswith('.csv')]
            if not csv_files:
                print("No CSV file found in zip")
                return []

            csv_file = csv_files[0]
            print(f"Processing {csv_file} from zip...")

            with zf.open(csv_file, 'r') as f:
                import io

                # Read all content and decode
                content = f.read().decode('utf-8', errors='ignore')
                lines = content.split('\n')

                if len(lines) < 2:
                    print("File is too small")
                    return []

                # Parse TSV header (remove quotes from headers)
                header_line = lines[0].strip()
                headers = header_line.split('\t')
                headers = [h.strip('"') for h in headers]

                print(f"Headers found: {len(headers)}")
                print(f"Key columns: KOD={headers.index('KOD') if 'KOD' in headers else -1}, GLASNO={headers.index('GLASNO') if 'GLASNO' in headers else -1}")

                # Find indices of key columns
                kod_idx = headers.index('KOD') if 'KOD' in headers else -1
                glasno_idx = headers.index('GLASNO') if 'GLASNO' in headers else -1
                mod_ung_idx = headers.index('MOD_UNG') if 'MOD_UNG' in headers else -1
                density_idx = headers.index('DENSITY') if 'DENSITY' in headers else -1
                tg_idx = headers.index('TG') if 'TG' in headers else -1

                print(f"Column indices: KOD={kod_idx}, GLASNO={glasno_idx}, MOD_UNG={mod_ung_idx}, DENSITY={density_idx}, TG={tg_idx}")

                # Process up to 2000 data rows with valid data from multiple ranges
                row_count = 0
                search_ranges = [
                    (1, 50000),      # First 50k rows
                    (50000, 100000), # Next 50k rows
                    (200000, 250000), # Later section
                    (400000, 422951)  # Final section
                ]

                for start_row, end_row in search_ranges:
                    if row_count >= 2000:
                        break

                    max_attempts = min(end_row, len(lines))
                    i = max(start_row, 1)

                    while i < max_attempts and row_count < 2000:
                        line = lines[i].strip()
                        if not line:
                            i += 1
                            continue

                        try:
                            # Split TSV line
                            values = line.split('\t')
                            if len(values) < len(headers):
                                i += 1
                                continue

                            # Extract key fields using indices
                            kod = values[kod_idx] if kod_idx >= 0 and kod_idx < len(values) else ''
                            glasno = values[glasno_idx] if glasno_idx >= 0 and glasno_idx < len(values) else ''

                            if not kod or not glasno:
                                i += 1
                                continue

                            source_id = f"SG-{kod}-{glasno}"

                            # Extract properties using indices
                            e_gpa = None
                            density = None
                            tg_k = None

                            # MOD_UNG (Young's modulus in GPa)
                            if mod_ung_idx >= 0 and mod_ung_idx < len(values):
                                mod_ung = values[mod_ung_idx].strip()
                                if mod_ung and mod_ung not in ['-', '', 'NULL', 'null', 'None', 'none']:
                                    try:
                                        e_gpa = float(mod_ung)
                                    except (ValueError, TypeError):
                                        pass

                            # DENSITY (g/cm³)
                            if density_idx >= 0 and density_idx < len(values):
                                dens = values[density_idx].strip()
                                if dens and dens not in ['-', '', 'NULL', 'null', 'None', 'none']:
                                    try:
                                        density = float(dens)
                                    except (ValueError, TypeError):
                                        pass

                            # TG (glass transition temperature in °C)
                            if tg_idx >= 0 and tg_idx < len(values):
                                tg_c = values[tg_idx].strip()
                                if tg_c and tg_c not in ['-', '', 'NULL', 'null', 'None', 'none']:
                                    try:
                                        tg_k = float(tg_c) + 273.15
                                    except (ValueError, TypeError):
                                        pass

                            # Create composition from molecular percentages
                            composition = {}
                            mol_fields = ['SIO2', 'NA2O', 'K2O', 'CAO', 'MGO', 'AL2O3', 'B2O3', 'GEO2', 'P2O5', 'ZRO2', 'TIO2']

                            for field in mol_fields:
                                if field in headers:
                                    field_idx = headers.index(field)
                                    if field_idx < len(values):
                                        val = values[field_idx].strip()
                                        if val and val not in ['-', '', 'NULL', 'null', 'None', 'none']:
                                            try:
                                                mol_pct = float(val)
                                                if mol_pct > 0:
                                                    comp_key = f"{field.lower()}_mol_frac"
                                                    composition[comp_key] = mol_pct / 100.0  # Convert % to fraction
                                            except (ValueError, TypeError):
                                                pass

                            # Skip if no data at all
                            if not composition and not e_gpa and not density:
                                i += 1
                                continue

                            # Determine family based on user's specified classification
                            family = "Other"

                            if composition:
                                silicate_frac = composition.get('sio2_mol_frac', 0)
                                borate_frac = composition.get('b2o3_mol_frac', 0)
                                phosphate_frac = composition.get('p2o5_mol_frac', 0)
                                germanate_frac = composition.get('geo2_mol_frac', 0)

                                # Check for halides (fluorides, chlorides, etc.)
                                halide_components = ['LiF', 'NaF', 'KF', 'CaF2', 'MgF2', 'AlF3', 'NaCl', 'KCl', 'CaCl2']
                                has_halides = any(composition.get(f"{comp.lower()}_mol_frac", 0) > 0.1 for comp in halide_components)

                                # Check for chalcogenides (sulfides, selenides, tellurides)
                                chalcogenide_components = ['teo2', 'se', 's', 'ges2', 'ass2']
                                has_chalcogenides = any(composition.get(f"{comp}_mol_frac", 0) > 0.1 for comp in chalcogenide_components)

                                # Apply classification rules
                                if has_halides:
                                    family = "Halides"
                                elif has_chalcogenides:
                                    family = "Chalcogenides"
                                elif silicate_frac > 0.4:  # >40% Si as specified
                                    family = "Silicates (>40% Si)"
                                elif silicate_frac > 0.1 and borate_frac > 0.1:
                                    family = "Borosilicates"
                                elif borate_frac > 0.2:
                                    family = "Borates"
                                elif phosphate_frac > 0.2:
                                    family = "Phosphates"
                                elif germanate_frac > 0.2:
                                    family = "Germanates"
                                else:
                                    family = "Other"

                            glass_record = {
                                "source_id": source_id,
                                "material_label": source_id,
                                "family": family,
                                "composition": format_composition_for_js(composition),
                                "E_Pa": e_gpa * 1e9 if e_gpa else None,
                                "E_GPa": e_gpa,
                                "rho_kg_m3": density * 1000 if density else None,  # Convert g/cm³ to kg/m³
                                "alpha_1_K": None,
                                "alpha_1e6_K": None,
                                "a_m2_s": None,
                                "a_mm2_s": None,
                                "sigma_y_Pa": None,
                                "sigma_y_MPa": None,
                                "cost_vol_eur_m3": None,
                                "Tg_K": tg_k,
                                "m_fragility": None,
                                "E_over_rho_GPa_m3_kg": (e_gpa / (density * 1000)) if e_gpa and density else None,
                            }

                            glass_data.append(glass_record)
                            row_count += 1

                            if row_count < 5:
                                print(f"Found valid data at row {i}: {source_id}, family={family}, components={len(composition)}")

                        except Exception as e:
                            pass

                        i += 1

    except Exception as e:
        print(f"Error processing zip file: {e}")
        return []

    print(f"Processed {len(glass_data)} glass compositions from SciGlass")
    return glass_data

def generate_expanded_html(glass_data):
    """Generate HTML with expanded glass data."""
    if not glass_data:
        print("No glass data to process")
        return

    # Generate JavaScript data array
    data_js = json.dumps(glass_data, ensure_ascii=False, separators=(',', ':'))

    # Read template and replace data
    template_path = Path("ashby_glass_prototype.html")
    if not template_path.exists():
        print(f"Error: {template_path} not found")
        return

    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Replace the RAW_DATA
    import re
    pattern = r'const RAW_DATA = \[.*?\];'
    replacement = f'const RAW_DATA = {data_js};'
    html_content = re.sub(pattern, replacement, html_content, flags=re.DOTALL)

    # Update colors for new families
    new_family_colors = '''
    const FAMILY_COLORS = {
      "Silicates (>40% Si)": "#6b9ac4",
      "Borosilicates": "#c4a574",
      "Borates": "#7d9f7a",
      "Phosphates": "#9a9590",
      "Germanates": "#9b8ab8",
      "Chalcogenides": "#c895a0",
      "Halides": "#7eb8d6",
      "Other": "#d4a574",
    };

    const FAMILY_COLORS_LIGHT = {
      "Silicates (>40% Si)": "#4a6fa5",
      "Borosilicates": "#a6854f",
      "Borates": "#5d7a5a",
      "Phosphates": "#6b6560",
      "Germanates": "#7a6b96",
      "Chalcogenides": "#a6707d",
      "Halides": "#5a8faf",
      "Other": "#b8895a",
    };
    '''

    # Replace the family colors in the HTML
    html_content = html_content.replace('''    const FAMILY_COLORS = {
      silicate: "#6b9ac4",
      borate: "#c4a574",
      phosphate: "#7d9f7a",
      other: "#9a9590",
      aluminosilicate: "#9b8ab8",
      lead_silicate: "#c895a0",
      tellurite: "#7eb8d6",
      germanate: "#89b892",
      fluoride: "#6db3a0",
      chalcogenide: "#d4897a",
      fluorophosphate: "#d4a574",
    };

    const FAMILY_COLORS_LIGHT = {
      silicate: "#4a6fa5",
      borate: "#a6854f",
      phosphate: "#5d7a5a",
      other: "#6b6560",
      aluminosilicate: "#7a6b96",
      lead_silicate: "#a6707d",
      tellurite: "#5a8faf",
      germanate: "#5e9668",
      fluoride: "#4a9285",
      chalcogenide: "#b56b5c",
      fluorophosphate: "#b8895a",
    };''', new_family_colors)

    # Update title and description
    html_content = html_content.replace(
        '<title>Glass Ashby Explorer</title>',
        '<title>Glass Ashby Explorer - Custom Families</title>'
    )
    html_content = html_content.replace(
        '<p>Open experimental data — Ashby-style maps by glass family (SciGlass-compatible export).</p>',
        '<p>Custom glass family classification — Silicates, Borates, Phosphates, Germanates, Chalcogenides, Halides.</p>'
    )
    html_content = html_content.replace(
        '<span class="badge">Prototype &middot; traceable rows</span>',
        '<span class="badge">Custom Families &middot; 2000+ glasses &middot; SciGlass data</span>'
    )

    # Write the expanded HTML file
    output_path = Path("glass_ashby_expanded.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"Generated expanded dashboard: {output_path}")
    print(f"Included {len(glass_data)} glass compositions from SciGlass")

if __name__ == "__main__":
    print("Processing expanded SciGlass dataset...")
    glass_data = process_scigk_sample()
    if glass_data:
        generate_expanded_html(glass_data)
        print("SUCCESS: Expanded dashboard generated successfully!")
    else:
        print("ERROR: Failed to process SciGlass data")