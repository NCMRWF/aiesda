#!/bin/bash
# ==============================================================================
# AIESDA Unified Installer (WSL/Laptop & HPC)
# ==============================================================================
# install.sh

SELF=$(realpath ${0})
HOST=$(hostname)
export JOBSDIR=${SELF%/*}
export PKG_ROOT=${SELF%/jobs/*}
export PKG_NAME=${PKG_ROOT##*/}

###########################################################################################
helpdesk()
{
echo -e "Usage: \n $0"
                        echo "options:"
			echo "-h	--help		Help"
			echo "-s	--site		site information for coustum settings"
			echo "-p	--pkg		Package Name"
                        exit 0
}
###########################################################################################
options()
{
while test $# -gt 0; do
     case "$1" in
            -h|--help) 	helpdesk;;
		    -s|--site)	shift; SITE_NAME=$1; shift;;
		    -p|--pkg)	shift; PKG_NAME=$1; shift;;
		    *)		shift;;
	esac
done
}
###########################################################################################
options $(echo $@  | tr "=" " ")
###########################################################################################
###########################################################
# --- 1. Configuration ---
###########################################################

PROJECT_NAME=${PKG_NAME:-"aiesda"}
# Capture Site Argument (Default to 'docker')
SITE_NAME=${SITE_NAME:-"docker"}

# Discover the Repo Root relative to this script's location
# This allows you to run 'bash jobs/install.sh' from anywhere
JOBS_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "$JOBS_DIR/.." && pwd)

# Change directory to root so setup.py and VERSION are accessible
cd "$PROJECT_ROOT"

VERSION=$(cat VERSION 2>/dev/null | tr -d '[:space:]' | sed 's/\.0\+/\./g')
VERSION=${VERSION:-"dev"}
# --- NEW: Initialize Logging NOW that variables are set ---
LOG_BASE="${HOME}/logs/$(date +%Y/%m/%d)/${PROJECT_NAME}/${VERSION}"
mkdir -p "$LOG_BASE"
echo "📝 Logs for this installation session: ${LOG_BASE}/install.log"
exec > >(tee -a "${LOG_BASE}/install.log") 2>&1
# ---------------------------------------------------------
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
# We export the JEDI_VERSION so the TCL script can pick it up via $env()
export JEDI_VERSION="${JEDI_VERSION}"
echo "🔍 Detected JEDI Target Version: ${JEDI_VERSION}"
JEDI_MODULE_FILE="${MODULE_PATH}/jedi/${JEDI_VERSION}"

# Uninstall pre-existing build copies of the same version number.
echo "♻️  Wiping existing installation for v$VERSION..."
bash $JOBS_DIR/remove.sh "$VERSION" >/dev/null 2>&1

# Dynamically extract NATIVE_BLOCKS and COMPLEX_BLOCKS from requirements.txt
if [ -f "$REQUIREMENTS" ]; then
    # Extract lines between markers, remove leading '# ', and FILTER OUT the markers themselves
    eval "$(sed -n '/# >>> BASH_CONFIG_START >>>/,/# <<< BASH_CONFIG_END <<</p' "$REQUIREMENTS" | \
            sed 's/^# //' | \
            grep -v ">>>" | grep -v "<<<")"
else
    echo "❌ ERROR: requirements.txt not found!"
    exit 1
fi

# Verify the extraction worked
echo "🔍 Loaded ${#NATIVE_BLOCKS[@]} Native Blocks and ${#COMPLEX_BLOCKS[@]} Complex Blocks."

###########################################################
# --- 1.1 Progress reporting function ---		###
###########################################################

# Helper for clean progress reporting
step_label() {
    echo -e "\n\033[1;34m[STEP $1]: $2\033[0m"
    echo "------------------------------------------------"
}

# Spinner for long-running background tasks
show_spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

###########################################################
# --- 2.1 Load Site-Specific Environment 		###
###########################################################
ENV_TCL="${PROJECT_ROOT}/sites/${SITE_NAME}/env_setup.tcl"
if [ -f "$ENV_TCL" ]; then
    echo "🌐 Loading environment from: $ENV_TCL"
    # Loading the TCL file via module command updates PATH for Python 3.9
    module load "$ENV_TCL"
else
    echo "⚠️  No site config found at $ENV_TCL, using default environment."
fi

# 2. Force use of the Python 3.9 from the module
export PYTHON_EXE=$(which python3)
echo "🐍 Using Python executable: $PYTHON_EXE"


###########################################################
# --- 2.2 Pre-flight Checks (WSL & OS Detection) ---
###########################################################
IS_WSL=false
if grep -qi "microsoft" /proc/version 2>/dev/null || grep -qi "wsl" /proc/sys/kernel/osrelease 2>/dev/null; then
    IS_WSL=true
    echo "💻 WSL Detected."
else
    echo "🐧 Native Linux/HPC Detected."
fi
show_spinner $!

###########################################################
# --- 3. Self-Healing: Check for pip ---
###########################################################
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
show_spinner $!

###########################################################
# --- 4. Helper Function (With '&' Fix) ---
###########################################################
get_req_block() {
    local block_name=$1
    local escaped_name=$(echo "$block_name" | sed 's/&/\\&/g')
    if [ -f "$REQUIREMENTS" ]; then
        # 1. Extract block
        # 2. Remove block headers
        # 3. Remove lines that are ONLY comments or empty
        # 4. Remove inline comments (space+#)
        sed -n "/# === BLOCK: ${escaped_name} ===/,/# === END BLOCK ===/p" "$REQUIREMENTS" | \
            sed "/# ===/d; /^\s*#/d; /^\s*$/d; s/[[:space:]]*#.*//g"
    fi
}
show_spinner $!

###########################################################
# --- 5. Installation Loop ---
###########################################################
echo "🐍 Upgrading pip..."
python3 -m pip install --user --upgrade pip --break-system-packages

for block in "${NATIVE_BLOCKS[@]}"; do
    echo "📦 Installing block: [$block]..."
    PKGS=$(get_req_block "$block")
    [ ! -z "$PKGS" ] && python3 -m pip install --user $PKGS --break-system-packages
done
show_spinner $!

###########################################################
# --- 6. Complex Block Verification ---
###########################################################
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
show_spinner $!

###########################################################
# --- 7. Docker Fallback Logic ---
###########################################################
if [ "$DA_MISSING" -gt 0 ]; then
    echo "🐳 Missing $DA_MISSING DA components. Initializing JEDI v${JEDI_VERSION} Build..."
    
    chmod +x "${JOBS_DIR}/jedi_docker_build.sh"
    # PASS JEDI_VERSION instead of AIESDA VERSION
    bash "${JOBS_DIR}/jedi_docker_build.sh" "$JEDI_VERSION"

else
    echo "✅ No Docker fallback required."
fi
show_spinner $!

###########################################################
# --- 8. Build & Module Generation ---
###########################################################
echo "🏗️  Finalizing AIESDA Build..."
rm -rf "${BUILD_DIR}"
# Build the package into the targeted build directory
python3 setup.py build --build-base "${BUILD_DIR}" \
                 egg_info --egg-base "${BUILD_DIR}"

# Manually sync assets that setup.py might miss or that you want in specific subfolders
AIESDA_INTERNAL_LIB="${BUILD_DIR}/lib/aiesda"
mkdir -p "${AIESDA_INTERNAL_LIB}"
for asset in nml yaml jobs scripts pydic pylib; do
    [ -d "${PROJECT_ROOT}/$asset" ] && cp -rp "${PROJECT_ROOT}/$asset" "${AIESDA_INTERNAL_LIB}/"
done

# Ensure VERSION file is in the build root so aiesda/__init__.py can find it
cp "${PROJECT_ROOT}/VERSION" "${AIESDA_INTERNAL_LIB}/"

# Ensure requirements.txt is archived with the build for future cleanup context
cp "${PROJECT_ROOT}/requirements.txt" "${AIESDA_INTERNAL_LIB}/"

# Define the target modulefile path
PKG_MODULE_FILE="${MODULE_PATH}/${PROJECT_NAME}/${VERSION}"
mkdir -p $(dirname "${PKG_MODULE_FILE}")
# Start with a generic header
cat << EOF_MODULE > "${PKG_MODULE_FILE}"
#%Module1.0
## AIESDA v${VERSION} (${SITE_NAME} environment)
EOF_MODULE

# Inject the site-specific TCL snippet
if [ -f "sites/${SITE_NAME}/env_setup.tcl" ]; then
    cat "sites/${SITE_NAME}/env_setup.tcl" >> "${PKG_MODULE_FILE}"
fi

# Append the core Python/Library paths
cat << EOF_MODULE >> "${PKG_MODULE_FILE}"

set version      ${VERSION}
set aiesda_root  ${AIESDA_INSTALLED_ROOT}

setenv           AIESDA_VERSION  \$version
setenv           AIESDA_ROOT     \$aiesda_root/lib/aiesda
setenv           AIESDA_NML      \$aiesda_root/lib/aiesda/nml
setenv           AIESDA_YAML     \$aiesda_root/lib/aiesda/yaml

# The main site-packages location for the build
prepend-path     PYTHONPATH      \$aiesda_root/lib

# Add asset subdirectories to pathing for safety
prepend-path     PYTHONPATH      \$aiesda_root/lib/aiesda/pylib
prepend-path     PYTHONPATH      \$aiesda_root/lib/aiesda/pydic
prepend-path     PATH            \$aiesda_root/lib/aiesda/scripts
prepend-path     PATH            \$aiesda_root/lib/aiesda/jobs

# Add Docker wrapper bin if on WSL/Laptop mode
if { [file isdirectory \$aiesda_root/bin] } {
    prepend-path PATH            \$aiesda_root/bin
}
EOF_MODULE
show_spinner $!

###########################################################
# --- 9. Build Metadata archival for future reference ---
###########################################################
# Inside install.sh (After the build/install step)
echo "📦 Archiving build metadata..."
mkdir -p "${BUILD_DIR}/lib/aiesda"
cp "${PROJECT_ROOT}/requirements.txt" "${BUILD_DIR}/lib/aiesda/requirements.txt"
cp "${PROJECT_ROOT}/VERSION" "${BUILD_DIR}/lib/aiesda/VERSION"
show_spinner $!

###########################################################
# --- 10. Testing Environment ---
###########################################################
echo "🧪 Running Post-Installation Tests..."
(
    # Initialize modules if they aren't already
    if [ -f /usr/share/modules/init/bash ]; then
        source /usr/share/modules/init/bash
    elif [ -f /etc/profile.d/modules.sh ]; then
        source /etc/profile.d/modules.sh
    fi
    
    if command -v module >/dev/null 2>&1; then
        module use "${MODULE_PATH}"
        echo "🔄 Loading AIESDA v${VERSION}..."
        module load "${PROJECT_NAME}/${VERSION}"
        
        # Test 1: Core AIESDA Metadata
        echo "🧐 Verifying AIESDA Version and Config..."
        python3 -c "import aiesda; print(f'✅ AIESDA v{aiesda.__version__} initialized with {aiesda.AIESDAConfig}')"
        
        # Test 2: Stack Integration
        if [ "$SITE_NAME" = "docker" ]; then
            echo "📝 WSL Detection: Testing JEDI-Bridge via jedi-run..."
            if command -v jedi-run >/dev/null 2>&1; then
                jedi-run python3 -c "import ufo; print('✅ Bridge Verified: JEDI container is reachable.')"
            else
                echo "❌ ERROR: 'jedi-run' wrapper not found in PATH."
            fi
        else
            echo "📝 HPC Detection: Testing Native Stack Integration..."
            python3 -c "import ufo; print('✅ Native Verified: JEDI modules linked.')"
        fi
    fi
)
show_spinner $!

###########################################################
# --- 11. Final Summary ---
###########################################################
echo "------------------------------------------------"
echo "✅ AIESDA v${VERSION} Installation Complete!"
echo "📝 Log: ${LOG_BASE}/install.log"
echo "📂 Build: ${BUILD_DIR}"
echo "💻 Command: module load ${PROJECT_NAME}/${VERSION}"
echo "------------------------------------------------"
exit 0
###########################################################
###	End of the file install.sh		        ###
###########################################################









