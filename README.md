# Glass Ashby Explorer

An interactive web application for exploring Ashby diagrams of vitreous materials using data from the SciGlass database.

## Features

- Interactive exploration of glass properties
- Ashby diagrams with multiple physical properties
- Filters by material family
- Tabular data visualization
- Responsive interface with light and dark themes

## Installation

### Prerequisites

- Python 3.8+
- pip

### Installing dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Run local server

```bash
python scripts/serve_dashboard.py
```

### Generate static dashboards

```bash
python scripts/build_dashboard.py
```

The generated HTML files will be available in the `web/` directory.

## Data Sources

The glass properties data comes from the **SciGlass** database published by EPAM Systems on GitHub under the [ODC Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/).

- Repository: https://github.com/epam/SciGlass
- Subset used: ~2,000 glass compositions (MVP sample)
- Derived data (processed CSV) is distributed under the same ODbL license.

## Project Structure

```
├── data/                 # SciGlass data files
├── scripts/              # Processing and generation scripts
├── src/                  # Python source code
├── web/                  # Generated HTML files
├── LICENSE_DATA.md       # Full ODbL license text
└── README.md            # This file
```

## Contributing

If you wish to contribute to this project, please consider:

1. Respect the ODbL license terms for the data used
2. Maintain appropriate attribution in any modifications
3. Document any changes in data handling

## Licenses

- **Data**: SciGlass Database - ODC Open Database License (ODbL) v1.0
