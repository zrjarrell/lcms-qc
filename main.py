import json
import os

from utilities import mkdir_if_not
from raw_manipulation import convert_mzxmls

from classes import QCResult

DEBUG = True
config = json.load(open("config.json"))

study_directory = "C:/Users/zjarrel/Desktop/explorisQC/test-raws"

""" #setup qc dir and 
mkdir_if_not(study_directory + "/qc")
#converts raw to mzxml, separates mzxmls by method
error_files = convert_mzxmls(study_directory)

#perform xcms extraction method-wise
methods = ["hilicpos", "c18neg"]
QCs = []
for method in methods:
    subset_path = study_directory + "/qc/mzxml/" + method
    if os.path.exists(subset_path):
        command = f"Rscript xcms_runscript.R {subset_path} {DEBUG}"
        if DEBUG:
            subprocess.run(command, stdout=subprocess.PIPE)
        else:
            subprocess.run(command)
        QCs += [QCResult(method, subset_path + "/featuretable.csv", subset_path, study_directory)] """




methods = ["hilicpos", "c18neg"]
QCs = []
for method in methods:
    subset_path = study_directory + "/qc/mzxml/" + method
    if os.path.exists(subset_path):
        QCs += [QCResult(method, subset_path + "/featuretable.csv", subset_path, study_directory)]

for qc in QCs:
    qc.get_ft()
    qc.count_peaks()
    qc.get_machine_info()
    qc.get_scan_stats()
    qc.get_runtimes()
    qc.get_targets()
    qc.get_meanmedianint()
    qc.get_replicability()

qc = QCs[0]


#get EICs of target matches
