#! python3
"""
Artificial Intelligence Data Assimilation Monthly Report
Created on Wed Jan 14 19:56:48 2026
@author: gibies
https://github.com/Gibies
"""
import os
import sys
CURR_PATH=os.path.dirname(os.path.abspath(__file__))
PKGHOME=os.path.dirname(CURR_PATH)
OBSLIB=os.environ.get('OBSLIB',PKGHOME+"/pylib")
sys.path.append(OBSLIB)
OBSDIC=os.environ.get('OBSDIC',PKGHOME+"/pydic")
sys.path.append(OBSDIC)
OBSNML=os.environ.get('OBSNML',PKGHOME+"/nml")
sys.path.append(OBSNML)

"""
report.py
"""

from scilib import AidaReportCard
from scilib import AssimilationValidator
from aidaconf import AidaConfig

# Initialize the reporter
report_gen = AidaReportCard(expid="AIESDA_V1", root_dir="./work")

# Example loop over a week of data
start_date = datetime(2026, 1, 1)
for i in range(28):  # 7 days * 4 cycles
    current_dt = start_date + timedelta(hours=i*6)
    dstr = current_dt.strftime('%Y%m%d')
    cstr = current_dt.strftime('%H')

    # Mock-up config for this cycle to locate files
    conf = AidaConfig(argparse.Namespace(date=dstr, cycle=cstr, expid="AIESDA_V1"))

    # Calculate stats using the Validator we built earlier
    validator = AssimilationValidator(conf)
    try:
        inc = validator.calculate_increment(conf.OUTDIR+"/analysis.nc", conf.GESDIR+"/guess.nc")
        stats = validator.compute_stats(inc)

        # Record the stats into the report card
        report_gen.collect_cycle_metrics(dstr, cstr, stats)
    except FileNotFoundError:
        continue

# Save the final report
report_gen.generate_summary_report("./reports")
