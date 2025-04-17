import os, json
import xml.etree.ElementTree as ET
from numpy.random import permutation
from statistics import mean, median

config = json.load(open("config.json"))

def find_mzxmls(mzxml_dir):
    files = os.listdir(mzxml_dir)
    mzxmls = []
    for file in files:
        if file[-6:] == ".mzXML":
            mzxmls += [file]
    return mzxmls

def get_machine_info(qc):
    mzxmls = find_mzxmls(qc.mzxml_dir)
    info_dict = {
        "msModel": "",
        "msIonisation": "",
        "msMassAnalyzer": "",
        "msDetector": ""
    }
    file = mzxmls[0]
    tree = ET.parse(f"{qc.mzxml_dir}/{file}")
    root = tree.getroot()
    prefix = root.findall("./")[0].tag.split("}")[0] + "}"
    for key in info_dict:
        info_dict[key] = root.find(f"./{prefix}msRun/{prefix}msInstrument/{prefix}{key}").attrib["value"]
    return info_dict

def get_scan_counts(mzxml_path):
    tree = ET.parse(mzxml_path)
    root = tree.getroot()
    prefix = root.findall("./")[0].tag.split("}")[0] + "}"
    msrun = root.find(f"{prefix}msRun")
    scan_count = int(msrun.attrib["scanCount"])
    return scan_count

def get_scan_stats(qc):
    mzxmls = find_mzxmls(qc.mzxml_dir)
    if len(mzxmls) > config["mzxml_sampling_num"]:
        samples = permutation(mzxmls)[:config["mzxml_sampling_num"]]
        mzxmls = samples
    scan_counts = []
    for file in mzxmls:
        scan_counts += [get_scan_counts(f"{qc.mzxml_dir}/{file}")]
    scan_stats = {}
    scan_stats["min"] = min(scan_counts)
    scan_stats["max"] = max(scan_counts)
    scan_stats["mean"] = mean(scan_counts)
    scan_stats["median"] = median(scan_counts)
    return scan_stats