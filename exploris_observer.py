import json, time, os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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
    json.dump(plate_log, open("plate_log.json", 'w'), indent=4)

def check_raw_queue():
    plate_log = json.load(open(plate_log_path))
    for file in plate_log["raw_queue"]:
        if (time.time() - os.path.getctime(file)) > (60 * 7):
            #need to refactor 'raw_manipulation.py -> convert_mzxmls()' so that it
            #takes individual *.raw paths
            pass

class Watcher:
    def __init__(self):
        self.observer = Observer()

    def run(self):
        self.observer.schedule(New_Dir_Handler(), watch_directory, recursive=False)
        #self.observer.schedule(new_active_handler, watch_directory, recursive=True)
        self.observer.schedule(Finished_Positive_Controls_Handler(), watch_directory, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(60)
        except:
            self.observer.stop()
            print("Observer Stopped")
        
        self.observer.join()

class New_Dir_Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            plate_log = json.load(open(plate_log_path))
            plate_log["new_directories"] += [os.path.abspath(event.src_path)]
            print(f"New directory detected: {os.path.abspath(event.src_path)}")
            json.dump(plate_log, open("plate_log.json", 'w'), indent=4)

# class New_Active_Dir_Handler(FileSystemEventHandler):
#     def on_created(self, event):
#         if event.is_directory:
#             pass
#         else:
#             file_dir, file_name = os.path.split(os.path.abspath(event.src_path))
#             plate_log = json.load(open(plate_log_path))
#             if file_name[-4:] == ".raw" and file_dir != plate_log["active_directory"]:
#                 if file_dir in plate_log["new_directories"]:
#                     plate_log["active_directory"] = file_dir
#                     print(f"Detected new file: {os.path.abspath(event.src_path)}")
#                     print(f"Changing active directory to: {file_dir}")
#                 json.dump(plate_log, open("plate_log.json", 'w'), indent=4)

class Finished_Positive_Controls_Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            pass
        else:
            file_dir, file_name = os.path.split(os.path.abspath(event.src_path))
            plate_log = json.load(open(plate_log_path))
            if file_dir in plate_log["new_directories"] and file_name == "Qstd_1.raw":
                print("First Qstd detected. Beginning QC of positive controls.")
                json.dump(plate_log, open("plate_log.json", 'w'), indent=4)

class New_Raw_Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            pass
        else:
            file_dir, file_name = os.path.split(os.path.abspath(event.src_path))
            plate_log = json.load(open(plate_log_path))
            if file_dir in plate_log["new_directories"] and file_name[-4:] == ".raw":
                print(f"New raw detected: {os.path.abspath}")
                plate_log["raw_queue"] += [{os.path.abspath(event.src_path)}]
                json.dump(plate_log, open("plate_log.json", 'w'), indent=4)
        

if __name__ == "__main__":
    check_directories_on_start()
    watch = Watcher()
    watch.run()