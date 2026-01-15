
import os
import xarray as xr
import numpy as np
import torch
import torch.nn as tornn
import torch.nn.functional as func

import anemoi.inference as anemoinfe # Local import for isolation
import anemoi.datasets as anemoids # Local import for isolation

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

def load_ai_model(model_path, config):
    """Initializes and loads the pre-trained weights."""
    # Logic moved from jobs/aiesda.py
    pass

def run_inference(model, input_tensor):
    """Performs the forward pass to get AI-forecast/analysis."""
    with torch.no_grad():
        return model(input_tensor)

def aiesda_loss(pred, target, background, physics_weight=0.1):
    # 1. Standard Reconstruction Loss (MSE)
    mse_loss = func.mse_loss(pred, target)
    
    # 2. Background Constraint (Prevents the AI from straying too far from the 'First Guess')
    bg_constraint = func.mse_loss(pred, background)
    
    # 3. Physics Constraint (e.g., Smoothness/Total Variation)
    # Penalizes sharp, unphysical noise in the prediction
    diff_i = torch.pow(pred[:, :, 1:, :] - pred[:, :, :-1, :], 2).sum()
    diff_j = torch.pow(pred[:, :, :, 1:] - pred[:, :, :, :-1], 2).sum()
    tv_loss = diff_i + diff_j
    
    return mse_loss + bg_constraint + (physics_weight * tv_loss)

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

def compute_error_stats(forecast_zarr, truth_zarr, output_nc):
    """Calculate B-Matrix variance (StdDev) from historical AI errors."""
    
    fcs = anemoids.open_dataset(forecast_zarr)
    truth = anemoids.open_dataset(truth_zarr)
    
    # Vectorized error calculation
    std_dev = (fcs - truth).std(dim='time')
    std_dev.to_netcdf(output_nc)
    return output_nc
