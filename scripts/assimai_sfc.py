import os
import sys
import numpy 
import xarray 
from datetime import datetime

# Import the new isolated libraries
# Ensure AIESDA_HOME is in your PYTHONPATH
import dalib
import ailib

def main():
    # --- 1. DYNAMIC TIME & PATH SETUP ---
    cycle_str = os.getenv('CYCLE_TIME', '2026-01-14T18:00:00Z')
    cycle_time = datetime.strptime(cycle_str, '%Y-%m-%dT%H:%M:%SZ')
    
    # Use dalib to handle window logic
    window_start, window_end = dalib.get_obs_window(cycle_time, hours=3)
    
    print(f"--- AIESDA Cycle Started: {cycle_time} ---")

    # --- 2. OBSERVATION INGEST (DALIB) ---
    # Data would typically be fetched from Monitobs tanks here
    lats = numpy.array([28.6, 19.1, 13.0], dtype='float32')
    lons = numpy.array([77.2, 72.8, 80.2], dtype='float32')
    temp = numpy.array([298.15, 301.50, 303.20], dtype='float32')
    ids  = numpy.array(['DEL01', 'BOM02', 'MAA03'], dtype=object)
    errs = numpy.full_like(temp, 1.5)

    obs_file = dalib.write_ioda_surface_obs(
        output_path="aiesda_obs_sfc.nc",
        lats=lats, lons=lons, values=temp, errors=errs, station_ids=ids
    )
    print(f"IODA Observations Ready: {obs_file}")

    # --- 3. BACKGROUND PREPARATION (AILIB) ---
    # Isolate Zarr slicing and JEDI renaming (2t -> air_temperature)
    bg_file = ailib.prepare_background_from_anemoi(
        zarr_path="ncmrwf_forecast.zarr",
        target_time=cycle_str,
        output_nc="ncmrwf_anemoi_bg.nc"
    )
    print(f"Anemoi Background Ready for JEDI: {bg_file}")

    # --- 4. B-MATRIX ERROR STATS (AILIB) ---
    stats_file = ailib.compute_error_stats(
        forecast_zarr="anemoi_historical_forecasts.zarr",
        truth_zarr="era5_reference.zarr",
        output_nc="anemoi_error_stats.nc"
    )
    print(f"SABER/BUMP Statistics Generated: {stats_file}")

    # --- 5. JEDI EXECUTION (Placeholder for Binary Call) ---
    # In a real workflow, this would be a subprocess call to fv3jedi_variational.x
    # For now, we assume 'aiesda_final_analysis.nc' is produced.
    print("Executing JEDI Variational Solver...")

    # --- 6. POST-DA DIAGNOSTICS (DALIB) ---
    # Move plotting logic to library to keep the driver clean
    # dalib.visualization.plot_increment(bg_file, "aiesda_final_analysis.nc")
    
    # --- 7. AI FORECAST ROLLOUT (AILIB) ---
    forecast_rollout = ailib.run_forecast_rollout(
        initial_state_nc="aiesda_final_analysis.nc",
        model_ckpt="path/to/anemoi_model.ckpt",
        lead_time=72
    )
    print("AI Forecast Rollout Complete (72h).")

    # --- 8. VERIFICATION (AILIB) ---
    # Verify against independent data
    truth_ds = xarray.open_dataset("monitobs_independent_verify.zarr")
    # This logic can be moved to ailib.metrics
    # rmse = ailib.compute_rmse(forecast_rollout, truth_ds)
    
    print("AIESDA Cycle Successful.")

if __name__ == "__main__":
    main()
