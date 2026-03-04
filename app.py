import os
import sqlite3
import uuid
from werkzeug.utils import secure_filename
from flask import Flask, request, render_template, jsonify, session, redirect, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from utils.token_generator import generate_token, validate_token_format
from transcribe import transcribe_audio
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import inch
from reportlab.lib import colors
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    print("Warning: pydub not available. Audio conversion will be skipped.")
    PYDUB_AVAILABLE = False
import re
import joblib
import pandas as pd

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

# -------------------------------------------------------------------
# Disease Prediction Model Loading
# -------------------------------------------------------------------
DISEASE_MODEL_PATH = os.path.join(BASE_DIR, "disease_prediction_model.pkl")
SYMPTOM_LIST_PATH = os.path.join(BASE_DIR, "symptom_list.pkl")

# Load disease prediction model and symptom list
disease_model = None
symptom_list = None
try:
    if os.path.exists(DISEASE_MODEL_PATH) and os.path.exists(SYMPTOM_LIST_PATH):
        disease_model = joblib.load(DISEASE_MODEL_PATH)
        symptom_list = joblib.load(SYMPTOM_LIST_PATH)
        print(f"✓ Disease prediction model loaded successfully")
        print(f"✓ Symptom list loaded with {len(symptom_list)} symptoms")
    else:
        print(f"⚠ Disease model files not found at {DISEASE_MODEL_PATH} or {SYMPTOM_LIST_PATH}")
except Exception as e:
    print(f"⚠ Error loading disease model: {e}")

# OpenAI API client for Whisper transcription
#try:
#    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#except Exception as e:
#    print(f"Warning: OpenAI API not configured. Transcription will use mock data. Error: {e}")
#    client = None

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
            patient_dob TEXT NOT NULL,
            patient_email TEXT NOT NULL,
            patient_phone TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT,
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
    Stop recording and process audio with Faster Whisper.
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
                        
                        wav_path = save_path.replace('.webm', '.wav')
                        try:
                            audio = AudioSegment.from_file(save_path, format="webm")
                            audio.export(wav_path, format="wav")
                            audio_file = wav_path
                        except Exception as e:
                            print(f"Error converting audio with pydub: {e}. Using original file.")
                            audio_file = save_path
                        # ✅ USE FASTER WHISPER TRANSCRIPTION
                        print(f"Transcribing audio with Faster Whisper...")
                        result = transcribe_audio(audio_file)
                        
                        if "error" in result:
                            return jsonify({"error": result["error"]}), 500
                        
                        transcript_text = result["transcript"]
                        symptoms = result["symptoms"]
                        
                        print(f"Transcript: {transcript_text}")
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
            "detected_symptoms": symptoms if isinstance(symptoms, list) else symptoms.get('symptoms', []),
            "message": "Recording processed successfully"
        }), 200
        
    except Exception as e:
        print(f"Error in stop_recording: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/predict-disease", methods=["POST"])
def predict_disease():
    """
    Predict disease based on extracted symptoms.
    Expects JSON payload with 'symptoms' list.
    """
    try:
        if disease_model is None or symptom_list is None:
            return jsonify({
                "error": "Disease prediction model not available",
                "predicted_disease": "Unknown",
                "confidence": 0.0
            }), 400
        
        data = request.get_json()
        extracted_symptoms = data.get("symptoms", [])
        
        if not extracted_symptoms:
            return jsonify({
                "error": "No symptoms provided",
                "predicted_disease": "Unknown",
                "confidence": 0.0
            }), 400
        
        # Extract symptom names from the extracted symptoms list
        # Handle both dict and string formats
        symptom_names = []
        for symptom in extracted_symptoms:
            if isinstance(symptom, dict):
                # If symptom is a dict, extract the 'name' field
                symptom_name = symptom.get('name', str(symptom)).lower().strip()
            else:
                # If symptom is a string, use it directly
                symptom_name = str(symptom).lower().strip()
            
            symptom_names.append(symptom_name)
        
        print(f"Extracted symptom names: {symptom_names}")
        print(f"Available symptoms in model: {symptom_list}")
        
        # Create binary feature vector (1 if symptom present, 0 if absent)
        # Use exact matching of symptom names with model's symptom_list
        input_vector = [
            1 if symptom.lower() in symptom_names else 0 
            for symptom in symptom_list
        ]
        
        print(f"Input vector: {input_vector}")
        
        # Convert to DataFrame for prediction
        input_df = pd.DataFrame([input_vector], columns=symptom_list)
        
        # Predict disease
        predicted_disease = disease_model.predict(input_df)[0]
        probabilities = disease_model.predict_proba(input_df)[0]
        confidence = float(max(probabilities))  # Convert to float for JSON serialization
        
        print(f"Predicted Disease: {predicted_disease}, Confidence: {confidence}")
        
        return jsonify({
            "success": True,
            "predicted_disease": predicted_disease,
            "confidence": round(confidence, 4),
            "message": f"Disease prediction successful"
        }), 200
        
    except Exception as e:
        print(f"Error in predict_disease: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "predicted_disease": "Unknown",
            "confidence": 0.0
        }), 500


@app.route("/generate_report", methods=["POST"])
def generate_report():
    """
    Generate medical report from consultation data in PDF format.
    """
    try:
        data = request.get_json()
        appointment_id = data.get("appointment_id")
        transcript = data.get("transcript", "")
        symptoms = data.get("symptoms", [])
        consultation_notes = data.get("notes", "")
        predicted_disease = data.get("predicted_disease", "Unknown")
        confidence = data.get("confidence", 0.0)
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
        
        # Get physician info from session or database
        physician_name = "Not specified"
        physician_speciality = "Not specified"
        physician_contact = "Not specified"
        
        if "user" in session:
            c.execute("SELECT name, speciality, contact FROM users WHERE email = ?", (session.get("user"),))
            physician = c.fetchone()
            if physician:
                physician_name = physician['name'] if physician['name'] else "Not specified"
                physician_speciality = physician['speciality'] if physician['speciality'] else "Not specified"
                physician_contact = physician['contact'] if physician['contact'] else "Not specified"
        
        # Generate PDF filename
        pdf_filename = f"report_{appt['token']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(REPORTS_DIR, pdf_filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=1  # Center alignment
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#333333'),
            spaceAfter=8,
            spaceBefore=8,
            borderColor=colors.grey,
            borderWidth=1,
            borderPadding=4
        )
        
        # Title
        story.append(Paragraph("MEDICAL CONSULTATION REPORT", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Patient Information Section
        story.append(Paragraph("PATIENT INFORMATION", heading_style))
        patient_data = [
            ["Name:", appt['patient_name']],
            ["Date of Birth:", appt['patient_dob']],
            ["Email:", appt['patient_email']],
            ["Phone:", appt['patient_phone']],
            ["Appointment Token:", appt['token']],
            ["Date:", appt['appointment_date']],
        ]
        patient_table = Table(patient_data, colWidths=[2*inch, 4*inch])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(patient_table)
        story.append(Spacer(1, 0.15*inch))
        
        # Physician Information Section
        story.append(Paragraph("PHYSICIAN INFORMATION", heading_style))
        physician_data = [
            ["Name:", physician_name],
            ["Speciality:", physician_speciality],
            ["Contact:", physician_contact],
        ]
        physician_table = Table(physician_data, colWidths=[2*inch, 4*inch])
        physician_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(physician_table)
        story.append(Spacer(1, 0.15*inch))
        
        # Chief Complaints & Symptoms Section
        story.append(Paragraph("CHIEF COMPLAINTS & SYMPTOMS", heading_style))
        if symptoms:
            symptoms_text = ""
            for symptom in symptoms:
                if isinstance(symptom, dict):
                    symptom_name = symptom.get('name', symptom).title()
                    duration = symptom.get('duration', "")
                    if duration:
                        symptoms_text += f"• {symptom_name} (Duration: {duration})<br/>"
                    else:
                        symptoms_text += f"• {symptom_name}<br/>"
                else:
                    symptoms_text += f"• {str(symptom).title()}<br/>"
            story.append(Paragraph(symptoms_text, styles['Normal']))
        else:
            story.append(Paragraph("• No specific symptoms reported", styles['Normal']))
        story.append(Spacer(1, 0.15*inch))
        
        # Consultation Transcript Section
        story.append(Paragraph("CONSULTATION TRANSCRIPT", heading_style))
        transcript_text = transcript if transcript else "No transcript available"
        story.append(Paragraph(transcript_text, styles['Normal']))
        story.append(Spacer(1, 0.15*inch))
        
        # Physician Notes Section
        story.append(Paragraph("PHYSICIAN NOTES", heading_style))
        notes_text = consultation_notes if consultation_notes else "No additional notes"
        story.append(Paragraph(notes_text, styles['Normal']))
        story.append(Spacer(1, 0.15*inch))
        
        # Assessment & Recommendations Section
        story.append(Paragraph("ASSESSMENT & RECOMMENDATIONS", heading_style))
        
        # Include disease prediction if available
        disease_prediction_text = ""
        if predicted_disease and predicted_disease != "Unknown":
            confidence_percent = round(confidence * 100, 1) if confidence else 0
            disease_prediction_text = f"<b>Preliminary Disease Prediction:</b> {predicted_disease} (Confidence: {confidence_percent}%)<br/><br/>"
        
        recommendations = disease_prediction_text + "• Further evaluation may be needed based on symptoms<br/>• Patient advised to monitor symptoms and seek care if worsens<br/>• Follow-up consultation recommended in 1 week"
        story.append(Paragraph(recommendations, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Footer with timestamp
        footer_text = f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=1
        )
        story.append(Paragraph(footer_text, footer_style))
        
        # Build PDF
        doc.build(story)
        
        # Update appointment in database with recording path and completion status
        c.execute(
            "UPDATE appointments SET recorded_audio_path = ?, consultation_notes = ?, status = ?, completed_at = ? WHERE id = ?",
            (recording_filename, consultation_notes, "completed", datetime.now().isoformat(), appointment_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "success",
            "report_filename": pdf_filename,
            "message": "Report generated and saved as PDF successfully"
        }), 200
        
    except Exception as e:
        print(f"Error generating report: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/download-report/<filename>", methods=["GET"])
def download_report(filename):
    """
    Download a generated PDF report.
    """
    try:
        # Validate filename to prevent directory traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            return jsonify({"error": "Invalid filename"}), 400
        
        report_path = os.path.join(REPORTS_DIR, filename)
        
        # Check if file exists
        if not os.path.exists(report_path):
            return jsonify({"error": "Report not found"}), 404
        
        return send_from_directory(REPORTS_DIR, filename, as_attachment=True, mimetype='application/pdf')
    except Exception as e:
        print(f"Error downloading report: {e}")
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
