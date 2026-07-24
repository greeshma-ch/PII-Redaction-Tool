import pytest
from detectors.companies import CompanyDetector
from detectors.base import DetectionResult, COMPANY

def test_company_detection():
    detector = CompanyDetector()
    results = detector.detect("Apple is releasing a new phone.")
    assert any(r.text == "Apple" and r.pii_type == COMPANY for r in results)

def test_company_exclusion():
    detector = CompanyDetector()
    results = detector.detect("KSH International Limited reported good earnings.")
    assert not any(r.text == "KSH International Limited" for r in results)
    
def test_custom_exclusion():
    detector = CompanyDetector(exclusions={"MyCorp"})
    results = detector.detect("MyCorp and Apple are partnering.")
    orgs = [r.text for r in results]
    assert "MyCorp" not in orgs
    assert "Apple" in orgs
