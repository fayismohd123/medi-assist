import random
import sqlite3
from datetime import datetime
import os

def generate_token():
    """
    Generates a unique token in format: YYYYMMDD_###
    Example: 20260110_001
    Increments number based on appointments booked today
    """
    today = datetime.now().strftime("%Y%m%d")
    
    # Get database path
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, "database.db")
    
    # Count appointments booked today
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as count FROM appointments WHERE token LIKE ?",
            (f"{today}_%",)
        )
        result = cursor.fetchone()
        count = result[0] if result else 0
        conn.close()
    except:
        count = 0
    
    # Next token number
    next_num = count + 1
    token = f"{today}_{next_num:03d}"
    return token

def validate_token_format(token):
    """
    Validates if token matches expected format: YYYYMMDD_###
    Example: 20260110_001
    """
    parts = token.split('_')
    if len(parts) == 2:
        try:
            int(parts[0])  # date should be 8 digits
            int(parts[1])  # sequence should be digits
            if len(parts[0]) == 8 and len(parts[1]) >= 1:
                return True
        except ValueError:
            return False
    return False
