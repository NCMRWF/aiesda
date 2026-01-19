#! python3
"""
Dynamical Forecast System Interface Library
Created on Mon Jan 19 2026
@author: gibies
"""
import numpy
import xarray
import aidadic

class BharatInterface:
    """
    Interface for NCMRWF's Bharat Forecast System.
    Handles high-resolution global/regional standardized output.
    """
    def __init__(self, config=None):
        self.config = config or {}
        self.levels = numpy.array(aidadic.bharat_levels)
        self.res = self.config.get('res', 0.125) # Standard Bharat resolution

    def prepare_state(self, raw_output):
        """Standardizes Bharat system data for JEDI ingestion."""
        mapping = {v: k for k, v in aidadic.bharat_jedi_var_mapping.items()}
        standardized_ds = raw_output.rename(mapping)

        # Coordinate Standardization
        if 'level' in standardized_ds.coords:
            standardized_ds = standardized_ds.rename({'level': 'lev'})
        elif 'vertical' in standardized_ds.coords:
            standardized_ds = standardized_ds.rename({'vertical': 'lev'})

        # Enforce exact pressure levels from aidadic
        if len(standardized_ds.lev) == len(self.levels):
            standardized_ds['lev'] = self.levels

        return standardized_ds



class MithunaInterface:
    """
    Interface for the Midhuna Forecast System.
    Handles regional high-resolution data standardization.
    """

    def __init__(self, config=None):
        self.config = config if config else {}
        self.levels = numpy.array(aidadic.midhuna_levels)
        # Mithuna often uses a higher resolution (e.g., 0.1 degree or 4km)
        self.res = self.config.get('res', 0.1)

    def prepare_state(self, raw_output):
        """
        Standardizes Midhuna output for the DA pipeline.
        - Maps regional variable names to JEDI standards.
        - Aligns vertical 'lev' coordinate.
        - Preserves regional domain metadata.
        """
        mapping = {v: k for k, v in aidadic.mithuna_jedi_var_mapping.items()}
        standardized_ds = raw_output.rename(mapping)

        # Standardize vertical coordinate naming
        for coord in ['level', 'pressure', 'plev']:
            if coord in standardized_ds.coords:
                standardized_ds = standardized_ds.rename({coord: 'lev'})

        # Assign centralized levels for numerical consistency
        if len(standardized_ds.lev) == len(self.levels):
            standardized_ds['lev'] = self.levels

        # Midhuna specific: Ensure projection info is retained if needed by JEDI
        if 'projection' in raw_output.attrs:
            standardized_ds.attrs['projection'] = raw_output.attrs['projection']

        return standardized_ds
