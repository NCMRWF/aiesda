

import os
import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
from aidaconf import AidaConfig
import aidadic

class AssimilationValidator:
    """Class to validate AI analysis against background and observations."""

    def __init__(self, conf: AidaConfig):
        self.conf = conf
        self.plot_dir = os.path.join(self.conf.WORK_DIR, "plots")
        os.makedirs(self.plot_dir, exist_ok=True)

    def calculate_increment(self, analysis_file, background_file):
        """Calculates Analysis Increment: (Analysis - Background)."""
        ds_an = xr.open_dataset(analysis_file)
        ds_bg = xr.open_dataset(background_file)

        # Ensure coordinates align before subtraction
        increment = ds_an - ds_bg
        return increment

    def plot_diagnostic_maps(self, var_name, analysis_file, background_file):
        """Generates a 3-panel plot: Background, Analysis, and Increment."""
        ds_an = xr.open_dataset(analysis_file)
        ds_bg = xr.open_dataset(background_file)

        # Mapping back to JEDI names if necessary
        plot_var = aidadic.jedi_anemoi_var_mapping.get(var_name, var_name)

        fig, axes = plt.subplots(1, 3, figsize=(18, 5))

        # Plotting logic
        ds_bg[plot_var].plot(ax=axes[0], cmap='RdYlBu_r')
        axes[0].set_title(f"Background ({var_name})")

        ds_an[plot_var].plot(ax=axes[1], cmap='RdYlBu_r')
        axes[1].set_title(f"Analysis ({var_name})")

        increment = ds_an[plot_var] - ds_bg[plot_var]
        increment.plot(ax=axes[2], cmap='bwr')
        axes[2].set_title("Assimilation Increment")

        plot_path = os.path.join(self.plot_dir, f"{var_name}_val.png")
        plt.savefig(plot_path)
        plt.close()
        return plot_path

    def compute_stats(self, increment_ds):
        """Computes RMSE and Bias of the increment."""
        stats = {
            "mean_increment": increment_ds.mean().to_array().values,
            "rmse_increment": np.sqrt((increment_ds**2).mean()).to_array().values
        }
        return stats
