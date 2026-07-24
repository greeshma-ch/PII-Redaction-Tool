import re
from typing import List, Set, Optional
from .base import DetectionResult, COMPANY
from core.gliner_client import detect

DEFAULT_COMPANY_GAZETTEER = {
    "SBI", "SEBI", "BSE", "NSE", "NSDL", "CDSL", "ICICI", "HDFC",
    "RIL", "TCS", "L&T", "ITC", "ONGC", "NTPC", "PNB", "BOB", "IDBI",
    "CANARA", "YES BANK", "KOTAK", "AXIS", "LIC", "NABARD", "HDFC BANK",
    "ICICI BANK", "AXIS BANK", "STATE BANK OF INDIA", "TATA STEEL",
    "WIPRO", "INFOSYS", "MARUTI SUZUKI", "BAJAJ AUTO", "SUN PHARMA",
    "VEDANTA", "JSW STEEL", "NTPC LIMITED", "ADANI GREEN", "BHARTI AIRTEL",
    "ZOMATO", "PAYTM", "NUVAMA", "LINK INTIME", "BIGSHARE"
}

class CompanyDetector:
    def __init__(
        self,
        exclusions: Optional[Set[str]] = None,
        threshold: float = 0.28,
        use_gazetteer: bool = True
    ):
        if exclusions is None:
            self.exclusions = {'KSH International Limited', 'KSH International', 'KSH'}
        else:
            self.exclusions = set(exclusions)
        self.threshold = threshold
        self.labels = ["company name", "company", "organization"]
        self.use_gazetteer = use_gazetteer
        self.gazetteer = set(DEFAULT_COMPANY_GAZETTEER)

        esc_items = [re.escape(item) for item in sorted(self.gazetteer, key=len, reverse=True)]
        self.gazetteer_pattern = re.compile(rf'\b({"|".join(esc_items)})\b', re.IGNORECASE) if esc_items else None

    def detect(self, text: str) -> List[DetectionResult]:
        if not text or not text.strip():
            return []

        results = []
        seen_spans = set()

        # 1. Gazetteer matching (confidence = 1.0)
        if self.use_gazetteer and self.gazetteer_pattern:
            for match in self.gazetteer_pattern.finditer(text):
                ent_text = match.group().strip()
                if ent_text in self.exclusions:
                    continue
                start, end = match.span()
                seen_spans.add((start, end))
                results.append(DetectionResult(
                    text=ent_text,
                    start=start,
                    end=end,
                    pii_type=COMPANY,
                    confidence=1.0
                ))

        # 2. GLiNER model matching
        entities = detect(text, labels=self.labels, threshold=self.threshold)
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
