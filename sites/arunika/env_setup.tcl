#%Module1.0
## Site-Specific Logic: Arunika HPC
## Location: aiesda/sites/arunika/env_setup.tcl

# 1. Load the Base Native Python Environment
if { [is-loaded python/3.9] == 0 } {
    module load python/3.9
}

# 2. Load the JEDI OOPS (Object-Oriented Prediction System)
if { [is-loaded jedi-oops/1.4.0/openmpi/5.0.3/gcc/8.5] == 0 } {
    module load jedi-oops/1.4.0/openmpi/5.0.3/gcc/8.5
}

# 3. Load the JEDI IODA (Interface for Observational Data Assimilation) Bundle
if { [is-loaded ioda-bundle/1.0.0/openmpi/5.0.3/gcc/8.5] == 0 } {
    module load ioda-bundle/1.0.0/openmpi/5.0.3/gcc/8.5
}

# 4. Load the JEDI SABER (System-Agnostic Background Error Representation)
if { [is-loaded saber/1.1.3/openmpi/5.0.3/gcc/8.5] == 0 } {
module load saber/1.1.3/openmpi/5.0.3/gcc/8.5
}

# 5. Load the JEDI UFO (Unified forward operator)
if { [is-loaded ufo/1.0.0/openmpi/5.0.3/gnu/8.5] == 0 } {
module load ufo/1.0.0/openmpi/5.0.3/gnu/8.5
}

# 4. Environment Flags for HPC Performance
setenv AIESDA_PLATFORM "arunika"
setenv JEDI_EXEC_METHOD "native"

# Optional: Set MPI specific settings if required by your model
setenv OMPI_MCA_btl_openib_allow_ib 1

proc ModulesHelp { } {
    puts stderr "This module configures AIESDA for the Arunika HPC environment."
    puts stderr "Components: Python 3.9, JEDI-OOPS 1.4.0, IODA 1.0.0, SABER 1.1.3, UFO 1.0.0"
}
