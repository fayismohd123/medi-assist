import spacy
import re
import json
from typing import List, Dict

class MedicalSymptomExtractor:
    """
    medical symptom extractor using:
    - scispaCy NER (BC5CDR)
    - NegSpacy for negation detection
    - Regex-based duration extraction
    """

    def __init__(self, model_name: str = "en_ner_bc5cdr_md"):
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            raise RuntimeError(
                f"Model '{model_name}' not found. "
                "Install from scispaCy releases."
            )

        # Ensure sentence boundaries
        if "sentencizer" not in self.nlp.pipe_names:
            self.nlp.add_pipe("sentencizer")

        # Negation detection
        from negspacy.negation import Negex
        self.nlp.add_pipe("negex", config={"ent_types": ["DISEASE"]})

        # Simple, high-coverage duration patterns
        self.duration_regex = re.compile(
            r"""
            (for\s+(?:the\s+)?(?:past|last)?\s*\d+\s+(?:days?|weeks?|months?|years?))|
            (\d+\s+(?:days?|weeks?|months?|years?)\s+ago)|
            (since\s+\w+)
            """,
            re.IGNORECASE | re.VERBOSE
        )

    def extract_duration(self, text: str) -> str:
        match = self.duration_regex.search(text)
        return match.group(0) if match else "not specified"

    def extract(self, transcript: str) -> List[Dict]:
        """
        Extract symptoms with negation and duration.
        """
        doc = self.nlp(transcript)
        results = []

        for ent in doc.ents:
            if ent.label_ != "DISEASE":
                continue

            sentence = ent.sent.text.strip()
            duration = self.extract_duration(sentence)

            negated = bool(getattr(ent._, "negex", False))

            results.append({
                "symptom": ent.text,
                "status": "absent" if negated else "present",
                "duration": duration,
                "context": sentence
            })

        return results
    

    
def save_to_json(results, output_file="symptoms_output.json"):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    extractor = MedicalSymptomExtractor()

    text = """
    Doctor: Good morning, what brings you in today?
    
    Patient: Hi doctor, I've been having this terrible headache for the past 3 days. 
    It's really been bothering me.
    
    Doctor: I see. Can you describe the headache? Where is it located?
    
    Patient: It's mostly on the right side of my head, and it's a throbbing pain. 
    I've also had some nausea since yesterday.
    
    Doctor: Have you had any fever?
    
    Patient: Yes, I had a low-grade fever for about 2 days, but it went away this morning.
    
    Doctor: Any other symptoms?
    
    Patient: Well, I've been feeling fatigued for the last week or so. And I've had a 
    sore throat for 4 days now. Also experiencing some chest pain that started 2 days ago.
    
    Doctor: Okay, let me examine you. Any shortness of breath?
    
    Patient: A little bit, yes. It started yesterday.
    
    Doctor: Any vomiting or diarrhea?
    
    Patient: No vomiting, no diarrhea. Patient denies any bleeding or bruising.
    
    Doctor: Have you had any cough?
    
    Patient: No cough at all. And I haven't had any dizziness either.
    
    Doctor: Good. No swelling in the legs?
    
    Patient: No swelling. No rash either.
    """

    results = extractor.extract(text)
    save_to_json(results, "symptoms_output.json")

    for r in results:
        print(r)
