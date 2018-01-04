"""
Database interaction classes:

dbConnect (class)   - Context-manager implementation of sqlite database cursor.
"""

import sqlite3


class dbConnect:

    """Implements db connection as context manager"""

    # class variables
    qry_tables = "SELECT name FROM sqlite_master WHERE type='table';"
    qry_data = "SELECT * FROM {0} WHERE hole_id='{1}';"
    qry_bhs = "SELECT DISTINCT hole_id FROM tbl_duct ORDER BY hole_id;"

    def __init__(self, dbpath):
        self.dbpath = dbpath
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.dbpath)
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_class, exc, traceback):
        self.conn.close()
