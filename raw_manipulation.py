import os, json, subprocess, time
from utilities import mkdir_if_not

config = json.load(open("config.json"))

def find_raws(dirpath):
    rawfiles = []
    for dirpath, _, filenames in os.walk(dirpath):
        for file in filenames:
            name, ext = os.path.splitext(file)
            if ext == '.raw':
                rawfiles += [os.path.normpath(os.path.join(dirpath,file))]
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
    for file in rawfiles:
        convert_mzxml(file)

def convert_mzxml(filepath):
    file_dir, file_name = os.path.split(filepath)
    mkdir_if_not(file_dir + "/qc/mzxml")
    method = check_file_sequence(file_name)
    mkdir_if_not(f"{file_dir}/qc/mzxml/{method}")
    command = f'{config["msconvert_path"]} {filepath} -o {file_dir}/qc/mzxml/{method} --64 --zlib --mzXML --filter "peakPicking true 1-"'
    subprocess.run(command)

def get_runtimes(qc):
    timestamps = {}
    rawfiles = find_raws(qc.study_dir)
    for i in range(0, len(rawfiles)):
        rawfiles[i] = qc.study_dir + "/" + rawfiles[i]
    timestamps["start_file"] = min(rawfiles, key=os.path.getmtime)
    timestamps["end_file"] = max(rawfiles, key=os.path.getmtime)
    timestamps["start_time"] = time.ctime(os.path.getmtime(timestamps["start_file"]))
    timestamps["end_time"] = time.ctime(os.path.getmtime(timestamps["end_file"]))
    return timestamps