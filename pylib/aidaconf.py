#! python3
"""
Artificial Intelligence Data Assimilation Orchastation Library
Created on Wed Jan 14 19:45:25 2026
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
aidaconf.py
"""

import argparse
import logging
import xarray
import numpy 
from datetime import datetime, timedelta
import ailib
import dalib
import yaml
import dynlib
import aidadic

class AidaConfig:
    def __init__(self, args):
        self.cdate = args.date
        self.cycle = args.cycle
        self.expid = args.expid
        self.home = os.environ.get('AIESDA_HOME', os.getcwd())
        
        # All path logic lives HERE ONLY
        self.WORK_DIR = f"{self.home}/work/{self.expid}/{self.cdate}/{self.cycle}"
        self.OBSDIR = f"{self.WORK_DIR}/obs"
        self.GESDIR = f"{self.WORK_DIR}/guess"
        self.OUTDIR = f"{self.WORK_DIR}/analysis"
        self.STATICDIR = f"{self.home}/static"
        
        # Automatic directory creation
        for path in [self.OBSDIR, self.GESDIR, self.OUTDIR]:
            os.makedirs(path, exist_ok=True)

class BaseWorker:
    """Handles shared logging and file checking for all tasks."""
    def __init__(self, conf: AidaConfig):
        self.conf = conf
        self.logger = logging.getLogger(self.__class__.__name__)

    def check_inputs(self, file_list):
        for f in file_list:
            if not os.path.exists(f):
                self.logger.error(f"Missing: {f}")
                return False
        return True

class SurfaceAssimWorker(BaseWorker):
    """Refactored Worker: Uses a persistent AI engine."""
    def __init__(self, conf: AidaConfig, ai_engine: ailib.AnemoiInterface):
        super().__init__(conf)
        self.ai_engine = ai_engine  # Injected from main loop
        
    def run(self):
        self.logger.info(f"Processing Surface for {self.conf.cdate}")
        # Logic for JEDI interactions via dalib or loss functions via ailib
        # Example: Using the custom loss for training/analysis
        # cost = ailib.aiesda_loss(pred, target, background)
        pass

class Orchestrator:
    """Manages the full multi-cycle production run."""
    def __init__(self, config_path):
        with open(config_path, "r") as f:
            self.full_config = yaml.safe_load(f)
        
        # CRITICAL: Init AI Engine ONCE for the whole experiment
        self.ai_engine = ailib.AnemoiInterface(
            model_path=self.full_config.get("model_ckpt")
        )
        # Initialize the JEDI bridge
        self.bridge = JEDIModelBridge(config=self.full_config)

    def start_production(self):
        """High-level loop over cycles."""
        """Loop logic for multi-day windows using self.ai_engine """
        """Loop through dates and bridge them to JEDI."""
        # 1. Get standardized background from AI model
        # background = self.bridge.prepare_jedi_background("raw_ai_output.nc")
        
        # 2. Pass background to JEDI UFO operator (via dalib)
        # h_x = dalib.UFOInterface(...).simulate(background)
        pass


class ModelPassport:
    """
    Strict Multi-Factor Authenticator for NWP and AI Models.
    Identifies and verifies datasets based on aidadic.MODEL_REGISTRY using explicit naming.
    """
    
    @staticmethod
    def identify(dataset: xarray.Dataset, config=None):
        """
        Main entry point: Identifies the model identity and validates all factors.
        Returns an initialized Interface class instance if verification passes.
        """
        # 1. Identity Search (Attributes & Biometric Grid)
        model_key = ModelPassport._find_registry_key(dataset)
        
        if not model_key:
            logging.error("Passport Denied: Dataset identity could not be verified against Registry.")
            raise PermissionError("ModelPassport: No matching model credentials found.")

        # 2. Strict Multi-Factor Checklist (Resolution, Variables, Integrity)
        ModelPassport.verify_factors(dataset, model_key)
        
        # 3. Secure Routing to Interface
        logging.info(f"Passport Verified: Access granted for {model_key.upper()}.")
        interface_path = aidadic.MODEL_REGISTRY[model_key]["interface_class"]
        
        return ModelPassport._get_interface_instance(interface_path, config)

    @staticmethod
    def _find_registry_key(dataset):
        """Tier 1 & 2: Identifies the model key using metadata and vertical fingerprints."""
        attribute_string = str(dataset.attrs).lower()
        
        for key, specs in aidadic.MODEL_REGISTRY.items():
            # Check for explicit metadata identity
            if key in attribute_string:
                return key
            
            # Biometric check: Compare vertical coordinate values
            if "vertical_levels" in specs and ("level" in dataset.coords or "lev" in dataset.coords):
                data_coords = dataset.coords.get("level", dataset.coords.get("lev"))
                data_levels = numpy.sort(data_coords.values)
                
                # Retrieve actual pressure values from aidadic via the fingerprint key
                registry_levels = numpy.sort(aidadic.GRID_VALUES.get(specs["vertical_levels"], []))
                
                # Use numpy.allclose to handle floating point precision in coordinate arrays
                if len(data_levels) == len(registry_levels):
                    if numpy.allclose(data_levels, registry_levels, atol=1e-3):
                        return key
        return None

    @staticmethod
    def verify_factors(dataset, model_key):
        """Tier 3: Performs an audit of the scientific integrity of the data."""
        specs = aidadic.MODEL_REGISTRY[model_key]
        
        # Factor A: Horizontal Resolution Check
        if "horizontal_res" in specs and specs["horizontal_res"] is not None:
            longitude_resolution = float(dataset.lon.diff("lon").mean())
            if not numpy.isclose(longitude_resolution, specs["horizontal_res"], atol=0.01):
                raise ValueError(f"Passport Denied: Resolution {longitude_resolution} does not match {model_key} standard.")

        # Factor B: Mandatory Variable Check
        missing_variables = [var for var in specs.get("required_vars", []) if var not in dataset.variables]
        if missing_variables:
            raise ValueError(f"Passport Denied: Missing mandatory variables {missing_variables} for {model_key}.")

        # Factor C: Data Integrity (Strict NaN check)
        if not specs.get("allow_nans", True):
            if dataset.to_array().isnull().any():
                raise ValueError(f"Passport Denied: {model_key} dataset contains invalid NaN values.")

    @staticmethod
    def _get_interface_instance(path, config):
        """Instantiates the interface class dynamically based on the registry path."""
        module_name, class_name = path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        interface_class = getattr(module, class_name)
        return interface_class(config=config)


class JEDIModelBridge:
    """
    A high-level bridge in dalib.py that connects any AI/NWP forecast
    output to the JEDI/UFO observation operators.
    """

    def __init__(self, config=None):
        self.config = config or {}

    def prepare_jedi_background(self, model_file):
        """
        Uses the ModelPassport to identify and verify the file,
        then standardizes it for UFO using aidadic mappings.
        """
        # 1. Open dataset
        dataset = xarray.open_dataset(model_file)

        # 2. Authenticate and identify via the Passport
        # This handles identity, grid fingerprints, and strict data integrity checks.
        interface = ModelPassport.identify(dataset, config=self.config)

        # 3. Retrieve the specific model key for dictionary lookups
        # (Assuming identify or the interface knows its registry key)
        model_key = interface.get_model_key()
        specs = aidadic.MODEL_REGISTRY[model_key]

        # 4. Standardize Variables using the flattened aidadic mapping
        # This renames model-specific names (e.g., 'spfh') to JEDI names (e.g., 'specific_humidity')
        mapping = specs.get("mapping", {})
        # Inverse mapping: {model_name: jedi_name} -> {jedi_name: model_name}
        # But for preparation, we usually want: dataset.rename({model_name: jedi_name})
        rename_dict = {v: k for k, v in mapping.items() if v in dataset.variables}
        standardized_ds = dataset.rename(rename_dict)

        # 5. Coordinate Standardization
        # Ensure vertical coordinate is consistently named 'level' or 'pressure' for JEDI
        if "lev" in standardized_ds.coords:
            standardized_ds = standardized_ds.rename({"lev": "level"})

        logging.info(f"JEDI Bridge: Standardized {model_key} using {len(rename_dict)} variable mappings.")

        return standardized_ds

    def generate_geovals(self, standardized_ds, output_path):
        """
        Writes the standardized dataset to the format JEDI expects for GeoVaLs.
        """
        # Logic for writing IODA-compliant files goes here
        pass




"""
Public functions
"""


