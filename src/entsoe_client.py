import requests
from entsoe import EntsoePandasClient
import pandas as pd
from .config import API_KEY, TIMEZONE, ZONE_LT
from src.entsoe_static import ZONE_MAP, NEIGHBORS, TSO_MAP, TSO_NEIGHBORS
from lxml import etree
from src.cache import cache_load, cache_save


def log(msg):
    """
    Lightweight logging helper for debugging ENTSO‑E client behavior.
    Printed messages appear in test output and notebooks.
    """
    print(f"[CLIENT] {msg}", flush=True)


# Global ENTSO‑E client instance (used only for simple calls)
client = EntsoePandasClient(api_key=API_KEY)

def get_domain_for_date(zone, date):
    """
    Resolve the correct ENTSO‑E domain (EIC code) for a given zone and date.

    Why this is needed:
        - Some bidding zones change their domain codes over time.
        - ZONE_MAP may contain:
            * a single static domain (str)
            * a list of (start, end, domain) tuples for time‑dependent mapping

    Parameters:
        zone (str): Human-readable zone code (e.g., "LT", "SE4")
        date (Timestamp): Timestamp with timezone

    Returns:
        str: EIC domain code
    """
    entry = ZONE_MAP.get(zone)

    if entry is None:
        raise ValueError(f"Unknown zone: {zone}")

    # Remove timezone for comparison
    date_naive = date.tz_localize(None)

    # Static mapping
    if isinstance(entry, str):
        return entry

    # Time-dependent mapping
    for start, end, domain in entry:
        if pd.Timestamp(start) <= date_naive < pd.Timestamp(end):
            return domain

    raise ValueError(f"No domain mapping for zone {zone} at date {date}")


def get_client():
    """
    Create a fresh ENTSO‑E API client instance.

    Why:
        - Some ENTSO‑E calls behave better with a new client per request.
        - Ensures API_KEY is validated before use.
    """
    if API_KEY is None:
        raise ValueError("API_KEY not set. Please update config.py")
    return EntsoePandasClient(api_key=API_KEY)


def _resolve_zone(zone: str) -> str:
    """
    Convert human-readable zone code into ENTSO‑E EIC code.

    Used only for static mappings (not time-dependent).
    """
    if zone not in ZONE_MAP:
        raise KeyError(f"Unknown zone '{zone}'. Not found in ZONE_MAP.")
    return ZONE_MAP[zone]

def get_day_ahead_prices(start, end, zone):
    """
    Fetch day-ahead electricity prices for a given zone and time range.

    Includes:
        - caching (HIT/MISS)
        - timezone normalization
        - domain resolution
    """
    log(f"Prices {zone} {start} → {end}")

    # Try cache first
    cached = cache_load("prices", start, end, zone)
    if cached is not None:
        log("Loaded from cache")
        return cached

    # Fetch from ENTSO‑E
    log("Fetching from ENTSO-E...")
    client = get_client()
    start = pd.Timestamp(start, tz=TIMEZONE)
    end = pd.Timestamp(end, tz=TIMEZONE)

    domain = get_domain_for_date(zone, start)
    df = client.query_day_ahead_prices(domain, start=start, end=end)

    # Save to cache
    cache_save("prices", start, end, zone, df)
    log("Saved to cache")
    return df

def get_generation(start, end, zone=ZONE_LT):
    """
    Fetch actual generation data (solar, wind, etc.) for a zone.

    Notes:
        - MultiIndex columns are handled later in dataset builder.
        - Default zone is LT (useful for notebooks).
    """
    log(f"Generation {zone} {start} → {end}")

    cached = cache_load("generation", start, end, zone)
    if cached is not None:
        log("Loaded from cache")
        return cached

    log("Fetching from ENTSO-E...")
    client = get_client()
    start = pd.Timestamp(start, tz=TIMEZONE)
    end = pd.Timestamp(end, tz=TIMEZONE)

    domain = get_domain_for_date(zone, start)
    df = client.query_generation(domain, start=start, end=end)

    cache_save("generation", start, end, zone, df)
    log("Saved to cache")
    return df

def get_wind_solar_forecast(start, end, zone):
    """
    Fetch wind and solar generation forecast for a zone.

    Returned columns depend on ENTSO‑E availability.
    """
    log(f"Forecast {zone} {start} → {end}")

    cached = cache_load("forecast", start, end, zone)
    if cached is not None:
        log("Loaded from cache")
        return cached

    log("Fetching from ENTSO-E...")
    client = get_client()
    start = pd.Timestamp(start, tz=TIMEZONE)
    end = pd.Timestamp(end, tz=TIMEZONE)

    domain = get_domain_for_date(zone, start)
    df = client.query_wind_and_solar_forecast(domain, start=start, end=end)

    cache_save("forecast", start, end, zone, df)
    log("Saved to cache")
    return df

def _generate_border_pairs(country: str):
    """
    Generate all directional flow pairs for a country.

    Example:
        LT → [(LT, LV), (LV, LT), (LT, PL), (PL, LT)]
    """
    if country not in NEIGHBORS:
        raise KeyError(f"No neighbor data for country '{country}'")

    pairs = []
    for neighbor in NEIGHBORS[country]:
        pairs.append((country, neighbor))  # outgoing
        pairs.append((neighbor, country))  # incoming
    return pairs


def get_physical_flow_pair(start, end, zone_from, zone_to):
    """
    Fetch physical cross-border flow between two TSO domains.

    Uses ENTSO‑E A75 document type (physical flows).
    Parsed manually from XML because the official client does not support A75.
    """
    log(f"Flow {zone_from} → {zone_to} {start} → {end}")

    # Normalize timestamps (A75 requires timezone-naive format)
    start = pd.Timestamp(start).tz_localize(None)
    end = pd.Timestamp(end).tz_localize(None)

    domain_from = TSO_MAP[zone_from]
    domain_to = TSO_MAP[zone_to]

    # Build A75 request URL
    url = (
        "https://web-api.tp.entsoe.eu/api?"
        f"documentType=A75"
        f"&in_Domain={domain_from}"
        f"&out_Domain={domain_to}"
        f"&periodStart={start.strftime('%Y%m%d%H%M')}"
        f"&periodEnd={end.strftime('%Y%m%d%H%M')}"
        f"&securityToken={API_KEY}"
    )

    response = requests.get(url)
    if response.status_code != 200:
        log("No data (status != 200)")
        return pd.DataFrame()

    # Parse XML response
    xml = etree.fromstring(response.content)

    records = []
    for ts in xml.findall(".//TimeSeries"):
        for period in ts.findall(".//Period"):
            start_time = pd.Timestamp(period.findtext("timeInterval/start"))
            for point in period.findall("Point"):
                pos = int(point.findtext("position"))
                qty = float(point.findtext("quantity"))
                timestamp = start_time + pd.Timedelta(hours=pos - 1)
                records.append((timestamp, qty))

    if not records:
        log("No records in XML")
        return pd.DataFrame()

    # Build DataFrame
    df = pd.DataFrame(records, columns=["timestamp", f"flow_{zone_from.lower()}_{zone_to.lower()}_mw"])
    df = df.set_index("timestamp")
    df = df.tz_localize("UTC").tz_convert(TIMEZONE)

    return df

def get_crossborder_flows(start, end, country):
    """
    Fetch all incoming and outgoing physical flows for a country.

    Steps:
        1. Try cache
        2. For each neighbor:
            - fetch country → neighbor
            - fetch neighbor → country
        3. Combine all flow columns
        4. Save to cache
    """
    log(f"Crossborder flows for {country} {start} → {end}")

    cached = cache_load("flows", start, end, country)
    if cached is not None:
        log("Loaded from cache")
        return cached

    log("Fetching flows from ENTSO-E...")
    dfs = []

    for neighbor in TSO_NEIGHBORS.get(country, []):
        # Skip invalid mappings
        if neighbor not in TSO_MAP or country not in TSO_MAP:
            continue

        df1 = get_physical_flow_pair(start, end, country, neighbor)
        df2 = get_physical_flow_pair(start, end, neighbor, country)

        # Normalize Series → DataFrame
        if isinstance(df1, pd.Series):
            df1 = df1.to_frame()
        if isinstance(df2, pd.Series):
            df2 = df2.to_frame()

        # Append only non-empty results
        if not df1.empty:
            dfs.append(df1)
        if not df2.empty:
            dfs.append(df2)

    # No flows found
    if not dfs:
        log("No flows found")
        empty = pd.DataFrame(index=pd.DatetimeIndex([], tz=TIMEZONE))
        cache_save("flows", start, end, country, empty)
        return empty

    # Combine all flow columns
    result = pd.concat(dfs, axis=1)

    cache_save("flows", start, end, country, result)
    log("Saved to cache")
    return result
