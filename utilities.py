import os

def mkdir_if_not(dirpath):
    if os.path.exists(dirpath):
        pass
    else:
        os.mkdir(dirpath)