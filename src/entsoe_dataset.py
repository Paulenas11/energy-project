import pandas as pd
import time
from src.entsoe_client import (
    get_day_ahead_prices,
    get_generation,
    get_wind_solar_forecast,
    get_crossborder_flows,
)

from src.entsoe_static import ZONE_MAP
from src.cache import cache_load, cache_save


def log(msg):
    """
    Lightweight logging helper for dataset-building progress.
    Ensures logs appear immediately in notebooks and pytest.
    """
    print(f"[DATASET] {msg}", flush=True)

def normalize_to_hourly(df):
    """
    Normalize any ENTSO‑E DataFrame to hourly resolution.

    Why:
        - ENTSO‑E sometimes returns 15‑min or 30‑min data.
        - Dataset requires strictly hourly alignment.
        - Some endpoints return Series instead of DataFrame.

    Steps:
        1. Convert Series → DataFrame
        2. Skip empty or non‑datetime indexed data
        3. If already hourly → return as-is
        4. Otherwise resample to hourly mean
    """
    if isinstance(df, pd.Series):
        df = df.to_frame()

    if df.empty:
        return df

    if not isinstance(df.index, pd.DatetimeIndex):
        return df

    # Already hourly
    if df.index.freqstr == "h":
        return df

    # Convert to hourly mean
    return df.resample("h").mean()

def get_domain_for_date(zone, date):
    """
    Resolve correct ENTSO‑E domain for a given zone and date.

    Used only for dataset-level validation.
    """
    entry = ZONE_MAP.get(zone)

    if entry is None:
        raise ValueError(f"Unknown zone: {zone}")

    if isinstance(entry, str):
        return entry

    for start, end, domain in entry:
        if pd.Timestamp(start) <= date < pd.Timestamp(end):
            return domain

    raise ValueError(f"No domain mapping for zone {zone} at date {date}")

def split_into_year_chunks(start, end):
    """
    Split a long date range into year-sized chunks.

    Why:
        - ENTSO‑E API performs poorly on large multi-year queries.
        - Caching works best when each chunk is independent.
        - Dataset builder can resume from cache chunk-by-chunk.

    Example:
        2015-01-01 → 2026-03-15
        becomes:
            (2015 → 2016)
            (2016 → 2017)
            ...
            (2026 → 2026-03-15)
    """
    start = pd.Timestamp(start)
    end = pd.Timestamp(end)

    chunks = []
    current = start

    while current < end:
        year_end = pd.Timestamp(year=current.year + 1, month=1, day=1)
        chunk_end = min(year_end, end)
        chunks.append((current, chunk_end))
        current = chunk_end

    return chunks

def get_entsoe_dataset(zones, start, end):
    """
    Build a unified hourly dataset for one or multiple bidding zones.

    Features:
        - Year-based chunking for performance
        - Full caching at dataset level (per zone per chunk)
        - Automatic normalization of:
            * prices
            * generation
            * wind/solar forecast
            * cross-border flows
        - Hourly alignment across all data sources
        - Concatenation of all chunks and zones

    Parameters:
        zones (str or list[str]): One or multiple bidding zones
        start, end (str/Timestamp): Time range

    Returns:
        DataFrame: Full hourly dataset with all variables merged
    """
    if isinstance(zones, str):
        zones = [zones]

    log(f"Starting dataset build for zones: {zones}")
    log(f"Period: {start} → {end}")

    all_frames = []
    chunks = split_into_year_chunks(start, end)

    # Process each zone independently
    for zone in zones:
        log(f"\n=== Processing zone {zone} ===")
        zone_frames = []

        # Process each year chunk
        for chunk_start, chunk_end in chunks:
            log(f"  → Chunk {chunk_start} → {chunk_end}")

            # Try dataset-level cache
            cached = cache_load("dataset", chunk_start, chunk_end, zone)
            if cached is not None:
                log("Loaded from cache")
                zone_frames.append(cached)
                continue

            log("Fetching from ENTSO-E API...")
            t0 = time.time()

            try:
                prices = get_day_ahead_prices(chunk_start, chunk_end, zone)
                gen = get_generation(chunk_start, chunk_end, zone)
                fc = get_wind_solar_forecast(chunk_start, chunk_end, zone)
                flows = get_crossborder_flows(chunk_start, chunk_end, zone)

                if isinstance(prices, pd.Series):
                    prices = prices.to_frame("price_eur_mwh")
                else:
                    prices.columns = [
                        c.lower().replace(" ", "_").replace("-", "_")
                        for c in prices.columns
                    ]

                if isinstance(gen, pd.Series):
                    gen = gen.to_frame()

                # Flatten MultiIndex columns
                if isinstance(gen.columns, pd.MultiIndex):
                    gen.columns = [
                        f"{tech.lower().replace(' ', '_').replace('-', '_')}_{kind.lower().replace(' ', '_')}"
                        for tech, kind in gen.columns
                    ]

                gen = gen.add_prefix("gen_")

                if isinstance(fc, pd.Series):
                    fc = fc.to_frame()

                fc.columns = [
                    c.lower().replace(" ", "_").replace("-", "_")
                    for c in fc.columns
                ]

                fc = fc.add_prefix("fc_")

                if isinstance(flows, pd.Series):
                    flows = flows.to_frame()

                prices = normalize_to_hourly(prices)
                gen = normalize_to_hourly(gen)
                fc = normalize_to_hourly(fc)
                flows = normalize_to_hourly(flows)

                idx = pd.date_range(
                    chunk_start, chunk_end,
                    freq="h",
                    tz=prices.index.tz,
                    inclusive="left"
                )

                df = (
                    prices.reindex(idx)
                    .join(gen.reindex(idx), how="left")
                    .join(fc.reindex(idx), how="left")
                    .join(flows.reindex(idx), how="left")
                )

                df["zone"] = zone

                cache_save("dataset", chunk_start, chunk_end, zone, df)

                elapsed = time.time() - t0
                log(f"Completed in {elapsed:.2f} sec")

                zone_frames.append(df)

            except Exception as e:
                log(f"Skipping zone {zone} for {chunk_start}–{chunk_end}: {e}")

        # Combine all chunks for this zone
        if zone_frames:
            all_frames.append(pd.concat(zone_frames))

    # Combine all zones
    return pd.concat(all_frames)
