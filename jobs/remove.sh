#!/bin/bash
# ==============================================================================
# AIESDA Version-Specific Cleanup Utility (remove.sh)
# ==============================================================================
# remove.sh
###########################################################################################
helpdesk()
{
echo -e "Usage: \n $0"
                        echo "options:"
			echo "-h	--help		Help"
			echo "-s	--site		site information for coustum settings"
			echo "-v	--version	target version for removal"
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
			-v|--version)	shift; TARGET_VERSION=$1; shift;;
		    -p|--pkg)	shift; PKG_NAME=$1; shift;;
		    *)		shift;;
	esac
done
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
export PKG_NAME=${PKG_ROOT##*/:-"aiesda"}
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

# Change directory to root so setup.py and VERSION are accessible
cd "$PROJECT_ROOT"

MODULE_PATH="${HOME}/modulefiles"

# 1. Determine Target Version
if [ -z "${TARGET_VERSION}" ]; then
    if [ -f "VERSION" ]; then
        TARGET_VERSION=$(cat VERSION | tr -d '[:space:]' | sed 's/\.0\+/\./g')
    else
        echo "❌ ERROR: No version specified. Usage: ./remove.sh 2026.1"
        exit 1
    fi
fi

SPECIFIC_BUILD="${BUILD_ROOT}/${PROJECT_NAME}_build_${TARGET_VERSION}"
# Path to requirements inside the build area (adjust based on your asset sync logic)
BUILD_REQUIREMENTS="${SPECIFIC_BUILD}/lib/aiesda/requirements.txt"

# 2. Extract JEDI Version and Dependencies from the TARGET BUILD requirements
if [ -f "$BUILD_REQUIREMENTS" ]; then
    # Extracts the version number
    JEDI_VERSION=$(grep -iE "^jedi" "$BUILD_REQUIREMENTS" | head -n 1 | sed 's/.*[>=]\+\s*//g' | tr -d '[:space:]')
    
    # Identify the specific libraries registered in this build
    # This filters for the core DA libraries defined in your COMPLEX_BLOCKS
    LIBS_IN_BUILD=$(grep -iE "^(ufo|ioda|soca|fv3jedi|oops|saber|vader)" "$BUILD_REQUIREMENTS" | cut -d'=' -f1 | cut -d'>' -f1 | tr '\n' ' ')
	
    if [[ -z "$JEDI_VERSION" || "$JEDI_VERSION" == "jedi" ]]; then
        JEDI_VERSION="latest"
    fi
fi

# Fallback if the build area is already partially gone or requirements missing.
JEDI_VERSION=${JEDI_VERSION:-"unknown"}

echo "🧹 Starting surgical cleanup for ${PROJECT_NAME} v${TARGET_VERSION}..."
[ "$JEDI_VERSION" != "unknown" ] && echo "🔗 Linked JEDI version detected: $JEDI_VERSION"

# --- ADDED: Print the specific libraries being de-referenced ---
if [ ! -z "$LIBS_IN_BUILD" ]; then
    echo -e "📦 Dependencies tracked in this version: \033[1;36m${LIBS_IN_BUILD}\033[0m"
fi

# Define JEDI paths based on the extracted version
JEDI_IMAGE="${PROJECT_NAME}_jedi:${JEDI_VERSION}" # Docker tag usually matches AIESDA version
JEDI_BUILD="${BUILD_ROOT}/jedi_build_${JEDI_VERSION}"
JEDI_MOD="${MODULE_PATH}/jedi/${JEDI_VERSION}"

# 3. Interactive JEDI Cleanup
DO_FULL_WIPE="false"

# ADD THIS: Extract current requirement to compare against the build being removed
NEW_JEDI_REQ=$(grep -iE "^jedi" "${PROJECT_ROOT}/requirements.txt" 2>/dev/null | sed 's/.*[>=]\+\s*//g' | tr -d '[:space:]')
OLD_JEDI_INSTALLED=$JEDI_VERSION

# Only wipe JEDI if SITE is Docker AND Version is different.
# In all other cases (HPC or same version), we skip the deep wipe.

if [[ "$SITE_NAME" == "docker" ]] && [[ "$NEW_JEDI_REQ" != "$OLD_JEDI_INSTALLED" ]]; then
    echo "⚠️  Docker & JEDI version mismatch detected ($OLD_JEDI_INSTALLED -> $NEW_JEDI_REQ)."
    if [[ -t 0 ]]; then
        echo ""
       	echo "❓ JEDI Component Detected (v${JEDI_VERSION})"
       	read -p "Do you also want to remove the associated JEDI Docker image and bridge? (y/N): " confirm_jedi
       	DO_FULL_WIPE="true"
    else
    	if [[ "$JEDI_VERSION" == "unknown" ]]; then
		confirm_jedi="y"
	else
		confirm_jedi="n"
    	fi
    fi
fi

if [[ "$DO_FULL_WIPE" == "true" ]]; then
    # Remove Docker Image
    trap 'rm -f .docker_cleaning' EXIT SIGINT SIGTERM
    if command -v docker &>/dev/null; then
        IMAGE_ID=$(docker images -q "$JEDI_IMAGE")
        if [ -n "$IMAGE_ID" ]; then
            echo "🐳 Removing Docker image: $JEDI_IMAGE"
	    # 1. Create the flag
            touch .docker_cleaning
            # 2. RUN IN BACKGROUND and remove flag when finished
            (docker rmi -f "$IMAGE_ID" &>/dev/null; rm -f .docker_cleaning) &
            spin='-\|/'
	    i=0
	    # Loop as long as the flag file exists
	    while [ -f .docker_cleaning ]; do
	       i=$(( (i+1) % 4 ))
	       printf "\r [%s] Processing cleanup..." "${spin:$i:1}"
	       sleep .1
	    done
            echo " Docker image cleaning ✅ Done."
        fi
    fi

    # Remove JEDI Build Dir (bridge/bin)
    [ -d "$JEDI_BUILD" ] && rm -rf "$JEDI_BUILD" && echo "✅ JEDI bridge cleared."

    # Remove JEDI Modulefile (using the version extracted from requirements)
    if [ -f "$JEDI_MOD" ]; then
        echo "📋 Removing JEDI modulefile: $JEDI_MOD"
        rm -f "$JEDI_MOD"
        rmdir "$(dirname "$JEDI_MOD")" 2>/dev/null
    fi
fi

# 4. Remove Specific AIESDA Build Directory
if [ -d "$SPECIFIC_BUILD" ]; then
    echo "📂 Removing AIESDA build directory: $SPECIFIC_BUILD"
    rm -rf "$SPECIFIC_BUILD"
    echo "✅ AIESDA build cleared."
fi

# 5. Remove AIESDA Modulefile
SPECIFIC_MODULE="${MODULE_PATH}/${PROJECT_NAME}/${TARGET_VERSION}"
if [ -f "$SPECIFIC_MODULE" ]; then
    echo "📋 Removing AIESDA modulefile: $SPECIFIC_MODULE"
    rm -f "$SPECIFIC_MODULE"
    rmdir "$(dirname "$SPECIFIC_MODULE")" 2>/dev/null
fi

echo "------------------------------------------------------------"
echo "✨ Cleanup for v${TARGET_VERSION} complete."
echo "------------------------------------------------------------"

