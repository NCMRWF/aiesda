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
import torch.nn.functional as tornnfunc
import anemoi.inference as anemoinfe
import anemoi.datasets as anemoids 
import aidadic
#import obsdic

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
            print(f"Loading Anemoi model from {model_path} on {self.device}...")
            self.model = self.runner.model.to(self.device)
            self.model.eval()

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
                                Default: {'air_temperature': '2t', 'eastward_wind': 'u10'}
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
        """
        High-level Workflow Orchestrator.
        Handles file I/O, variable renaming, and calls the engine.
        """
        # 1. Prepare (JEDI -> Anemoi naming)
        input_data = self.prepare_input(analysis_nc)
        
        # 2. Execute (Calls the internal engine method)
        forecast_ds = self.execute_anemoi_runner(
            initial_state_ds=input_data, 
            lead_time=lead_time_hours
        )
        
        # 3. Save
        forecast_ds.to_netcdf(output_nc)
        return output_nc

    def execute_anemoi_runner(self, initial_state_ds, lead_time=72, frequency="6h"):
        """
        Internal Inference Engine.
        Directly wraps the anemoi.inference logic using the loaded runner.
        """
        print(f"Running Anemoi inference for {lead_time}h...")
        forecast = self.runner.run(
            initial_state=initial_state_ds,
            lead_time=lead_time,
            frequency=frequency
        )
        return forecast

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

