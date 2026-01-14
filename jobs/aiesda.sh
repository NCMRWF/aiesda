#!/bin/bash

#==============================================================================
#  Script: aiesda_python_driver.sh
#  Purpose: Drive the Anemoi-JEDI-Monitobs Python pipeline using AIESDA
#           environment standards.
#==============================================================================

# 1. SET NAMES AND PATHS
# ------------------------------------------------------------------------------
SCRIPT_NAME=$(basename $0)
export APP_NAME="AIESDA_PY_PIPELINE"

# Set base directories (adjust to your local environment)
export AIESDA_DIR=${AIESDA_DIR:-"........"}
export DATA_ROOT=${DATA_ROOT:-".........."}
export OUT_DIR="${AIESDA_DIR}/output"
export LOG_DIR="${AIESDA_DIR}/logs"

mkdir -p ${OUT_DIR} ${LOG_DIR}

# 2. TIME HANDLING (Format based on AIESDA jobs/bufr_to_obstore_mwri.sh)
# ------------------------------------------------------------------------------
# In production, CYLC_TASK_CYCLE_TIME or $1 provides the time
CYCLE_TIME=${1:-${CYLC_TASK_CYCLE_TIME:-"2026-01-14T18:00:00Z"}}

# Extract DTG (YYYYMMDDHH)
export DTG=$(date -u -d "${CYCLE_TIME}" +"%Y%m%d%H")
export YYYY=$(date -u -d "${CYCLE_TIME}" +"%Y")
export MM=$(date -u -d "${CYCLE_TIME}" +"%m")
export DD=$(date -u -d "${CYCLE_TIME}" +"%d")
export HH=$(date -u -d "${CYCLE_TIME}" +"%H")

echo "[${SCRIPT_NAME}] Processing Cycle: ${DTG}"

# 3. CONSTRUCT FILE NAMES
# ------------------------------------------------------------------------------
export OBS_FILE="${OUT_DIR}/aiesda_obs_sfc_${DTG}.nc"
export BG_FILE="${OUT_DIR}/ncmrwf_anemoi_bg_${DTG}.nc"
export AN_FILE="${OUT_DIR}/aiesda_final_analysis_${DTG}.nc"

# 4. ENVIRONMENT CHECK
# ------------------------------------------------------------------------------
# Load required Python/JEDI stack if on Mihir/Arunika
# module load aiesda_stack/v1.0

# 5. EXECUTE PYTHON PIPELINE
# ------------------------------------------------------------------------------
# Pass cycle time and file paths as environment variables to the Python script
export CYCLE_TIME_STR="${YYYY}-${MM}-${DD}T${HH}:00:00Z"

echo "[${SCRIPT_NAME}] Executing Python pipeline..."

python3 ${AIESDA_DIR}/scripts/aiesda_pipeline.py << EOF
import os
import sys

# The Python script captures environment variables set by this driver
os.environ['CYCLE_TIME'] = "${CYCLE_TIME_STR}"
os.environ['OBS_OUTPUT'] = "${OBS_FILE}"
os.environ['BG_OUTPUT']  = "${BG_FILE}"

# Trigger the workflow you've developed
try:
    # Logic from your previous version starts here
    print(f"Executing AIESDA logic for {os.environ['CYCLE_TIME']}")
    # ... (Your Python Code Implementation) ...
    sys.exit(0)
except Exception as e:
    print(f"Error: {str(e)}")
    sys.exit(1)
EOF

# 6. EXIT STATUS CHECK (Standard AIESDA Logic)
# ------------------------------------------------------------------------------
ERR=$?
if [ $ERR -ne 0 ]; then
    echo "[${SCRIPT_NAME}] FAILED at cycle ${DTG}"
    exit $ERR
else
    echo "[${SCRIPT_NAME}] COMPLETED successfully for ${DTG}"
    echo "Files generated: ${OBS_FILE}, ${BG_FILE}"
fi

exit 0
