library("xcms")
library("parallel")

args = commandArgs(trailingOnly = TRUE)

for (i in args) {
	print(i)
}

directory = args[1]

if (args[2] == "True") {
	DEBUG = TRUE
} else {
	DEBUG = FALSE
}

print(DEBUG)
setwd(directory)

c1 = detectCores()-4

ms_files = list.files(directory, pattern=".mzXML", full.names=TRUE)

step_01_set<- xcmsSet(files= ms_files, method= "centWave", nSlaves= c1, ppm= 5, peakwidth=c(10,45), snthr=10, mzdiff=-0.001, noise=5000, prefilter= c(round(length(ms_files)/10,0), 1000))
print("pass step1")
#first grouping
step_02_set<- group(step_01_set, method="density", bw=10, mzwid=0.015, max=100, minsamp = 3)
print("pass step2")
#retention time correction using loess method
#ifpass<-try(step_03_set<- retcor(step_02_set, method="loess", plottype= NULL))
ifpass<-try(step_03_set<- retcor(step_02_set, method="obiwarp", plottype = "deviation"))
print(class(ifpass))
if(length(grep("error",class(ifpass),perl=TRUE))>0){
	error_batch=c(error_batch,batch_id)
	next
}
print("pass step3")
#peak grouping post retention time correction
step_04_set<- group(step_03_set, method="density", bw=5, mzwid=0.015, max=100, minsamp = 3)
print("pass step4")
#fill missing values and create final object
xset_final<- fillPeaks(object=step_04_set, method= "chrom", nSlaves=c1)
print("get a feature table")	
#proc.time() - ptm
print("xcms processing complete")
if (DEBUG) save(xset_final, step_03_set, file = "xcms_set.RData", sep = "/")		

feature_table<- peakTable(object=xset_final)
write.csv(feature_table, file = "featuretable.csv", row.names = FALSE)