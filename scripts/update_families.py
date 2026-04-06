#!/usr/bin/env python3
"""Update family classification in existing dashboard."""

import json
import re

def update_family_classification():
    """Update the family classification in the HTML file."""

    # Read the HTML file
    with open('ashby_glass_prototype.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Extract the RAW_DATA from the HTML
    data_match = re.search(r'const RAW_DATA = (\[.*?\]);', html_content, re.DOTALL)
    if not data_match:
        print("Could not find RAW_DATA in HTML file")
        return

    try:
        glass_data = json.loads(data_match.group(1))
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON data: {e}")
        return

    # Update family classification for each glass
    updated_count = 0
    for glass in glass_data:
        composition = glass.get('composition', {})

        if composition:
            # Find the major component
            major_component = max(composition.items(), key=lambda x: x[1])[0] if composition else None
            major_fraction = max(composition.values()) if composition else 0

            old_family = glass.get('family', 'unknown')

            if major_component == 'sio2_mol_frac' and major_fraction > 0.2:
                # Check for modifiers in silicate glasses
                na_fraction = composition.get('na2o_mol_frac', 0)
                k_fraction = composition.get('k2o_mol_frac', 0)
                cao_fraction = composition.get('cao_mol_frac', 0)
                mgo_fraction = composition.get('mgo_mol_frac', 0)

                if na_fraction > 0.1 or k_fraction > 0.1:
                    new_family = "soda_lime_silicate"
                elif cao_fraction > 0.1 or mgo_fraction > 0.1:
                    new_family = "alkaline_earth_silicate"
                else:
                    new_family = "pure_silicate"
            elif major_component == 'b2o3_mol_frac' and major_fraction > 0.2:
                new_family = "borate"
            elif major_component == 'p2o5_mol_frac' and major_fraction > 0.2:
                new_family = "phosphate"
            elif major_component == 'geo2_mol_frac' and major_fraction > 0.2:
                new_family = "germanate"
            elif major_component == 'al2o3_mol_frac' and major_fraction > 0.2:
                new_family = "aluminate"
            elif composition.get('teo2_mol_frac', 0) > 0.2:
                new_family = "tellurite"
            elif composition.get('zro2_mol_frac', 0) > 0.2:
                new_family = "zirconate"
            elif composition.get('tio2_mol_frac', 0) > 0.2:
                new_family = "titanate"
            elif composition.get('bio2o3_mol_frac', 0) > 0.1:
                new_family = "bismuthate"
            else:
                # Check for mixed systems
                silicate_frac = composition.get('sio2_mol_frac', 0)
                borate_frac = composition.get('b2o3_mol_frac', 0)
                phosphate_frac = composition.get('p2o5_mol_frac', 0)

                if silicate_frac > 0.1 and borate_frac > 0.1:
                    new_family = "borosilicate"
                elif silicate_frac > 0.1 and phosphate_frac > 0.1:
                    new_family = "silicophosphate"
                elif borate_frac > 0.1 and phosphate_frac > 0.1:
                    new_family = "borophosphate"
                elif major_fraction < 0.3:  # No dominant component
                    new_family = "complex_mixed"
                else:
                    new_family = "mixed"

            if new_family != old_family:
                glass['family'] = new_family
                updated_count += 1

    print(f"Updated family classification for {updated_count} glasses")

    # Update the HTML content
    updated_data_js = json.dumps(glass_data, ensure_ascii=False, separators=(',', ':'))
    html_content = re.sub(r'const RAW_DATA = (\[.*?\]);', f'const RAW_DATA = {updated_data_js};', html_content, flags=re.DOTALL)

    # Write back to file
    with open('ashby_glass_prototype.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

    print("Updated ashby_glass_prototype.html with new family classification")

if __name__ == "__main__":
    update_family_classification()