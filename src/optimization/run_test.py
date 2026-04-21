import pandas as pd
from datetime import datetime

from src.optimization.model_runner import run_daily_optimization
from src.optimization.metrics import compute_metrics

from src.entsoe_client import get_day_ahead_prices


def load_profile_from_csv(path, start, end):
    """
    Load consumption and generation data from a CSV file and
    prepare hourly time series for the selected period.
    """

    df = pd.read_csv(path)

    # Convert timestamp column and set as index
    df["PL_T"] = pd.to_datetime(df["PL_T"], errors="coerce")
    df = df.set_index("PL_T").sort_index()

    # Convert consumption (P+) and generation (P-) to numeric
    df["P+"] = pd.to_numeric(df["P+"], errors="coerce").fillna(0)
    df["P-"] = pd.to_numeric(df["P-"], errors="coerce").fillna(0)

    # All objects contribute to consumption
    load = df["P+"].resample("1h").sum().fillna(0)

    # Only producer objects contribute to generation
    df_gen = df[df["OBJ_GV_TIPAS"] == "G"]
    gen = df_gen["P-"].resample("1h").sum().fillna(0)

    # Restrict to selected time window
    load = load.loc[start:end]
    gen = gen.loc[start:end]

    # Ensure continuous hourly index
    idx = pd.date_range(start, end, freq="1h")
    load = load.reindex(idx).fillna(0)
    gen = gen.reindex(idx).fillna(0)

    return load.rename("load"), gen.rename("gen_ren")


def build_df(prices, gen):
    """
    Build a unified dataframe containing market prices and
    renewable generation aligned on the same hourly index.
    """

    df = pd.DataFrame(index=prices.index)

    df["price_eur_mwh"] = prices
    df["gen_ren"] = gen  # renewable generation from the user's profile

    # Fill missing values to ensure model stability
    df["price_eur_mwh"] = df["price_eur_mwh"].ffill().bfill().fillna(0)
    df["gen_ren"] = df["gen_ren"].fillna(0)

    return df


# Default battery and grid parameters used if none are provided
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


def run_period(start, end, zone, load_csv_path, params=None):
    """
    Run the full optimization workflow for a selected time period:
    - fetch day-ahead prices,
    - load consumption and generation profiles,
    - align all data,
    - run daily optimization,
    - compute summary metrics.
    """

    if params is None:
        params = DEFAULT_PARAMS

    # Convert pandas timestamps to Python datetime if needed
    if isinstance(start, pd.Timestamp):
        start = start.to_pydatetime()
    if isinstance(end, pd.Timestamp):
        end = end.to_pydatetime()

    # Fetch day-ahead electricity prices from ENTSO-E
    prices = get_day_ahead_prices(start, end, zone)

    # Convert timezone to local (Vilnius) and remove tz info
    if prices.index.tz is not None:
        prices.index = prices.index.tz_convert("Europe/Vilnius").tz_localize(None)

    # Remove duplicate timestamps and sort
    prices = prices[~prices.index.duplicated(keep="first")]
    prices = prices.sort_index()

    # Load user consumption and generation profiles
    load, gen_user = load_profile_from_csv(load_csv_path, start, end)

    # Align load and generation to the price index
    idx = prices.index
    load = load.reindex(idx).fillna(0)
    gen = gen_user.reindex(idx).fillna(0)

    # If no generation exists, create a zero series
    if gen.sum() == 0:
        gen = pd.Series(0, index=idx, name="gen_ren")

    # Build combined market dataframe
    market_df = build_df(prices, gen)
    market_df = market_df.fillna(0)

    # Run daily optimization and compute metrics
    results = run_daily_optimization(market_df, load, params)
    metrics = compute_metrics(results)

    return results, metrics


if __name__ == "__main__":
    # Example usage for testing the optimization pipeline

    start = datetime(2022, 9, 1)
    end_week = datetime(2022, 9, 8)
    end_month = datetime(2022, 10, 1)

    ZONE = "LT"
    LOAD_CSV = "../../data/OBJ_NAMAS_1.csv"

    # Weekly results
    results_week, metrics_week = run_period(start, end_week, ZONE, LOAD_CSV)
    print("\n=== WEEKLY FINANCIAL METRICS ===")
    print(metrics_week["financial"])

    # Monthly results
    results_month, metrics_month = run_period(start, end_month, ZONE, LOAD_CSV)
    print("\n=== MONTHLY FINANCIAL METRICS ===")
    print(metrics_month["financial"])
