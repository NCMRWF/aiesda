#!/bin/bash
# ==============================================================================
# AIESDA CalVer Bumper (yyyy.mm.xx) - SSoT Logic
# ==============================================================================
PROJECT_NAME="aiesda"

# Discover the Repo Root relative to this script's location
# This allows you to run 'bash jobs/bump_version.sh' from anywhere
JOBS_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "$JOBS_DIR/.." && pwd)

# Change directory to root so setup.py and VERSION are accessible
cd "$PROJECT_ROOT"
VERSION_FILE="VERSION"

# 1. Read the current version and strip leading zeros (e.g., 2026.01.01 -> 2026.1.1)
CURRENT_VERSION=$(cat "$VERSION_FILE" 2>/dev/null | tr -d '[:space:]' | sed 's/\.0\+/\./g')
CURRENT_VERSION=${CURRENT_VERSION:-"2026.1.0"}

# 2. Get current system Year and Month (stripped of leading zeros)
NOW_YYYY=$(date +%Y)
NOW_MM=$(date +%-m)

# 3. Parse Current Version parts
OLD_YYYY=$(echo "$CURRENT_VERSION" | cut -d. -f1)
OLD_MM=$(echo "$CURRENT_VERSION" | cut -d. -f2)
OLD_XX=$(echo "$CURRENT_VERSION" | cut -d. -f3)
OLD_XX=${OLD_XX:-0}

# 4. Logic: If Year/Month changed, reset XX to 1. Otherwise, increment XX.
if [ "$NOW_YYYY" != "$OLD_YYYY" ] || [ "$NOW_MM" != "$OLD_MM" ]; then
    NEW_XX=1
else
    NEW_XX=$((OLD_XX + 1))
fi

NEW_VERSION="${NOW_YYYY}.${NOW_MM}.${NEW_XX}"

# 5. Update the Single Source of Truth
echo "$NEW_VERSION" > "$VERSION_FILE"
echo "🆙 Version updated in SSoT: $CURRENT_VERSION -> $NEW_VERSION"
