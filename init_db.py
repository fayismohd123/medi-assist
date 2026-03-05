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

# Create appointments table (token-based booking system)
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT UNIQUE NOT NULL,
    patient_name TEXT NOT NULL,
    patient_dob TEXT NOT NULL,
    patient_email TEXT NOT NULL,
    patient_phone TEXT NOT NULL,
    appointment_date TEXT NOT NULL,
    physician_name TEXT,
    physician_speciality TEXT,
    physician_contact TEXT,
    status TEXT DEFAULT 'scheduled',
    consultation_notes TEXT,
    recorded_audio_path TEXT,
    report_generated BOOLEAN DEFAULT 0,
    prescribed_medicines TEXT DEFAULT '[]',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    doctor_id INTEGER,
    FOREIGN KEY(doctor_id) REFERENCES users(id)
)
""")
conn.commit()

# Migrate existing appointments table if needed (add prescribed_medicines column if missing)
try:
    cols = [r[1] for r in c.execute("PRAGMA table_info(appointments)")]
    if 'prescribed_medicines' not in cols:
        c.execute("ALTER TABLE appointments ADD COLUMN prescribed_medicines TEXT DEFAULT '[]'")
        conn.commit()
        print("✓ Added 'prescribed_medicines' column to appointments table")
except Exception as e:
    print(f"Note: Could not add prescribed_medicines column: {e}")

conn.close()
print("Appointments table verified/created successfully")

# Keep patients table for backwards compatibility
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
print("Patients table verified/created successfully (backwards compatibility)")

