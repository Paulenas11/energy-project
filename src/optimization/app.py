import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from dispatch import DispatchModel
from loader import build_dataset


# ---------------------------------------------------------------------
# Streamlit UI configuration
# ---------------------------------------------------------------------
st.set_page_config(page_title="Battery Dispatch Tool", layout="wide")
st.title("Battery Dispatch (Prosumers)")

st.sidebar.header("Input")

# ---------------------------------------------------------------------
# File upload
# ---------------------------------------------------------------------
uploaded_file = st.sidebar.file_uploader(
    "Upload Prosumer Dataset CSV",
    type=["csv"]
)

# ---------------------------------------------------------------------
# Date selection
# ---------------------------------------------------------------------
start_date = st.sidebar.date_input("Start date", datetime(2020, 1, 1))
end_date = st.sidebar.date_input("End date", datetime(2022, 12, 31))

# ---------------------------------------------------------------------
# ENTSO-E zone selection
# ---------------------------------------------------------------------
zone = st.sidebar.selectbox("ENTSO-E zone", ["LT", "LV", "EE"], index=0)

# ---------------------------------------------------------------------
# System parameters
# ---------------------------------------------------------------------
st.sidebar.subheader("System")

P_pv = st.sidebar.number_input(
    "PV capacity (kW)",
    min_value=0.0,
    value=5.0
)

# ---------------------------------------------------------------------
# Battery parameters
# ---------------------------------------------------------------------
st.sidebar.subheader("Battery")

P_b = st.sidebar.number_input(
    "Battery power (kW)",
    min_value=0.0,
    value=3.0
)

E_b = st.sidebar.number_input(
    "Battery energy (kWh)",
    min_value=0.0,
    value=10.0
)

E0 = st.sidebar.number_input(
    "Initial SoC (kWh)",
    min_value=0.0,
    value=5.0
)

# ---------------------------------------------------------------------
# Run optimization button
# ---------------------------------------------------------------------
if st.sidebar.button("Run Optimization"):

    # Ensure CSV is uploaded
    if uploaded_file is None:
        st.error("Upload CSV first.")
        st.stop()

    # Save uploaded file temporarily
    temp_path = "temp_obj.csv"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Local timezone for date conversion
    tz = pytz.timezone("Europe/Vilnius")

    # Convert selected dates to timezone-aware datetimes
    start_dt = tz.localize(datetime.combine(start_date, datetime.min.time()))
    end_dt = tz.localize(datetime.combine(end_date, datetime.min.time()))

    st.info("Loading data...")

    # Build dataset: load + PV + prices
    df = build_dataset(
        obj_path=temp_path,
        start=start_dt,
        end=end_dt,
        zone=zone
    )

    st.success("Data loaded")

    # -----------------------------------------------------------------
    # Optimization model parameters
    # -----------------------------------------------------------------
    params = {
        "eta_c": 0.95,          # Battery charging efficiency
        "eta_d": 0.95,          # Battery discharging efficiency
        "SoC_min": 0.1,         # Minimum SoC fraction
        "SoC_max": 0.9,         # Maximum SoC fraction
        "P_grid_max": 10.0,     # Grid import/export limit (kW)
        "X": 1.0,               # Import price adder
        "Y": 1.0,               # Export price adder
        "c_b_var": 0.0,         # Battery variable cycling cost
        "E_terminal_min": 5.0,  # Required SoC at end of day
    }

    st.info("Running optimization...")

    # Initialize dispatch model
    model = DispatchModel(
        P_b=P_b,
        E_b=E_b,
        params=params,
        P_pv=P_pv
    )

    # Run multi-day optimization
    df_dispatch = model.run(df, E0)

    # Check for simultaneous import/export (should not happen)
    df_check = df_dispatch[
         (df_dispatch["P_grid_imp"] > 1e-6) &
         (df_dispatch["P_grid_exp"] > 1e-6)
     ]

    print(df_check)

    st.success("Done")

    # -----------------------------------------------------------------
    # Display results
    # -----------------------------------------------------------------
    st.subheader("Results")
    st.dataframe(df_dispatch, use_container_width=True)

    # -----------------------------------------------------------------
    # Download results
    # -----------------------------------------------------------------
    st.subheader("Download")

    csv = df_dispatch.to_csv().encode("utf-8")

    original_name = Path(uploaded_file.name).stem
    results_filename = f"results_{original_name}.csv"

    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=results_filename,
        mime="text/csv"
    )
