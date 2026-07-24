import re
from typing import List
from detectors.base import DetectionResult, SSN

class SSNDetector:
    def __init__(self):
        self.pattern = re.compile(r'\b(\d{3})-(\d{2})-(\d{4})\b')

    def detect(self, text: str) -> List[DetectionResult]:
        results = []
        for match in self.pattern.finditer(text):
            g1, g2, g3 = match.groups()
            
            if g1 == '000' or g1 == '666' or int(g1) >= 900:
                continue
            if g2 == '00' or g3 == '0000':
                continue
                
            results.append(DetectionResult(
                text=match.group(),
                start=match.start(),
                end=match.end(),
                pii_type=SSN,
                confidence=0.9
            ))
        return results
