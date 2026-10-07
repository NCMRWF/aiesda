#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 27 23:07:54 2019
Updated for Python 3

@author: gibies
"""
import sys
import os
import subprocess

OBSLIB = os.environ.get('OBSLIB', "${MONITOBS}/pylib")
if OBSLIB not in sys.path:
    sys.path.append(OBSLIB)

import obslib
#import obstore
import pandas
import numpy

diaglev = int(os.environ.get('GEN_MODE', 0))
MAXINDX = int(os.environ.get('MAXINDX', getattr(obstore, 'MAXINDX', 1000)))

def errprint(*args, **kwargs):
    if diaglev > 0:
        print(*args, file=sys.stderr, **kwargs)

def query(obsfile, nmlfile, subtype=None, indx=None, selectlist=None, userquery=None, nanqlist=None, nanvalue=-1073741824.0, minlev=5, maxindx=MAXINDX):
    if nanqlist is None:
        nanqlist = []
        
    print("inside query function in sqlobs")
    print(selectlist)
    
    if subtype is None:
        subtype = obstore.obstore_read_index_subtype(obsfile, indx)
    if indx is None:
        indx = obstore.obstore_read_subtype_index(obsfile, subtype)
    if selectlist is None:
        selectlist = obstore.getelenams(obsfile, nmlfile, subtype, indx)
        
    elist = obstore.obstore_read_batch_elements(obsfile, indx, nmlfile, maxindx)
    data = obstore.frame_data_batch(obsfile, nmlfile, indx, selectlist, maxindx=maxindx)
    
    data = nanquery(data, elist, nanqlist, nanvalue, minlev)
    
    if userquery is None:
        querystring = ""
    else:
        querystring = " & ".join(userquery)
        
    try:
        data = data.query(querystring)
    except Exception:
        errprint("Retrieving data without any user defined filter query")
        
    print("inside query function of sqlobs")
    print(data)
    return data

def nanquery(data, elist, nanqlist, nanvalue, minlev):
    nanq = []
    for elenam in nanqlist:
        ncols = obstore.getldc(elenam, elist=elist)
        if ncols > 1:
            nanq += [f"{elenam}{j} != {nanvalue}" for j in range(1, minlev, 1)]
        else:
            nanq += [f"{elenam} != {nanvalue}"]
            
    nanquerystring = " & ".join(nanq)
    try:
        data = data.query(nanquerystring)
    except Exception:
        errprint("Retrieving data without any nan-value filter query")
    return data
