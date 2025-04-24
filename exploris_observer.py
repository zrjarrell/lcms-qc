import json, time, os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from utilities import mkdir_if_not
from raw_manipulation import convert_mzxml

## sequence of events for exploris IndiPharm workflow

#detect path: D:/IndiPharm/
config = json.load(open("config.json"))
watch_directory = config["watch_directory"]

plate_log_path = "./plate_log.json"

def check_directories_on_start():
    plate_log = json.load(open(plate_log_path))
    directories = next(os.walk(watch_directory))[1]
    for directory in directories:
        directory = os.path.abspath(directory)
        if directory in plate_log["directories_analyzed"]:
            pass
        elif directory in plate_log["new_directories"]:
            pass
        else:
            plate_log["new_directories"] += [os.path.abspath(directory)]
    json.dump(plate_log, open(plate_log_path, 'w'), indent=4)

def check_raw_queue():
    plate_log = json.load(open(plate_log_path))
    print(f"Raw Queue: {plate_log["raw_queue"]}")
    for i in range(len(plate_log["raw_queue"])-1, -1, -1):
        file = plate_log["raw_queue"][i]
        time_since_create = time.time() - os.path.getctime(file)
        delta_modified_created = os.path.getmtime(file) - os.path.getctime(file)
        if time_since_create > (7 * 60) and delta_modified_created > (5 * 60):
            convert_mzxml(file)
            done = plate_log["raw_queue"].pop(i)
            print(f"Conversion of {done} complete.")
    json.dump(plate_log, open(plate_log_path, 'w'), indent=4)

class Watcher:
    def __init__(self):
        self.observer = Observer()

    def run(self):
        self.observer.schedule(New_Dir_Handler(), watch_directory, recursive=False)
        #self.observer.schedule(Finished_Positive_Controls_Handler(), watch_directory, recursive=True)
        self.observer.schedule(New_Raw_Handler(), watch_directory, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(20)
                print("20 second interval passed.")
                check_raw_queue()
        except:
            self.observer.stop()
            print("Observer stopped.")
        
        self.observer.join()

class New_Dir_Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            plate_log = json.load(open(plate_log_path))
            print(os.path.abspath(event.src_path))
            plate_log["new_directories"] += [os.path.abspath(event.src_path)]
            print(f"New directory detected: {os.path.abspath(event.src_path)}")
            mkdir_if_not(os.path.abspath(event.src_path) + "/qc")
            json.dump(plate_log, open(plate_log_path, 'w'), indent=4)

# class Finished_Positive_Controls_Handler(FileSystemEventHandler):
#     def on_created(self, event):
#         if event.is_directory:
#             pass
#         else:
#             file_dir, file_name = os.path.split(os.path.abspath(event.src_path))
#             plate_log = json.load(open(plate_log_path))
#             if file_dir in plate_log["new_directories"] and file_name == "Qstd_1.raw":
#                 print("First Qstd detected. Beginning QC of positive controls.")
#                 json.dump(plate_log, open(plate_log_path, 'w'), indent=4)

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
                plate_log["raw_queue"] += [os.path.abspath(event.src_path)]
                json.dump(plate_log, open(plate_log_path, 'w'), indent=4)

if __name__ == "__main__":
    check_directories_on_start()
    watch = Watcher()
    watch.run()