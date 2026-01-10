import sqlite3
import json
from datetime import datetime

DB_PATH = 'database.db'

def view_database():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("DATABASE CONTENTS - MediAssist")
    print("="*80)
    
    # Check USERS table
    print("\n📋 USERS TABLE (Doctors/Admin)")
    print("-" * 80)
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    
    if users:
        for user in users:
            print(f"ID: {user['id']}")
            print(f"  Email: {user['email']}")
            print(f"  Name: {user['name']}")
            print()
    else:
        print("❌ No users found")
    
    # Check APPOINTMENTS table
    print("\n📋 APPOINTMENTS TABLE")
    print("-" * 80)
    cursor.execute('SELECT * FROM appointments')
    appointments = cursor.fetchall()
    
    if appointments:
        print(f"Total appointments: {len(appointments)}\n")
        for apt in appointments:
            print(f"ID: {apt['id']}")
            print(f"  Token: {apt['token']}")
            print(f"  Patient Name: {apt['patient_name']}")
            print(f"  Patient DOB: {apt['patient_dob']}")
            print(f"  Patient Email: {apt['patient_email']}")
            print(f"  Patient Phone: {apt['patient_phone']}")
            print(f"  Appointment Date: {apt['appointment_date']}")
            print(f"  Status: {apt['status']}")
            print(f"  Physician Name: {apt['physician_name']}")
            print(f"  Physician Specialty: {apt['physician_speciality']}")
            print(f"  Physician Contact: {apt['physician_contact']}")
            print(f"  Consultation Notes: {apt['consultation_notes']}")
            print(f"  Created: {apt['created_at']}")
            if apt['completed_at']:
                print(f"  Completed: {apt['completed_at']}")
            print()
    else:
        print("❌ No appointments found")
    
    # Database Statistics
    print("\n" + "="*80)
    print("DATABASE STATISTICS")
    print("="*80)
    cursor.execute('SELECT COUNT(*) as count FROM users')
    user_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM appointments')
    apt_count = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM appointments WHERE status = "scheduled"')
    scheduled = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM appointments WHERE status = "completed"')
    completed = cursor.fetchone()['count']
    
    print(f"Total Users: {user_count}")
    print(f"Total Appointments: {apt_count}")
    print(f"  - Scheduled: {scheduled}")
    print(f"  - Completed: {completed}")
    print("="*80 + "\n")
    
    conn.close()

if __name__ == '__main__':
    try:
        view_database()
    except Exception as e:
        print(f"❌ Error: {e}")
