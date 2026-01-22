#!/bin/bash
###########################################################
# --- 1. Configuration ---
VERSION="0.1.0"
PROJECT_NAME="aiesda"
PROJECT_ROOT=$(pwd)
BUILD_DIR="${HOME}/build/${PROJECT_NAME}_build_${VERSION}"
MODULE_FILE="${HOME}/modulefiles/${PROJECT_NAME}/${VERSION}"
REQUIREMENTS="${PROJECT_ROOT}/requirement.txt"
AIESDA_INSTALLED_ROOT="${BUILD_DIR}"
###########################################################

# --- 1. Pre-flight Checks (WSL Detection) ---
IS_WSL=false
if grep -qi "microsoft" /proc/version 2>/dev/null || grep -qi "wsl" /proc/sys/kernel/osrelease 2>/dev/null; then
    IS_WSL=true
    echo "💻 WSL Detected."
fi

###########################################################

# --- 2. Block Definition ---
NATIVE_BLOCKS=(
    "Numerical and Data Handling"
    "Geospatial Visualization"
    "AI and Deep Learning"
    "Meteorological Specifics"
    "Configuration and Logging Libraries"
    "ECMWF Anemoi and Related Stack"
)

COMPLEX_BLOCKS=(
    "NCAR Legacy Graphics and I/O"
    "JCSDA JEDI and Related Stack"
)

echo "🚀 Starting Sequential Block-Wise Installation..."

# Helper: Extract packages between markers
get_req_block() {
    local block_name=$1
    # Escape & for sed safety
    local escaped_name=$(echo "$block_name" | sed 's/&/\\&/g')
    if [ -f "$REQUIREMENTS" ]; then
        sed -n "/# === BLOCK: ${escaped_name} ===/,/# === END BLOCK ===/p" "$REQUIREMENTS" | \
            sed "/# ===/d; /^#/d; /^\s*$/d; s/[[:space:]]*#.*//g"
    fi
}
###########################################################

# --- 3. Dependency Management Loop ---
echo "🐍 Upgrading pip..."
python3 -m pip install --user --upgrade pip --break-system-packages

for block in "${NATIVE_BLOCKS[@]}"; do
    echo "📦 Installing block: [$block]..."
    PKGS=$(get_req_block "$block")
    if [ ! -z "$PKGS" ]; then
        python3 -m pip install --user $PKGS --break-system-packages
    fi
done

# Check Complex Blocks
DA_MISSING=0
for block in "${COMPLEX_BLOCKS[@]}"; do
    echo "🔍 Checking complex block: [$block]..."
    PKGS=$(get_req_block "$block")
    for pkg in $PKGS; do
        # Clean name for import check
        lib=$(echo "$pkg" | sed 's/py//' | cut -d'=' -f1 | cut -d'>' -f1 | tr -d '[:space:]')
        if ! python3 -c "import $lib" &>/dev/null; then
            echo "❌ $lib not found."
            DA_MISSING=1
        fi
    done
done
###########################################################

# --- 4. Complex Blocks Check ---
DA_MISSING=0
for block in "${COMPLEX_BLOCKS[@]}"; do
    echo "🔍 Checking complex block: [$block]..."
    PKGS=$(get_req_block "$block")
    for pkg in $PKGS; do
        lib=$(echo "$pkg" | sed 's/py//' | cut -d'=' -f1 | cut -d'>' -f1 | tr -d '[:space:]')
        if ! python3 -c "import $lib" &>/dev/null; then
            echo "❌ $lib not found."
            DA_MISSING=1
        fi
    done
done

###########################################################

# --- 5. Docker Fallback (Merged & Cleaned) ---
if [ "$DA_MISSING" -eq 1 ]; then
    echo "🐳 JEDI/Complex libraries missing."
    
    if [ "$IS_WSL" = true ]; then
        echo "🔍 Checking Docker Desktop integration..."
        if ! docker ps &>/dev/null; then
            echo "❌ Docker check failed! Ensure Docker Desktop is running and WSL Integration is enabled."
            exit 1
        fi
    fi

    if command -v docker &>/dev/null; then
        echo "🏗️ Building JEDI-Enabled Docker Fallback..."
        cat << 'EOF_DOCKER' > Dockerfile
FROM jcsda/docker-gnu-openmpi-dev:latest
WORKDIR /home/aiesda
COPY requirement.txt .
RUN pip3 install --no-cache-dir -r requirement.txt --break-system-packages
ENV PYTHONPATH="/home/aiesda/lib/aiesda/pylib:/home/aiesda/lib/aiesda/pydic:${PYTHONPATH}"
ENV PATH="/home/aiesda/lib/aiesda/scripts:/home/aiesda/lib/aiesda/jobs:${PATH}"
EOF_DOCKER

        docker build -t aiesda_jedi:latest .
        
        # Create the alias if it doesn't exist
        if ! grep -q "aida-run" ~/.bashrc; then
            echo "alias aida-run='docker run -it --rm -v \$(pwd):/home/aiesda aiesda_jedi:latest'" >> ~/.bashrc
            echo "✅ Created 'aida-run' alias. Run 'source ~/.bashrc' after installation."
        fi
    else
        echo "⚠️  Warning: JEDI is missing and Docker is not installed. DA components will not work."
    fi
fi


###########################################################

# --- 6. Build and Module Generation ---
echo "🏗️ Building Python package..."
rm -rf "${BUILD_DIR}"
python3 setup.py build --build-base "${BUILD_DIR}"

AIESDA_INTERNAL_LIB="${BUILD_DIR}/lib/aiesda"
mkdir -p "${AIESDA_INTERNAL_LIB}"
for asset in nml yaml jobs scripts pydic pylib; do
    [ -d "${PROJECT_ROOT}/$asset" ] && cp -rp "${PROJECT_ROOT}/$asset" "${AIESDA_INTERNAL_LIB}/"
done

mkdir -p $(dirname "${MODULE_FILE}")
cat << EOF_MODULE > "${MODULE_FILE}"
#%Module1.0
## AIESDA v${VERSION}

if { [is-loaded jedi] == 0 } {
    catch { module load jedi/1.5.0 }
}

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
echo "✅ Installation Complete!"
echo "   Module: ${PROJECT_NAME}/${VERSION}"
echo "------------------------------------------------------------"
###########################################################

# --- 6. Testing Environment ---
(
    [ -f /usr/share/modules/init/bash ] && source /usr/share/modules/init/bash
    if command -v module >/dev/null 2>&1; then
        module use ${HOME}/modulefiles
        module load aiesda/${VERSION}
        echo "🧪 Testing module load..."
        echo "AIESDA_NML: \$AIESDA_NML"
        python3 -c "import aidaconf; print('✅ Success! aidaconf found.')"
    fi
)

###########################################################
exit 0

###########################################################
###		End of the file install.sh		###
###########################################################
