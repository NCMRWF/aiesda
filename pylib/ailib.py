import torch
import torch.nn as tornn
import torch.nn.functional as func


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
