from detectors.dob import DOBDetector
from detectors.base import DOB

def test_dob_with_context():
    detector = DOBDetector()
    text = "The patient was born on 05/12/1990 in London. DOB: Jan 12, 1985."
    results = detector.detect(text)
    assert len(results) == 2
    assert results[0].text == "05/12/1990"
    assert results[0].confidence == 0.85
    assert results[1].text == "Jan 12, 1985"
    assert results[1].confidence == 0.85

def test_dob_without_context():
    detector = DOBDetector()
    text = "We have a meeting on 10-10-1995."
    results = detector.detect(text)
    assert len(results) == 1
    assert results[0].confidence == 0.4

def test_impossible_dates():
    detector = DOBDetector()
    text = "born on 12/12/1899 or born on 01/01/2020." # outside 1900-2015 range
    results = detector.detect(text)
    assert len(results) == 0
