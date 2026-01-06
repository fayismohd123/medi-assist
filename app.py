import os
import sqlite3
import uuid
from werkzeug.utils import secure_filename
from flask import Flask, request, render_template, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "mediassist_secret_key"

# Enable CORS for React frontend
CORS(app, supports_credentials=True, origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"])

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
# Template routes commented out - React frontend handles routing
# @app.route("/")
# def home():
#     return render_template("login.html")


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
        return jsonify({
            "message": "Login successful",
            "user": {
                "email": email,
                "name": user["name"] if user["name"] else ""
            }
        }), 200

    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200


@app.route("/api/auth/status")
def auth_status():
    if "user" in session:
        return jsonify({
            "authenticated": True,
            "user": {
                "email": session.get("user"),
                "name": session.get("name", "")
            }
        }), 200
    return jsonify({"authenticated": False}), 401


# Template route commented out - React frontend handles routing
# @app.route("/dashboard")
# def dashboard():
#     if "user" not in session:
#         return redirect("/")
#     doctor_name = session.get("name", "")
#     return render_template("dashboard.html", doctor_name=doctor_name)


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
    if 'audio' in request.files:
        audio_file = request.files['audio']
        if audio_file and audio_file.filename:
            # generate a safe unique filename
            ext = os.path.splitext(secure_filename(audio_file.filename))[1] or '.webm'
            filename = f"{uuid.uuid4().hex}{ext}"
            save_path = os.path.join(RECORDINGS_DIR, filename)
            audio_file.save(save_path)
            saved_filename = filename
        else:
            saved_filename = None
    else:
        saved_filename = None

    # Accept JSON or form data for language selection
    if request.is_json:
        data = request.get_json() or {}
        current_language = data.get('language') or data.get('language_select')
    else:
        current_language = request.form.get('language') or request.form.get('language_select')

    if not current_language:
        current_language = request.values.get('language') or request.values.get('language_select') or 'en'

    is_recording = False

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


# -------------------------------------------------------------------
# App entry point
# -------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
