from os.path import getctime, dirname, basename
from pandas import DataFrame

from utilities import db_labeler, check_file_sequence

def append_target(cur, target, mode, table = "intStdTargets"):
    if table == "intStdTargets":
        label = "is"
    elif table == "posCtrlTargets":
        label = "pos"
    else:
        label = "endo"
    insert_query = f"INSERT INTO {table} (id, chemical_name, mode, ref_mz, ref_time, adduct) VALUES (?, ?, ?, ?, ?, ?)"
    data_tuple = (db_labeler(label, target["num"]), target["name"], mode, target["mz"], target["time"], target["adduct"])
    cur.execute(insert_query, data_tuple)

def append_experiment(cur, experimentID, path):
    insert_query = f"INSERT INTO experiment (id, path, start_time) VALUES (?, ?, ?)"
    data_tuple = (experimentID, path, getctime(path))
    cur.execute(insert_query, data_tuple)

def append_sampleQC(cur, sampleID, experimentID, path, file_type, scans, tic):
    insert_query = f"INSERT INTO sampleQC (id, experimentID, file_name, sample_type, mode, scans, tic, create_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    data_tuple = (sampleID, experimentID, basename(path), file_type, check_file_sequence(path), scans, tic, getctime(path))
    cur.execute(insert_query, data_tuple)

def append_matches(cur, sampleID, match_table: DataFrame):
    targetID_label = match_table.columns[0]
    if targetID_label == "isTargetID":
        table = "intStdMatches"
        print(sampleID, match_table)
    elif targetID_label == "pcTargetID":
        table = "posCtrlMatches"
        print(sampleID, match_table)
    for row in match_table.index:
        print(row)
        insert_query = f"INSERT INTO {table} (sampleID, {targetID_label}, mz, time, intensity, mass_error, apex_intensity, time_error) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        data_tuple = (sampleID, match_table.loc[row, targetID_label], match_table.loc[row, "mz"], match_table.loc[row, "time"],
                      match_table.loc[row, "intensity"], match_table.loc[row, "mass_error"], match_table.loc[row, "apex_intensity"],
                      match_table.loc[row, "time_error"])
        cur.execute(insert_query, data_tuple)

def append_experimentQC(cur, experimentID, qstd_qc):
    for mode in qstd_qc:
        for qstd in qstd_qc[mode]["qc"]["sample_replicability"]:
            insert_query = f"INSERT INTO experimentQC (experimentID, qstd_num, mode, num_peaks, num_peaks_2_reps, num_peaks_3_reps, pairwiseR_1, pairwiseR_2, pairwiseR_3, featureCV_q0, featureCV_q1, featureCV_q2, featureCV_q3, featureCV_q4, eic_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            data_tuple = (experimentID, qstd, mode, qstd_qc[mode]["qc"]["peak_numbers"][qstd][0], qstd_qc[mode]["qc"]["peak_numbers"][qstd][1], qstd_qc[mode]["qc"]["peak_numbers"][qstd][2],
                          qstd_qc[mode]["qc"]["sample_replicability"][qstd][0], qstd_qc[mode]["qc"]["sample_replicability"][qstd][1], qstd_qc[mode]["qc"]["sample_replicability"][qstd][2],
                          qstd_qc[mode]["qc"]["feature_replicability"][qstd][0], qstd_qc[mode]["qc"]["feature_replicability"][qstd][1], qstd_qc[mode]["qc"]["feature_replicability"][qstd][2],
                          qstd_qc[mode]["qc"]["feature_replicability"][qstd][3], qstd_qc[mode]["qc"]["feature_replicability"][qstd][4], qstd_qc[mode]["eic_path"])
            cur.execute(insert_query, data_tuple)

def get_sample_experimentID(cur, sample_path):
    dir_path = dirname(sample_path)
    cur.execute(f"SELECT id FROM experiment WHERE path = '{dir_path}'")
    result = cur.fetchall()
    print(result)
    return result[0][0]