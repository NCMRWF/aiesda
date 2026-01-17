#! python3
"""
Artificial Intelligence Data Assimilation Dictionary
Created on Wed Jan 14 19:45:25 2026
@author: gibies
https://github.com/Gibies
"""
CURR_PATH=os.path.dirname(os.path.abspath(__file__))
PKGHOME=os.path.dirname(CURR_PATH)
OBSLIB=os.environ.get('OBSLIB',PKGHOME+"/pylib")
sys.path.append(OBSLIB)
OBSDIC=os.environ.get('OBSDIC',PKGHOME+"/pydic")
sys.path.append(OBSDIC)
OBSNML=os.environ.get('OBSNML',PKGHOME+"/nml")
sys.path.append(OBSNML)

"""
aidadic.py
"""

jedi_anemoi_var_mapping = {
    'air_temperature': '2t',
    'eastward_wind': 'u10',
    'northward_wind': 'v10',
    'specific_humidity': 'q'
  }
