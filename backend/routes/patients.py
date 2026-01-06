from flask import Blueprint, jsonify, request, session

from backend.utils.database import get_db_connection

patients_bp = Blueprint("patients", __name__, url_prefix="/api")


@patients_bp.route("/register-patient", methods=["POST"])
def register_patient():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
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
        (name, phone, age_val, session.get("user")),
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Patient registered"}), 201


@patients_bp.route("/lookup-patient")
def lookup_patient():
    phone = (request.args.get("phone") or "").strip()
    if not phone:
        return jsonify({"patients": []}), 200

    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, name, phone, age, created_at FROM patients WHERE phone = ? ORDER BY created_at DESC",
        (phone,),
    )
    rows = c.fetchall()
    conn.close()

    patients = []
    for r in rows:
        patients.append(
            {
                "id": r["id"],
                "name": r["name"],
                "phone": r["phone"],
                "age": r["age"],
                "created_at": r["created_at"],
            }
        )

    return jsonify({"patients": patients}), 200
