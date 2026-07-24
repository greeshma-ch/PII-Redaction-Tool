import re
from typing import List
from detectors.base import DetectionResult, EMAIL

class EmailDetector:
    def __init__(self):
        # RFC 5322-style regex (simplified for typical use cases)
        self.pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )

    def detect(self, text: str) -> List[DetectionResult]:
        results = []
        for match in self.pattern.finditer(text):
            results.append(DetectionResult(
                text=match.group(),
                start=match.start(),
                end=match.end(),
                pii_type=EMAIL,
                confidence=0.95
            ))
        return results
