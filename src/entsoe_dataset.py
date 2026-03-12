import pandas as pd
from src.entsoe_client import (
    get_day_ahead_prices,
    get_generation,
    get_wind_solar_forecast,
    get_crossborder_flows,
)


def normalize_to_hourly(df):
    """
    Convert 15‑min or irregular ENTSO‑E data to hourly resolution.
    If already hourly → return unchanged.
    """
    # Pandas 3.0 uses lowercase "h"
    if df.index.freqstr == "h":
        return df

    return df.resample("h").mean()


def get_entsoe_dataset(zones, start, end):
    """
    High‑level ENTSO‑E dataset builder.

    Parameters:
        zones (str or list[str]): trading zone(s)
        start, end (str): date range

    Returns:
        pandas.DataFrame: unified hourly dataset for all zones
    """

    if isinstance(zones, str):
        zones = [zones]

    all_frames = []

    for zone in zones:
        try:

            prices = get_day_ahead_prices(start, end, zone)
            gen = get_generation(start, end, zone)
            fc = get_wind_solar_forecast(start, end, zone)
            flows = get_crossborder_flows(start, end)


            if isinstance(prices, pd.Series):
                prices = prices.to_frame("price_eur_mwh")
            else:
                prices.columns = [
                    c.lower().replace(" ", "_").replace("-", "_")
                    for c in prices.columns
                ]


            if isinstance(gen.columns, pd.MultiIndex):
                gen.columns = [
                    f"{tech.lower().replace(' ', '_').replace('-', '_')}_"
                    f"{kind.lower().replace(' ', '_')}"
                    for tech, kind in gen.columns
                ]


            gen = gen.add_prefix("gen_")


            fc = fc.rename(columns=lambda c: c.lower().replace(" ", "_"))
            fc = fc.add_prefix("fc_")


            flows = flows.rename(columns=lambda c: c.lower())

            # NORMALIZE TO HOURLY
            prices = normalize_to_hourly(prices)
            gen = normalize_to_hourly(gen)
            fc = normalize_to_hourly(fc)
            flows = normalize_to_hourly(flows)


            idx = pd.date_range(
                start, end, freq="h", tz=prices.index.tz, inclusive="left"
            )


            prices = prices.reindex(idx)
            gen = gen.reindex(idx)
            fc = fc.reindex(idx)
            flows = flows.reindex(idx)


            df = (
                prices
                .join(gen, how="left")
                .join(fc, how="left")
                .join(flows, how="left")
            )

            df["zone"] = zone
            all_frames.append(df)

        except Exception as e:
            print(f"Skipping zone {zone}: {e}")
            continue

    if not all_frames:
        raise ValueError("No ENTSO‑E data available for any zone.")

    return pd.concat(all_frames)
