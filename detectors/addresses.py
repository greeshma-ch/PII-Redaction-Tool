import re
from typing import List
from .base import DetectionResult, ADDRESS
from ._nlp_loader import get_nlp

class AddressDetector:
    def __init__(self):
        # Keywords to identify address context for PIN code
        self.address_keywords = re.compile(
            r'\b(road|street|nagar|district|state|india|floor|plot|building)\b', re.IGNORECASE
        )
        self.pin_pattern = re.compile(r'\b\d{6}\b')

    def detect(self, text: str) -> List[DetectionResult]:
        nlp = get_nlp()
        doc = nlp(text)
        
        # We will collect spans (start, end)
        raw_entities = []
        for ent in doc.ents:
            if ent.label_ in ('GPE', 'LOC', 'FAC'):
                raw_entities.append((ent.start_char, ent.end_char))

        # Check for regex based addresses (PINs near keywords)
        for match in self.pin_pattern.finditer(text):
            start, end = match.span()
            # check context window of ~50 chars around it
            context_start = max(0, start - 50)
            context_end = min(len(text), end + 50)
            context = text[context_start:context_end]
            if self.address_keywords.search(context):
                raw_entities.append((start, end))
                
        # Merge adjacent entities within 5 chars
        if not raw_entities:
            return []
            
        # Sort by start_char
        raw_entities.sort(key=lambda x: x[0])
        
        merged_entities = []
        curr_start, curr_end = raw_entities[0]
        
        for i in range(1, len(raw_entities)):
            next_start, next_end = raw_entities[i]
            # Check if within 5 chars
            if next_start - curr_end <= 5:
                curr_end = max(curr_end, next_end)
            else:
                merged_entities.append((curr_start, curr_end))
                curr_start, curr_end = next_start, next_end
        merged_entities.append((curr_start, curr_end))
        
        results = []
        for start, end in merged_entities:
            ent_text = text[start:end]
            
            # Confidence logic:
            # 0.85 for multi-token structured addresses, 0.65 for standalone city/state names from NER
            tokens = ent_text.split()
            if len(tokens) > 1 or any(char.isdigit() for char in ent_text):
                confidence = 0.85
            else:
                confidence = 0.65
                
            results.append(DetectionResult(
                text=ent_text,
                start=start,
                end=end,
                pii_type=ADDRESS,
                confidence=confidence
            ))
            
        return results
