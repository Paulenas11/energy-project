import pandas as pd
from src.entsoe_dataset import get_entsoe_dataset, normalize_to_hourly

def test_normalize_to_hourly_hourly_input():
    idx = pd.date_range("2020-01-01", periods=5, freq="h", tz="Europe/Vilnius")
    df = pd.DataFrame({"value": [1, 2, 3, 4, 5]}, index=idx)

    out = normalize_to_hourly(df)
    assert out.index.equals(idx)
    assert out.equals(df)


def test_normalize_to_hourly_quarter_hour_input():
    idx = pd.date_range("2020-01-01", periods=8, freq="15min", tz="Europe/Vilnius")
    df = pd.DataFrame({"value": range(8)}, index=idx)

    out = normalize_to_hourly(df)

    assert len(out) == 2
    assert out.index.freqstr == "h"


def test_entsoe_single_zone():
    df = get_entsoe_dataset("LT", "2020-01-01", "2020-01-03")

    assert isinstance(df, pd.DataFrame)
    assert "price_eur_mwh" in df.columns
    assert "zone" in df.columns
    assert df["zone"].unique().tolist() == ["LT"]
    assert df.index.freqstr == "h"


def test_entsoe_multiple_zones():
    df = get_entsoe_dataset(["LT", "LV"], "2020-01-01", "2020-01-03")

    assert isinstance(df, pd.DataFrame)
    assert "zone" in df.columns

    zones = df["zone"].unique().tolist()
    assert "LT" in zones
    assert "LV" in zones


def test_entsoe_invalid_zone():
    df = get_entsoe_dataset(["LT", "BAD_CODE"], "2020-01-01", "2020-01-03")

    assert "LT" in df["zone"].unique().tolist()
    assert "INVALID_ZONE" not in df["zone"].unique().tolist()


def test_debug_output():
    df = get_entsoe_dataset(["LT", "SE4"], "2020-01-01", "2020-01-05")

    print("\n--- Zones present ---")
    print(df["zone"].unique().tolist())

    # Print head(10) for each zone separately
    for zone in df["zone"].unique():
        print(f"\n--- First 10 rows for zone {zone} ---")
        print(df[df["zone"] == zone].head(10)[["price_eur_mwh"] +
                                              [c for c in df.columns if c.startswith("gen_") or c.startswith("fc_")]])

    print("\n--- Time index ---")
    print("Start:", df.index.min())
    print("End:", df.index.max())


if __name__ == "__main__":
    test_normalize_to_hourly_hourly_input()
    test_normalize_to_hourly_quarter_hour_input()
    test_entsoe_single_zone()
    test_entsoe_multiple_zones()
    test_entsoe_invalid_zone()
    test_debug_output()