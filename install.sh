#!/bin/bash
# ==============================================================================
# AIESDA Unified Installer (WSL/Laptop & HPC)
# ==============================================================================

# --- 1. Configuration ---
# Read version, clean whitespace, and strip leading zeros (2026.01 -> 2026.1)
VERSION=$(cat VERSION 2>/dev/null | tr -d '[:space:]' | sed 's/\.0\+/\./g')
VERSION=${VERSION:-"dev"}  # If VERSION is empty or file missing, default to 'dev'
PROJECT_NAME="aiesda"
PROJECT_ROOT=$(pwd)
BUILD_DIR="${HOME}/build/${PROJECT_NAME}_build_${VERSION}"
BUILD_WORKSPACE="${HOME}/build/docker_build_tmp"
MODULE_PATH="${HOME}/modulefiles"
PKG_MODULE_FILE="${MODULE_PATH}/${PROJECT_NAME}/${VERSION}"
REQUIREMENTS="${PROJECT_ROOT}/requirements.txt"
AIESDA_INSTALLED_ROOT="${BUILD_DIR}"
# Surgical cleanup: only removes the block between our markers
sed -i '/# >>> AIESDA_JEDI_SETUP >>>/,/# <<< AIESDA_JEDI_SETUP <<< /d' ~/.bashrc
# Extract JEDI version from requirements.txt
# Looks for the line starting with 'jedi==' or 'jedi>=' within the file
JEDI_VERSION=$(grep -iE "^jedi[>=]*" "$REQUIREMENTS" | head -n 1 | sed 's/[^0-9.]*//g')
# Fallback if not found
JEDI_VERSION=${JEDI_VERSION:-"latest"}
echo "🔍 Detected JEDI Target Version: ${JEDI_VERSION}"
JEDI_MODULE_FILE="${MODULE_PATH}/jedi/${JEDI_VERSION}"

NATIVE_BLOCKS=(
    "Numerical and Data Handling"
    "Geospatial Visualization"
    "AI and Deep Learning"
    "Meteorological Specifics"
    "Configuration and Logging Libraries"
    "ECMWF Anemoi and Related Stack"
)

COMPLEX_BLOCKS=(
    "NCAR Legacy Graphics and InOut"
    "JCSDA JEDI and Related Stack"
)
###########################################################

# --- 2. Pre-flight Checks (WSL & OS Detection) ---
IS_WSL=false
if grep -qi "microsoft" /proc/version 2>/dev/null || grep -qi "wsl" /proc/sys/kernel/osrelease 2>/dev/null; then
    IS_WSL=true
    echo "💻 WSL Detected."
else
    echo "🐧 Native Linux/HPC Detected."
fi
###########################################################

# --- 3. Self-Healing: Check for pip ---
if ! command -v pip3 &> /dev/null; then
    echo "python3-pip not found. Attempting to install..."
    if [ "$IS_WSL" = true ]; then
        echo "Please enter your password to install pip:"
        sudo apt update && sudo apt install python3-pip -y
    else
        echo "❌ ERROR: pip3 is missing. Please contact your SysAdmin to install it."
        exit 1
    fi
fi
###########################################################

# --- 4. Helper Function (With '&' Fix) ---
get_req_block() {
    local block_name=$1
    # FIX: Escape ampersands for sed safety
    local escaped_name=$(echo "$block_name" | sed 's/&/\\&/g')
    if [ -f "$REQUIREMENTS" ]; then
        sed -n "/# === BLOCK: ${escaped_name} ===/,/# === END BLOCK ===/p" "$REQUIREMENTS" | \
            sed "/# ===/d; /^#/d; /^\s*$/d; s/[[:space:]]*#.*//g"
    fi
}
###########################################################

# --- 5. Installation Loop ---
echo "🐍 Upgrading pip..."
python3 -m pip install --user --upgrade pip --break-system-packages

for block in "${NATIVE_BLOCKS[@]}"; do
    echo "📦 Installing block: [$block]..."
    PKGS=$(get_req_block "$block")
    [ ! -z "$PKGS" ] && python3 -m pip install --user $PKGS --break-system-packages
done
###########################################################

# --- 6. Complex Block Verification ---
DA_MISSING=0

if [ "$IS_WSL" = true ]; then
    # WSL always defaults to needing the Docker JEDI bridge
    DA_MISSING=1
else
    echo "🔍 Checking native DA components (HPC Mode)..."
    DA_FOUND_COUNT=0
    TOTAL_DA_PKGS=0
    
    for block in "${COMPLEX_BLOCKS[@]}"; do
        PKGS=$(get_req_block "$block")
        for pkg in $PKGS; do
            ((TOTAL_DA_PKGS++))
            # Clean package name to get the importable module name
            lib=$(echo "$pkg" | sed 's/py//' | cut -d'=' -f1 | cut -d'>' -f1 | tr -d '[:space:]')
            if python3 -c "import $lib" &>/dev/null; then
                ((DA_FOUND_COUNT++))
            fi
        done
    done

    # Calculate how many are missing. If > 0, we need the container fallback.
    DA_MISSING=$((TOTAL_DA_PKGS - DA_FOUND_COUNT))
fi

###########################################################

# --- 7. Docker Fallback Logic ---
if [ "$DA_MISSING" -gt 0 ]; then
    echo "🐳 Missing $DA_MISSING DA components. Initializing JEDI v${JEDI_VERSION} Build..."
    
    chmod +x "${PROJECT_ROOT}/jobs/jedi_docker_build.sh"
    # PASS JEDI_VERSION instead of AIESDA VERSION
    bash "${PROJECT_ROOT}/jobs/jedi_docker_build.sh" "$JEDI_VERSION"

else
    echo "✅ No Docker fallback required."
fi


###########################################################
# --- 8. Build & Module Generation ---
echo "🏗️  Finalizing AIESDA Build..."
rm -rf "${BUILD_DIR}"
python3 setup.py build --build-base "${BUILD_DIR}"

AIESDA_INTERNAL_LIB="${BUILD_DIR}/lib/aiesda"
mkdir -p "${AIESDA_INTERNAL_LIB}"
for asset in nml yaml jobs scripts pydic pylib; do
    [ -d "${PROJECT_ROOT}/$asset" ] && cp -rp "${PROJECT_ROOT}/$asset" "${AIESDA_INTERNAL_LIB}/"
done

mkdir -p $(dirname "${PKG_MODULE_FILE}")
cat << EOF_MODULE > "${PKG_MODULE_FILE}"
#%Module1.0
## AIESDA v${VERSION}
if { [is-loaded jedi] == 0 } { catch { module load jedi/1.5.0 } }
set version      ${VERSION}
set aiesda_root  ${AIESDA_INSTALLED_ROOT}
setenv           AIESDA_VERSION  \$version
setenv           AIESDA_ROOT     \$aiesda_root/lib/aiesda
setenv           AIESDA_NML      \$aiesda_root/lib/aiesda/nml
setenv           AIESDA_YAML     \$aiesda_root/lib/aiesda/yaml
prepend-path     PYTHONPATH      \$aiesda_root/lib/aiesda/pylib
prepend-path     PYTHONPATH      \$aiesda_root/lib/aiesda/pydic
prepend-path     PATH            \$aiesda_root/lib/aiesda/scripts
prepend-path     PATH            \$aiesda_root/lib/aiesda/jobs
EOF_MODULE

echo "------------------------------------------------------------"
echo "✅ Installation Complete! Run 'source ~/.bashrc' to activate."
echo "------------------------------------------------------------"


###########################################################

# --- 9. Testing Environment ---
echo "🧪 Running Post-Installation Tests..."
(
    # Initialize modules
    [ -f /usr/share/modules/init/bash ] && source /usr/share/modules/init/bash
    
    if command -v module >/dev/null 2>&1; then
        module use ${HOME}/modulefiles
        
        echo "🔄 Loading AIESDA and JEDI modules..."
        module load ${PKG_MODULE_FILE}
        module load ${JEDI_MODULE_FILE}

        # New, cleaner test verifying both version and config
        python3 -c "import aiesda; print(f'✅ AIESDA v{aiesda.__version__} initialized with {aiesda.AIESDAConfig}')"
        if [ "$IS_WSL" = true ]; then
            echo "📝 WSL Detection: Testing JEDI-Bridge..."
            # Verify the wrapper from the 'jedi' module is active
            if command -v jedi-run >/dev/null 2>&1; then
                jedi-run python3 -c "import ufo; import aidaconf; print('✅ Bridge Verified: JEDI + AIESDA are talking.')"
            else
                echo "❌ ERROR: 'jedi-run' not found. Check if the jedi/${VERSION} module was created correctly."
            fi
        else
            echo "📝 HPC Detection: Testing Native Stack..."
            python3 -c "import ufo; import aidaconf; print('✅ Native Verified: JEDI + AIESDA linked.')"
        fi
    fi
)

###########################################################
exit 0

###########################################################
###		End of the file install.sh		                ###
###########################################################
