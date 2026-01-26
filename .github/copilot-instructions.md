# MediAssist - Copilot Instructions

## Project Overview

MediAssist is a full-stack medical consultation platform combining:
- **Frontend**: React 18 (Vite) at port 3000 with 3 pages (Login, Dashboard, BookAppointment)
- **Backend**: Flask API at port 5000 serving React and handling medical workflows
- **Database**: SQLite (`database.db`) with users, appointments, and patients tables
- **AI Integration**: OpenAI Whisper for audio transcription + pattern-based symptom extraction

**Critical Architecture**: Flask serves the React build from `dist/` in production, but during development Vite proxies API calls to Flask via `vite.config.js`.

## Key Development Workflows

### Starting the Application
1. **Frontend Dev**: `npm run dev` (Vite at http://localhost:3000, proxies `/api/*` to Flask)
2. **Backend**: `python app.py` (Flask at http://127.0.0.1:5000)
3. **Build**: `npm run build` creates `dist/` folder
4. **Database Init**: `python init_db.py` (creates/verifies users, appointments, patients tables)

**Dependencies to install**: `openai`, `pydub`, `flask`, `werkzeug` (see terminal history for commands)

### Critical Paths
- **App Root**: [app.py](app.py) - all Flask routes and core logic
- **Frontend Entry**: [src/main.jsx](src/main.jsx) → [src/App.jsx](src/App.jsx)
- **Database Schema**: [init_db.py](init_db.py)
- **Symptom Extraction**: Pattern matching in [app.py](app.py#L53-L89)

## Data Flow & Service Boundaries

### Authentication Flow
```
Login.jsx → POST /api/login → check_password_hash(users table) → session created → redirect to /dashboard
```

### Medical Recording & Report Generation Flow
```
Dashboard.jsx → /start-recording → saves WebRTC audio to recordings/ → /stop-recording 
→ uploads audio file → transcribe_audio_with_whisper() → extract_symptoms_from_transcript()
→ /generate_report → produces report in reports/ directory
```

### Appointment Booking Flow
```
BookAppointment.jsx → POST /api/book-appointment → token generated → appointments table stored
→ /api/lookup-appointment (by token) → doctor reviews & updates status
```

## Essential Code Patterns & Conventions

### Database Connections
- Always use **absolute path** for DB: `DB_PATH = os.path.join(BASE_DIR, "database.db")`
- All connections use: `conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row`
- **Why absolute path**: prevents corruption from relative path issues when Flask serves from `dist/`

### Session Management
- Flask session stored server-side (uses `app.secret_key = "mediassist_secret_key"`)
- Login sets session; logout clears it
- Auth check: `if 'user_id' not in session: return {"error": "Unauthorized"}`

### API Error Handling Pattern
All endpoints return JSON with consistent structure:
```python
if error_condition:
    return {"error": "Description"}, 400
return {"success": True, "data": result}, 200
```

### File Management
- **Recordings**: stored in `recordings/` (audio files from browser)
- **Reports**: stored in `reports/` with timestamp format: `report_YYYYMMDD_NNN_YYYYMMDD_HHMMSS.txt`
- **Static assets**: served from `dist/` folder after build

### Symptom Extraction
Uses **regex pattern matching** (NOT ML) in [app.py#L53-L89](app.py#L53-L89):
- Maps 15+ symptom keywords to regex patterns
- Extracts duration if mentioned (e.g., "fever for 3 days")
- Returns list of dicts: `{"name": "fever", "status": "present", "duration": "3 days"}`
- This is the core medical logic—modify patterns here to extend symptom detection

### Audio Transcription
```python
# OpenAI Whisper API (requires OPENAI_API_KEY env var)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# Falls back to mock transcript if API not configured
```

## Frontend Conventions

### React Router Structure
- Route `/`: Login (signup/signin/forgot password)
- Route `/dashboard`: Main consultation interface
- Route `/book-appointment`: Token-based appointment booking
- All routes redirect unknown paths to `/`

### Form Submission Pattern
```jsx
const handleSubmit = async (e) => {
  e.preventDefault()
  const formData = new FormData(e.target)
  const payload = { email: formData.get('email'), ... }
  const res = await fetch('/api/endpoint', { method: 'POST', body: JSON.stringify(payload) })
  const data = await res.json()
  if (!res.ok) { alert(data.error); return }
  // success logic
}
```

## Vite Development Server Configuration

[vite.config.js](vite.config.js) proxies these endpoints to Flask at `http://127.0.0.1:5000`:
- `/api/*` (all API routes)
- `/start-recording`, `/stop-recording`, `/generate_report` (non-/api routes)

**Important**: Without proxies, frontend API calls fail during dev. If adding new Flask endpoints, update `vite.config.js` proxy config.

## Integration Points & External Dependencies

| Component | Purpose | Config | Fallback |
|-----------|---------|--------|----------|
| OpenAI Whisper API | Audio transcription | `OPENAI_API_KEY` env var | Mock transcript (returns dummy text) |
| pydub | Audio format conversion (WAV/MP3) | Auto-imported | Skips conversion if unavailable |
| Lucide React | UI icons (Login, Dashboard) | `npm install lucide-react` | Already in package.json |

## Common Tasks & Commands

| Task | Command |
|------|---------|
| Install packages | `npm install` |
| Dev server (frontend) | `npm run dev` |
| Build for production | `npm run build` |
| Run Flask backend | `python app.py` |
| Init/verify database | `python init_db.py` |
| Check database | `python check_database.py` |
| Stop Node processes | `Get-Process node \| Stop-Process -Force` |

## Project Structure Reference

```
app.py                    # All Flask routes, transcription, symptom extraction
init_db.py               # Database schema (users, appointments, patients)
src/App.jsx              # React router config
src/pages/
  ├── Login.jsx          # Auth (signup/signin/forgot password)
  ├── Dashboard.jsx      # Main consultation UI
  └── BookAppointment.jsx # Token-based appointment booking
vite.config.js           # Dev server + API proxies
recordings/              # Stored audio files
reports/                 # Generated medical reports
```

## Debugging Notes

- **Flask not starting**: Check `OPENAI_API_KEY` env var, DB path, and port 5000 availability
- **Frontend API calls fail**: Ensure `npm run dev` is running AND `python app.py` is running; verify `vite.config.js` proxies match endpoint paths
- **Audio transcription fails**: Check `OPENAI_API_KEY` is set; system falls back to mock data if missing
- **Database locked**: Use absolute path in DB_PATH; check for concurrent connections
- **pydub import errors**: Audio conversion skipped gracefully; not required for basic functionality
