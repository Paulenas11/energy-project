import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

NOMINATIM_HEADERS = {
    "User-Agent": "PauliusEnergyProject/1.0 (pauliuspuidokas10@gmail.com)"
}

ADDRESS_FIELDS = ["street", "city", "postcode", "country"]


def normalize_address(address):
    """
    Normalize different address formats into a single text string.

    Supports:
        - plain text address (str)
        - structured address (dict) with optional keys:
            street, city, postcode, country

    Returns:
        str: normalized address string
    """
    # If address is already a string, return as-is
    if isinstance(address, str):
        return address

    # If structured dict, join available fields into a single string
    if isinstance(address, dict):
        parts = [address.get(field, "") for field in ADDRESS_FIELDS]
        return ", ".join([p for p in parts if p])

    raise TypeError("Address must be a string or a dict.")


def geocode_address(address):
    """
    Convert a human-readable address into geographic coordinates (latitude, longitude)
    using the OpenStreetMap Nominatim API.

    Parameters:
        address (str or dict): Full address as text, or structured address as a dictionary.

    Returns:
        tuple: (latitude, longitude) as floats.
    """

    # Normalize input so both string and dict formats are supported
    address = normalize_address(address)

    # Query parameters for Nominatim API
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
    }

    # Send request to Nominatim
    resp = requests.get(NOMINATIM_URL, params=params, headers=NOMINATIM_HEADERS)
    resp.raise_for_status()  # raise error if request failed

    # Parse JSON response
    data = resp.json()
    if not data:
        raise ValueError(f"No coordinates found for address: {address}")

    # Extract latitude and longitude
    lat = float(data[0]["lat"])
    lon = float(data[0]["lon"])

    return lat, lon
