import os
import sys

# Ensure custom package libraries are imported correctly
CURR_PATH = os.path.dirname(os.path.abspath(__file__))
PKGHOME = os.path.dirname(CURR_PATH)
OBSLIB = os.environ.get("OBSLIB", os.path.join(PKGHOME, "pylib"))
OBSNML = os.environ.get("OBSNML", os.path.join(PKGHOME, "nml"))

if OBSLIB not in sys.path:
    sys.path.append(OBSLIB)

import ecbufr
import obslib
import obsmod
import obscodc
import numpy
import pandas
import pyodc



if __name__ == "__main__":
    PDY = sys.argv[1] if len(sys.argv) > 1 else obsmod.today()
    CYC = sys.argv[2] if len(sys.argv) > 2 else "00"

    bufr_filepath = os.getenv("BUFRFILE")
    odb_filepath = os.getenv("ODB2FILE")

    if not bufr_filepath or not odb_filepath:
        print(
            "Error: Both BUFRFILE and ODB2FILE environment variables must be defined."
        )
        sys.exit(1)

    # 1. Header Inspection (Diagnostic)
    #try:
    #    ecbufr.get_bufr_subtype_elements(bufr_filepath)
    #except Exception as e:
    #    print(f"Inspection note: {e}")

    # 2. Main Execution (BUFR -> ODB Conversion)
    print("insise main script")
    generated_odb = obscodc.convert_bufr_to_odb(
        bufr_filepath=bufr_filepath, odb_filepath=odb_filepath
    )
    exit()
    # 3. Read back generated ODB file for verification
    if generated_odb:
        obscodc.read_and_verify_odb(generated_odb)
