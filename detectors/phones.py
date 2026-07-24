"""Phone number detector — handles Indian, US, and international formats."""

import re
from typing import List
from detectors.base import DetectionResult, PHONE


class PhoneDetector:
    """Detects phone numbers in Indian, US, and international formats.

    Avoids matching standalone short digit sequences (years, PIN codes,
    order numbers).
    """

    def __init__(self):
        # Ordered by specificity — most specific patterns first
        self.patterns = [
            # Indian: +91 / 0 prefix + 10-digit mobile
            (re.compile(
                r'(?:\+91|0)[\s\-]?[6-9]\d{4}[\s\-]?\d{5}\b'
            ), 0.9),
            # US: (XXX) XXX-XXXX
            (re.compile(
                r'\(\d{3}\)\s?\d{3}[\-\s]\d{4}\b'
            ), 0.9),
            # US: XXX-XXX-XXXX (no country code)
            (re.compile(
                r'(?<!\d)\d{3}[\-]\d{3}[\-]\d{4}(?!\d)'
            ), 0.85),
            # International with +CC prefix
            (re.compile(
                r'\+[1-9]\d{0,2}[\s\-](?:\d[\s\-]?){8,14}\d\b'
            ), 0.9),
            # Indian bare 10-digit mobile (starts with 6-9)
            (re.compile(
                r'(?<!\d)[6-9]\d{4}[\s]?\d{5}(?!\d)'
            ), 0.75),
        ]

    def detect(self, text: str) -> List[DetectionResult]:
        results = []
        matched_spans = set()

        for pattern, confidence in self.patterns:
            for match in pattern.finditer(text):
                start, end = match.span()

                # Skip if overlapping with an already-matched span
                if any(s < end and e > start for s, e in matched_spans):
                    continue

                # Must have at least 10 digits
                digits = re.sub(r'\D', '', match.group())
                if len(digits) < 10:
                    continue

                matched_spans.add((start, end))
                results.append(DetectionResult(
                    text=match.group(),
                    start=start,
                    end=end,
                    pii_type=PHONE,
                    confidence=confidence,
                ))

        return results
