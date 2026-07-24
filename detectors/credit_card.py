import re
from typing import List
from detectors.base import DetectionResult, CREDIT_CARD

class CreditCardDetector:
    def __init__(self):
        self.seq_pattern = re.compile(r'\b(?:\d[ \-]?){13,16}\b')

    def luhn_check(self, num_str: str) -> bool:
        digits = [int(c) for c in num_str if c.isdigit()]
        if not digits:
            return False
        checksum = 0
        reverse_digits = digits[::-1]
        for i, d in enumerate(reverse_digits):
            if i % 2 == 1:
                d *= 2
                if d > 9:
                    d -= 9
            checksum += d
        return (checksum % 10) == 0

    def detect(self, text: str) -> List[DetectionResult]:
        results = []
        for match in self.seq_pattern.finditer(text):
            raw = match.group()
            cleaned = re.sub(r'[\s\-]', '', raw)
            
            if len(cleaned) not in [13, 15, 16]:
                continue
                
            is_valid_format = False
            if cleaned.startswith('4') and len(cleaned) in [13, 16]:
                is_valid_format = True
            elif (re.match(r'^5[1-5]', cleaned) or re.match(r'^2(?:22[1-9]|2[3-9]|[3-6]|7[01]|720)', cleaned)) and len(cleaned) == 16:
                is_valid_format = True
            elif cleaned.startswith(('34', '37')) and len(cleaned) == 15:
                is_valid_format = True
            elif cleaned.startswith(('6011', '65')) and len(cleaned) == 16:
                is_valid_format = True
                
            if not is_valid_format:
                continue
                
            passes_luhn = self.luhn_check(cleaned)
            conf = 0.95 if passes_luhn else 0.4
            
            if passes_luhn:
                results.append(DetectionResult(
                    text=raw,
                    start=match.start(),
                    end=match.end(),
                    pii_type=CREDIT_CARD,
                    confidence=conf
                ))
        return results
