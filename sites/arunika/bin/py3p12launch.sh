#!/bin/bash
SELF=$(realpath $0)
PKGHOME=${PKGHOME:-${SELF%/site/*}}
PKGNAM=${PKGHOME##*/}
JOBDIR="${PKGHOME}/jobs"
PYSCRYPT=$(realpath $1)
shift
ARGS=$@

module load python/3.12.5
