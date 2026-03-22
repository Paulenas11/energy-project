from entsoe import EntsoePandasClient
import pandas as pd
from .config import API_KEY, TIMEZONE, ZONE_LT
from src.entsoe_zones import ZONE_MAP, NEIGHBORS


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


def _resolve_zone(zone: str) -> str:
    """
    Convert human-readable zone code (e.g., 'SE4', 'LT')
    into ENTSO‑E EIC code required by the API.

    Raises:
        KeyError: If zone is unknown.
    """
    if zone not in ZONE_MAP:
        raise KeyError(f"Unknown zone '{zone}'. Not found in ZONE_MAP.")
    return ZONE_MAP[zone]


def get_day_ahead_prices(start, end, zone=ZONE_LT):
    """
    Fetch day‑ahead electricity prices for the specified time range.
    """
    client = get_client()
    start = pd.Timestamp(start, tz=TIMEZONE)
    end = pd.Timestamp(end, tz=TIMEZONE)

    zone_eic = _resolve_zone(zone)
    return client.query_day_ahead_prices(zone_eic, start=start, end=end)


def get_generation(start, end, zone=ZONE_LT):
    """
    Fetch actual generation data (solar, wind, etc.) for the specified time range.
    """
    client = get_client()
    start = pd.Timestamp(start, tz=TIMEZONE)
    end = pd.Timestamp(end, tz=TIMEZONE)

    zone_eic = _resolve_zone(zone)
    return client.query_generation(zone_eic, start=start, end=end)


def get_wind_solar_forecast(start, end, zone=ZONE_LT):
    """
    Fetch wind and solar generation forecasts for the specified time range.
    """
    client = get_client()
    start = pd.Timestamp(start, tz=TIMEZONE)
    end = pd.Timestamp(end, tz=TIMEZONE)

    zone_eic = _resolve_zone(zone)
    return client.query_wind_and_solar_forecast(zone_eic, start=start, end=end)

def _generate_border_pairs(country: str):
    """
    Generate all cross-border flow directions for a given country.
    Example: LT → [(LT, LV), (LV, LT), (LT, PL), (PL, LT), ...]
    """
    if country not in NEIGHBORS:
        raise KeyError(f"No neighbor data for country '{country}'")

    pairs = []
    for neighbor in NEIGHBORS[country]:
        pairs.append((country, neighbor))  # outgoing
        pairs.append((neighbor, country))  # incoming
    return pairs




def get_crossborder_flows(start, end, country="LT", tz="Europe/Vilnius"):
    """
    Fetch cross‑border electricity flows for all neighbors of a given country.
    """

    client = get_client()

    # Convert timestamps to target timezone
    start = pd.Timestamp(start, tz=tz)
    end = pd.Timestamp(end, tz=tz)

    # Dynamically generate all border directions
    borders = _generate_border_pairs(country)

    dfs = []

    for country_from, country_to in borders:
        df = client.query_crossborder_flows(
            country_code_from=country_from,
            country_code_to=country_to,
            start=start,
            end=end
        )

        df = df.to_frame(name=f"flow_{country_from.lower()}_{country_to.lower()}_mw")
        df = df.tz_convert(tz)
        dfs.append(df)

    return pd.concat(dfs, axis=1)

