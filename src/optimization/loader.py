import pandas as pd
from src.entsoe_client import get_day_ahead_prices


# ---------------------------------------------------------
# 1. OBJ_NAMAS LOADER (PROSUMER)
# ---------------------------------------------------------
def load_obj_namas(path):
    df = pd.read_csv(path)

    if "PL_T" not in df.columns:
        raise ValueError("CSV must contain PL_T column")

    # Parse timestamp
    df["timestamp"] = pd.to_datetime(df["PL_T"], errors="coerce")

    # Localize su DST fix
    df["timestamp"] = df["timestamp"].dt.tz_localize(
        "Europe/Vilnius",
        ambiguous="NaT",
        nonexistent="shift_forward"
    )

    df = df.dropna(subset=["timestamp"])
    df = df.sort_values("timestamp")
    df = df.set_index("timestamp")

    if "P+" not in df.columns or "P-" not in df.columns:
        raise ValueError("CSV must contain P+ and P- columns")

    df["load"] = df["P+"]
    df["gen_pv"] = df["P-"]

    df = df[["load", "gen_pv"]].fillna(0)

    return df


# ---------------------------------------------------------
# 2. ENTSO-E PRICES (DST SAFE)
# ---------------------------------------------------------
def load_prices(start, end, zone):

    prices = get_day_ahead_prices(start, end, zone)
    prices = prices.rename("price").to_frame()

    # Ensure timezone
    if prices.index.tz is None:
        prices.index = prices.index.tz_localize("UTC")

    prices = prices.tz_convert("UTC")

    # Safe rounding
    prices.index = prices.index.floor("h")

    # Back to LT
    prices = prices.tz_convert("Europe/Vilnius")

    return prices


# ---------------------------------------------------------
# 3. BUILD DATASET (DST SAFE)
# ---------------------------------------------------------
def build_dataset(obj_path, start, end, zone):

    # --------------------------
    # Load OBJ_NAMAS
    # --------------------------
    df_obj = load_obj_namas(obj_path)

    df_obj = df_obj.tz_convert("UTC")
    df_obj.index = df_obj.index.floor("h")
    df_obj = df_obj.tz_convert("Europe/Vilnius")

    df_obj = df_obj.loc[start:end]

    # --------------------------
    # Load prices
    # --------------------------
    df_price = load_prices(start, end, zone)

    # --------------------------
    # Merge
    # --------------------------
    df = df_obj.join(df_price, how="left")

    # --------------------------
    # Fill missing
    # --------------------------
    df["price"] = df["price"].ffill().bfill()
    df["load"] = df["load"].fillna(0)
    df["gen_pv"] = df["gen_pv"].fillna(0)

    df = df.fillna(0)
    df = df.sort_index()

    return df