#! python3
"""
Data Assimilation Interface Library
Created on Wed Jan 14 19:41:36 2026
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
dalib.py
"""
import numpy
import pandas
import xarray
import ufo
import oops
import saber
import ioda
from pyiodaconv import ioda_conv_engines as iodaconv
import aidadic

class JEDI_Interface:
    """Interface class to be used by the JEDI-OOPS wrapper."""
    
    def __init__(self, config):
        self.config = config
        self.geometry = self._setup_geometry()

    def _setup_geometry(self):
        # Define grid based on NCMRWF standards (e.g., IMDAA 12km)
        pass

    def apply_observation_operator(self, state):
        """Equivalent to H(x) in JEDI."""
        # Call your AI model from ailib here
        # return simulated_observations
        pass

    def compute_cost_gradient(self, state, observations):
        """Calculates grad(J) for the JEDI minimizer."""
        # Logic for dJ/dx
        pass

class UFOInterface:
    """Interface to JEDI Unified Forward Operators within dalib."""

    def __init__(self, obs_config_yaml):
        """
        Initializes UFO with a specific configuration (e.g., surface.yaml or satrad.yaml).
        """
        self.config = ufo.ObsOperatorConfig(obs_config_yaml)
        self.obs_space = None 

    def setup_obs_space(self, ioda_file):
        """Connects to the IODA observation database."""
        self.obs_space = ioda.ObsSpace(ioda_file)

    def compute_simulated_obs(self, model_state):
        """
        The H(x) operation using JEDI UFO.
        model_state: The state object (e.g., from ailib or anemoi)
        """
        # 1. Convert AIESDA/Anemoi state to JEDI State if necessary
        jedi_state = self._to_jedi_format(model_state)
        
        # 2. Initialize the specific Forward Operator (e.g., Radiance, VertInterp)
        hop = ufo.ObsOperator(self.obs_space, self.config)
        
        # 3. Create a container for simulated observations (H(x))
        y_sim = ioda.ObsVector(self.obs_space)
        
        # 4. Apply the operator
        hop.simulate_obs(jedi_state, y_sim)
        
        return y_sim

    def _to_jedi_format(self, state):
        """Helper to ensure tensors are JEDI-ready."""
        # Logic to map xarray/torch to JEDI fieldsets
        pass

class SaberInterface:
    def __init__(self, conf):
        self.conf = conf
        try:
            import oops
            import saber
            self.jedi_ready = True
        except ImportError:
            self.jedi_ready = False

    def apply_localization(self, increments):
        if not self.jedi_ready:
            print("SABER not found. Skipping localization.")
            return increments
        # Logic to wrap increments in FieldSet and apply SABER block
        return increments


    def compute_error_stats(forecast_zarr, truth_zarr, output_nc):
        """Calculate B-Matrix variance (StdDev) from historical AI errors."""
        
        fcs = anemoids.open_dataset(forecast_zarr)
        truth = anemoids.open_dataset(truth_zarr)
        
        # Vectorized error calculation
        std_dev = (fcs - truth).std(dim='time')
        std_dev.to_netcdf(output_nc)
        return output_nc


class SurfaceManager:
    """Handles QC and JEDI-formatting for surface observations."""

    def __init__(self, config):
        self.max_temp = config.get('max_temp', 325.0) # ~52°C
        self.min_temp = config.get('min_temp', 230.0) # ~-43°C
        self.std_threshold = config.get('std_threshold', 3.0)

    def apply_quality_control(self, df):
        """
        Performs Gross Error Check and Spike Removal.
        df: pandas.DataFrame with 'value', 'lat', 'lon'
        """
        # 1. Range Check
        df = df[(df['value'] > self.min_temp) & (df['value'] < self.max_temp)]

        # 2. Step/Spike Check (if temporal data is available)
        # 3. Spatial Consistency (z-score check against neighbors)
        z_scores = (df['value'] - df['value'].mean()) / df['value'].std()
        df = df[abs(z_scores) < self.std_threshold]

        return df

    @staticmethod
    def height_correction(obs_value, obs_elev, model_elev):
        """
        Adjusts temperature based on lapse rate (standard 6.5 K/km)
        to account for topography mismatch.
        """
        lapse_rate = 0.0065
        corrected_value = obs_value + lapse_rate * (obs_elev - model_elev)
        return corrected_value

    def to_ioda(self, df, filename):
        """Converts cleaned DataFrame to JEDI IODA NetCDF."""
        # Implementation of IODA Grouping (ObsValue, ObsError, MetaData)
        pass


class RadianceObserver:
    """Handles JEDI UFO Observation Operators for Satellites (e.g., AMSU-A, IASI)."""
    
    def __init__(self, sensor_id, channels, crtm_coeff_path):
        self.sensor_id = sensor_id
        self.channels = channels
        # JEDI UFO Config for Radiance
        self.ufo_config = {
            "name": "Radiance",
            "sensor": self.sensor_id,
            "channels": self.channels,
            "Absorbers": ["H2O", "O3"],
            "CoefficientPath": crtm_coeff_path
        }


    def prepare_geovals(self, model_ds):
        """
        Extracts vertical profiles from the AI model (Anemoi) into JEDI GeoVaLs.
        Uses aidadic for consistent variable naming.
        """
        # Create a reverse mapping: { 'anemoi_name': 'jedi_name' }
        # This helps us identify which Anemoi variable corresponds to which JEDI GeoVaL
        anemoi_to_jedi = {v: k for k, v in aidadic.jedi_anemoi_var_mapping.items()}
        
        geovals = {}
        
        # Iterating through the dataset to map Anemoi keys to JEDI keys
        for anemoi_var in model_ds.data_vars:
            if anemoi_var in anemoi_to_jedi:
                jedi_name = anemoi_to_jedi[anemoi_var]
                geovals[jedi_name] = model_ds[anemoi_var].values
                print(f"Mapped Anemoi '{anemoi_var}' to JEDI GeoVaL '{jedi_name}'")
        
        # Handle special cases not in the standard 2D mapping (like surface pressure)
        if 'surface_pressure' not in geovals and 'sp' in model_ds:
             geovals['surface_pressure'] = model_ds['sp'].values

        return geovals


    def compute_hofx(self, geovals, obs_space):
        """
        Computes H(x) - the Simulated Brightness Temperatures.
        This uses the JEDI UFO Radiance operator + CRTM.
        """
        # 1. Initialize the UFO operator
        hop = ufo.ObsOperator(obs_space, self.ufo_config)
        
        # 2. Container for simulated observations
        hofx = ioda.ObsVector(obs_space)
        
        # 3. Simulate observations based on the GeoVaLs (model state)
        hop.simulate_obs(geovals, hofx)
        
        return hofx


class StabilityChecker:
    """Checks the physical consistency of vertical atmospheric profiles."""

    def __init__(self):
        # Constants for meteorology
        self.dry_lapse_rate = 0.0098  # K/m (approximate)
        self.standard_levels = numpy.array(aidadic.crtm_standard_levels)

    def check_static_stability(self, dataset):
        """
        Calculates the vertical temperature gradient (dT/dP).
        In the troposphere, temperature should generally decrease with altitude.
        """
        # Ensure we are working with the correct variables via aidadic
        temp_var = aidadic.jedi_anemoi_var_mapping.get('air_temperature')
        
        if temp_var not in dataset:
            return None

        # Calculate the derivative of Temperature with respect to Level
        # In meteorology, we look for 'Stability' where d(Potential Temp)/dz > 0
        temperatures = dataset[temp_var]
        
        # Simple check for negative temperature values (Kelvin check)
        if (temperatures <= 0).any():
            print("CRITICAL: Negative Kelvin values detected in profile.")
            return False

        # Check for extreme lapse rates between CRTM layers
        # A jump of > 10K between adjacent layers in the 100-level grid is likely an interpolation error
        temp_diff = temperatures.diff(dim='lev')
        if (numpy.abs(temp_diff) > 10.0).any():
            print("WARNING: Unphysical temperature jump detected between layers.")
            return False

        return True

    def calculate_potential_temperature(self, dataset):
        """Computes Potential Temperature (Theta) for stability analysis."""
        # Mapping names via aidadic
        t_name = aidadic.jedi_anemoi_var_mapping.get('air_temperature')
        p_name = 'lev' # CRTM pressure levels
        
        # Standard formula: Theta = T * (P0 / P)^(R/Cp)
        p0 = 1000.0  # Reference pressure in hPa
        kappa = 0.286
        
        theta = dataset[t_name] * (p0 / dataset[p_name])**kappa
        return theta


class RadianceBiasManager:
    """Handles Variational Bias Correction (VarBC) for satellite sensors."""

    def __init__(self, conf):
        self.conf = conf
        self.bias_dir = os.path.join(self.conf.STATICDIR, "varbc")
        self.predictors = ['constant', 'scan_angle', 'lapse_rate', 'clw']

    def load_coefficients(self, sensor_id):
        """Loads beta coefficients using full pandas name."""
        coeff_file = os.path.join(self.bias_dir, f"{sensor_id}_coeffs.csv")
        if os.path.exists(coeff_file):
            return pandas.read_csv(coeff_file).set_index('channel')
        else:
            return None

    def calculate_bias(self, sensor_id, channel_list, predictor_values):
        """Computes bias using full numpy name."""
        coeffs = self.load_coefficients(sensor_id)
        if coeffs is None:
            return numpy.zeros_like(predictor_values['constant'])

        # Logic to apply coefficients to predictors...
        pass



"""
Public functions
"""

def apply_h_operator(state, obs_data):
    """Maps model state to observation space (JEDI H-operator)."""
    # Moves the mapping logic out of the main job script
    pass

def compute_cost(analysis, background, obs, B_inv, R_inv):
    """Calculates the JEDI variational cost function."""
    # Logic for J(x)
    pass

def jedi_bind_state(state_data):
    """Utility to convert AI tensors to JEDI-compatible State objects."""
    return {"data": state_data, "metadata": "NCMRWF-AIESDA-v1"}


def write_ioda_surface_obs(output_path, lats, lons, values, errors, station_ids, var_name="air_temperature"):
    """
    Isolated IODA writer. This function encapsulates all pyiodaconv dependencies.
    """
    # 1. Define location keys for MetaData
    location_key_list = [("latitude", "float"), ("longitude", "float")]

    # 2. Instantiate the isolated writer
    writer = iodaconv.IodaWriter(output_path, location_key_list)

    # 3. Format data dictionary with JEDI-specific HDF5 groups
    data = {
        (var_name, 'ObsValue'): values.astype('float32'),
        (var_name, 'ObsError'): errors.astype('float32'),
        ('latitude', 'MetaData'): lats.astype('float32'),
        ('longitude', 'MetaData'): lons.astype('float32'),
        ('station_id', 'MetaData'): np.array(station_ids, dtype=object),
    }

    # 4. Perform the write (HDF5/NetCDF)
    writer.BuildIoda(data, {})
    return os.path.abspath(output_path)

def get_obs_window(cycle_time, hours=3):
    """Utility for time logic, moved out of the main driver."""
    from datetime import timedelta
    return cycle_time - timedelta(hours=hours), cycle_time + timedelta(hours=hours)

