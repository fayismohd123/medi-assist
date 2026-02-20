import re
import spacy
import json
from negspacy.negation import Negex
from transformers import pipeline


class MedicalSymptomExtractor:

    def __init__(self):

        # HuggingFace NER
        self.ner = pipeline(
            "token-classification",
            model="HUMADEX/english_medical_ner",
            aggregation_strategy="simple",
            device=-1
        )


        # spaCy + Negspacy
        self.nlp = spacy.load("en_core_web_sm")
        self.nlp.add_pipe("negex")

        # Duration regex
        self.duration_pattern = r"\b(\d+)\s+(day|days|week|weeks|month|months|year|years)\b"

    # --------------------------------
    # Extract durations with span
    # --------------------------------
    def extract_durations_with_span(self, text):
        durations = []
        for match in re.finditer(self.duration_pattern, text.lower()):
            durations.append({
                "text": match.group(),
                "start": match.start(),
                "end": match.end()
            })
        return durations

    # --------------------------------
    # Attach nearest duration
    # --------------------------------
    def attach_duration(self, symptom_start, durations, window=60):

        closest = None
        min_distance = float("inf")

        for d in durations:
            distance = abs(symptom_start - d["start"])
            if distance < min_distance and distance <= window:
                min_distance = distance
                closest = d["text"]

        return closest

    # --------------------------------
    # Assertion classification
    # --------------------------------
    def classify_assertion(self, negated, doc, entity_start, entity_end):

        if negated:
            return "absent"

        # Define uncertainty words
        uncertainty_words = {"might", "maybe", "possibly", "could", "suspect"}

        # Look 5 tokens before symptom
        window_size = 5

        for token in doc:
            if token.idx >= entity_start:
                break

            if entity_start - token.idx <= 50:  # small char window
                if token.text.lower() in uncertainty_words:
                    return "possible"

        return "present"


    # --------------------------------
    # Main extraction
    # --------------------------------
    def extract(self, text):

        doc = self.nlp(text)
        durations = self.extract_durations_with_span(text)

        ner_results = self.ner(text)

        # Filter PROBLEM entities
        problem_entities = [
            e for e in ner_results
            if "PROBLEM" in e["entity_group"]
        ]

        # Merge adjacent tokens
        merged_entities = []
        current = None

        for entity in problem_entities:

            if current is None:
                current = entity
                continue

            if entity["start"] <= current["end"] + 1:
                current["word"] += " " + entity["word"]
                current["end"] = entity["end"]
                current["score"] = max(current["score"], entity["score"])
            else:
                merged_entities.append(current)
                current = entity

        if current:
            merged_entities.append(current)

        # Build output
        symptoms = []

        for entity in merged_entities:

            # Remove very short noise
            if len(entity["word"]) <= 2:
                continue

            # Negation detection
            span = doc.char_span(entity["start"], entity["end"])
            negated = span._.negex if span else False

            # Assertion
            assertion = self.classify_assertion(
                negated,
                doc,
                entity["start"],
                entity["end"]
            )


            # Attach duration
            duration = self.attach_duration(entity["start"], durations)

            symptoms.append({
                "name": entity["word"].lower(),
                "confidence": round(entity["score"], 3),
                "assertion": assertion,
                "duration": duration
            })

        return {
            "symptoms": symptoms
        }


