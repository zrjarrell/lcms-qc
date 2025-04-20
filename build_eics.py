import subprocess
from copy import deepcopy

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

