# py -m streamlit run src/optimization/app.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

from src.optimization.run_test import (
    run_period,
    DEFAULT_PARAMS,
)

st.set_page_config(page_title="Battery Optimization", layout="wide")

st.title("Battery Optimization Tool")

st.sidebar.header("Input")

uploaded_file = st.sidebar.file_uploader("Upload OBJ_NAMAS CSV", type=["csv"])

start_date = st.sidebar.date_input("Start date", datetime(2022, 9, 1))
end_date = st.sidebar.date_input("End date", datetime(2022, 9, 8))

zone = st.sidebar.selectbox("ENTSO-E zone", ["LT", "LV", "EE"], index=0)

if st.sidebar.button("Clear"):
    st.experimental_rerun()

# Battery parameters
st.sidebar.subheader("Battery parameters")
DEFAULT_PARAMS["E_max"] = st.sidebar.number_input("Battery capacity (kWh)", value=DEFAULT_PARAMS["E_max"])
DEFAULT_PARAMS["P_ch_max"] = st.sidebar.number_input("Max charge power (kW)", value=DEFAULT_PARAMS["P_ch_max"])
DEFAULT_PARAMS["P_dis_max"] = st.sidebar.number_input("Max discharge power (kW)", value=DEFAULT_PARAMS["P_dis_max"])
DEFAULT_PARAMS["SoC_start"] = st.sidebar.number_input("Initial SoC (kWh)", value=DEFAULT_PARAMS["SoC_start"])

# --- Main area ---
if st.sidebar.button("Optimize"):

    if uploaded_file is None:
        st.error("Please upload OBJ_NAMAS CSV first.")
        st.stop()

    # Save uploaded file temporarily
    temp_path = "temp_load.csv"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.info("Running optimization...")

    # date_input grąžina date → paverčiam į datetime be tz
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.min.time())

    results, metrics = run_period(
        start=start_dt,
        end=end_dt,
        zone=zone,
        load_csv_path=temp_path,
        params=DEFAULT_PARAMS
    )

    st.success("Optimization completed!")

    # --- Show results ---
    st.subheader("Results table")
    st.dataframe(results)

    # --- Plot ---
    st.subheader("Energy flows")
    fig, ax = plt.subplots(figsize=(14, 6))
    cols = [c for c in ["load", "gen_ren", "P_ch", "P_dis", "SoC"] if c in results.columns]
    results[cols].plot(ax=ax)
    st.pyplot(fig)

    # --- Financial metrics ---
    st.subheader("Financial summary")
    st.json(metrics["financial"])
