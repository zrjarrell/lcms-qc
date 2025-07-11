import json, subprocess, sqlite3
import numpy as np
import pandas as pd
from copy import deepcopy
from time import time

from utilities import check_file_sequence, db_labeler
from db_amending import append_target

config = json.load(open("config.json"))

con = sqlite3.connect("./db/qc_results.db")
cur = con.cursor()

def match_feature(ft, target_dict):
    no_result = False
    mzmin = target_dict["mz"] - (config["target_matching"]["mass_error_ppm"] * target_dict["mz"] / 1e6)
    mzmax = target_dict["mz"] + (config["target_matching"]["mass_error_ppm"] * target_dict["mz"] / 1e6)
    rtmin = target_dict["time"] - config["target_matching"]["rt_error_seconds"]
    rtmax = target_dict["time"] + config["target_matching"]["rt_error_seconds"]
    result = deepcopy(ft[(ft["mz"] > mzmin) & (ft["mz"] < mzmax) & (ft["rt"] > rtmin) & (ft["rt"] < rtmax)])
    if len(result) == 0:
        na_row = {}
        no_result = True
        for col in result.columns:
            na_row[col] = np.nan
        result = pd.concat([result, pd.DataFrame([na_row])], ignore_index=True)
    result.loc[:, "target.name"] = target_dict["name"]
    if no_result:
        result.loc[:, "ft.index"] = -1
        result.loc[:, "mass.error"] = np.nan
        result.loc[:, "time.error"] = np.nan
    else:
        result.loc[:, "ft.index"] = result.index
        result.loc[:, "mass.error"] = abs((result.loc[:, "mz"] - target_dict["mz"]) / target_dict["mz"] * 1e6)
        result.loc[:, "time.error"] = abs(result.loc[:, "rt"] - target_dict["time"])
    columns = result.columns.to_list()
    columns = columns[-5:] + columns[:-5]
    result = result[columns]
    return result

def add_target_nums(targets, table):
    num = 0
    for mode in targets:
        subset = targets[mode]
        for target in subset:
            if "num" in target and target['num'] > num:
                num = target['num']
    for mode in targets:
        subset = targets[mode]
        for target in subset:
            if "num" not in target:
                num = num + 1
                target['num'] = num
                append_target(cur, target, mode, table)
    con.commit()
    return targets

def update_targets():
    global config
    if time() - config["targets_lastUpdate"] > 86400: #seeing if it has been a day since targets were updated
        print("Updating target list.")
        config["positiveControl_targets"] = add_target_nums(config["positiveControl_targets"], "posCtrlTargets")
        config["internalStd_targets"] = add_target_nums(config["internalStd_targets"], "intStdTargets")
        config["targets_lastUpdate"] = time()
        json.dump(config, open("config.json", 'w'), indent=4)
        config = json.load(open("config.json"))

def filter_targets(targets: list):
    for i in range(len(targets) - 1, -1, -1):
        if targets[i]["check"].lower() == "false":
            remove = targets.pop(i)
    return targets

def match_targets(path: str, target_set: str = "intstd"):
    update_targets()
    if target_set == "positives":
        key = 'positiveControl_targets'
        rt_error = config["qc_thresholds"]["posCtrl_rt_error_thresh"]
        id_prefix = "pos"
        id_column = "pcTargetID"
    else:
        key = 'internalStd_targets'
        rt_error = config["qc_thresholds"]["rt_error_thresh"]
        id_prefix = "is"
        id_column = "isTargetID"
    targets = config[key]
    key = check_file_sequence(path)
    targets = targets[key]
    targets = filter_targets(targets)
    masses = []
    times = []
    ids = []
    for target in targets:
        masses += [str(target['mz'])]
        times += [str(target['time'])]
        ids += [db_labeler(id_prefix, target["num"])]
    masses_str = ";".join(masses)
    times_str = ";".join(times)
    result = subprocess.run(f"Rscript inspect_raw.R {path} {config['qc_thresholds']['mass_error_thresh']} {rt_error} {masses_str} {times_str}", stdout=subprocess.PIPE)
    scans, tic, result = clean_result(result)
    labeled_result = pd.DataFrame({id_column: ids})
    labeled_result = labeled_result.join(result)
    return labeled_result, scans, tic

def clean_result(result):
    result = result.stdout.decode('utf-8')
    print(result)
    result = result.split("STARTRESULT?")[1]
    result = result.split("?ENDRESULT")[0]
    result = result.split("?")
    result_rows = []
    for i in range(0, len(result)):
        if i == 0:
            scans, tic = result[i].strip('"').split(";")
            scans = int(scans)
            tic = float(tic)
        else:
            result_rows += [result[i].strip('"').split(";")]
    result_table = pd.DataFrame(result_rows, columns=["mz", "time", "intensity", "mass_error", "apex_intensity", "time_error"])
    return scans, tic, result_table