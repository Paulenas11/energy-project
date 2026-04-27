# Energy Data Pipeline & Battery Dispatch Optimization  
### ENTSO‑E + PVGIS Integration • Myopic Battery Dispatch Model • Streamlit App

This project implements a complete workflow for:

1. Collecting and processing electricity market data from ENTSO‑E  
2. Retrieving modeled solar generation from PVGIS  
3. Building a unified hourly dataset  
4. Running a battery dispatch optimization model  
5. Visualizing and exporting results through a Streamlit application  

The system is designed for:

- Energy market analysis  
- PV + battery system studies  
- Academic research  
- Forecasting and optimization experiments  

---

## Project Overview

### 1. ENTSO‑E Data Pipeline
Retrieves and processes:

- Day‑ahead electricity prices  
- Actual generation (solar, wind, hydro, thermal)  
- Forecasted renewable generation  
- Cross‑border physical flows  
- TSO‑level domain mapping  
- Time‑zone‑corrected hourly datasets  

### 2. PVGIS Solar Modeling
Retrieves:

- Hourly modeled PV generation  
- Based on geographic coordinates  
- Using PVGIS “Series” API  

### 3. Unified Dataset Builder
All data is:

- Converted to hourly resolution  
- Localized to `Europe/Vilnius`  
- Merged into a single DataFrame  

### 4. Battery Dispatch Optimization
Implements a myopic (day‑by‑day) linear optimization model:

- Battery charge/discharge  
- PV self‑consumption  
- Grid import/export  
- SoC constraints  
- End‑of‑day SoC requirement  
- Optional curtailment and load shedding  

### 5. Streamlit Application
Interactive UI for:

- Uploading Prosumer Dataset CSV  
- Selecting date range  
- Running optimization  
- Viewing results  
- Exporting CSV  

---

## Project Structure

```
project/
│
├── optimization/
│   ├── app.py              # Streamlit UI
│   ├── dispatch.py         # Battery dispatch optimization model
│   ├── loader.py           # Dataset builder (load + PV + prices)
│   ├── cost_model.py       # TAC cost model
│   └── cache/              # Cached ENTSO‑E responses
│
├── src/
│   ├── entsoe_client.py    # ENTSO‑E API wrapper
│   ├── entsoe_dataset.py   # Dataset utilities
│   ├── entsoe_static.py    # Domain mappings, TSO codes
│   ├── pvgis_client.py     # PVGIS API wrapper
│   ├── pvgis_dataset.py    # PVGIS dataset builder
│   ├── geocoding.py        # Nominatim geocoder
│   └── market_data.py      # Market data helpers
│
├── notebooks/
│   ├── 01_entsoe.ipynb     # ENTSO‑E data exploration
│   ├── 02_pvgis.ipynb      # PVGIS modeling
│   └── 03_merge.ipynb      # Dataset merging
│
├── tests/
│   ├── test_entsoe_client.py
│   ├── test_entsoe_dataset.py
│   ├── test_geocoding.py
│   └── test_pvgis_dataset.py
│
├── data/                   # Exported datasets
├── cache/                  # Cached API responses
├── requirements.txt
└── README.md
```

---

## Installation

### Create Virtual Environment

```bash
python -m venv .venv
```

Activate:

**Linux/macOS**
```bash
source .venv/bin/activate
```

**Windows**
```bash
.venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Streamlit Application

```bash
cd energy-project/src/optimization
streamlit run app.py
```

To run the optimization:

- Upload Prosumer Dataset CSV  
- Select date range  
- Choose ENTSO‑E zone  
- Set PV and battery parameters  
- Run optimization  
- Download results  

---

## Output Dataset

Each row contains:

| Column | Description |
|--------|-------------|
| load | Household consumption (kW) |
| gen_pv | PV generation (kW) |
| price | Day‑ahead price (€/MWh) |
| P_pv_use | PV → load |
| P_ch | PV → battery |
| P_dis | Battery → load |
| P_grid_imp | Import from grid |
| P_grid_exp | Export to grid |
| E | Battery SoC (kWh) |

---

## Time Handling

All timestamps are:

- Localized to `Europe/Vilnius`  
- Aligned to hourly resolution  
- DST‑safe (handles ambiguous/nonexistent times)  

---

## License

This project is intended for academic and research use.
