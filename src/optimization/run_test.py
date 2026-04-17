# src/optimization/run_test.py

import pandas as pd
from datetime import datetime

from src.optimization.model_runner import run_daily_optimization
from src.optimization.metrics import compute_metrics

from src.entsoe_client import get_day_ahead_prices


# =========================================================
# 1. APKROVOS IR GAMYBOS PROFILIS IŠ OBJ_NAMAS CSV
# =========================================================

print(">>> LOADED NEW run_test.py (NO ENTSOE GEsadaadsdsadsadsadsadsaNERATION)")

def load_profile_from_csv(path, start, end):
    df = pd.read_csv(path)

    df["PL_T"] = pd.to_datetime(df["PL_T"], errors="coerce")
    df = df.set_index("PL_T").sort_index()

    df["P+"] = pd.to_numeric(df["P+"], errors="coerce").fillna(0)
    df["P-"] = pd.to_numeric(df["P-"], errors="coerce").fillna(0)

    # Visi objektai turi vartojimą
    load = df["P+"].resample("1h").sum().fillna(0)

    # Gamyba tik iš gamintojų
    df_gen = df[df["OBJ_GV_TIPAS"] == "G"]
    gen = df_gen["P-"].resample("1h").sum().fillna(0)

    load = load.loc[start:end]
    gen = gen.loc[start:end]

    idx = pd.date_range(start, end, freq="1h")
    load = load.reindex(idx).fillna(0)
    gen = gen.reindex(idx).fillna(0)

    return load.rename("load"), gen.rename("gen_ren")




# =========================================================
# 2. MARKET DATAFRAME KONSTRUKCIJA
# =========================================================

def build_df(prices, gen):
    df = pd.DataFrame(index=prices.index)

    df["price_eur_mwh"] = prices
    df["gen_ren"] = gen  # tik namo gamyba

    df["price_eur_mwh"] = df["price_eur_mwh"].ffill().bfill().fillna(0)
    df["gen_ren"] = df["gen_ren"].fillna(0)

    return df


# =========================================================
# 3. PARAMETRAI
# =========================================================

DEFAULT_PARAMS = {
    "E_max": 10,
    "P_ch_max": 5,
    "P_dis_max": 5,
    "eta_ch": 0.95,
    "eta_dis": 0.95,
    "soc_min": 0.1,
    "soc_max": 0.9,
    "SoC_start": 5,
    "P_grid_max": 10,
    "sell_price_factor": 0.7,
}


# =========================================================
# 4. VIENO PERIODO PALEIDIMAS (TIK NAMAS)
# =========================================================

def run_period(start, end, zone, load_csv_path, params=None):
    if params is None:
        params = DEFAULT_PARAMS

    # Užtikrinam, kad start/end yra datetime be tz
    if isinstance(start, pd.Timestamp):
        start = start.to_pydatetime()
    if isinstance(end, pd.Timestamp):
        end = end.to_pydatetime()

    # --- 1. KAINOS (ENTSO-E) ---
    prices = get_day_ahead_prices(start, end, zone)

    if prices.index.tz is not None:
        prices.index = prices.index.tz_convert("Europe/Vilnius").tz_localize(None)

    prices = prices[~prices.index.duplicated(keep="first")]
    prices = prices.sort_index()

    # --- 2. APKROVA IR GAMYBA IŠ NAMO CSV ---
    load, gen_user = load_profile_from_csv(load_csv_path, start, end)

    # --- 3. SUDERINAME VISKĄ SU KAINŲ INDEKSU ---
    idx = prices.index

    load = load.reindex(idx).fillna(0)
    gen = gen_user.reindex(idx).fillna(0)

    # Jei namas negamina → priverstinai 0
    if gen.sum() == 0:
        gen = pd.Series(0, index=idx, name="gen_ren")

    # --- 4. MARKET DF ---
    market_df = build_df(prices, gen)
    market_df = market_df.fillna(0)

    # --- 5. OPTIMIZACIJA ---
    results = run_daily_optimization(market_df, load, params)
    metrics = compute_metrics(results)

    return results, metrics


# =========================================================
# 5. PAGRINDINIS PALEIDIMAS (TESTAS)
# =========================================================

if __name__ == "__main__":
    start = datetime(2022, 9, 1)
    end_week = datetime(2022, 9, 8)
    end_month = datetime(2022, 10, 1)

    ZONE = "LT"
    LOAD_CSV = "../../data/OBJ_NAMAS_1.csv"

    results_week, metrics_week = run_period(start, end_week, ZONE, LOAD_CSV)
    print("\n=== SAVAITĖS FINANSINĖS METRIKOS ===")
    print(metrics_week["financial"])

    results_month, metrics_month = run_period(start, end_month, ZONE, LOAD_CSV)
    print("\n=== MĖNESIO FINANSINĖS METRIKOS ===")
    print(metrics_month["financial"])
