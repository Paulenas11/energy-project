import pandas as pd
from src.entsoe_client import (
    get_day_ahead_prices,
    get_generation,
    get_wind_solar_forecast,
    get_crossborder_flows
)

def get_market_data(start, end, tz="Europe/Vilnius"):
    """
    Fetch and combine all required ENTSO‑E datasets into a unified hourly DataFrame.

    Parameters:
        start (str): Start date (YYYY-MM-DD)
        end (str): End date (YYYY-MM-DD)
        tz (str): Target timezone for all datasets

    Returns:
        pandas.DataFrame: Hourly dataset containing prices, generation,
                          forecasts, and cross‑border flows.
    """

    # Download all required ENTSO‑E datasets
    prices = get_day_ahead_prices(start, end).to_frame("price_eur_mwh")
    gen = get_generation(start, end)
    forecast = get_wind_solar_forecast(start, end)
    flows = get_crossborder_flows(start, end, tz=tz)

    # Flatten MultiIndex columns (technology, type) into simple names
    gen.columns = [
        f"{tech.lower().replace(' ', '_').replace('-', '_')}_{kind.lower().replace(' ', '_')}"
        for tech, kind in gen.columns
    ]

    # Select only the required generation columns
    gen = gen[[
        "solar_actual_aggregated",
        "wind_onshore_actual_aggregated"
    ]]

    # Rename generation columns to clearer names
    gen = gen.rename(columns={
        "solar_actual_aggregated": "gen_solar_mw",
        "wind_onshore_actual_aggregated": "gen_wind_onshore_mw"
    })

    # Rename forecast columns to clearer names
    forecast = forecast.rename(columns={
        "Solar": "fc_solar_mw",
        "Wind Onshore": "fc_wind_onshore_mw"
    })

    # Convert all datasets to the same timezone
    prices = prices.tz_convert(tz)
    gen = gen.tz_convert(tz)
    forecast = forecast.tz_convert(tz)
    flows = flows.tz_convert(tz)

    # Create a unified hourly time index
    idx = pd.date_range(start, end, freq="h", tz=tz, inclusive="left")

    # Align all datasets to the same hourly index
    prices = prices.reindex(idx)
    gen = gen.reindex(idx)
    forecast = forecast.reindex(idx)
    flows = flows.reindex(idx)

    # Combine all datasets into a single DataFrame
    market_df = (
        prices
        .join(gen, how="left")
        .join(forecast, how="left")
        .join(flows, how="left")
    )

    return market_df
