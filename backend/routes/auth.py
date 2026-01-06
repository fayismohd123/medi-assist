from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from backend.utils.database import get_db_connection

auth_bp = Blueprint("auth", __name__, url_prefix="/api")


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
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
            (name, email, hashed_password),
        )
        conn.commit()
        return jsonify({"message": "Signup successful"}), 201
    except Exception:
        return jsonify({"error": "Email already exists"}), 409
    finally:
        conn.close()


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT password, name FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()

    if user and check_password_hash(user["password"], password):
        session["user"] = email
        session["name"] = user["name"] if user["name"] else ""
        return jsonify(
            {
                "message": "Login successful",
                "user": {"email": email, "name": user["name"] or ""},
            }
        ), 200

    return jsonify({"error": "Invalid credentials"}), 401


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200


@auth_bp.route("/auth/status")
def auth_status():
    if "user" in session:
        return jsonify(
            {
                "authenticated": True,
                "user": {
                    "email": session.get("user"),
                    "name": session.get("name", ""),
                },
            }
        ), 200
    return jsonify({"authenticated": False}), 401
