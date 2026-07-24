from detectors.phones import PhoneDetector
from detectors.base import PHONE


def test_indian_phones():
    detector = PhoneDetector()
    text = "Call +91 98765 43210 or +91-98765-43210 or 09876543210."
    results = detector.detect(text)
    assert len(results) >= 3
    assert all(r.pii_type == PHONE for r in results)


def test_us_parenthesized():
    detector = PhoneDetector()
    text = "Contact (555) 123-4567."
    results = detector.detect(text)
    assert len(results) == 1
    assert results[0].pii_type == PHONE


def test_us_dashed():
    detector = PhoneDetector()
    text = "Call 555-123-4567."
    results = detector.detect(text)
    assert len(results) == 1


def test_international():
    detector = PhoneDetector()
    text = "Reach us at +1-555-123-4567."
    results = detector.detect(text)
    assert len(results) == 1
    assert results[0].confidence >= 0.85


def test_invalid_phones():
    detector = PhoneDetector()
    text = "Year 2024. PIN code 400001. Order number 12345."
    results = detector.detect(text)
    assert len(results) == 0
