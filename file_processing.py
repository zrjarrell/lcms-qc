import sqlite3, subprocess
import pandas as pd
from os.path import basename, dirname
from os import listdir
from shutil import rmtree

from raw_manipulation import convert_mzxml
from target_matching import match_targets
from replicate_inspection import check_qstd_replicability
from build_eics import build_eics_qstd
from utilities import db_labeler, get_next_id
from db_amending import append_experiment, get_sample_experimentID, append_sampleQC, append_matches, append_experimentQC

con = sqlite3.connect("./db/qc_results.db", check_same_thread=False)
cur = con.cursor()

def new_experiment_to_db(path: str):
    next_id_num = get_next_id(cur, 'experiment')
    experimentID = db_labeler("exp", next_id_num)
    append_experiment(cur, experimentID, path)
    con.commit()

def process_file(path: str):
    file_type = determine_type(path)
    print(file_type)
    sampleID, experimentID = process_sample(path, file_type)
    if file_type == "qstd":
        convert_mzxml(path)
    elif file_type == "positive":
        process_positive(path, sampleID)
    if basename(path) == "qstd_12.raw":
        qstd_qc = process_qstds(dirname(path), experimentID)
        append_experimentQC(cur, experimentID, qstd_qc)
        try:
            rmtree(dirname(path) + "/qc")
        except:
            pass
    con.commit()

def process_qstds(experiment_dirname, experimentID):
    feature_tables = xcms_extract_qstds(experiment_dirname)
    for mode in feature_tables:
        ft = pd.read_csv(feature_tables[mode]["path"])
        feature_tables[mode]["qc"] = check_qstd_replicability(ft, mode)
        print(feature_tables)
        feature_tables[mode]["eic_path"] = build_eics_qstd(experimentID, ft, feature_tables[mode]["path"], mode)
    return feature_tables

def xcms_extract_qstds(experiment_dirname):
    methods = listdir(experiment_dirname + "/qc/mzxml")
    feature_tables = {}
    for method in methods:
        qstds_path = experiment_dirname + "/qc/mzxml/" + method
        command = f"Rscript xcms_runscript.R {qstds_path} True"
        subprocess.run(command, stdout=subprocess.PIPE)
        feature_tables[method] = {}
        feature_tables[method]["path"] = qstds_path + "/featuretable.csv"
    return feature_tables

def process_sample(path: str, file_type):
    match_table, scans, tic = match_targets(path)
    print("made it 1")
    next_id_num = get_next_id(cur, 'sampleQC')
    print("made it 2")
    sampleID = db_labeler("samp", next_id_num)
    print("made it 3")
    experimentID = get_sample_experimentID(cur, path)
    print("made it 4")
    append_sampleQC(cur, sampleID, experimentID, path, file_type, scans, tic)
    print("made it 5")
    append_matches(cur, sampleID, match_table)
    print("made it 6")
    con.commit()
    return sampleID, experimentID

def process_positive(path: str, sampleID: str):
    match_table, _scans, _tic = match_targets(path, "positives")
    append_matches(cur, sampleID, match_table)
    con.commit()

def determine_type(path: str):
    file_name = basename(path)
    if file_name[0:4] == "qstd":
        return "qstd"
    elif file_name[0:8] == "positive":
        return "positive"
    else:
        return "sample"