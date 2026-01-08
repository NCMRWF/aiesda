import sys, os
CURR_PATH=os.path.dirname(os.path.abspath(__file__))
PKGHOME=os.path.dirname(CURR_PATH)
OBSLIB=os.environ.get('OBSLIB',PKGHOME+"/pylib")
sys.path.append(OBSLIB)
OBSDIC=os.environ.get('OBSDIC',PKGHOME+"/pydic")
sys.path.append(OBSDIC)
OBSNML=os.environ.get('OBSNML',PKGHOME+"/nml")
sys.path.append(OBSNML)

usernam=os.environ.get('USER',"myhome")
#sys.path.append("/home/"+usernam+"/packages/monitobs/pylib")
import obsmod

datauser="meena"

datapath="/scratch/"+datauser+"/data/postprocessed/sattcwv_obstore/sattcwv_umprod_gdas_dump_20230601_12"
plotpath="/scratch/"+usernam+"/plots"
nmlpath="/home/"+datauser+"/packages/monitobs/nml"
obstypelist = ["sattcwv"]
text="20230601T1200Z SatTCWV"
title="20230601T1200Z SatTCWV"
pltnam="SatTCWV_20230601T1200Z"

obsmod.obs_latlon_plot(datapath,plotpath,nmlpath,obstypelist=obstypelist,text=text,title=title,pltnam=pltnam)
