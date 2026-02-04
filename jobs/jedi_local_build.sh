#!/bin/bash
# ==============================================================================
# AIESDA JEDI Local Builder (Native WSL Compilation)
# ==============================================================================
# jedi_local_build.sh

step_label() {
    echo "------------------------------------------------"
    echo "🏗️  LOCAL BUILD: $1"
    echo "------------------------------------------------"
}

# --- 1. Environment Configuration ---
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
REQUIREMENTS="$PROJECT_ROOT/requirements.txt"
JEDI_VERSION=$(grep -iE "^jedi[>=]*" "$REQUIREMENTS" | head -n 1 | sed 's/[^0-9.]*//g')
JEDI_VERSION=${JEDI_VERSION:-"latest"}

# Target Paths
JEDI_INSTALL_DIR="${HOME}/build/jedi_${JEDI_VERSION}"
JEDI_SRC_DIR="${HOME}/build/jedi_src_${JEDI_VERSION}"
MODULE_PATH="${HOME}/modulefiles/jedi/${JEDI_VERSION}"

###########################################################################################
# --- 2. Build Logic (Source Compilation) ---
###########################################################################################
if [ -d "$JEDI_INSTALL_DIR/bin" ]; then
    step_label "CHECK" "JEDI local build already exists at $JEDI_INSTALL_DIR"
else
    step_label "PREP" "Setting up Build Workspace..."
    mkdir -p "$JEDI_SRC_DIR"
    mkdir -p "$JEDI_INSTALL_DIR"

    cd "$JEDI_SRC_DIR"
    
    # 1. Clone the JEDI Bundle (The manifest for all components)
    if [ ! -d "jedi-bundle" ]; then
        git clone https://github.com/JCSDA/jedi-bundle.git
    fi

    # 2. Configure with ecbuild
    step_label "CONFIG" "Running ecbuild..."
    mkdir -p build && cd build
    ecbuild --init --prefix="$JEDI_INSTALL_DIR" ../jedi-bundle

    # 3. Compile and Install
    step_label "COMPILE" "Building JEDI components (UFO, IODA, OOPS, SABER)..."
    make -j$(nproc)
    make install
fi

###########################################################################################
# --- 3. Local Module Generation ---
###########################################################################################
step_label "MODULE" "Generating Modulefile..."
mkdir -p "$(dirname "$MODULE_PATH")"

cat << EOF_MODULE > "$MODULE_PATH"
#%Module1.0
## JEDI v${JEDI_VERSION} (Local Native Build)

set version      "${JEDI_VERSION}"
set jedi_root    "${JEDI_INSTALL_DIR}"

setenv           JEDI_VERSION    \$version
setenv           JEDI_METHOD     "local"
setenv           JEDI_ROOT       \$jedi_root

# Paths for Binaries and Libraries
prepend-path     PATH            \$jedi_root/bin
prepend-path     LD_LIBRARY_PATH \$jedi_root/lib
prepend-path     PYTHONPATH      \$jedi_root/lib/python3/dist-packages
prepend-path     PYTHONPATH      \$jedi_root/lib

proc ModulesHelp { } {
    puts stderr "This module enables the natively compiled JEDI stack."
    puts stderr "Location: ${JEDI_INSTALL_DIR}"
}
EOF_MODULE

echo "✅ Local JEDI Build and Module Complete!"
