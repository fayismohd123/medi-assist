import os
import sqlite3
import uuid
from werkzeug.utils import secure_filename
from flask import Flask, request, render_template, jsonify, session, redirect, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import subprocess
import json

app = Flask(__name__, static_folder='dist', static_url_path='')
app.secret_key = "mediassist_secret_key"

# -------------------------------------------------------------------
# Database configuration (ABSOLUTE PATH – prevents corruption issues)
# -------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

# Directory where uploaded/recorded audio files are saved for later processing
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Ensure users table exists and has a 'name' column (migrate older DBs)
def ensure_users_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # create table if it doesn't exist (with name column)
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not c.fetchone():
        c.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
            """
        )
        conn.commit()
    else:
        # add 'name' column if missing
        cols = [r[1] for r in c.execute("PRAGMA table_info(users)")]
        if 'name' not in cols:
            try:
                c.execute("ALTER TABLE users ADD COLUMN name TEXT")
                conn.commit()
            except Exception:
                # safe to ignore; we'll handle missing column in queries
                pass

    conn.close()


# Run migration/check at startup
ensure_users_table()


# Ensure patients table exists
def ensure_patients_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            age INTEGER,
            created_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


ensure_patients_table()


# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------
@app.route("/")
def home():
    # Serve React app
    return send_from_directory(app.static_folder, 'index.html')


@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "Name, email and password required"}), 400

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    c = conn.cursor()

    try:
        c.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, hashed_password)
        )
        conn.commit()
        return jsonify({"message": "Signup successful"}), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 409

    finally:
        conn.close()


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT password, name FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()

    if user and check_password_hash(user["password"], password):
        session["user"] = email
        # store display name in session for templates
        session["name"] = user["name"] if user["name"] else ""
        return jsonify({"message": "Login successful"}), 200

    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/api/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200


@app.route("/dashboard")
def dashboard():
    # Serve React app - React Router will handle the route
    return send_from_directory(app.static_folder, 'index.html')

@app.route("/api/user-info")
def user_info():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({
        "email": session.get("user"),
        "name": session.get("name", "")
    }), 200


# -------------------------------------------------------------------
# Speech / Recording Simulation (placeholder logic)
# -------------------------------------------------------------------
is_recording = False
current_language = "en"
transcript_text = ""


@app.route("/start-recording", methods=["POST"])
def start_recording():
    global is_recording
    is_recording = True
    print("Recording started")
    return jsonify({"status": "recording_started"}), 200


@app.route("/stop-recording", methods=["POST"])
def stop_recording():
    global is_recording, current_language, transcript_text
    # Accept either multipart/form-data (with file) or JSON/form POSTs
    current_language = None

    # If an audio file was uploaded (from the browser MediaRecorder), save it
    audio_file = None
    saved_filename = None
    
    if 'audio' in request.files:
        audio_file = request.files['audio']
        if audio_file and audio_file.filename:
            try:
                # Ensure directory exists
                os.makedirs(RECORDINGS_DIR, exist_ok=True)
                
                # generate a safe unique filename
                ext = os.path.splitext(secure_filename(audio_file.filename))[1] or '.webm'
                filename = f"{uuid.uuid4().hex}{ext}"
                save_path = os.path.join(RECORDINGS_DIR, filename)
                
                # Save the file
                audio_file.save(save_path)
                
                # Verify file was saved
                if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                    saved_filename = filename
                    print(f"Recording saved successfully: {save_path} ({os.path.getsize(save_path)} bytes)")
                else:
                    print(f"ERROR: File was not saved properly to {save_path}")
                    saved_filename = None
            except Exception as e:
                print(f"ERROR saving recording: {e}")
                saved_filename = None
        else:
            print("WARNING: audio file is empty or has no filename")
            saved_filename = None
    else:
        print("WARNING: No 'audio' file in request.files")
        saved_filename = None

    is_recording = False

    # Default language for transcription (can be changed if needed)
    current_language = 'ml'  # Default to Malayalam for mixed input

    # Placeholder transcript (Whisper integration will replace this)
    transcript_text = "Patient reports fever and cough"

    resp = {
        "status": "recording_stopped",
        "language": current_language,
        "transcript": transcript_text,
        "audio_file": saved_filename
    }
    return jsonify(resp), 200


@app.route("/generate_report", methods=["POST"])
def generate_report():
    if not transcript_text:
        return jsonify({"error": "No transcript available"}), 400

    report = (
        "Chief Complaint: Fever, cough\n"
        "Assessment: Possible viral infection\n"
        "Plan: Paracetamol, hydration"
    )

    return jsonify({"report": report}), 200


@app.route("/api/register-patient", methods=["POST"])
def register_patient():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    name = data.get("name")
    phone = data.get("phone")
    age = data.get("age")

    if not name or not phone:
        return jsonify({"error": "Name and phone required"}), 400

    try:
        age_val = int(age) if age not in (None, "") else None
    except ValueError:
        return jsonify({"error": "Age must be a number"}), 400

    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO patients (name, phone, age, created_by) VALUES (?, ?, ?, ?)",
        (name, phone, age_val, session.get("user"))
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Patient registered"}), 201


@app.route("/api/lookup-patient")
def lookup_patient():
    phone = request.args.get('phone', '').strip()
    if not phone:
        return jsonify({"patients": []}), 200

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, phone, age, created_at FROM patients WHERE phone = ? ORDER BY created_at DESC", (phone,))
    rows = c.fetchall()
    conn.close()

    patients = []
    for r in rows:
        patients.append({
            "id": r["id"],
            "name": r["name"],
            "phone": r["phone"],
            "age": r["age"],
            "created_at": r["created_at"]
        })

    return jsonify({"patients": patients}), 200


# Catch all routes for React Router
@app.route("/<path:path>")
def serve_react(path):
    # Serve React app for all routes except API routes
    if path.startswith("api/") or path.startswith("start-recording") or path.startswith("stop-recording") or path.startswith("generate_report"):
        return jsonify({"error": "Not found"}), 404
    return send_from_directory(app.static_folder, 'index.html')

# -------------------------------------------------------------------
# App entry point
# -------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
