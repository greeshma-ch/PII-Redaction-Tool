import re
from typing import List
from detectors.base import DetectionResult, IP_ADDRESS

class IPAddressDetector:
    def __init__(self):
        self.ipv4_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
        self.ipv6_pattern = re.compile(r'\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b|\b(?:[A-Fa-f0-9]{1,4}:)*::(?:[A-Fa-f0-9]{1,4}:)*[A-Fa-f0-9]{1,4}\b')
        
    def detect(self, text: str) -> List[DetectionResult]:
        results = []
        for match in self.ipv4_pattern.finditer(text):
            parts = match.group().split('.')
            if all(0 <= int(p) <= 255 for p in parts):
                results.append(DetectionResult(
                    text=match.group(),
                    start=match.start(),
                    end=match.end(),
                    pii_type=IP_ADDRESS,
                    confidence=0.95
                ))
                
        for match in self.ipv6_pattern.finditer(text):
            results.append(DetectionResult(
                text=match.group(),
                start=match.start(),
                end=match.end(),
                pii_type=IP_ADDRESS,
                confidence=0.9
            ))
            
        return results
