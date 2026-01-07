import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Stethoscope,
  LogOut,
  Send,
  Mic,
  Pause,
  Play,
  FileText,
  CheckCircle,
  AlertCircle,
  History,
  UserPlus,
  Loader2
} from 'lucide-react'
import './Dashboard.css'

function Dashboard() {
  const navigate = useNavigate()
  const [doctorName, setDoctorName] = useState('Your Name')
  const [phoneNumber, setPhoneNumber] = useState('')
  const [patientInfo, setPatientInfo] = useState(null)
  const [patientList, setPatientList] = useState([])
  const [showPatientList, setShowPatientList] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [showRegisterForm, setShowRegisterForm] = useState(false)
  const [registerForm, setRegisterForm] = useState({ name: '', phone: '', age: '' })
  const [symptoms, setSymptoms] = useState([])
  const [transcript, setTranscript] = useState('')

  const mediaRecorderRef = useRef(null)
  const mediaStreamRef = useRef(null)
  const recordedChunksRef = useRef([])

  useEffect(() => {
    // Fetch doctor name from session or API
    fetch('/api/user-info')
      .then(res => {
        if (res.ok) {
          return res.json()
        }
        throw new Error('Not authenticated')
      })
      .then(data => {
        if (data && data.name) {
          setDoctorName(data.name)
        } else if (data && data.email) {
          // Fallback to email if name not available
          setDoctorName(data.email.split('@')[0])
        }
      })
      .catch(() => {
        // If not authenticated, redirect to login
        navigate('/')
      })
  }, [navigate])

  const handleLogout = async () => {
    try {
      await fetch('/api/logout')
      navigate('/')
    } catch (err) {
      navigate('/')
    }
  }

  const handleInput = (e) => {
    const value = e.target.value.replace(/[^0-9]/g, '')
    setPhoneNumber(value)
    setPatientInfo(null)
    setShowPatientList(false)
  }

  const lookupPatient = async () => {
    const phone = phoneNumber.trim()

    if (!phone) {
      showError('Please enter a phone number')
      return
    }

    if (phone.length < 10) {
      showError('Please enter a valid phone number')
      return
    }

    setIsLoading(true)
    try {
      const res = await fetch(`/api/lookup-patient?phone=${encodeURIComponent(phone)}`)
      const data = await res.json()
      setIsLoading(false)

      if (data && Array.isArray(data.patients) && data.patients.length > 0) {
        if (data.patients.length === 1) {
          showPatientFound(data.patients[0])
        } else {
          displayPatientList(data.patients)
        }
      } else {
        showPatientNotFound(phone)
      }
    } catch (err) {
      setIsLoading(false)
      showError('Lookup failed')
    }
  }

  const showPatientFound = (patient) => {
    const name = typeof patient === 'string' ? patient : (patient && patient.name ? patient.name : 'Unknown')
    setPatientInfo({ type: 'success', patient, name })
    setShowPatientList(false)
    enableControls()
  }

  const displayPatientList = (patients) => {
    setPatientList(patients)
    setShowPatientList(true)
    setPatientInfo(null)
    disableControls()
  }

  const selectPatient = (patient) => {
    if (patient && patient.phone) setPhoneNumber(patient.phone)
    showPatientFound(patient)
  }

  const showPatientNotFound = (phone) => {
    setPatientInfo({ type: 'error', message: `No patient found with number ${phone}`, phone })
    setShowPatientList(false)
    disableControls()
  }

  const showError = (message) => {
    setPatientInfo({ type: 'error', message })
    setShowPatientList(false)
    disableControls()
  }

  const enableControls = () => {
    // Controls are enabled by default, just ensure they're not disabled
  }

  const disableControls = () => {
    // This would disable controls, but we'll handle it via state
  }

  const startCapture = async (e) => {
    if (e) e.preventDefault()
    if (isRecording) return

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaStreamRef.current = stream
      recordedChunksRef.current = []

      // Get supported MIME type
      const options = { mimeType: 'audio/webm' }
      if (!MediaRecorder.isTypeSupported(options.mimeType)) {
        options.mimeType = 'audio/webm;codecs=opus'
        if (!MediaRecorder.isTypeSupported(options.mimeType)) {
          options.mimeType = 'audio/webm'
        }
      }

      const recorder = new MediaRecorder(stream, options)
      mediaRecorderRef.current = recorder

      recorder.ondataavailable = (ev) => {
        if (ev.data && ev.data.size > 0) {
          recordedChunksRef.current.push(ev.data)
          console.log(`Data chunk received: ${ev.data.size} bytes`)
        }
      }

      recorder.onerror = (ev) => {
        console.error('MediaRecorder error:', ev.error)
        showError('Recording error occurred')
      }

      recorder.onstop = async () => {
        console.log('Recording stopped. Chunks:', recordedChunksRef.current.length)
        
        if (recordedChunksRef.current.length === 0) {
          showError('No audio data recorded. Please try again.')
          return
        }

        const blob = new Blob(recordedChunksRef.current, {
          type: recordedChunksRef.current[0]?.type || 'audio/webm'
        })
        
        console.log(`Blob created: ${blob.size} bytes, type: ${blob.type}`)
        
        if (blob.size === 0) {
          showError('Recording is empty. Please try again.')
          return
        }

        const form = new FormData()
        const filename = `recording_${Date.now()}.webm`
        form.append('audio', blob, filename)

        try {
          console.log('Uploading recording...')
          const res = await fetch('/stop-recording', {
            method: 'POST',
            body: form
          })
          const data = await res.json()
          if (!res.ok) {
            showError(data.error || 'Stop recording failed')
          } else {
            console.log('Upload response', data)
            if (data.transcript) {
              setTranscript(data.transcript)
            }
            if (data.symptoms && Array.isArray(data.symptoms)) {
              setSymptoms(data.symptoms)
            }
          }
        } catch (err) {
          console.error('Upload error:', err)
          showError('Stop recording failed: ' + err.message)
        }

        if (mediaStreamRef.current) {
          mediaStreamRef.current.getTracks().forEach(t => t.stop())
          mediaStreamRef.current = null
        }
        mediaRecorderRef.current = null
        recordedChunksRef.current = []
      }

      // Start recording with timeslice to ensure data collection
      recorder.start(1000) // Collect data every 1 second
      setIsRecording(true)
      setIsPaused(false)
      setSymptoms([])
      setTranscript('')
      console.log('Recording started')
    } catch (err) {
      console.error(err)
      showError('Could not access microphone')
    }
  }

  const stopCapture = (e) => {
    if (e) e.preventDefault()
    if (!isRecording) return

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    setIsRecording(false)
    setIsPaused(false)
  }

  const togglePause = async () => {
    if (!isRecording) return

    // Stop the recording and save it
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      // Request final data chunk before stopping
      mediaRecorderRef.current.requestData()
      mediaRecorderRef.current.stop()
    }
    
    // The onstop handler will handle saving the recording
    setIsRecording(false)
    setIsPaused(false)
  }

  const handleGenerateReport = async (e) => {
    e.preventDefault()
    try {
      const res = await fetch('http://127.0.0.1:5000/generate_report', {
        method: 'POST'
      })
      const data = await res.json()
      if (res.ok) {
        alert('Report generated successfully')
      } else {
        alert(data.error || 'Failed to generate report')
      }
    } catch (err) {
      alert('Failed to generate report')
    }
  }

  const openRegisterForm = (prefillPhone = '') => {
    setRegisterForm({ name: '', phone: prefillPhone || phoneNumber, age: '' })
    setShowRegisterForm(true)
  }

  const closeRegisterForm = () => {
    setShowRegisterForm(false)
    setRegisterForm({ name: '', phone: '', age: '' })
  }

  const handleRegisterPatient = async (e) => {
    e.preventDefault()
    const { name, phone, age } = registerForm

    if (!name || !phone) {
      showError('Name and phone are required to register a patient')
      return
    }

    try {
      const res = await fetch('/api/register-patient', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, phone, age })
      })

      if (res.ok) {
        setPatientInfo({ type: 'success', message: `Patient registered: ${name}` })
        enableControls()
        setPhoneNumber(phone)
        closeRegisterForm()
        lookupPatient()
      } else {
        const err = await res.json()
        showError(err.error || 'Registration failed')
      }
    } catch (err) {
      showError('Registration failed')
    }
  }

  const viewHistory = () => {
    window.location.href = `/patient-history?phone=${phoneNumber}`
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isLoading) {
      lookupPatient()
    }
  }

  return (
    <div className="app">
      {/* Header */}
      <header>
        <div className="header-content">
          <div className="logo-container">
            <div className="logo-icon">
              <Stethoscope size={32} />
            </div>
            <div className="brand">
              <h1>MediAssist</h1>
              <p className="doctor-name">Dr. {doctorName}</p>
            </div>
          </div>
          <div className="header-actions">
            <button type="button" onClick={handleLogout} className="logout-button">
              <LogOut size={16} />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </header>

      {/* Two-column layout: sidebar + main content */}
      <div className="layout">
        <aside className="sidebar">
          <div className="patient-lookup">
            <div className="input-container">
              <input
                type="tel"
                value={phoneNumber}
                onChange={handleInput}
                onKeyPress={handleKeyPress}
                placeholder="Patient Phone Number"
                pattern="[0-9]*"
                inputMode="numeric"
                disabled={isLoading}
              />
              <button
                id="lookupBtn"
                className="lookup-btn"
                onClick={lookupPatient}
                disabled={isLoading}
              >
                {isLoading ? (
                  <Loader2 size={16} className="loading" />
                ) : (
                  <Send size={16} />
                )}
              </button>
            </div>

            {patientInfo && (
              <div id="patientInfo" className={`patient-info ${patientInfo.type === 'error' ? 'shake' : ''}`}>
                {patientInfo.type === 'success' && (
                  <div className="success-message">
                    <div className="success-message-content">
                      <CheckCircle size={16} />
                      <span>Patient: {patientInfo.name || patientInfo.patient?.name}</span>
                    </div>
                    <div className="button-container">
                      <button
                        type="button"
                        onClick={viewHistory}
                        className="history-button"
                      >
                        <History size={16} />
                        <span>View History</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => openRegisterForm(phoneNumber)}
                        className="add-patient-button"
                      >
                        <UserPlus size={20} />
                        <span>Add New Patient</span>
                      </button>
                    </div>
                  </div>
                )}
                {patientInfo.type === 'error' && (
                  <div className="error-container">
                    <div className="error-message">
                      <AlertCircle size={16} />
                      <span>{patientInfo.message}</span>
                    </div>
                    {patientInfo.phone && (
                      <button
                        type="button"
                        onClick={() => openRegisterForm(patientInfo.phone)}
                        className="add-patient-button"
                      >
                        <UserPlus size={20} />
                        <span>Add New Patient</span>
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}

            {showPatientList && patientList.length > 0 && (
              <div id="patientList" className="patient-list">
                {patientList.map((p) => (
                  <div
                    key={p.id}
                    className="patient-item"
                    onClick={() => selectPatient(p)}
                  >
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <strong>{p.name || 'Unknown'}</strong>
                      {p.age && (
                        <span style={{ fontSize: '0.85rem', color: 'rgba(191,219,254,0.7)' }}>
                          Age: {p.age}
                        </span>
                      )}
                    </div>
                    {p.created_at && (
                      <div style={{ fontSize: '0.8rem', color: 'rgba(191,219,254,0.6)' }}>
                        {new Date(p.created_at).toLocaleString()}
                      </div>
                    )}
                  </div>
                ))}
                <div style={{ marginTop: '0.6rem' }}>
                  <button
                    type="button"
                    onClick={() => openRegisterForm(phoneNumber)}
                    className="add-patient-button"
                  >
                    <UserPlus size={20} />
                    <span style={{ marginLeft: '0.5rem' }}>Add New Patient</span>
                  </button>
                </div>
              </div>
            )}

            {showRegisterForm && (
              <div id="registerPatientContainer" style={{ display: 'block', marginTop: '0.75rem' }}>
                <form onSubmit={handleRegisterPatient}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    <input
                      value={registerForm.name}
                      onChange={(e) => setRegisterForm({ ...registerForm, name: e.target.value })}
                      placeholder="Patient Name"
                      required
                      style={{
                        padding: '0.65rem',
                        borderRadius: '0.5rem',
                        border: '1px solid rgba(96,165,250,0.2)',
                        background: 'rgba(30,58,138,0.4)',
                        color: 'white'
                      }}
                    />
                    <input
                      value={registerForm.phone}
                      onChange={(e) => setRegisterForm({ ...registerForm, phone: e.target.value })}
                      placeholder="Phone Number"
                      pattern="[0-9]*"
                      inputMode="numeric"
                      required
                      style={{
                        padding: '0.65rem',
                        borderRadius: '0.5rem',
                        border: '1px solid rgba(96,165,250,0.2)',
                        background: 'rgba(30,58,138,0.4)',
                        color: 'white'
                      }}
                    />
                    <input
                      value={registerForm.age}
                      onChange={(e) => setRegisterForm({ ...registerForm, age: e.target.value })}
                      placeholder="Age (optional)"
                      type="number"
                      min="0"
                      style={{
                        padding: '0.65rem',
                        borderRadius: '0.5rem',
                        border: '1px solid rgba(96,165,250,0.2)',
                        background: 'rgba(30,58,138,0.4)',
                        color: 'white'
                      }}
                    />
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button type="submit" className="add-patient-button">
                        Register Patient
                      </button>
                      <button
                        type="button"
                        onClick={closeRegisterForm}
                        className="add-patient-button"
                        style={{ background: '#374151' }}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </form>
              </div>
            )}
          </div>
        </aside>

        <div className="content">
          {/* Main Content */}
          <main>
            <div className="main-layout">
              <div className="controls-section">
                <div className="controls">
                  <div className="controls-wrapper">
                    <form onSubmit={startCapture}>
                      <button
                        type="submit"
                        className={`mic-button ${isRecording && !isPaused ? 'recording' : ''}`}
                        disabled={!patientInfo || patientInfo.type !== 'success'}
                      >
                        <Mic size={64} />
                        {isRecording && !isPaused && <div className="ping-animation"></div>}
                      </button>
                    </form>

                    <form onSubmit={stopCapture}>
                      <button
                        type="button"
                        className="pause-button"
                        onClick={togglePause}
                        disabled={!isRecording}
                      >
                        {isPaused ? <Play size={32} /> : <Pause size={32} />}
                      </button>
                    </form>
                  </div>

                  <form onSubmit={handleGenerateReport}>
                    <button
                      type="submit"
                      className="report-button"
                      disabled={!patientInfo || patientInfo.type !== 'success'}
                    >
                      <FileText size={24} />
                      <span>Generate Report</span>
                    </button>
                  </form>
                </div>
              </div>

              <div className="symptoms-section">
                <div className="symptoms-box">
                  <h3 className="symptoms-title">Symptoms (Real-time)</h3>
                  {transcript && (
                    <div className="transcript-display">
                      <strong>Transcript:</strong>
                      <p>{transcript}</p>
                    </div>
                  )}
                  {symptoms.length > 0 ? (
                    <div className="symptoms-list">
                      {symptoms.map((symptom, index) => (
                        <div key={index} className={`symptom-item ${symptom.status}`}>
                          <div className="symptom-name">
                            {symptom.symptom}
                            <span className={`symptom-status ${symptom.status}`}>
                              ({symptom.status})
                            </span>
                          </div>
                          {symptom.duration && symptom.duration !== 'not specified' && (
                            <div className="symptom-duration">{symptom.duration}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="no-symptoms">
                      {isRecording ? 'Recording... Symptoms will appear here.' : 'No symptoms detected yet.'}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>

      {/* Footer */}
      <footer>
        <p>&copy; 2025 MediAssist. All rights reserved.</p>
      </footer>
    </div>
  )
}

export default Dashboard
