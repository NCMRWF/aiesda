#! python3
"""
Artificial Intelligence Data Assimilation Dictionary
Created on Wed Jan 14 19:45:25 2026
@author: gibies
https://github.com/Gibies
"""
import os
import sys
CURR_PATH=os.path.dirname(os.path.abspath(__file__))
PKGHOME=os.path.dirname(CURR_PATH)
OBSLIB=os.environ.get('OBSLIB',PKGHOME+"/pylib")
sys.path.append(OBSLIB)
OBSDIC=os.environ.get('OBSDIC',PKGHOME+"/pydic")
sys.path.append(OBSDIC)
OBSNML=os.environ.get('OBSNML',PKGHOME+"/nml")
sys.path.append(OBSNML)

"""
aidadic.py
"""

import numpy

# --- Registry of Multi-Factor Passports ---
MODEL_REGISTRY = {
    "bharat": {
        "interface_class": "dynlib.BharatInterface",
        "required_vars": ["air_temp", "spfh", "u_wind", "v_wind", "sfc_pres"],
        "horizontal_res": 0.0625,
        "vertical_levels": "bharat_85",
        "expected_units": {"air_temp": "K", "sfc_pres": "Pa"},
        "allow_nans": False,
        "mapping": {"air_temperature": "air_temp", "specific_humidity": "spfh", "eastward_wind": "u_wind", "northward_wind": "v_wind", "geopotential_height": "geo_ht", "surface_pressure": "sfc_pres"}
    },
    "crtm": {
        "interface_class": "dalib.CRTMInterface",
        "required_vars": ["pressure", "temperature", "humidity", "ozone", "cloud_water"],
        "horizontal_res": None, # Typically point-based or obs-space
        "vertical_levels": "crtm_standard_100",
        "expected_units": {"pressure": "hPa", "temperature": "K"},
        "allow_nans": False,
        "mapping": {"air_pressure": "pressure", "air_temperature": "temperature", "specific_humidity": "humidity", "mass_fraction_of_ozone_in_air": "ozone"}
    },
    "rttov": {
        "interface_class": "dalib.RTTOVInterface",
        "required_vars": ["p", "t", "q", "o3"],
        "horizontal_res": None,
        "vertical_levels": "rttov_54", # Standard RTTOV coefficient levels
        "expected_units": {"p": "hPa", "t": "K"},
        "allow_nans": False,
        "mapping": {"air_pressure": "p", "air_temperature": "t", "specific_humidity": "q", "mass_fraction_of_ozone_in_air": "o3"}
    },
    "anemoi": {
        "interface_class": "ailib.AnemoiInterface",
        "required_vars": ["2t", "u10", "v10", "q", "sp"],
        "horizontal_res": 0.25,
        "allow_nans": False,
        "mapping": {"air_temperature": "2t", "eastward_wind": "u10", "northward_wind": "v10", "specific_humidity": "q", "surface_pressure": "sp"}
    },
    "graphcast": {
        "interface_class": "ailib.GraphCastInterface",
        "required_vars": ["t", "q", "u", "v", "z"],
        "horizontal_res": 0.25,
        "vertical_levels": "era5_37",
        "allow_nans": False,
        "mapping": {"air_temperature": "t", "specific_humidity": "q", "eastward_wind": "u", "northward_wind": "v", "geopotential": "z"}
    },
    "pangu": {
        "interface_class": "ailib.PanguWeatherInterface",
        "required_vars": ["t", "q", "u", "v", "z"],
        "horizontal_res": 0.25,
        "vertical_levels": "pangu_13",
        "allow_nans": False,
        "mapping": {"air_temperature": "t", "specific_humidity": "q", "eastward_wind": "u", "northward_wind": "v", "geopotential": "z"}
    },
    "fourcastnet": {
        "interface_class": "ailib.FourCastNetInterface",
        "required_vars": ["t", "q", "u", "v", "z", "sp"],
        "horizontal_res": 0.25,
        "vertical_levels": "fourcastnet_13",
        "allow_nans": False,
        "mapping": {"air_temperature": "t", "specific_humidity": "q", "eastward_wind": "u", "northward_wind": "v", "geopotential": "z", "surface_pressure": "sp"}
    },
    "prithvi": {
        "interface_class": "ailib.PrithviInterface",
        "required_vars": ["T", "QV", "U", "V", "PS"],
        "horizontal_res": 0.5,
        "vertical_levels": "prithvi_37",
        "allow_nans": False,
        "mapping": {"air_temperature": "T", "specific_humidity": "QV", "eastward_wind": "U", "northward_wind": "V", "geopotential_height": "H", "surface_pressure": "PS"}
    },
    "mithuna": {
        "interface_class": "dynlib.MithunaInterface",
        "required_vars": ["temp", "q", "u", "v", "pres_sfc"],
        "horizontal_res": 0.125,
        "vertical_levels": "mithuna_17",
        "allow_nans": False,
        "mapping": {"air_temperature": "temp", "specific_humidity": "q", "eastward_wind": "u", "northward_wind": "v", "geopotential_height": "gh", "surface_pressure": "pres_sfc"}
    }
}



