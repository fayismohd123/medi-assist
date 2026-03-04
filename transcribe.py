from faster_whisper import WhisperModel
from extractor import MedicalSymptomExtractor
import numpy as np

# ================= INITIALIZE MODELS ONCE AT STARTUP =================
print("⏳ Loading Faster Whisper model... (this happens once at Flask startup)")
WHISPER_MODEL = WhisperModel("medium", device="cpu", compute_type="int8")
SYMPTOM_EXTRACTOR = MedicalSymptomExtractor()
print("✅ Faster Whisper and Medical Symptom Extractor models loaded and ready!")


# ================= HELPER FUNCTION =================
def convert_to_serializable(obj):
    """Convert NumPy types to Python native types for JSON serialization"""
    if isinstance(obj, np.floating):
        return float(obj)  # Convert float32/float64 to Python float
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(val) for key, val in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    return obj


# ================= TRANSCRIPTION FUNCTION =================
def transcribe_audio(audio_file_path):
    """
    Transcribe audio file using Faster Whisper and extract symptoms.
    
    Args:
        audio_file_path (str): Path to audio file (WAV, MP3, etc.)
    
    Returns:
        dict: {
            "transcript": str (transcribed text),
            "symptoms": list (extracted symptoms),
            "error": str (error message if any)
        }
    """
    try:
        # STEP 1: TRANSCRIBE with Faster Whisper
        print(f"🗣️ Transcribing: {audio_file_path}")
        segments, info = WHISPER_MODEL.transcribe(
            audio_file_path,
            task="translate",  # converts Malayalam → English automatically
            vad_filter=True
        )
        
        # Combine segments into one string for analysis
        transcript = " ".join([seg.text for seg in segments])
        # Apply medical correction layer
        transcript1 = apply_medical_corrections(transcript)
        print(f"✅ Transcription complete:\n{transcript1}\n")
        # STEP 2: EXTRACT SYMPTOMS
        print("💊 Extracting symptoms...")
        symptoms_result = SYMPTOM_EXTRACTOR.extract(transcript1)
        #print(f"✅ Raw symptoms extracted: {symptoms_result}\n")
        
        # Extract the 'symptoms' list from the result object
        symptoms_list = symptoms_result.get('symptoms', []) if isinstance(symptoms_result, dict) else symptoms_result
        
        # Convert to serializable format
        symptoms = convert_to_serializable(symptoms_list)
        print(f"✅ Symptoms extracted: {symptoms}\n")
        
        return {
            "transcript": transcript1,
            "symptoms": symptoms
        }
    
    except Exception as e:
        print(f"❌ Transcription Error: {e}")
        return {
            "transcript": "",
            "symptoms": [],
            "error": str(e)
        }
def apply_medical_corrections(text):
    """
    Apply rule-based corrections for common medical ASR errors.
    """
    correction_rules = {
        "working": "fever","work": "fever","worked": "fever",}
    
    words = text.split()
    corrected_words = [
        correction_rules.get(word.lower(), word) for word in words
    ]
    
    return " ".join(corrected_words)

# ================= STANDALONE SCRIPT MODE =================
# If run directly (not imported), allow testing with output.wav
if __name__ == "__main__":
    audio_file = "output.wav"
    result = transcribe_audio(audio_file)
    
    print("=" * 60)
    if result.get('error'):
        print(f"⚠️ Error: {result['error']}")
