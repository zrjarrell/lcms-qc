import sqlite3
import pandas as pd
import sys

con = sqlite3.connect("./db/qc_results.db")
cur = con.cursor()

def readTable(table):
    return pd.read_sql_query(f"SELECT * FROM {table}", con)

print(readTable(sys.argv[1]))