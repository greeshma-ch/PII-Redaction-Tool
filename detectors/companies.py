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

# Corporate suffixes to expand gazetteer matches (e.g. "L&T" -> "L&T Finance")
CORP_SUFFIXES = re.compile(r'^\s+(limited|ltd|finance|bank|india|steel|auto|pharma|green|airtel|motors|capital|securities)\b', re.IGNORECASE)

# Exclusion stoplist for regulatory bodies and non-sensitive entities
COMPANY_STOPLIST = {
    "vivek", "shri", "mr", "mrs", "dr", "ms",
    "sebi", "ministry of corporate affairs", "reserve bank of india", "rbi"
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

        # Ensure gazetteer match is NOT part of an email address (@domain.com)
        esc_items = [re.escape(item) for item in sorted(self.gazetteer, key=len, reverse=True)]
        self.gazetteer_pattern = re.compile(rf'(?<![@\w])\b({"|".join(esc_items)})\b(?![@\w])', re.IGNORECASE) if esc_items else None

    def detect(self, text: str) -> List[DetectionResult]:
        if not text or not text.strip():
            return []

        raw_entities = []

        # 1. Gazetteer matching (confidence = 1.0)
        if self.use_gazetteer and self.gazetteer_pattern:
            for match in self.gazetteer_pattern.finditer(text):
                start, end = match.span()

                # Expand gazetteer match if followed by a corporate suffix (e.g. "L&T" -> "L&T Finance")
                remainder = text[end:]
                suf_match = CORP_SUFFIXES.search(remainder)
                if suf_match:
                    end += suf_match.end()

                ent_text = text[start:end].strip()
                if ent_text in self.exclusions or ent_text.lower() in COMPANY_STOPLIST:
                    continue

                # Skip if part of an email address
                context_start = max(0, start - 15)
                context_end = min(len(text), end + 15)
                if "@" in text[context_start:context_end]:
                    continue

                raw_entities.append((start, end, 1.0))

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
            if ent_text.lower() in COMPANY_STOPLIST:
                continue

            context_start = max(0, start - 15)
            context_end = min(len(text), end + 15)
            if "@" in text[context_start:context_end]:
                continue

            score = float(ent.get("score", 0.8))
            raw_entities.append((start, end, score))

        if not raw_entities:
            return []

        # Sort entities by start offset
        raw_entities.sort(key=lambda x: x[0])

        # Merge adjacent company spans (e.g. "JSW" + "Steel")
        merged_entities = []
        curr_start, curr_end, curr_score = raw_entities[0]

        for i in range(1, len(raw_entities)):
            next_start, next_end, next_score = raw_entities[i]
            if next_start - curr_end <= 2:
                curr_end = max(curr_end, next_end)
                curr_score = max(curr_score, next_score)
            else:
                merged_entities.append((curr_start, curr_end, curr_score))
                curr_start, curr_end, curr_score = next_start, next_end, next_score
        merged_entities.append((curr_start, curr_end, curr_score))

        results = []
        seen_spans = set()
        for start, end, score in merged_entities:
            ent_text = text[start:end].strip()
            if ent_text in self.exclusions or ent_text.lower() in COMPANY_STOPLIST:
                continue
            span = (start, end)
            if span in seen_spans:
                continue
            seen_spans.add(span)

            results.append(DetectionResult(
                text=ent_text,
                start=start,
                end=end,
                pii_type=COMPANY,
                confidence=score
            ))

        return results
