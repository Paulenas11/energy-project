import pandas as pd
from .model_daily import optimize_day


def run_daily_optimization(market_df, load_series, params):
    """
    Run day-by-day optimization over the full time period.
    Each day is optimized independently using the daily LP model.
    """

    # Work on a copy to avoid modifying the original market dataframe
    df = market_df.copy()

    # Attach load series to the market dataframe (aligned by timestamp)
    df["load"] = load_series

    # Extract unique days from the datetime index
    days = sorted(df.index.normalize().unique())

    all_results = []

    # Process each day separately (myopic daily optimization)
    for day in days:
        # Select rows belonging to the current day
        day_mask = df.index.normalize() == day
        df_day = df.loc[day_mask]

        # Extract daily input arrays for the optimization model
        prices = df_day["price_eur_mwh"].values
        load = df_day["load"].values
        gen_ren = df_day["gen_ren"].values

        # Solve the optimization problem for this day
        res_day = optimize_day(prices, load, gen_ren, params)

        # Attach timestamps back to the daily results
        res_day["timestamp"] = df_day.index.values

        # Store daily results for later concatenation
        all_results.append(res_day)

    # Combine all daily results into a single time-indexed dataframe
    final = pd.concat(all_results).set_index("timestamp")

    return final
