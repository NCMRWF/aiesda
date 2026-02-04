#!/bin/bash
# ==============================================================================
# AIESDA Development Cycle Stress Test
# ==============================================================================
# aiesda-dev-cycle-test.sh
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
# Helper for clean progress reporting
step_label() {
    echo -e "\n\033[1;34m[STEP $1]: $2\033[0m"
    echo "------------------------------------------------"
}
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
PKG_NAME=${PKG_ROOT##*/}
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
###########################################################################################
# Auto-revert version if the test fails
trap 'echo "$START_VER" > VERSION; echo "⚠️ Test failed. Version reverted to $START_VER."' ERR
set -e  # Immediate exit on error

# Ensure we are in the repo root
if [ ! -f "VERSION" ]; then
    echo "❌ ERROR: Run this from the repository root."
    exit 1
fi

PROJECT_NAME="aiesda"
START_VER=$(cat VERSION | tr -d '[:space:]')

echo "🚀 Starting Dev Cycle Test [Current Version: $START_VER]"

# ---------------------------------------------------------
# 1. VERSION BUMP
# ---------------------------------------------------------
echo "🔢 Bumping version..."
make bump
NEW_VER=$(cat VERSION | tr -d '[:space:]' | sed 's/\.0\+/\./g')
echo "✅ Target Version set to: $NEW_VER"

# ---------------------------------------------------------
# 2. CLEAN INSTALLATION
# ---------------------------------------------------------
echo "🏗️  Executing Out-of-Source Installation..."
# We pipe 'n' to install.sh in case it asks for sudo/interactive prompts 
# (assuming your environment is already pre-configured)
bash ${JOBS_DIR}/install.sh -v "${NEW_VER}" -s "${SITE_NAME}"

# ---------------------------------------------------------
# 3. ARCHITECTURE VERIFICATION
# ---------------------------------------------------------
echo "🧐 Verifying 'Away' File System..."

echo ${PROJECT_NAME}
LOG_BASE="${HOME}/logs/$(date +%Y/%m/%d)/${PROJECT_NAME}/${NEW_VER}"
BUILD_DIR="${HOME}/build/${PROJECT_NAME}_build_${NEW_VER}"

[ -d "$BUILD_DIR" ] && echo "✅ Build Directory exists." || { echo "❌ Build Dir Missing"; exit 1; }
[ -f "${LOG_BASE}/install.log" ] && echo "✅ Log File exists." || { echo "❌ Log Missing"; exit 1; }

# ---------------------------------------------------------
# 4. RUNTIME & NAMESPACE TEST
# ---------------------------------------------------------
echo "🐍 Testing Python Namespace and CLI..."
(
    # Simulate a user environment
    source /etc/profile.d/modules.sh 2>/dev/null || source /usr/share/modules/init/bash 2>/dev/null
    module use "${HOME}/modulefiles"
    module load "${PROJECT_NAME}/${NEW_VER}"
    
    # Check if the CLI is in the PATH
    if command -v aiesda-run >/dev/null 2>&1; then
        echo "✅ CLI 'aiesda-run' is in PATH."
        aiesda-run --status
    else
        echo "❌ CLI 'aiesda-run' NOT found."
        exit 1
    fi
)

# ---------------------------------------------------------
# 5. SURGICAL REMOVAL
# ---------------------------------------------------------
echo "🧹 Testing Surgical Uninstaller..."
# We provide 'n' to avoid deleting the Docker image during every dev test
echo "n" | bash remove.sh -v "${NEW_VER}" -s "${SITE_NAME}"

if [ ! -d "$BUILD_DIR" ]; then
    echo "✅ Cleanup verified: $BUILD_DIR is gone."
else
    echo "❌ Cleanup failed: $BUILD_DIR still exists."
    exit 1
fi

echo "------------------------------------------------"
echo "✨ DEV CYCLE TEST PASSED for v${NEW_VER} ✨"
echo "------------------------------------------------"
