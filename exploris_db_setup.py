import sqlite3, json

from utilities import mkdir_if_not
from db_amending import append_target

def make_db_tables(con, cur):
    cur.execute("CREATE TABLE experiment(id TINYTEXT PRIMARY KEY, path TEXT NOT NULL, start_time REAL NOT NULL)")
    cur.execute("CREATE TABLE experimentQC(experimentID TINYTEXT NOT NULL, qstd_num SMALLINT NOT NULL, analytical_mode TINYTEXT NOT NULL, num_peaks MEDIUMINT NOT NULL, num_peaks_2_reps MEDIUMINT NOT NULL, num_peaks_3_reps MEDIUMINT NOT NULL, pairwiseR_1 REAL NOT NULL, pairwiseR_2 REAL NOT NULL, pairwiseR_3 REAL NOT NULL, featureCV_q0 REAL NOT NULL, featureCV_q1 REAL NOT NULL, featureCV_q2 REAL NOT NULL, featureCV_q3 REAL NOT NULL, featureCV_q4 REAL NOT NULL, eic_path TINYTEXT NOT NULL, CONSTRAINT exp_qstd_mode PRIMARY KEY (experimentID, qstd_num, mode))")
    cur.execute("CREATE TABLE sampleQC(id TINYTEXT PRIMARY KEY, experimentID TINYTEXT NOT NULL, file_name TINYTEXT NOT NULL, sample_type TINYTEXT NOT NULL, analytical_mode TINYTEXT NOT NULL, scans SMALLINT NOT NULL, tic REAL NOT NULL, create_time REAL NOT NULL)")
    cur.execute("CREATE TABLE intStdTargets(id TINYTEXT PRIMARY KEY, chemical_name TINYTEXT NOT NULL, analytical_mode TINYTEXT NOT NULL, ref_mz REAL NOT NULL, ref_time REAL NOT NULL, adduct TINYTEXT NOT NULL)")
    cur.execute("CREATE TABLE posCtrlTargets(id TINYTEXT PRIMARY KEY, chemical_name TINYTEXT NOT NULL, analytical_mode TINYTEXT NOT NULL, ref_mz REAL NOT NULL, ref_time REAL NOT NULL, adduct TINYTEXT NOT NULL)")
    cur.execute("CREATE TABLE intStdMatches(sampleID TINYTEXT NOT NULL, isTargetID TINYTEXT NOT NULL, mz REAL NOT NULL, time REAL NOT NULL, intensity REAL NOT NULL, mass_error REAL NOT NULL, apex_intensity REAL NOT NULL, time_error REAL NOT NULL, CONSTRAINT sample_target PRIMARY KEY (sampleID, isTargetID))")
    cur.execute("CREATE TABLE posCtrlMatches(sampleID TINYTEXT NOT NULL, pcTargetID TINYTEXT NOT NULL, mz REAL NOT NULL, time REAL NOT NULL, intensity REAL NOT NULL, mass_error REAL NOT NULL, apex_intensity REAL NOT NULL, time_error REAL NOT NULL, CONSTRAINT sample_target PRIMARY KEY (sampleID, pcTargetID))")
    con.commit()

def populate_targets(cur, targets, table):
    for mode in targets:
        for target in targets[mode]:
            append_target(cur, target, mode, table)
    #import targets already in config.json

config = json.load(open("config.json"))

mkdir_if_not("./db")
mkdir_if_not("./db/eics")

con = sqlite3.connect("./db/qc_results.db")
cur = con.cursor()

make_db_tables(con, cur)

populate_targets(cur, config["internalStd_targets"], "intStdTargets")
populate_targets(cur, config["positiveControl_targets"], "posCtrlTargets")
con.commit()
