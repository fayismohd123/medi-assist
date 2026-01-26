from faster_whisper import WhisperModel
from extractor import MedicalSymptomExtractor, save_to_json

# ================= MODEL =================
model = WhisperModel("medium", device="cpu", compute_type="int8")
audio_file = "output.wav"

# ================= STEP 1: TRANSCRIBE =================
segments, info = model.transcribe(
    audio_file,
    task="translate",   # converts Malayalam → English automatically
    vad_filter=True
)

# Combine segments into one string for analysis
transcript = " ".join([seg.text for seg in segments])
print("🗣️ Transcription:\n", transcript)

# ================= STEP 2: EXTRACT SYMPTOMS =================
extractor = MedicalSymptomExtractor()
results = extractor.extract(transcript)

# ================= STEP 3: SAVE / PRINT =================
save_to_json(results, "symptoms_from_audio.json")

for r in results:
    print(r)
