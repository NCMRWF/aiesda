#!/bin/bash
# ==============================================================================
# AIESDA Version-Specific Cleanup Utility (remove.sh)
# ==============================================================================

PROJECT_NAME="aiesda"

# Discover the Repo Root relative to this script's location
# This allows you to run 'bash jobs/remove.sh' from anywhere
JOBS_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "$JOBS_DIR/.." && pwd)

# Change directory to root so setup.py and VERSION are accessible
cd "$PROJECT_ROOT"
BUILD_ROOT="${HOME}/build"
MODULE_PATH="${HOME}/modulefiles"

# 1. Determine Target Version
if [ -z "$1" ]; then
    if [ -f "VERSION" ]; then
        TARGET_VERSION=$(cat VERSION | tr -d '[:space:]' | sed 's/\.0\+/\./g')
    else
        echo "❌ ERROR: No version specified. Usage: ./remove.sh 2026.1"
        exit 1
    fi
else
    TARGET_VERSION=$1
fi

SPECIFIC_BUILD="${BUILD_ROOT}/${PROJECT_NAME}_build_${TARGET_VERSION}"
# Path to requirements inside the build area (adjust based on your asset sync logic)
BUILD_REQUIREMENTS="${SPECIFIC_BUILD}/lib/aiesda/requirements.txt"

# 2. Extract JEDI Version from the TARGET BUILD requirements
if [ -f "$BUILD_REQUIREMENTS" ]; then
    # Extracts the version number even if the line is 'jedi==1.2.3' or 'jedi>=1.2.3'
    JEDI_VERSION=$(grep -iE "^jedi" "$BUILD_REQUIREMENTS" | head -n 1 | sed 's/.*[>=]\+\s*//g' | tr -d '[:space:]')
    
    # If the requirements just said 'jedi' without a version, default to 'latest'
    if [[ -z "$JEDI_VERSION" || "$JEDI_VERSION" == "jedi" ]]; then
        JEDI_VERSION="latest"
    fi
fi

# Fallback if the build area is already partially gone or requirements missing
JEDI_VERSION=${JEDI_VERSION:-"unknown"}

echo "🧹 Starting surgical cleanup for ${PROJECT_NAME} v${TARGET_VERSION}..."
[ "$JEDI_VERSION" != "unknown" ] && echo "🔗 Linked JEDI version detected: $JEDI_VERSION"

# Define JEDI paths based on the extracted version
JEDI_IMAGE="${PROJECT_NAME}_jedi:${JEDI_VERSION}" # Docker tag usually matches AIESDA version
JEDI_BUILD="${BUILD_ROOT}/jedi_build_${JEDI_VERSION}"
JEDI_MOD="${MODULE_PATH}/jedi/${JEDI_VERSION}"

# 3. Interactive JEDI Cleanup
if [[ -t 0 && "$JEDI_VERSION" != "unknown" ]]; then
    echo ""
    echo "❓ JEDI Component Detected (v${JEDI_VERSION})"
    read -p "Do you also want to remove the associated JEDI Docker image and bridge? (y/N): " confirm_jedi
else
    confirm_jedi="n"
fi

if [[ "$confirm_jedi" =~ ^[yY]$ ]]; then
    # Remove Docker Image
    if command -v docker &>/dev/null; then
        IMAGE_ID=$(docker images -q "$JEDI_IMAGE")
        if [ -n "$IMAGE_ID" ]; then
            echo "🐳 Removing Docker image: $JEDI_IMAGE"
            docker rmi -f "$IMAGE_ID"
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

