#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 12 15:45:39 2021
Updated for Python 3

@author: gibies
"""
#  Some of the basic elements of this program were derived from
#  automatically generated code with bufr_dump -Dpython
#  Using ecCodes version: 2.16.0 (or newer)

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

# Namelist Paths
obs_nml = os.environ.get('obs_index_nml', os.path.join(OBSNMLDIR, "obs_index_nml"))
odb_nml = os.environ.get('odb_index_nml', os.path.join(OBSNMLDIR, "odb_index_nml"))
varno_nml = os.environ.get('odb_varno_nml', os.path.join(OBSNMLDIR, "odb_varno_nml"))
subtype_nml = os.environ.get('obs_subtype_nml', os.path.join(OBSNMLDIR, "obs_subtype.nml"))
ECBUFRNML = os.environ.get('ECBUFRNML', os.path.join(OBSNMLDIR, "ecbufr_fieldname.nml"))
AAPP_NML = os.environ.get('AAPP_NML', os.path.join(OBSNMLDIR, "aapp_fieldname.nml"))

import obslib
import traceback
import pandas
import numpy
import collections
import eccodes

def get_bufr_subtype_elements(bufr_path):
    with open(bufr_path, "rb") as f:
        while True:
            gid = eccodes.codes_bufr_new_from_file(f)
            if gid is None:
                break

            try:
                # 1. Access Section 1 / Section 3 Header keys BEFORE unpacking
                subtype = (
                    eccodes.codes_get(gid, "dataSubtype")
                    if eccodes.codes_is_defined(gid, "dataSubtype")
                    else None
                )

                rraobs_subtype = (
                    eccodes.codes_get(gid, "rraobsSubtype")
                    if eccodes.codes_is_defined(gid, "rraobsSubtype")
                    else None
                )

                # Descriptors array (unexpanded FXY sequence)
                descriptors = (
                    eccodes.codes_get_array(gid, "unexpandedDescriptors")
                    if eccodes.codes_is_defined(gid, "unexpandedDescriptors")
                    else []
                )

                print(f"Subtype: {subtype} (rraobsSubtype: {rraobs_subtype})")
                print(f"Descriptors Count: {len(descriptors)}")
                print(f"Descriptors Array: {descriptors}")

                # 2. Unpack data section (Section 4) only if element values are needed
                eccodes.codes_set(gid, "unpack", 1)

            except eccodes.CodesInternalError as err:
                print(
                    f"Warning: Failed to process BUFR message handle: {err}"
                )

            finally:
                # Always release handle to avoid memory leaks on HPC runs
                eccodes.codes_release(gid)


def get_bufr_descriptors(bufr_filepath):
    print("inside get descriptors function")
    """Reads sequence/unexpanded descriptors from the first BUFR message."""
    descriptors = []
    with open(bufr_filepath, "rb") as f:
        ibufr = eccodes.codes_bufr_new_from_file(f)
        if ibufr is not None:
            try:
                # Extract sequence descriptors array
                descriptors = eccodes.codes_get_array(ibufr, "unexpandedDescriptors")
            except Exception:
                try:
                    descriptors = eccodes.codes_get_array(
                        ibufr, "unexpandedDescriptorsArray"
                    )
                except Exception:
                    descriptors = []
            eccodes.codes_release(ibufr)
    print(descriptors)
    info=obslib.get_subtype_info_from_descriptor(descriptors)
    print(info)
    return info

def get_ecbufr_elist(bufr_filepath,nmlfile=None,obsname=None):
    info = get_bufr_descriptors(bufr_filepath)
    subtypecode=info.get("subtype_code")
    subtype=info.get("subtype")
    obstype=info.get("obstype")
    obsname=obstype.lower()
    print(obstype)
    #stypcode=obslib.get_subtype_code(nmlfile,subtype)
    print(subtypecode)
    if nmlfile is None:
        nmlfile = os.environ.get(
            "KEYNMLFILE", os.path.join(OBSNMLDIR, f"keys_{obsname}.nml")
        )
    elemlist=obslib.get_elemlist(subtype,nmlfile)
    #print(elemlist)
    return elemlist


def read_elist(ibufr):
    iterid = eccodes.codes_keys_iterator_new(ibufr)
    while iterid:
        iterid = eccodes.codes_keys_iterator_next(iterid)
        # print(f"ID: {iterid}")
        if not iterid:
            break
        key_names = eccodes.codes_keys_iterator_get_name(iterid)
        # print(f"Name: {key_names}")
        # val = eccodes.codes_get(ibufr, key_names)
        # print(f"Value: {val}")
        if key_names == 'md5Data':
            break
    eccodes.codes_keys_iterator_delete(iterid)

def get_dtype(elename, eleindxmaptbl=ECBUFRNML):
    """Retrieves the datatype for a given element name from the mapping namelist table."""
    elename = elename.split('#')[-1]
    try:
        # Use sep=r'\s+' to handle space-delimited namelist tables safely
        df = pandas.read_csv(eleindxmaptbl, sep=r'\s+')
        match = df.query("fieldname == @elename")
        if not match.empty:
            return match.datatype.values[0]
    except Exception as e:
        errprint(f"Error reading datatype for {elename}: {e}")
    return None

def rename_field(data):
    """Lists and returns the column fields of the dataset."""
    fieldlist = list(data.columns)
    print("Field List:", fieldlist)
    return data


def get_ecbufr_fieldlist(bufr_filepath, elemlist=None, nmlfile=None, eleindxmaptbl=ECBUFRNML, subtyp=None, obsname=None):
    print("indide get fieldlist function")
    print(subtyp)
    if obsname is None:
       bsname="surface"
    if nmlfile is None:
       nmlfile = os.environ.get('KEYNMLFILE', os.path.join(OBSNMLDIR, f"keys_{obsname}.nml"))
    if elemlist is None:
        elemlist = get_ecbufr_elist(bufr_filepath,nmlfile=None,obsname=None)
        if elemlist is None:
            if subtyp is None:
                elemlist = obslib.get_key_info(nmlfile, key="elemlist")
            else:
                elemlist = obslib.get_key_info(nmlfile, key=f"elemlist_{subtyp}")
            
    if isinstance(elemlist, str):
        elemlist = numpy.fromstring(elemlist[1:-1], sep=',', dtype=int)
        
    elist = pandas.DataFrame(list(collections.Counter(elemlist).items()), columns=["elem", "elcnt"])
    elist = elist.sort_values(by=['elem'])
    
    # Load the mapping table once outside the loop for high performance
    if eleindxmaptbl is None:
        eleindxmaptbl=ECBUFRNML
    #print(eleindxmaptbl)
    try:
        maptbl = pandas.read_csv(eleindxmaptbl, sep=r'\s+')
    except Exception:
        maptbl = pandas.read_table(eleindxmaptbl, sep=r'\s+')
        
    obs_fieldlist = []
    ecb_fieldlist = []
    obsindxlist = []
    levlist = []
    
    #print(elist.elem)
    for elem in elist.elem:
        #print(elem)
        match_elem = maptbl.query("indx == @elem")
        if match_elem.empty:
            print(f"Element {elem} not found")
            continue
            
        fieldname = match_elem.fieldname.values[0]
        elename = match_elem.elename.values[0]
        count = elist.query("elem == @elem").elcnt.values[0]
        
        if count == 1:
            if pandas.notna(fieldname):
                if elem > 261:
                    ecb_fieldlist.append(f"#{count}#{fieldname}")
                else:
                    ecb_fieldlist.append(fieldname)
                obs_fieldlist.append(elename)
                obsindxlist.append(elem)
                levlist.append(1)
        else:
            chnlmap = obslib.get_key_info(nmlfile, key=fieldname)
            if isinstance(chnlmap, str):
                chnlmap = numpy.fromstring(chnlmap[1:-1], sep=',', dtype=int)
            for i, indx in enumerate(chnlmap, start=1):
                if indx > 0:
                    if pandas.notna(fieldname):
                        ecb_fieldlist.append(f"#{indx}#{fieldname}")
                        obs_fieldlist.append(f"{elename}_{i}")
                        obsindxlist.append(elem)
                        levlist.append(i)
                        
    fieldlist = pandas.DataFrame({
        "obsindx": obsindxlist,
        "chnlev": levlist,
        "elename": obs_fieldlist,
        "fieldname": ecb_fieldlist
    })
    fieldtable = fieldlist.set_index(["obsindx", "chnlev"]).sort_index(ascending=True)
    #print(fieldtable)
    return fieldtable

"""
def read_element(ibufr, field, count, data, eleindxmaptbl=ECBUFRNML):
    elename = field.elename
    fieldname = field.fieldname
    dtype = get_dtype(fieldname, eleindxmaptbl)
    
    if dtype in ["iVal", "rVal"]:
        data1 = eccodes.codes_get(ibufr, fieldname)
        data1 = [data1] * count
    else:
        data1 = eccodes.codes_get_array(ibufr, fieldname)
        
    if len(data1) == 1:
        data1 = [data1[0]] * count
        
    data[elename] = data1
    return data
"""

def read_element(ibufr, field, count, data, eleindxmaptbl=ECBUFRNML):
    # Standardize string extraction for raw strings, tuples, dicts, or pandas Series
    if isinstance(field, str):
        elename = field
        fieldname = field
    elif hasattr(field, 'elename') and hasattr(field, 'fieldname'):
        elename = field.elename
        fieldname = field.fieldname
    elif isinstance(field, (tuple, list)):
        elename = field[1] if len(field) > 1 else field[0]
        fieldname = elename
    elif hasattr(field, 'get'):
        elename = field.get('elename', field.get('fieldname'))
        fieldname = field.get('fieldname', elename)
    else:
        elename = str(field)
        fieldname = str(field)

    dtype = get_dtype(fieldname, eleindxmaptbl)

    if dtype in ["iVal", "rVal"]:
        try:
            data1 = eccodes.codes_get(ibufr, fieldname)
            data1 = [data1] * count
        except Exception:
            data1 = [None] * count
    else:
        try:
            data1 = eccodes.codes_get_array(ibufr, fieldname)
        except Exception:
            data1 = [None] * count

    if len(data1) == 1:
        data1 = [data1[0]] * count

    data[elename] = data1
    return data

def message_read(ibufr, fieldlist=None, eleindxmaptbl=ECBUFRNML):
    eccodes.codes_set(ibufr, 'unpack', 1)
    count = eccodes.codes_get(ibufr, 'numberOfSubsets')
    data = pandas.DataFrame(index=range(1, (count + 1), 1))
    
    if fieldlist is None:
        fieldlist = ['year', 'month', 'latitude', 'longitude']

    # Convert list or pandas Series to a standardized iterable of (index, field) tuples
    if isinstance(fieldlist, list):
        fields = list(enumerate(fieldlist))
    elif hasattr(fieldlist, 'iterrows'):
        # If fieldlist is a DataFrame, iterate rows picking the field name/row object
        fields = list(fieldlist.iterrows())
    elif hasattr(fieldlist, 'items'):
        # If fieldlist is a pandas Series
        fields = list(fieldlist.items())
    else:
        fields = list(enumerate(fieldlist))
    print(fields)

    for indx, field in fields:
        data = read_element(ibufr, field, count, data, eleindxmaptbl=eleindxmaptbl)
        
    return data

def bufr_decode(input_file, nmlfile, eleindxmaptbl=ECBUFRNML, elemlist=None, subtype=None, fieldlist=None):
    if fieldlist is None:
        fieldlist = get_ecbufr_fieldlist(nmlfile=nmlfile, eleindxmaptbl=eleindxmaptbl, elemlist=elemlist, subtyp=subtype)
    print(fieldlist)
    frames = []
    with open(input_file, 'rb') as f:
        while True:
            ibufr = eccodes.codes_bufr_new_from_file(f)
            if ibufr is None:
                break
            try:
                eccodes.codes_set(ibufr, 'unpack', 1)
                data1 = message_read(ibufr, fieldlist, eleindxmaptbl=eleindxmaptbl)
                frames.append(data1)
            finally:
                eccodes.codes_release(ibufr)
    if frames:
        data = pandas.concat(frames, ignore_index=True)
    else:
        data = pandas.DataFrame()
    print(data)
    print(subtype)    
    if subtype is None:
        info = get_bufr_descriptors(input_file)
        subtypecode=info.get("subtype_code")
        print(subtypecode)
    data = data.assign(subtype=[int(subtypecode)] * len(data))
    return data


def bufr_decode_files(bufr_filepath, Tnode, slctstr, nmlfile, eleindxmaptbl=None, elemlist=None, subtype=None, keyfieldlst=None, minval=-99999.99, maxval=99999.99, obsname=None, field=None):
    """
    Decodes multiple BUFR files matching a glob pattern, applies window filters, 
    and returns a combined pandas DataFrame.
    """
    print("inside ecbufr library parent function call")
    print(subtype)
    if keyfieldlst is None:
        searchstring = os.path.join(bufr_filepath, slctstr)
        infiles = obslib.globlist(searchstring)
        target_file = infiles[0] if isinstance(infiles, (list, tuple)) else infiles
        fieldtable = get_ecbufr_fieldlist(target_file)
    #print(ecbufr_fldlst)
    #return ecbufr_fldlst
        #fieldtable = get_bufr_descriptors(target_file)
        print(fieldtable)
        keyfieldlst = fieldtable.fieldname.values.tolist()
        #fieldlist = get_ecbufr_fieldlist(nmlfile=nmlfile, eleindxmaptbl=eleindxmaptbl, elemlist=elemlist, subtyp=subtype)
        print(keyfieldlst)
        #print(fieldlist)

        if obsname is None:
            obsname="surface"
        if nmlfile is None:
            nmlfile = os.environ.get('KEYNMLFILE', os.path.join(OBSNML, f"keys_{obsname}.nml"))
        if eleindxmaptbl is None:
            eleindxmaptbl = ECBUFRNML
        
        
    
    if len(infiles) == 0:
        print(f"File not found: {searchstring}")
        
    print(f"Received {len(infiles)} BUFR files")
    
    frames = []
    for infile in infiles:
        print(infile)
        data1 = bufr_decode(infile, nmlfile, eleindxmaptbl=eleindxmaptbl, elemlist=elemlist, subtype=subtype,fieldlist=keyfieldlst)
        
        for field in keyfieldlst:
            data1 = obslib.frame_window_filter(data1, item=field, minval=minval, maxval=maxval)
            
        print(data1)
        frames.append(data1.copy())
        
    if frames:
        data = pandas.concat(frames, ignore_index=True)
    else:
        data = pandas.DataFrame()
        
    data = obslib.reset_index(data)
    return data
