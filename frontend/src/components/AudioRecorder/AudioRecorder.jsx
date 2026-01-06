import { useState, useRef, useEffect } from 'react';
import { Mic, Pause, Play, FileText } from 'lucide-react';
import { recordingAPI } from '../../api/api';
import './AudioRecorder.css';

const AudioRecorder = ({ patient }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [language, setLanguage] = useState('en');
  const [transcript, setTranscript] = useState('');
  const [report, setReport] = useState('');
  
  const mediaRecorderRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const recordedChunksRef = useRef([]);

  useEffect(() => {
    return () => {
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      recordedChunksRef.current = [];

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const blob = new Blob(recordedChunksRef.current, { 
          type: recordedChunksRef.current[0]?.type || 'audio/webm' 
        });
        
        const formData = new FormData();
        formData.append('audio', blob, `recording_${Date.now()}.webm`);
        formData.append('language', language);

        try {
          const response = await recordingAPI.stop(formData);
          setTranscript(response.data.transcript || '');
        } catch (error) {
          console.error('Error stopping recording:', error);
          alert('Error processing recording');
        }

        if (mediaStreamRef.current) {
          mediaStreamRef.current.getTracks().forEach(track => track.stop());
          mediaStreamRef.current = null;
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      setIsPaused(false);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Could not access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsPaused(false);
    }
  };

  const togglePause = () => {
    if (!isRecording) return;

    if (isPaused) {
      mediaRecorderRef.current?.resume();
      setIsPaused(false);
    } else {
      mediaRecorderRef.current?.pause();
      setIsPaused(true);
    }
  };

  const generateReport = async () => {
    if (!transcript) {
      alert('No transcript available');
      return;
    }

    try {
      const response = await recordingAPI.generateReport();
      setReport(response.data.report || '');
    } catch (error) {
      console.error('Error generating report:', error);
      alert('Failed to generate report');
    }
  };

  return (
    <div className="controls">
      <div className="controls-wrapper">
        <button
          onClick={startRecording}
          className={`mic-button ${isRecording ? 'recording' : ''}`}
          disabled={isRecording || !patient}
          title={!patient ? 'Please select a patient first' : 'Start recording'}
        >
          <Mic size={64} />
          {isRecording && <div className="ping-animation"></div>}
        </button>

        <button
          onClick={isPaused ? togglePause : stopRecording}
          className="pause-button"
          disabled={!isRecording}
          title={isPaused ? 'Resume recording' : 'Stop recording'}
        >
          {isPaused ? <Play size={32} /> : <Pause size={32} />}
        </button>
      </div>

      <div className="language-select">
        <select 
          value={language} 
          onChange={(e) => setLanguage(e.target.value)}
          disabled={isRecording}
        >
          <option value="en">English</option>
          <option value="ta">தமிழ்</option>
          <option value="hi">हिंदी</option>
        </select>
      </div>

      {transcript && (
        <div className="transcript-container">
          <h3>Transcript:</h3>
          <p>{transcript}</p>
        </div>
      )}

      <button
        onClick={generateReport}
        className="report-button"
        disabled={!transcript}
      >
        <FileText size={24} />
        <span>Generate Report</span>
      </button>

      {report && (
        <div className="report-container">
          <h3>Medical Report:</h3>
          <pre>{report}</pre>
        </div>
      )}
    </div>
  );
};

export default AudioRecorder;
