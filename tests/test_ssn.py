from detectors.ssn import SSNDetector
from detectors.base import SSN

def test_valid_ssn():
    detector = SSNDetector()
    text = "My SSN is 123-45-6789."
    results = detector.detect(text)
    assert len(results) == 1
    assert results[0].text == "123-45-6789"
    assert results[0].pii_type == SSN
    assert results[0].confidence == 0.9

def test_invalid_ssn():
    detector = SSNDetector()
    text = "Invalid ones: 000-12-3456, 666-12-3456, 900-12-3456, 123-00-1234, 123-12-0000."
    results = detector.detect(text)
    assert len(results) == 0
