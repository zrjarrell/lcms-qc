import json
import numpy as np
import pandas as pd
from statistics import mean, median
from copy import deepcopy

config = json.load(open("config.json"))

def separate_replicates(qc, num_reps, analyses = None):
    if analyses == None:
        analyses = qc.ft.columns[8:].to_list()
    if len(analyses) % num_reps != 0:
        print("Incorrect number of analyses present.")
        return
    replicates = []
    for i in range(0, int(len(analyses)/num_reps)):
        rep_set = []
        for j in range(0, num_reps):
            rep_set += [analyses[j + i*num_reps]]
        replicates += [rep_set]
    return replicates

def impute_missing(df):
    df = df.replace(0, np.nan)
    nz_means = df.mean(axis=1)
    for col in df.columns:
        df[col] = df[col].fillna(nz_means)
    return df

#get mean median technical replicate CV
def evaluate_replicate_cv(ft, replicates, min_pres = 0.6):
    feature_cvs = pd.DataFrame(data={"good_samples": len(ft) * [0]})
    for rep_set in replicates:
        rep_ints = deepcopy(ft[rep_set])
        reps = deepcopy(rep_ints)
        reps.loc[:, "percent_pres"] = rep_ints.astype(bool).sum(axis=1) / len(rep_ints.columns)
        rep_ints = impute_missing(rep_ints)
        reps.loc[:, "cv"] = rep_ints.std(axis=1) / rep_ints.mean(axis=1)
        reps.loc[:, "good_sample"] = reps["percent_pres"] > min_pres
        reps["cv"] = np.where(reps["good_sample"] == False, np.nan, reps["cv"])
        feature_cvs.loc[:, rep_set[0]] = reps["cv"]
        feature_cvs["good_samples"] = feature_cvs["good_samples"] + reps["good_sample"]
    feature_cvs.loc[:, "median_cv"] = feature_cvs.iloc[:, 1:].median(axis=1)
    feature_cvs.loc[:, "qrscore"] = (feature_cvs["good_samples"] / len(replicates)) / feature_cvs["median_cv"]
    feature_stats = {}
    feature_stats["min_median_cv"] = min(feature_cvs["median_cv"])
    feature_stats["median_median_cv"] = median(feature_cvs["median_cv"])
    feature_stats["mean_median_cv"] = mean(feature_cvs["median_cv"])
    feature_stats["max_median_cv"] = max(feature_cvs["median_cv"])
    feature_stats["min_median_qrscore"] = min(feature_cvs["qrscore"])
    feature_stats["median_median_qrscore"] = median(feature_cvs["qrscore"])
    feature_stats["mean_median_qrscore"] = mean(feature_cvs["qrscore"])
    feature_stats["max_median_qrscore"] = max(feature_cvs["qrscore"])
    return feature_stats

#get mean mean technical replicate Pearson coefficient
#get min, median, mean & max
def evaluate_replicate_correlation(ft, replicates):
    mean_corrs = []
    for rep_set in replicates:
        correlations = []
        rep_ints = deepcopy(ft[rep_set])
        rep_ints = rep_ints.replace(0, np.nan)
        corr_matrix = rep_ints.corr(method="pearson")
        for row in range(1, len(rep_set)):
            for col in range(0, row):
                correlations += [corr_matrix.iloc[row, col]]
        mean_corrs += [float(mean(correlations))]
    sample_stats = {}
    sample_stats["min_mean_correlation"] = min(mean_corrs)
    sample_stats["median_mean_correlation"] = median(mean_corrs)
    sample_stats["mean_mean_correlation"] = mean(mean_corrs)
    sample_stats["max_mean_correlation"] = max(mean_corrs)
    return sample_stats

def check_replicability(qc, analyses = None):
    replicate_stats = {}
    num_reps = config["num_replicates"]
    if num_reps == 1:
        return {
            "feature-wise": {"min_median_cv": None, "median_median_cv": None, "mean_median_cv": None, "max_median_cv": None,
                             "min_median_qrscore": None, "median_median_qrscore": None, "mean_median_qrscore": None, "max_median_qrscore": None},
            "sample-wise": {"min_mean_correlation": None, "median_mean_correlation": None, "mean_mean_correlation": None, "max_mean_correlation": None}
        }
    else:
        replicates = separate_replicates(qc, num_reps, analyses)
        replicate_stats["feature-wise"] = evaluate_replicate_cv(qc.ft, replicates)
        replicate_stats["sample-wise"] = evaluate_replicate_correlation(qc.ft, replicates)
        return replicate_stats


####below are for qstd only for IndiPharm

def check_qstd_replicability(ft, mode):
    replicate_stats = {}
    qstd_nums = [1, 3, 5, 7, 9, 11]
    if mode == "c18neg":
        qstd_nums = [num + 1 for num in qstd_nums]
    qstd_names = [f"qstd_{num}" for num in qstd_nums]
    ft = ft[qstd_names]
    replicates = [qstd_names[0:3], qstd_names[3:7]]
    replicate_stats["sample_replicability"] = evaluate_qstd_correlation(ft, replicates)
    replicate_stats["feature_replicability"] = evaluate_qstd_cvs(ft, replicates)
    replicate_stats["peak_numbers"] = check_qstd_peak_num(ft, replicates)
    return replicate_stats

def check_qstd_peak_num(ft, replicates):
    detects = {}
    counter = 1
    for rep_set in replicates:
        rep_ints = deepcopy(ft[rep_set])
        above_zero = rep_ints.iloc[:, 0:3] > 0
        count = []
        for row in above_zero.index:
            count += [sum(above_zero.loc[row, :])]
        num_peaks = len([x for x in count if x > 0])
        num_peaks_2_reps = len([x for x in count if x > 1])
        num_peaks_3_reps = len([x for x in count if x > 2])
        detects[str(counter)] = [num_peaks, num_peaks_2_reps, num_peaks_3_reps]
        counter += 1
    return detects


def evaluate_qstd_correlation(ft, replicates):
    correlations = {}
    counter = 1
    for rep_set in replicates:
        correlation_set = []
        rep_ints = deepcopy(ft[rep_set])
        rep_ints = rep_ints.replace(0, np.nan)
        corr_matrix = rep_ints.corr(method="pearson")
        for row in range(1, len(rep_set)):
            for col in range(0, row):
                correlation_set += [float(corr_matrix.iloc[row, col])]
        correlations[str(counter)] = correlation_set
        #order of pairwise comparisons is 0) A_vs_B, 1) A_vs_C, & 2) B_vs_C
        counter += 1
    return correlations

def evaluate_qstd_cvs(ft, replicates, min_pres = 0.6):
    feature_cvs = pd.DataFrame(data={"good_samples": len(ft) * [0]})
    for rep_set in replicates:
        rep_ints = deepcopy(ft[rep_set])
        reps = deepcopy(rep_ints)
        #calculating percent of triplicate with measured intensity
        reps.loc[:, "percent_pres"] = rep_ints.astype(bool).sum(axis=1) / len(rep_ints.columns)
        #if missing value, replaced with mean
        rep_ints = impute_missing(rep_ints)
        #calculate cv for rep
        reps.loc[:, "cv"] = rep_ints.std(axis=1) / rep_ints.mean(axis=1)
        #determines if sample was 'good'
        reps.loc[:, "good_sample"] = reps["percent_pres"] > min_pres
        #if not a good sample, sets cv to 'NA'
        reps["cv"] = np.where(reps["good_sample"] == False, np.nan, reps["cv"])
        feature_cvs.loc[:, rep_set[0]] = reps["cv"]
        feature_cvs["good_samples"] = feature_cvs["good_samples"] + reps["good_sample"]
    cvs = {}
    for counter in range(1, 3):
        quantiles = feature_cvs.iloc[:, counter].quantile([0, 0.25, 0.5, 0.75, 1])
        quantiles = [float(quantile) for quantile in quantiles]
        cvs[str(counter)] = quantiles
    return cvs