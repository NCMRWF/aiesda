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


class ModelFactory:
    """
    Orchestration Factory to route datasets to the correct 
    NCMRWF or AI interface.
    """
    @staticmethod
    def get_interface(ds, config=None):
        model_name = ds.attrs.get('model_name', ds.attrs.get('source', '')).lower()
        num_levels = len(ds.coords.get('level', ds.coords.get('lev', [])))

        # 1. NCMRWF National Systems
        if 'bharat' in model_name:
            return dynlib.BharatInterface(config=config)
        
        if 'mithuna' in model_name or 'midhuna' in model_name: # Handle legacy naming in files
            return dynlib.MithunaInterface(config=config)

        # 2. Global AI Foundation Models (ailib)
        if num_levels == 37:
            # Differentiate by variable names (MERRA-2 vs ERA5)
            if 'T' in ds.variables: 
                return ailib.PrithviInterface(config=config)
            return ailib.GraphCastInterface(config=config)
            
        if num_levels == 13:
            if 'z' in ds.variables: 
                return ailib.PanguWeatherInterface(config=config)
            return ailib.FourCastNetInterface(config=config)

        # 3. Default to Anemoi if checkpoint is provided
        if 'anemoi' in model_name:
            return ailib.AnemoiInterface(config=config)

        raise ValueError(f"Model Factory: Identification failed for {model_name} ({num_levels} levels).")



class JEDIModelBridge:
    """
    A high-level bridge in dalib.py that connects any AI forecast 
    output to the JEDI/UFO observation operators.
    """

    def __init__(self, config=None):
        self.config = config or {}

    def prepare_jedi_background(self, model_file):
        """
        Takes a raw AI netCDF, identifies the model, 
        standardizes it, and prepares it for UFO.
        """
        # 1. Open dataset
        ds = xarray.open_dataset(model_file)

        # 2. Use ailib's Factory to identify the interface
        # This keeps dalib.py clean of model-specific renaming logic
        ai_bridge = ailib.ModelFactory.get_interface(ds, config=self.config)
        
        # 3. Standardize variables (T, Q, U, V, Z) and Coordinates (lev)
        standardized_ds = ai_bridge.prepare_state(ds)

        print(f"Detected and standardized background from: {type(ai_bridge).__name__}")
        
        return standardized_ds

    def generate_geovals(self, standardized_ds, output_path):
        """
        Writes the standardized dataset to the format JEDI expects 
        for GeoVaLs (Model variables at observation locations).
        """
        # Implementation depends on your DataManager.write_ioda logic
        pass

"""
Public functions
"""

def get_common_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', required=True, help='Forecast date YYYYMMDD')
    parser.add_argument('--cycle', required=True, help='Cycle hour (e.g., 00, 06, 12, 18)')
    parser.add_argument('--expid', default='test_run', help='Experiment ID')
    return parser


def get_aida_args(description="AIESDA Script"):
    """Centralized argument parser for all AIESDA scripts."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--date', type=str, required=True, help='Date in YYYYMMDD format')
    parser.add_argument('--cycle', type=str, required=True, help='Cycle (00, 06, 12, 18)')
    parser.add_argument('--expid', type=str, default='test', help='Experiment ID')
    # Add other common flags found in both scripts here
    return parser

def run_assimilation(args, cfg):
    """
    Core AI Surface Assimilation Logic.
    This replaces the duplicated code formerly at the top of the script.
    """
    work_dir = cfg['WORK_DIR']
    print(f"Executing Surface AI Assimilation in {work_dir}")

    # ... (Actual AI model loading and NCMRWF data processing goes here) ...
    # e.g., model = load_model(f"{cfg['HOME']}/models/sfc_model.pth")

def run_surface_assimilation(args, work_dir):
    """Core logic moved into a function to be callable from aiesda.py"""
    # ... (Actual AI model loading and data processing logic goes here) ...
    print(f"Processing surface data for {args.date} in {work_dir}")

def run_assim_logic(conf):
    """
    Core Logic: No longer parses args.
    Uses the attributes provided by the AidaConfig instance.
    """
    # Use paths provided by aidaconf.py
    # Example: conf.OBSDIR, conf.GESDIR, conf.OUTDIR
    print(f"--- Surface Assimilation Phase ---")
    print(f"Working Directory: {conf.DATADIR}")
    print(f"Target Date: {conf.cdate}")

    # Logic to load AI model using paths from conf
    model_path = os.path.join(conf.STATICDIR, "sfc_model_v1.pth")

    # ... Process Surface Data ...
    # result = ai_engine.predict(input_data=conf.GESDIR)

    print(f"Surface Analysis complete for {conf.expid}")

def run_cycle(conf):
    """
    Core logic converted to a function. 
    Uses the 'conf' object for all path references.
    """
    print(f"Processing Surface Data in: {conf.OUTDIR}")
    
    # Use paths defined in aidaconf.py
    obs_file = os.path.join(conf.OBSDIR, f"sfc_obs_{conf.cdate}.nc")
    guess_file = os.path.join(conf.GESDIR, f"sfc_guess_{conf.cdate}.nc")
    
    # ... AI Inference Logic Here ...
    # result = model.predict(obs_file, guess_file)
    
    output_path = os.path.join(conf.OUTDIR, "analysis_sfc.nc")
    print(f"Analysis saved to {output_path}")

def execute_task(conf):
    """
    Main entry point for Surface Assimilation.
    Receives an AidaConfig object with all paths pre-calculated.
    """
    # Use paths directly from the AidaConfig object
    obs_path = conf.OBSDIR
    guess_path = conf.GESDIR
    output_path = conf.OUTDIR
    
    print(f"--- Surface AI Assimilation ---")
    print(f"Reading Observations from: {obs_path}")
    print(f"Reading Background from: {guess_path}")
    
    # AI Model Logic here
    # Example: model = load_model(conf.STATICDIR + '/sfc_weights.pth')
    
    print(f"Saving Analysis to: {output_path}")

