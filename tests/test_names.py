import pytest
from detectors.names import NameDetector
from detectors.base import DetectionResult, NAME


def test_full_name():
    detector = NameDetector()
    results = detector.detect("My name is Rashi Patil.")
    assert len(results) >= 1
    assert any(r.pii_type == NAME and r.confidence == 0.85 for r in results)


def test_name_in_context():
    detector = NameDetector()
    # spaCy recognises names better with surrounding context
    results = detector.detect("John Smith is the CEO of the company.")
    assert len(results) >= 1
    names = [r.text for r in results if r.pii_type == NAME]
    assert any("John" in n for n in names)


def test_filters_single_char():
    detector = NameDetector()
    results = detector.detect("A went to the store.")
    assert not any(r.text == "A" for r in results)


def test_filters_honorific():
    detector = NameDetector()
    results = detector.detect("Mr is here.")
    assert not any(r.text == "Mr" for r in results)


def test_filters_short_caps():
    detector = NameDetector()
    results = detector.detect("He works at IT department.")
    assert not any(r.text == "IT" for r in results)
