import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "knowledge.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    return conn

def get_connection():
    return sqlite3.connect(DB_PATH)
