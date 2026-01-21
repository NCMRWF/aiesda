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
python3 -m pip install --user --upgrade pip

if [ -f "$REQUIREMENTS" ]; then
    # We skip-broken or ignore legacy pynio/pyngl if they cause crashes
    python3 -m pip install --user -r "$REQUIREMENTS" || echo "⚠️ Some dependencies failed. Check C-libraries."
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

sudo apt update && sudo apt install environment-modules -y

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

###########################################################

# --- 5. Testing Environment ---
# We use a subshell to test so we don't mess up the current terminal
(
    # Try to find and source modules if available
    [ -f /usr/share/modules/init/bash ] && source /usr/share/modules/init/bash

    if command -v module >/dev/null 2>&1; then
        module use ${HOME}/modulefiles
        module load aiesda/${VERSION}
        echo "🧪 Testing module load..."
	# 2. Check environment variables
	echo $AIESDA_NML
	# 3. Check Python resolution
        python3 -c "import aidaconf; print('✅ Success! aidaconf found at:', aidaconf.__file__)"
    else
        echo "⚠️  Note: 'module' command not found. Environment module created but not tested."
        echo "   To fix: sudo apt install environment-modules"
    fi
)

