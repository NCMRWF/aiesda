import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pyiodaconv import ioda_conv_engines as iconv

# Place a single Dirac spike at NCMRWF (Noida/Delhi)
lats = np.array([28.6], dtype='float32')
lons = np.array([77.4], dtype='float32')
# A +1.0 Kelvin 'innovation'
temp = np.array([1.0], dtype='float32')

writer = iconv.IodaWriter("dirac_obs_noida.nc", [("latitude", "float"), ("longitude", "float")])

data = {
    ('air_temperature', 'ObsValue'): temp,
    ('air_temperature', 'ObsError'): np.array([1.0], dtype='float32'),
    ('latitude', 'MetaData'): lats,
    ('longitude', 'MetaData'): lons,
}
writer.BuildIoda(data, {})
print("Dirac observation generated at 28.6N, 77.4E")



def gaussian_spread(lat_center, lon_center, lats, lons, length_scale_km):
    # Rough approximation of B-Matrix spatial correlation (Gaussian)
    # 1 degree lat ~ 111km
    dist_sq = ((lats - lat_center)**2 + (lons - lon_center)**2) * (111.0**2)
    return np.exp(-dist_sq / (2 * (length_scale_km**2)))

# 1. Setup Grid over India
lat = np.linspace(5, 38, 100)
lon = np.linspace(65, 98, 100)
lon_grid, lat_grid = np.meshgrid(lon, lat)

# 2. Define Seasonal Scales (in km)
monsoon_scale = 150.0  # Tighter, convective focus
winter_scale = 400.0   # Broader, synoptic focus

# 3. Calculate Influence Fields
noida_lat, noida_lon = 28.6, 77.4
monsoon_field = gaussian_spread(noida_lat, noida_lon, lat_grid, lon_grid, monsoon_scale)
winter_field = gaussian_spread(noida_lat, noida_lon, lat_grid, lon_grid, winter_scale)

# 4. Visualization
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), subplot_kw={'projection': ccrs.PlateCarree()})

for ax, field, title in zip([ax1, ax2], [monsoon_field, winter_field],
                             ['Monsoon Scale (150km)', 'Winter Scale (400km)']):
    ax.set_extent([68, 88, 18, 38]) # Focus on North/Central India
    ax.coastlines()
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.STATES, edgecolor='gray', alpha=0.3)

    cf = ax.contourf(lon_grid, lat_grid, field, levels=10, cmap='YlGnBu')
    ax.plot(noida_lon, noida_lat, 'ro', markersize=8) # NCMRWF Location
    ax.set_title(f"AIESDA Dirac Test: {title}")
    plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.05, label='Influence Weight')

plt.tight_layout()
plt.show()
