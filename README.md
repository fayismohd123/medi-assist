# MediAssist - React Frontend

Full-stack application with a Flask API backend and a React (Vite) frontend.


## Project Structure

```
MEDI-ASSIST/
├── src/
│   ├── pages/
│   │   ├── Login.jsx          # Login page component
│   │   ├── Login.css          # Login page styles
│   │   ├── Dashboard.jsx      # Dashboard page component
│   │   └── Dashboard.css     # Dashboard page styles
│   ├── App.jsx                # Main app component with routing
│   ├── main.jsx               # React entry point
│   └── index.css              # Global styles
├── app.py                     # Flask backend (updated to serve React)
├── package.json               # React dependencies
├── vite.config.js            # Vite configuration
└── index.html                # HTML template
```

## Setup Instructions

### 1. Install Dependencies

```bash
npm install
```

### 2. Development Mode

Run the React development server (with proxy to Flask backend):

```bash
npm run dev
```

The React app will be available at `http://localhost:3000`

### 3. Production Build

Build the React app for production:

```bash
npm run build
```

This will create a `dist` folder with the production build.

### 4. Run Flask Backend

The Flask backend should be configured to serve the React build from the `dist` folder:

```bash
python app.py
```

The Flask server will run on `http://127.0.0.1:5000`


## API Endpoints

The Flask backend provides the following API endpoints:

- `POST /api/login` - User login
- `POST /api/signup` - User registration
- `POST /api/forgot-password` - Password reset
- `GET /api/logout` - User logout
- `GET /api/user-info` - Get current user info
- `POST /api/register-patient` - Register a new patient
- `GET /api/lookup-patient` - Lookup patient by phone
- `POST /start-recording` - Start audio recording
- `POST /stop-recording` - Stop audio recording
- `POST /generate_report` - Generate medical report

## Development Notes

- The React app uses Vite as the build tool
- React Router is used for client-side routing
- Lucide React is used for icons 
- The Flask backend serves the React build in production mode

