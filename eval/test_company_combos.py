"""A/B Testing script for COMPANY label wording, threshold, and gazetteer boost."""

import json
from detectors.names import NameDetector
from detectors.companies import CompanyDetector
from detectors.addresses import AddressDetector
from detectors.emails import EmailDetector
from detectors.phones import PhoneDetector
from detectors.ssn import SSNDetector
from detectors.credit_card import CreditCardDetector
from detectors.dob import DOBDetector
from detectors.ip_address import IPAddressDetector
from eval.evaluate import Evaluator

def main():
    evaluator = Evaluator()
    with open("eval/gold_standard.json", "r") as f:
        gold_data = json.load(f)

    base_detectors = [
        EmailDetector(), PhoneDetector(), SSNDetector(), CreditCardDetector(),
        DOBDetector(), IPAddressDetector(), NameDetector(), AddressDetector()
    ]

    labels_old = ["company name", "company", "organization"]
    labels_new = ["company, bank, or organization name, including abbreviations"]

    combos = [
        ("Combo 1: Old label / 0.3", labels_old, 0.30, False),
        ("Combo 2: Old label / 0.2", labels_old, 0.20, False),
        ("Combo 3: New label / 0.3", labels_new, 0.30, False),
        ("Combo 4: New label / 0.2", labels_new, 0.20, False),
        ("Combo 5: New label / 0.2 + Gazetteer", labels_new, 0.20, True),
        ("Combo 6: Old label / 0.25 + Gazetteer", labels_old, 0.25, True),
        ("Combo 7: Old label / 0.28 + Gazetteer", labels_old, 0.28, True),
        ("Combo 8: Old label / 0.30 + Gazetteer", labels_old, 0.30, True),
    ]

    print("=== COMPANY Detector A/B Testing Results ===")
    print(f"{'Combo Name':<38} {'Precision':<10} {'Recall':<10} {'F1':<10}")
    print("-" * 72)

    for name, labels, thresh, use_gazetteer in combos:
        comp_det = CompanyDetector(threshold=thresh)
        comp_det.labels = labels
        comp_det.use_gazetteer = use_gazetteer

        all_detectors = base_detectors + [comp_det]
        res = evaluator.evaluate(gold_data, all_detectors)
        metrics = res.compute()
        comp_m = metrics.get("COMPANY", {"Precision": 0, "Recall": 0, "F1": 0})
        print(f"{name:<38} {comp_m['Precision']:<10.3f} {comp_m['Recall']:<10.3f} {comp_m['F1']:<10.3f}")

if __name__ == "__main__":
    main()
