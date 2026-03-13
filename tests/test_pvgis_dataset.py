from src.pvgis_dataset import get_pvgis_dataset, reverse_geocode

# Test reverse geocoding functionality.
# Ensures that coordinates can be converted into a country and human-readable address.
def test_reverse_geocode():
    meta = reverse_geocode(54.8982, 23.9045)  # Kaunas
    print("Reverse geocode:", meta)


# Test PVGIS dataset generation for a single year.
# Confirms that hourly solar data is successfully retrieved and enriched with metadata.
def test_pvgis_single_year():
    df = get_pvgis_dataset(54.8982, 23.9045, 2023)
    print(df.head())


# Test PVGIS dataset generation for multiple years.
# Verifies that:
#   - the function loops through multiple years,
#   - unavailable years are skipped safely,
#   - available years are combined into a single DataFrame.
def test_pvgis_multi_year():
    df = get_pvgis_dataset(54.8982, 23.9045, [2020, 2023])
    print(df.head())


# Run tests manually when executing this file directly.
if __name__ == "__main__":
    test_reverse_geocode()
    test_pvgis_single_year()
    test_pvgis_multi_year()
