#!/bin/bash
VERSION="0.1.0"
PROJECT_NAME="aiesda"
PROJECT_ROOT=$(pwd)
BUILD_DIR="${HOME}/build/${PROJECT_NAME}_build_${VERSION}"
MODULE_FILE="${HOME}/modulefiles/${PROJECT_NAME}/${VERSION}"

echo "🚀 Installing ${PROJECT_NAME} v${VERSION}..."

# 1. Clean and Build
rm -rf "${BUILD_DIR}"
python3 setup.py build --build-base "${BUILD_DIR}"

# 2. Sync Configs to the Build Lib (for portability)
# We place them inside the aiesda package folder in the build path
INSTALL_LIB_PATH="${BUILD_DIR}/lib/aiesda"
mkdir -p "${INSTALL_LIB_PATH}/config"
cp -r nml yaml palette jobs "${INSTALL_LIB_PATH}/config/"

# 3. Create Module
mkdir -p $(dirname "${MODULE_FILE}")
cat << EOF > "${MODULE_FILE}"
#%Module1.0
set version    ${VERSION}
set build_path ${BUILD_DIR}/lib

prepend-path    PYTHONPATH    \$build_path
prepend-path    PATH          ${PROJECT_ROOT}/scripts

setenv          AIESDA_VERSION ${VERSION}
setenv          AIESDA_CONF    ${INSTALL_LIB_PATH}/config
setenv          AIESDA_NML     ${INSTALL_LIB_PATH}/config/nml
setenv          AIESDA_YAML    ${INSTALL_LIB_PATH}/config/yaml
EOF

echo "✅ Environment ready. Load with: module load ${PROJECT_NAME}/${VERSION}"
