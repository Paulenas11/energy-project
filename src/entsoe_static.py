# ENTSO-E static configuration for bidding zones, TSOs and neighbors.
# No imports here – pure data structures.

# -----------------------------
# TSO (Transmission System Operator) EIC codes
# -----------------------------

TSO_MAP = {
    "LT": "10YLT-1000A0001A",
    "LV": "10YLV-1000A0001J",
    "EE": "10Y1001A1001A39I",
    "PL": "10YPL-AREA-----S",
    "DE": "10Y1001A1001A83F",  # DE-LU TSO
    "AT": "10YAT-APG------L",
    "FI": "10YFI-1--------U",
    "SE": "10Y1001A1001A44P",  # Svenska Kraftnät (SE1 TSO code)
    "NO": "10YNO-1--------2",
    "DK": "10YDK-1--------W",
    "NL": "10YNL----------L",
    "BE": "10YBE----------2",
    "FR": "10YFR-RTE------C",
    "CH": "10YCH-SWISSGRIDZ",
    "CZ": "10YCZ-CEPS-----N",
    "SK": "10YSK-SEPS-----K",
    "HU": "10YHU-MAVIR----U",
    "SI": "10YSI-ELES-----O",
    "HR": "10YHR-HEP------M",
    "RS": "10YCS-SERBIATS0",
    "BA": "10YBA-JPCC-----D",
    "ME": "10YME-EPCG-----M",
    "MK": "10YMK-MEPSO----8",
    "BG": "10YCA-BULGARIA-R",
    "RO": "10YRO-TEL------P",
    "GR": "10YGR-HTSO-----Y",
    "ES": "10YES-REE------0",
    "PT": "10YPT-REN------W",
    "IE": "10YIE-1001A00010",
    "NI": "10Y1001A1001A016",
    "GB": "10YGB----------A",
}

# -----------------------------
# Bidding zone EIC codes (ZONE_MAP)
# Includes time-dependent zones where needed (DE, AT, LU)
# -----------------------------

ZONE_MAP = {
    # Baltic countries
    "LT": "10YLT-1001A0008Q",
    "LV": "10YLV-1001A00074",
    "EE": "10Y1001A1001A39I",

    # Nordics – Finland & Sweden bidding zones
    "FI": "10YFI-1--------U",

    "SE1": "10Y1001A1001A44P",
    "SE2": "10Y1001A1001A45N",
    "SE3": "10Y1001A1001A46L",
    "SE4": "10Y1001A1001A47J",

    # Norway bidding zones
    "NO1": "10YNO-1--------2",
    "NO2": "10YNO-2--------T",
    "NO3": "10YNO-3--------J",
    "NO4": "10YNO-4--------9",
    "NO5": "10Y1001A1001A48H",

    # Denmark bidding zones
    "DK1": "10YDK-1--------W",
    "DK2": "10YDK-2--------M",

    # Central Europe – time-dependent Germany, Austria, Luxembourg
    "DE": [
        ("2015-01-01", "2018-10-01", "10Y1001A1001A63L"),  # DE-AT-LU joint zone
        ("2018-10-01", "9999-12-31", "10Y1001A1001A83F"),  # DE-LU
    ],

    "AT": [
        ("2015-01-01", "2018-10-01", "10Y1001A1001A63L"),  # DE-AT-LU
        ("2018-10-01", "9999-12-31", "10YAT-APG------L"),  # AT
    ],

    "LU": [
        ("2015-01-01", "2018-10-01", "10Y1001A1001A63L"),  # DE-AT-LU
        ("2018-10-01", "9999-12-31", "10YLU-CEGEDEL-NQ"),  # LU
    ],

    # Other Central European bidding zones
    "NL": "10YNL----------L",
    "BE": "10YBE----------2",
    "FR": "10YFR-RTE------C",
    "CH": "10YCH-SWISSGRIDZ",
    "PL": "10YPL-AREA-----S",
    "CZ": "10YCZ-CEPS-----N",
    "SK": "10YSK-SEPS-----K",
    "HU": "10YHU-MAVIR----U",
    "SI": "10YSI-ELES-----O",

    # Balkans
    "HR": "10YHR-HEP------M",
    "RS": "10YCS-SERBIATS0",
    "BA": "10YBA-JPCC-----D",
    "ME": "10YME-EPCG-----M",
    "MK": "10YMK-MEPSO----8",
    "BG": "10YCA-BULGARIA-R",
    "RO": "10YRO-TEL------P",
    "GR": "10YGR-HTSO-----Y",

    # Iberia
    "ES": "10YES-REE------0",
    "PT": "10YPT-REN------W",

    # Italy bidding zones
    "IT-NORD": "10Y1001A1001A73I",
    "IT-CNOR": "10Y1001A1001A70O",
    "IT-CSUD": "10Y1001A1001A71M",
    "IT-SUD":  "10Y1001A1001A788",
    "IT-FOGN": "10Y1001A1001A72K",
    "IT-PRGP": "10Y1001A1001A76E",
    "IT-SARD": "10Y1001A1001A74G",
    "IT-SICI": "10Y1001A1001A75C",

    # British Isles
    "IE": "10YIE-1001A00010",
    "NI": "10Y1001A1001A016",
    "GB": "10YGB----------A",

    # Iceland (not in ENTSO-E, but kept as placeholder)
    "IS": "IS-ICELAND-NONENTSOE",
}

# -----------------------------
# Bidding zone neighbors (physical interconnections)
# This is at bidding-zone level, not just country level.
# -----------------------------

NEIGHBORS = {
    # Baltics & Nordics
    "LT": ["LV", "PL", "SE4"],
    "LV": ["LT", "EE"],
    "EE": ["LV", "FI"],
    "FI": ["EE", "SE1"],
    "SE1": ["FI", "NO4", "SE2"],
    "SE2": ["SE1", "SE3", "NO4", "NO3"],
    "SE3": ["SE2", "SE4", "NO1", "NO2", "DK1"],
    "SE4": ["SE3", "DK2", "LT", "PL"],
    "NO1": ["SE3", "NO2", "DK1"],
    "NO2": ["NO1", "NO5", "DK1", "NL", "DE"],
    "NO3": ["SE2", "NO4"],
    "NO4": ["SE1", "SE2", "NO3"],
    "NO5": ["NO2"],
    "DK1": ["SE3", "NO1", "DE", "NL"],
    "DK2": ["SE4", "DE"],

    # Central Europe core
    "DE": ["DK1", "DK2", "NL", "BE", "FR", "CH", "AT", "CZ", "PL"],
    "AT": ["DE", "CZ", "SK", "HU", "SI", "CH", "IT-NORD"],
    "LU": ["DE", "BE", "FR"],

    "NL": ["DE", "BE", "GB", "DK1"],
    "BE": ["NL", "FR", "DE", "GB"],
    "FR": ["BE", "DE", "CH", "ES", "GB", "IT-NORD"],
    "CH": ["FR", "DE", "AT", "IT-NORD"],

    "PL": ["DE", "CZ", "SK", "LT", "SE4"],
    "CZ": ["DE", "PL", "SK", "AT"],
    "SK": ["CZ", "PL", "HU", "AT"],
    "HU": ["SK", "RO", "RS", "HR", "SI", "AT"],
    "SI": ["AT", "HU", "HR", "IT-NORD"],
    "HR": ["SI", "HU", "RS", "BA"],
    "RS": ["HU", "RO", "BG", "MK", "BA", "ME"],
    "BA": ["HR", "RS", "ME"],
    "ME": ["BA", "RS"],
    "MK": ["RS", "BG", "GR"],
    "RO": ["HU", "RS", "BG"],
    "BG": ["RO", "RS", "MK", "GR"],
    "GR": ["BG", "MK"],

    # Iberia
    "ES": ["FR", "PT"],
    "PT": ["ES"],

    # Italy zones
    "IT-NORD": ["FR", "CH", "AT", "SI", "IT-CNOR"],
    "IT-CNOR": ["IT-NORD", "IT-CSUD"],
    "IT-CSUD": ["IT-CNOR", "IT-SUD", "IT-PRGP", "IT-FOGN"],
    "IT-SUD": ["IT-CSUD", "IT-SICI"],
    "IT-FOGN": ["IT-CSUD"],
    "IT-PRGP": ["IT-CSUD"],
    "IT-SARD": ["IT-CNOR", "IT-SICI"],
    "IT-SICI": ["IT-SUD", "IT-SARD"],

    # British Isles
    "GB": ["FR", "NL", "BE", "IE", "NI"],
    "IE": ["GB"],
    "NI": ["GB"],

    # Standalone / no ENTSO-E neighbors in this graph
    "IS": [],
}

# -----------------------------
# Optional: TSO-level neighbors (if ever needed)
# -----------------------------

TSO_NEIGHBORS = {
    "LT": ["LV", "PL"],
    "LV": ["LT", "EE"],
    "EE": ["LV", "FI"],
    "FI": ["EE", "SE"],
    "SE": ["FI", "NO", "DK"],
    "NO": ["SE", "DK"],
    "DK": ["SE", "NO", "DE"],
    "DE": ["DK", "NL", "BE", "FR", "CH", "AT", "CZ", "PL"],
    "PL": ["DE", "CZ", "SK", "LT"],
    "CZ": ["DE", "PL", "SK", "AT"],
    "SK": ["CZ", "PL", "HU", "AT"],
    "AT": ["DE", "CZ", "SK", "HU", "SI", "CH"],
    "HU": ["SK", "RO", "RS", "HR", "SI", "AT"],
    "SI": ["AT", "HU", "HR", "IT-NORD"],
    "HR": ["SI", "HU", "RS", "BA"],
    "RS": ["HU", "RO", "BG", "MK", "BA", "ME"],
    "RO": ["HU", "RS", "BG"],
    "BG": ["RO", "RS", "MK", "GR"],
    "GR": ["BG", "MK"],
    "CH": ["FR", "DE", "AT", "IT-NORD"],
    "FR": ["BE", "DE", "CH", "ES", "GB"],
    "BE": ["NL", "FR", "DE"],
    "NL": ["DE", "BE", "GB"],
    "ES": ["FR", "PT"],
    "PT": ["ES"],
    "GB": ["FR", "NL", "IE", "NI"],
    "IE": ["GB"],
    "NI": ["GB"],
}
