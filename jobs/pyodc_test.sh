
export TESTJOB="$(basename "${BASH_SOURCE[0]}")"
export JOBSDIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
export PKGHOME="$(dirname ${JOBSDIR})"
export TESTDIR="${PKGHOME}/test"
export SRPTDIR="${PKGHOME}/scripts"

echo ${TESTDIR}

module load python/3.12.5
module load pyodc/1.6.0
module load eccodes/2.41.0/openmpi/5.0.3/gcc/8.5 
module load odbserver/0.16.2/intel/2020.4.304

#cd ${TESTDIR}
#python pyodctest.py

cd ${SRPTDIR}
#export BUFRFILE="/scratch/ncmrwf/prod/data/nwdata/gts/20260925/IS/ISIN01_DEMS_250300_080.bul"
export BUFRFILE="/scratch/ncmrwf/prod/data/nwdata/gts/20261004/IS/ISIN01_DEMS_040900_926.bul"
export ODB2FILE="/home/ncmrwf/hpc/gibies/research/aiesda/test/ISIN01_DEMS_test.odb2"
python bufr_to_odb.py

