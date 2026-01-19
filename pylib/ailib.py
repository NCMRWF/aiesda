#! python3
"""
AI Interface Library
Created on Wed Jan 14 19:32:07 2026
@author: gibies
https://github.com/Gibies
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
ailib.py
"""
import xarray 
import numpy 
import torch
import torch.nn as tornn
import torch.nn.functional as tornnfunc
import anemoi.inference as anemoinfe
import anemoi.datasets as anemoids 
import aidadic
#import obsdic



class AtmosphericAutoencoder(tornn.Module):
    def __init__(self, input_channels=1, latent_dim=128):
        super(AtmosphericAutoencoder, self).__init__()
        # Encoder: Compresses the atmospheric grid
        self.encoder = tornn.Sequential(
            tornn.Conv2d(input_channels, 32, kernel_size=3, stride=2, padding=1),
            tornn.ReLU(),
            tornn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            tornn.ReLU(),
            tornn.Flatten(),
            tornn.Linear(64 * 16 * 16, latent_dim) # Adjust based on grid size
        )
        # Decoder: Reconstructs the full model state
        self.decoder = tornn.Sequential(
            tornn.Linear(latent_dim, 64 * 16 * 16),
            tornn.Unflatten(1, (64, 16, 16)),
            tornn.ConvTranspose2d(64, 32, kernel_size=4, stride=2, padding=1),
            tornn.ReLU(),
            tornn.ConvTranspose2d(32, input_channels, kernel_size=4, stride=2, padding=1),
            tornn.Sigmoid() 
        )

    def forward(self, x):
        latent = self.encoder(x)
        reconstruction = self.decoder(latent)
        return reconstruction, latent

    @staticmethod    
    def calculate_variational_cost(x_analysis, x_background, observations, obs_operator, B_inv, R_inv):
        """
        Standard Variational Cost Function:
        J(x) = (x - xb)^T B^-1 (x - xb) + (y - H(x))^T R^-1 (y - H(x))
        """
        # Background term (Difference from first guess)
        bg_diff = x_analysis - x_background
        J_b = 0.5 * torch.matmul(torch.matmul(bg_diff.T, B_inv), bg_diff)
    
        # Observation term (Difference from actual satellite/station data)
        # H(x) is the observation operator (often a neural network in aiesda)
        h_x = obs_operator(x_analysis) 
        obs_diff = observations - h_x
        J_o = 0.5 * torch.matmul(torch.matmul(obs_diff.T, R_inv), obs_diff)
        return J_b + J_o
    
    @staticmethod
    def aiesda_loss(pred, target, background, physics_weight=0.1, bg_weight=0.5):
        """
        AIESDA Custom Loss Function.
    
        Args:
            pred (torch.Tensor): The AI model's output (analysis/forecast).
            target (torch.Tensor): The 'Truth' or high-quality analysis.
            background (torch.Tensor): The JEDI background (First Guess).
            physics_weight (float): Weight for the Smoothness/TV penalty.
            bg_weight (float): Weight for the Background constraint (DA-like regularization).
            By adding the bg_constraint (background error), the model learns 
            to stay within the "physical manifold" defined by the JEDI First Guess.
        """
        # 1. Standard Reconstruction Loss (MSE) - Accuracy against truth
        mse_loss = tornnfunc.mse_loss(pred, target)

        # 2. Background Constraint (JEDI-Consistency)
        # This prevents the AI from straying too far from the physical 'First Guess'
        bg_constraint = tornnfunc.mse_loss(pred, background)

        # 3. Physics Constraint (Total Variation)
        # Penalizes sharp, unphysical noise in the prediction
        diff_i = torch.pow(pred[:, :, 1:, :] - pred[:, :, :-1, :], 2).sum()
        diff_j = torch.pow(pred[:, :, :, 1:] - pred[:, :, :, :-1], 2).sum()
        tv_loss = diff_i + diff_j

        # Total Weighted Loss
        return mse_loss + (bg_weight * bg_constraint) + (physics_weight * tv_loss)

class AnemoiInterface:
    """Interface for Anemoi ML-NWP models within aiesda."""

    def __init__(self, model_path=None, device=None, config=None):
        """
        Initializes and loads the pre-trained weights.
        This incorporates the logic formerly in load_ai_model.
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.config = config or {}
        self.runner = None
        # Initialize and load weights
        if model_path:
            print(f"Loading Anemoi model from {model_path}...")
            # FIX: Initialize the runner first
            self.runner = anemoinfe.Runner(checkpoint=model_path)
            # FIX: Extract model from the runner
            self.model = self.runner.model.to(self.device)
            self.model.eval()
        else:
            self.runner = None
            self.model = None

    def run_inference(self, input_tensor):
        """
        Performs the forward pass to get AI-forecast/analysis.
        Centrally handles torch.no_grad() and device management.
        """
        # Ensure input is on the correct device
        if isinstance(input_tensor, torch.Tensor):
            input_tensor = input_tensor.to(self.device)
            
        with torch.no_grad():
            return self.model(input_tensor)

    def prepare_input(self, analysis_file, var_mapping=None):
        """
        Converts the JEDI/AIESDA analysis NetCDF into Anemoi input format.
        
        Args:
            analysis_file (str): Path to the NetCDF file output by JEDI.
            var_mapping (dict): JEDI to Anemoi mapping. 
        """
        if var_mapping is None:
            var_mapping = aidadic.jedi_anemoi_var_mapping

        ds = xarray.open_dataset(analysis_file)

        # 1. Rename JEDI variables back to Anemoi/ECMWF short names
        mapping_to_use = {k: v for k, v in var_mapping.items() if k in ds.variables}
        ds_anemoi = ds.rename(mapping_to_use)

        # 2. Data Integrity: Ensure time dimension exists (Anemoi expects a sequence)
        if 'time' not in ds_anemoi.dims:
            ds_anemoi = ds_anemoi.expand_dims('time')

        print(f"Prepared JEDI analysis from {analysis_file} for Anemoi input.")
        return ds_anemoi

    def run_forecast(self, initial_state, steps=24):
        """
        Executes the forecast rollout.
        initial_state: xarray dataset or torch tensor
        steps: Number of auto-regressive rollout steps
        """
        with torch.no_grad():
            # Anemoi handles the internal rollout logic
            forecast = self.model.predict(initial_state, steps=steps)
        return forecast

    def rollout_forecast(self, analysis_nc, output_nc, lead_time_hours):
        """Unified Rollout Orchestrator."""
        # Preparation
        input_data = self.prepare_input(analysis_nc)

        # Inference using the internal runner
        print(f"Executing {lead_time_hours}h rollout...")
        forecast_ds = self.runner.run(
            initial_state=input_data,
            lead_time=lead_time_hours
        )

        forecast_ds.to_netcdf(output_nc)
        return output_nc

    def prepare_background_from_anemoi(self, zarr_path, target_time, output_nc):
        """
        Class-based background preparation. 
        Reuses export_for_jedi to ensure consistent variable naming.
        """
        # 1. Open the Zarr dataset using Anemoi's dataset utility
        ds = anemoids.open_dataset(zarr_path)
        
        # 2. Leverage the existing class function for transformation and export
        return self.export_for_jedi(ds, output_nc, target_time)

    def export_for_jedi(self, dataset, output_path, analysis_time, var_mapping=None):
        """Converts Anemoi Xarray/Zarr output to JEDI-compliant NetCDF."""
        if var_mapping is None:
            var_mapping = {v: k for k, v in aidadic.jedi_anemoi_var_mapping.items()}

        ds_at_time = dataset.sel(time=analysis_time)
        ds_jedi = ds_at_time.rename({k: v for k, v in var_mapping.items() if k in ds_at_time.variables})
        ds_jedi.to_netcdf(output_path)
        return output_path



class GraphCastInterface:
    def __init__(self, config=None):
        self.config = config if config else {}
        # Reference levels from central dictionary
        self.standard_levels = numpy.array(aidadic.graphcast_levels)

    def prepare_state(self, raw_output):
        """Standardizes GraphCast output using aidadic mapping."""
        mapping = {v: k for k, v in aidadic.graphcast_jedi_var_mapping.items()}
        standardized_ds = raw_output.rename(mapping)
        
        if 'level' in standardized_ds.coords:
            standardized_ds = standardized_ds.rename({'level': 'lev'})
        
        # ADD THIS: Ensures the 37 levels match aidadic exactly
        standardized_ds['lev'] = self.standard_levels
        return standardized_ds


class FourCastNetInterface:
    """
    Interface to handle FourCastNet (AFNO) model states.
    Optimized for the standard 13-level atmospheric profile.
    """

    def __init__(self, config=None):
        self.config = config if config else {}
        # Reference 13 levels from aidadic
        self.levels = numpy.array(aidadic.fourcastnet_levels)
        self.res = 0.25  # Standard horizontal resolution

    def prepare_state(self, raw_output):
        """
        Standardizes FourCastNet output for dalib.
        Handles renaming and coordinate alignment for 13 levels.
        """
        # Create reverse mapping: { 't': 'air_temperature' }
        mapping = {v: k for k, v in aidadic.fourcastnet_jedi_var_mapping.items()}
        
        # Rename variables
        standardized_ds = raw_output.rename(mapping)
        
        # Standardize vertical coordinate
        if 'level' in standardized_ds.coords:
            standardized_ds = standardized_ds.rename({'level': 'lev'})
        elif 'pressure' in standardized_ds.coords:
            standardized_ds = standardized_ds.rename({'pressure': 'lev'})

        # Assign the aidadic levels to ensure floating point precision matches
        standardized_ds['lev'] = self.levels
        
        return standardized_ds


class PanguWeatherInterface:
    """
    Interface to handle Pangu-Weather model states.
    Supports the 3D Earth-Specific Transformer output format.
    """

    def __init__(self, config=None):
        self.config = config if config else {}
        # Reference 13 levels from aidadic
        self.levels = numpy.array(aidadic.pangu_levels)
        self.res = 0.25

    def prepare_state(self, raw_output):
        """
        Standardizes Pangu-Weather output.
        - Maps variable names to JEDI standards.
        - Ensures vertical coordinates are correctly labeled for dalib.
        """
        # Create reverse mapping: { 't': 'air_temperature' }
        mapping = {v: k for k, v in aidadic.pangu_jedi_var_mapping.items()}
        
        # Rename variables and coordinate system
        standardized_ds = raw_output.rename(mapping)
        
        # Pangu-Weather standard coordinate handling
        if 'level' in standardized_ds.coords:
            standardized_ds = standardized_ds.rename({'level': 'lev'})
            
        # Standardize units: Pangu Geopotential is often m^2/s^2 
        # whereas some DA systems expect Geopotential Height (m)
        if 'geopotential' in standardized_ds:
            gravity = 9.80665
            standardized_ds['geopotential_height'] = standardized_ds['geopotential'] / gravity

        # Align pressure levels with aidadic
        standardized_ds['lev'] = self.levels
        
        return standardized_ds


class PrithviInterface:
    """
    Interface for NASA-IBM Prithvi WxC Foundation Model.
    Designed to handle MERRA-2 based variables and flexible spatial grids.
    """

    def __init__(self, config=None):
        self.config = config if config else {}
        # Reference levels from aidadic (MERRA-2 standard)
        self.levels = numpy.array(aidadic.prithvi_levels)
        # Prithvi can vary resolution (e.g., 0.5 or 0.25), default to 0.5
        self.res = self.config.get('res', 0.5)

    def prepare_state(self, raw_output):
        """
        Standardizes Prithvi output for the JEDI pipeline.
        - Translates MERRA-2 variable names (e.g., QV to specific_humidity).
        - Standardizes vertical 'lev' coordinate.
        """
        # Map MERRA-2 names to JEDI standard names
        mapping = {v: k for k, v in aidadic.prithvi_jedi_var_mapping.items()}
        standardized_ds = raw_output.rename(mapping)

        # Coordinate Standardization
        for coord_name in ['pressure', 'level', 'layers']:
            if coord_name in standardized_ds.coords:
                standardized_ds = standardized_ds.rename({coord_name: 'lev'})

        # Physical Unit Conversion for Prithvi (MERRA-2)
        # Convert Geopotential Height (H) to Geopotential (Z) if needed by JEDI
        if 'geopotential_height' in standardized_ds:
            standardized_ds['geopotential'] = standardized_ds['geopotential_height'] * 9.80665

        if len(standardized_ds.lev) == len(self.levels):
            standardized_ds['lev'] = self.levels
            
        return standardized_ds

class ModelFactory:
    """
    Automated interface selector for AI-NWP models.
    Detects model type from dataset attributes or config.
    """
    @staticmethod
    def get_interface(ds, config=None):
        """
        Args:
            ds (xarray.Dataset): The raw output from an AI model.
            config (dict): Optional manual override.
        """
        # 1. Check for explicit attributes (common in Prithvi/Anemoi)
        model_name = ds.attrs.get('model_name', '').lower()
        
        # 2. Logic-based detection (level counts and variable names)
        num_levels = len(ds.coords.get('level', ds.coords.get('lev', [])))
        
        if 'anemoi' in model_name or hasattr(ds, 'anemoi_metadata'):
            return AnemoiInterface(config=config)
        
        if num_levels == 37:
            # Check for MERRA-2 naming (Prithvi) vs ERA5 (GraphCast)
            if 'QV' in ds.variables or 'T' in ds.variables:
                return PrithviInterface(config=config)
            return GraphCastInterface(config=config)
            
        if num_levels == 13:
            # Pangu and FourCastNet share levels, differentiate by variable names
            if 'z' in ds.variables and 'q' in ds.variables:
                return PanguWeatherInterface(config=config)
            return FourCastNetInterface(config=config)
            
        raise ValueError(f"Unknown model profile with {num_levels} levels. Please specify interface manually.")

"""
Public functions
"""


def load_ai_model(model_path, config=None):
    """class object initialisation"""
    return AnemoiInterface(model_path, config=config)
    
def rollout_forecast(model_checkpoint, analysis_nc, output_nc, lead_time_hours):
    """Legacy wrapper calling the class method."""
    interface = AnemoiInterface(model_checkpoint)
    return interface.rollout_forecast(analysis_nc, output_nc, lead_time_hours)

def prepare_background_from_anemoi(zarr_path, target_time, output_nc):
    """Legacy wrapper calling the class method."""
    interface = AnemoiInterface()
    return interface.prepare_background_from_anemoi(zarr_path, target_time, output_nc)

def export_for_jedi(dataset, output_path, analysis_time, var_mapping=None):
    """Legacy wrapper calling the class method."""
    interface = AnemoiInterface()
    return interface.export_for_jedi(dataset, output_path, analysis_time, var_mapping=var_mapping)

