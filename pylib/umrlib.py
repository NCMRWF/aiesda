#!/usr/bin/env python

"""
The initial version of this file is derived from the UMRider Package developed at NCMRWF by Arulalan and team.

Only some of the general use library functions of UMRider is available in this file. 

Seperate Package for UMRider is available at https://github.com/NCMRWF/UMRider

Functions available below are from g2utils/um2grb2.py file of the UMRider package

__author__ = 'arulalant'
__version__ = 'v3.1.0'
__long_name__ = 'NCUM Parallel Rider'

References:
1. Iris. v1.8.1 03-Jun-2015. Met Office. UK. https://github.com/SciTools/iris/archive/v1.8.1.tar.gz

2. Saji M. (2014), "Utility to convert UM fieldsfile output to NCEP GRIB1 format:
                    A User Guide", NMRF/TR/01/2014, April 2014, pp. 51, available at
                    http://www.ncmrwf.gov.in/umfld2grib.pdf

Disclaimers (if any!)
This is just test code as of now and is meant for a specific purpose only!

Copyright: ESSO-NCMRWF, MoES, 2015-2016, 2016-2017.

Author : Arulalan.T
previous Update : 11-Mar-2016
latest Update : 29-Aug-2016
"""
import os,sys
CURR_PATH=os.path.dirname(os.path.abspath(__file__))
PKGHOME=os.path.dirname(CURR_PATH)
LIB=os.environ.get('LIB',PKGHOME+"/pylib")
sys.path.append(LIB)
DIC=os.environ.get('DIC',PKGHOME+"/pydic")
sys.path.append(DIC)
NML=os.environ.get('NML',PKGHOME+"/nml")
sys.path.append(NML)
import umrdic
import multiprocessing as mp
import multiprocessing.pool as mppool       

_soilFirstSecondFixedSurfaceUnit__ = umrdic.__soilFirstSecondFixedSurfaceUnit__


def getCubeAttr(tmpCube):
    """
    This module returns basic coordinate & attribute info about any Iris data cube.
    :param tmpCube: a temporary Iris cube containing a single geophysical field/parameter
    :return: stdNm: CF-compliant Standard name of the field/parameter
    :return: fcstTm: forecast time period for eg: 00, 06, 12 etc -- units as in hours
    :return: refTm: reference time -- units as date  in Gregorian
    :return: lat as scalar array (1D) units as degree (from 90S to 90N)
    :return: lon as scalar array (1D) units as degree (from 0E to 360E)
    Original by MNRS
    """
    stdNm = tmpCube.standard_name
    stdNm = stdNm if stdNm else tmpCube.long_name
    stash = str(tmpCube.attributes['STASH'])
    fcstTm = tmpCube.coord('forecast_period')
    refTm = tmpCube.coord('forecast_reference_time')
    lat = tmpCube.coord('latitude')
    lon = tmpCube.coord('longitude')

    return stdNm, stash, fcstTm, refTm, lat, lon

# create a class #2 to initiate mp daemon processes
class _NoDaemonProcess(mp.Process):
    # make 'daemon' attribute always return False
    # A class created by AAT
    def _get_daemon(self):
        return False
    def _set_daemon(self, value):
        pass
    daemon = property(_get_daemon, _set_daemon)
# end of class #2

# create a class #3 to set-up worker-pools
class _MyPool(mppool.Pool):
    # We sub-class multiprocessing.pool. Pool instead of multiprocessing.Pool
    # because the latter is only a wrapper function, not a proper class.
    ### http://stackoverflow.com/questions/6974695/python-process-pool-non-daemonic
    ### refer the above link to invoke child processes
    # A class created by AAT
    Process = _NoDaemonProcess
# end of class #3

def _createDepthBelowLandSurfaceCoords1Lev(cube):
    # Dr. Saji / UM_Model_DOC suggested that UM produce Root zone soil model
    # level number is equivalent to 0 to 2m. (i.e. from 1 to 4 layer no)
    
    global __soilFirstSecondFixedSurfaceUnit__ 

    if __soilFirstSecondFixedSurfaceUnit__ == 'cm':
        # So we kept here unit as 'cm'. But points are muliplied by
        # 100 with its  corresponding cm values. Why because, that 
        # 100 will be factorized (divied) in grib_message by setting 
        # scaleFactorOfFirstFixedSurface as 2 and 
        # scaleFactorOfFirstFixedSurface as 2. So we must follow 
        # Lets create new coords with 0, 2m infomation.   
        depth_below_land_surface = iris.coords.DimCoord(numpy.array([15000]), 
                         bounds=numpy.array([[0, 30000]]), units=Unit('cm'),
                                       long_name='depth_below_land_surface')
    elif __soilFirstSecondFixedSurfaceUnit__ == 'mm':  
        # We kept here unit as 'mm'. But points are muliplied by
        # 1000 with its  corresponding cm values. Why because, that 
        # 1000 will be factorized (divied) in grib_message by setting 
        # scaleFactorOfFirstFixedSurface as 3 and 
        # scaleFactorOfSecondFixedSurface as 3. So we must follow 
        # this procedure to get correct results.

        # Lets create new coords with 0, 3m infomation.   
        depth_below_land_surface = iris.coords.DimCoord(numpy.array([1500000]), 
                          bounds=numpy.array([[0, 3000000]]), units=Unit('mm'), 
                                        long_name='depth_below_land_surface')    
    else:
        return 
    # end of if __soilFirstSecondFixedSurfaceUnit__ == 'cm':
        
    # add the above created new coords to the cube 
    cube.add_aux_coord(depth_below_land_surface)    
# end of def _createDepthBelowLandSurfaceCoords1Lev():

def _updateDepthBelowLandSurfaceCoords4Levs(depth_below_land_surface):
    # Dr. Saji / UM_Model_DOC suggested that UM produce soil model
    # level number is equivalent to 10cm, 35cm, 1m & 2m. 
    
    global __soilFirstSecondFixedSurfaceUnit__ 

    if __soilFirstSecondFixedSurfaceUnit__ == 'cm':
        # So we kept here unit as 'cm'. But points are muliplied by
        # 100 with its  corresponding cm values. Why because, that 
        # 100 will be factorized (divied) in grib_message by setting 
        # scaleFactorOfFirstFixedSurface as 2 and 
        # scaleFactorOfFirstFixedSurface as 2. So that in grib2 will
        # be able to read as 0.1 m, 0.35m, 1m & 2m. Iris will convert 
        # cm to m while saving into grib2 file. So we must follow 
        # this procedure to get correct results. (tested and suggested for 
        # WRF-Noah model input)
        
        # 1000 cm -> 10 m -> 10 m / 100 (scaleFactorOfFirstFixedSurface = 2) -> 0.1 m
        # 3500 cm -> 35 m -> 35 m / 100 (scaleFactorOfSecondFixedSurface = 2) -> 0.35 m
        # 10000 cm -> 100 m -> 100 m / 100 (scaleFactorOfSecondFixedSurface = 2) -> 1.0 m
        # 30000 cm -> 300 m -> 300 m / 100 (scaleFactorOfSecondFixedSurface = 2) -> 3.0 m
        
        depth_below_land_surface.points = numpy.array([500, 2250, 6750, 20000])
        # we must set the bounds in vertical depths, since we required
        # to mention the four different layers depth properly.
        depth_below_land_surface.bounds = numpy.array([[0, 1000], 
                                   [1000, 3500], [3500,10000],[10000,30000]])
        depth_below_land_surface.units = Unit('cm')
    elif __soilFirstSecondFixedSurfaceUnit__ == 'mm':
        # Here we kept unit as 'mm'. But points are muliplied by
        # 1000 with its  corresponding mm values. Why because, that 
        # 1000 will be factorized (divied) in grib_message by setting 
        # scaleFactorOfFirstFixedSurface as 3 and 
        # scaleFactorOfSecondFixedSurface as 3. So that in grib2 will
        # be able to read as 0.1m, 0.35m, 1m & 3m. Iris will convert 
        # mm to m while saving into grib2 file. So we must follow 
        # this procedure to get correct results.
        # Moreover IMD-MFI model required to be scaling range of 100000. So we 
        # must follow this procedure only (i.e. mm to m conversion and not cm to m conversion) 
        
        # 100000 mm -> 100 m -> 100 m / 1000 (scaleFactorOfFirstFixedSurface = 3) -> 0.1 m
        # 350000 mm -> 350 m -> 350 m / 1000 (scaleFactorOfSecondFixedSurface = 3) -> 0.35 m
        # 1000000 mm -> 1000 m -> 1000 m / 1000 (scaleFactorOfSecondFixedSurface = 3) -> 1.0 m
        # 3000000 mm -> 3000 m -> 3000 m / 1000 (scaleFactorOfSecondFixedSurface = 3) -> 3.0 m
        
        depth_below_land_surface.points = numpy.array([50000, 225000, 675000, 2000000])
        # we must set the bounds in vertical depths, since we required
        # to mention the four different layers depth properly.
        depth_below_land_surface.bounds = numpy.array([[0, 100000], 
                           [100000, 350000], [350000,1000000],[1000000,3000000]])
        depth_below_land_surface.units = Unit('mm')
    # end of if __soilFirstSecondFixedSurfaceUnit__ == 'cm':
    
    depth_below_land_surface.long_name = 'depth_below_land_surface'    
    depth_below_land_surface.standard_name = 'depth'
# end of def _updateDepthBelowLandSurfaceCoords4Levs():

def _convert2VolumetricMoisture(cube, levels=[100.0, 250.0, 650.0, 2000.0]):
    #### Lets convert moisture_content_of_soil_layer into 
    ##  volumetric_moisture_of_soil_layer by divide each layer 
    ## with its layer depth in mm.
    ## Unit also gets changed from Kg/m2 into m3/m3. How ?
    ## voulumetric_soil_moisture = moisture_content_of_soil_layer / (density_of_water x depth_of_soil_layer)
    ## density_of_water is 1000 Kg/m3
    ## depth_of_soil_layer of first layer from 0 to 10 cm = 10/100 m
    ## depth_of_soil_layer of first layer from 10 to 35 cm = 25/100 m
    ## depth_of_soil_layer of first layer from 35 to 100 cm = 65/100 m
    ## depth_of_soil_layer of first layer from 100 to 300 cm = 200/100 m
    
    ## So if we apply the above values of density 1000 Kg/m3 
    ## & depth in meter in the denominator of voulumetric_soil_moisture
    ## equavation, we will endup with just divide first layer 
    ## by 100, second layer by 250, third layer by 650 and 
    ## fourth layer by 2000.
    
    ## By this way, we converted moisture_content_of_soil_layer 
    ## from Kg/m2 into volumetric_soil_moisture_of_layer m3/m3.
    
    ## Reference : "Comparison of the Met Office soil moisture
    ## analyses with SMOS retrievals (2010-2011)", MARCH 2013.
    
    ## Link : http://www.researchgate.net/publication/257940913
    
    print "before volumetirc", cube.data.min(), cube.data.max()
    if isinstance(levels, (list, tuple)):   
        # This block of code for 4 different layers 
        for idx, dval in enumerate(levels):
            cube.data[idx] /= dval
    elif isinstance(levels, float):
        # this block of code for single layer 
        cube.data /= levels
    # end of for idx, denominator in enumerate([...]):
    print "after volumetirc", cube.data.min(), cube.data.max()
    # WRF-WPS requires minimum vlaue as 0.005. If it is < 0.005 then 
    # Noah thorws segmentation error due to low value of soil moisture. 
    # Reference : look at the lines from 1219 t0 1260 in the below link
    # http://www.cisl.ucar.edu/staff/huangwei/WRFV3/dyn_em/module_initialize_real.F.html
    # though the above Noah code replace the <0.005 grid values with 0.005,
    # but it does only for the first time step (say analysis 00hr), and then 
    # model will blow up for the next time step (say forecast 06hr).
    # And either we should do mask grid points < 0.005 or replace with 0.0051.
    # Here we are replacing with 0.0051 since soil moisture masking will not 
    # make proper sense!. so replace the values less than 0.005 with 0.0051.
    cube.data[numpy.ma.logical_and(cube.data > 0.0, cube.data < 0.005)] = 0.0051
    
    # update the units as m3 / m3
    cube.units = Unit('m3 m-3')
    # make sure that standard_name as None, so that it will  
    # not messup with units while writing as grib2. 
    cube.standard_name = None
    # set long name as volumetric_moisture_of_soil_layer, 
    # though its not standard cf name, I made it as 
    # understandable long name which points into volumetirc 
    # grib2 param code in _grib_cf_map.py.
    cube.long_name = 'volumetric_moisture_of_soil_layer'        
# end of def _convert2VolumetricMoisture(cube):

def _convert2WEASD(cube):
    # http://www.nrcs.usda.gov/wps/portal/nrcs/detail/or/snow/?cid=nrcs142p2_046155
    if cube.standard_name == 'snowfall_amount':
        cube.standard_name = 'liquid_water_content_of_surface_snow'
        # convert the snow amount data to water equivalent by divide by 10 or 
        # multiply by 0.1.
        # reference link : look above        
        cube.data *= 0.1 
    # end of if cube.standard_name == 'snowfall_amount':
# end of def _convert2WEASD(cube):

    
def renameVar(cube, varName, varSTASH):
    if (varName, varSTASH) in [
		('x_wind', 'm01s03i225'), # 10meter B-Grid U component wind
			]: 
		cube.long_name = 'zonal wind at 10 m height'
    if (varName, varSTASH) in [
		('y_wind', 'm01s03i226'), # 10meter B-Grid V component wind
			]: cube.long_name = 'meridional wind at 10 m height'
    if (varName, varSTASH) in [
		('x_wind', 'm01s15i212'),  # 50meter B-Grid U component wind 
			]: cube.long_name = 'zonal wind at 50 m height'
    if (varName, varSTASH) in [
		('y_wind', 'm01s15i213'),  # 50meter B-Grid V component wind     
			]: cube.long_name = 'meridional wind at 50 m height'
    print(varName, varSTASH, cube.standard_name, cube.long_name)
    return(cube)


def tweaked_messages(cubeList):
    global _ncmrGrib2LocalTableVars_, _aod_pseudo_level_var_, __UMtype__, \
           __setGrib2TableParameters__, __soilFirstSecondFixedSurfaceUnit__           
    
    for cube in cubeList:
        for cube, grib_message in iris.fileformats.grib.as_pairs(cube): #save_pairs_from_cube(cube):
            print "Tweaking begin ", cube.standard_name
            # post process the GRIB2 message, prior to saving
            gribapi.grib_set_long(grib_message, "centre", 29) # RMC of India
            gribapi.grib_set_long(grib_message, "subCentre", 0) # No subcentre
            print "reset the centre as 29"
            if cube.coord("forecast_period").bounds is not None:        
                # if we set bounds[0][0] = 0, wgrib2 gives error for 0 fcst time.
                # so we need to set proper time intervals 
                # (typeOfTimeIncrement) as 2 as per below table.
                # http://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_table4-11.shtml
                # fileformats/grib/_save_rules.py-> set_forecast_time() ->
                # _non_missing_forecast_period() returns 'fp' as bounds[0][0]. 
                # but mean while lets fix by setting typeOfTimeIncrement=2.
                # http://www.cosmo-model.org/content/model/documentation/grib/pdtemplate_4.11.htm 
                gribapi.grib_set(grib_message, "typeOfTimeIncrement", 2)           
                print 'reset typeOfTimeIncrement as 2 for', cube.standard_name
                
                if __UMtype__ == 'regional':
                    # fixing floating precesion point problem
                    forecast_period = cube.coords('forecast_period')[0]
                    forecast_period.points = numpy.round(forecast_period.points, 3)
                    forecast_period.bounds = numpy.round(forecast_period.bounds, 3)
                    print "forecast_period = ", forecast_period
                # end of if __UMtype__ == 'regional':
                
            # end of if cube.coord("forecast_period").bounds is not None:
            if cube.coords('depth_below_land_surface') or cube.coords('depth'):                
                if __soilFirstSecondFixedSurfaceUnit__ == 'cm':
                    # scaleFactorOfFirstFixedSurface as 2, equivalent to divide
                    # the depth_below_land_surface.points by 100. So that we can 
                    # be sure that grib2 has 0.1m, 0.35m, 1m & 3m. Otherwise, we 
                    # will endup with 0m, 0m, 1m & 3m and finally will loose 
                    # information about decimal values of levels.
                    gribapi.grib_set(grib_message, "scaleFactorOfFirstFixedSurface", 2)
                    gribapi.grib_set(grib_message, "scaleFactorOfSecondFixedSurface", 2)
                    print "reset scaleFactorOfFirstFixedSurface as 2"
                    print "reset scaleFactorOfSecondFixedSurface as 2"
                elif __soilFirstSecondFixedSurfaceUnit__ == 'mm':
                    # scaleFactorOfFirstFixedSurface as 3, equivalent to divide
                    # the depth_below_land_surface.points by 1000. So that we can 
                    # be sure that grib2 has 0.1m, 0.35m, 1m & 3m. Otherwise, we 
                    # will endup with 0m, 0m, 1m & 3m and finally will loose 
                    # information about decimal values of levels.
                    gribapi.grib_set(grib_message, "scaleFactorOfFirstFixedSurface", 3)
                    gribapi.grib_set(grib_message, "scaleFactorOfSecondFixedSurface", 3)
                    print "reset scaleFactorOfFirstFixedSurface as 3"
                    print "reset scaleFactorOfSecondFixedSurface as 3"
                # end of if __soilFirstSecondFixedSurfaceUnit__ == 'cm':
            # end of if cube.coords('depth_below_land_surface'):    
            if cube.standard_name or cube.long_name:
                if cube.standard_name:
                    loc_longname = None
                    if cube.standard_name.startswith('air_pressure_at_sea_level'):
                        # we have to explicitly re-set the type of first fixed
                        # surfcae as Mean sea level (101)
                        gribapi.grib_set(grib_message, "typeOfFirstFixedSurface", 101) 
                    if cube.standard_name.startswith('toa'):
                        # we have to explicitly re-set the type of first surfcae
                        # as Nominal top of the atmosphere i.e. 8 (WMO standard)
                        gribapi.grib_set(grib_message, "typeOfFirstFixedSurface", 8) 
                    # end of if cube.standard_name.startswith('toa'): 
                    if cube.standard_name.startswith('tropopause'):
                        # we have to explicitly re-set the type of first surfcae
                        # as tropopause i.e. 7 (WMO standard)
                        gribapi.grib_set(grib_message, "typeOfFirstFixedSurface", 7) 
                    # end of if cube.standard_name.startswith('tropopause'): 
                # end of if cube.standard_name:

                if cube.long_name: 
                    aod_name = _aod_pseudo_level_var_.keys()[0]
                    if cube.long_name.startswith(aod_name):
                        # we have to explicitly re-set the type of first surfcae
                        # as surfaced (1) and type of second fixed surface as 
                        # tropopause (7) as per WMO standard, for the aod var.
                        gribapi.grib_set(grib_message, "typeOfFirstFixedSurface", 1)
                        gribapi.grib_set(grib_message, "typeOfSecondFixedSurface", 7) 
                        print "Set typeOfFirstFixedSurface as 1 and typeOfSecondFixedSurface as 7 to aod"
                    # end of if cube.long_name.startswith(aod_name):
                    # check for long name in _ncmrGrib2LocalTableVars_
                    loc_longname = [1 for lname in _ncmrGrib2LocalTableVars_ if cube.long_name.startswith(lname)]
                # end of if cube.long_name: 
                
                # here str conversion is essential to avoid checking 'cloud' in None
                # (for long_name in some case), which will throw error.
                if 'cloud' in str(cube.standard_name) or 'cloud' in str(cube.long_name) or 'ligtning' in str(cube.long_name):
                    # we have to explicitly re-set the type of first surfcae
                    # as surfaced (1) and type of second fixed surface as 
                    # as Nominal top of the atmosphere i.e. 8 (WMO standard)
                    gribapi.grib_set(grib_message, "typeOfFirstFixedSurface", 1)
                    gribapi.grib_set(grib_message, "typeOfSecondFixedSurface", 8) 
                # end of if 'cloud' in cube.long_name or 'cloud':
                
                if cube.standard_name in _ncmrGrib2LocalTableVars_ or loc_longname:
                    # We have to enable local table version and disable the 
                    # master table only the special variables.
                    # http://www.cosmo-model.org/content/model/documentation/grib/grib2keys_1.htm 
                    # Above link says that tablesVersion must be set to 255, 
                    # then only local table will be enabled.
                    gribapi.grib_set_long(grib_message, "tablesVersion", 255)
                    # http://apt-browse.org/browse/debian/wheezy/main/i386/libgrib-api-1.9.16/1.9.16-2%2Bb1/file/usr/share/grib_api/definitions/grib2/section.1.def (line no 42)
                    # Above link says versionNumberOfGribLocalTables is alias 
                    # of LocalTablesVersion.        
                    # Set local table version number as 1 as per 
                    # ncmr_grib2_local_table standard.
                    gribapi.grib_set_long(grib_message, "versionNumberOfGribLocalTables", 1)
                # end of if cube.standard_name in _ncmrGrib2LocalTableVars_:
            # end of if cube.standard_name or ...:
            if __setGrib2TableParameters__:
                # This user defined parameters must be at last of this function!
                for key, val in __setGrib2TableParameters__:
                    gribapi.grib_set_long(grib_message, key, val)
                    print "set user defined grib2table parameter ('%s', %s)" % (key, val)
            # end of if __setGrib2TableParameters__:
            print "Tweaking end ", cube.standard_name
            
            yield grib_message
        # end of for cube, grib_message in iris.fileformats.grib.save_pairs_from_cube(cube):
    # end of for cube in cubeList:
# end of def tweaked_messages(cube):



def substringcheck(string, sub_str):
    if (string.find(sub_str) == -1):
        result=False
    else:
        result=True
    return(result)

def rename_gribvar(name,fpath):
    if substringcheck(fpath,"toa"):
	name=name.replace("surface_downwelling_shortwave_flux_in_air","toa_incoming_shortwave_flux")
	name=name.replace("surface_upwelling_longwave_flux_in_air","toa_outgoing_longwave_flux")
	name=name.replace("surface_net_downward_shortwave_flux","toa_outgoing_shortwave_flux")
	#name=name.replace("surface_upwelling_shortwave_flux_in_air","toa_outgoing_shortwave_flux")
	#name=name.replace("surface_net_downward_shortwave_flux","toa_net_downward_shortwave_flux")
	name=name.replace("surface","toa")
    if substringcheck(fpath,"skin"):
	name=name.replace("air_temperature","surface_temperature")
    return(name)

################################################################################################
###
################################################################################################

