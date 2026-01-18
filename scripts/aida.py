#! python3
"""
Artificial Intelligence Data Assimilation Run Script
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
aida.py
"""

import argparse
import logging
from aidaconf import AidaConfig, SurfaceAssimWorker, Orchestrator
from ailib import AnemoiInterface
from dalib import UFOInterface
from metlib import AssimilationValidator

def main():
    # 1. Parse Arguments (Centralized via aidaconf)
    parser = argparse.ArgumentParser(description="AIESDA Production Suite")
    parser.add_argument('--date', required=True, help='YYYYMMDD')
    parser.add_argument('--cycle', required=True, help='HH (00, 06, 12, 18)')
    parser.add_argument('--expid', default='exp_v1', help='Experiment ID')
    parser.add_argument('--config', required=True, help='Path to model_config.yaml')
    args = parser.parse_args()

    # 2. Initialize Single Source of Truth for Paths
    conf = AidaConfig(args)
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("AIESDA_ORCHESTRATOR")

    # 3. Load AI Model Engine (Persistent in VRAM)
    # We load this here so it can be reused across different worker tasks
    ai_engine = AnemoiInterface(model_path=args.config)

    logger.info(f"--- Starting AIESDA Cycle: {conf.cdate} {conf.cycle} ---")

    # 4. TASK A: Prepare Background for JEDI
    # Pulls from Anemoi history (Zarr) and creates a JEDI-compliant NetCDF
    bg_file = f"{conf.GESDIR}/bg_{conf.cdate}_{conf.cycle}.nc"
    ai_engine.prepare_background_from_anemoi(
        zarr_path=f"{conf.home}/data/history.zarr",
        target_time=f"{conf.cdate}T{conf.cycle}:00:00",
        output_nc=bg_file
    )

    # 5. TASK B: Surface Assimilation Worker
    # This worker handles the QC and the AI-based analysis logic
    sfc_worker = SurfaceAssimWorker(conf, ai_engine)
    try:
        sfc_worker.run()
    except Exception as e:
        logger.error(f"Surface Worker Failed: {e}")
        sys.exit(1)

    # 5.5 TASK: Validation and Diagnostics
    validator = AssimilationValidator(conf)
    inc_ds = validator.calculate_increment(analysis_file, bg_file)
    stats = validator.compute_stats(inc_ds)

    print(f"Mean Increment (Bias Check): {stats['mean_increment']}")

    # Generate plots for critical variables
    for var in ['air_temperature', 'eastward_wind']:
        path = validator.plot_diagnostic_maps(var, analysis_file, bg_file)
        print(f"Diagnostic plot saved to: {path}")

    # 6. TASK C: Forecast Rollout
    # Use the Analysis from JEDI/Worker to start the next forecast
    analysis_file = f"{conf.OUTDIR}/analysis_{conf.cdate}_{conf.cycle}.nc"
    forecast_file = f"{conf.OUTDIR}/forecast_{conf.cdate}_{conf.cycle}.nc"
    
    ai_engine.rollout_forecast(
        analysis_nc=analysis_file,
        output_nc=forecast_file,
        lead_time_hours=6
    )

    logger.info("--- Cycle Complete ---")


    # 7. SENSITIVITY ANALYSIS (Optional Diagnostic)
    logger.info("Running sensitivity analysis for Temperature...")
    sens_ds = validator.run_sensitivity_test(
        ai_engine=ai_engine, 
        base_analysis_file=analysis_file, 
        var_name='air_temperature'
    )

    # Plot where the model 'feels' the data most
    sens_plot = validator.plot_sensitivity(sens_ds, 'air_temperature')
    logger.info(f"Sensitivity map generated at {sens_plot}")


    # Current Cycle files
    current_an = conf.OUTDIR + "/analysis.nc"
    # Path to the forecast generated 6 hours ago
    prev_fc = f"{conf.home}/work/{conf.expid}/{prev_date}/{prev_cycle}/analysis/forecast_6h.nc"

    if os.path.exists(prev_fc):
        jump_ds, alerts = validator.check_temporal_consistency(current_an, prev_fc)
        for msg in alerts:
            logger.warning(msg)
        validator.plot_temporal_tendency(jump_ds, 'air_temperature')

if __name__ == "__main__":
    main()
