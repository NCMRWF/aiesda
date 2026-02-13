#!/bin/bash
SELF=$(realpath $0)
PKGHOME=${PKGHOME:-${SELF%/site/*}}
PKGNAM=${PKGHOME##*/}
JOBDIR="${PKGHOME}/jobs"
PYSCRYPT=$(realpath $1)
shift
ARGS=$@


module load python/3.9
module load jedi-oops/1.4.0/openmpi/5.0.3/gcc/8.5
module load ioda-bundle/1.0.0/openmpi/5.0.3/gcc/8.5
