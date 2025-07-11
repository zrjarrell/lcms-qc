library(xcms)

args = commandArgs(trailingOnly = TRUE)

path = args[1]
outputName = args[2]
print(path)
matchesPath = paste(path, "/matches.csv", sep="")
print(matchesPath)

matches = read.csv(matchesPath)
intensities = matches[,14:length(matches)]
intensities = t(intensities)
load(paste(path, "/xcms_set.RData", sep=""))

peak_plots<- getEIC(xset_final, groupidx= matches$ft.index)

# for(i in 1:nrow(matches)) {
#     jpeg(paste(path, "/", as.character(i), "_", matches[i, "target.name"],"_eic.jpg", sep= ""))
#     plot(peak_plots, groupidx = i)
#     dev.off()
#     jpeg(paste(path, "/", as.character(i), "_", matches[i, "target.name"],"_intensities.jpg", sep= ""))
#     barplot(intensities[,i], main="Intensity by sample")
#     dev.off()
# }		

pdf(file = outputName)
for(i in 1:nrow(matches)) {
    plot(peak_plots, groupidx = i, col = c("#fd5901", "#f78104", "#faab36", "#249ea0", "#008083", "#005f60"), legtext = matches[i, "target.name"])
}

dev.off()