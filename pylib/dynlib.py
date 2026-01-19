#! python3
"""
Dynamical Forecast System Interface Library
Created on Mon Jan 19 2026
@author: gibies
"""
import numpy
import xarray
import aidadic

import numpy
import xarray
import pandas
import aidadic

class BharatInterface:
    """
    Interface for NCMRWF's Bharat Forecast System (Global Coupled).
    Encapsulates all logic for the 6km/12km TCo dynamical grid.
    """
    def __init__(self, config=None):
        self.config = config or {}
        # Load model-specific vertical coordinates from the dictionary
        self.atmosphere_levels = numpy.array(aidadic.bharat_atmosphere_levels)
        self.ocean_depth_levels = numpy.array(aidadic.bharat_ocean_depths)
        self.resolution = 0.125  # ~12km resolution

    def prepare_state(self, raw_atmosphere_data, raw_ocean_data):
        """
        Model-specific standardization:
        1. Renames internal BFS variables to JEDI standards.
        2. Aligns disparate vertical coordinates.
        3. Merges components into a single Coupled State.
        """
        # Atmospheric Mapping
        atm_map = {v: k for k, v in aidadic.bharat_jedi_atm_mapping.items()}
        std_atm = raw_atmosphere_data.rename(atm_map)

        # Oceanic Mapping (Coupled variables)
        ocn_map = {v: k for k, v in aidadic.bharat_jedi_ocn_mapping.items()}
        std_ocn = raw_ocean_data.rename(ocn_map)

        # Bharat Grid-Specific Logic: Enforce lev vs depth naming
        std_atm = std_atm.rename({'level': 'lev'})
        std_ocn = std_ocn.rename({'depth': 'ocean_depth'})

        # Return the Unified Coupled Dataset
        standardized_ds = xarray.merge([std_atm, std_ocn])
        return standardized_ds


    def get_jedi_config(self):
        """Returns the YAML-ready configuration specific to the Bharat model."""
        return {
            "geometry": {
                "atm_levels": len(self.atmosphere_levels),
                "ocn_levels": len(self.ocean_depth_levels)
            },
            "variables": list(aidadic.bharat_jedi_atm_mapping.keys()) + 
                        list(aidadic.bharat_jedi_ocn_mapping.keys())
        }

class MithunaInterface:
    """
    Interface for the Mithuna Global Coupled Forecast System.
    Handles specialized physics and regional high-res coupling.
    """
    def __init__(self, config=None):
        self.config = config or {}
        self.levels = numpy.array(aidadic.mithuna_levels)
        self.resolution = self.config.get('res', 0.1)

    def prepare_state(self, raw_data):
        # Specific naming logic for Mithuna (e.g., handling 'plev' or 'vertical')
        mapping = {v: k for k, v in aidadic.mithuna_jedi_var_mapping.items()}
        standardized_dataset = raw_data.rename(mapping)
        
        # Enforce naming conventions
        for coord in ['pressure', 'plev', 'level']:
            if coord in standardized_dataset.coords:
                standardized_dataset = standardized_dataset.rename({coord: 'lev'})
        
        return standardized_dataset




