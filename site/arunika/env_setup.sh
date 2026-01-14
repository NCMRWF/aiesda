#!/bin/bash
# ==============================================================================
# AIESDA Environment Setup for NCMRWF Mihir Cluster
# Purpose: Dynamic path management for Monitobs inheritance and JEDI/Anemoi
# ==============================================================================

# 1. CORE DIRECTORIES
# Replace these with your actual local home and scratch directories
export HOMEDIR="${HOMEDIR:-/home/ncmrwf/.......}"
export SCRATCH_DIR="/gpfs/fs1/scratch/$(whoami)/aiesda_run"
export LOG_DIR="${HOMEDIR}/logs"

# 2. LEGACY MONITOBS PATHS (The "Path Migration")
# Instead of hard-coding in Python, these are now injected via environment
export DATA_ROOT="/home/ncmrwf/....../tanks"
export BUFR_TABLES="${HOMEDIR}/legacy/bufr_tables"
export BLACKLIST_FILE="${HOMEDIR}/config/station_blacklist.txt"

# 3. HPC MODULE LOADING (NCMRWF Stack)
# Tailored for Mihir's Intel/Cray environment
module purge
module load intel/19.0.1.144
module load cray-mpich
module load python/3.10-anaconda
module load hdf5/1.10.5
module load netcdf/4.7.1

# 4. PYTHON ENVIRONMENT
# Source your specific AIESDA conda environment
source activate aiesda_env
export PYTHONPATH="${HOMEDIR}/scripts:${PYTHONPATH}"

# 5. JEDI / SABER SPECIFICS
export JEDI_BIN="/home/ncmrwf/jedi/bin"
export SABER_DATA="${HOMEDIR}/config/saber"

# Create necessary runtime directories
mkdir -p ${SCRATCH_DIR} ${LOG_DIR}

echo "--- AIESDA Environment Loaded Successfully ---"
echo "Active DTG Root: ${DATA_ROOT}"
echo "----------------------------------------------"
