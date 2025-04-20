import pandas as pd
from statistics import median, mean

from mzxml_manipulation import get_machine_info as get_mi
from mzxml_manipulation import get_scan_stats as get_ss
from raw_manipulation import get_runtimes as get_times
from feature_matching import find_targets
from replicate_inspection import check_replicability
from build_eics import build_eics

class QCResult:
    def __init__(self, method, study_dir, ft_path, mzxml_dir):
        self.method = method
        self.study_dir = study_dir
        self.ft_path = ft_path
        self.mzxml_dir = mzxml_dir
    
    def print_stats(self):
        for attr in self.__dict__:
            if attr in ("method", "ft_path", "ft", "mzxml_dir"):
                pass
            else:
                print(f"{attr}:\t{str(self.__dict__[attr])}")
    
    def get_ft(self):
        self.ft = pd.read_csv(self.ft_path)

    def count_peaks(self):
        ft = self.ft
        self.num_samples = len(ft.columns) - 8
        self.peaks = {}
        self.peaks["num"] = len(ft.index)

        nonzero = 0
        present90per = 0
        present50per = 0

        for row in ft.index:
            nz = 0
            for col in ft.iloc[:, 8:]:
                if ft.loc[row, col] > 0:
                    nz += 1
            if nz == self.num_samples:
                nonzero += 1
            if nz / self.num_samples > 0.9:
                present90per += 1
            if nz / self.num_samples > 0.5:
                present50per += 1
        
        self.peaks["nonzero"] = nonzero
        self.peaks["present90per"] = present90per
        self.peaks["present50per"] = present50per

    def get_meanmedianint(self):
        ft = self.ft
        medians = []
        for col in ft.iloc[:, 8:]:
            medians += [median(ft[col])]
        self.mean_median_intensity = mean(medians)
    
    def get_machine_info(self):
        self.machine_info = get_mi(self)
    
    def get_scan_stats(self):
        self.scan_stats = get_ss(self)

    def get_runtimes(self):
        self.runtimes = get_times(self)
    
    def get_targets(self):
        self.target_matches = find_targets(self)
        self.target_stats = {}
        observed_matches = self.target_matches[self.target_matches["ft.index"] >= 0]
        self.target_stats["targets_matched"] = len(set(observed_matches["target.name"]))
        self.target_stats["num_matches"] = len(observed_matches)
        self.target_stats["duplicate_matches"] = self.target_stats["num_matches"] - self.target_stats["targets_matched"]
        self.target_stats["min_mass_error"] = min(observed_matches["mass.error"])
        self.target_stats["mean_mass_error"] = mean(observed_matches["mass.error"])
        self.target_stats["max_mass_error"] = max(observed_matches["mass.error"])
        self.target_stats["min_rt_error"] = min(observed_matches["time.error"])
        self.target_stats["mean_rt_error"] = mean(observed_matches["time.error"])
        self.target_stats["max_rt_error"] = max(observed_matches["time.error"])
    
    def get_replicability(self):
        self.replicability = check_replicability(self)

    def get_eics(self):
        build_eics(self)