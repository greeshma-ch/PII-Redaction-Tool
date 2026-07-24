from detectors.credit_card import CreditCardDetector
from detectors.base import CREDIT_CARD


def test_valid_visa():
    detector = CreditCardDetector()
    # 4111 1111 1111 1111 is a known Visa test number that passes Luhn
    text = "My card is 4111 1111 1111 1111."
    results = detector.detect(text)
    assert len(results) == 1
    assert results[0].text.strip() == "4111 1111 1111 1111"
    assert results[0].pii_type == CREDIT_CARD
    assert results[0].confidence == 0.95


def test_valid_visa_hyphenated():
    detector = CreditCardDetector()
    text = "Card: 4111-1111-1111-1111."
    results = detector.detect(text)
    assert len(results) == 1
    assert results[0].confidence == 0.95


def test_invalid_luhn():
    detector = CreditCardDetector()
    # 4000 0000 0000 0000 fails Luhn
    text = "Failing Luhn: 4000 0000 0000 0000."
    results = detector.detect(text)
    assert len(results) == 0


def test_random_digits_not_matched():
    detector = CreditCardDetector()
    text = "Order 1234 5678 9012 3456 is confirmed."
    results = detector.detect(text)
    # Should not match — doesn't start with valid card prefix or fails Luhn
    assert len(results) == 0
