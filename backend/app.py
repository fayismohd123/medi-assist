import os

from flask import Flask
from flask_cors import CORS

from backend import config
from backend.routes.auth import auth_bp
from backend.routes.patients import patients_bp
from backend.routes.recordings import recordings_bp
from backend.utils.database import init_db


def create_app():
    app = Flask(__name__)
    app.secret_key = config.SECRET_KEY

    # Ensure data paths exist and initialize DB
    init_db()

    # CORS for frontend
    CORS(app, supports_credentials=True, origins=config.ALLOWED_ORIGINS)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(recordings_bp)

    @app.route("/")
    def health():
        return {
            "message": "MediAssist API Server",
            "status": "running",
            "frontend_url": "http://localhost:5173",
            "note": "This server serves APIs only; the React UI runs separately.",
        }

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
