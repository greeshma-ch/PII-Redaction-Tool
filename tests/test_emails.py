from detectors.emails import EmailDetector
from detectors.base import EMAIL

def test_valid_emails():
    detector = EmailDetector()
    text = "Send an email to john.doe@example.com or jane_doe+test@domain.co.uk."
    results = detector.detect(text)
    assert len(results) == 2
    assert results[0].text == "john.doe@example.com"
    assert results[1].text == "jane_doe+test@domain.co.uk"
    assert all(r.pii_type == EMAIL for r in results)
    assert all(r.confidence == 0.95 for r in results)

def test_invalid_emails():
    detector = EmailDetector()
    text = "This is not an email @ but this is invalid@com without dot and plain.text@."
    results = detector.detect(text)
    assert len(results) == 0
