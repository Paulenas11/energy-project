import requests
import pandas as pd

# PVGIS API endpoint (hourly solar generation model)
PVGIS_URL = "https://re.jrc.ec.europa.eu/api/v5_3/seriescalc"

def auto_tilt_azimuth(lat):
    """
    Automatically determine optimal tilt and azimuth based on latitude.

    Rules:
        - Azimuth always 0° (south-facing)
        - Tilt depends on latitude:
            < 50°  → 35°
            50–60° → 40°
            > 60°  → 45°
    """
    if lat < 50:
        tilt = 35
    elif lat < 60:
        tilt = 40
    else:
        tilt = 45

    azimuth = 0
    return tilt, azimuth


def get_pvgis_hourly(lat, lon, year, peak_power_kw=1.0):
    """
    Fetch hourly modeled solar generation from PVGIS for a given location and year.

    Parameters:
        lat, lon (float): Geographic coordinates.
        year (int): Year for which PVGIS should return modeled data.
        peak_power_kw (float): Installed PV capacity (kW).
        tilt (int): Panel tilt angle in degrees.
        azimuth (int): Panel azimuth (0 = south-facing).

    Returns:
        DataFrame with hourly solar generation in kWh.
    """

    #Auto-select orientation
    tilt, azimuth = auto_tilt_azimuth(lat)

    # Parameters required by PVGIS API
    params = {
        "lat": lat,
        "lon": lon,
        "startyear": year,
        "endyear": year,
        "pvcalculation": 1,       # enable PV performance model
        "peakpower": peak_power_kw,
        "loss": 14,               # default system losses (%)
        "angle": tilt,            # panel tilt
        "aspect": azimuth,        # panel azimuth
        "outputformat": "json",
        "hourly": 1               # request hourly data
    }

    # Send request to PVGIS
    resp = requests.get(PVGIS_URL, params=params)
    resp.raise_for_status()       # raise error if request failed

    # Extract hourly data from JSON response
    data = resp.json()
    hourly = data["outputs"]["hourly"]

    # Convert list of hourly entries into DataFrame
    df = pd.DataFrame(hourly)

    # PVGIS time format example: "20200101:1300"
    # Convert manually into pandas Timestamp with UTC timezone
    def parse_pvgis_time(t):
        date_part, time_part = t.split(":")
        year = date_part[0:4]
        month = date_part[4:6]
        day = date_part[6:8]
        hour = time_part[0:2]
        minute = time_part[2:4]
        return pd.Timestamp(f"{year}-{month}-{day} {hour}:{minute}", tz="UTC")

    # Apply timestamp parsing and set as index
    df["time"] = df["time"].apply(parse_pvgis_time)
    df = df.set_index("time")

    # Rename PVGIS output column "P" → "pvgis_solar_kwh"
    df = df.rename(columns={"P": "pvgis_solar_kwh"})

    # Return only the solar generation column
    return df[["pvgis_solar_kwh"]]
