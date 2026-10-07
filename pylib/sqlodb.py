#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 22 06:45:11 2019

@author: gibies
"""
from __future__ import print_function
import os
import sys
OBSLIB=os.environ.get('OBSLIB',"${MONITOBS}/pylib")
sys.path.append(OBSLIB)
OBSNML=os.environ.get('OBSNML',"${MONITOBS}/nml")
sys.path.append(OBSNML)
odb_index_nml=OBSNML+"/odb_index_nml"
import obslib
import subprocess
#subprocess.call("module unload PrgEnv-cray", shell=True)
#subprocess.call("module load PrgEnv-intel/6.0.4", shell=True)
#subprocess.call("module load intel/odbserver/0.16.2.omp.1", shell=True)
#import odb
import pandas
import numpy
import datetime
import pyodc
import codc
import sqlite3

diaglev=int(os.environ.get('GEN_MODE',0))


# --- Compatibility Shim for Legacy 'odb' using pyodc + sqlite3 ---
class ODBShim:
    def connect(self, odbfile):
        conn = sqlite3.connect(':memory:')
        if os.path.exists(odbfile) and os.path.getsize(odbfile) > 0:
            # 1. Read ODB-2 file into a Pandas DataFrame using pyodc
            odbdf = pyodc.read_odb(odbfile)

            # 2. Convert generator/iterable of frames into a single Pandas DataFrame
            if hasattr(odbdf, '__iter__') and not isinstance(odbdf, pandas.DataFrame):
                odbdf = pandas.concat(odbdf, ignore_index=True)
            else:
                odbdf = odb_data

            # 3. Load DataFrame into SQLite using the exact file path as the table name
            # (SQLite allows paths/dots as table names when double-quoted)
            odbdf.to_sql(odbfile, conn, index=False, if_exists='replace')
        return conn

odb = ODBShim()
# -----------------------------------------------------------------


def errprint(*args, **kwargs):
    if diaglev > 0: print(*args, file=sys.stderr, **kwargs)
    
def sqlodb(odbfile,sqlquerystring):
    if os.path.getsize(odbfile) > 0:
        data=pandas.read_sql_query(str(sqlquerystring),odb.connect(odbfile))
        return(data)

def query(odbfile,nmlfile=odb_index_nml,subtype=None,elenams=None,varnolist=None,userquery=None):
    print(varnolist)
    if elenams is None:
        elenams = []
    if varnolist is None:
        varnolist = []
    if userquery is None:
        userquery = []
    odbname=[None]*len(elenams)
    print("varnolist:", varnolist)
    odbname = [None] * len(elenams)
    for i, opsname in enumerate(elenams):
        odbname[i] = obslib.getodbname(nmlfile, opsname) if hasattr(obslib, 'getodbname') else opsname

    if not odbname:
        selectstring = "*"
    else:
        selectstring = ','.join(elenams + ["ops_subtype", "varno"])

    # Safely build conditions to prevent syntax errors
    conditions = []
    if subtype is not None:
        conditions.append(f"ops_subtype = {subtype}")
    if userquery:
        if isinstance(userquery, list):
            conditions.extend(userquery)
        else:
            conditions.append(str(userquery))
    if varnolist:
        v_str = ' OR '.join([f"varno = {v}" for v in varnolist])
        conditions.append(f"({v_str})")

    where_clause = ""
    if conditions:
        where_clause = "where " + " AND ".join(conditions)

    # Rebuild the exact legacy SQL query format safely
    sql_query = f'select {selectstring} from "{odbfile}" {where_clause};'
    print("Executing SQL:", sql_query)
    data = sqlodb(odbfile, sql_query)
    return(data)

"""
##### Legasy logic befor modification 20260930 ###
   for i,opsname in enumerate(elenams):
           odbname[i]=obslib.getodbname(nmlfile,opsname)
    if not odbname: selectstring = "*"
    else: selectstring = ','.join(odbname+["ops_subtype"])
    if not subtype: subtypequery = ""
    else: subtypequery = "where ops_subtype = "+str(subtype)
    if not userquery: querystring= subtypequery
    else: querystring=' and '.join( [subtypequery]+ userquery )
    varnoquery=queryvarno(varnolist)
    if not varnolist: print(querystring)
    else: querystring= ' AND '.join( [querystring] + varnoquery  )
    data=sqlodb(odbfile,'select ' + selectstring + ' from "' + odbfile + '" ' + querystring + ';')
"""

def queryvarno(varnolist):
    varnoquery=' OR varno = '.join(["varno = "+str(varnolist[0])] + [str(i) for i in varnolist[1:]] )
    return(["( " +varnoquery +")"])
    
def odb_readdata(odbfile):
    return(sqlodb(odbfile,'select * from "' + odbfile + '" ;'))
#    if os.path.getsize(odbfile) > 0:
#        data=pandas.read_sql_query('select * from "' + odbfile + '" ;',odb.connect(odbfile))
#        return(data)
        
def odb_sqlwhere(odbfile,querystring):
    return(sqlodb(odbfile,'select * from "' + odbfile + '" where '+querystring+' ;'))
        
def odb_sqlselect(odbfile,elenams):
    elestr=','.join(elenams)
    return(sqlodb(odbfile,'select '+ elestr +' from "' + odbfile + '" ;'))

def odb_list_varno(odbfile):
    return(sqlodb(odbfile,'select distinct varno from "' + odbfile + '";').values[:,0])

def odb_list_subtype(odbfile):
    return(pandas.read_sql_query('select distinct ops_subtype from "' +odbfile + '" ;',odb.connect(odbfile)).values[:,0])

def odb_filter_varno(odbfile,varno):
    return(sqlodb(odbfile,'select * from "' + odbfile + '" where varno ='+ str(varno) +' ;'))

def odb_readfield(odbfile,nmlfile,element):
    odbname = obslib.getodbname(nmlfile,element)
    data=sqlodb(odbfile,'select '+odbname+' from "' + odbfile + '" ;')
    return(data.rename(index=str,columns={odbname:element}))
    
def obs_frametable(odbfile,odbnmlfile,elenams):
    dataframelist=[None]*len(elenams)
    for i,element in enumerate(elenams):
        print(element)
        dataframelist[i]=odb_readfield(odbfile,odbnmlfile,element)
    return(obslib.obsdfcat(dataframelist))

