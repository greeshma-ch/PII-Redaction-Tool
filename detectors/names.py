from typing import List
from .base import DetectionResult, NAME
from core.gliner_client import detect

NAME_STOPLIST = {
    "registrar", "auditor", "lead manager", "book running lead manager",
    "brlm", "compliance officer", "company secretary", "statutory auditor",
    "legal counsel", "lead manager to the issue", "registrar to the issue",
    "managing director", "executive director", "whole time director",
    "independent director", "non-executive director", "chief executive officer",
    "chief financial officer", "promoter", "promoters", "chairman", "director",
    "directors", "auditors", "bankers to the issue", "syndicate member",
    "book runner", "sponsor bank", "legal advisor", "peer review auditor",
}

class NameDetector:
    def __init__(self, threshold: float = 0.15):
        self.honorifics = {'mr', 'mrs', 'dr', 'shri', 'ms', 'miss'}
        self.threshold = threshold
        self.labels = ["person name", "person", "name", "full name"]

    def detect(self, text: str) -> List[DetectionResult]:
        if not text or not text.strip():
            return []

        entities = detect(text, labels=self.labels, threshold=self.threshold)
        if not entities:
            return []

        # Sort entities by start offset
        entities.sort(key=lambda x: x["start"])

        # Merge adjacent name tokens (e.g. First Last)
        merged_spans = []
        curr_start = entities[0]["start"]
        curr_end = entities[0]["end"]
        curr_score = float(entities[0].get("score", 0.85))

        for i in range(1, len(entities)):
            next_start = entities[i]["start"]
            next_end = entities[i]["end"]
            next_score = float(entities[i].get("score", 0.85))

            if next_start - curr_end <= 2:
                curr_end = max(curr_end, next_end)
                curr_score = max(curr_score, next_score)
            else:
                merged_spans.append((curr_start, curr_end, curr_score))
                curr_start, curr_end, curr_score = next_start, next_end, next_score
        merged_spans.append((curr_start, curr_end, curr_score))

        results = []
        for start, end, score in merged_spans:
            raw = text[start:end]
            stripped = raw.rstrip(".,;:!?\"'()[]{}")
            end = start + len(stripped)
            ent_text = stripped.strip()

            if len(ent_text) <= 1:
                continue
            if ent_text.lower() in self.honorifics:
                continue
            if ent_text.isupper() and len(ent_text) < 3:
                continue
            if ent_text.lower() in NAME_STOPLIST:
                continue

            results.append(DetectionResult(
                text=ent_text,
                start=start,
                end=end,
                pii_type=NAME,
                confidence=score
            ))
        return results
