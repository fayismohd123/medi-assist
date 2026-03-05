import React, { useState, useEffect } from 'react'
import { Mic, Square, FileText, LogOut, ChevronRight, Activity } from 'lucide-react'
import './Dashboard.css'

export default function Dashboard() {
  const [tokenInput, setTokenInput] = useState('')
  const [currentAppointment, setCurrentAppointment] = useState(null)
  const [lookupError, setLookupError] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [mediaRecorder, setMediaRecorder] = useState(null)
  const [symptoms, setSymptoms] = useState([])
  const [transcript, setTranscript] = useState('')
  const [transcribedText, setTranscribedText] = useState('')
  const [reportGenerated, setReportGenerated] = useState(false)
  const [reportContent, setReportContent] = useState('')
  const [reportFilename, setReportFilename] = useState('')
  const [doctorName, setDoctorName] = useState('')
  const [appointments, setAppointments] = useState([])
  const [recordingFilename, setRecordingFilename] = useState('')
  const [predictedDisease, setPredictedDisease] = useState('')
  const [confidenceScore, setConfidenceScore] = useState(0)
  const [isPredicting, setIsPredicting] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [medicines, setMedicines] = useState([])
  const [medicineInput, setMedicineInput] = useState('')
  const [medicineList, setMedicineList] = useState([])
  const [showMedicineDropdown, setShowMedicineDropdown] = useState(false)
  const [currentMedicine, setCurrentMedicine] = useState({
    name: '',
    dosage: '',
    frequency: '',
    duration: ''
  })
  const [isSavingMedicines, setIsSavingMedicines] = useState(false)
  const [physicianDetails, setPhysicianDetails] = useState({
    physician_name: '',
    physician_speciality: '',
    physician_contact: ''
  })

  useEffect(() => {
    fetch('/api/user-info')
      .then(res => res.ok ? res.json() : Promise.reject())
      .then(data => {
        setDoctorName(data.name || data.email?.split('@')[0] || 'Doctor')
        setPhysicianDetails({
          physician_name: data.name || '',
          physician_speciality: data.speciality || '',
          physician_contact: data.contact || ''
        })
      })
      .catch(() => window.location.href = '/')
  }, [])

  useEffect(() => {
    fetch('/api/appointments')
      .then(res => res.ok ? res.json() : Promise.reject())
      .then(data => {
        if (data.success) {
          setAppointments(data.appointments)
        }
      })
      .catch(err => console.error('Failed to fetch appointments:', err))
  }, [])

  useEffect(() => {
    fetch('/api/get-medicines')
      .then(res => res.ok ? res.json() : Promise.reject())
      .then(data => {
        if (data.success) {
          setMedicineList(data.medicines)
        }
      })
      .catch(err => console.error('Failed to fetch medicines:', err))
  }, [])

  useEffect(() => {
    let interval
    if (isRecording) {
      interval = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)
    }
    return () => clearInterval(interval)
  }, [isRecording])

  const handleTokenLookup = async (e) => {
    e.preventDefault()
    setLookupError('')
    setSymptoms([])
    setTranscript('')
    setReportGenerated(false)

    if (!tokenInput.trim()) {
      setLookupError('Please enter a token')
      return
    }

    try {
      const response = await fetch('/api/lookup-appointment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: tokenInput.toUpperCase() })
      })

      const data = await response.json()

      if (response.ok) {
        setCurrentAppointment(data.appointment)
        setTokenInput('')
      } else {
        setLookupError(data.error || 'Appointment not found')
        setCurrentAppointment(null)
      }
    } catch (err) {
      setLookupError('Network error: ' + err.message)
    }
  }

  const handleSelectAppointment = (appointment) => {
    setCurrentAppointment(appointment)
    setSymptoms([])
    setTranscript('')
    setTranscribedText('')
    setReportGenerated(false)
    setLookupError('')
    setPredictedDisease('')
    setConfidenceScore(0)
    setMedicines([])
    setMedicineInput('')
    setCurrentMedicine({ name: '', dosage: '', frequency: '', duration: '' })
  }

  const getFilteredMedicines = (query) => {
    const normalizedQuery = query.trim().toLowerCase()
    if (!normalizedQuery) {
      return []
    }
    return medicineList
      .filter(med => med.toLowerCase().includes(normalizedQuery))
      .slice(0, 5)
  }

  const normalizeDosage = (value) => {
    const trimmed = value.trim()
    if (!trimmed) {
      return ''
    }
    if (/nos$/i.test(trimmed)) {
      return trimmed
    }
    if (/^\d+(\.\d+)?$/.test(trimmed)) {
      return `${trimmed} Nos`
    }
    return trimmed
  }

  const normalizeDuration = (value) => {
    const trimmed = value.trim()
    if (!trimmed) {
      return ''
    }
    if (trimmed.includes('ദിവസം') || trimmed.toLowerCase().includes('day')) {
      return trimmed
    }
    if (/^\d+(\.\d+)?$/.test(trimmed)) {
      return `${trimmed} ദിവസം`
    }
    return trimmed
  }

  const normalizeFrequency = (value) => {
    const trimmed = value.trim()
    if (!trimmed) {
      return ''
    }

    const lower = trimmed.toLowerCase()
    const timeOfDayMap = {
      morning: 'രാവിലെ',
      night: 'രാത്രി',
      evening: 'വൈകുന്നേരം',
      afternoon: 'ഉച്ചയ്ക്ക്',
      noon: 'ഉച്ചയ്ക്ക്',
      bedtime: 'രാത്രി'
    }

    if (timeOfDayMap[lower]) {
      return timeOfDayMap[lower]
    }

    if (/^\d+$/.test(lower)) {
      const timesPerDay = parseInt(lower, 10)
      if (timesPerDay === 1) {
        return 'ദിവസവും ഒരു തവണ'
      }
      if (timesPerDay > 1) {
        if (24 % timesPerDay === 0) {
          return `${24 / timesPerDay} മണിക്കൂർ ഇടവിട്ട്`
        }
        return `ദിവസത്തിൽ ${timesPerDay} തവണ`
      }
    }

    return trimmed
  }

  const applyDosage = (value) => {
    setCurrentMedicine(prev => ({ ...prev, dosage: normalizeDosage(value) }))
  }

  const applyDuration = (value) => {
    setCurrentMedicine(prev => ({ ...prev, duration: normalizeDuration(value) }))
  }

  const applyFrequency = (value) => {
    setCurrentMedicine(prev => ({ ...prev, frequency: normalizeFrequency(value) }))
  }

  const handleMedicineSearch = (e) => {
    const value = e.target.value
    setMedicineInput(value)
    setShowMedicineDropdown(value.length > 0)
  }

  const handleMedicineKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      const matches = getFilteredMedicines(medicineInput)
      if (matches.length > 0) {
        handleSelectMedicineFromDropdown(matches[0])
        return
      }
      if (medicineInput.trim()) {
        setCurrentMedicine(prev => ({ ...prev, name: medicineInput.trim() }))
        setShowMedicineDropdown(false)
      }
    }
  }

  const handleSelectMedicineFromDropdown = (medicineName) => {
    setCurrentMedicine(prev => ({ ...prev, name: medicineName }))
    setMedicineInput(medicineName)
    setShowMedicineDropdown(false)
  }

  const handleAddMedicine = () => {
    const normalizedMedicine = {
      ...currentMedicine,
      dosage: normalizeDosage(currentMedicine.dosage),
      duration: normalizeDuration(currentMedicine.duration),
      frequency: normalizeFrequency(currentMedicine.frequency)
    }

    if (!normalizedMedicine.name || !normalizedMedicine.duration || !normalizedMedicine.frequency) {
      alert('Please fill in medicine name, dosage, and frequency')
      return
    }

    const newMedicine = { ...normalizedMedicine }
    setMedicines([...medicines, newMedicine])
    setCurrentMedicine({ name: '', dosage: '', frequency: '', duration: '' })
    setMedicineInput('')
  }

  const handleRemoveMedicine = (index) => {
    setMedicines(medicines.filter((_, idx) => idx !== index))
  }

  const handleSaveMedicines = async () => {
    if (!currentAppointment) {
      alert('Please select an appointment first')
      return
    }

    if (medicines.length === 0) {
      alert('Please add at least one medicine')
      return
    }

    try {
      setIsSavingMedicines(true)
      const response = await fetch('/api/save-medicines', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          appointment_id: currentAppointment.id,
          medicines: medicines
        })
      })

      const data = await response.json()

      if (response.ok) {
        alert(`Saved ${medicines.length} medicine(s) successfully!`)
      } else {
        alert('Error saving medicines: ' + data.error)
      }
    } catch (err) {
      alert('Error: ' + err.message)
    } finally {
      setIsSavingMedicines(false)
    }
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      const audioChunks = []

      recorder.ondataavailable = (event) => {
        audioChunks.push(event.data)
      }

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })
        console.log('Recording stopped, audio blob size:', audioBlob.size)
        
        // Upload recording to backend
        try {
          setIsTranscribing(true)
          const formData = new FormData()
          formData.append('audio', audioBlob, 'recording.webm')
          
          const response = await fetch('/stop-recording', {
            method: 'POST',
            body: formData
          })
          
          const data = await response.json()
          
          if (response.ok) {
            console.log('Recording uploaded successfully:', data)
            console.log('Response symptoms:', data.detected_symptoms)
            setRecordingFilename(data.audio_file)
            setTranscript(data.transcript)
            setTranscribedText(data.transcript)
            // ✅ Handle detected_symptoms from backend
            if (data.detected_symptoms && Array.isArray(data.detected_symptoms)) {
              console.log('Setting symptoms:', data.detected_symptoms)
              // Extract symptoms list from the response object if nested
              if (data.detected_symptoms.symptoms) {
                setSymptoms(data.detected_symptoms.symptoms)
              } else {
                setSymptoms(data.detected_symptoms)
              }
              
              // ✅ Call disease prediction endpoint with extracted symptoms
              console.log('Calling predict-disease endpoint...')
              setIsPredicting(true)
              try {
                const predictResponse = await fetch('/api/predict-disease', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({
                    symptoms: Array.isArray(data.detected_symptoms) ? data.detected_symptoms : data.detected_symptoms.symptoms || []
                  })
                })
                
                const predictData = await predictResponse.json()
                console.log('Disease prediction response:', predictData)
                
                if (predictResponse.ok && predictData.success) {
                  setPredictedDisease(predictData.predicted_disease)
                  setConfidenceScore(predictData.confidence)
                  console.log(`Disease prediction: ${predictData.predicted_disease} (${predictData.confidence})`)
                } else {
                  console.warn('Disease prediction failed:', predictData.error)
                  setPredictedDisease('')
                  setConfidenceScore(0)
                }
              } catch (err) {
                console.error('Error calling predict-disease:', err)
                setPredictedDisease('')
                setConfidenceScore(0)
              } finally {
                setIsPredicting(false)
              }
            } else {
              console.warn('No symptoms found in response')
              setSymptoms([])
              setPredictedDisease('')
              setConfidenceScore(0)
            }
            alert('Recording processed successfully!')
          } else {
            alert('Error uploading recording: ' + data.error)
          }
        } catch (err) {
          alert('Error uploading recording: ' + err.message)
        } finally {
          setIsTranscribing(false)
        }
      }

      setMediaRecorder(recorder)
      recorder.start()
      setIsRecording(true)
      setRecordingTime(0)
    } catch (err) {
      alert('Error accessing microphone: ' + err.message)
    }
  }

  const stopRecording = () => {
    if (mediaRecorder) {
      mediaRecorder.stop()
      mediaRecorder.stream.getTracks().forEach(track => track.stop())
      setIsRecording(false)
    }
  }

  const generateReport = async () => {
    if (!currentAppointment) {
      alert('Please select an appointment first')
      return
    }

    try {
      const response = await fetch('/generate_report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          appointment_id: currentAppointment.id,
          symptoms: symptoms,
          transcript: transcribedText,
          recording_filename: recordingFilename,
          notes: transcript,
          predicted_disease: predictedDisease,
          confidence: confidenceScore,
          physician_name: physicianDetails.physician_name,
          physician_speciality: physicianDetails.physician_speciality,
          physician_contact: physicianDetails.physician_contact
        })
      })

      const data = await response.json()

      if (response.ok) {
        setReportGenerated(true)
        setReportContent('Report generated successfully as PDF')
        setReportFilename(data.report_filename)
        await fetch(`/api/update-appointment/${currentAppointment.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            status: 'completed',
            consultation_notes: transcript,
            physician_name: physicianDetails.physician_name,
            physician_speciality: physicianDetails.physician_speciality,
            physician_contact: physicianDetails.physician_contact
          })
        })
      } else {
        alert('Error generating report: ' + data.error)
      }
    } catch (err) {
      alert('Error: ' + err.message)
    }
  }

  const handleLogout = async () => {
    await fetch('/api/logout')
    window.location.href = '/'
  }

  return (
    <div className="dashboard-wrapper">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-content">
          <div>
            <h1>MediAssist</h1>
            <p>Welcome, Dr. {doctorName}</p>
          </div>
          <button className="btn-logout" onClick={handleLogout}>
            <LogOut size={20} /> Logout
          </button>
        </div>
      </div>

      {/* Main 3-Column Layout */}
      <div className="dashboard-container">
        {/* LEFT SIDEBAR - Patient Appointment Selection */}
        <div className="left-panel">
          <div className="panel-header">
            <h2>Patients</h2>
            <span className="badge">{appointments.length}</span>
          </div>

          <div className="appointments-list">
            {appointments.length > 0 ? (
              appointments.map(apt => (
                <div
                  key={apt.id}
                  className={`appointment-card ${currentAppointment?.id === apt.id ? 'active' : ''}`}
                  onClick={() => handleSelectAppointment(apt)}
                >
                  <div className="apt-name">{apt.patient_name}</div>
                  <div className="apt-token">{apt.token}</div>
                  <div className="apt-date">{apt.appointment_date}</div>
                </div>
              ))
            ) : (
              <p className="no-appointments">No appointments</p>
            )}
          </div>

          <div className="search-section">
            <h3>Search by Token</h3>
            <form onSubmit={handleTokenLookup} className="search-form">
              <input
                type="text"
                placeholder="Enter token"
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value.toUpperCase())}
              />
              <button type="submit">Search</button>
            </form>
            {lookupError && <div className="error">{lookupError}</div>}
          </div>
        </div>

        {/* CENTER - Recording & Consultation */}
        <div className="center-panel">
          {currentAppointment ? (
            <>
              <div className="appointment-header">
                <div>
                  <h2>{currentAppointment.patient_name}</h2>
                  <p className="token-badge">{currentAppointment.token}</p>
                </div>
                <div className="appointment-meta">
                  <div className="meta-item">
                    <span className="label">Date:</span>
                    <span className="value">{currentAppointment.appointment_date}</span>
                  </div>
                  <div className="meta-item">
                    <span className="label">DOB:</span>
                    <span className="value">{currentAppointment.patient_dob}</span>
                  </div>
                </div>
              </div>

              <div className="consultation-section">
                <h3>Consultation Recording</h3>
                <div className="recording-controls">
                  {!isRecording ? (
                    <button className="btn-record" onClick={startRecording}>
                      <Mic size={20} /> Start Recording
                    </button>
                  ) : (
                    <>
                      <button className="btn-recording" onClick={stopRecording}>
                        <Square size={20} /> Stop Recording
                      </button>
                      <div className="recording-timer">{formatTime(recordingTime)}</div>
                    </>
                  )}
                </div>

                <div className="transcript-section">
                  <div className="transcript-header">
                    <label>Consultation Notes</label>
                    {isTranscribing && (
                      <div className="transcribing-indicator">
                        <span className="spinner" />
                        <span>Transcribing...</span>
                      </div>
                    )}
                  </div>
                  <textarea
                    value={transcript}
                    onChange={(e) => setTranscript(e.target.value)}
                    placeholder="Enter consultation notes..."
                    rows="2"
                  />
                </div>

                {/* Medicines section moved here */}
                <div className="medicines-section">
                  <label>Prescribed Medicines</label>

                  {/* Medicine Input Form */}
                  <div className="medicine-form">
                    <div className="form-group">
                      <input
                        type="text"
                        placeholder="Type medicine..."
                        value={medicineInput}
                        onChange={handleMedicineSearch}
                        onKeyDown={handleMedicineKeyDown}
                        className="medicine-search"
                      />
                      {showMedicineDropdown && medicineInput.length > 0 && (
                        <div className="medicine-dropdown">
                          {getFilteredMedicines(medicineInput)
                            .map((med, idx) => (
                              <div
                                key={idx}
                                className="dropdown-item"
                                onClick={() => handleSelectMedicineFromDropdown(med)}
                              >
                                {med}
                              </div>
                            ))}
                        </div>
                      )}
                    </div>

                    <div className="form-row">
                      <input
                        type="text"
                        placeholder="Dosage (e.g., 1,1/2)"
                        value={currentMedicine.dosage}
                        onChange={(e) => setCurrentMedicine(prev => ({ ...prev, dosage: e.target.value }))}
                        onBlur={(e) => applyDosage(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault()
                            applyDosage(e.target.value)
                          }
                        }}
                        className="form-input"
                      />
                      <input
                        type="text"
                        placeholder="Frequency (e.g., 3x daily)"
                        value={currentMedicine.frequency}
                        onChange={(e) => setCurrentMedicine(prev => ({ ...prev, frequency: e.target.value }))}
                        onBlur={(e) => applyFrequency(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault()
                            applyFrequency(e.target.value)
                          }
                        }}
                        className="form-input"
                      />
                    </div>

                    <div className="form-row">
                      <input
                        type="text"
                        placeholder="Duration (e.g., 5 days)"
                        value={currentMedicine.duration}
                        onChange={(e) => setCurrentMedicine(prev => ({ ...prev, duration: e.target.value }))}
                        onBlur={(e) => applyDuration(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault()
                            applyDuration(e.target.value)
                          }
                        }}
                        className="form-input"
                      />
                      <button
                        className="btn-add-medicine"
                        onClick={handleAddMedicine}
                      >
                        Add Medicine
                      </button>
                    </div>
                  </div>

                  {/* Selected Medicines List */}
                  <div className="medicines-list">
                    {medicines.length > 0 ? (
                      medicines.map((medicine, idx) => (
                        <div key={idx} className="medicine-item">
                          <div className="medicine-header">
                            <div className="medicine-info">
                              <div className="medicine-name">{medicine.name}</div>
                              <div className="medicine-details">
                                {medicine.dosage} • {medicine.frequency}
                                {medicine.duration && ` • ${medicine.duration}`}
                              </div>
                            </div>
                            <button
                              className="btn-remove"
                              onClick={() => handleRemoveMedicine(idx)}
                              title="Remove medicine"
                            >
                              ✕
                            </button>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="no-data">No medicines added</p>
                    )}
                  </div>

                  {medicines.length > 0 && (
                    <button
                      className="btn-save-medicines"
                      onClick={handleSaveMedicines}
                      disabled={isSavingMedicines}
                    >
                      {isSavingMedicines ? 'Saving...' : `Save ${medicines.length} Medicine(s)`}
                    </button>
                  )}
                </div>

                <button 
                  className="btn-generate"
                  onClick={generateReport}
                  disabled={reportGenerated}
                >
                  <FileText size={18} /> Generate Report
                </button>
              </div>
            </>
          ) : (
            <div className="empty-state">
              <Activity size={48} />
              <h3>Select a Patient</h3>
              <p>Choose a patient from the list to begin consultation</p>
            </div>
          )}
        </div>

        {/* RIGHT SIDEBAR - Disease Recommendation */}
        <div className="right-panel">
          <div className="panel-header">
            <h2>Symptoms & Recommendations</h2>
          </div>

          <div className="symptoms-section">
            <label>Detected Symptoms</label>
            <div className="symptoms-list">
              {symptoms && symptoms.length > 0 ? (
                symptoms.map((symptom, idx) => {
                  // Handle both object and string formats
                  const symptomName = typeof symptom === 'string' ? symptom : symptom.name || symptom;
                  const duration = symptom.duration ? symptom.duration : 'not specified';
                  
                  return (
                    <div key={idx} className="symptom-item">
                      <div className="symptom-header">
                        <span className="symptom-number">{idx + 1}</span>
                        <span className="symptom-name">{symptomName}</span>
                        <span className="symptom-duration">{duration}</span>
                      </div>
                    </div>
                  );
                })
              ) : (
                <p className="no-data">No symptoms detected</p>
              )}
            </div>
          </div>

          <div className="recommendations-section">
            <label>Disease Recommendations</label>
            <div className="recommendations-list">
              {isPredicting ? (
                <div className="recommendation-item loading">
                  <div className="rec-title">Predicting disease...</div>
                  <p className="rec-desc">Analyzing symptoms to predict disease...</p>
                </div>
              ) : predictedDisease ? (
                <div className="recommendation-item success">
                  <div className="rec-title">Predicted Diagnosis</div>
                  <div className="rec-disease">{predictedDisease}</div>
                  <div className="rec-confidence">
                    Confidence: {(confidenceScore * 100).toFixed(1)}%
                  </div>
                  <p className="rec-desc">
                    Based on detected symptoms and AI analysis
                  </p>
                </div>
              ) : (
                <div className="recommendation-item">
                  <div className="rec-title">Based on consultation</div>
                  <p className="rec-desc">
                    {transcript ? 'Record and analyze symptoms to see disease prediction' : 'Add consultation recording to see predictions'}
                  </p>
                </div>
              )}
            </div>
          </div>


          {reportGenerated && (
            <div className="report-status">
              <div className="status-success">✓ Report Generated</div>
              {reportContent && (
                <div className="report-display">
                  <div className="report-title">Medical Consultation Report</div>
                  <div className="report-content">
                    <pre>{reportContent}</pre>
                  </div>
                  <button 
                    className="download-btn"
                    onClick={() => {
                      if (reportFilename) {
                        const downloadUrl = `/download-report/${reportFilename}`
                        const link = document.createElement('a')
                        link.href = downloadUrl
                        link.download = reportFilename
                        document.body.appendChild(link)
                        link.click()
                        document.body.removeChild(link)
                      } else {
                        alert('Report filename not available')
                      }
                    }}
                  >
                    ⬇ Download Report
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
