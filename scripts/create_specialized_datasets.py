#!/usr/bin/env python3
"""Create multiple specialized glass datasets with 3-4 properties each."""

import json
import zipfile
from pathlib import Path
from collections import defaultdict

def create_specialized_datasets():
    """Create multiple datasets with different property combinations."""

    scigk_zip = Path("../SciGlass/sciglass/select/SciGK.csv.zip")

    if not scigk_zip.exists():
        print("ERROR: SciGK.csv.zip not found. Please download SciGlass:")
        print("  git clone https://github.com/drcassar/SciGlass.git ../SciGlass")
        return

    # Initialize datasets
    datasets = {
        'thermal': {'name': 'Thermal Dataset', 'props': ['rho_kg_m3', 'Tg_K'], 'data': []},
        'mechanical': {'name': 'Mechanical Dataset', 'props': ['rho_kg_m3', 'E_GPa'], 'data': []},
        'optical': {'name': 'Optical Dataset', 'props': ['rho_kg_m3', 'n_d'], 'data': []},
        'thermal_mechanical': {'name': 'Thermal-Mechanical', 'props': ['rho_kg_m3', 'Tg_K', 'E_GPa'], 'data': []},
        'thermal_optical': {'name': 'Thermal-Optical', 'props': ['rho_kg_m3', 'Tg_K', 'n_d'], 'data': []},
        'mechanical_optical': {'name': 'Mechanical-Optical', 'props': ['rho_kg_m3', 'E_GPa', 'n_d'], 'data': []},
        'thermal_expansion': {'name': 'Thermal Expansion', 'props': ['rho_kg_m3', 'Tg_K', 'alpha_1e6_K'], 'data': []},
        'comprehensive_4prop': {'name': '4-Property Comprehensive', 'props': ['rho_kg_m3', 'Tg_K', 'E_GPa', 'alpha_1e6_K'], 'data': []}
    }

    try:
        with zipfile.ZipFile(scigk_zip, 'r') as zf:
            csv_files = [f for f in zf.namelist() if f.endswith('.csv')]
            if not csv_files:
                print("ERROR: No CSV file found")
                return

            csv_file = csv_files[0]
            print(f"Processing {csv_file} from SciGlass...")

            with zf.open(csv_file, 'r') as f:
                content = f.read().decode('utf-8', errors='ignore')
                lines = content.split('\n')

                if len(lines) < 2:
                    print("ERROR: File too small")
                    return

                # Parse header
                header_line = lines[0].strip()
                headers = header_line.split('\t')
                headers = [h.strip('"') for h in headers]

                # Column indices
                indices = {
                    'kod': headers.index('KOD') if 'KOD' in headers else -1,
                    'glasno': headers.index('GLASNO') if 'GLASNO' in headers else -1,
                    'density': headers.index('DENSITY') if 'DENSITY' in headers else -1,
                    'tg': headers.index('TG') if 'TG' in headers else -1,
                    'mod_ung': headers.index('MOD_UNG') if 'MOD_UNG' in headers else -1,
                    'tec': headers.index('TEC55') if 'TEC55' in headers else -1,
                    'nd': headers.index('ND300') if 'ND300' in headers else -1,
                }

                print(f"Column mapping: {indices}")

                # Process records
                total_processed = 0
                counters = {key: 0 for key in datasets.keys()}

                for i in range(1, len(lines)):
                    line = lines[i].strip()
                    if not line:
                        continue

                    total_processed += 1
                    if total_processed % 100000 == 0:
                        print(f"Processed {total_processed} records...")

                    try:
                        values = line.split('\t')

                        # Extract basic info
                        kod = values[indices['kod']] if indices['kod'] >= 0 and indices['kod'] < len(values) else ''
                        glasno = values[indices['glasno']] if indices['glasno'] >= 0 and indices['glasno'] < len(values) else ''

                        if not kod or not glasno:
                            continue

                        source_id = f"SG-{kod}-{glasno}"

                        # Extract properties
                        properties = {}

                        # Density
                        if indices['density'] >= 0 and indices['density'] < len(values):
                            dens_val = values[indices['density']].strip()
                            if dens_val and dens_val not in ['-', '', 'NULL', 'null', 'None', 'none']:
                                try:
                                    properties['rho_kg_m3'] = float(dens_val) * 1000
                                except (ValueError, TypeError):
                                    pass

                        # Tg
                        if indices['tg'] >= 0 and indices['tg'] < len(values):
                            tg_val = values[indices['tg']].strip()
                            if tg_val and tg_val not in ['-', '', 'NULL', 'null', 'None', 'none']:
                                try:
                                    properties['Tg_K'] = float(tg_val) + 273.15
                                except (ValueError, TypeError):
                                    pass

                        # Young's modulus
                        if indices['mod_ung'] >= 0 and indices['mod_ung'] < len(values):
                            mod_val = values[indices['mod_ung']].strip()
                            if mod_val and mod_val not in ['-', '', 'NULL', 'null', 'None', 'none']:
                                try:
                                    properties['E_GPa'] = float(mod_val)
                                    properties['E_Pa'] = float(mod_val) * 1e9
                                except (ValueError, TypeError):
                                    pass

                        # Thermal expansion
                        if indices['tec'] >= 0 and indices['tec'] < len(values):
                            tec_val = values[indices['tec']].strip()
                            if tec_val and tec_val not in ['-', '', 'NULL', 'null', 'None', 'none']:
                                try:
                                    properties['alpha_1e6_K'] = float(tec_val) * 1e6
                                    properties['alpha_1_K'] = float(tec_val)
                                except (ValueError, TypeError):
                                    pass

                        # Refractive index
                        if indices['nd'] >= 0 and indices['nd'] < len(values):
                            nd_val = values[indices['nd']].strip()
                            if nd_val and nd_val not in ['-', '', 'NULL', 'null', 'None', 'none']:
                                try:
                                    properties['n_d'] = float(nd_val)
                                except (ValueError, TypeError):
                                    pass

                        # Get composition
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
                                                composition[comp_key] = mol_pct / 100.0
                                        except (ValueError, TypeError):
                                            pass

                        # Determine family
                        family = "Other"
                        if composition:
                            silicate_frac = composition.get('sio2_mol_frac', 0)
                            borate_frac = composition.get('b2o3_mol_frac', 0)
                            phosphate_frac = composition.get('p2o5_mol_frac', 0)
                            germanate_frac = composition.get('geo2_mol_frac', 0)

                            if silicate_frac > 0.4:
                                family = "Silicates (>40% Si)"
                            elif silicate_frac > 0.1 and borate_frac > 0.1:
                                family = "Borosilicates"
                            elif borate_frac > 0.2:
                                family = "Borates"
                            elif phosphate_frac > 0.2:
                                family = "Phosphates"
                            elif germanate_frac > 0.2:
                                family = "Germanates"

                        # Create base record
                        base_record = {
                            "source_id": source_id,
                            "material_label": source_id,
                            "family": family,
                            "composition": composition,
                            **properties,
                            "a_m2_s": None,
                            "a_mm2_s": None,
                            "sigma_y_Pa": None,
                            "sigma_y_MPa": None,
                            "cost_vol_eur_m3": None,
                            "m_fragility": None,
                            "E_over_rho_GPa_m3_kg": (properties.get('E_GPa', 0) / (properties.get('rho_kg_m3', 1000) / 1000)) if 'E_GPa' in properties and 'rho_kg_m3' in properties else None,
                        }

                        # Add to appropriate datasets
                        for key, dataset in datasets.items():
                            required_props = dataset['props']
                            if all(prop in properties for prop in required_props):
                                if len(dataset['data']) < 10000:  # Limit each dataset to 10k
                                    dataset['data'].append(base_record.copy())
                                    counters[key] += 1

                    except Exception as e:
                        continue

                print(f"\nCompleted processing {total_processed} records from SciGlass")

                # Save datasets
                for key, dataset in datasets.items():
                    if dataset['data']:
                        filename = f"glass_dataset_{key}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(dataset['data'], f, ensure_ascii=False, indent=2)

                        # Family distribution
                        families = defaultdict(int)
                        for glass in dataset['data']:
                            families[glass.get('family', 'Other')] += 1

                        print(f"\n{dataset['name']} ({len(dataset['data'])} glasses):")
                        print(f"  Properties: {', '.join(dataset['props'])}")
                        print("  Family distribution:")
                        for fam, count in sorted(families.items()):
                            print(f"    {fam}: {count}")

                    else:
                        print(f"\n{dataset['name']}: No data found")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    print("Creating specialized glass datasets with 3-4 properties each...")
    create_specialized_datasets()
    print("\nDataset creation completed!")