import re
from typing import List
from .base import DetectionResult, ADDRESS
from core.gliner_client import detect

class AddressDetector:
    def __init__(self, threshold: float = 0.20):
        # Keywords to identify address context for PIN code
        self.address_keywords = re.compile(
            r'\b(road|street|nagar|district|state|india|floor|plot|building)\b', re.IGNORECASE
        )
        self.pin_pattern = re.compile(r'\b\d{6}\b')
        self.threshold = threshold
        self.labels = ["address", "location address", "street address", "city", "location", "state"]

    def detect(self, text: str) -> List[DetectionResult]:
        if not text or not text.strip():
            return []

        raw_entities = []
        gliner_ents = detect(text, labels=self.labels, threshold=self.threshold)
        for ent in gliner_ents:
            raw_entities.append((ent["start"], ent["end"], float(ent.get("score", 0.85))))

        # Check for regex based addresses (PINs near keywords)
        for match in self.pin_pattern.finditer(text):
            start, end = match.span()
            context_start = max(0, start - 50)
            context_end = min(len(text), end + 50)
            context = text[context_start:context_end]
            if self.address_keywords.search(context):
                raw_entities.append((start, end, 0.85))

        if not raw_entities:
            return []

        # Sort by start_char
        raw_entities.sort(key=lambda x: x[0])

        merged_entities = []
        curr_start, curr_end, curr_score = raw_entities[0]

        for i in range(1, len(raw_entities)):
            next_start, next_end, next_score = raw_entities[i]
            # Check if within 5 chars
            if next_start - curr_end <= 5:
                curr_end = max(curr_end, next_end)
                curr_score = max(curr_score, next_score)
            else:
                merged_entities.append((curr_start, curr_end, curr_score))
                curr_start, curr_end, curr_score = next_start, next_end, next_score
        merged_entities.append((curr_start, curr_end, curr_score))

        results = []
        for start, end, score in merged_entities:
            ent_text = text[start:end]

            tokens = ent_text.split()
            if len(tokens) > 1 or any(char.isdigit() for char in ent_text):
                confidence = max(score, 0.85)
            else:
                confidence = max(score, 0.65)

            results.append(DetectionResult(
                text=ent_text,
                start=start,
                end=end,
                pii_type=ADDRESS,
                confidence=confidence
            ))

        return results
