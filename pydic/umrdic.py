#!/usr/bin/env python

"""
The initial version of this file is derived from the UMRider Package developed at NCMRWF by Arulalan and team.

Only dictionaries and static variable declarations of UMRider is available in this file. 

Seperate Package for UMRider is available at https://github.com/NCMRWF/UMRider

Static variables and dictionaries available below are from g2utils/um2grb2.py file of the UMRider package.

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

# -- Start importing necessary modules
import os, sys, time, subprocess, errno

__LPRINT__ = True
__utc__ = '00'
__UMReanalysis__ = False
__outFileType__ = 'ana'
# start and step hour in short forecast files
__anl_step_hour__ = 6
# start hour in long forecast files
__start_long_fcst_hour__ = 6
# step hour in long forecast files
__fcst_step_hour__ = 6
# maximum long forecast hours produced by model
__end_long_fcst_hour__ = 240
# analysis reference time applicable only to average/accumulation vars.
__anl_aavars_reference_time__ = 'shortforecast'
# analysis time bounds option applicable only to average/accumulation vars.
__anl_aavars_time_bounds__ = True
# grib1 file suffix
__grib1FilesNameSuffix__ = '.grib1'
# flag for removing grib2 files after grib1 has been converted 
__removeGrib2FilesAfterGrib1FilesCreated__ = False
# fill fully masked vars with this value.
__fillFullyMaskedVars__ = None

# Defining default out grib2 file name structure for analysis 
__anlFileNameStructure__ = ('um_ana', '_', '*HHH*', 'hr', '_', 
                            '*YYYYMMDD*', '_', '*ZZ*', 'Z', '.grib2')

# Defining default out grib2 file name structure for forecast                             
__fcstFileNameStructure__ = ('um_prg', '_', '*HHH*', 'hr', '_', 
                            '*YYYYMMDD*', '_', '*ZZ*', 'Z', '.grib2')
                            
# the _convertVars_ is global list which should has final variables list of 
# tuples (varName, varSTASH) will be converted, otherwise default variables 
# of this module will be converted!
_convertVars_ = []
_removeVars_ = []   # used to store temporary vars 
_current_date_ = None
_startT_ = None
_tmpDir_ = None
_inDataPath_ = None
_opPath_ = None
_doRegrid_ = False
_targetGrid_ = None
_targetGridFile_ = ''
_targetGridRes_ = None
_reverseLatitude_ = False
_requiredLat_ = None
_requiredLon_ = None
_requiredPressureLevels_ = []
_mdl2heights_ = []
_AGL_ = True
_preExtension_ = '_unOrdered'
_createGrib2CtlIdxFiles_ = True
_createGrib1CtlIdxFiles_ = False
_convertGrib2FilestoGrib1Files_ = False
__setGrib2TableParameters__ = None
__wgrib2Arguments__ = None
_extraPolateMethod_ = 'auto'
__UMtype__ = 'global'
_write2NetcdfFile_ = False
# By default __soilFirstSecondFixedSurfaceUnit__ takes as 'cm', suggested for
# WRF-Noah model. 
__soilFirstSecondFixedSurfaceUnit__ = 'cm'
# global ordered variables (the order we want to write into grib2)
_orderedVars_ = {'PressureLevel': [
## Pressure Level Variable names & STASH codes
###('x_wind', 'm01s15i243'),
###('y_wind', 'm01s15i244'),
###('wet_bulb_potential_temperature', 'm01s16i205'),
('geopotential_height', 'm01s16i202'),        
('x_wind', 'm01s15i201'),
('y_wind', 'm01s15i202'),
('upward_air_velocity', 'm01s15i242'),
('air_temperature', 'm01s16i203'),
('relative_humidity', 'm01s16i256'),
('specific_humidity', 'm01s30i205')],

## Model level variables
'ModelLevel': [
('x_wind', 'm01s00i002'),
('y_wind', 'm01s00i003'),
('upward_air_velocity','m01s00i150'),
('specific_humidity','m01s00i010'),
('mass_fraction_of_cloud_liquid_water_in_air','m01s00i254'),
('mass_fraction_of_cloud_ice_in_air','m01s00i012'),
('dimensionless_exner_function','m01s00i255'),
('air_temperature','m01s16i004'),
('air_pressure','m01s00i408'), # THETA levels
('air_pressure','m01s00i407'), # RHO levels
('air_potential_temperature','m01s00i004'),
('mass_fraction_of_dust_ukmo_division_2_dry_aerosol_in_air','m01s00i432'),
('mass_fraction_of_dust_ukmo_division_1_dry_aerosol_in_air','m01s00i431'),
#('m01s00i272','m01s00i272'),
('density_r_r_in_air','m01s00i253'),
#('m01s16i207','m01s16i207'),
('wet_bulb_temperature', 'm01s09i222'),
('potential_vorticity_of_atmosphere_layer', 'm01s15i217'),
('mass_concentration_of_dust_dry_aerosol_in_air', 'm01s17i257'),
('geopotential_height', 'm01s16i201'),
('dimensionless_exner_function', 'm01s00i406'),
('cloud_area_fraction_in_atmosphere_layer', 'm01s02i261'),
#('m01s16i206', 'm01s16i206'),
('direct_uv_flux_in_air', 'm01s01i212')],

## Non Pressure Level Variable names & STASH codes
'nonPressureLevel': [
('tropopause_altitude', 'm01s30i453'),
('tropopause_air_temperature', 'm01s30i452'),
('tropopause_air_pressure', 'm01s30i451'),
('surface_air_pressure', 'm01s00i409'),
('air_pressure_at_sea_level', 'm01s16i222'),
('surface_temperature', 'm01s00i024'),
('relative_humidity', 'm01s03i245'), 
('specific_humidity', 'm01s03i237'),
('air_temperature', 'm01s03i236'),
('dew_point_temperature', 'm01s03i250'),
('atmosphere_convective_available_potential_energy_wrt_surface', 'm01s05i233'), # CAPE
('atmosphere_convective_inhibition_wrt_surface', 'm01s05i234'), #CIN
('high_type_cloud_area_fraction', 'm01s09i205'),
('medium_type_cloud_area_fraction', 'm01s09i204'),
('low_type_cloud_area_fraction', 'm01s09i203'), 
('cloud_area_fraction_assuming_random_overlap', 'm01s09i216'),
('cloud_area_fraction_assuming_maximum_random_overlap', 'm01s09i217'),
('x_wind', 'm01s03i225'),  # 10meter B-Grid U component wind 
('y_wind', 'm01s03i226'),  # 10meter B-Grid V component wind
('x_wind', 'm01s15i212'),  # 50meter B-Grid U component wind 
('y_wind', 'm01s15i213'),  # 50meter B-Grid V component wind     
('x_wind_10m', 'm01s03i225'),  # 10meter B-Grid U component wind 
('y_wind_10m', 'm01s03i226'),  # 10meter B-Grid V component wind
('x_wind_50m', 'm01s15i212'),  # 50meter B-Grid U component wind 
('y_wind_50m', 'm01s15i213'),  # 50meter B-Grid V component wind     
('roughness_length_after_boundary_layer', 'm01s03i026'),
('visibility_in_air', 'm01s03i247'),
('precipitation_amount', 'm01s05i226'),
('stratiform_snowfall_amount', 'm01s04i202'),
('convective_snowfall_amount', 'm01s05i202'),
('stratiform_rainfall_amount', 'm01s04i201'),
('convective_rainfall_amount', 'm01s05i201'),
('rainfall_flux', 'm01s05i214'),
('snowfall_flux', 'm01s05i215'),
('precipitation_flux', 'm01s05i216'),
('atmosphere_mass_content_of_water', 'm01s30i404'),
('atmosphere_mass_content_of_dust_dry_aerosol_particles', 'm01s30i403'),
('atmosphere_cloud_liquid_water_content', 'm01s30i405'),
('atmosphere_cloud_ice_content', 'm01s30i406'),
('fog_area_fraction', 'm01s03i248'),
('toa_incoming_shortwave_flux', 'm01s01i207'), 
('toa_outgoing_shortwave_flux', 'm01s01i205'),
('toa_outgoing_shortwave_flux_assuming_clear_sky', 'm01s01i209'),  
('toa_outgoing_longwave_flux', 'm01s02i205'),
('toa_outgoing_longwave_flux_assuming_clear_sky', 'm01s02i206'),   
('surface_upward_latent_heat_flux', 'm01s03i234'),
('surface_upward_sensible_heat_flux', 'm01s03i217'),
('surface_downwelling_shortwave_flux_in_air', 'm01s01i235'),
('surface_downwelling_longwave_flux', 'm01s02i207'),
('surface_downwelling_longwave_flux_in_air', 'm01s01i238'),
('surface_net_downward_longwave_flux', 'm01s02i201'), 
('surface_net_downward_shortwave_flux', 'm01s01i202'),
('atmosphere_boundary_layer_thickness', 'm01s00i025'),
('atmosphere_optical_thickness_due_to_dust_ambient_aerosol', 'm01s02i422'),
('moisture_content_of_soil_layer', 'm01s08i223'),  # 4 layers 
# single layer, this must be after 4 layers as in order 
('soil_moisture_content', 'm01s08i208'),       # single layer  
## though moisture_content_of_soil_layer and volumetric_moisture_of_soil_layer
## has same STASH code, but we must include seperate entry here.
('volumetric_moisture_of_soil_layer', 'm01s08i223'), # 4 layers
# single layer, this must be after 4 layers as in order 
('volumetric_moisture_of_soil_layer', 'm01s08i208'), # single layer
('soil_temperature', 'm01s03i238'),  
('land_binary_mask', 'm01s00i030'),
('sea_ice_area_fraction', 'm01s00i031'),
('sea_ice_thickness', 'm01s00i032'),
('snowfall_amount', 'm01s00i023'),
# the snowfall_amount might be changed as 
# liquid_water_content_of_surface_snow by convert it into
# water equivalent of snow amount, before re-ordering itself.
('liquid_water_content_of_surface_snow', 'm01s00i023'),
# IMDAA reanalysis extra variables other than NCUM 
('stratiform_snowfall_rate', 'm01s04i204'),
('soil_evaporation_rate', 'm01s03i296'),
('canopy_evaporation_rate', 'm01s03i297'),
('direct_surface_shortwave_flux_in_air', 'm01s01i215'),
('surface_downwelling_longwave_flux_assuming_clear_sky', 'm01s02i208'),
('open_sea_evaporation_rate', 'm01s03i232'),
('very_low_type_cloud_area_fraction', 'm01s09i202'),
('cloud_base_altitude', 'm01s09i219'),
('convective_rainfall_rate', 'm01s05i205'),
('convective_snowfall_flux', 'm01s05i206'),
('stratiform_rainfall_rate', 'm01s04i203'),
('subsurface_runoff_flux', 'm01s08i235'),
('surface_diffuse_downwelling_shortwave_flux_in_air', 'm01s01i216'),
('surface_downwelling_shortwave_flux_in_air_assuming_clear_sky', 'm01s01i210'),
('surface_net_downward_shortwave_flux', 'm01s01i201'),
('downward_heat_flux_in_soil', 'm01s03i202'),
('surface_roughness_length', 'm01s00i026'),
('surface_runoff_flux', 'm01s08i234'),
('surface_upward_water_flux', 'm01s03i223'),
('surface_upwelling_shortwave_flux_in_air_assuming_clear_sky', 'm01s01i211'),
('wind_speed_of_gust', 'm01s03i463'),
('surface_net_downward_shortwave_flux_corrected', 'm01s01i202'),
('soil_temperature', 'm01s08i225'),
('ligtning_flash_count', 'm01s21i104'),
('radar_reflectivity', 'm01s04i112'),
# the below one is for orography which presents only in analysis file.
# so we must keep this as the last one in the ordered variables!
('surface_altitude', 'm01s00i033'),
('surface_geopotential_height', 'm01s00i033') # this is orography, but 
# some model requires orography has to be written in gpm unit.
],
}
  
    
#Define _precipVars_
# The following vars should contains only precipitation, rainfall, snow 
# variables, those whose regrid extrapolate should be only in 'linear' mode
# and not in 'mask' mode, and should not have -ve values.
_precipVars_ = [('precipitation_amount', 'm01s05i226'),
              ('stratiform_snowfall_amount', 'm01s04i202'),
              ('convective_snowfall_amount', 'm01s05i202'),
              ('stratiform_rainfall_amount', 'm01s04i201'),
              ('convective_rainfall_amount', 'm01s05i201'),
              ('rainfall_flux', 'm01s05i214'),
              ('snowfall_flux', 'm01s05i215'),
              ('precipitation_flux', 'm01s05i216')]

# Define _accumulationVars_
# The following variables should be 6-hourly accumulated, but model
# produced as 1-hourly accumulation. So we need to sum of 6-hours data to 
# get 6-hourly accumulation.
# rainfall_flux, snowfall_flux, precipitation_flux are not accumulated 
# vars, since those are averaged rain rate (kg m-2 s-1). 
# But the following vars unit is (kg m-2), accumulated vars.  
_accumulationVars_ = [('precipitation_amount', 'm01s05i226'),
                      ('stratiform_snowfall_amount', 'm01s04i202'),
                      ('convective_snowfall_amount', 'm01s05i202'),
                      ('stratiform_rainfall_amount', 'm01s04i201'),
                      ('convective_rainfall_amount', 'm01s05i201')]                      

## Define _ncfilesVars_
## the following variables need to be written into nc file, initially for 
## some reason (like either it may contain soil_model_level_number or 
## duplicate grib param where typeOfFirstFixedSurface [i.e toa, tropopause]
## is not implemented yet), but at the end of the program (after re-ordering)
## these intermediate nc files will be deleted automatically! 
## while storing into nc file, there wont be much problem and reading from
## nc file also wont be problem to load cf_standard_name into cube and 
## followed by storing into grib2 file. All because we need to write variables
## in the way we need (i.e. ordered always)!!
_ncfilesVars_ = [
### Debug by Gibies using seperate grib file to avoid NetCDF
#('volumetric_moisture_of_soil_layer', 'm01s08i223'), 
# 'moisture_content_of_soil_layer' renamed as  
# 'volumetric_moisture_of_soil_layer', but same STASH m01s08i223 code.
#('volumetric_moisture_of_soil_layer', 'm01s08i208'), 
# 'soil_moisture_content' renamed as  
# 'volumetric_moisture_of_soil_layer', but same STASH m01s08i208 code.
#('soil_temperature', 'm01s08i225'), 
#('soil_temperature', 'm01s03i238'),
#('toa_incoming_shortwave_flux', 'm01s01i207'),
#('toa_outgoing_longwave_flux', 'm01s02i205'),
#('toa_outgoing_shortwave_flux', 'm01s01i205'),
('tropopause_altitude', 'm01s30i453'),
('tropopause_air_temperature', 'm01s30i452'),
('tropopause_air_pressure', 'm01s30i451'),
('surface_net_downward_shortwave_flux_corrected', 'm01s01i202'),
('atmosphere_optical_thickness_due_to_dust_ambient_aerosol', 'm01s02i422'),
('atmosphere_mass_content_of_dust_dry_aerosol_particles', 'm01s30i403'),
# surface_temperature grib code is same as air_temperature (for the purpose 
# of OSF, Hycom requirements). So while reading surface_temperature variable 
# from grib2 will make confusion along with air_temperature. To avoid this
# confusion, lets write this variable in nc seperate file.
#('surface_temperature', 'm01s00i024'),
]



                 
## Define _ncmrGrib2LocalTableVars_
## the following variables need to be set localTableVersion no as 1 and
## master table version no as 255 (undefined), since WRF grib2 table doesnt
## support for the following variables. So we created our own local table.
_ncmrGrib2LocalTableVars_ = [
        'fog_area_fraction',
        'soil_evaporation_rate', 
        'canopy_evaporation_rate', 
        'open_sea_evaporation_rate', 
        'density_r_r_in_air',    
        'surface_net_downward_shortwave_flux_corrected',
        'direct_uv_flux_in_air', 
        'surface_downwelling_shortwave_flux_in_air_assuming_clear_sky', 
        'surface_upwelling_shortwave_flux_in_air_assuming_clear_sky'
        'toa_outgoing_shortwave_flux_assuming_clear_sky',
        'toa_outgoing_longwave_flux_assuming_clear_sky',   
        'surface_downwelling_longwave_flux_assuming_clear_sky', 
        'atmosphere_optical_thickness_due_to_dust_ambient_aerosol',
        'atmosphere_mass_content_of_dust_dry_aerosol_particles',
        'very_low_type_cloud_area_fraction', 
        'cloud_area_fraction_assuming_random_overlap',
        'cloud_area_fraction_assuming_maximum_random_overlap',
        'subsurface_runoff_flux', 
        'surface_upward_water_flux', 
        'downward_heat_flux_in_soil', 
        'cloud_volume_fraction_in_atmosphere_layer'
        'liquid_cloud_volume_fraction_in_atmosphere_layer'
        'ice_cloud_volume_fraction_in_atmosphere_layer',
        'ligtning_flash_count',
        'radar_reflectivity',
        'roughness_length_after_boundary_layer',] 


_short_name_ = {
    'convective_rainfall_amount': 'ACPCP',
    'convective_snowfall_amount': 'SNOC',
    'precipitation_amount': 'APCP',
    'stratiform_rainfall_amount': 'NCPCP',
    'stratiform_snowfall_amount': 'SNOL',
    'convective_rainfall_rate': 'CPRAT',
    'stratiform_rainfall_rate': 'LSPRATE',
    'stratiform_snowfall_rate': 'LSSRATE',
    'convective_snowfall_flux': 'CSRATE',
    'snowfall_amount': 'TSNOWP',
    'direct_surface_shortwave_flux_in_air': 'DSSWRFLX',
    'surface_diffuse_downwelling_shortwave_flux_in_air': 'DIFSSWRF',
    'surface_net_downward_shortwave_flux_corrected': 'NDDSWRFC',
    'toa_outgoing_shortwave_flux_assuming_clear_sky': 'CSUSFT',
    'toa_outgoing_longwave_flux_assuming_clear_sky': 'CSULFT',
    'surface_upwelling_shortwave_flux_in_air_assuming_clear_sky': 'CSUSFS',
    'surface_downwelling_shortwave_flux_in_air_assuming_clear_sky': 'CSDSFS',
    'surface_downwelling_longwave_flux_assuming_clear_sky': 'CSDLFS',
    'moisture_content_of_soil_layer': 'SOILM',
    'soil_temperature': 'TSOIL',
    'downward_heat_flux_in_soil': 'DSHFLUX',    
    'roughness_length_after_boundary_layer': 'ROHLENABL',

    }


## Define _maskOverOceanVars_
## the following variables need to be set mask over ocean because the original
## model itself producing mask over ocean. but when we are doing regrid it 
## couldnt retain the mask ! dont know why ! So using land_binary_mask 
## variable, we are resetting mask over ocean for the following vars.
_maskOverOceanVars_ = ['moisture_content_of_soil_layer', 
        'soil_moisture_content', 'volumetric_moisture_of_soil_layer', 
        # 'moisture_content_of_soil_layer' and 'soil_moisture_content' are 
        # renamed as  'volumetric_moisture_of_soil_layer', 
        # but same STASH m01s08i223 and m01s08i208 code.
                 'soil_temperature'] # # this line is must to run WRF-Noah
 
## Define dust aerosol optical thickness of model pseudo level with its 
## corresponding micron / micro wavelength. We need to tweak with following 
## information before writing into final grib2 file.
_aod_pseudo_level_var_ = {
'atmosphere_optical_thickness_due_to_dust_ambient_aerosol': [
(1, '0.38'), (2, '0.44'), (3, '0.55'), (4, '0.67'), (5, '0.87'), (6, '1.02')]}

## Define _depedendantVars_ where A is key, B is value. A is depedendant on B,
## B is not. B not necessarily to be written in out file. User may just specify
## only A in var.cfg configure file.
_depedendantVars_ = {
# land_binary_mask is needed to set ocean mask 
('volumetric_moisture_of_soil_layer', 'm01s08i208'): [('land_binary_mask', 'm01s00i030')],
('moisture_content_of_soil_layer', 'm01s08i208'): [('land_binary_mask', 'm01s00i030')],
('soil_temperature', 'm01s03i238'): [('land_binary_mask', 'm01s00i030')],
# need to calculate surface up sw/lw using surface down & net sw/lw fluxes
('surface_upwelling_shortwave_flux_in_air', 'None'): [
                 ('surface_net_downward_shortwave_flux', 'm01s01i202'),
                 ('surface_downwelling_shortwave_flux_in_air', 'm01s01i235')],
                 
('surface_upwelling_longwave_flux_in_air', 'None'): [
                        ('surface_net_downward_longwave_flux', 'm01s02i201'), 
                        ('surface_downwelling_longwave_flux', 'm01s02i207')],

('atmosphere_precipitable_water_content', 'None'): [
    ('atmosphere_mass_content_of_water', 'm01s30i404'),
    ('atmosphere_mass_content_of_dust_dry_aerosol_particles', 'm01s30i403'),
    ('atmosphere_cloud_liquid_water_content', 'm01s30i405'),
    ('atmosphere_cloud_ice_content', 'm01s30i406'),    
    ],

('surface_geopotential_height', 'm01s00i033'): [('surface_altitude', 'm01s00i033')],

('upward_air_velocity_in_pascal', 'm01s15i242'): [
                                ('upward_air_velocity', 'm01s15i242'),
                                ('air_temperature', 'm01s16i203')]
}
                                            



