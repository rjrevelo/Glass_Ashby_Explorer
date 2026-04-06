#!/usr/bin/env python3
"""Debug SciGlass data format."""

import zipfile
from pathlib import Path

def debug_sciglass():
    """Debug the SciGlass data format."""
    scigk_zip = Path("../SciGlass/sciglass/select/SciGK.csv.zip")

    if not scigk_zip.exists():
        print("SciGK.zip not found")
        return

    try:
        with zipfile.ZipFile(scigk_zip, 'r') as zf:
            csv_files = [f for f in zf.namelist() if f.endswith('.csv')]
            if not csv_files:
                print("No CSV file found in zip")
                return

            csv_file = csv_files[0]
            print(f"Processing {csv_file}")

            with zf.open(csv_file, 'r') as f:
                content = f.read().decode('utf-8', errors='ignore')
                lines = content.split('\n')

                print(f"Total lines: {len(lines)}")

                # Show first few lines
                print("\nFirst 5 lines:")
                for i in range(min(5, len(lines))):
                    print(f"Line {i}: {repr(lines[i][:100])}...")

                if len(lines) > 0:
                    headers = lines[0].split('\t')
                    print(f"\nHeaders ({len(headers)}):")
                    for i, h in enumerate(headers[:20]):  # First 20 headers
                        print(f"  {i:2d}: {h}")

                    # Look for key columns
                    key_cols = ['KOD', 'GLASNO', 'MOD_UNG', 'DENSITY', 'TG', 'SIO2', 'NA2O', 'GEO2']
                    print("\nKey columns found:")
                    for col in key_cols:
                        if col in headers:
                            idx = headers.index(col)
                            print(f"  {col}: index {idx}")
                        else:
                            print(f"  {col}: NOT FOUND")

                    # Show all headers containing key terms
                    print("\nAll headers with key terms:")
                    for i, h in enumerate(headers):
                        if any(term in h.upper() for term in ['MOD', 'DENS', 'TG', 'GLAS', 'KOD']):
                            print(f"  {i}: {h}")

                    # Show sample data rows
                    print("\nSample data rows:")
                    for i in range(1, min(6, len(lines))):
                        if i < len(lines):
                            values = lines[i].split('\t')
                            kod = values[0] if len(values) > 0 else "N/A"
                            glasno = values[1] if len(values) > 1 else "N/A"
                            mod_ung = values[headers.index('MOD_UNG')] if 'MOD_UNG' in headers and len(values) > headers.index('MOD_UNG') else "N/A"
                            density = values[headers.index('DENSITY')] if 'DENSITY' in headers and len(values) > headers.index('DENSITY') else "N/A"
                            sio2 = values[headers.index('SIO2')] if 'SIO2' in headers and len(values) > headers.index('SIO2') else "N/A"

                            print(f"  Row {i}: KOD={kod}, GLASNO={glasno}, MOD_UNG={mod_ung}, DENSITY={density}, SIO2={sio2}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_sciglass()