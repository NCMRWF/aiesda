#%Module1.0
## Site-Specific Logic: Docker/WSL Bridge
## Location: aiesda/sites/docker/env_setup.tcl

# 1. Dependency Check: Load the JEDI container bridge module
# The version is passed from the installer's JEDI_VERSION detection
set jedi_ver $env(JEDI_VERSION)

if { [is-loaded jedi/$jedi_ver] == 0 } {
    # If the JEDI module is available, load it. 
    # This module usually provides the 'jedi-run' command.
    catch { module load jedi/$jedi_ver }
}

# 2. Pathing for the Docker Wrapper
# In Docker mode, we often use a 'bin' directory for shell wrappers 
# that translate local commands into 'docker exec' calls.
set aiesda_bin $aiesda_root/bin

if { [file isdirectory $aiesda_bin] } {
    prepend-path PATH $aiesda_bin
}

# 3. Environment Flags
# Inform AIESDA pylib that it is running in a container-bridged environment
setenv AIESDA_PLATFORM "docker"
setenv JEDI_EXEC_METHOD "container"

# 4. Verification Note (for 'module help')
proc ModulesHelp { } {
    puts stderr "This module configures AIESDA to communicate with JEDI via Docker."
    puts stderr "Method: jedi-run (Container Bridge)"
}

# 5. Provision for manual JEDI run
if { [module-info mode load] } {
    # Check if the modulefile exists before trying to load it
    if { [file exists "$::env(HOME)/modulefiles/jedi/latest"] } {
        module load jedi/latest
    } else {
        # Fallback for environments where the bridge is handled differently
        setenv JEDI_METHOD "manual"
    }
}
