import re
from typing import List
from detectors.base import DetectionResult, DOB

class DOBDetector:
    def __init__(self):
        months = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
        self.patterns = [
            re.compile(r'\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})\b'),
            re.compile(r'\b(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})\b'),
            re.compile(rf'\b{months}\s+\d{{1,2}},?\s+\d{{4}}\b', re.IGNORECASE),
            re.compile(rf'\b\d{{1,2}}\s+{months}\s+\d{{4}}\b', re.IGNORECASE)
        ]
        self.context_keywords = ['born', 'dob', 'date of birth', 'birthday', 'b.', 'age']
        
    def detect(self, text: str) -> List[DetectionResult]:
        results = []
        for pattern in self.patterns:
            for match in pattern.finditer(text):
                date_str = match.group()
                start = match.start()
                end = match.end()
                
                year_match = re.search(r'\b(19\d{2}|200\d|201[0-5])\b', date_str)
                if not year_match:
                    continue
                    
                pre_text = text[max(0, start - 50):start].lower()
                has_context = any(kw in pre_text for kw in self.context_keywords)
                
                conf = 0.85 if has_context else 0.4
                
                results.append(DetectionResult(
                    text=date_str,
                    start=start,
                    end=end,
                    pii_type=DOB,
                    confidence=conf
                ))
        return results
