import numpy as np
import xarray as xr
import h5py
import ioda                     # From JEDI
import anemoi.inference as ai
import anemoi.datasets as ads    # From Anemoi
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pyiodaconv import ioda_conv_engines as iconv

# 1. Define your data (cloned/extracted from Monitobs scripts)
lats = np.array([28.6, 19.1, 13.0], dtype='float32') # Delhi, Mumbai, Chennai
lons = np.array([77.2, 72.8, 80.2], dtype='float32')
temp = np.array([298.15, 301.50, 303.20], dtype='float32') # 2m Temperature

# 2. Setup IODA Global Attributes
location_key_list = [("latitude", "float"), ("longitude", "float")]

# 3. Create the ObsSpace
writer = iconv.IodaWriter("aiesda_obs_sfc.nc", location_key_list)


# 4. Fill with Data Groups
# 'ObsValue' = Measurements | 'ObsError' = Uncertainty | 'MetaData' = Spatial/ID info
station_ids = np.array(['DEL01', 'BOM02', 'MAA03'], dtype=object)
obs_errors = np.array([1.2, 1.5, 1.8], dtype='float32') # Kelvin

data = {
    ('air_temperature', 'ObsValue'): temp,
    ('air_temperature', 'ObsError'): obs_errors,
    ('latitude', 'MetaData'): lats,
    ('longitude', 'MetaData'): lons,
    ('station_id', 'MetaData'): station_ids,
}

# 5. Write to file
# BuildIoda organizes these into the HDF5 groups JEDI expects
writer.BuildIoda(data, {})


# Load Model Data (Anemoi)
ds = ads.open_dataset("ncmrwf_forecast.zarr")

# Load Assimilated Data (JEDI)
#obs = ioda.ObsGroup.read("aiesda_obs_sfc.nc")

print("Successfully linked Anemoi Model Grid with JEDI Observation Space.")

# 6. Export Anemoi state for JEDI Background
# Convert Anemoi Xarray/Zarr to NetCDF for JEDI
# Ensure the variable names match the JEDI 'state variables' list
# Select the analysis time (e.g., T+0 for the start of the DA window)
# JEDI requires specific NetCDF naming; map Anemoi variables to JEDI names
# Example: Rename '2t' to 'air_temperature' if needed
# Part 6 Update: Ensure NetCDF variables match JEDI expectation
# Rename Anemoi '2t' to JEDI 'air_temperature'
ds_at_time = ds.sel(time="2026-01-14T18:00:00").rename({'2t': 'air_temperature'})
ds_at_time.to_netcdf("ncmrwf_anemoi_bg.nc")

#print("Background file ready for JEDI OOPS.")
print("AIESDA Pipeline Complete: IODA observations and Anemoi background ready.")



# Load a historical archive of Anemoi forecasts and a reference (like ERA5)
# This is used to calculate the 'spread' or 'uncertainty' of your ML model
forecasts = ads.open_dataset("anemoi_historical_forecasts.zarr")
truth = ads.open_dataset("era5_reference.zarr")

# 7. Calculate the Error (Forecast - Truth)
errors = forecasts - truth

# 8. Calculate Standard Deviation across time
# JEDI/SABER uses this to scale the 'trust' in the background
std_dev = errors.std(dim='time')

# 9. Save as NetCDF for JEDI SABER block
std_dev.to_netcdf("anemoi_error_stats.nc")

print("SABER error statistics generated for AIESDA.")


# 10. Load your Background (Anemoi) and final Analysis (JEDI output)
background = xr.open_dataset("ncmrwf_anemoi_bg.nc")
analysis = xr.open_dataset("aiesda_final_analysis.nc") # Generated after JEDI run

# 11. Calculate the Increment (Analysis - Background)
increment = analysis['air_temperature'] - background['air_temperature']

# 12. Create the Visualization
fig = plt.figure(figsize=(12, 8))
ax = plt.axes(projection=ccrs.PlateCarree())

# 13. Add Geographic features for context
ax.set_extent([65, 98, 5, 38], crs=ccrs.PlateCarree()) # Zoom into India region
ax.coastlines()
ax.add_feature(cfeature.BORDERS, linestyle=':')
ax.add_feature(cfeature.STATES, edgecolor='gray', alpha=0.5)

# 14. Plot the Increment as a filled contour (using a divergent colormap)
increment.plot(ax=ax, transform=ccrs.PlateCarree(),
               cmap='RdBu_r', center=0,
               cbar_kwargs={'label': 'Temperature Increment (K)'})

plt.title("AIESDA: Analysis Increment (JEDI Analysis - Anemoi Background)")
plt.show()

# 15. Load the AIESDA Analysis (The "Starting Point" you created with JEDI)
analysis_state = xr.open_dataset("aiesda_final_analysis.nc")

# 16. Configure the Anemoi Rollout (e.g., a 72-hour forecast)
# This uses the 'anemoi-inference' runner
runner = ai.Runner(checkpoint="path/to/anemoi_model.ckpt")
forecast_rollout = runner.run(
    initial_state=analysis_state,
    lead_time=72,      # 3-day forecast
    frequency="6h"     # Output every 6 hours
)

# 17. Load the "Truth" (The Monitobs Observations)
# In AIESDA, we verify against independent observations not used in DA
obs_truth = ads.open_dataset("monitobs_independent_verify.zarr")

# 18. Calculate RMSE (Root Mean Square Error) for the Rollout
rmse = ((forecast_rollout - obs_truth)**2).mean(dim=['lat', 'lon']).compute()**0.5

# 19. Plot the Error Growth
plt.figure(figsize=(10, 5))
plt.plot(rmse.lead_time, rmse.air_temperature, marker='o', label='AIESDA (ML + DA)')
plt.xlabel("Lead Time (Hours)")
plt.ylabel("RMSE (Kelvin)")
plt.title("AIESDA Verification: Forecast Error vs. Monitobs Observations")
plt.grid(True)
plt.legend()
plt.show()
