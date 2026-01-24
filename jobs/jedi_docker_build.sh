#!/bin/bash
# ==============================================================================
# AIESDA JEDI Docker Builder (WSL/Laptop Integration)
# ==============================================================================

# 1. Path & Environment Setup
SELF=$(realpath "${0}")
HOMEDIR=$(cd "$(dirname "$(realpath "$0")")/.." && pwd)
export HOMEDIR
PROJECT_ROOT="$HOMEDIR" # Fixed syntax
REQUIREMENTS="$PROJECT_ROOT/requirements.txt"
JEDI_VERSION=${VERSION:-"dev"}
BUILD_WORKSPACE="${HOME}/build/docker_build_tmp"


# --- 7. Docker Fallback Logic ---
if [ "$DA_MISSING" -eq 1 ] && [ "$IS_WSL" = true ]; then
    echo "🐳 JEDI components missing. Checking Docker..."

    # 1. Pre-flight Check: Docker Command
    if ! command -v docker &>/dev/null; then
        echo "❌ ERROR: Docker command not found. Please install Docker Desktop."
        exit 1
    fi

    # 2. Ensure Docker is running
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

    # 3. Build Logic
    if docker image inspect aiesda_jedi:${VERSION} &>/dev/null; then
        echo "✅ Docker image aiesda_jedi:${VERSION} already exists."
    else
        echo "🏗️  Starting JEDI-Enabled Docker Build (v${VERSION})..."
        mkdir -p "$BUILD_WORKSPACE"
        
        # Copy requirements using the absolute path we calculated
        if [ -f "${REQUREMENTS}" ]; then
            cp "${REQUREMENTS}" "$BUILD_WORKSPACE/"
        else
            echo "❌ ERROR: ${REQUREMENTS} not found."
            exit 1
        fi

        # Generate the Dockerfile
        
        cat << 'EOF_DOCKER' > "$BUILD_WORKSPACE/Dockerfile"
FROM jcsda/docker-gnu-openmpi-dev:latest
USER root

RUN apt-get update && apt-get install -y \
    python3-pip libeccodes-dev build-essential python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home/aiesda
COPY requirement.txt .

RUN python3 -m pip install --no-cache-dir -r requirement.txt --break-system-packages

# Path Discovery
RUN JEDI_BASE_DIR=$(find /usr/local -name "ufo" -type d | head -n 1) && \
    if [ -n "$JEDI_BASE_DIR" ]; then \
        JEDI_PATH=$(dirname "$JEDI_BASE_DIR"); \
        echo "export PYTHONPATH=$JEDI_PATH:/home/aiesda/lib/aiesda/pylib:/home/aiesda/lib/aiesda/pydic:\$PYTHONPATH" >> /etc/bash.bashrc; \
        echo "PYTHONPATH=$JEDI_PATH:/home/aiesda/lib/aiesda/pylib:/home/aiesda/lib/aiesda/pydic:\$PYTHONPATH" >> /etc/environment; \
    fi

ENV PYTHONPATH="/usr/local/bundle/install/lib/python3.10/dist-packages:/usr/local/lib/python3.10/dist-packages:/usr/local/bundle/install/lib/python3.12/dist-packages:/usr/local/lib/python3.12/dist-packages:/home/aiesda/lib/aiesda/pylib:/home/aiesda/lib/aiesda/pydic"

RUN JEDI_BASE_DIR=$(find /usr/local -name "ufo" -type d | head -n 1) && \
    if [ -z "$JEDI_BASE_DIR" ]; then echo "❌ FAILED: ufo module not found"; exit 1; fi && \
    export JEDI_PATH=$(dirname "$JEDI_BASE_DIR") && \
    export PYTHONPATH="$JEDI_PATH:$PYTHONPATH" && \
    python3 -c "import ufo; print('✅ JEDI UFO found at:', ufo.__file__)"
EOF_DOCKER

        docker build --no-cache -t aiesda_jedi:${VERSION} -t aiesda_jedi:latest \
                     -f "$BUILD_WORKSPACE/Dockerfile" "$BUILD_WORKSPACE"

        BUILD_STATUS=$?
        rm -rf "$BUILD_WORKSPACE"

        if [ $BUILD_STATUS -ne 0 ]; then
            echo "❌ Docker build failed."
            exit 1
        fi
        echo "✅ Docker build successful: aiesda_jedi:${VERSION}"
    fi

  # ... (After successful docker build) ...
    
    # 4. Create Wrapper Script instead of Alias
    AIESDA_BIN_DIR="${BUILD_DIR}/bin"
    mkdir -p "$AIESDA_BIN_DIR"
    
    cat << EOF > "${AIESDA_BIN_DIR}/jedi-run"
#!/bin/bash
# AIESDA JEDI Docker Wrapper
docker run -it --rm -v \$(pwd):/home/aiesda aiesda_jedi:latest "\$@"
EOF

    chmod +x "${AIESDA_BIN_DIR}/jedi-run"
    echo "✅ Created Docker wrapper at ${AIESDA_BIN_DIR}/jedi-run"
fi
fi

# --- 8. Module Generation ---
MODULE_PATH="${HOME}/modulefiles"
JEDI_MODULE_FILE="${MODULE_PATH}/jedi/${JEDI_VERSION}"
mkdir -p "${MODULE_PATH}"

cat << EOF_MODULE > "${JEDI_MODULE_FILE}"
#%Module1.0
## JEDI v${VERSION} (AIESDA Bridge)
set version      ${JEDI_VERSION}
set jedi_root    ${BUILD_DIR}

# Metadata
setenv           JEDI_VERSION  \$version
setenv           JEDI_ROOT     \$jedi_root/lib/jedi

# Docker Wrapper Path (for WSL/Laptop)
# This prepends the bin directory only if it exists
if { [file isdirectory \$jedi_root/bin] } {
    prepend-path PATH            \$jedi_root/bin
}

help "This module provides the 'jedi-run' command to execute JEDI tasks via Docker on WSL."
EOF_MODULE

# --- 10. Testing Environment & Instructions ---
echo "###########################################################"
echo "✅ Installation Complete!"
echo ""
echo "👉 To activate AIESDA in this session, run:"
echo "   module load ${JEDI_MODULE_FILE}
echo ""
echo "🚀 To test the JEDI-AIESDA Bridge, run:"
# We use backslashes here to ensure the quotes are printed correctly in the terminal
echo "   jedi-run python3 -c \"import ufo; import aidaconf; print('🚀 JEDI-AIESDA Bridge is Online')\""
echo "###########################################################"
