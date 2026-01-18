#! python3
"""
Artificial Intelligence Data Assimilation Science Library
Created on Wed Jan 14 19:56:48 2026
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
scilib.py
"""


import os
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from datetime import datetime, timedelta
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

    def run_sensitivity_test(self, ai_engine, base_analysis_file, var_name, epsilon=0.1):
        """
        Computes the sensitivity of the analysis to the background state.
        S = (A(x + eps) - A(x)) / eps
        """
        # 1. Load baseline analysis
        base_an = xr.open_dataset(base_analysis_file)

        # 2. Create a perturbed background (simulating a change in input)
        # We add a small 'epsilon' to the variable in question
        perturbed_bg = base_an.copy(deep=True)
        perturbed_bg[var_name] = perturbed_bg[var_name] + epsilon

        perturbed_bg_path = os.path.join(self.conf.WORK_DIR, "temp_perturbed_bg.nc")
        perturbed_bg.to_netcdf(perturbed_bg_path)

        # 3. Run AI Inference on the perturbed state
        perturbed_out_path = os.path.join(self.conf.WORK_DIR, "temp_perturbed_analysis.nc")
        ai_engine.rollout_forecast(
            analysis_nc=perturbed_bg_path,
            output_nc=perturbed_out_path,
            lead_time_hours=6
        )

        # 4. Calculate Sensitivity Map
        perturbed_an = xr.open_dataset(perturbed_out_path)
        sensitivity = (perturbed_an[var_name] - base_an[var_name]) / epsilon

        return sensitivity

    def plot_sensitivity(self, sensitivity_ds, var_name):
        """Visualizes areas where the model is most sensitive to input changes."""
        plt.figure(figsize=(10, 6))
        sensitivity_ds.plot(cmap='viridis')
        plt.title(f"Model Sensitivity Map: {var_name}")

        save_path = os.path.join(self.plot_dir, f"sensitivity_{var_name}.png")
        plt.savefig(save_path)
        plt.close()
        return save_path

    def check_temporal_consistency(self, current_analysis_file, previous_forecast_file, threshold=2.0):
        """
        Validates the transition between cycles.
        Compares Analysis(T) with Forecast(T-6) valid at T.
        """
        ds_an = xr.open_dataset(current_analysis_file)
        ds_fc_prev = xr.open_dataset(previous_forecast_file)

        # Calculate the 'Jump' (Analysis - Background from previous cycle)
        jump = ds_an - ds_fc_prev
        
        # Calculate RMS of the jump across the grid
        rms_jump = np.sqrt((jump**2).mean())
        
        # Alert if the jump exceeds a physical threshold (e.g., 2 Kelvin for Temp)
        alerts = []
        for var in jump.data_vars:
            val = rms_jump[var].values
            if val > threshold:
                alerts.append(f"WARNING: High temporal jump in {var}: {val:.4f}")
        
        return jump, alerts

    def plot_temporal_tendency(self, jump_ds, var_name):
        """Visualizes the spatial distribution of the cycle-to-cycle jump."""
        plt.figure(figsize=(10, 6))
        jump_ds[var_name].plot(cmap='seismic', robust=True)
        plt.title(f"Temporal Jump (Analysis $T_0$ - Forecast $T_{-6}$): {var_name}")
        
        save_path = os.path.join(self.plot_dir, f"temporal_jump_{var_name}.png")
        plt.savefig(save_path)
        plt.close()
        return save_path


class AidaReportCard:
    """Batch processing class to evaluate experiment performance over time."""
    
    def __init__(self, expid, root_dir):
        self.expid = expid
        self.root_dir = root_dir
        self.metrics_db = []

    def collect_cycle_metrics(self, date, cycle, stats_dict):
        """Logs metrics for a specific cycle into a central database."""
        stats_dict.update({'date': date, 'cycle': cycle})
        self.metrics_db.append(stats_dict)

    def generate_summary_report(self, output_dir):
        """Creates a performance report with time-series of RMSE and Bias."""
        df = pd.DataFrame(self.metrics_db)
        df['timestamp'] = pd.to_datetime(df['date'] + df['cycle'], format='%Y%m%d%H')
        df = df.sort_values('timestamp')

        # Create Time-Series Plots
        fig, ax = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        
        ax[0].plot(df['timestamp'], df['rmse_increment'], marker='o', color='tab:red')
        ax[0].set_title(f"Experiment {self.expid}: Root Mean Square Increment (RMSI)")
        ax[0].set_ylabel("RMSE")

        ax[1].plot(df['timestamp'], df['mean_increment'], marker='s', color='tab:blue')
        ax[1].set_title("Mean Increment (Bias)")
        ax[1].set_ylabel("Bias")
        ax[1].axhline(0, color='black', linestyle='--')

        report_path = os.path.join(output_dir, f"{self.expid}_summary_report.png")
        plt.tight_layout()
        plt.savefig(report_path)
        
        # Save CSV for further analysis in Excel/Pandas
        df.to_csv(os.path.join(output_dir, f"{self.expid}_metrics.csv"), index=False)
        return report_path


class VerticalInterpolator:
    """Handles interpolation from coarse AI levels to CRTM standard layers."""
    
    def __init__(self):
        # Always use the standard levels defined in aidadic
        self.target_levels = np.array(aidadic.crtm_standard_levels)

    def interpolate_field(self, source_p, data_array):
        """Performs log-linear interpolation for meteorological profiles."""
        # Using log-pressure for linear interpolation of T and Q
        x_src = np.log(source_p)
        x_tgt = np.log(self.target_levels)

        f = interp1d(x_src, data_array, axis=0, kind='linear', 
                     bounds_error=False, fill_value="extrapolate")
        
        return f(x_tgt)

    def generate_geovals(self, model_ds):
        """
        Main entry point: Converts Anemoi state to JEDI GeoVaLs on CRTM levels.
        """
        # Dictionary to hold the interpolated high-res fields
        geovals_ds = xr.Dataset(coords={'lev': self.target_levels})
        
        # Source pressure from Anemoi (e.g., 13 levels)
        source_p = model_ds['lev'].values 

        # Loop through mapping defined in aidadic
        for jedi_var, anemoi_var in aidadic.jedi_anemoi_var_mapping.items():
            if anemoi_var in model_ds:
                # Interpolate from 13 levels -> 100 levels
                interp_data = self.interpolate_field(source_p, model_ds[anemoi_var].values)
                geovals_ds[jedi_var] = (('lev', 'lat', 'lon'), interp_data)
                
        return geovals_ds
