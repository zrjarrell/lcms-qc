import os

def mkdir_if_not(dirpath):
    if os.path.exists(dirpath):
        pass
    else:
        dirpath = os.path.normpath(dirpath)
        os.mkdir(dirpath)

def check_file_sequence(filename):
    try:
        file_num = int(filename[-5])
        if file_num % 2 == 1:
            return "hilicpos"
        else:
            return "c18neg"
    except:
        return "error"

def db_labeler(prefix: str, num: int, length: int = 8):
    num = str(num)
    return prefix + "0" * (length - len(num)) + num

def get_next_id(cur, table):
    if table == "experiment":
        label = "exp"
    elif table == "sampleQC":
        label = "samp"
    cur.execute(f"SELECT id FROM {table}")
    rows = cur.fetchall()
    if len(rows) == 0:
        return 1
    else:
        ids = [row[0] for row in rows]
        nums = [int(id.split(label)[1]) for id in ids]
        return max(nums) + 1
