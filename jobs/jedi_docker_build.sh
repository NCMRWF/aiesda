#!/bin/bash
# ==============================================================================
# AIESDA JEDI Docker Builder (WSL/Laptop Integration)
# ==============================================================================

# --- 1. Path & Environment Setup ---
SELF=$(realpath "${0}")
HOMEDIR=$(cd "$(dirname "$(realpath "$0")")/.." && pwd)
PROJECT_ROOT="$HOMEDIR"
MODULE_PATH="${HOME}/modulefiles"

# Ensure VERSION and PROJECT_NAME are set (inherited or defaulted)
VERSION=${VERSION:-"dev"}
PROJECT_NAME=${PROJECT_NAME:-"aiesda"}
BUILD_DIR="${HOME}/build/${PROJECT_NAME}_build_${VERSION}"
BUILD_WORKSPACE="${HOME}/build/docker_build_tmp"

# Corrected spelling for variable consistency
REQUIREMENTS="$PROJECT_ROOT/requirements.txt"

# Extract JEDI version from requirements.txt
JEDI_VERSION=$(grep -iE "^jedi[>=]*" "$REQUIREMENTS" | head -n 1 | sed 's/[^0-9.]*//g')
JEDI_VERSION=${JEDI_VERSION:-"latest"}
echo "🔍 Detected JEDI Target Version: ${JEDI_VERSION}"

# Define Module File Location
JEDI_MODULE_FILE="${MODULE_PATH}/jedi/${JEDI_VERSION}"

# --- 2. Docker Fallback Logic ---
# Note: Ensure IS_WSL is passed or detected here
if [ "$IS_WSL" = true ]; then
    echo "🐳 JEDI components missing. Checking Docker..."

    if ! command -v docker &>/dev/null; then
        echo "❌ ERROR: Docker command not found. Please install Docker Desktop."
        exit 1
    fi

    if ! docker ps &>/dev/null; then
        echo "🐋 Starting Docker Desktop..."
        "/mnt/c/Program Files/Docker/Docker/Docker Desktop.exe" &
        COUNT=0
        while ! docker ps &>/dev/null && [ $COUNT -lt 12 ]; do
            sleep 5; ((COUNT++))
            echo "...waiting ($((COUNT * 5))s)..."
        done
    fi

    if ! docker ps &>/dev/null; then
        echo "❌ ERROR: Docker failed to start. Check WSL Integration in Settings."
        exit 1
    fi
fi

    # 3. Build Logic
# Note: Ensure IS_WSL is passed or detected here
if [ "$IS_WSL" = true ]; then
    if docker image inspect aiesda_jedi:${JEDI_VERSION} &>/dev/null; then
        echo "✅ Docker image aiesda_jedi:${JEDI_VERSION} already exists."
    else
        echo "🏗️  Starting JEDI-Enabled Docker Build (v${JEDI_VERSION})..."
        mkdir -p "$BUILD_WORKSPACE"
        
        if [ -f "${REQUIREMENTS}" ]; then
            cp "${REQUIREMENTS}" "$BUILD_WORKSPACE/requirements.txt"
        else
            echo "❌ ERROR: ${REQUIREMENTS} not found."
            exit 1
        fi

        # Update inside Section 3 of jedi_docker_build.sh:
        cat << 'EOF_DOCKER' > "$BUILD_WORKSPACE/Dockerfile"
FROM jcsda/docker-gnu-openmpi-dev:latest
USER root
RUN apt-get update && apt-get install -y python3-pip libeccodes-dev build-essential python3-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt --break-system-packages

# Dynamically find JEDI paths and verify UFO availability
RUN JEDI_BASE_DIR=$(find /usr/local -name "ufo" -type d | head -n 1) && \
    JEDI_PATH=$(dirname "$JEDI_BASE_DIR") && \
    echo "export PYTHONPATH=$JEDI_PATH:\$PYTHONPATH" >> /etc/bash.bashrc && \
    export PYTHONPATH="$JEDI_PATH:$PYTHONPATH" && \
    python3 -c "import ufo; print('✅ JEDI UFO found at:', ufo.__file__)"
EOF_DOCKER
        
        # JEDI version taging inside aiesda/jobs/jedi_docker_build.sh
        docker build --no-cache -t aiesda_jedi:${JEDI_VERSION} -t aiesda_jedi:latest \
                     -f "$BUILD_WORKSPACE/Dockerfile" "$BUILD_WORKSPACE"

        BUILD_STATUS=$?
        rm -rf "$BUILD_WORKSPACE"
        [ $BUILD_STATUS -ne 0 ] && echo "❌ Docker build failed." && exit 1
    fi
fi

# --- 4. Create Wrapper Script ---
AIESDA_BIN_DIR="${BUILD_DIR}/bin"
mkdir -p "$AIESDA_BIN_DIR"

# Verify this variable is set at the top of your builder or passed in
AIESDA_INSTALLED_ROOT="${BUILD_DIR}"

# The Wrapper Creation
cat << EOF > "${AIESDA_BIN_DIR}/jedi-run"
#!/bin/bash
# AIESDA JEDI Docker Wrapper
# Mounts the current directory AND the AIESDA install root for full integration
docker run -it --rm \\
    -v "\$(pwd):/app/work" \\
    -v "${AIESDA_INSTALLED_ROOT}/lib:/app/lib" \\
    -w /app/work \\
    -e PYTHONPATH="/app/lib:/app/lib/aiesda/pylib:/app/lib/aiesda/pydic:\$PYTHONPATH" \\
    aiesda_jedi:${JEDI_VERSION} "\$@"
EOF
chmod +x "${AIESDA_BIN_DIR}/jedi-run"

# --- 3. Module Generation ---
mkdir -p "$(dirname "${JEDI_MODULE_FILE}")"

cat << EOF_MODULE > "${JEDI_MODULE_FILE}"
#%Module1.0
## JEDI v${JEDI_VERSION} (AIESDA Bridge)
set version      ${JEDI_VERSION}
set jedi_root    ${BUILD_DIR}

setenv           JEDI_VERSION  \$version
setenv           JEDI_ROOT     \$jedi_root

if { [file isdirectory \$jedi_root/bin] } {
    prepend-path PATH            \$jedi_root/bin
}

help "This module provides 'jedi-run' to execute JEDI tasks via Docker on WSL."
EOF_MODULE

# --- 4. Testing Environment & Instructions ---
echo "###########################################################"
echo "✅ JEDI Bridge Installation Complete!"
echo ""
echo "👉 To activate JEDI in this session, run:"
echo "   module use ${MODULE_PATH}"
echo "   module load jedi/${JEDI_VERSION}"
echo ""
echo "🚀 To test the bridge, run:"
echo "   jedi-run python3 -c \"import ufo; print('🚀 JEDI-AIESDA Bridge is Online')\""
echo "###########################################################"
