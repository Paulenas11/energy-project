import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

from dispatch import DispatchModel
from loader import build_dataset


st.set_page_config(page_title="Battery Dispatch Tool", layout="wide")
st.title("Battery Dispatch (Prosumers)")

# =========================
# SIDEBAR
# =========================
st.sidebar.header("Input")

uploaded_file = st.sidebar.file_uploader(
    "Upload OBJ_NAMAS CSV",
    type=["csv"]
)

start_date = st.sidebar.date_input("Start date", datetime(2022, 1, 1))
end_date = st.sidebar.date_input("End date", datetime(2022, 12, 31))

zone = st.sidebar.selectbox("ENTSO-E zone", ["LT", "LV", "EE"], index=0)

st.sidebar.subheader("System")

P_pv = st.sidebar.number_input("PV capacity (kW)", min_value=0.0, value=5.0)

st.sidebar.subheader("Battery")

P_b = st.sidebar.number_input("Battery power (kW)", min_value=0.0, value=3.0)
E_b = st.sidebar.number_input("Battery energy (kWh)", min_value=0.0, value=10.0)
E0 = st.sidebar.number_input("Initial SoC (kWh)", min_value=0.0, value=5.0)

# =========================
# RUN BUTTON
# =========================
if st.sidebar.button("Run Optimization"):

    if uploaded_file is None:
        st.error("Upload CSV first.")
        st.stop()

    # Save uploaded file
    temp_path = "temp_obj.csv"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    tz = pytz.timezone("Europe/Vilnius")

    start_dt = tz.localize(datetime.combine(start_date, datetime.min.time()))
    end_dt = tz.localize(datetime.combine(end_date, datetime.min.time()))

    # =========================
    # LOAD DATA
    # =========================
    st.info("Loading data...")

    df = build_dataset(
        obj_path=temp_path,
        start=start_dt,
        end=end_dt,
        zone=zone
    )

    st.success("Data loaded")

    # =========================
    # PARAMS
    # =========================
    params = {
        "eta_c": 0.95,
        "eta_d": 0.95,
        "SoC_min": 0.1,
        "SoC_max": 0.9,
        "P_grid_max": 10.0,
        "X": 0.0,
        "Y": 0.0,
        "c_b_var": 0.0
    }

    # =========================
    # RUN DISPATCH
    # =========================
    st.info("Running optimization...")

    model = DispatchModel(
        P_pv=P_pv,
        P_b=P_b,
        E_b=E_b,
        params=params
    )

    df_dispatch = model.run(df, E0)

    st.success("Done")

    # =========================
    # OUTPUT
    # =========================
    st.subheader("Results")

    st.dataframe(df_dispatch, use_container_width=True)

    # =========================
    # DOWNLOAD
    # =========================
    st.subheader("Download")

    csv = df_dispatch.to_csv().encode("utf-8")

    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="dispatch_results.csv",
        mime="text/csv"
    )