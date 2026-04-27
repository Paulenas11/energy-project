import pandas as pd
from src.entsoe_client import get_day_ahead_prices


def load_obj_namas(path):
    """
    Load household (OBJ_NAMAS) CSV data and convert it into a clean
    hourly time series with 'load' and 'gen_pv' columns.

    Expected CSV columns:
        - PL_T : timestamp column
        - P+   : consumption (kW)
        - P-   : PV generation (kW)

    Returns:
        DataFrame indexed by hourly timestamps (Europe/Vilnius)
        with columns: ['load', 'gen_pv']
    """

    df = pd.read_csv(path)

    # Ensure required timestamp column exists
    if "PL_T" not in df.columns:
        raise ValueError("CSV must contain PL_T column")

    # Parse timestamps
    df["timestamp"] = pd.to_datetime(df["PL_T"], errors="coerce")

    # Localize to Europe/Vilnius, handling DST issues
    df["timestamp"] = df["timestamp"].dt.tz_localize(
        "Europe/Vilnius",
        ambiguous="NaT",
        nonexistent="shift_forward"
    )

    # Drop invalid timestamps
    df = df.dropna(subset=["timestamp"])
    df = df.sort_values("timestamp")
    df = df.set_index("timestamp")

    # Ensure required power columns exist
    if "P+" not in df.columns or "P-" not in df.columns:
        raise ValueError("CSV must contain P+ and P- columns")

    # Map raw columns to load and PV generation
    df["load"] = df["P+"]
    df["gen_pv"] = df["P-"]

    # Align to hourly resolution
    df.index = df.index.floor("h")

    return df[["load", "gen_pv"]].fillna(0)


def load_prices(start, end, zone):
    """
    Load day-ahead electricity prices from ENTSO-E and return
    an hourly price series in Europe/Vilnius timezone.

    Steps:
        - Fetch raw prices
        - Ensure timezone awareness
        - Convert to UTC
        - Floor to hourly timestamps
        - Convert to Europe/Vilnius
    """

    prices = get_day_ahead_prices(start, end, zone)
    prices = prices.rename("price").to_frame()

    # Ensure timezone is set
    if prices.index.tz is None:
        prices.index = prices.index.tz_localize("UTC")

    # Normalize to UTC and hourly resolution
    prices = prices.tz_convert("UTC")
    prices.index = prices.index.floor("h")

    # Convert to local time
    prices = prices.tz_convert("Europe/Vilnius")

    return prices


def build_dataset(obj_path, start, end, zone):
    """
    Build the full dataset required for optimization.

    Steps:
        1. Load household load + PV data
        2. Slice to selected date range
        3. Load day-ahead prices
        4. Join datasets
        5. Fill missing values
        6. Return clean, sorted DataFrame

    Output columns:
        - load
        - gen_pv
        - price
    """

    # Load household data
    df_obj = load_obj_namas(obj_path)

    # Restrict to selected time window
    df_obj = df_obj.loc[start:end]

    # Load price data
    df_price = load_prices(start, end, zone)

    # Merge load/PV with prices
    df = df_obj.join(df_price, how="left")

    # Fill missing values
    df["price"] = df["price"].ffill().bfill()
    df["load"] = df["load"].fillna(0)
    df["gen_pv"] = df["gen_pv"].fillna(0)

    return df.sort_index()
