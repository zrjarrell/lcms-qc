import os, json, subprocess, time
from utilities import mkdir_if_not

config = json.load(open("config.json"))

def find_raws(dirpath):
    dirFiles = os.listdir(dirpath)
    rawfiles = []
    for file in dirFiles:
        name, ext = os.path.splitext(file)
        if ext == '.raw':
           rawfiles += [file]
    return rawfiles

def check_file_sequence(filename):
    try:
        file_num = int(filename[-5])
        if file_num % 2 == 1:
            return "hilicpos"
        else:
            return "c18neg"
    except:
        return "error"

def convert_mzxmls(dirpath):
    rawfiles = find_raws(dirpath)
    prev_dir = os.getcwd()
    os.chdir(dirpath)
    mkdir_if_not(dirpath + "/qc/mzxml")
    error_files = []
    for file in rawfiles:
        method = check_file_sequence(file)
        if method == "error":
            error_files += [file]
        else:
            mkdir_if_not(f"{dirpath}/qc/mzxml/{method}")
            command = f'{config["msconvert_path"]} {file} -o ./qc/mzxml/{method} --64 --zlib --mzXML --filter "peakPicking true 1-"'
            subprocess.run(command)
    os.chdir(prev_dir)
    return error_files

def get_runtimes(qc):
    timestamps = {}
    rawfiles = find_raws(qc.raw_dir)
    for i in range(0, len(rawfiles)):
        rawfiles[i] = qc.raw_dir + "/" + rawfiles[i]
    timestamps["start_file"] = min(rawfiles, key=os.path.getmtime)
    timestamps["end_file"] = max(rawfiles, key=os.path.getmtime)
    timestamps["start_time"] = time.ctime(os.path.getmtime(timestamps["start_file"]))
    timestamps["end_time"] = time.ctime(os.path.getmtime(timestamps["end_file"]))
    return timestamps