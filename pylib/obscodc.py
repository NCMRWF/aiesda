
import subprocess
import sys
import os

CURR_PATH = os.path.dirname(os.path.abspath(__file__))
PKGHOME = os.path.dirname(CURR_PATH)

OBSLIBDIR = os.environ.get("OBSLIBDIR", os.path.join(PKGHOME, "pylib"))
OBSDICDIR = os.environ.get("OBSDICDIR", os.path.join(PKGHOME, "pydic"))
OBSNMLDIR = os.environ.get("OBSNMLDIR", os.path.join(PKGHOME, "nml"))

for path in (OBSLIBDIR, OBSDICDIR, OBSNMLDIR):
    if path not in sys.path:
        sys.path.append(path)

obs_index_nml=OBSNMLDIR+"/obs_index_nml"
odb_index_nml=OBSNMLDIR+"/odb_index_nml"
varobs_nml=OBSNMLDIR+"/varobs_nml"
varcx_surf_nml=OBSNMLDIR+"/varcx_surf_nml"
varcx_uair_nml=OBSNMLDIR+"/varcx_uair_nml"
ecbufr_nml = os.environ.get("ECBUFRNML", os.path.join(OBSNMLDIR,"ecbufr_fieldname.nml"))

import wmocode
import pandas
import eccodes
import sqlodb
import codc
import pyodc
import ecbufr
import obsmod
import obslib
import numpy

ODB_MISSING_INT = numpy.iinfo(numpy.int32).min + 1  # -2147483647

def diag_hasnans(df):
    # --- Diagnostic snippet to find columns causing hasnans ---
    print("--- DIAGNOSTIC: Checking columns for NaNs and types ---")
    types=parse_fieldname_nml()
    print(df)
    for col in df.columns:
        has_nan = df[col].isnull().any()
        col_dtype = df[col].dtype
        assigned_type = types.get(col, "Not in types dict")
        if has_nan:
            print(f"COLUMN WITH NaNs -> Name: {col!r}, Pandas Dtype: {col_dtype}, Assigned ODB Type: {assigned_type}")
    print("-------------------------------------------------------")


def parse_fieldname_nml(nml_path=ecbufr_nml):
    """Parses ecbufr_fieldname.nml to build a column-to-type map.

    Maps 'rValues'/'rVal' -> 'float' and 'iValues'/'iVal' -> 'integer'.
    """
    type_map = {}
    if not nml_path or not os.path.exists(nml_path):
        return type_map
    with open(nml_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines or comments
            if not line or line.startswith('!') or line.startswith('#'):
                continue
            parts = line.split()
            # Lines follow: <index> <bufr_key> <odb_fieldname> <codec_type>
            if len(parts) >= 4:
                field_name = parts[2].strip()
                codec_type = parts[3].strip().lower()
                if codec_type in ['rvalues', 'rval']:
                    type_map[field_name] = 'float'
                elif codec_type in ['ivalues', 'ival']:
                    type_map[field_name] = 'integer'
    type_map["subtype"] = 'integer'
    return type_map

def dfhasnansclean(df):
    types=parse_fieldname_nml()
    types_clean = {}
    if types and isinstance(types, dict):
        types_lower = {str(k).lower(): str(v).lower() for k, v in types.items()}
        for col in df.columns:
            col_lower = str(col).lower()
            if col_lower in types_lower:
                raw_t = types_lower[col_lower]
                if raw_t in ['float', 'real', 'double', 'rvalues', 'rval']:
                    types_clean[col] = 'double'
                elif raw_t in ['integer', 'int', 'ivalues', 'ival']:
                    types_clean[col] = 'integer'
                else:
                    types_clean[col] = raw_t

  # Ensure supplementary columns like subtype are mapped explicitly
        if 'subtype' in df.columns:
            types_clean['subtype'] = 'integer'

        types = types_clean

  # 2. DataFrame pre-encoding cleaning loop
    for col in df.columns:
        col_type = types.get(col, None)

    # Integer handling: replace NaNs with ODB missing indicator and cast to int64 numpy array
        if col_type == 'integer' or numpy.issubdtype(df[col].dtype, numpy.integer):
            df[col] = (
                df[col].fillna(ODB_MISSING_INT).to_numpy(dtype=numpy.int64, copy=False)
            )

    # Double/Float handling: ensure standard float64 array with numpy nan
        elif col_type == 'double' or numpy.issubdtype(df[col].dtype, numpy.floating):
            df[col] = df[col].to_numpy(dtype=numpy.float64, copy=False)

    # String/Object handling: catch mixed types or fill strings
        else:
            if df[col].isnull().any():
                try:
                    df[col] = pandas.to_numeric(df[col], errors='raise').to_numpy(
                        dtype=numpy.float64, copy=False
                    )
                except (ValueError, TypeError):
                    df[col] = df[col].fillna('').astype(str)
            else:
                try:
                    df[col] = pandas.to_numeric(df[col], errors='raise')
                except (ValueError, TypeError):
                    df[col] = df[col].astype(str)
    return df

def dfclean(df, types=None, nml_path=ecbufr_nml):
    schema_type_map=parse_fieldname_nml(nml_path)
    print(schema_type_map)

    # Always guarantee critical metadata and integer columns are defined properly
    standard_ints = {
        'subtype', 'year', 'month', 'day', 'hour', 'minute',
        'stationnumber', 'blocknumber', 'typicalyear', 'typicalmonth',
        'typicalday', 'typicalhour', 'typicalminute', 'cloudamount',
        'pastweather1', 'presentweather', 'winddirection', 'relativehumidity'
    }

    for col in df.columns:
        # Declare col_schema_type safely at top of loop
        col_schema_type = schema_type_map.get(col)
        # Determine type from types dictionary if provided
        col_type = schema_type_map.get(col)
        print(col,col_type,col_schema_type)                                                                                                                                                                       
        #Used right here as an immediate override check
        if col_lower in standard_ints:
            cleaned_types[col] = 'integer'
            df[col] = (
                pandas.to_numeric(df[col], errors='coerce')
                .fillna(ODB_MISSING_INT)
                .to_numpy(dtype=numpy.int64, copy=False)
            )
            continue

        # 1. Integer Columns
        if col_type in ['integer', 'int', 'int32', 'int64', 'ivalues', 'ival'] or numpy.issubdtype(df[col].dtype, numpy.integer):
            arr = (
                pandas.to_numeric(df[col], errors='coerce')
                .fillna(ODB_MISSING_INT)
                .to_numpy(dtype=numpy.int64, copy=False)
            )
            df[col] = pandas.Series(arr, index=df.index, dtype=numpy.int64)

        # 2. Float / Double / Real Columns
        elif str(col_type).lower() in ['float', 'double', 'real', 'float32', 'float64', 'rvalues', 'rval'] or numpy.issubdtype(df[col].dtype, numpy.floating):
            arr = (
                pandas.to_numeric(df[col], errors='coerce')
                .to_numpy(dtype=numpy.float64, copy=False)
            )
            df[col] = pandas.Series(arr, index=df.index, dtype=numpy.float64)

        # 3. Target Schema is String -> Convert to float64 to prevent len() codec crashes
        elif str(col_schema_type).lower() in ['string', 'str']:
            arr = (
                pandas.to_numeric(df[col], errors='coerce')
                .to_numpy(dtype=numpy.float64, copy=False)
            )
            df[col] = pandas.Series(arr, index=df.index, dtype=numpy.float64)

        # 4. Dynamic Fallback based on Column Data
        else:
            if numpy.issubdtype(df[col].dtype, numpy.integer):
                arr = (
                    pandas.to_numeric(df[col], errors='coerce')
                    .fillna(ODB_MISSING_INT)
                    .to_numpy(dtype=numpy.int64, copy=False)
                )
                df[col] = pandas.Series(arr, index=df.index, dtype=numpy.int64)
            else:
                arr = (
                    pandas.to_numeric(df[col], errors='coerce')
                    .to_numpy(dtype=numpy.float64, copy=False)
                )
                df[col] = pandas.Series(arr, index=df.index, dtype=numpy.float64)

    print(df)
    return df, cleaned_types


def read_odb2pandas(odb_filepath=None):
    # Read file paths from environment variables
    if not odb_filepath:
        odb_filepath = os.getenv("ODB2FILE")
    print("Reading ODB file"+odb_filepath)

    frames = list(codc.read_odb(odb_filepath))
    df = pandas.concat(frames, ignore_index=True)
    print(df)


def read_odb2(odb_filepath=None):
    # Read file paths from environment variables
    if not odb_filepath:
        odb_filepath = os.getenv("ODB2FILE")
    print("Reading ODB file"+odb_filepath)
    # Read the ODB file
    df = codc.read_odb(odb_filepath, single=True)
    print(df)

def odbquery(odb_filepath=None,varnolist=None):
    # Read file paths from environment variables
    if not odb_filepath:
        odb_filepath = os.getenv("ODB2FILE")
    print("Reading ODB file"+odb_filepath)
    # Read the ODB file
    print(varnolist)
    df = sqlodb.query(odb_filepath,varnolist=varnolist)
    print(df)


def read_and_verify_odb(odb_filepath):
    """Reads ODB file directly into DataFrame for verification."""
    if os.path.exists(odb_filepath):
        print(f"\n--- Reading and Verifying ODB File: {odb_filepath} ---")
        # Pass single=True to read directly into a DataFrame
        df = pyodc.read_odb(odb_filepath, single=True)
        print(df)
        return df
    else:
        print(f"File not found: {odb_filepath}")
        return None


def convert_bufr_to_odb(
    bufr_filepath, odb_filepath, nmlfile=None, obsname="surface", subtype=None
):
    print("inside main function call")
    """Converts BUFR surface observations to ODB format using ecCodes and pyodc."""
    if nmlfile is None:
        nmlfile = os.environ.get(
            "KEYNMLFILE", os.path.join(OBSNMLDIR, f"keys_{obsname}.nml")
        )

    print(f"Reading BUFR file: {bufr_filepath}")
    print(f"Using Namelist: {nmlfile}")

    bufr_dir = os.path.dirname(bufr_filepath)
    bufr_pattern = os.path.basename(bufr_filepath)
    tnode = obsmod.pydate(obsmod.today())
    # Before calling obsmod.py -> ecbufr_decode_files()
    if subtype is None:
    # 1. Read sequence descriptor from BUFR (e.g. [307080])
        #ecbufr_fldlst = ecbufr.get_bufr_descriptors(bufr_filepath,obsname=obsname)
        ecbufr_fldlst=None
    # Decode BUFR observations using standard decoding engine
    print("library function call")
    decoded_data = obsmod.ecbufr_decode_files(
        bufr_dir, tnode, bufr_pattern, nmlfile, keyfieldlst=ecbufr_fldlst
    )

    if decoded_data is None or (
        isinstance(decoded_data, pandas.DataFrame) and decoded_data.empty
    ):
        print(f"Warning: No valid records decoded from {bufr_filepath}.")
        return None

    df = (
        decoded_data
        if isinstance(decoded_data, pandas.DataFrame)
        else pandas.DataFrame(decoded_data)
    )

    # Clean up directory and ensure target output exists
    outdir = os.path.dirname(odb_filepath)
    if outdir and not os.path.exists(outdir):
        os.makedirs(outdir, exist_ok=True)

    # 1. Clean the DataFrame first
    df = dfhasnansclean(df)
    print(df)
    diag_hasnans(df)

    # 2. Build the `types` dictionary AFTER cleaning, based on the final cleaned dtypes
    types = {}
    for col in df.columns:
        if pandas.api.types.is_integer_dtype(df[col]):
            types[col] = pyodc.INTEGER
        elif pandas.api.types.is_float_dtype(df[col]):
            types[col] = pyodc.REAL
        else:
            types[col] = pyodc.STRING

    print(types)

    # 3. Encode with the synchronized types dictionary
    with open(odb_filepath, "wb") as f:
        pyodc.encode_odb(df, f, types=types)
        print(odb_filepath)

    print(f"ODB creation completed: {odb_filepath}")
    return odb_filepath


"""

"""


