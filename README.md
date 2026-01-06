# MediAssist

Full-stack application with a Flask API backend and a React (Vite) frontend.

## Project Structure

```
medi-assist/
├── backend/                 # Flask backend package
│   ├── app.py               # App factory + blueprints
│   ├── config.py            # Paths, secrets, CORS origins
│   ├── routes/              # API blueprints
│   │   ├── auth.py
│   │   ├── patients.py
│   │   └── recordings.py
│   ├── utils/               # DB helpers
│   │   └── database.py
│   ├── ml/                  # ML components
│   │   └── extractor.py
├── data/                    # Persistent data
│   ├── database.db
│   └── recordings/
├── frontend/                # React (Vite) app
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── context/
│   │   └── ...
│   ├── package.json
│   └── vite.config.js
├── init_db.py               # Manual DB initialization helper
├── requirements.txt         # Python dependencies
└── app.py                   # Entry point (imports backend.app)
```

## Running the project

1) Backend (Flask API)
```bash
pip install -r requirements.txt
python app.py
```
Runs on http://127.0.0.1:5000 (API only; UI is separate).

2) Frontend (React)
```bash
cd frontend
npm install
npm run dev
```
Access http://localhost:5173 (proxied to the Flask API).

## Notes
- The backend is API-only; the React app handles all UI routes.
- CORS is enabled for localhost ports 5173/3000.
- Audio uploads are stored in `data/recordings/`; the SQLite DB is in `data/database.db`.
