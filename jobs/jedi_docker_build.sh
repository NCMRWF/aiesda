#!/bin/bash
# ==============================================================================
# AIESDA JEDI Docker Builder
# This script handles the JEDI-bridge image creation for WSL/Laptop users.
# ==============================================================================

# Inherit variables from main installer or set defaults
VERSION=${VERSION:-"dev"}
BUILD_WORKSPACE="${HOME}/build/docker_build_tmp"
PROJECT_ROOT=$(pwd)

echo "🏗️  Starting JEDI-Enabled Docker Build (v${VERSION})..."

mkdir -p "$BUILD_WORKSPACE"

# 1. Copy requirements from the project root (assuming we are in /jobs)
if [ -f "../requirement.txt" ]; then
    cp "../requirement.txt" "$BUILD_WORKSPACE/"
elif [ -f "./requirement.txt" ]; then
    cp "requirement.txt" "$BUILD_WORKSPACE/"
else
    echo "❌ ERROR: requirement.txt not found!"
    exit 1
fi

# 2. Generate the Dockerfile
# Using 'EOF_DOCKER' (quoted) is critical to prevent local variable expansion.
cat << 'EOF_DOCKER' > "$BUILD_WORKSPACE/Dockerfile"
FROM jcsda/docker-gnu-openmpi-dev:latest
USER root

# 1. Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    libeccodes-dev \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Setup Working Directory
WORKDIR /home/aiesda
COPY requirement.txt .

# 3. Install Python Stack
RUN python3 -m pip install --no-cache-dir -r requirement.txt --break-system-packages

# 4. DYNAMIC PATH DISCOVERY
# This finds the ufo module parent dir and injects it into the system environment
RUN JEDI_BASE_DIR=$(find /usr/local -name "ufo" -type d | head -n 1) && \
    if [ -n "$JEDI_BASE_DIR" ]; then \
        JEDI_PATH=$(dirname "$JEDI_BASE_DIR"); \
        echo "export PYTHONPATH=$JEDI_PATH:/home/aiesda/lib/aiesda/pylib:/home/aiesda/lib/aiesda/pydic:\$PYTHONPATH" >> /etc/bash.bashrc; \
        echo "PYTHONPATH=$JEDI_PATH:/home/aiesda/lib/aiesda/pylib:/home/aiesda/lib/aiesda/pydic:\$PYTHONPATH" >> /etc/environment; \
    else \
        echo "Warning: JEDI ufo module not found during build discovery."; \
    fi

# 5. Static PYTHONPATH Fallback (Standard locations for JCSDA images)
ENV PYTHONPATH="/usr/local/bundle/install/lib/python3.10/dist-packages:/usr/local/lib/python3.10/dist-packages:/usr/local/bundle/install/lib/python3.12/dist-packages:/usr/local/lib/python3.12/dist-packages:/home/aiesda/lib/aiesda/pylib:/home/aiesda/lib/aiesda/pydic"

# 6. Verification check (Crucial: finds the path and imports in one RUN layer)
RUN JEDI_BASE_DIR=$(find /usr/local -name "ufo" -type d | head -n 1) && \
    if [ -z "$JEDI_BASE_DIR" ]; then echo "❌ FAILED: ufo module not found"; exit 1; fi && \
    export JEDI_PATH=$(dirname "$JEDI_BASE_DIR") && \
    export PYTHONPATH="$JEDI_PATH:$PYTHONPATH" && \
    python3 -c "import ufo; print('✅ JEDI UFO found at:', ufo.__file__)"
EOF_DOCKER

# 3. Build the image
docker build --no-cache -t aiesda_jedi:${VERSION} -t aiesda_jedi:latest \
             -f "$BUILD_WORKSPACE/Dockerfile" "$BUILD_WORKSPACE"

# 4. Cleanup
BUILD_STATUS=$?
rm -rf "$BUILD_WORKSPACE"

if [ $BUILD_STATUS -eq 0 ]; then
    echo "✅ Docker build successful: aiesda_jedi:${VERSION}"
else
    echo "❌ Docker build failed."
    exit 1
fi
