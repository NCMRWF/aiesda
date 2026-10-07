
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

import wmocode
import pandas
import eccodes
import sqlodb
import codc
import pyodc
import ecbufr
import obsmod
import obslib




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

    # Encode Pandas DataFrame into ODB using pyodc
    print(f"Writing ODB file: {odb_filepath}")
    types = {}
    for col in df.columns:
        if pandas.api.types.is_integer_dtype(df[col]):
            types[col] = pyodc.INTEGER
        elif pandas.api.types.is_float_dtype(df[col]):
            types[col] = pyodc.REAL
        else:
            types[col] = pyodc.STRING

    with open(odb_filepath, "wb") as f:
        pyodc.encode_odb(df, f, types=types)

    print(f"ODB creation completed: {odb_filepath}")
    return odb_filepath


"""        
def convert_bufr_to_odb(
    bufr_filepath,
    odb_filepath,
    nmlfile=None,
    obsname="surface",
    eleindxmaptbl=None,
    PDY=None,
    CYC=None,
):

    if PDY is None:
        PDY = obsmod.today()

    if CYC is None:
        CYC = "00"

    bufr_filepath=None
    odb_filepath=None
    if not bufr_filepath:
        bufr_filepath = os.getenv("BUFRFILE")
    if not odb_filepath:
        odb_filepath = os.getenv("ODB2FILE")
    ecbufr.get_bufr_subtype_elements(bufr_filepath)
    exit

    #obscodc.convert_bufr_to_odb(bufr_filepath=bufr_filepath, odb_filepath=odb_filepath)

    odbquery(odbfile,varnolist=varnolist)
    #copied from python odb2read.py

    #Decodes a BUFR file using obsmod.ecbufr_decode_files and encodes the
    #resulting dataset into an ODB file via pyodc.

    # 1. Resolve Namelist and Map Table Paths
    if nmlfile is None:
        nmlfile = os.environ.get(
            "KEYNMLFILE", os.path.join(OBSNML, f"keys_{obsname}.nml")
        )

    if eleindxmaptbl is None:
        eleindxmaptbl = os.environ.get(
            "ECBUFRNML", os.path.join(OBSNML, "ecbufr_fieldname.nml")
        )

    # Resolve literal PKGHOME strings if present
    eleindxmaptbl = eleindxmaptbl.replace("PKGHOME", PKGHOME)
    nmlfile = nmlfile.replace("PKGHOME", PKGHOME)

    print(f"Reading BUFR file: {bufr_filepath}")
    print(f"Using Namelist: {nmlfile}")

    # 2. Extract folder and file pattern for ecbufr_decode_files
    bufr_dir = os.path.dirname(bufr_filepath)
    bufr_pattern = os.path.basename(bufr_filepath)
    tnode = obsmod.pydate(obsmod.today())

    obsname=os.environ.get('obsname', "${obsname}")
    cntmax=int(os.environ.get('OBS_CNT_MAX', 500000))
    btchcnt=int(os.environ.get('BTCH_CNT_MAX',5))
    TDATE=os.environ.get('PDY',PDY)
    print(TDATE)
    Tnode=obsmod.pydate(TDATE)
    datacfldrname=obsmod.cylcdate(Tnode)
    outpath=os.environ.get('WRK_OBSTORE',"/scratch/"+USER+"/obstore/work/"+obsname+"/"+PDY+"/"+CYC+"/workdir_obstore")
    inpath=os.environ.get('BUFRDIR',"")
    slctstr=os.environ.get('BUFRFILESTR',"")
    nmlfile=os.environ.get('KEYNMLFILE',OBSNML+"/keys_"+obsname+".nml")
    eleindxmaptbl=os.environ.get('ELEINDXMAPTBL',OBSNML+"/aapp_fieldname.nml")



    # 3. Decode BUFR data using existing decoding engine
    decoded_data=obsmod.ecbufr_decode_files(inpath,Tnode,slctstr,nmlfile,subtype=subtype,eleindxmaptbl=eleindxmaptbl)
    obsmod.ascii_file_write(data,outfile=outpath+"/data_"+obsname+".txt",option=1)
    outfile=obsmod.obstore_write(data,nmlfile,outpath,btchcnt=btchcnt,cntmax=cntmax,DT=Tnode,diagflag=0)

    #decoded_data = obsmod.ecbufr_decode_files(bufr_dir, tnode, bufr_pattern, nmlfile)

    if decoded_data is None or (
        isinstance(decoded_data, pandas.DataFrame) and decoded_data.empty
    ):
        print(
            f"Warning: No valid records decoded from {bufr_filepath}. Skipping ODB output."
        )
        return None

    # Ensure output is a pandas DataFrame
    if not isinstance(decoded_data, pandas.DataFrame):
        df = pandas.DataFrame(decoded_data)
    else:
        df = decoded_data

    # 4. Map columns to ODB naming convention (if opsname mapping exists)
    try:
        odb_name_lookup = obsmod.getodbname(
            nmlfile=nmlfile, opsname=obsname
        )  # or map columns
    except Exception:
        pass

    # Ensure directory exists
    outdir = os.path.dirname(odb_filepath)
    if outdir and not os.path.exists(outdir):
        os.makedirs(outdir, exist_ok=True)

    # 5. Write DataFrame directly to ODB format using pyodc
    print(f"Writing ODB file: {odb_filepath}")

    # Prepare data dictionary and type map for pyodc.encode_odb
    types = {}
    for col in df.columns:
        if pandas.api.types.is_integer_dtype(df[col]):
            types[col] = pyodc.INTEGER
        elif pandas.api.types.is_float_dtype(df[col]):
            types[col] = pyodc.REAL
        else:
            types[col] = pyodc.STRING

    # Encode pandas DataFrame into ODB file
    with open(odb_filepath, "wb") as f:
        pyodc.encode_odb(df, f, types=types)

    print(f"ODB creation completed: {odb_filepath}")
    return odb_filepath
"""

"""
def convert_bufr_to_odb(bufr_filepath, odb_filepath, nmlfile=None, subtype=None, eleindxmaptbl=None):
    if eleindxmaptbl is None:
        eleindxmaptbl = os.environ.get('ECBUFRNML', "PKGHOME/nml/ecbufr_fieldname.nml")

    print(f"Reading BUFR file: {bufr_filepath}")
    
    # 1. Dynamically generate the field list using ecbufr module
    fieldlist = ecbufr.get_ecbufr_fieldlist(
        nmlfile=nmlfile, 
        eleindxmaptbl=eleindxmaptbl, 
        subtyp=subtype
    )
    
    records = []
    
    with open(bufr_filepath, 'rb') as f:
        while True:
            bufr_id = eccodes.codes_bufr_new_from_file(f)
            if bufr_id is None:
                break

            try:
                # Unpack the BUFR message data
                eccodes.codes_set(bufr_id, 'unpack', 1)

                # Use ecbufr's message reading logic to extract the dataframe based on the fieldlist
                df_msg = ecbufr.message_read(bufr_id, fieldlist=fieldlist, eleindxmaptbl=eleindxmaptbl)
                
                if df_msg.empty:
                    continue

                # Dynamically extract varno and ops_subtype metadata keys
                try:
                    varno_val = eccodes.codes_get(bufr_id, 'varno')
                except Exception:
                    try:
                        varno_val = eccodes.codes_get(bufr_id, 'localVarno')
                    except Exception:
                        varno_val = 0

                try:
                    subtype_val = eccodes.codes_get(bufr_id, 'subtype')
                except Exception:
                    try:
                        subtype_val = eccodes.codes_get(bufr_id, 'dataSubtype')
                    except Exception:
                        subtype_val = subtype if subtype is not None else 0

                # Map extracted columns to include necessary ODB scopes (e.g., @hdr, @body)
                # Rename or map columns to align with your odb_index_nml schema definitions
                rename_map = {}
                if 'latitude' in df_msg.columns:
                    rename_map['latitude'] = 'lat@hdr'
                if 'longitude' in df_msg.columns:
                    rename_map['longitude'] = 'lon@hdr'
                
                df_msg = df_msg.rename(columns=rename_map)
                
                # Add mandatory compatibility/metadata columns if missing
                if 'varno' not in df_msg.columns:
                    df_msg['varno'] = varno_val
                if 'ops_subtype' not in df_msg.columns:
                    df_msg['ops_subtype'] = subtype_val

                records.append(df_msg)

            except Exception as e:
                print(f"Error processing a BUFR message: {e}")
            finally:
                eccodes.codes_release(bufr_id)

    # --- Combine and write ODB-2 file once ---
    if not records:
        print("No records extracted from the BUFR file.")
    else:
        final_df = pandas.concat(records, ignore_index=True)
        print(final_df.head())
        print(f"Extracted {len(final_df)} rows. Writing to ODB-2: {odb_filepath}")
        
        with open(odb_filepath, 'wb') as out_f:
            pyodc.encode_odb(out_f, final_df)
            
        print("Successfully completed conversion.")
"""

"""
###############################################################################################
def convert_bufr_to_odb(bufr_filepath=None, odb_filepath=None):
    print(dir(codc))
    # Read file paths from environment variables
    
    # Validate that the environment variables are set
    if not bufr_filepath or not odb_filepath:
        print("Error: BUFRFILE and/or ODB2FILE environment variables are not set.")
        return

    records = []  # Ensure records list is initialized before the loop

    with open(bufr_filepath, 'rb') as f:
        while True:
            bufr_id = eccodes.codes_bufr_new_from_file(f)
            if bufr_id is None:
                break

            try:
                # Unpack the BUFR message data
                eccodes.codes_set(bufr_id, 'unpack', 1)

                # Extract common coordinate/header keys
                lat = eccodes.codes_get(bufr_id, 'latitude')
                lon = eccodes.codes_get(bufr_id, 'longitude')

                # Note: If varno or subtype can be extracted from BUFR keys, fetch them here.
                # Otherwise, we assign your target default values (e.g., varno = 2) for compatibility.
                target_varno = 2
                target_subtype = 0

                # Handle single values or arrays (subsets)
                if isinstance(lat, (list, tuple)):
                    for la, lo in zip(lat, lon):
                        records.append({
                            'lat': la,
                            'lon': lo,
                            'varno': target_varno,
                            'ops_subtype': target_subtype
                        })
                else:
                    records.append({
                        'lat': lat,
                        'lon': lon,
                        'varno': target_varno,
                        'ops_subtype': target_subtype
                    })

            except Exception as e:
                print(f"Error processing a BUFR message: {e}")
            finally:
                # Always release the message handle to prevent memory leaks
                eccodes.codes_release(bufr_id)

    # --- Process and write AFTER the loop has read all messages ---
    if not records:
        print("No records extracted from the BUFR file.")
    else:
        # Convert to DataFrame and write to ODB-2 once
        df = pandas.DataFrame(records)
        print(df)
        print(f"Extracted {len(df)} rows. Writing to ODB-2: {odb_filepath}")
        codc.encode_odb(df, odb_filepath)
        print("Successfully completed conversion.")



"""


