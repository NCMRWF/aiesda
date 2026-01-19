#! python3
"""
Dynamical Forecast System Interface Library
Created on Mon Jan 19 2026
@author: gibies
"""
import sys
import os
CURR_PATH=os.path.dirname(os.path.abspath(__file__))
PKGHOME=os.path.dirname(CURR_PATH)
OBSLIB=os.environ.get('OBSLIB',PKGHOME+"/pylib")
sys.path.append(OBSLIB)
OBSDIC=os.environ.get('OBSDIC',PKGHOME+"/pydic")
sys.path.append(OBSDIC)
OBSNML=os.environ.get('OBSNML',PKGHOME+"/nml")
sys.path.append(OBSNML)
"""
dynlib.py
"""
import numpy
import xarray
import pandas
import aidadic

class BharatInterface:
    """
    Encapsulated Interface for Bharat Forecast System (Global Coupled).
    Handles high-resolution TCo dynamical grid data.
    """
    def __init__(self, config=None):
        self.config = config or {}
        self.atmosphere_levels = numpy.array(aidadic.bharat_atm_levels)
        self.ocean_levels = numpy.array(aidadic.bharat_ocn_depths)

    def prepare_state(self, raw_atm, raw_ocn):
        """Standardizes Bharat coupled data for JEDI ingestion."""
        # 1. Atmospheric Processing
        atm_map = {v: k for k, v in aidadic.bharat_jedi_atm_mapping.items()}
        standardized_atm = raw_atm.rename(atm_map)
        
        # 2. Oceanic Processing
        ocn_map = {v: k for k, v in aidadic.bharat_jedi_ocn_mapping.items()}
        standardized_ocn = raw_ocn.rename(ocn_map)

        # 3. Model-Specific Vertical Alignment
        # Bharat uses 'lev' for air and 'depth' for water
        standardized_atm = standardized_atm.rename({'level': 'lev'})
        standardized_ocn = standardized_ocn.rename({'depth': 'ocean_depth'})

        # 4. Final Coupling
        return xarray.merge([standardized_atm, standardized_ocn])

    def get_jedi_config(self):
        """Returns the specific JEDI YAML parameters for BharatFS."""
        return {
            "model_name": "BharatFS",
            "grid_type": "TCo",
            "resolution": 0.0625,  # ~6km
            "variables": list(aidadic.bharat_jedi_atm_mapping.keys()) + 
                        list(aidadic.bharat_jedi_ocn_mapping.keys())
        }

class MithunaInterface:
    """
    Encapsulated Interface for Mithuna Global Coupled Model.
    Handles standard global grid data at 12km resolution.
    """
    def __init__(self, config=None):
        self.config = config or {}
        self.levels = numpy.array(aidadic.mithuna_levels)

    def prepare_state(self, raw_coupled_data):
        """Processes Mithuna's integrated atmosphere-ocean file."""
        mapping = {v: k for k, v in aidadic.mithuna_jedi_mapping.items()}
        standardized_ds = raw_coupled_data.rename(mapping)

        # Mithuna specific: rename coordinate levels if they vary
        if 'pressure' in standardized_ds.coords:
            standardized_ds = standardized_ds.rename({'pressure': 'lev'})
        
        return standardized_ds

    def get_jedi_config(self):
        return {
            "model_name": "MithunaFS",
            "resolution": 0.125, # 12km
            "variables": list(aidadic.mithuna_jedi_mapping.keys())
        }






