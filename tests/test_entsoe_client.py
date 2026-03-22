import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from src.entsoe_client import (
    get_client,
    _resolve_zone,
    _generate_border_pairs,
    get_day_ahead_prices,
    get_generation,
    get_wind_solar_forecast,
    get_crossborder_flows,
)
from src.entsoe_zones import ZONE_MAP, NEIGHBORS

def test_get_client_success():
    """
    Ensure that get_client() returns a valid EntsoePandasClient instance.
    This test does not mock anything because the constructor itself is safe.
    """

    client = get_client()
    assert client is not None

def test_resolve_zone_valid():
    """
    _resolve_zone() should return the correct EIC code for a known zone.
    """

    assert _resolve_zone("LT") == ZONE_MAP["LT"]


def test_resolve_zone_invalid():
    """
    _resolve_zone() should raise KeyError for unknown bidding zones.
    """

    with pytest.raises(KeyError):
        _resolve_zone("BAD_ZONE")

def test_generate_border_pairs_lt():
    """
    Ensure that border pair generation for LT matches the expected
    outgoing and incoming directions.
    """

    pairs = _generate_border_pairs("LT")

    expected = {
        ("LT", "LV"), ("LV", "LT"),
        ("LT", "PL"), ("PL", "LT"),
        ("LT", "SE"), ("SE", "LT"),
    }

    assert set(pairs) == expected


def test_generate_border_pairs_invalid():
    """
    _generate_border_pairs() should raise KeyError for countries
    not present in NEIGHBORS.
    """

    with pytest.raises(KeyError):
        _generate_border_pairs("XX")


@patch("src.entsoe_client.get_client")
def test_get_day_ahead_prices(mock_get_client):
    """
    Verify that get_day_ahead_prices():
    - calls the correct EntsoePandasClient method
    - returns a Series with correct length
    """

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    idx = pd.date_range("2020-01-01", periods=24, freq="h", tz="Europe/Vilnius")
    mock_client.query_day_ahead_prices.return_value = pd.Series(range(24), index=idx)

    out = get_day_ahead_prices("2020-01-01", "2020-01-02", zone="LT")

    assert isinstance(out, pd.Series)
    assert len(out) == 24
    mock_client.query_day_ahead_prices.assert_called_once()

@patch("src.entsoe_client.get_client")
def test_get_generation(mock_get_client):
    """
    Verify that get_generation():
    - calls query_generation()
    - returns a DataFrame with expected columns
    """

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    idx = pd.date_range("2020-01-01", periods=24, freq="h", tz="Europe/Vilnius")
    mock_client.query_generation.return_value = pd.DataFrame({"solar": range(24)}, index=idx)

    out = get_generation("2020-01-01", "2020-01-02", zone="LT")

    assert isinstance(out, pd.DataFrame)
    assert "solar" in out.columns
    mock_client.query_generation.assert_called_once()

@patch("src.entsoe_client.get_client")
def test_get_wind_solar_forecast(mock_get_client):
    """
    Verify that get_wind_solar_forecast():
    - calls query_wind_and_solar_forecast()
    - returns a DataFrame with expected forecast columns
    """

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    idx = pd.date_range("2020-01-01", periods=24, freq="h", tz="Europe/Vilnius")
    mock_client.query_wind_and_solar_forecast.return_value = pd.DataFrame(
        {"fc_solar": range(24)}, index=idx
    )

    out = get_wind_solar_forecast("2020-01-01", "2020-01-02", zone="LT")

    assert isinstance(out, pd.DataFrame)
    assert "fc_solar" in out.columns
    mock_client.query_wind_and_solar_forecast.assert_called_once()

@patch("src.entsoe_client.get_client")
def test_get_crossborder_flows(mock_get_client):
    """
    Verify that get_crossborder_flows():
    - generates correct border directions using NEIGHBORS
    - calls query_crossborder_flows() correct number of times
    - returns a DataFrame with correct column names
    - preserves the time index
    """

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    # Fake hourly series
    idx = pd.date_range("2020-01-01", periods=3, freq="h", tz="Europe/Vilnius")
    fake_series = pd.Series([1, 2, 3], index=idx)

    mock_client.query_crossborder_flows.return_value = fake_series

    df = get_crossborder_flows("2020-01-01", "2020-01-02", country="LT")

    # Expected border pairs for LT
    expected_pairs = _generate_border_pairs("LT")

    # Check number of API calls
    assert mock_client.query_crossborder_flows.call_count == len(expected_pairs)

    # Check columns
    expected_columns = [
        f"flow_{a.lower()}_{b.lower()}_mw" for a, b in expected_pairs
    ]
    assert list(df.columns) == expected_columns

    # Check index
    assert df.index.equals(idx)

