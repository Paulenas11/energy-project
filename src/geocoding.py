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
        - Flexible dict: only 'country' is required, others are optional

    Returns:
        str: normalized address string
    """
    # Case 1: plain string
    if isinstance(address, str):
        return address

    # Cases 2 and 3: structured dictionary
    if isinstance(address, dict):

        # Country is mandatory
        if "country" not in address or not address["country"]:
            raise ValueError("Address dictionary must include at least 'country'.")

        # Allowed fields in order
        fields = ["street", "city", "postcode", "country"]

        parts = [address.get(f, "") for f in fields]
        parts = [p for p in parts if p]  # remove empty fields

        return ", ".join(parts)

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
