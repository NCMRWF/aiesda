#! python3
"""
AI Interface Library
Created on Wed Jan 14 19:32:07 2026
@author: gibies
https://github.com/Gibies
"""
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
import sys
import os
import xarray 
import numpy 
import torch
import torch.nn as tornn
import torch.nn.functional as func
import anemoi.inference as anemoinfe
import anemoi.datasets as anemoids 
import aidadic
#import obsdic

class AnemoiInterface:
    """Interface for Anemoi ML-NWP models within aiesda."""

    def __init__(self, model_path, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        # Load the Anemoi checkpoint (contains weights and metadata)
        self.model = AnemoiPredictor.from_checkpoint(model_path).to(self.device)
        self.model.eval()
    def prepare_input(self, analysis_file, var_mapping=None):
        """
        Converts the JEDI/AIESDA analysis NetCDF into Anemoi input format.
        
        Args:
            analysis_file (str): Path to the NetCDF file output by JEDI.
            var_mapping (dict): JEDI to Anemoi mapping. 
                                Default: {'air_temperature': '2t', 'eastward_wind': 'u10'}
        """
        if var_mapping is None:
            var_mapping = aidadic.jedi_anemoi_var_mapping

        ds = xr.open_dataset(analysis_file)

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

    def export_for_jedi(self, dataset, output_path, analysis_time, var_mapping=None):
        """Converts Anemoi Xarray/Zarr output to JEDI-compliant NetCDF."""
        if var_mapping is None:
            var_mapping = {v: k for k, v in aidadic.jedi_anemoi_var_mapping.items()}

        ds_at_time = dataset.sel(time=analysis_time)
        ds_jedi = ds_at_time.rename({k: v for k, v in var_mapping.items() if k in ds_at_time.variables})
        ds_jedi.to_netcdf(output_path)
        return output_path

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
    
    def aiesda_loss(pred, target, background, physics_weight=0.1, bg_weight=0.5):
        """
        AIESDA Custom Loss Function.
    
        Args:
            pred (torch.Tensor): The AI model's output (analysis/forecast).
            target (torch.Tensor): The 'Truth' or high-quality analysis.
            background (torch.Tensor): The JEDI background (First Guess).
            physics_weight (float): Weight for the Smoothness/TV penalty.
            bg_weight (float): Weight for the Background constraint (DA-like regularization).
        """
        # 1. Standard Reconstruction Loss (MSE) - Accuracy against truth
        mse_loss = func.mse_loss(pred, target)

        # 2. Background Constraint (JEDI-Consistency)
        # This prevents the AI from straying too far from the physical 'First Guess'
        bg_constraint = func.mse_loss(pred, background)

        # 3. Physics Constraint (Total Variation)
        # Penalizes sharp, unphysical noise in the prediction
        diff_i = torch.pow(pred[:, :, 1:, :] - pred[:, :, :-1, :], 2).sum()
        diff_j = torch.pow(pred[:, :, :, 1:] - pred[:, :, :, :-1], 2).sum()
        tv_loss = diff_i + diff_j

        # Total Weighted Loss
        return mse_loss + (bg_weight * bg_constraint) + (physics_weight * tv_loss)

"""
Public functions
"""

def rollout_forecast(model_checkpoint, analysis_nc, output_nc, lead_time_hours):
    """High-level wrapper for the jobs/aiesda.py script."""
    ai_engine = AnemoiInterface(model_checkpoint)
    input_data = ai_engine.prepare_input(analysis_nc)
    
    # Calculate steps based on model's dt (usually 6h)
    steps = lead_time_hours // 6 
    
    forecast_ds = ai_engine.run_forecast(input_data, steps=steps)
    forecast_ds.to_netcdf(output_nc)
    return output_nc


def load_ai_model(model_path, config):
    """Initializes and loads the pre-trained weights."""
    # Logic moved from jobs/aiesda.py
    pass

def run_inference(model, input_tensor):
    """Performs the forward pass to get AI-forecast/analysis."""
    with torch.no_grad():
        return model(input_tensor)




def prepare_background_from_anemoi(zarr_path, target_time, output_nc):
    """
    Isolated Anemoi-to-JEDI bridge.
    Encapsulates anemoi.datasets to provide a NetCDF background for JEDI.
    """
    
    # 1. Open the Zarr dataset
    ds = anemoids.open_dataset(zarr_path)
    
    # 2. Extract and Rename variables to JEDI conventions
    # Mapping Anemoi names (e.g., '2t', '10u') to JEDI names
    ds_at_time = ds.sel(time=target_time).rename({
        '2t': 'air_temperature',
        '10u': 'eastward_wind',
        '10v': 'northward_wind'
    })
    
    # 3. Export to NetCDF (JEDI standard)
    ds_at_time.to_netcdf(output_nc)
    return os.path.abspath(output_nc)

def run_forecast_rollout(initial_state_nc, model_ckpt, lead_time=72):
    """
    Isolated Anemoi Inference.
    Encapsulates anemoi.inference logic.
    """
    
    # Load analysis state from DA
    analysis_state = xarray.open_dataset(initial_state_nc)
    
    # Initialize and run the ML model
    runner = anemoinfe.Runner(checkpoint=model_ckpt)
    forecast = runner.run(
        initial_state=analysis_state,
        lead_time=lead_time,
        frequency="6h"
    )
    return forecast

