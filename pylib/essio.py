#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 23 12:56:36 2019

@author: gibies
"""
from __future__ import print_function
import os,sys
CURR_PATH=os.path.dirname(os.path.abspath(__file__))
PKGHOME=os.environ.get('PKGHOME',os.path.dirname(CURR_PATH))
PKGNAME=os.path.basename(PKGHOME)
LIB=os.environ.get('LIB',PKGHOME+"/pylib")
sys.path.append(LIB)
DIC=os.environ.get('DIC',PKGHOME+"/pydic")
sys.path.append(DIC)
NML=os.environ.get('NML',PKGHOME+"/nml")
sys.path.append(NML)
PALETTE=os.environ.get('PYNGL_COLORMAPS',PKGHOME+"/palette")
SUBTYPNML=NML+"/obs_subtype.nml"

diaglev=int(os.environ.get('GEN_MODE',0))
def errprint(*args, **kwargs):
    if diaglev > 0: print(*args, file=sys.stderr, **kwargs)

import datadic
import subprocess
import obslib
import pplib
import vardic
import glob,datetime
import Nio, Ngl
#import netCDF4
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as pyplot
pyplot.switch_backend('agg')
import matplotlib.colors as colors
import matplotlib.cm as mplcm
from mpl_toolkits.basemap import Basemap, shiftgrid, addcyclic
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import pandas
import numpy
import domaindic
import math
import xarray
import pygrib
import iris
from iris.util import new_axis
import iris_grib
import umrlib


####################################################
#import numpy.core.multiarray
#import gribapi
### ImportError: No module named _multiarray_umath
####################################################

def dset_latlon_assign(datset, lon, lat, datval):
    indx = pairwise_distances_argmin(X=[[lon, lat]], Y=numpy.c_[datset['lon'].values.ravel(), datset['lat'].values.ravel()])
    i0, j0 = numpy.unravel_index(indx, (datset['lon'].shape))
    #datset.loc[x=j0, y=i0]=datval
    return datset

def dset_latlon_extract(datset, lon, lat):
    indx = pairwise_distances_argmin(X=[[lon, lat]], Y=numpy.c_[datset['lon'].values.ravel(), datset['lat'].values.ravel()])
    i0, j0 = numpy.unravel_index(indx, (datset['lon'].shape))
    return datset.isel(x=j0, y=i0).squeeze()

def datfr_extract(datset,datfr,distcol,varlst):
	indx=dat
	for varnam in varlst:
		print(varnam)

def datfr_min_indx(datfr,colnam):
	indx=datfr[datfr[colnam]==datfr[colnam].min()].index[0]
	return(indx)

def datfr_max_indx(datfr,colnam):
	indx=datfr[datfr[colnam]==datfr[colnam].max()].index[0]
	return(indx)

def datfr_colocate(datset,datframe,gridsize,lon,lat,lev=None,time=None,datfrlat="Latitude",datfrlon="Longitude",varlst=None):
	hlfwdth=gridsize/2
	datframe=datframe.assign(colocdist=None)
	#### initialisation of variables ####
	for varnam in varlst:
		   datset[varnam]=numpy.nan
	#####################################
	for latval in lat:
	   for lonval in lon:
	      lonmin=lonval-hlfwdth
	      lonmax=lonval+hlfwdth
	      latmin=latval-hlfwdth
	      latmax=latval+hlfwdth
	      qrystr=str(datfrlat)+" > "+str(latmin)+" and "+datfrlat+" < "+str(latmax)+" and "+datfrlon+" > "+str(lonmin)+" and "+datfrlon+" < "+str(lonmax)
	      if datfrlat in datframe:
	         if datfrlon in datframe:
	            datfr=datframe.query(qrystr)
	      print(datfr)
	      if len(datfr.index) > 0:
		for indx in datfr.index:
	            datfr["colocdist"].loc[indx]=math.sqrt((datfr[datfrlat].loc[indx]-latval)**2+(datfr[datfrlon].loc[indx]-lonval)**2)
	        indx=datfr_min_indx(datfr,"colocdist")
	        #indx=datfr["colocdist"].idxmin()
		#print(datfr)
		print(indx)
		print(datfr.loc[indx])
	      else:
	        indx=None
	      print(indx)
	      for varnam in varlst:
		if indx is not None:
		   if varnam is "datfrindx":
	      		datset["datfrindx"].loc[{"lat":latval,"lon":lonval}]=indx
		   else:
			datval=datfr[varnam].loc[indx]
			print(datval)
			print(datset[varnam])
			datset[varnam].loc[{"lat":latval,"lon":lonval}]=datval
		#else:
		#   datset[varnam].loc[{"lat":latval,"lon":lonval}]=numpy.nan
	return(datset)

def datset_colocate(datset,gridsize,lon,lat):
        hlfwdth=gridsize/2
        for latval in lat:
           for lonval in lon:
              lonmin=lonval-hlfwdth
              lonmax=lonval+hlfwdth
              latmin=latval-hlfwdth
              latmax=latval+hlfwdth
              qrystr=str(datfrlat)+" > "+str(latmin)+" and "+datfrlat+" < "+str(latmax)+" and "+datfrlon+" > "+str(lonmin)+" and "+datfrlon+" < "+str(lonmax)


def datfr_compute_tcwv(datfr,subtyplst=None,varlst=None):
	if varlst is None: varlst=["datfrindx"]
	if subtyplst is None: subtyplst=obslib.unique_list(datframe.subtype.values)
	print(subtyplst)
	print(varlst)
	for column in datfr.columns:
		for value in datfr[column]:
	        # Extract numerical value and unit from the string
	        	num_value, unit = extract_value_and_unit(str(value))
	        # Print the numerical value and unit
	       		print("Column: {}, Numerical Value: {}, Unit: {}".format(column,num_value,unit))

    		#print("Column: {}, Data Type: {}".format(column, datfr[column].dtype))
		#print(f"Column: {column}, Data Type: {df[column].dtype}")
	#pandas.set_option('display.max_columns', None)
	#pandas.set_option('display.max_rows', None)
	print(datfr)
	print(datfr.columns.values)
	datfr=datfr.assign(TCWV=None)
	if len(datfr.index) > 0:
                for indx in datfr.index:
                    datfr["TCWV"].loc[indx]=numpy.nan
	return(datfr)

def specific_humidity_from_dewpoint(pressure, dewpoint):
    e0 = 6.113 
    c_water = 5423 
    c_ice = 6139
    T0 = 273.15
    pres = pressure.to('hPa').magnitude
    dew = dewpoint.to('kelvin').magnitude
    if dew >= T0:
        c = c_water 
    else: 
        c=c_ice
    q = ((622 * e0)/ pres) * numpy.exp(c * (dew - T0) / (dew * T0))   # g/kg
    return(q)

#############################################################################################################################
### GribAPI and IRIS based functions
#############################################################################################################################

def read_grib(gribfile):
	filtered_messages = []
	for msg in iris_grib.message.GribMessage.messages_from_filename(gribfile):
	    if msg.sections[4]['productDefinitionTemplateNumber'] is not None:
		print(msg.sections[4]['productDefinitionTemplateNumber'])
		print(msg.sections[4]['parameterNumber'])
		print(msg.sections[4]['typeOfFirstFixedSurface'])
		print(msg.sections[1])
		print(msg.sections[3])
		print(msg.sections[4])
		print(msg.sections[5])
		print(msg.sections[6])
		print(msg.sections[7])
		print(msg.sections[8])
		filtered_messages.append(msg)
	cubes_messages = iris_grib.load_pairs_from_fields(filtered_messages)
	print(cubes_messages)
	for cube, msg in cubes_messages:
	   prod_stat = msg.sections[1]['productionStatusOfProcessedData']
	   cube.attributes['productionStatusOfProcessedData'] = prod_stat
	print(cube.attributes['productionStatusOfProcessedData'])
		#msg.sections[4]['productDefinitionTemplateNumber']; 
		#msg.sections[4]['parameterNumber']
	cubes = iris.load(gribfile)
	return(cubes)

def cube_list(infile):
	cubes = read_grib(infile)
	cubes = list(cubes)
	umrlib.tweaked_messages(cubes)
	return(cubes)

def save_grib(gribfile,cubes):
	iris.save(cubes, gribfile)

def gri_load(fpath):
    if os.path.isfile(fpath):
        try:        
            f = iris.load(fpath, callback=update_cf_standard_name) # load intermediate grib2 file
        except gribapi.GribInternalError as e:
            if str(e) == "Wrong message length":
                print("ALERT!!!! ERROR!!! Couldn't read grib2 file to re-order", e)
            else:
                print("ALERT!!! ERROR!!! couldn't read grib2 file to re-order", e)
            return 
        except Exception as e:
            print("ALERT!!! ERROR!!! couldn't read grib2 file to re-order", e)
            return
        print("f = ", f)
	return(f)

#############################################################################################################################
### Pygrib based functions
#############################################################################################################################

def pyg_get_file_varlst(infile):
	grbptr=pygrib.open(infile)
	grbmsg=grbptr.select()
	msgcnt=len(grbmsg)
	varlst=[]
	for msgindx in range(0,msgcnt):
		varnam=grbmsg[msgindx].name
		#varnam=map(str,grbmsg[msgindx].name)
		varlst.append(varnam)
	return(varlst)

def pyg_indx(infile,keylist,indxfltr):
	if keylist is None:
		grbindx=pygrib.open(infile)
	else:
		grbindx=pygrib.index(infile,*keylist)
	if indxfltr is None:
		grbindx=grbindx.select()
	else:
		grbindx=grbindx.select(**indxfltr)
	return(grbindx)

def pyg_get_levs(infile):
	gr = pygrib.open(infile) 
	levlst =[]
	for g in gr:
	    levlst.append(g.level)
	#print(levlst)
	levlst=numpy.array(levlst)
	#print(levlst)
	return(levlst)

def pyg_datset_attr(datset,grbmsg,varnam,attrlst=None,attrs=None):
	if attrlst is None: attrlst=grbmsg.keys()
	if attrs is None: attrs=datset[varnam].attrs
	#print(grbmsg)
	for attrnam in attrlst:
		print(attrnam)
		#attrnam=str(attrnam)
		if attrnam in grbmsg.keys():
			#if grbmsg[attrnam] is not None:
				try:
               				value = grbmsg[attrnam]
        			except:
               				value = None
				attrs.update({attrnam:value})
	datset[varnam].attrs=attrs
	#print(datset)
	return(datset)

def pyg_read_file(infile,indxkeys=None,indxfltr=None,varlst=None,coords=None,dimlst=None,attrlst=None):
	if varlst is None: varlst=pyg_get_file_varlst(infile)
	levlst=pyg_get_levs(infile)
	datset=xarray.Dataset()
	if coords is None: 
		coords=datset.coords
	if dimlst is None: 
		dimlst=["lat","lon"]
	for varnam in varlst:
		#indxkeys=['name','shortName','level','forecastTime']
		indxfltr={"name":varnam,}
		grbptr=pyg_indx(infile,indxkeys,indxfltr)
		grbmsg=grbptr[0]
		data1,lats2d,lons2d=grbmsg.data()
		coords.update({"lats2d":(dimlst,lats2d),})
		coords.update({"lons2d":(dimlst,lons2d),})
		coords.update({"lat":lats2d[:,0]})
		coords.update({"lon":lons2d[0,:]})
		attrlst=grbmsg.__getattr__
		#print(attrlst)
		if dimlst is None: dimlst=coords.keys()	
		datset[varnam]=xarray.DataArray(data=data1,dims=dimlst,coords=coords,name=varnam)
		#datset=pyg_datset_attr(datset,grbmsg,varnam)
	return(datset)

def pyg_write_file(datset,outfile,indxkeys=None,indxfltr=None,varlst=None,coords=None,dimlst=None,attrlst=None):
	with open(outfile, 'wb') as outgrb:
		for varnam in varlst:
			print(varnam)
			datstring=""
			msg = pygrib.fromstring(datstring)
			outgrb.write(msg)
		#outgrb.close()
	return(outfile)


def pyg_extract(infile,indxkeys=None,indxfltr=None,varlst=None,coords=None,dimlst=None,attrlst=None):
	return(pyg_read_file(infile,indxkeys,indxfltr,varlst,coords,dimlst,attrlst))
		


#############################################################################################################################
### IRIS based functions
#############################################################################################################################

def iri_load_cubes(infile,cnst=None,callback=None,stashcode=None,option=0,dimlst=None,ref_dim=None,time_cnstlst=None,domain=None):
    opt=str(option)
    if stashcode is not None: cnst=iris.AttributeConstraint(STASH=stashcode)
    switcher = {
       "0" :lambda: iris.load(infile,constraints=cnst, callback=callback),
       "1" :lambda: iris.load_cubes(infile,constraints=cnst, callback=callback),
       "2" :lambda: iris.load_cube(infile,constraint=cnst, callback=callback),
       "3" :lambda: iris.load_raw(infile,constraints=cnst, callback=callback),
    }

    func = switcher.get(opt, lambda: 'Invalid option')
    cubes = func()
    print("cubes cubes cubes cubes cubes cubes",cubes)
    if time_cnstlst is not None:
	timemin = time_cnstlst[0]
	print("t1 is",timemin)
	timemax = time_cnstlst[1]
	print("t2 is",timemax)
	cubes=cubes[timemin:timemax]
	print(cubes)
    #print("ref_dim before", ref_dim)
    cubes = cubes.collapsed('time', iris.analysis.MEAN)
    if ref_dim is not None:
         interp_cube=iri_regrid(cubes,ref_dim=ref_dim)
	 #print("ref_dim after:interp_cube", interp_cube)
	 cubedimlst=[coord.name() for coord in interp_cube.dim_coords]
         cubeauxc=[coord.name() for coord in interp_cube.aux_coords]
	 if dimlst is not None:
	    for dimnam in dimlst:
		if dimnam in cubeauxc:
		   if len(interp_cube.coord(dimnam).points) is 1:
		      cubes=new_axis(interp_cube,dimnam)
    		      print("load_cubes", cubes.units)
    else:
    	cubedimlst=[coord.name() for coord in cubes.dim_coords]
    	cubeauxc=[coord.name() for coord in cubes.aux_coords]
    	if dimlst is not None:
	   for dimnam in dimlst:
	       if dimnam in cubeauxc:
		  if len(cubes.coord(dimnam).points) is 1:
		     cubes=new_axis(cubes,dimnam)
    #print(cube)
    if domain is not None:
	latmin=domain.latmin
	latmax=domain.latmax
	lonmin=domain.lonmin
	lonmax=domain.lonmax
	cubes=cubes.intersection(longitude=(lonmin,lonmax),latitude=(latmin,latmax))
	#cubes=iris.Constraint(time=lambda cell: pdt1 <= cell.point < pdt2)
    return(cubes)

def iri_to_nc(infile,varlst,outfile,callback=None,stashcode=None,option=2,dimlst=None,coords=None):
	cube=iri_load_cubes(infile,cnst=varlst,callback=callback,stashcode=stashcode,option=option,dimlst=dimlst)
	nc_file=iris.save(cube,outfile)
	return(nc_file)

def iri_regrid(cube,ref_dim=None,ref_cube=None,lat=None,lon=None,lev=None):
	print("cube attributes",cube.units)
	if ref_dim is not None:
		lat = ref_dim['lat']
		lon = ref_dim['lon']
		lev = ref_dim['lev']
	if ref_cube is not None:
		lat = ref_cube.coord('latitude').points
		lon = ref_cube.coord('longitude').points
		lev = ref_cube.coord('level_height').points
	interp_cube = cube.interpolate([('latitude', lat), ('longitude', lon),('level_height', lev)],iris.analysis.Linear())
	#attrlst = list(interp_cube.units)
	print("interp_cube attributes",interp_cube.units)
	return(interp_cube)	

#############################################################################################################################
### IRIS and XARRAY combination based functions
#############################################################################################################################

def irx_cube_array(cube,varlst,dimlst=None,coords=None):
	cubedimlst=[coord.name() for coord in cube.dim_coords]
	cubeauxc=[coord.name() for coord in cube.aux_coords]
	if dimlst is None: dimlst=cubedimlst	
	datset=xarray.Dataset()
	if coords is None: 
		coords=datset.coords
		for dimnam in dimlst:
			coords.update({dimnam:cube.coord(dimnam).points,})
			unit=cube.coord(dimnam).units
			datset[dimnam].attrs['units'] = unit
	for var in varlst:
		data1=cube.data
		units=cube.units
		#keys=cube.keys()
		#print("keys",keys)
		datset[var]=xarray.DataArray(data=data1,dims=dimlst,coords=coords,name=var)
		datset[var].attrs['units'] = units
		print("irx_cube_array",datset[var].attrs['units'])
	return(datset)

def irx_load_cubray(infile,varlst,dimlst=None,coords=None,callback=None,stashcode=None,ref_dim=None,time_cnstlst=None,option=2):
	cube=iri_load_cubes(infile,cnst=varlst,callback=callback,stashcode=stashcode,option=option,dimlst=dimlst,ref_dim=ref_dim,time_cnstlst=time_cnstlst)
	print("irx_load_cubray",cube)
	#if lat is not None and lon is not None and lev is not  None:
		#interp_cube=iri_regrid(cube,lat=lat,lon=lon,lev=lev)
		#datset=irx_cube_array(interp_cube,varlst,dimlst=dimlst,coords=coords)
	#else:
	datset=irx_cube_array(cube,varlst,dimlst=dimlst,coords=coords)
	for var in varlst:
		print("units", datset[var].attrs['units'])
	return(datset)


def irx_extract(infile,varlst,dimlst=None,coords=None,callback=None,stashcode=None,ref_dim=None,time_cnstlst=None,option=2):
	datset=irx_load_cubray(infile,varlst,callback=callback,stashcode=stashcode,option=option,dimlst=dimlst,coords=coords,ref_dim=ref_dim,time_cnstlst=time_cnstlst)
	return(datset)

#############################################################################################################################
### NCAR Input Output Library (NIO) and XARRAY combination based functions
#############################################################################################################################


def nix_write_varattr(datset,fileptr,varnam,attrnam,attrtyp="str"):
	attrval=datset[varnam].attrs[attrnam]
	if attrtyp is "str": attrval=str(attrval)
	attrptr=setattr(fileptr.variables[varnam],attrnam,attrval)
	return(fileptr)

def nix_write_var(datset,fileptr,varnam,vartyp="d",varattlst=None):
	data=datset[varnam]
	if varattlst is None: 
	   if data.attrs is not None:
		#for attrky in data.attrs:
			#varattlst=[attrky]
	     		
	      varattlst=list(data.attrs.keys())
	   else:
	      varattlst=[]
	print(varattlst)
	varptr = fileptr.create_variable(varnam,vartyp,data.dims)
	fileptr.variables[varnam].assign_value(data)
	#if len(varattlst) > 0: 
	for attrnam in varattlst:
		fileptr=nix_write_varattr(datset,fileptr,varnam,attrnam)
	return(fileptr)

def nix_write(datset,filenam,dimlst=None,varlst=None):
	if dimlst is None: dimlst=xar_dimlst(datset)
	if varlst is None: varlst=xar_varlst(datset)
	fileptr=Nio.open_file(filenam, "rw")
	for dimnam in dimlst:
		dimptr=fileptr.create_dimension(dimnam,len(datset[dimnam]))
		fileptr=nix_write_var(datset,fileptr,dimnam,vartyp="d")
	for varnam in varlst:
		fileptr=nix_write_var(datset,fileptr,varnam,vartyp="d")
	fileptr.close()
	return(filenam)

def nix_read_varattr(fileptr,varnam,attrnam,datset=None):
	if datset is None: datset=xarray.Dataset()
	attrval=fileptr.variables[varnam].attributes[attrnam]
	datset.variables[varnam].attrs[attrnam]=attrval
	return(datset)

def nix_read_var(fileptr,varnam,varattlst=None,datset=None):
	if varattlst is None: varattlst=["units"]
	if datset is None: datset=xarray.Dataset()
	var=fileptr.variables[varnam]
	type = var.typecode()
	numDims = var.rank
	dimSizes = var.shape
	dimlst = var.dimensions
	data=var.get_value()
	datset[varnam]=xarray.DataArray(data,name=varnam,dims=dimlst)
	for attrnam in varattlst:
		datset=nix_read_varattr(fileptr,varnam,attrnam,datset=datset)
	return(datset)

def nix_read(filenam,dimlst,varlst):
	fileptr=Nio.open_file(filenam, "r")
	datset=xarray.Dataset()
	for varnam in varlst:
		datset=nix_read_var(fileptr,varnam,varattlst=["units"],datset=datset)
	for dimnam in dimlst:
		datset=nix_read_var(fileptr,dimnam,varattlst=["units"],datset=datset)
	return(datset)

def nix_extract(filenam,varlst,dimlst):
	datset=nix_read(filenam=filenam,dimlst=dimlst,varlst=varlst)
	return(datset)

#############################################################################################################################
### XARRAY based functions
#############################################################################################################################

def xar_dummy(coords,varlst):
	dims=coords.keys()
	dimsize={}
	for dimnam in dims:
		dimsize.update({dimnam:len(coords[dimnam])})
	datarr=xar_data_dummy(dimsize)
	datset=xarray.Dataset(coords=coords)
	for varnam in varlst:
		datset[varnam]=xarray.DataArray(data=datarr,coords=coords,dims=dimsize.keys(),name=varnam)
	return(datset)

def xar_framegrid(datframe,gridsize=None,lon=None,lat=None,lev=None,time=None,reference_time=None,datfrlat="Latitude",datfrlon="Longitude",varlst=None,subtyplst=None):
	if varlst is None: varlst=["datfrindx"]
	if subtyplst is None: subtyplst=obslib.unique_list(datframe.subtype.values)
	if gridsize is None: gridsize=1.0
	if lon is None: lon=numpy.arange(0.0,360.0,gridsize)
	if lat is None: lat=numpy.arange(-90.0,90.0,gridsize)
	if lev is None: lev=numpy.arange(0.0,1.0,gridsize)
	if time is None: time=numpy.arange(0.0,1.0,gridsize)
	if reference_time is None: reference_time=obslib.pydate()
	coords=dict(lon=lon,lat=lat,lev=lev,time=time,)
	dimsize={"lon":len(lon),"lat":len(lat),"lev":len(lev),"time":len(time)}
	if "datfrindx" not in varlst: varlst=varlst+["datfrindx"]
	datset=xar_dummy(coords,varlst)
	lon=numpy.array([142,])
	lat=numpy.array([51,])
	if 50100 in subtyplst and "TCWV" in varlst: datframe=datfr_compute_tcwv(datframe,subtyplst,varlst)
	datset=datfr_colocate(datset,datframe,gridsize,lon,lat,datfrlat=datfrlat,datfrlon=datfrlon,varlst=varlst)
	return(datset)

def xar_regrid(data,lon=None,lat=None,lev=None):
	if lon is None: lon=numpy.arange(1.0,359.0,1)
	if lat is None: lat=numpy.arange(-89.0,89.0,1)
	data=data.interp(latitude=lat, longitude=lon, method="nearest")
	#datanew = datanew.interp(level_height=lev)
	return(data)

def xar_geoloc(lats=None,lons=None):
	if lons is None: lons=numpy.arange(0.0,360.0,1)
	if lats is None: lats=numpy.arange(-90.0,90.0,1)
	midx = pandas.MultiIndex.from_product([lats,lons])
	midx_coords = xarray.Coordinates.from_pandas_multiindex(midx, "x")
	datset=xarray.Dataset(coords=midx_coords)
	return(datset)

def xar_dimsize(datset,dimlst):
	dimsize={}
	for dimnam in dimlst:
		if isinstance(dimlst, dict):
			dimlen=dimlst[dimnam]
		else:
			dimlen=len(datset.variables[dimnam])
		dimsize.update({dimnam:dimlen})
	return(dimsize)
	
def xar_dims_update(dimsize,recdim,recsize):
	if dimsize[recdim] is not recsize:
		dimsize.update({recdim:recsize})
	return(dimsize)

def xar_dimlst(datset):
	dimlst=datset.dims
	return(dimlst)

def xar_varlst(datset):
	varlst=[var for var in datset.data_vars]
	return(varlst)

def xar_ref_dim(daset,varname,lat=None,lon=None,lev=None):
	ref_dim={}
	#for dim in dimlst:
		#ref_dim[dim]=daset[dim]
	ref_dim['lat']=daset[varname].latitude
	ref_dim['lon']=daset[varname].longitude
	ref_dim['lev']=daset[varname].level_height
	#ref_dim['time']=daset[varname].time
	#print(ref_dim)
	#exit()
	return(ref_dim)
	
def xar_extract(filenam,varlst=None,dimlst=None):
	datset=xarray.open_dataset(filenam)
	print("xar_extract time",datset["time"].attrs)
	print("xar_extract time",datset["longitude"].attrs)
	if dimlst is None: dimlst=xar_dimlst(datset)
	if varlst is None: varlst=xar_varlst(datset)
	#for varnam in varlst:
            #for attrky,attrvl in datset[varnam].attrs.items():
                #attrkey=attrky.encode('utf-8') 
		#attrkey = str(attrky)
                #attrval = str(attrvl)
                #datset[varnam].attrs[attrkey]=attrval
		#print("xar_extract dataset attributes",datset[varnam].attrs)
	return(datset)

def xar_data_dummy(dimsize,dimlst=None):
	size_tuple=()
	if dimlst is None: dimlst=dimsize.keys()
	for dimnam in dimlst:
		size_tuple=size_tuple+(dimsize[dimnam],)
	data=numpy.full(size_tuple,fill_value=numpy.nan)
	return(data)

def xar_rec_coords_update(datvar,recdim,recrds=None,recmeta=None,reclen=None,recgap=None,varlst=None,dimlst=None):
	if dimlst is None: dimlst=xar_dimlst(datvar)
	if varlst is None: varlst=xar_varlst(datvar)
	if recrds is None:
		if recdim in recmeta.coords: 
			rec1=recmeta.coords[recdim].values
			recz=rec1+(reclen*recgap)
		else:
			rec1=0
			recz=reclen
			recgap=1
	recrds=numpy.arange(rec1,recz,recgap)
	recdimset=eval(eval('str({ recdim : list(recrds) })'))
	coords=datvar.coords
	coords.update(recdimset)
	if recmeta is not None:
		for dimnam in dimlst:
			if dimnam is not recdim:
				dimcoord=recmeta.coords[dimnam]
				coords.update({dimnam:dimcoord,})
	return(datvar)

def xar_datset_dummy(recmeta,recdim,reclen,recrds=None,recgap=None,dimsize=None,coords=None,dimlst=None,varlst=None):
	if dimlst is None: dimlst=xar_dimlst(recmeta)
	if varlst is None: varlst=xar_varlst(recmeta)
	if recdim not in dimlst:
		#Defrosting 'Frozen' object
		dimlst=dict(dimlst)
		dimlst.update({recdim:reclen})
	if dimsize is None:
		dimsize=xar_dimsize(recmeta,dimlst)
		dimsize=xar_dims_update(dimsize,recdim,reclen)
	data1=xar_data_dummy(dimsize,dimlst)
	data1=xarray.DataArray(data=data1,coords=coords,dims=dimlst)
	datset=xarray.Dataset()
	for varnam in varlst:
		data1=xar_rec_coords_update(data1,recdim,recrds=recrds,recmeta=recmeta,reclen=reclen,recgap=recgap,varlst=varlst,dimlst=dimlst)
		datset[varnam]=data1
	return(datset)

def xar_append(recmeta,reclen,recpoint=None,recdim=None,varlst=None,dimlst=None,dimsize=None,recrds=None,recgap=None,datset=None):
	if recdim is None: recdim="time"
	if varlst is None: varlst=xar_varlst(recmeta)
	if datset is None: datset=xar_datset_dummy(recmeta,recdim,reclen,recrds=recrds,recgap=recgap,dimsize=dimsize,dimlst=dimlst,varlst=varlst)
	if recdim in recmeta.coords: recpoint=recmeta[recdim].values[0]
	slicedic=eval(eval('str({ recdim : recpoint })'))
	#print(slicedic)
	for varnam in varlst:
		if recdim not in recmeta.coords:
			recmeta[recdim]=(recdim,[recpoint])
			recmeta[varnam]=recmeta[varnam].expand_dims(dim = slicedic, axis=0)
			coords=recmeta[varnam].coords
			dimlst=coords.keys()
		recdata=recmeta[varnam].loc[slicedic]
		datset[varnam].loc[slicedic] = recdata
	return(datset)

def xar_print(datset,diagflg=1,varlst=None,dimlst=None):
	print("diagflg = "+str(diagflg))
	if dimlst is None: dimlst=list(xar_dimlst(datset))
	if varlst is None: varlst=xar_varlst(datset)
	if diagflg > 0:
		print(varlst)
		print(dimlst)
	if diagflg > 1:
		for varnam in varlst:
			print(varnam)
			print(datset.variables[varnam].attrs)
			if diagflg > 2: print(datset.variables[varnam])
		for dimnam in dimlst:
			print(None)
			print(datset.variables[dimnam].attrs)
			if diagflg > 2: print(datset.variables[dimnam])
	datset.close()
	return(None)

#############################################################################################################################
### Special functions
#############################################################################################################################

def xar_layer_thickness(q,levdim):
	level_height = q.coords[levdim]	#hybrid_ht
	thickness = xarray.DataArray(data=numpy.zeros(len(level_height)),dims=[levdim],coords={levdim: level_height},name="thickness")
	#thickness = xar_slice(thickness,levdim,None, -1)
	for i in range(1, len(level_height) - 1):
	    thickness[i] = ((level_height[i] - level_height[i - 1]) / 2) + ((level_height[i + 1] - level_height[i]) / 2)
	thickness[0] = (level_height[1] - level_height[0]) / 2
	thickness[-1] = (level_height[-1] - level_height[-2]) / 2
	return(thickness)

def xar_quot_rsqure(datset,varname,levdim):
	data1=datset[varname]
	level_height = data1.coords[levdim]
	R = level_height + 6371*(10**3)
	R_square = R**2
	data = data1 / R_square
	return(data)

def xar_qrhodh(datset,levdim,rhonam,humnam):
	if "density" in datset:
		rhodata=datset["density"]
	else:
		rhodata=xar_quot_rsqure(datset,rhonam,levdim)
	if humnam in datset: qdata=datset[humnam]
	thickness=xar_layer_thickness(qdata,levdim)
	#qdata = xar_slice(qdata,levdim,None, -1)
	weighted_q = qdata * thickness * rhodata.values
	return(weighted_q)

def xar_qtransdh(datset,levdim,rhonam,humnam,vectvar=None):
	if humnam in datset: qdata=datset[humnam]
	if "density" in datset:
		rhodata=datset["density"]
	else:	
		rhodata=xar_quot_rsqure(datset,rhonam,levdim)
	thickness=xar_layer_thickness(qdata,levdim)
	#qdata = xar_slice(qdata,levdim,None, -1)
	if vectvar is None:
		weighted_data = qdata * thickness*rhodata.values
        else:
                weighted_data = qdata * thickness*rhodata.values*datset[vectvar].values
	return(weighted_data)

def xar_height_integral(datset,levdim):
	data = datset.sum(levdim)
	return(data)

def xar_vimt(datset,vardic=None,levdim=None,humnam=None,rhonam=None,uwndnam=None,vwndnam=None):
	if vardic is not None:
		levdim=vardic["levnam"]
		humnam=vardic["humnam"]
		rhonam=vardic["rhonam"]
		uwndnam=vardic["uwndnm"]
		vwndnam=vardic["vwndnm"]
	weighted_q_u = xar_qtransdh(datset,levdim,rhonam,humnam,vectvar=uwndnam)
	u = xar_height_integral(weighted_q_u,levdim)
	weighted_q_v = xar_qtransdh(datset,levdim,rhonam,humnam,vectvar=vwndnam)
	v = xar_height_integral(weighted_q_v,levdim) 
	dataset=xarray.Dataset(
		data_vars=dict(
        		u=(["latitude", "longitude"], u),
        		v=(["latitude", "longitude"], v),
    				),
    		coords=dict(
        		longitude=datset[humnam].longitude.values,
        		latitude=datset[humnam].latitude.values,
        		#time=datset[humnam].time.values,
        		#reference_time=datset[humnam].reference_time,
    				),
    		#attrs=dict(
			#units=datset['time'].attrs['units']),
				)
	for coords in u.coords:
                dataset[coords].attrs = u[coords].attrs
                print("dataset in ipw",u[coords].attrs)
	for varnam in dataset.data_vars:
		dataset[varnam].attrs['units'] = 'kg m-1 s-1'
	return(dataset)
	
def xar_datset(q,rho,u_wind=None,v_wind=None):
	#lon=q["specific_humidity"].longitude
	#lat=q["specific_humidity"].latitude
	#lev=q["specific_humidity"].level_height
	#lev=rho["rhorsq"].level_height
	#q_x=xar_regrid(q,"specific_humidity",lon=lon,lat=lat,lev=lev)
	#rho_x=xar_regrid(rho,"rhorsq",lon=lon,lat=lat,lev=lev)
	#u_wind_x=xar_regrid(u_wind,"x_wind",lon=lon,lat=lat,lev=lev)
	#v_wind_x=xar_regrid(v_wind,"y_wind",lon=lon,lat=lat,lev=lev)
	
	datset=xarray.Dataset()
	datset["sphum"]=q["specific_humidity"]
	datset["rhorsq"]=rho["rhorsq"]
	if u_wind is not None:
		datset["x_wind"]=u_wind["x_wind"]
	if v_wind is not None:
		datset["y_wind"]=v_wind["y_wind"]
	return(datset)

def datset_vimt(filepath=None,filefldr=None,varfile=None,varlst=None,varstash=None,varopt=None,dimlst=None,datset=None,vardic=None):
	if datset is None : datset=datset_build(filepath,filefldr,varfile,varlst,varstash,varopt,dimlst)
	#vimt = xar_vimt(daset,"level_height","rhorsq","sphum")
	#vimt = xar_vimt(datset,vardic)	#"level_height","rhorsq","specific_humidity","x_wind"."y_wind")
	#datset_append(datset)
	#print(datset)
	#return(vimt)
	return(datset)

#############################################################################################################################
### General functions
#############################################################################################################################

def datset_regrid(datset,varname,refer=None,lon=None,lat=None,lev=None):
	if refer is not None:
	   if datset[refer] is not None:
		lon = datset[refer].longitude
		lat = datset[refer].latitude
		#lev = datset[refer].level_height
	data= datset[varname]
	datanew=xar_regrid(datary,lon=None,lat=None,lev=None)
        datset[varname] = datanew	
	return(datset)

def datset_print(datset,diagflg=1,varlst=None,dimlst=None):
	xar_print(datset,diagflg=diagflg,varlst=varlst,dimlst=dimlst)

def datset_save(datset,outpath=None,outfile=None,infile=None,varlst=None,dimlst=None,coords=None,diagflg=0):
	varlst=xar_varlst(datset)
	dimlst=xar_dimlst(datset)
	coords=datset.coords
	var_lst_str=obslib.underscore(varlst)
	if outfile is None: 
		if infile is None:
			outfile=var_lst_str+".nc"
		else:
			iname=infile.split("/")[-1]
			fileprefix=iname.split(".")[0]
			outfile=fileprefix+"_"+var_lst_str+".nc"
	if outpath is not None:
		obslib.mkdir(outpath)
		outfile=outpath+"/"+outfile
	void=nix_write(datset,outfile,dimlst,varlst)
	print(outfile)
	if diagflg > 0: xar_print(datset,diagflg)
	return(outfile)
	

def datset_extract(infile,varlst,dimlst=None,coords=None,outpath=None,outfile=None,callback=None,stashcode=None,ref_dim=None,indxkeys=None,indxfltr=None,attrlst=None,option=None,time_cnstlst=None,diagflg=0):
	if option is None: option=2
	switcher = {
		"0" :lambda: irx_extract(infile,varlst,dimlst=dimlst,coords=coords,callback=callback,stashcode=stashcode,ref_dim=ref_dim,option=option),
		"1" :lambda: irx_extract(infile,varlst,dimlst=dimlst,coords=coords,callback=callback,stashcode=stashcode,ref_dim=ref_dim,option=option),
		"2" :lambda: irx_extract(infile,varlst,dimlst=dimlst,coords=coords,callback=callback,stashcode=stashcode,ref_dim=ref_dim,option=option,time_cnstlst=time_cnstlst),
		"3" :lambda: irx_extract(infile,varlst,dimlst=dimlst,coords=coords,callback=callback,stashcode=stashcode,ref_dim=ref_dim,option=option),
		"4" :lambda: nix_extract(infile,varlst,dimlst),
		"5" :lambda: xar_extract(infile,varlst,dimlst),
		"6" :lambda: pyg_extract(infile,indxkeys=indxkeys,indxfltr=indxfltr,varlst=varlst,coords=coords,dimlst=dimlst,attrlst=attrlst),
    	}
	func = switcher.get(str(option), lambda: 'Invalid option : '+str(option) )
	datset = func()
	##############################
	### Slice code
	##############################
	if outpath is not None: outfile=datset_save(datset,outpath,outfile,infile,diagflg=diagflg)
	return(datset)

def datset_extend(infile,varlst,datset=None,dimlst=None,coords=None,outpath=None,outfile=None,callback=None,stashcode=None,refvar=None,ref_dim=None,indxkeys=None,indxfltr=None,attrlst=None,option=None,time_cnstlst=None,diagflg=0):
	if datset is None:
		datset=datset_extract(infile,varlst,dimlst=dimlst,coords=coords,outpath=outpath,outfile=outfile,callback=callback,stashcode=stashcode,option=option,time_cnstlst=time_cnstlst,diagflg=diagflg)
		#print("datset_extend time",datset["time"].attrs)
	else:
		if ref_dim is None:
			if refvar is None: refvar=xar_varlst(datset)[0]
			#if refvar is None: datset[1]
			ref_dim=xar_ref_dim(datset,refvar)
		datnew=datset_extract(infile,varlst,dimlst=dimlst,coords=coords,outpath=outpath,outfile=outfile,callback=callback,stashcode=stashcode,ref_dim=ref_dim,indxkeys=indxkeys,indxfltr=indxfltr,attrlst=indxfltr,option=option,time_cnstlst=time_cnstlst,diagflg=diagflg)
		#print("datnew time",datnew["time"].attrs)
		for varnam in varlst:
			datset.update({varnam:(dimlst,datnew[varnam])})
			#datset.update({varnam:(datnew[varnam].dims,datnew[varnam])})
			#for attrky,attrvl in datnew[varnam].attrs.items():
			datset[varnam].attrs.update(datnew[varnam].attrs)
				#attrkey = str(attrky)
				#attrval = str(attrvl)
				#datset[varnam].attrs[attrkey]=attrval
			#print("datnew in datset_extend",datnew[varnam].attrs)
                	#print("datset in datset_extend", datset[varnam].attrs)
	#print("datset in datset_extend",datset.attrs)
	return(datset)

def datset_append(infiles,recdim=None,varlst=None,dimlst=None,dimsize=None,reclen=None,recgap=None,recrds=None,datset=None,outpath=None,outfile=None,indxkeys=None,indxfltr=None,attrlst=None,coords=None,option=None,diagflg=0):
	if type(infiles) is list:
		filelst=infiles
	else:
		filelst=obslib.globlist(infiles)
	if reclen is None: reclen=len(filelst)
	for recpoint,file1 in enumerate(filelst):
		dat1=datset_extract(file1,varlst=varlst,dimlst=dimlst,coords=coords,indxkeys=indxkeys,indxfltr=indxfltr,attrlst=attrlst,option=option)
		datset=xar_append(dat1,reclen,recpoint,recdim,varlst=varlst,dimlst=dimlst,dimsize=dimsize,recrds=recrds,recgap=recgap,datset=datset)
	if outpath is not None: outfile=datset_save(datset,outpath,outfile,diagflg=diagflg)
	return(datset)

def pyg_append(infile,recdim=None,reclen=None,indxkeys=None,indxfltr=None,varlst=None,coords=None,dimlst=None,attrlst=None,datset=None,option=None):
	if type(infile) is list:
		filelst=infile
	else:
		filelst=obslib.globlist(infile)
	if reclen is None: reclen=len(filelst)
	for file1 in filelst:
		dat1=datset_extract(file1,indxkeys=indxkeys,indxfltr=indxfltr,varlst=varlst,coords=coords,dimlst=dimlst,attrlst=attrlst,option=option)
		datset=xar_append(dat1,reclen,recdim,varlst=varlst,dimlst=dimlst,dimsize=dimsize,recrds=recrds,recgap=recgap,datset=datset)
		
def datset_build(filepath,varfile,varlst,varstash,varopt,dimlst,indxkeys=None,indxfltr=None,attrlst=None,option=None,datset=None,filefldr=None):
	print(varfile,varlst,varstash,varopt)
	if varlst is None: varlst=list(varfile.keys())
	for varnam in varlst:
		if varnam in varfile:
			filenam=varfile[varnam]
		else:
			print("Filename information is not available for "+str(varnam))
		if varnam in varstash:
			stashcode=varstash[varnam]
		else:
			stashcode=None
		if varnam in varopt:
			option=varopt[varnam]
		else:
			option=option
		if filefldr is not None:
			infiles=filepath+"/"+filefldr+"/"+filenam
		else:
			infiles=filepath+"/"+filenam
		datset=datset_extend(infiles,[varnam],datset=datset,stashcode=stashcode,dimlst=dimlst,indxkeys=indxkeys,indxfltr=indxfltr,attrlst=attrlst,option=option)
	return(datset)


def coupled_pentad(files,varnam,dimlst,time_cnstlst):
	day=[]
	for i,(t1,t2) in enumerate(time):
        	data =[]
        	for file in files:
                	datset=essio.datset_extract(file,["precipitation_flux"],dimlst=["time","latitude","longitude"],time_cnstlst=[t1,t2])
                	print(rain_ctl)
               		datset_ex =datset.sel(longitude=slice(30,120),latitude=slice(-15,45))
	                datset_mean = datset_ex.mean(dim="time",keep_attrs=True)
	                out_ctl = plotdir+'/precipitation_mem1_16_'+str(t1)+'to'+str(t2)+'days_ctl.nc'
	                datset_day = datset_mean[varnam] * 86400
	                data.append(rain_ctl_day)
	                print("appended list for rain_ctl_day",data)
	        datset_day_c = xr.concat(data,dim = 'time')
	        print("concated list for rain_ctl_day",rain_ctl_day_c)
	        datset_day_mean = datset_day_c.mean(dim="time",keep_attrs=True)
	        day.append(datset_day_mean)
	print("appended in day_ctl",day)
	day_con = xr.concat(day,dim = 'time')
	print(day_con)
