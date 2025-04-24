import os

def mkdir_if_not(dirpath):
    if os.path.exists(dirpath):
        pass
    else:
        dirpath = os.path.normpath(dirpath)
        os.mkdir(dirpath)