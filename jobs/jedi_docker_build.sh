#!/bin/bash
# ==============================================================================
# AIESDA JEDI Docker Builder (WSL/Laptop Integration)
# ==============================================================================
# jedi_docker_build.sh
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
###########################################################################################
# --- 1.1 Environment Configuration ---
###########################################################################################

###########################################################################################

###########################################################################################
SELF=$(realpath "${0}")
JOBS_DIR=$(cd "$(dirname "${SELF}")" && pwd)
if [[ "$SELF" == *"/jobs/"* ]]; then
    export PKG_ROOT=$(cd "$JOBS_DIR/.." && pwd)
else
    export PKG_ROOT="$JOBS_DIR"
fi
options $(echo "$@" | tr "=" " ")
PKG_NAME=$(basename "${PKG_ROOT}")
export PKG_NAME=${PKG_NAME:-"aiesda"}
PROJECT_NAME="${PKG_NAME}"
PROJECT_ROOT="${PKG_ROOT}"
SITE_NAME=${SITE_NAME:-"docker"}
HOST=$(hostname)
REQUIREMENTS="$PROJECT_ROOT/requirements.txt"
VERSION=$(cat ${PROJECT_ROOT}/VERSION 2>/dev/null | tr -d '[:space:]' | sed 's/\.0\+/\./g')
VERSION=${VERSION:-"dev"}
JEDI_VERSION=$(grep -iE "^jedi[>=]*" "$REQUIREMENTS" | head -n 1 | sed 's/[^0-9.]*//g')
JEDI_VERSION=${JEDI_VERSION:-"latest"}
export JEDI_VERSION="${JEDI_VERSION}"
BUILD_ROOT="${HOME}/build"
BUILD_DIR="${BUILD_ROOT}/${PROJECT_NAME}_build_${VERSION}"
BUILD_WORKSPACE="${HOME}/build/docker_build_tmp"
MODULE_PATH="${HOME}/modulefiles"
JEDI_MODULE_FILE="${MODULE_PATH}/jedi/${JEDI_VERSION}"
PKG_MODULE_FILE="${MODULE_PATH}/${PROJECT_NAME}/${VERSION}"
LOG_BASE="${HOME}/logs/$(date +%Y/%m/%d)/${PROJECT_NAME}/${VERSION}"
###########################################################################################
###########################################################################################
# --- 2. Docker Fallback Logic ---
if [ -z "$IS_WSL" ]; then
    grep -qi "microsoft" /proc/version && IS_WSL=true || IS_WSL=false
fi
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
# Quick check if Docker is running
if ! docker ps &>/dev/null; then
    echo "❌ ERROR: Docker daemon is not running."
    echo "Please ensure Docker Desktop is started and WSL integration is enabled."
    exit 1
fi
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
## JEDI v${JEDI_VERSION} (AIESDA Docker Bridge)
## Generated on: $(date)

# Hardcoded paths from installation
set version      "${JEDI_VERSION}"
set aiesda_root	 "${BUILD_DIR}"
set aiesda_bin   "${BUILD_DIR}/bin"

setenv           JEDI_VERSION  \$version
setenv           JEDI_METHOD   "docker"
setenv			 JEDI_ROOT		\$aiesda_root

# Point to the directory containing 'jedi-run'
if { [file isdirectory \$aiesda_bin] } {
    prepend-path PATH          \$aiesda_bin
}

proc ModulesHelp { } {
    puts stderr "This module enables the AIESDA-JEDI Docker bridge."
    puts stderr "It provides 'jedi-run' to execute JEDI commands within a container."
}
EOF_MODULE

echo "📋 Modulefile created at: ${JEDI_MODULE_FILE}"

# Create a 'latest' symlink for the JEDI module
JEDI_MODULE_DIR=$(dirname "${JEDI_MODULE_FILE}")
ln -sf "${JEDI_VERSION}" "${JEDI_MODULE_DIR}/latest"
echo "🔗 Linked jedi/${JEDI_VERSION} to jedi/latest"

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
