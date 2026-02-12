import requests

# Nominatim API endpoint for geocoding
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

def geocode_address(address):
    """
    Convert a human-readable address into geographic coordinates (latitude, longitude)
    using the OpenStreetMap Nominatim API.

    Parameters:
        address (str): Full address or location name to geocode.

    Returns:
        tuple: (latitude, longitude) as floats.
    """

    # Query parameters for Nominatim API
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
    }

    # Required User-Agent header (Nominatim blocks requests without it)
    headers = {
        "User-Agent": "PauliusEnergyProject/1.0 (pauliuspuidokas10@gmail.com)"
    }

    # Send request to Nominatim
    resp = requests.get(NOMINATIM_URL, params=params, headers=headers)
    resp.raise_for_status()  # raise error if request failed

    # Parse JSON response
    data = resp.json()
    if not data:
        raise ValueError(f"No coordinates found for address: {address}")

    # Extract latitude and longitude
    lat = float(data[0]["lat"])
    lon = float(data[0]["lon"])

    return lat, lon
