import os
import uuid

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from backend import config

recordings_bp = Blueprint("recordings", __name__)

# Simple in-memory placeholders
is_recording = False
current_language = "en"
transcript_text = ""


@recordings_bp.route("/start-recording", methods=["POST"])
def start_recording():
    global is_recording
    is_recording = True
    return jsonify({"status": "recording_started"}), 200


@recordings_bp.route("/stop-recording", methods=["POST"])
def stop_recording():
    global is_recording, current_language, transcript_text
    current_language = None

    saved_filename = None
    if "audio" in request.files:
        audio_file = request.files["audio"]
        if audio_file and audio_file.filename:
            ext = os.path.splitext(secure_filename(audio_file.filename))[1] or ".webm"
            filename = f\"{uuid.uuid4().hex}{ext}\"
            save_path = config.RECORDINGS_DIR / filename
            audio_file.save(save_path)
            saved_filename = filename

    if request.is_json:
        data = request.get_json() or {}
        current_language = data.get("language") or data.get("language_select")
    else:
        current_language = (
            request.form.get("language") or request.form.get("language_select")
        )

    if not current_language:
        current_language = (
            request.values.get("language")
            or request.values.get("language_select")
            or "en"
        )

    is_recording = False

    # Placeholder transcript (replace with Whisper integration later)
    transcript_text = "Patient reports fever and cough"

    resp = {
        "status": "recording_stopped",
        "language": current_language,
        "transcript": transcript_text,
        "audio_file": saved_filename,
    }
    return jsonify(resp), 200


@recordings_bp.route("/generate_report", methods=["POST"])
def generate_report():
    if not transcript_text:
        return jsonify({"error": "No transcript available"}), 400

    report = (
        "Chief Complaint: Fever, cough\n"
        "Assessment: Possible viral infection\n"
        "Plan: Paracetamol, hydration"
    )

    return jsonify({"report": report}), 200
