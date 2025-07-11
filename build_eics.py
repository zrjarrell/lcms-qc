import subprocess, json
import pandas as pd
from copy import deepcopy
from os.path import dirname

from target_matching import match_feature

config = json.load(open("config.json"))

def build_eics(qc):
    matches = deepcopy(qc.target_matches[qc.target_matches["ft.index"] >= 0])
    if len(matches) == 0:
        return
    else:
        matches["ft.index"] = matches["ft.index"] + 1
        path = qc.ft_path.split("/featuretable.csv")[0]
        matches.to_csv(path + "/matches.csv", index=False)
        command = f"Rscript xcms_eics.R {path}"
        print(command)
        subprocess.run(command, stdout=subprocess.PIPE)

def build_eics_qstd(experimentID, ft, path, mode):
    targets = config["internalStd_targets"][mode]
    matches = pd.DataFrame()
    for target in targets:
        new_result = match_feature(ft, target)
        matches = pd.concat([matches, new_result], ignore_index=True)
    path = dirname(path)
    matches = matches[matches["ft.index"] >= 0]
    if len(matches) == 0:
        return "NA"
    else:
        matches["ft.index"] = matches["ft.index"] + 1
        matches.to_csv(path + "/matches.csv", index=False)
        output_name = f"./db/eics/{experimentID}_{mode}_eics.pdf"
        command = f"Rscript xcms_eics.R {path} {output_name}"
        print(command)
        subprocess.run(command, stdout=subprocess.PIPE)
        return output_name