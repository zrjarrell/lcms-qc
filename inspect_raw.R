library(rawrr)

args = commandArgs(trailingOnly = TRUE)
path = args[1]
mass_tol = as.numeric(args[2])
rt_tol = as.numeric(args[3])
masses = as.numeric(strsplit(args[4], ";")[[1]])
times = as.numeric(strsplit(args[5], ";")[[1]])


integrate_peak = function(path, mass, time) {
    #extracting chromatogram for supplied mass and mass_tol
    chromatogram = rawrr::readChromatogram(rawfile = path, mass=mass, tol=mass_tol, type="xic", filter="ms")
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
    #handles potential leftward bias introduced by peak_index defaulting to start_index when
    #intensity of whole range is 0
    if (peak_index == start_index & chromatogram$intensities[peak_index] == 0) {
        peak_time = chromatogram$times[peak_index]
        if (peak_time < (290/60)) {
            adjusted_peak_index = peak_index
            while (chromatogram$times[adjusted_peak_index] < peak_time + 10/60) {
                adjusted_peak_index = adjusted_peak_index + 1
            }
            peak_index = adjusted_peak_index
        }
    }
    #determining time of within-range maximum intensity and filtering chromatogram to +/- 10 seconds of peak RT
    central_time = chromatogram$times[peak_index]
    reduced_times = chromatogram$times[chromatogram$times > (central_time - 10/60) & chromatogram$times < (central_time + 10/60)]
    intensities = chromatogram$intensities[chromatogram$times > (central_time - 10/60) & chromatogram$times < (central_time + 10/60)]
    chromatogram$times = reduced_times
    chromatogram$intensities = intensities
    #getting area under curve of truncated chromatogram as rough peak integration
    area = auc(chromatogram$times, chromatogram$intensities) * 60
    #was using peak_index to pass to "get_mass_error_match" as scan arg...trying this to fix issue
    #with chromatogram index not aligning with file's actual scan index
    scan_index = readIndex(path)
    scan = scan_index[scan_index$StartTime == central_time & scan_index$MSOrder == "Ms",]$scan
    if (area == 0) {
        mass_stats = c("NA", "NA", 0)
        time_stats = c("NA", "NA")
    } else {
        mass_stats = get_mass_error_match(path, scan, mass)
        time_stats = c(central_time * 60, central_time * 60 - time)
    }
    peak_stats = paste(c(mass_stats[1], time_stats[1], area, mass_stats[2], mass_stats[3], time_stats[2]), collapse=";")
    #columns are: "mz", "time", "intensity", "mass_error", "apex_intensity", "time_error"
    return(peak_stats)
}

get_mass_error_match = function(path, scan, mass) {
    spectrum = rawrr::readSpectrum(path, scan)[[1]]
    indices = c()
    for (i in 1:length(spectrum$mZ)) {
        if (spectrum$mZ[i] > mass - (mass * mass_tol / 1e6) & spectrum$mZ[i] < mass + (mass * mass_tol / 1e6)) {
            indices = c(indices, i)
        }
    }
    max_index = indices[1]
    for (i in 1:length(indices)) {
        if (spectrum$intensity[indices[i]] > spectrum$intensity[max_index]) {
            max_index = indices[i]
        }
    }
    mass_error = (spectrum$mZ[max_index] - mass) / mass * 1e6
    apex_intensity = spectrum$intensity[max_index]
    return(c(spectrum$mZ[max_index], mass_error, apex_intensity))
}

get_scans_tic = function(path) {
    chromatogram = rawrr::readChromatogram(path, type="tic")
    scans = length(chromatogram$times)
    chromatogram$times = as.numeric(chromatogram$times)
    tic = auc(chromatogram$times, chromatogram$intensities) * 60
    result = paste(c(scans, tic), collapse=";")
    #columns are: "scans", "tic"
    return(result)
}

#auc() copied from https://github.com/ekstroem/MESS/blob/master/R/auc.R on July 4, 2025
auc <- function(x, y, from = min(x, na.rm=TRUE), to = max(x, na.rm=TRUE), type=c("linear", "spline"), absolutearea=FALSE, subdivisions =100, ...) {
    type <- match.arg(type)

    # Sanity checks
    stopifnot(length(x) == length(y))
    stopifnot(!is.na(from))

    if (length(unique(x)) < 2)
        return(NA)

    if (type=="linear") {

        ## Default option
        if (absolutearea==FALSE) {
            values <- approx(x, y, xout = sort(unique(c(from, to, x[x > from & x < to]))), ...)
            res <- 0.5 * sum(diff(values$x) * (values$y[-1] + values$y[-length(values$y)]))
        } else { ## Absolute areas
            ## This is done by adding artificial dummy points on the x axis
            o <- order(x)
            ox <- x[o]
            oy <- y[o]

            idx <- which(diff(oy >= 0)!=0)
            newx <- c(x, x[idx] - oy[idx]*(x[idx+1]-x[idx]) / (y[idx+1]-y[idx]))
            newy <- c(y, rep(0, length(idx)))
            values <- approx(newx, newy, xout = sort(unique(c(from, to, newx[newx > from & newx < to]))), ...)
            res <- 0.5 * sum(diff(values$x) * (abs(values$y[-1]) + abs(values$y[-length(values$y)])))
        }
        
    } else { ## If it is not a linear approximation
        if (absolutearea)
            myfunction <- function(z) { abs(splinefun(x, y, method="natural")(z)) }
        else
            myfunction <- splinefun(x, y, method="natural")


        res <- integrate(myfunction, lower=from, upper=to, subdivisions=subdivisions)$value
    }

    res
}

scans_tic = get_scans_tic(path)
target_intensities = c()
for (i in 1:length(masses)) {
    target_intensities = c(target_intensities, integrate_peak(path, masses[i], times[i]))
}

result = c("STARTRESULT", scans_tic, target_intensities, "ENDRESULT")
result = paste(result, collapse="?")
print(result)

#python command example: result = subprocess.run("Rscript inspect_raw.R C:/Users/zjarrel/repos/lcms-qc/test-raws/F119_240709_M579_007.raw 5 30 156.0721;183.0782;166.0863 50;52;42", stdout=subprocess.PIPE)
#capturing return: result.stdout.decode('utf-8')[4:-2].split(" ")

# plotChrom = function(path, mass) {
#     plot(rawrr::readChromatogram(path, mass, tol=10, type="xic"))
# }