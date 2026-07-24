from typing import List, Set, Optional
from .base import DetectionResult, COMPANY
from ._nlp_loader import get_nlp

class CompanyDetector:
    def __init__(self, exclusions: Optional[Set[str]] = None):
        if exclusions is None:
            self.exclusions = {'KSH International Limited', 'KSH International', 'KSH'}
        else:
            self.exclusions = set(exclusions)

    def detect(self, text: str) -> List[DetectionResult]:
        nlp = get_nlp()
        doc = nlp(text)
        results = []
        for ent in doc.ents:
            if ent.label_ == 'ORG':
                if ent.text.strip() in self.exclusions:
                    continue
                
                results.append(DetectionResult(
                    text=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    pii_type=COMPANY,
                    confidence=0.8
                ))
        return results
