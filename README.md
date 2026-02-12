#  Energy project

This project implements a complete data pipeline for collecting, processing, and merging electricity market data.

##  Project Structure

```
project/
│
├── src/
│   ├── entsoe_client.py      # Custom ENTSO-E API wrapper
│   ├── pvgis_client.py       # PVGIS API client
│   ├── geocoding.py          # Nominatim geocoding utility
│   └── ...
│
├── notebooks/
│   ├── 01_entsoe.ipynb       # ENTSO-E data collection & export
│   └── 02_pvgis.ipynb        # PVGIS retrieval & dataset merging
│
├── data/
│   ├── market_<start>_<end>.csv   # ENTSO-E dataset
│   └── market_with_pvgis.csv      # Final merged dataset
│
├── requirements.txt
└── README.md
```

---

##  Installation

### Create Virtual Environment

```bash
python -m venv .venv
```

Activate it:

**Linux / macOS**
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

##  Usage Workflow

1. Run `01_entsoe.ipynb`  
   → Collect and export ENTSO-E market data  

2. Run `02_pvgis.ipynb`  
   → Retrieve PVGIS solar data  
   → Merge with ENTSO-E dataset  

3. Final output:

```
data/market_with_pvgis.csv
```

---

##  Time Handling

All time series:
- Converted to hourly resolution  
- Localized to `Europe/Vilnius` timezone  
- Properly aligned before merging  

This ensures compatibility for modeling and forecasting tasks.

---

##  Output Dataset

The final dataset includes:

- Market prices  
- Actual renewable generation  
- Forecasted generation  
- Cross-border flows  
- Modeled PV generation  

All indexed by hourly timestamps.

---

##  License

This project is intended for academic and research use.
