import json
import os
from collections import namedtuple

try:
    from detectors.ssn import SSNDetector
    from detectors.credit_card import CreditCardDetector
    from detectors.dob import DOBDetector
    from detectors.ip_address import IPAddressDetector
except ImportError:
    pass

DetectionResult = namedtuple('DetectionResult', ['text', 'start', 'end', 'pii_type', 'confidence'])

def run_synthetic_tests():
    # SSN Test cases
    ssn_tests = [
        ("My SSN is 123-45-6789.", [("123-45-6789", "SSN")]),
        ("Social security: 987-65-4321", [("987-65-4321", "SSN")]),
        ("Invalid SSN 123-45-67890", []),
        ("Another invalid 000-45-6789", []), # often 000 is invalid in area
        ("He gave his SSN as 555-55-5555.", [("555-55-5555", "SSN")]),
        ("Not an SSN: 12-345-6789", []),
        ("Valid: 111-22-3333 is mine.", [("111-22-3333", "SSN")]),
        ("Text without SSN here.", []),
    ] * 3 # Expand to ~24 cases

    # CC Test cases (some dummy valid Luhn vs invalid)
    # Using simple dummy numbers for testing structural matches
    cc_tests = [
        ("Visa: 4111-1111-1111-1111", [("4111-1111-1111-1111", "CREDIT_CARD")]),
        ("Mastercard: 5555-5555-5555-5555", [("5555-5555-5555-5555", "CREDIT_CARD")]),
        ("Amex: 3782-822463-10005", [("3782-822463-10005", "CREDIT_CARD")]),
        ("Invalid: 4111-1111-1111-1112", []),
        ("No card here", []),
    ] * 4 # Expand to ~20 cases
    
    # DOB Test cases
    dob_tests = [
        ("Date of birth: 01/01/1990", [("01/01/1990", "DOB")]),
        ("DOB 12-31-1985", [("12-31-1985", "DOB")]),
        ("Born on 1992-05-15", [("1992-05-15", "DOB")]),
        ("Meeting on 01/01/2025", []), # Not a DOB
        ("Her birthdate is Jan 5, 2000.", [("Jan 5, 2000", "DOB")]),
    ] * 4 # Expand to ~20 cases
    
    # IP Address Test cases
    ip_tests = [
        ("Login from 192.168.1.1", [("192.168.1.1", "IP_ADDRESS")]),
        ("Server IP is 10.0.0.255", [("10.0.0.255", "IP_ADDRESS")]),
        ("IPv6 addr: 2001:0db8:85a3:0000:0000:8a2e:0370:7334", [("2001:0db8:85a3:0000:0000:8a2e:0370:7334", "IP_ADDRESS")]),
        ("Invalid IP 256.256.256.256", []),
        ("Ping 8.8.8.8 for test", [("8.8.8.8", "IP_ADDRESS")]),
    ] * 4 # Expand to ~20 cases

    all_tests = {
        "SSN": ssn_tests,
        "CREDIT_CARD": cc_tests,
        "DOB": dob_tests,
        "IP_ADDRESS": ip_tests
    }
    
    try:
        detectors = {
            "SSN": SSNDetector(),
            "CREDIT_CARD": CreditCardDetector(),
            "DOB": DOBDetector(),
            "IP_ADDRESS": IPAddressDetector()
        }
    except NameError:
        print("Detectors not available to run tests.")
        return

    print("=== Synthetic PII Detection Evaluation ===")
    print(f"{'Type':<15} {'TP':<4} {'FP':<4} {'FN':<4} {'Precision':<10} {'Recall':<10} {'F1':<10}")
    
    for ptype, tests in all_tests.items():
        detector = detectors[ptype]
        tp = 0
        fp = 0
        fn = 0
        
        for text, golds in tests:
            detected = detector.detect(text)
            # Simple exact match for synthetic tests
            gold_vals = [g[0] for g in golds]
            det_vals = [d.text for d in detected]
            
            matched_gold = []
            for d in det_vals:
                if d in gold_vals:
                    tp += 1
                    matched_gold.append(d)
                else:
                    fp += 1
                    
            for g in gold_vals:
                if g not in matched_gold:
                    fn += 1
                    
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        print(f"{ptype:<15} {tp:<4} {fp:<4} {fn:<4} {precision:<10.3f} {recall:<10.3f} {f1:<10.3f}")

if __name__ == "__main__":
    run_synthetic_tests()
