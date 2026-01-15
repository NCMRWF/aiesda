
# aidaconf.py
import argparse
import os
import logging


def get_common_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', required=True, help='Forecast date YYYYMMDD')
    parser.add_argument('--cycle', required=True, help='Cycle hour (e.g., 00, 06, 12, 18)')
    parser.add_argument('--expid', default='test_run', help='Experiment ID')
    return parser

def setup_environment(args):
    """Sets up standard NCMRWF directory structures."""
    base_path = os.environ.get('AIESDA_HOME', './')
    work_dir = os.path.join(base_path, args.expid, args.date, args.cycle)
    os.makedirs(work_dir, exist_ok=True)
    
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s')
    return work_dir

def get_aida_args(description="AIESDA Script"):
    """Centralized argument parser for all AIESDA scripts."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--date', type=str, required=True, help='Date in YYYYMMDD format')
    parser.add_argument('--cycle', type=str, required=True, help='Cycle (00, 06, 12, 18)')
    parser.add_argument('--expid', type=str, default='test', help='Experiment ID')
    # Add other common flags found in both scripts here
    return parser

def config_env(args):
    """Sets up common paths and environment variables."""
    config = {}
    config['HOME'] = os.environ.get('AIESDA_HOME', os.getcwd())
    config['WORK_DIR'] = f"{config['HOME']}/work/{args.expid}/{args.date}/{args.cycle}"

    # Ensure work directory exists
    os.makedirs(config['WORK_DIR'], exist_ok=True)

    # Add project paths to sys.path to ensure imports work correctly
    sys.path.append(os.path.join(config['HOME'], 'pylib'))

    return config

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

class SurfaceAssimTask:
    def __init__(self, conf: AidaConfig):
        self.conf = conf
        # Load AI models once during initialization
        self.model_path = os.path.join(self.conf.STATICDIR, "sfc_model.pth")
        
    def run(self):
        """The actual execution logic"""
        print(f"Processing Surface Data for {self.conf.cdate}")
        # Logic for reading conf.OBSDIR and conf.GESDIR goes here
        # result = self.my_ai_model(obs, guess)
        print(f"Saving output to {self.conf.OUTDIR}")
