import re
from typing import List
from detectors.base import DetectionResult, PHONE

class PhoneDetector:
    def __init__(self):
        self.patterns = [
            (re.compile(r'(?:\+91|0)[-\s]?([6-9]\d{4})[-\s]?(\d{5})\b'), 0.9),
            (re.compile(r'\b(?<!\d)[6-9]\d{4}[-\s]?\d{5}(?!\d)\b'), 0.75),
            (re.compile(r'(?:\+1[-\s]?)?\(?\b([2-9]\d{2})\)?[-\s]?([2-9]\d{2})[-\s]?(\d{4})\b'), 0.9),
            (re.compile(r'(?:\+[1-9]{1,3})[-\s\.]?(?:\d[-\s\.]?){8,14}\d\b'), 0.9)
        ]

    def detect(self, text: str) -> List[DetectionResult]:
        results = []
        matched_spans = set()
        
        for pattern, base_conf in self.patterns:
            for match in pattern.finditer(text):
                start, end = match.span()
                
                if any(s < end and e > start for s, e in matched_spans):
                    continue
                    
                digits = re.sub(r'\D', '', match.group())
                if len(digits) < 10:
                    continue
                    
                matched_spans.add((start, end))
                
                conf = base_conf
                if len(digits) == 10 and len(match.group()) == 10 and base_conf == 0.9:
                    conf = 0.75
                    
                results.append(DetectionResult(
                    text=match.group(),
                    start=start,
                    end=end,
                    pii_type=PHONE,
                    confidence=conf
                ))
        return results
