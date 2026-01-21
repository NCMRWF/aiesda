#!/bin/bash
# --- 1. Configuration ---
VERSION="0.1.0"
PROJECT_NAME="aiesda"
PROJECT_ROOT=$(pwd)
BUILD_DIR="${HOME}/build/${PROJECT_NAME}_build_${VERSION}"
MODULE_FILE="${HOME}/modulefiles/${PROJECT_NAME}/${VERSION}"
REQUIREMENTS="${PROJECT_ROOT}/requirement.txt"

echo "🚀 Installing ${PROJECT_NAME} v${VERSION}..."
#########################################################

# --- 2. Dependency Management ---
echo "🐍 Upgrading pip and installing requirements..."
python3 -m pip install --upgrade pip

if [ -f "$REQUIREMENTS" ]; then
    python3 -m pip install -r "$REQUIREMENTS"
else
    echo "⚠️  Warning: requirement.txt not found, skipping pip install."
fi

rm -rf "${BUILD_DIR}"
python3 setup.py build --build-base "${BUILD_DIR}"
##########################################################

# --- 3. Internal Paths ---
# The root of the package inside the build path
AIESDA_INSTALLED_ROOT="${BUILD_DIR}/lib/aiesda"

# Ensure the build lib directory exists before copying assets
mkdir -p "${AIESDA_INSTALLED_ROOT}"

echo "📂 Snapshotting assets to build directory..."
cp -rp ${PROJECT_ROOT}/nml ${AIESDA_INSTALLED_ROOT}/
cp -rp ${PROJECT_ROOT}/yaml ${AIESDA_INSTALLED_ROOT}/
cp -rp ${PROJECT_ROOT}/jobs ${AIESDA_INSTALLED_ROOT}/
###########################################################

# --- 4. Generate Environment Module ---
mkdir -p $(dirname "${MODULE_FILE}")
cat << EOF > "${MODULE_FILE}"
#%Module1.0
## AIESDA Environment Module v${VERSION}

set version      ${VERSION}
set aiesda_root  ${AIESDA_INSTALLED_ROOT}

module-whatis    "AIESDA Framework v${VERSION}"

# Environment Variables
setenv           AIESDA_VERSION  ${VERSION}
setenv           AIESDA_ROOT     \$aiesda_root
setenv           AIESDA_NML      \$aiesda_root/nml
setenv          AIESDA_YAML     \$aiesda_root/yaml

# Logic Access
prepend-path     PYTHONPATH      \$aiesda_root/pylib

# Script Access (Versioned)
prepend-path     PATH            \$aiesda_root/jobs
EOF

echo "------------------------------------------------------------"
echo "✅ Installation Complete!"
echo "   Module: ${PROJECT_NAME}/${VERSION}"
echo "   All assets (nml, yaml, scripts) are now in the build path."
echo "------------------------------------------------------------"
