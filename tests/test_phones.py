from detectors.phones import PhoneDetector
from detectors.base import PHONE

def test_indian_phones():
    detector = PhoneDetector()
    text = "Call +91 98765 43210, +91-98765-43210, 09876543210, or 9876543210."
    results = detector.detect(text)
    assert len(results) == 4
    assert all(r.pii_type == PHONE for r in results)

def test_us_phones():
    detector = PhoneDetector()
    text = "Contact (555) 123-4567, 555-123-4567, +1-555-123-4567."
    results = detector.detect(text)
    assert len(results) == 3

def test_invalid_phones():
    detector = PhoneDetector()
    text = "Year 2024. PIN code 400001. Order number 12345. Short +1 234."
    results = detector.detect(text)
    assert len(results) == 0
