import { useState } from 'react';
import { Send, CheckCircle, AlertCircle, UserPlus, History, Loader2 } from 'lucide-react';
import { patientAPI } from '../../api/api';
import PatientRegistration from '../PatientRegistration/PatientRegistration';
import './PatientLookup.css';

const PatientLookup = ({ onPatientSelect, selectedPatient }) => {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [patients, setPatients] = useState([]);
  const [error, setError] = useState('');
  const [showRegister, setShowRegister] = useState(false);

  const handleLookup = async () => {
    if (!phoneNumber.trim() || phoneNumber.length < 10) {
      setError('Please enter a valid phone number');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await patientAPI.lookup(phoneNumber);
      const patientList = response.data.patients || [];

      if (patientList.length === 0) {
        setPatients([]);
        setError(`No patient found with number ${phoneNumber}`);
      } else if (patientList.length === 1) {
        setPatients([]);
        onPatientSelect(patientList[0]);
      } else {
        setPatients(patientList);
      }
    } catch (err) {
      setError('Lookup failed');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      handleLookup();
    }
  };

  const selectPatient = (patient) => {
    onPatientSelect(patient);
    setPatients([]);
  };

  return (
    <div className="patient-lookup">
      <div className="input-container">
        <input
          type="tel"
          value={phoneNumber}
          onChange={(e) => {
            setPhoneNumber(e.target.value.replace(/[^0-9]/g, ''));
            setError('');
          }}
          onKeyPress={handleKeyPress}
          placeholder="Patient Phone Number"
          pattern="[0-9]*"
          inputMode="numeric"
        />
        <button 
          onClick={handleLookup} 
          className="lookup-btn"
          disabled={loading}
        >
          {loading ? (
            <Loader2 size={16} className="loading-spinner" />
          ) : (
            <Send size={16} />
          )}
        </button>
      </div>

      {error && (
        <div className="error-container">
          <div className="error-message">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
          <button 
            onClick={() => setShowRegister(true)} 
            className="add-patient-button"
          >
            <UserPlus size={20} />
            <span>Add New Patient</span>
          </button>
        </div>
      )}

      {selectedPatient && !error && (
        <div className="success-message">
          <div className="success-message-content">
            <CheckCircle size={16} />
            <span>Patient: {selectedPatient.name}</span>
          </div>
          <div className="button-container">
            <button className="history-button">
              <History size={16} />
              <span>View History</span>
            </button>
            <button 
              onClick={() => setShowRegister(true)}
              className="add-patient-button"
            >
              <UserPlus size={20} />
              <span>Add New Patient</span>
            </button>
          </div>
        </div>
      )}

      {patients.length > 0 && (
        <div className="patient-list">
          {patients.map((patient) => (
            <div 
              key={patient.id} 
              className="patient-item"
              onClick={() => selectPatient(patient)}
            >
              <div>
                <strong>{patient.name || 'Unknown'}</strong>
                {patient.age && <span style={{ display: 'block', fontSize: '0.85rem', color: 'rgba(191,219,254,0.7)' }}>Age: {patient.age}</span>}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'rgba(191,219,254,0.6)' }}>
                {new Date(patient.created_at).toLocaleString()}
              </div>
            </div>
          ))}
          <button 
            onClick={() => setShowRegister(true)}
            className="add-patient-button"
            style={{ marginTop: '0.6rem' }}
          >
            <UserPlus size={20} />
            <span>Add New Patient</span>
          </button>
        </div>
      )}

      {showRegister && (
        <PatientRegistration
          prefillPhone={phoneNumber}
          onClose={() => setShowRegister(false)}
          onSuccess={(patient) => {
            setShowRegister(false);
            onPatientSelect(patient);
            setError('');
          }}
        />
      )}
    </div>
  );
};

export default PatientLookup;
