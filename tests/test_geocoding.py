from src.geocoding import geocode_address

# Test geocoding using a plain text address.
# This verifies that the function works with simple string input.
def test_plain_text_address():
    lat, lon = geocode_address("Kaunas, Lithuania")
    print("Plain text:", lat, lon)


# Test geocoding using a structured dictionary address.
# This verifies that normalize_address() correctly builds a full address string.
def test_structured_address():
    address = {
        "street": "Studentų g. 50",
        "city": "Kaunas",
        "postcode": "51368",
        "country": "Lithuania"
    }
    lat, lon = geocode_address(address)
    print("Structured:", lat, lon)


# Test geocoding using a partial address (only city).
# This checks that the function still works even when some fields are missing.
def test_partial_address():
    lat, lon = geocode_address({"city": "Vilnius"})
    print("Partial:", lat, lon)


# Test behavior when the address does NOT exist.
# The function should raise ValueError, proving that error handling works correctly.
def test_invalid_address():
    try:
        geocode_address("hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh")  # clearly invalid
    except ValueError as e:
        print(e)  # Expected output: "No coordinates found for address: ..."
        return

    # If no exception was raised, the test should fail.
    assert False, "Expected ValueError for invalid address"


# Run all tests when executing this file directly.
if __name__ == "__main__":
    test_plain_text_address()
    test_structured_address()
    test_partial_address()
    test_invalid_address()
