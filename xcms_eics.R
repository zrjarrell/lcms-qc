library(xcms)

args = commandArgs(trailingOnly = TRUE)

path = args[1]
print(path)
matchesPath = paste(path, "/matches.csv", sep="")
print(matchesPath)

matches = read.csv(matchesPath)
load(paste(path, "/xcms_set.RData", sep=""))

peak_plots<- getEIC(xset_final, groupidx= matches$ft.index)

for(i in 1:nrow(matches)) {
    jpeg(paste(path, "/", as.character(i), "_", matches[i, "target.name"],".jpg", sep= ""))
    if (length(matches$ft.index)>1) {
        plot(peak_plots, groupidx = i)
    } else {
        plot(peak_plots) }
    dev.off()
}		
