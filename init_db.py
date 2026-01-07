import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    name TEXT
)
""")

conn.commit()
conn.close()

print("Users table verified/created successfully")
print("Database path:", DB_PATH)

# Ensure 'name' column exists for older databases
#conn = sqlite3.connect(DB_PATH)
#c = conn.cursor()
#cols = [r[1] for r in c.execute("PRAGMA table_info(users)")]
#if 'name' not in cols:
 #   try:
  ##      c.execute("ALTER TABLE users ADD COLUMN name TEXT")
        #conn.commit()
        #print("Added 'name' column to users table")
    #except Exception as e:
        #print("Could not add 'name' column:", e)
#conn.close()

# Create patients table (allows duplicate phone numbers)
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    age INTEGER,
    created_by TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()
conn.close()
print("Patients table verified/created successfully")

