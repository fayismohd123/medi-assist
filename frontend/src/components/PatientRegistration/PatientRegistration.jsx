import { useState } from 'react';
import { UserPlus, X } from 'lucide-react';
import { patientAPI } from '../../api/api';
import './PatientRegistration.css';

const PatientRegistration = ({ prefillPhone, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    name: '',
    phone: prefillPhone || '',
    age: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    if (name === 'phone') {
      setFormData({ ...formData, [name]: value.replace(/[^0-9]/g, '') });
    } else if (name === 'age') {
      setFormData({ ...formData, [name]: value.replace(/[^0-9]/g, '') });
    } else {
      setFormData({ ...formData, [name]: value });
    }
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!formData.name || !formData.phone) {
      setError('Name and phone are required');
      return;
    }

    setLoading(true);
    try {
      const response = await patientAPI.register(formData.name, formData.phone, formData.age);
      onSuccess({ name: formData.name, phone: formData.phone, age: formData.age ? parseInt(formData.age) : null });
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="patient-registration-overlay">
      <div className="patient-registration-modal">
        <div className="modal-header">
          <h3>Register New Patient</h3>
          <button onClick={onClose} className="close-button">
            <X size={20} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="registration-form">
          <div className="form-group">
            <label htmlFor="regName">Patient Name</label>
            <input
              id="regName"
              name="name"
              type="text"
              placeholder="Patient Name"
              value={formData.name}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="regPhone">Phone Number</label>
            <input
              id="regPhone"
              name="phone"
              type="tel"
              placeholder="Phone Number"
              pattern="[0-9]*"
              inputMode="numeric"
              value={formData.phone}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="regAge">Age (optional)</label>
            <input
              id="regAge"
              name="age"
              type="number"
              placeholder="Age"
              min="0"
              value={formData.age}
              onChange={handleChange}
            />
          </div>
          {error && <div className="error-message">{error}</div>}
          <div className="form-actions">
            <button type="button" onClick={onClose} className="cancel-button">
              Cancel
            </button>
            <button type="submit" className="submit-button" disabled={loading}>
              {loading ? 'Registering...' : (
                <>
                  <UserPlus size={20} />
                  <span>Register Patient</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PatientRegistration;
