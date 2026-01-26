import os
import sqlite3
import uuid
from werkzeug.utils import secure_filename
from flask import Flask, request, render_template, jsonify, session, redirect, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import subprocess
import json
from datetime import datetime
from utils.token_generator import generate_token, validate_token_format
from openai import OpenAI
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    print("Warning: pydub not available. Audio conversion will be skipped.")
    PYDUB_AVAILABLE = False
import re

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

# Directory for generated reports
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# OpenAI API client for Whisper transcription
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    print(f"Warning: OpenAI API not configured. Transcription will use mock data. Error: {e}")
    client = None

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def extract_symptoms_from_transcript(transcript):
    """
    Extract symptoms from medical transcript using pattern matching.
    Returns a list of symptoms with status and details.
    """
    if not transcript:
        return []
    
    transcript_lower = transcript.lower()
    
    # Common symptoms and their variations
    symptom_patterns = {
        "fever": [r"\bfever\b", r"\btemperature\b", r"\bhot\b", r"\bfebrile\b"],
        "cough": [r"\bcough\b", r"\bcoughing\b", r"\bcoughs\b"],
        "headache": [r"\bheadache\b", r"\bhead pain\b", r"\bheadaches\b"],
        "sore_throat": [r"\bsore throat\b", r"\bthroat pain\b", r"\bthroat ache\b"],
        "body_ache": [r"\bbody ache\b", r"\bbody pain\b", r"\bmuscle pain\b", r"\bache\b"],
        "fatigue": [r"\bfatigue\b", r"\btired\b", r"\bweak\b", r"\bweakness\b"],
        "nausea": [r"\bnausea\b", r"\bnauseous\b"],
        "vomiting": [r"\bvomit\b", r"\bvomiting\b"],
        "diarrhea": [r"\bdiarrhea\b", r"\bloose stool\b"],
        "rash": [r"\brash\b", r"\bskin rash\b"],
        "chills": [r"\bchills\b", r"\bchilly\b"],
        "shortness_of_breath": [r"\bshortness of breath\b", r"\bdyspnea\b", r"\bbreathing difficulty\b"],
        "congestion": [r"\bcongestion\b", r"\bcongested\b", r"\bnasal congestion\b"],
        "sneeze": [r"\bsneeze\b", r"\bsneezing\b"],
        "runny_nose": [r"\brunny nose\b", r"\bnasal discharge\b"],
    }
    
    symptoms = []
    
    for symptom_name, patterns in symptom_patterns.items():
        for pattern in patterns:
            if re.search(pattern, transcript_lower):
                # Extract duration if mentioned
                duration_pattern = pattern + r".*?(?:for|since|about|for the last)\s+([\d\w\s]+)"
                duration_match = re.search(duration_pattern, transcript_lower)
                duration = duration_match.group(1).strip() if duration_match else None
                
                symptoms.append({
                    "name": symptom_name.replace("_", " "),
                    "status": "present",
                    "duration": duration
                })
                break  # Found this symptom, move to next
    
    return symptoms


def transcribe_audio_with_whisper(audio_path):
    """
    Use OpenAI Whisper API to transcribe audio file.
    Falls back to mock data if API not configured.
    """
    if not client:
        # Return mock transcript if OpenAI not configured
        return "Patient reports fever, cough, and body aches. Symptoms started 3 days ago. Has been experiencing chills and fatigue."
    
    try:
        # Convert to WAV if needed and pydub is available
        audio_file = audio_path
        if PYDUB_AVAILABLE and audio_path.endswith('.webm'):
            wav_path = audio_path.replace('.webm', '.wav')
            try:
                audio = AudioSegment.from_file(audio_path, format="webm")
                audio.export(wav_path, format="wav")
                audio_file = wav_path
            except Exception as e:
                print(f"Error converting audio with pydub: {e}. Using original file.")
                audio_file = audio_path
        
        # Transcribe with Whisper API
        with open(audio_file, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="en"
            )
        
        return transcript.text
    
    except Exception as e:
        print(f"Whisper API error: {e}")
        return "Error transcribing audio. Please check OpenAI API configuration."


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
                password TEXT NOT NULL,
                speciality TEXT,
                contact TEXT
            )
            """
        )
        conn.commit()
    else:
        # add missing columns
        cols = [r[1] for r in c.execute("PRAGMA table_info(users)")]
        if 'name' not in cols:
            try:
                c.execute("ALTER TABLE users ADD COLUMN name TEXT")
                conn.commit()
            except Exception:
                pass
        if 'speciality' not in cols:
            try:
                c.execute("ALTER TABLE users ADD COLUMN speciality TEXT")
                conn.commit()
            except Exception:
                pass
        if 'contact' not in cols:
            try:
                c.execute("ALTER TABLE users ADD COLUMN contact TEXT")
                conn.commit()
            except Exception:
                pass

    conn.close()


# Run migration/check at startup
ensure_users_table()


# Ensure appointments table exists (token-based booking system)
def ensure_appointments_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            patient_name TEXT NOT NULL,
            patient_email TEXT NOT NULL,
            patient_phone TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            status TEXT DEFAULT 'scheduled',
            consultation_notes TEXT,
            recorded_audio_path TEXT,
            report_generated BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME,
            doctor_id INTEGER,
            FOREIGN KEY(doctor_id) REFERENCES users(id)
        )
        """
    )
    conn.commit()
    conn.close()


ensure_appointments_table()


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
    speciality = data.get("speciality", "")
    contact = data.get("contact", "")

    if not name or not email or not password:
        return jsonify({"error": "Name, email and password required"}), 400

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    c = conn.cursor()

    try:
        c.execute(
            "INSERT INTO users (name, email, password, speciality, contact) VALUES (?, ?, ?, ?, ?)",
            (name, email, hashed_password, speciality, contact)
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
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT name, speciality, contact FROM users WHERE email = ?", (session.get("user"),))
    user = c.fetchone()
    conn.close()
    
    if user:
        return jsonify({
            "email": session.get("user"),
            "name": user['name'],
            "speciality": user['speciality'],
            "contact": user['contact']
        }), 200
    else:
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
    """
    Start recording endpoint - just acknowledges the recording has started.
    Frontend handles actual audio capture via MediaRecorder API.
    """
    print("Recording started")
    return jsonify({"status": "recording_started", "message": "Audio recording in progress"}), 200


@app.route("/stop-recording", methods=["POST"])
def stop_recording():
    """
    Stop recording and process audio with Whisper API.
    Returns transcript and extracted symptoms.
    """
    saved_filename = None
    transcript_text = ""
    symptoms = []
    
    try:
        # Save audio file from browser
        if 'audio' in request.files:
            audio_file = request.files['audio']
            if audio_file and audio_file.filename:
                try:
                    # Generate safe unique filename with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    ext = os.path.splitext(secure_filename(audio_file.filename))[1] or '.webm'
                    filename = f"recording_{timestamp}{ext}"
                    save_path = os.path.join(RECORDINGS_DIR, filename)
                    
                    # Save the file
                    audio_file.save(save_path)
                    
                    # Verify file was saved
                    if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                        saved_filename = filename
                        print(f"Recording saved: {save_path} ({os.path.getsize(save_path)} bytes)")
                        
                        # Transcribe with Whisper API
                        print(f"Transcribing audio with Whisper API...")
                        transcript_text = transcribe_audio_with_whisper(save_path)
                        print(f"Transcript: {transcript_text}")
                        
                        # Extract symptoms from transcript
                        symptoms = extract_symptoms_from_transcript(transcript_text)
                        print(f"Extracted symptoms: {symptoms}")
                    else:
                        return jsonify({"error": "File not saved properly"}), 400
                        
                except Exception as e:
                    print(f"Error processing audio: {e}")
                    return jsonify({"error": f"Audio processing failed: {str(e)}"}), 400
            else:
                return jsonify({"error": "No audio file provided"}), 400
        else:
            return jsonify({"error": "No audio file in request"}), 400
        
        # Return successful response with transcript and symptoms
        return jsonify({
            "status": "recording_stopped",
            "audio_file": saved_filename,
            "transcript": transcript_text,
            "symptoms": symptoms,
            "message": "Recording processed successfully"
        }), 200
        
    except Exception as e:
        print(f"Error in stop_recording: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/generate_report", methods=["POST"])
def generate_report():
    """
    Generate medical report from consultation data.
    """
    try:
        data = request.get_json()
        appointment_id = data.get("appointment_id")
        transcript = data.get("transcript", "")
        symptoms = data.get("symptoms", [])
        consultation_notes = data.get("notes", "")
        recording_filename = data.get("recording_filename")
        
        if not appointment_id:
            return jsonify({"error": "Appointment ID required"}), 400
        
        # Get appointment details from database
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
        appt = c.fetchone()
        
        if not appt:
            conn.close()
            return jsonify({"error": "Appointment not found"}), 404
        
        # Build report content
        report_lines = [
            "="*60,
            "MEDICAL CONSULTATION REPORT",
            "="*60,
            "",
            "PATIENT INFORMATION",
            "-"*60,
            f"Name: {appt['patient_name']}",
            f"Date of Birth: {appt['patient_dob']}",
            f"Email: {appt['patient_email']}",
            f"Phone: {appt['patient_phone']}",
            f"Appointment Token: {appt['token']}",
            f"Date: {appt['appointment_date']}",
            "",
            "PHYSICIAN INFORMATION",
            "-"*60,
            f"Name: {appt['physician_name']}",
            f"Speciality: {appt['physician_speciality']}",
            f"Contact: {appt['physician_contact']}",
            "",
            "CHIEF COMPLAINTS & SYMPTOMS",
            "-"*60,
        ]
        
        if symptoms:
            for symptom in symptoms:
                symptom_text = f"• {symptom['name'].title()}"
                if symptom.get('duration'):
                    symptom_text += f" (Duration: {symptom['duration']})"
                report_lines.append(symptom_text)
        else:
            report_lines.append("• No specific symptoms reported")
        
        report_lines.extend([
            "",
            "CONSULTATION TRANSCRIPT",
            "-"*60,
            transcript if transcript else "No transcript available",
            "",
            "PHYSICIAN NOTES",
            "-"*60,
            consultation_notes if consultation_notes else "No additional notes",
            "",
            "ASSESSMENT & RECOMMENDATIONS",
            "-"*60,
            "• Further evaluation may be needed based on symptoms",
            "• Patient advised to monitor symptoms and seek care if worsens",
            "• Follow-up consultation recommended in 1 week",
            "",
            "="*60,
            f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "="*60,
        ])
        
        report_text = "\n".join(report_lines)
        
        # Save report to file
        report_filename = f"report_{appt['token']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_path = os.path.join(REPORTS_DIR, report_filename)
        
        with open(report_path, 'w') as f:
            f.write(report_text)
        
        # Update appointment in database with recording path and completion status
        c.execute(
            "UPDATE appointments SET recorded_audio_path = ?, consultation_notes = ?, status = ?, completed_at = ? WHERE id = ?",
            (recording_filename, consultation_notes, "completed", datetime.now().isoformat(), appointment_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "success",
            "report": report_text,
            "report_filename": report_filename,
            "message": "Report generated and saved successfully"
        }), 200
        
    except Exception as e:
        print(f"Error generating report: {e}")
        return jsonify({"error": str(e)}), 500


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


# ============ APPOINTMENT BOOKING ENDPOINTS ============

@app.route("/api/book-appointment", methods=["POST"])
def book_appointment():
    """
    Patient books an appointment and gets a token
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['patient_name', 'patient_dob', 'patient_email', 'patient_phone', 'appointment_date']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Generate unique token
        token = generate_token()
        
        # Insert into database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO appointments (token, patient_name, patient_dob, patient_email, patient_phone, appointment_date, status)
            VALUES (?, ?, ?, ?, ?, ?, 'scheduled')
        ''', (
            token,
            data['patient_name'],
            data['patient_dob'],
            data['patient_email'],
            data['patient_phone'],
            data['appointment_date']
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'token': token,
            'message': f'Appointment booked successfully! Your token: {token}'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/api/lookup-appointment", methods=["POST"])
def lookup_appointment():
    """
    Doctor enters token to find appointment & patient details
    """
    try:
        data = request.get_json()
        token = data.get('token', '').strip().upper()
        
        # Validate token format
        if not validate_token_format(token):
            return jsonify({'error': 'Invalid token format'}), 400
        
        # Query database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM appointments WHERE token = ?', (token,))
        appointment = cursor.fetchone()
        conn.close()
        
        if not appointment:
            return jsonify({'error': 'Token not found'}), 404
        
        # Check if appointment is already completed
        if appointment['status'] == 'completed':
            return jsonify({'error': 'This appointment has already been completed'}), 400
        
        return jsonify({
            'success': True,
            'appointment': {
                'id': appointment['id'],
                'token': appointment['token'],
                'patient_name': appointment['patient_name'],
                'patient_dob': appointment['patient_dob'],
                'patient_email': appointment['patient_email'],
                'patient_phone': appointment['patient_phone'],
                'appointment_date': appointment['appointment_date'],
                'physician_name': appointment['physician_name'],
                'physician_speciality': appointment['physician_speciality'],
                'physician_contact': appointment['physician_contact'],
                'status': appointment['status']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/api/appointments", methods=["GET"])
def get_appointments():
    """
    Get all scheduled appointments
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all scheduled appointments, newest first
        cursor.execute('''
            SELECT id, token, patient_name, patient_dob, patient_email, patient_phone, 
                   appointment_date, status, created_at
            FROM appointments 
            WHERE status = 'scheduled'
            ORDER BY created_at DESC
        ''')
        
        appointments = []
        for row in cursor.fetchall():
            appointments.append({
                'id': row['id'],
                'token': row['token'],
                'patient_name': row['patient_name'],
                'patient_dob': row['patient_dob'],
                'patient_email': row['patient_email'],
                'patient_phone': row['patient_phone'],
                'appointment_date': row['appointment_date'],
                'status': row['status'],
                'created_at': row['created_at']
            })
        
        conn.close()
        return jsonify({'success': True, 'appointments': appointments}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/api/update-appointment/<int:appointment_id>", methods=["PUT"])
def update_appointment(appointment_id):
    """
    Update appointment status after consultation with physician details
    """
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update with consultation notes, physician details and mark as completed
        cursor.execute('''
            UPDATE appointments 
            SET status = ?, 
                consultation_notes = ?, 
                physician_name = ?,
                physician_speciality = ?,
                physician_contact = ?,
                completed_at = ?
            WHERE id = ?
        ''', (
            data.get('status', 'completed'),
            data.get('consultation_notes', ''),
            data.get('physician_name', ''),
            data.get('physician_speciality', ''),
            data.get('physician_contact', ''),
            datetime.now().isoformat(),
            appointment_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Appointment updated'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
