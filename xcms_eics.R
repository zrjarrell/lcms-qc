library(xcms)

args = commandArgs(trailingOnly = TRUE)

path = args[1]
print(path)
matchesPath = paste(path, "/matches.csv", sep="")
print(matchesPath)

matches = read.csv(matchesPath)
intensities = matches[,14:length(matches)]
intensities = t(intensities)
load(paste(path, "/xcms_set.RData", sep=""))

peak_plots<- getEIC(xset_final, groupidx= matches$ft.index)

for(i in 1:nrow(matches)) {
    jpeg(paste(path, "/", as.character(i), "_", matches[i, "target.name"],"_eic.jpg", sep= ""))
    plot(peak_plots, groupidx = i)
    dev.off()
    jpeg(paste(path, "/", as.character(i), "_", matches[i, "target.name"],"_intensities.jpg", sep= ""))
    barplot(intensities[,i], main="Intensity by sample")
    dev.off()
}		
