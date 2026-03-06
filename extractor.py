import re
import spacy
import json
from negspacy.negation import Negex
from transformers import pipeline
from py_heideltime import heideltime
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

class MedicalSymptomExtractor:

    def __init__(self):

        self.ner = pipeline(
            "token-classification",
            model="./symptom_model",
            tokenizer="./symptom_model",
            aggregation_strategy="simple"
        )

        #self.ner = pipeline(
         #   "token-classification",
          #  model="HUMADEX/english_medical_ner",
           # aggregation_strategy="simple",
            #device=-1
        #)
        self.nlp_med = spacy.load("en_core_sci_sm")
        self.nlp_gen = spacy.load("en_core_web_sm")
        # spaCy + Negspacy
        if "negex" not in self.nlp_med.pipe_names:
            self.nlp_med.add_pipe("negex")

        # Confidence threshold
        self.confidence_threshold = 0.6

    # --------------------------------
    # Extract durations with span
    # --------------------------------
    def extract_durations_with_span(self, doc):
        durations = []

        for ent in doc.ents:
            if ent.label_ == "DATE":
                text = ent.text.lower()

                if any(unit in text for unit in [
                    "day", "week", "month", "year", "hour", "night","morning","afternoon","evening"
                ]):
                    durations.append({
                        "text": text,
                        "start_token": ent.start,
                        "end_token": ent.end
                    })

        return durations
    
    # --------------------------------
    # Attach nearest duration
    # --------------------------------
    def attach_duration_dependency(self, symptom_span, durations):
        if not symptom_span or not durations:
            return None

        best_duration = None
        min_distance = float('inf')

        for duration in durations:

            # 🔹 Get the duration token from the doc
            duration_token = symptom_span.doc[duration["start_token"]]

            # 🔹 NEW: Only link if in the same sentence
            if duration_token.sent != symptom_span.sent:
                continue
            # Calculate distance between symptom and duration tokens
            if duration["start_token"] > symptom_span.end:
                dist = duration["start_token"] - symptom_span.end
            else:
                dist = symptom_span.start - duration["end_token"]

            # Only link if they are relatively close (e.g., within 10 tokens)
            if dist < min_distance and dist < 10:
                min_distance = dist
                best_duration = duration["text"]

        return best_duration

    # --------------------------------
    # Assertion classification
    # --------------------------------
    def classify_assertion(self, negated, doc, entity_start):

        if negated:
            return "absent"

        # Define uncertainty words
        uncertainty_words = {"might", "maybe", "possibly", "could", "suspect"}

        for token in doc:
            if token.idx >= entity_start:
                break

            if entity_start - token.idx <= 50:  # small char window
                if token.text.lower() in uncertainty_words:
                    return "possible"

        return "present"

        # --------------------------------
    # Merge adjacent entities safely
    # --------------------------------
    def merge_entities(self, entities):

        if not entities:
            return []

        merged = []
        current = entities[0]

        for entity in entities[1:]:

            gap_text = text[current["end"]:entity["start"]]

            if entity["start"] <= current["end"] + 2 and "," not in gap_text:
                word = entity["word"].replace("##", "")
                current["word"] += " " + word
                current["end"] = entity["end"]
                current["score"] = max(current["score"], entity["score"])
            else:
                merged.append(current)
                current = entity

        merged.append(current)
        return merged

    # --------------------------------
    # Main extraction
    # --------------------------------
    def extract(self, text):

        doc_med = self.nlp_med(text)   # For negation
        doc_gen = self.nlp_gen(text.lower())
        print("\nDetected Entities:")
        for ent in doc_gen.ents:
            print(ent.text, ent.label_)   # For duration + dependency
        durations = self.extract_durations_with_span(doc_gen)

        ner_results = self.ner(text)

        # Filter PROBLEM entities
        problem_entities = [
            e for e in ner_results
            if e["entity_group"] == "SYMPTOM"
            and e["score"] >= self.confidence_threshold
        ]

        # Merge adjacent tokens
        merged_entities = self.merge_entities(problem_entities)
        # Build output
        symptoms = []

        for entity in merged_entities:

            # Remove very short noise
            if len(entity["word"]) <= 2:
                continue

            # Negation detection
            span = doc_med.char_span(
                entity["start"],
                entity["end"],
                alignment_mode="expand"
            )
            negated = span._.negex if span else False

            # Assertion

            assertion = self.classify_assertion(
                negated,
                doc_med,
                entity["start"]
            )

            # Attach duration
            duration = None
            if assertion in ["present", "possible"]:
                duration = self.attach_duration_dependency(span, durations)

            symptoms.append({
                "name": entity["word"].lower(),
                "confidence": round(float(entity["score"]), 3),
                "assertion": assertion,
                "duration": duration
            })

        return {
            "symptoms": symptoms
        }


if __name__ == "__main__":

    extractor = MedicalSymptomExtractor()

    #text = "I have been experiencing palpitations and fatigue since last week, but no chest pain or shortness of breath."
    text = "I have been suffering from sore throat,sore legs and sore hand for 10 days."
    result = extractor.extract(text)

    print("\nExtracted Symptoms:")
    print(result)