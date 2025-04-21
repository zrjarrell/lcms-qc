import json
import numpy as np
import pandas as pd
from copy import deepcopy

config = json.load(open("config.json"))

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
    result.loc[:, "type"] = target_dict["type"]
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

def find_targets(qc):
    ft = qc.ft
    targets = config[qc.method + "_targets"]
    results = pd.DataFrame()
    for target in targets:
        new_result = match_feature(ft, target)
        results = pd.concat([results, new_result], ignore_index=True)
    return results