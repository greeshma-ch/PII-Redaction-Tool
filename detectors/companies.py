from typing import List, Set, Optional
from .base import DetectionResult, COMPANY
from core.gliner_client import detect

class CompanyDetector:
    def __init__(self, exclusions: Optional[Set[str]] = None, threshold: float = 0.28):
        if exclusions is None:
            self.exclusions = {'KSH International Limited', 'KSH International', 'KSH'}
        else:
            self.exclusions = set(exclusions)
        self.threshold = threshold
        self.labels = ["company name", "company", "organization"]

    def detect(self, text: str) -> List[DetectionResult]:
        if not text or not text.strip():
            return []

        entities = detect(text, labels=self.labels, threshold=self.threshold)
        results = []
        seen_spans = set()

        for ent in entities:
            start, end = ent["start"], ent["end"]
            raw = text[start:end]
            stripped = raw.rstrip(".,;:!?\"'()[]{}")
            end = start + len(stripped)
            ent_text = stripped.strip()

            if ent_text in self.exclusions or len(ent_text) <= 1:
                continue

            span = (start, end)
            if span in seen_spans:
                continue
            seen_spans.add(span)

            score = float(ent.get("score", 0.8))

            results.append(DetectionResult(
                text=ent_text,
                start=start,
                end=end,
                pii_type=COMPANY,
                confidence=score
            ))
        return results
