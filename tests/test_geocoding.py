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

# Test geocoding using a dictionary with some parts of the address missing (country is mandatory)
# This verifies that normalize_address() correctly builds a full address string.
def test_almost_structured_address():
    address = {
       # "street": "Studentų g. 50",
       # "city": "Kaunas",
        "postcode": "51368",
        "country": "Lithuania"
    }
    lat, lon = geocode_address(address)
    print("Almost structured:", lat, lon)


# Test geocoding using an address without field 'country'
# This checks that the function still works even when field 'country' is missing.
def test_address_without_country():
    try:
        geocode_address(
            {
        "street": "Studentų g. 50",
        "city": "Kaunas",
        "postcode": "51368",
    })
    except ValueError as e:
        print("Expected error:", e)
        return
    assert False, "Expected ValueError when 'country' is missing"


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
    test_almost_structured_address()
    test_address_without_country()
    test_invalid_address()
