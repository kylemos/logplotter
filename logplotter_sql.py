import sqlite3

class dbConnect:
    
    '''Implements read-only db connection as context manager'''
    
    # class variables: queries
    qry_tables = "SELECT name FROM sqlite_master WHERE type='table';"
    qry_data = "SELECT * FROM ?;"

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