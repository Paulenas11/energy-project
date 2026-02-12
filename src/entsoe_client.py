from entsoe import EntsoePandasClient
import pandas as pd
from .config import API_KEY, TIMEZONE, ZONE_LT

# Initialize ENTSO‑E client using API key from config
client = EntsoePandasClient(api_key=API_KEY)

def get_client():
    """
    Create and return a new ENTSO‑E API client instance.

    Raises:
        ValueError: If API_KEY is missing in config.py
    """
    if API_KEY is None:
        raise ValueError("API_KEY not set. Please update config.py")
    return EntsoePandasClient(api_key=API_KEY)

def get_day_ahead_prices(start, end, zone=ZONE_LT):
    """
    Fetch day‑ahead electricity prices for the specified time range.

    Parameters:
        start, end (str): Date range (YYYY-MM-DD)
        zone (str): Bidding zone code (default: Lithuania)

    Returns:
        pandas.Series: Hourly day‑ahead prices
    """
    client = get_client()
    start = pd.Timestamp(start, tz=TIMEZONE)
    end = pd.Timestamp(end, tz=TIMEZONE)
    return client.query_day_ahead_prices(zone, start=start, end=end)

def get_generation(start, end, zone=ZONE_LT):
    """
    Fetch actual generation data (solar, wind, etc.) for the specified time range.

    Parameters:
        start, end (str): Date range (YYYY-MM-DD)
        zone (str): Bidding zone code

    Returns:
        pandas.DataFrame: Generation data with MultiIndex columns
    """
    client = get_client()
    start = pd.Timestamp(start, tz=TIMEZONE)
    end = pd.Timestamp(end, tz=TIMEZONE)
    return client.query_generation(zone, start=start, end=end)

def get_wind_solar_forecast(start, end, zone=ZONE_LT):
    """
    Fetch wind and solar generation forecasts for the specified time range.

    Parameters:
        start, end (str): Date range (YYYY-MM-DD)
        zone (str): Bidding zone code

    Returns:
        pandas.DataFrame: Forecasted solar and wind generation
    """
    client = get_client()
    start = pd.Timestamp(start, tz=TIMEZONE)
    end = pd.Timestamp(end, tz=TIMEZONE)
    return client.query_wind_and_solar_forecast(zone, start=start, end=end)

def get_crossborder_flows(start, end, tz="Europe/Vilnius"):
    """
    Fetch cross‑border electricity flows between Lithuania and neighboring countries.

    Parameters:
        start, end (str): Date range (YYYY-MM-DD)
        tz (str): Target timezone for returned data

    Returns:
        pandas.DataFrame: Hourly flows for all LT border directions
    """

    client = get_client()

    # Convert timestamps to target timezone
    start = pd.Timestamp(start, tz=tz)
    end = pd.Timestamp(end, tz=tz)

    # List of all border directions to query
    borders = [
        ("LT", "LV"),
        ("LV", "LT"),
        ("LT", "PL"),
        ("PL", "LT"),
        ("LT", "SE"),
        ("SE", "LT"),
    ]

    dfs = []

    # Query each border direction separately
    for country_from, country_to in borders:
        df = client.query_crossborder_flows(
            country_code_from=country_from,
            country_code_to=country_to,
            start=start,
            end=end
        )

        # Convert Series → DataFrame and rename column
        df = df.to_frame(name=f"flow_{country_from.lower()}_{country_to.lower()}_mw")

        # Convert timezone to target tz
        df = df.tz_convert(tz)

        dfs.append(df)

    # Combine all border flow columns into a single DataFrame
    flows = pd.concat(dfs, axis=1)
    return flows
