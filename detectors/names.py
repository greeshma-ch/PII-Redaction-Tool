from typing import List
from .base import DetectionResult, NAME
from ._nlp_loader import get_nlp

class NameDetector:
    def __init__(self):
        self.honorifics = {'mr', 'mrs', 'dr', 'shri', 'ms', 'miss'}

    def detect(self, text: str) -> List[DetectionResult]:
        nlp = get_nlp()
        doc = nlp(text)
        results = []
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                ent_text = ent.text.strip()
                # Filter: single character
                if len(ent_text) <= 1:
                    continue
                # Filter: common titles/honorifics used alone
                if ent_text.lower() in self.honorifics:
                    continue
                # Filter: all uppercase and less than 3 chars
                if ent.text.isupper() and len(ent_text) < 3:
                    continue
                
                # Confidence
                tokens = ent_text.split()
                confidence = 0.85 if len(tokens) > 1 else 0.70
                
                results.append(DetectionResult(
                    text=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    pii_type=NAME,
                    confidence=confidence
                ))
        return results
