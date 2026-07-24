"""Base types and utilities shared across all PII detectors."""

from typing import NamedTuple, List, Protocol


class DetectionResult(NamedTuple):
    """A single detected PII span.

    Attributes:
        text:       The exact text that was matched.
        start:      Start character offset within the source string.
        end:        End character offset within the source string.
        pii_type:   One of the canonical PII type constants below.
        confidence: Float in [0, 1] indicating detection confidence.
    """
    text: str
    start: int
    end: int
    pii_type: str
    confidence: float


# ── Canonical PII type constants ─────────────────────────────────────────
NAME        = "NAME"
EMAIL       = "EMAIL"
PHONE       = "PHONE"
COMPANY     = "COMPANY"
ADDRESS     = "ADDRESS"
SSN         = "SSN"
CREDIT_CARD = "CREDIT_CARD"
DOB         = "DOB"
IP_ADDRESS  = "IP_ADDRESS"


class Detector(Protocol):
    """Interface that every detector module must satisfy."""

    def detect(self, text: str) -> List[DetectionResult]:
        """Return all PII spans found in *text*."""
        ...
