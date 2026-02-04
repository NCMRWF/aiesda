#%Module1.0
## Site-Specific Logic: Docker/WSL Bridge
## Location: aiesda/sites/docker/env_setup.tcl

# 1. Locate the SSoT (VERSION file)
# We assume the script is being called via the installer which sets PKG_ROOT
if { [info exists env(PKG_ROOT)] } {
    set version_file "$env(PKG_ROOT)/VERSION"
} else {
    # Fallback to the current directory if PKG_ROOT isn't exported
    set version_file "./VERSION"
}

# 2. Read and Trim the Version String
if { [file exists $version_file] } {
    set fp [open $version_file r]
    set raw_ver [read $fp]
    close $fp
    set aiesda_ver [string trim $raw_ver]
} else {
    # Fail-safe if version file is missing
    set aiesda_ver "unknown"
}

# 3. Dependency Check: Load the JEDI container bridge module
# The version is passed from the installer's JEDI_VERSION detection
set jedi_ver $env(JEDI_VERSION)
set aiesda_root	 "$env(HOME)/build/aiesda_build_$env(aiesda_ver)"
set aiesda_bin   \$aiesda_root/bin"

if { [module-info mode load] } {
    # Check if the modulefile exists before trying to load it
    if { [file exists "$::env(HOME)/modulefiles/jedi/$jedi_ver"] } {
        if { [is-loaded jedi/$jedi_ver] == 0 } {
            # If the JEDI module is available, load it. 
            # This module usually provides the 'jedi-run' command.
            catch { module load jedi/$jedi_ver }
            }
    } else {
        # Fallback for environments where the bridge is handled differently
        setenv JEDI_METHOD "manual"
    }
}


# 4. Pathing for the Docker Wrapper
# In Docker mode, we often use a 'bin' directory for shell wrappers 
# that translate local commands into 'docker exec' calls.
set aiesda_bin $aiesda_root/bin

if { [file isdirectory $aiesda_bin] } {
    prepend-path PATH $aiesda_bin
}

# 5. Environment Flags
# Inform AIESDA pylib that it is running in a container-bridged environment
setenv AIESDA_PLATFORM "docker"
setenv JEDI_EXEC_METHOD "container"

# 6. Verification Note (for 'module help')
proc ModulesHelp { } {
    puts stderr "This module configures AIESDA to communicate with JEDI via Docker."
    puts stderr "Method: jedi-run (Container Bridge)"
}

