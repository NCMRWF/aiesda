
import subprocess
import sys
import os
CURR_PATH=os.path.dirname(os.path.abspath(__file__))
PKGHOME=os.path.dirname(CURR_PATH)
OBSLIB=os.environ.get('OBSLIB',PKGHOME+"/pylib")
sys.path.append(OBSLIB)
OBSDIC=os.environ.get('OBSDIC',PKGHOME+"/pydic")
sys.path.append(OBSDIC)
OBSNML=os.environ.get('OBSNML',PKGHOME+"/nml")
sys.path.append(OBSNML)
obs_index_nml=OBSNML+"/obs_index_nml"
odb_index_nml=OBSNML+"/odb_index_nml"
varobs_nml=OBSNML+"/varobs_nml"
varcx_surf_nml=OBSNML+"/varcx_surf_nml"
varcx_uair_nml=OBSNML+"/varcx_uair_nml"

import codc
import pandas
import obscodc
#import sqlodb


if __name__ == "__main__":
    # Replace with your actual input and output filenames
    odbfile = None
    varnolist=[2]
    print(dir(codc))
    print(varnolist)
    obscodc.odbquery(odbfile,varnolist=varnolist)
