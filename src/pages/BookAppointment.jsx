import React, { useState } from 'react'
import { Calendar, Mail, Phone, User, Copy, CheckCircle } from 'lucide-react'
import './BookAppointment.css'

export default function BookAppointment() {
  const [formData, setFormData] = useState({
    patient_name: '',
    patient_dob: '',
    patient_email: '',
    patient_phone: '',
    appointment_date: ''
  })

  const [token, setToken] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setToken('')
    setSuccess(false)

    try {
      const response = await fetch('/api/book-appointment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })

      const data = await response.json()

      if (response.ok) {
        setToken(data.token)
        setSuccess(true)
        // Reset form
        setFormData({
          patient_name: '',
          patient_dob: '',
          patient_email: '',
          patient_phone: '',
          appointment_date: ''
        })
      } else {
        setError(data.error || 'Booking failed')
      }
    } catch (err) {
      setError('Network error: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const copyToken = () => {
    navigator.clipboard.writeText(token)
    alert('Token copied to clipboard!')
  }

  return (
    <div className="book-appointment-container">
      <div className="booking-card">
        <h1>📅 Book Your Appointment</h1>
        <p className="subtitle">Enter your details to schedule a consultation</p>

        {success && token && (
          <div className="success-box">
            <CheckCircle size={24} />
            <h2>Appointment Booked Successfully! ✅</h2>
            <p>Your appointment token has been generated. Please save it for your consultation.</p>
            
            <div className="token-display">
              <span className="token-text">{token}</span>
              <button className="copy-btn" onClick={copyToken}>
                <Copy size={18} /> Copy Token
              </button>
            </div>
            
            <p className="token-info">
              📧 A confirmation has been sent to <strong>{formData.patient_email}</strong>
            </p>
            
            <button 
              className="btn-primary"
              onClick={() => setSuccess(false)}
            >
              Book Another Appointment
            </button>
          </div>
        )}

        {!success && (
          <form onSubmit={handleSubmit} className="booking-form">
            {error && <div className="error-message">{error}</div>}

            <div className="form-group">
              <label htmlFor="name">
                <User size={18} /> Full Name
              </label>
              <input
                id="name"
                type="text"
                name="patient_name"
                placeholder="Enter your full name"
                value={formData.patient_name}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="dob">
                <Calendar size={18} /> Date of Birth
              </label>
              <input
                id="dob"
                type="date"
                name="patient_dob"
                value={formData.patient_dob}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">
                <Mail size={18} /> Email Address
              </label>
              <input
                id="email"
                type="email"
                name="patient_email"
                placeholder="your@email.com"
                value={formData.patient_email}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="phone">
                <Phone size={18} /> Phone Number
              </label>
              <input
                id="phone"
                type="tel"
                name="patient_phone"
                placeholder="+91 98765 43210"
                value={formData.patient_phone}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="date">
                <Calendar size={18} /> Appointment Date
              </label>
              <input
                id="date"
                type="date"
                name="appointment_date"
                value={formData.appointment_date}
                onChange={handleChange}
                required
              />
            </div>

            <button 
              type="submit" 
              className="btn-primary"
              disabled={loading}
            >
              {loading ? 'Booking...' : 'Book Appointment'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
