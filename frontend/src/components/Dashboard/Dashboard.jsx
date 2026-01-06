import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { LogOut, Stethoscope } from 'lucide-react';
import PatientLookup from '../PatientLookup/PatientLookup';
import AudioRecorder from '../AudioRecorder/AudioRecorder';
import './Dashboard.css';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const [selectedPatient, setSelectedPatient] = useState(null);

  const handleLogout = async () => {
    await logout();
    window.location.href = '/login';
  };

  return (
    <div className="app">
      <header>
        <div className="header-content">
          <div className="logo-container">
            <div className="logo-icon">
              <Stethoscope size={32} />
            </div>
            <div className="brand">
              <h1>MediAssist</h1>
              <p className="doctor-name">Dr. {user?.name || 'Your Name'}</p>
            </div>
          </div>
          <div className="header-actions">
            <button onClick={handleLogout} className="logout-button">
              <LogOut size={16} />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </header>

      <div className="layout">
        <aside className="sidebar">
          <PatientLookup 
            onPatientSelect={setSelectedPatient}
            selectedPatient={selectedPatient}
          />
        </aside>

        <div className="content">
          <main>
            <div className="container">
              <AudioRecorder 
                patient={selectedPatient}
              />
            </div>
          </main>
        </div>
      </div>

      <footer>
        <p>&copy; 2025 MediAssist. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default Dashboard;
