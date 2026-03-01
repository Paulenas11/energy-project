import requests
import pandas as pd
from src.pvgis_client import get_pvgis_hourly

# Nominatim reverse geocoding endpoint
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"


def reverse_geocode(lat, lon):
    """
    Convert coordinates into a human-readable address and country
    using OpenStreetMap Nominatim reverse geocoding.

    Returns:
        dict with keys:
            - country: country name
            - address: full formatted address
    """

    params = {
        "lat": lat,
        "lon": lon,
        "format": "json"
    }

    # Required User-Agent header (Nominatim blocks requests without it)
    headers = {
        "User-Agent": "PauliusEnergyProject/1.0 (pauliuspuidokas10@gmail.com)"
    }

    # Send request to Nominatim
    resp = requests.get(NOMINATIM_REVERSE_URL, params=params, headers=headers)
    resp.raise_for_status()

    data = resp.json()

    # Extract country and full address
    country = data.get("address", {}).get("country", "Unknown")
    address = data.get("display_name", "Unknown")

    return {"country": country, "address": address}


def get_pvgis_dataset(lat, lon, years):
    """
    Fetch PVGIS hourly solar generation for one or multiple years,
    enrich the dataset with metadata (country, address, coordinates),
    and return a combined DataFrame.

    Parameters:
        lat, lon (float): geographic coordinates
        years (int or list[int]): one year or list of years

    Returns:
        DataFrame with columns:
            time, pvgis_solar_kwh, latitude, longitude,
            year, country, address
    """

    # Normalize input: allow both int and list[int]
    if isinstance(years, int):
        years = [years]

    # Reverse geocode once (same for all years)
    meta = reverse_geocode(lat, lon)

    frames = []

    for year in years:
        try:
            # Fetch hourly PVGIS data for the given year
            df = get_pvgis_hourly(lat, lon, year)
        except Exception as e:
            # PVGIS sometimes returns 400 for unavailable years
            print(f"PVGIS error for year {year}: {e}")
            continue

        # Add metadata columns
        df = df.copy()
        df["latitude"] = lat
        df["longitude"] = lon
        df["year"] = year
        df["country"] = meta["country"]
        df["address"] = meta["address"]

        frames.append(df)

    # If no data was collected for any year → fail gracefully
    if not frames:
        raise ValueError("No PVGIS data available for any of the requested years.")

    # Combine all years into one DataFrame
    return pd.concat(frames)


def save_pvgis_csv(lat, lon, years, output_path):
    """
    Fetch PVGIS dataset and save it to a CSV file.

    Parameters:
        lat, lon (float)
        years (int or list[int])
        output_path (str): path to output CSV file

    Returns:
        str: output file path
    """
    df = get_pvgis_dataset(lat, lon, years)
    df.to_csv(output_path)
    return output_path
