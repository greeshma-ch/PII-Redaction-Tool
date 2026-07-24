from detectors.credit_card import CreditCardDetector
from detectors.base import CREDIT_CARD

def test_valid_credit_card():
    detector = CreditCardDetector()
    # 4111 1111 1111 1111 is a known Visa test number that passes Luhn
    text = "My card is 4111 1111 1111 1111 and another is 4111-1111-1111-1111."
    results = detector.detect(text)
    assert len(results) == 2
    assert results[0].text == "4111 1111 1111 1111"
    assert results[0].confidence == 0.95

def test_invalid_credit_card():
    detector = CreditCardDetector()
    # 4000 0000 0000 0000 fails Luhn
    text = "Failing Luhn: 4000 0000 0000 0000. Just a random sequence: 1234 5678 9012 3456."
    results = detector.detect(text)
    # The current implementation drops cards failing Luhn, or does it? 
    # Ah, the requirement said 'only flag numbers that pass Luhn', and gave confidence 0.4 if not.
    # Wait, the code drops it if not passes_luhn. Let's make sure it does not flag them at all.
    assert len(results) == 0
