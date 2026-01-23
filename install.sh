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
MODULE_FILE="${HOME}/modulefiles/${PROJECT_NAME}/${VERSION}"
REQUIREMENTS="${PROJECT_ROOT}/requirement.txt"
AIESDA_INSTALLED_ROOT="${BUILD_DIR}"
# Surgical cleanup: only removes the block between our markers
sed -i '/# >>> AIESDA_JEDI_SETUP >>>/,/# <<< AIESDA_JEDI_SETUP <<< /d' ~/.bashrc

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
# On WSL, we assume we need Docker (DA_MISSING=1)
# On HPC, we will flip this to 0 if native libraries are found
DA_MISSING=1

if [ "$IS_WSL" = false ]; then
    echo "🔍 Checking native DA components (HPC Mode)..."
    DA_FOUND_COUNT=0
    TOTAL_DA_PKGS=0
    
    for block in "${COMPLEX_BLOCKS[@]}"; do
        PKGS=$(get_req_block "$block")
        for pkg in $PKGS; do
            ((TOTAL_DA_PKGS++))
            lib=$(echo "$pkg" | sed 's/py//' | cut -d'=' -f1 | cut -d'>' -f1 | tr -d '[:space:]')
            if python3 -c "import $lib" &>/dev/null; then
                ((DA_FOUND_COUNT++))
            fi
        done
    done

    # If we found all packages natively, we don't need Docker
    if [ "$TOTAL_DA_PKGS" -gt 0 ] && [ "$DA_FOUND_COUNT" -eq "$TOTAL_DA_PKGS" ]; then
        echo "✅ All DA components found natively."
        DA_MISSING=0
    fi
fi

###########################################################

# --- 7. Docker Fallback Logic ---
if [ "$DA_MISSING" -eq 1 ] && [ "$IS_WSL" = true ]; then
    echo "🐳 JEDI components missing. Checking Docker..."

    # 1. Check if Docker is installed
    if ! command -v docker &>/dev/null; then
        echo "❌ ERROR: Docker command not found. Please install Docker Desktop on Windows."
        exit 1
    fi

    # 2. Try to start Docker if it's not running
    if ! docker ps &>/dev/null; then
        echo "🐋 Docker is not running. Attempting to start Docker Desktop..."
        # Launch the Windows executable from WSL
        "/mnt/c/Program Files/Docker/Docker/Docker Desktop.exe" &
        
        echo "⏳ Waiting for Docker to initialize (this may take a minute)..."
        # Wait up to 60 seconds for Docker to become responsive
        COUNT=0
        while ! docker ps &>/dev/null && [ $COUNT -lt 12 ]; do
            sleep 5
            ((COUNT++))
            echo "   ...still waiting ($((COUNT * 5))s)..."
        done
    fi

    # 3. Final verification of the connection
    if ! docker ps &>/dev/null; then
        echo "❌ ERROR: Docker Desktop failed to start or WSL Integration is disabled."
        echo "👉 Please manually open Docker Desktop -> Settings -> Resources -> WSL Integration"
        echo "   and ensure 'Ubuntu' is toggled ON."
        exit 1
    fi

    echo "✅ Docker is ready. "

# Check if the image already exists before building
    if docker image inspect aiesda_jedi:${VERSION} &>/dev/null; then
        echo "✅ Docker image aiesda_jedi:${VERSION} already exists. Skipping build."
    else
        echo "🏗️  Building JEDI-Enabled Docker Image..."
        # Define a clean build workspace outside the repo
        
        mkdir -p "$BUILD_WORKSPACE"

        # 1. Copy only the necessary requirement file to the workspace
        cp requirement.txt "$BUILD_WORKSPACE/"

        # 2. Generate the Dockerfile directly in the build area
        cat << 'EOF_DOCKER' > "$BUILD_WORKSPACE/Dockerfile"
FROM jcsda/docker-gnu-openmpi-dev:latest
USER root

# Cache buster to force path re-evaluation
RUN echo "Build Date: $(date)" > /build_info.txt

# Check if python3 exists before trying to use it or install it
RUN if ! command -v python3 >/dev/null 2>&1; then \
        apt-get update && apt-get install -y python3 python3-pip libeccodes-dev; \
    else \
        echo "Python3 already present, ensuring pip is available..." && \
        apt-get update && apt-get install -y python3-pip libeccodes-dev; \
    fi && rm -rf /var/lib/apt/lists/*
# Install system dependencies needed for some python wheels
RUN apt-get update && apt-get install -y build-essential python3-dev
RUN apt-get update && apt-get install -y python3-pip libeccodes-dev && \
    rm -rf /var/lib/apt/lists/*

# 3. DISCOVER AND INJECT PATH (Internal to Container)
# We use a unique marker 'AIESDA_INTERNAL_PATHS' to ensure idempotency
RUN JEDI_PATH=$(find /usr/local -name "ufo" -type d -path "*/dist-packages/*" | head -n 1 | sed 's/\/ufo//') && \
    MARKER="AIESDA_INTERNAL_PATHS" && \
    if ! grep -q "$MARKER" /etc/bash.bashrc; then \
        echo -e "\n# >>> $MARKER >>>\nexport PYTHONPATH=\$JEDI_PATH:/home/aiesda/lib/aiesda/pylib:/home/aiesda/lib/aiesda/pydic:\$PYTHONPATH\n# <<< $MARKER <<<" >> /etc/bash.bashrc; \
    fi

# 4. SET ROBUST PATHS
# Using a wildcard (*) allows Python to find site-packages in 3.10, 3.11, or 3.12
# Inside your Dockerfile generation block:
# We use a wildcard to capture any python 3.x version present in the JCSDA image
ENV PYTHONPATH="/usr/local/bundle/install/lib/python3.*/dist-packages:/usr/local/lib/python3.*/dist-packages:/app:/usr/local/lib:/home/aiesda/lib/aiesda/pylib:/home/aiesda/lib/aiesda/pydic:\${PYTHONPATH}"
ENV LD_LIBRARY_PATH="/usr/local/lib:\${LD_LIBRARY_PATH}"
ENV PATH="/usr/bin:/usr/local/bin:\${PATH}"

WORKDIR /home/aiesda
COPY requirement.txt .

# 5. Install Python Stack with extra retries for spotty connections
RUN python3 -m pip install \
    --no-cache-dir \
    --retries 10 \
    --timeout 60 \
    -r requirement.txt --break-system-packages

# 6. Verification check during build
RUN python3 -c "import sys; print('Python Path:', sys.path); import ufo; print('✅ JEDI UFO found inside container')"
EOF_DOCKER

        docker build --no-cache -t aiesda_jedi:${VERSION} -t aiesda_jedi:latest \
                     -f "$BUILD_WORKSPACE/Dockerfile" "$BUILD_WORKSPACE"
        # Cleanup the temporary build workspace
        rm -rf "$BUILD_WORKSPACE"
    fi

    # Define the unique identifier for your block
    MARKER="AIESDA_JEDI_SETUP"

    if ! grep -q "$MARKER" ~/.bashrc; then
        echo "📝 Adding AIESDA configuration to ~/.bashrc..."
        cat << EOF >> ~/.bashrc

# >>> $MARKER >>>
alias aida-run='docker run -it --rm -v \$(pwd):/home/aiesda aiesda_jedi:latest'

# <<< $MARKER <<<
EOF
        echo "✅ Configuration added."
    else
        echo "ℹ️ AIESDA configuration already exists in ~/.bashrc, skipping."
    fi

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

mkdir -p $(dirname "${MODULE_FILE}")
cat << EOF_MODULE > "${MODULE_FILE}"
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
(
    # Initialize modules if available
    [ -f /usr/share/modules/init/bash ] && source /usr/share/modules/init/bash
    
    if command -v module >/dev/null 2>&1; then
        module use ${HOME}/modulefiles
        module load aiesda/${VERSION}
        echo "🧪 Testing module load..."
        
        if [ "$IS_WSL" = true ]; then
            echo "📝 WSL/Laptop detected: Running Bridge Test via Docker..."
            # Use the newly built image to test if aidaconf can see UFO inside the container
            docker run --rm -v $(pwd):/home/aiesda aiesda_jedi:${VERSION} python3 -c "import ufo; import aidaconf; print('✅ Success! JEDI and AIESDA linked via Docker.')"
        else
            echo "📝 Native/HPC detected: Running Native Test..."
            python3 -c "import aidaconf; print('✅ Success! aidaconf found natively.')"
        fi
    fi
)

# --- 10. Testing Environment & Instructions ---
echo "###########################################################"
echo "✅ Installation Complete!"
echo ""
echo "👉 To activate AIESDA in this session, run:"
echo "   source ~/.bashrc"
echo ""
echo "🚀 To test the JEDI-AIESDA Bridge, run:"
# We use backslashes here to ensure the quotes are printed correctly in the terminal
echo "   aida-run python3 -c \"import ufo; import aidaconf; print('🚀 JEDI-AIESDA Bridge is Online')\""
echo "###########################################################"
###########################################################
exit 0

###########################################################
###		End of the file install.sh		                ###
###########################################################
