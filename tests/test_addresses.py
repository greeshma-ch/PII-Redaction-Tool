import pytest
from detectors.addresses import AddressDetector
from detectors.base import DetectionResult, ADDRESS

def test_standalone_city():
    detector = AddressDetector()
    results = detector.detect("I live in Mumbai.")
    assert any(r.text == "Mumbai" and r.confidence >= 0.5 for r in results)

def test_pin_code_with_keywords():
    detector = AddressDetector()
    results = detector.detect("The building is at MG Road, 400001.")
    assert any("400001" in r.text for r in results)

def test_merged_address():
    detector = AddressDetector()
    results = detector.detect("My address is MG Road, Mumbai, Maharashtra.")
    addresses = [r.text for r in results]
    # Depending on spaCy's exact parsing, we verify it captures the locations
    assert any("Mumbai" in a or "Maharashtra" in a for a in addresses)

def test_no_address():
    detector = AddressDetector()
    results = detector.detect("There is nothing here.")
    assert len(results) == 0
