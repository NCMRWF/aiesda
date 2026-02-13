#!/bin/bash
# ==============================================================================
# AIESDA JEDI Docker Builder (WSL/Laptop Integration)
# ==============================================================================
# jedi_docker_build.sh

###########################################################################################
# --- 0. Helper Functions (NEW) ---
###########################################################################################
step_label() {
    echo "------------------------------------------------"
    echo "🧪 $1: $2"
    echo "------------------------------------------------"
}

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
# --- 1.1 Environment Configuration ---
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

# Toggle "source" to build UFO/IODA/SABER from GitHub
JEDI_BUILD_MODE="discovery" 

###########################################################################################
# --- 2. Docker Fallback Logic ---
###########################################################################################
if [ -z "$IS_WSL" ]; then
    grep -qi "microsoft" /proc/version && IS_WSL=true || IS_WSL=false
fi

if [ "$IS_WSL" = true ]; then
    step_label "DOCKER" "Checking Docker Health..."
    if ! docker ps &>/dev/null; then
        echo "🐋 Starting Docker Desktop..."
        "/mnt/c/Program Files/Docker/Docker/Docker Desktop.exe" &
        sleep 5
    fi
fi

###########################################################################################
# --- 3. Build Logic ---
###########################################################################################
if [ "$IS_WSL" = true ]; then
    # Improved image check
    if docker images -q aiesda_jedi:${JEDI_VERSION} >/dev/null 2>&1; then
        echo "✅ Docker image aiesda_jedi:${JEDI_VERSION} exists."
    else
        mkdir -p "$BUILD_WORKSPACE"
        cp "${REQUIREMENTS}" "$BUILD_WORKSPACE/requirements.txt"

        if [ "$JEDI_BUILD_MODE" = "source" ]; then
            # Build from GitHub logic
            cat << 'EOF_DOCKER' > "$BUILD_WORKSPACE/Dockerfile"
FROM jcsda/docker-gnu-openmpi-dev:latest
USER root
RUN apt-get update && apt-get install -y git-lfs cmake build-essential && \
    git lfs install && rm -rf /var/lib/apt/lists/*
WORKDIR /jedi
RUN git clone https://github.com/JCSDA/jedi-bundle.git .
RUN mkdir build && cd build && ecbuild --init .. && make -j$(nproc)
ENV PYTHONPATH="/jedi/build/lib:/jedi/build/ioda/pylib:$PYTHONPATH"
EOF_DOCKER
        else
            # Discovery logic (Improved with Python-native lookup)
            cat << 'EOF_DOCKER' > "$BUILD_WORKSPACE/Dockerfile"
FROM jcsda/docker-gnu-openmpi-dev:latest
USER root
RUN apt-get update && apt-get install -y python3-pip libeccodes-dev build-essential python3-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt --break-system-packages
RUN JEDI_PATH=$(python3 -c "import site; print(site.getsitepackages()[0])") && \
    echo "export PYTHONPATH=$JEDI_PATH:\$PYTHONPATH" >> /etc/bash.bashrc && \
    export PYTHONPATH="$JEDI_PATH:$PYTHONPATH" && \
    python3 -c "import ufo; print('✅ JEDI UFO found at:', ufo.__file__)"
EOF_DOCKER
        fi

        docker build -t aiesda_jedi:${JEDI_VERSION} -t aiesda_jedi:latest "$BUILD_WORKSPACE"
        rm -rf "$BUILD_WORKSPACE"
    fi
fi

###########################################################################################
# --- 4. Create Wrapper Script ---
###########################################################################################
AIESDA_BIN_DIR="${BUILD_DIR}/bin"
mkdir -p "$AIESDA_BIN_DIR"

cat << EOF > "${AIESDA_BIN_DIR}/jedi-run"
#!/bin/bash
if ! docker ps &>/dev/null; then
    echo "❌ ERROR: Docker daemon is not running."
    exit 1
fi
docker run -it --rm \\
	-v "\$(pwd):/home/aiesda" \\
    -v "${BUILD_DIR}:/app_build" \\
    -e PYTHONPATH="/app_build/lib:/app_build/lib/aiesda/pylib:/app_build/lib/aiesda/pydic:\$PYTHONPATH" \\
    -w /home/aiesda \\
    aiesda_jedi:${JEDI_VERSION} "\$@"
EOF
chmod +x "${AIESDA_BIN_DIR}/jedi-run"

###########################################################################################
# --- 5. Module Generation ---
###########################################################################################
mkdir -p "$(dirname "${JEDI_MODULE_FILE}")"
cat << EOF_MODULE > "${JEDI_MODULE_FILE}"
#%Module1.0
setenv           JEDI_VERSION    "${JEDI_VERSION}"
setenv           JEDI_METHOD     "docker"
setenv           JEDI_ROOT       "${BUILD_DIR}"
set version      "${JEDI_VERSION}"
set aiesda_bin   "${BUILD_DIR}/bin"
if { [file isdirectory \$aiesda_bin] } {
    prepend-path PATH          \$aiesda_bin
}
EOF_MODULE

echo "📋 Modulefile created at: ${JEDI_MODULE_FILE}"
JEDI_MODULE_DIR=$(dirname "${JEDI_MODULE_FILE}")
cd "${JEDI_MODULE_DIR}"
rm -f latest
ln -s "${JEDI_VERSION}" latest
echo "🔗 Linked jedi/${JEDI_VERSION} to jedi/latest"

###########################################################################################
# --- 6. Testing Environment & Instructions ---
###########################################################################################
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
