import pytest
from detectors.names import NameDetector
from detectors.base import DetectionResult, NAME

def test_full_name():
    detector = NameDetector()
    results = detector.detect("My name is Rashi Patil.")
    assert len(results) >= 1
    assert any(r.text == "Rashi Patil" and r.pii_type == NAME and r.confidence == 0.85 for r in results)

def test_single_name():
    detector = NameDetector()
    results = detector.detect("Call John today.")
    assert len(results) >= 1
    names = [r.text for r in results if r.pii_type == NAME]
    assert "John" in names

def test_filters():
    detector = NameDetector()
    # Single char
    results = detector.detect("A went to the store.")
    assert not any(r.text == "A" for r in results)
    
    # Honorific
    results = detector.detect("Mr is here.")
    assert not any(r.text == "Mr" for r in results)

    # All caps < 3 chars
    results = detector.detect("He works at IT department.")
    assert not any(r.text == "IT" for r in results)
