import re
from typing import List
from .base import DetectionResult, ADDRESS
from core.gliner_client import detect

# Major Indian cities — built from actual false-negative text in the gold standard
# plus standard metro/tier-1 cities likely to appear in regulatory filings.
# TODO: If future documents cover smaller cities, this list can be extended.
INDIAN_CITIES = {
    "mumbai", "delhi", "new delhi", "bengaluru", "bangalore", "hyderabad",
    "chennai", "kolkata", "pune", "ahmedabad", "gurugram", "gurgaon",
    "noida", "jaipur", "lucknow", "chandigarh", "indore", "bhopal",
    "patna", "kochi", "thiruvananthapuram", "coimbatore", "nagpur",
    "visakhapatnam", "vadodara", "surat", "thane", "navi mumbai",
    "ghaziabad", "faridabad", "greater noida", "mysuru", "mysore",
}

# Single-word non-address terms that GLiNER sometimes tags as ADDRESS
ADDRESS_STOPLIST = {"india"}

class AddressDetector:
    def __init__(self, threshold: float = 0.20):
        # Keywords to identify address context for PIN code
        self.address_keywords = re.compile(
            r'\b(road|street|nagar|district|state|india|floor|plot|building|address)\b', re.IGNORECASE
        )
        self.pin_pattern = re.compile(r'\b\d{6}\b')
        self.threshold = threshold
        self.labels = ["address", "location address", "street address", "city", "location", "state"]

    def _extend_pin_to_city(self, text: str, pin_start: int, pin_end: int) -> tuple:
        """
        Look at the token(s) immediately preceding a PIN code span (allowing for
        whitespace or a comma between them). If they match a known Indian city name
        (case-insensitive), extend the span start to include the city name.
        If not, return the PIN-only span unchanged.
        """
        # Look at up to 30 chars before the PIN for a city name
        prefix = text[max(0, pin_start - 30):pin_start].rstrip(" ,\t")
        if not prefix:
            return pin_start, pin_end

        # Try two-word city names first (e.g. "New Delhi", "Navi Mumbai")
        words = prefix.split()
        if len(words) >= 2:
            two_word = f"{words[-2]} {words[-1]}"
            if two_word.lower() in INDIAN_CITIES:
                # Find the actual start position of the two-word city in the original text
                city_start = text.rfind(words[-2], max(0, pin_start - 30), pin_start)
                if city_start >= 0:
                    return city_start, pin_end

        # Try single-word city name
        if words:
            last_word = words[-1]
            if last_word.lower() in INDIAN_CITIES:
                city_start = text.rfind(last_word, max(0, pin_start - 30), pin_start)
                if city_start >= 0:
                    return city_start, pin_end

        return pin_start, pin_end

    def detect(self, text: str) -> List[DetectionResult]:
        if not text or not text.strip():
            return []

        raw_entities = []
        gliner_ents = detect(text, labels=self.labels, threshold=self.threshold)
        for ent in gliner_ents:
            raw_entities.append((ent["start"], ent["end"], float(ent.get("score", 0.85))))

        # Check for regex based addresses (PINs near keywords OR preceded by city name)
        for match in self.pin_pattern.finditer(text):
            start, end = match.span()
            context_start = max(0, start - 50)
            context_end = min(len(text), end + 50)
            context = text[context_start:context_end]
            if self.address_keywords.search(context):
                raw_entities.append((start, end, 0.85))

        if not raw_entities:
            return []

        # Post-processing: extend any PIN-only spans to include preceding city name
        extended_entities = []
        for start, end, score in raw_entities:
            span_text = text[start:end].strip()
            # If the span is a bare 6-digit PIN code, try to extend it
            if re.fullmatch(r'\d{6}', span_text):
                new_start, new_end = self._extend_pin_to_city(text, start, end)
                extended_entities.append((new_start, new_end, score))
            else:
                extended_entities.append((start, end, score))

        # Sort by start_char
        extended_entities.sort(key=lambda x: x[0])

        merged_entities = []
        curr_start, curr_end, curr_score = extended_entities[0]

        for i in range(1, len(extended_entities)):
            next_start, next_end, next_score = extended_entities[i]
            # Check if within 5 chars
            if next_start - curr_end <= 5:
                curr_end = max(curr_end, next_end)
                curr_score = max(curr_score, next_score)
            else:
                merged_entities.append((curr_start, curr_end, curr_score))
                curr_start, curr_end, curr_score = next_start, next_end, next_score
        merged_entities.append((curr_start, curr_end, curr_score))

        results = []
        for start, end, score in merged_entities:
            ent_text = text[start:end]

            # Filter out stoplist terms (e.g. standalone "India")
            if ent_text.strip().lower() in ADDRESS_STOPLIST:
                continue

            tokens = ent_text.split()
            if len(tokens) > 1 or any(char.isdigit() for char in ent_text):
                confidence = max(score, 0.85)
            else:
                confidence = max(score, 0.65)

            results.append(DetectionResult(
                text=ent_text,
                start=start,
                end=end,
                pii_type=ADDRESS,
                confidence=confidence
            ))

        return results
