library(rawrr)

args = commandArgs(trailingOnly = TRUE)
path = args[1]
mass_tol = as.numeric(args[2])
rt_tol = as.numeric(args[3])
masses = as.numeric(strsplit(args[4], ";")[[1]])
times = as.numeric(strsplit(args[5], ";")[[1]])


integrate_peak = function(path, mass, time) {
    #extracting chromatogram for supplied mass and mass_tol
    chromatogram = rawrr::readChromatogram(rawfile = path, mass=mass, tol=mass_tol, type="xic")
    chromatogram = chromatogram[[1]]
    #determining lower bound of RT window
    min_time = (time - rt_tol) / 60
    #finding first index in list of times at which time is above lower bound
    start_index = 1
    if (min_time > 0) {
        while (chromatogram$time[start_index] < min_time) {
            start_index = start_index + 1
        }
    }
    #finding maximum intensity within RT window and determining unfiltered index of that intensity
    valid_ints = chromatogram$intensities[chromatogram$times > (time - rt_tol)/60 & chromatogram$times < (time + rt_tol)/60]
    peak_index = which.max(valid_ints) - 1 + start_index
    #determining time of within-range maximum intensity and filtering chromatogram to +/- 10 seconds of peak RT
    central_time = chromatogram$times[peak_index]
    times = chromatogram$times[chromatogram$times > (central_time - 10/60) & chromatogram$times < (central_time + 10/60)]
    intensities = chromatogram$intensities[chromatogram$times > (central_time - 10/60) & chromatogram$times < (central_time + 10/60)]
    chromatogram$times = times
    chromatogram$intensities = intensities
    #getting area under curve of truncated chromatogram as rough peak integration
    area = rawrr:::auc.rawrrChromatogram(chromatogram)
    return(area)
}

get_scans_tic = function(path) {
    chromatogram = rawrr::readChromatogram(path, type="tic")
    scans = length(chromatogram$times)
    tic = sum(chromatogram$intensities)
    return(c(scans, tic))
}

scans_tic = get_scans_tic(path)
target_intensities = c()
for (i in 1:length(masses)) {
    target_intensities = c(target_intensities, integrate_peak(path, masses[i], times[i]))
}

result = c(scans_tic, target_intensities)
print(result)

#python command example: result = subprocess.run("Rscript inspect_raw.R C:/Users/zjarrel/repos/lcms-qc/test-raws/F119_240709_M579_007.raw 5 30 156.0721;183.0782;166.0863 50;52;42", stdout=subprocess.PIPE)
#capturing return: result.stdout.decode('utf-8')[4:-2].split(" ")