import sqlite3, shutil
import pandas as pd

download_path = "C:\\Users\\Thermo\\Desktop\\QC Reports" #use absolute path

con = sqlite3.connect("./db/qc_results.db", check_same_thread=False)
cur = con.cursor()

experiments = pd.read_sql_query("SELECT id, path FROM experiment", con)
print("\nExperiment ID\tPath")
for i in experiments.index:
    print(f"{experiments.loc[i, 'id']}\t{experiments.loc[i, 'path']}")

experimentID = input("\nPlease copy the experiment ID you want and paste here: ")

results = {}

results["sampleQC"] = pd.read_sql_query(f"SELECT * FROM sampleQC WHERE experimentID = '{experimentID}'", con)
results["experimentQC"] = pd.read_sql_query(f"SELECT * FROM experimentQC WHERE experimentID = '{experimentID}'", con)
results["intStdTargets"] = pd.read_sql_query(f"SELECT * FROM intStdTargets JOIN intStdMatches ON intStdTargets.id = intStdMatches.isTargetID JOIN sampleQC ON intStdMatches.sampleID = sampleQC.id WHERE sampleQC.experimentID = '{experimentID}'", con)
results["posCtrlTargets"] = pd.read_sql_query(f"SELECT * FROM posCtrlTargets JOIN posCtrlMatches ON posCtrlTargets.id = posCtrlMatches.pcTargetID JOIN sampleQC ON posCtrlMatches.sampleID = sampleQC.id WHERE sampleQC.experimentID = '{experimentID}'", con)

report_path = f"{download_path}/{experimentID}_qc-report.xlsx"
with pd.ExcelWriter(report_path) as writer:
    results["experimentQC"].to_excel(writer, sheet_name="experiment_qc")
    results["sampleQC"].to_excel(writer, sheet_name="sample_qc")
    results["intStdTargets"].to_excel(writer, sheet_name="int-std_matches")
    results["posCtrlTargets"].to_excel(writer, sheet_name="pos-ctrl_matches")

print(f"\nQC Report saved to {report_path}.")

eic_files = list(results["experimentQC"].eic_path.unique())

for file in eic_files:
    if file == 'NA':
        print("No EIC found.")
    else:
        print(f"EIC file, {file}, copied to {download_path}")
        shutil.copy(file, download_path)