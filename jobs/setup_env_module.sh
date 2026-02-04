#!/bin/bash
# ==============================================================================
# Environment Modules Availability Check & Setup
# ==============================================================================
# setup_env_module.sh


setup_modules() {
    echo "🔍 Checking for Environment Modules..."

    # 1. Check if 'module' is already a function/alias/command
    if command -v module >/dev/null 2>&1 || type module >/dev/null 2>&1; then
        echo "✅ Environment Modules are already active."
        return 0
    fi

    # 2. Check if installed but just not sourced
    local init_script="/usr/share/modules/init/bash"
    if [ -f "$init_script" ]; then
        echo "🔗 Modules installed but not sourced. Initializing now..."
        source "$init_script"
        return 0
    fi

    # 3. If not found at all, install it (Requires sudo)
    echo "⚠️ Environment Modules not found. Starting installation..."
    
    # Check for sudo privileges
    if ! command -v sudo >/dev/null 2>&1; then
        echo "❌ ERROR: sudo is required to install 'environment-modules'. Please install manually."
        exit 1
    fi

    sudo apt update && sudo apt install -y environment-modules

    # 4. Source the newly installed script
    if [ -f "$init_script" ]; then
        source "$init_script"
        echo "✅ Modules installed and initialized."
    else
        echo "❌ ERROR: Installation finished but $init_script was not found."
        exit 1
    fi
}

# Run the function
setup_modules

# Verify
if command -v module >/dev/null 2>&1; then
    echo "🚀 Module system is ready. Path: $(which module 2>/dev/null || echo 'Shell Function')"
else
    echo "❌ Module system failed to initialize."
fi
