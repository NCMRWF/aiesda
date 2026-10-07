

import codc
import eccodes

def test_libraries():
    print("--- Testing pyodc (codc) ---")
    try:
        # Check if codc is loaded correctly
        print("Success: `codc` imported and ready for ODB-2 data handling.")
    except Exception as e:
        print(f"Error with codc: {e}")

    print("\n--- Testing ecCodes ---")
    try:
        # Retrieve the ecCodes version information
        version_info = eccodes.codes_get_version_info()
        print("Success: `eccodes` imported successfully!")
        print(f"ecCodes Version Info: {version_info}")
    except Exception as e:
        print(f"ecCodes imported, but encountered an issue fetching version info: {e}")

if __name__ == "__main__":
    test_libraries()
