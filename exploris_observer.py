import json, time, os, sqlite3
import tkinter as tk
from tkinter import messagebox
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from file_processing import process_file, new_experiment_to_db

## sequence of events for exploris IndiPharm workflow
## Handling of sequence, queue and watchdog operations here. Interactions with files 
## are defined elsewhere.




####################SETUP###############

#detect path: D:/IndiPharm/
config = json.load(open("config.json"))
watch_directory = config["watch_directory"]

#this plate log will be used to maintain list of directories for watchdog to filter
#and to maintain an updated RAW file queue
plate_log_path = "./plate_log.json"

#setup DB connection
con = sqlite3.connect("./db/qc_results.db")
cur = con.cursor()




####################NEW DIR LOGIC####################

#updates plate_log.json to check for any new directories created during program downtime
#either skips because already in old or new list, or prompts user whether to add to new
#directories list, yes: adds to 'new_directories', no: adds to 'ignore_directories'
def check_directories_on_start():
    plate_log = json.load(open(plate_log_path))
    directories = next(os.walk(watch_directory))[1]
    #loop through list of dirs in watch_directory
    for directory in directories:
        directory = os.path.normpath(os.path.join(watch_directory,directory))
        if directory in plate_log["directories_analyzed"] or directory in plate_log["ignore_directories"]:
            pass
        elif directory in plate_log["new_directories"]:
            pass
        else:
            #if not already in 'directories_analyzed', 'ignore_directories' or 'new_directories'
            #prompt user for decision with check_new_dir() to determine if new or ignore
            result = check_new_dir(os.path.abspath(directory))
            if result:
                #if user selects to add to new, experiment added to db 'experiment' table
                #and assigned an experimentID
                plate_log["new_directories"] += [os.path.abspath(directory)]
                new_experiment_to_db(os.path.abspath(directory))
            else:
                plate_log["ignore_directories"] += [os.path.abspath(directory)]
    #update plate_log
    json.dump(plate_log, open(plate_log_path, 'w'), indent=4)

#called by check_raw_queue() once last sample of experiment sequence is analyzed
#moves dir from 'new_directories' to 'directories_analyzed'
def clear_dir_from_watch(plate_log, dir_path):
    watchlist = plate_log["new_directories"]
    for i in range(len(watchlist)-1, -1, -1):
        if dir_path == watchlist[i]:
            plate_log["directories_analyzed"] += [watchlist.pop(i)]
    plate_log["new_directories"] = watchlist
    return plate_log

#called by check_directories_on_start(); creates popup dialog to determine if user wants
#newly detected directory to be added to 'new_directories' list
def check_new_dir(dir_path):
    response = True
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes('-topmost', True)
    notice = f"New subdirectory detected data directory:\n{dir_path}\n\nAdd to observer queue?"
    response = messagebox.askyesno("New Directory Detection", notice, parent=root)
    root.after(5000, root.destroy)
    return response




####################NEW RAW LOGIC####################

#updates plate_log.json to check for any new raw files created during program downtime
#calls get_sorted_raws() for each directory in 'new_directories' to get a sorted, filtered
#list of raw files that have not been processed already for QC and adds to 'raw_queue'
def check_raws_on_start():
    plate_log = json.load(open(plate_log_path))
    for directory in plate_log["new_directories"]:
        sorted_raws = get_sorted_raws(directory)
        plate_log["raw_queue"] += sorted_raws
    json.dump(plate_log, open(plate_log_path, 'w'), indent=4)

#called by check_raws_on_start(); for directory provided, gets raw files, places them in queue order
#and removes any that already have QCs in the database
def get_sorted_raws(dir):
    #get files in dir, filter to only .raws, sort by creation time and then reverse so that
    #oldest are at the bottom of the list
    files = os.listdir(dir)
    files = [file for file in files if file[-4:] == ".raw"]
    files = [os.path.join(dir, file) for file in files]
    files.sort(key=os.path.getctime)
    files.reverse()
    #get 'experimentID' for the directory. if there are none, full file list is returned as none need removal
    #at moment, this case shouldn't happen, as experiment paths are added to 'experiment' table just before
    #this function is called
    result = cur.execute(f"SELECT id FROM experiment WHERE path = '{dir}'").fetchall()
    if len(result) == 0:
        return files
    else:
        #gets id, searches sampleQC for any file_names tied to that experimentID. If there are any, that file
        #has already been processed, so it is removed from the 'files' list. Remaining files in list are added to 'raw_queue'
        experimentID = result[0][0]
        result = cur.execute(f"SELECT file_name FROM sampleQC WHERE experimentID = '{experimentID}'").fetchall()
        already_run = [item[0] for item in result]
        final_list = []
        for file in files:
            if os.path.basename(file) not in already_run:
                final_list += [file]
        return final_list

#major logic of the watchdog loop. checks the raw file at end of raw_queue (front of line due to reversed stacking)
#of plate_log, and for any raw file created more than 10 minutes ago (~5 min after run finishes), it calls process_file()
#on the file. The rest updates the raw_queue and directories list in response to file being processed for QC
def check_raw_queue():
    plate_log = json.load(open(plate_log_path))
    if len(plate_log["raw_queue"]) > 0:
        #grabbing end of queue (front of line)
        file = plate_log["raw_queue"][-1]
        time_since_create = time.time() - os.path.getctime(file)
        delta_modified_created = os.path.getmtime(file) - os.path.getctime(file) #modified time not currently used
        #if file older than 10 minutes, process file for QC
        if time_since_create > (10 * 60):
            print("Processing file: " + file)
            process_file(file)
            #removing processed file from queue
            plate_log["raw_queue"] = plate_log["raw_queue"][:-1]
            print(f"Processing of {file} complete.")
            #trying to deal with issue of plate_log.json getting written to by new_raw_handler and then being overwritten by check_raw_queue's update
            #checks what was last written to plate_log.json, grabs that queue, and for anything in this functions' queue (after removal of one just processed)
            #that is not already in the newly read queue, it gets added to end. Then the merged list is saved.
            new_raw_queue = json.load(open(plate_log_path))["raw_queue"][:-1]
            for raw in plate_log["raw_queue"]:
                if raw not in new_raw_queue:
                    new_raw_queue += [raw]
            plate_log["raw_queue"] = new_raw_queue
            plate_log["new_directories"] = json.load(open(plate_log_path))["new_directories"]
            json.dump(plate_log, open(plate_log_path, 'w'), indent=4)
        #if file is the last in sequence, run clear_dir_from_watch() to update directory lists
        if os.path.basename(file)[0:6] == "blank4" and os.path.basename(file)[-5:] == "2.raw":
            plate_log = clear_dir_from_watch(plate_log, os.path.dirname(file))
            json.dump(plate_log, open(plate_log_path, 'w'), indent=4)




####################WATCHDOG SETUP####################

#parent watchdog observer class
#orchestrates file system event handlers on a 20 second interval
class Watcher:
    def __init__(self):
        self.observer = Observer()

    def run(self):
        self.observer.schedule(New_Dir_Handler(), watch_directory, recursive=False)
        self.observer.schedule(New_Raw_Handler(), watch_directory, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(20)
                print("20 second interval passed.")
                check_raw_queue()
        except Exception as error:
            self.observer.stop()
            print("Observer stopped. Error: ", error)
        
        self.observer.join()

#detects new directory creation
#adds new directories to plate_log:new_directories
#creates "qc" subdirectory if not already there
class New_Dir_Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            plate_log = json.load(open(plate_log_path))
            result = check_new_dir(os.path.abspath(event.src_path))
            if result:
                plate_log["new_directories"] = [os.path.abspath(event.src_path)] + plate_log["new_directories"]
                new_experiment_to_db(os.path.abspath(event.src_path))
                print(f"New directory watched: {os.path.abspath(event.src_path)}")
            else:
                plate_log["ignore_directories"] += [os.path.abspath(event.src_path)]
                print(f"New directory ignored: {os.path.abspath(event.src_path)}")
            json.dump(plate_log, open(plate_log_path, 'w'), indent=4)

#detects new raw files, adds to plate_log:raw_queue
class New_Raw_Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            pass
        else:
            print("New file detected.")
            file_dir, file_name = os.path.split(os.path.abspath(event.src_path))
            plate_log = json.load(open(plate_log_path))
            if file_dir in plate_log["new_directories"] and file_name[-4:] == ".raw":
                print(f"New raw detected: {os.path.abspath(event.src_path)}")
                plate_log["raw_queue"] = [os.path.abspath(event.src_path)] + plate_log["raw_queue"]
                json.dump(plate_log, open(plate_log_path, 'w'), indent=4)

if __name__ == "__main__":
    check_directories_on_start()
    check_raws_on_start()
    watch = Watcher()
    watch.run()