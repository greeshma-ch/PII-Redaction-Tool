import json
import os
from collections import namedtuple
from typing import List

# Assuming detectors return List[DetectionResult] where DetectionResult = namedtuple('DetectionResult', ['text', 'start', 'end', 'pii_type', 'confidence'])
try:
    from detectors.emails import EmailDetector
    from detectors.phones import PhoneDetector
    from detectors.ssn import SSNDetector
    from detectors.credit_card import CreditCardDetector
    from detectors.dob import DOBDetector
    from detectors.ip_address import IPAddressDetector
    from detectors.names import NameDetector
    from detectors.companies import CompanyDetector
    from detectors.addresses import AddressDetector
except ImportError:
    pass

DetectionResult = namedtuple('DetectionResult', ['text', 'start', 'end', 'pii_type', 'confidence'])

class EvalResult:
    def __init__(self):
        self.metrics = {}
        self.overall = {"TP": 0, "FP": 0, "FN": 0}
        
    def add(self, pii_type, tp, fp, fn):
        if pii_type not in self.metrics:
            self.metrics[pii_type] = {"TP": 0, "FP": 0, "FN": 0}
        self.metrics[pii_type]["TP"] += tp
        self.metrics[pii_type]["FP"] += fp
        self.metrics[pii_type]["FN"] += fn
        self.overall["TP"] += tp
        self.overall["FP"] += fp
        self.overall["FN"] += fn
        
    def compute(self):
        results = {}
        for pii_type, counts in self.metrics.items():
            tp, fp, fn = counts["TP"], counts["FP"], counts["FN"]
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            results[pii_type] = {
                "TP": tp, "FP": fp, "FN": fn,
                "Precision": precision, "Recall": recall, "F1": f1
            }
        
        tp, fp, fn = self.overall["TP"], self.overall["FP"], self.overall["FN"]
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        results["OVERALL"] = {
            "TP": tp, "FP": fp, "FN": fn,
            "Precision": precision, "Recall": recall, "F1": f1
        }
        return results

class Evaluator:
    def __init__(self):
        pass

    def _iou(self, start1, end1, start2, end2):
        intersection = max(0, min(end1, end2) - max(start1, start2))
        union = max(end1, end2) - min(start1, start2)
        if union == 0:
            return 0.0
        return intersection / union

    def evaluate(self, gold_data: List[dict], detectors: List) -> EvalResult:
        result = EvalResult()
        
        for entry in gold_data:
            text = entry["text"]
            gold_annotations = entry["annotations"]
            
            detected = []
            for detector in detectors:
                detected.extend(detector.detect(text))
            
            # Group gold and detected by pii_type
            gold_by_type = {}
            for ann in gold_annotations:
                ptype = ann["pii_type"]
                gold_by_type.setdefault(ptype, []).append(ann)
                
            det_by_type = {}
            for det in detected:
                ptype = det.pii_type
                det_by_type.setdefault(ptype, []).append(det)
            
            all_types = set(gold_by_type.keys()).union(set(det_by_type.keys()))
            
            for ptype in all_types:
                gold_list = gold_by_type.get(ptype, [])
                det_list = det_by_type.get(ptype, [])
                
                matched_gold = set()
                matched_det = set()
                
                for i, g in enumerate(gold_list):
                    for j, d in enumerate(det_list):
                        if j in matched_det:
                            continue
                        if self._iou(g["start"], g["end"], d.start, d.end) > 0.5:
                            matched_gold.add(i)
                            matched_det.add(j)
                            break
                            
                tp = len(matched_gold)
                fn = len(gold_list) - len(matched_gold)
                fp = len(det_list) - len(matched_det)
                
                result.add(ptype, tp, fp, fn)
                
        return result

    def format_report(self, result: EvalResult) -> str:
        metrics = result.compute()
        
        lines = []
        lines.append("=== PII Detection Evaluation ===")
        lines.append(f"{'Type':<15} {'TP':<4} {'FP':<4} {'FN':<4} {'Precision':<10} {'Recall':<10} {'F1':<10}")
        
        for ptype in sorted(metrics.keys()):
            if ptype == "OVERALL": continue
            m = metrics[ptype]
            lines.append(f"{ptype:<15} {m['TP']:<4} {m['FP']:<4} {m['FN']:<4} {m['Precision']:<10.3f} {m['Recall']:<10.3f} {m['F1']:<10.3f}")
            
        if "OVERALL" in metrics:
            m = metrics["OVERALL"]
            lines.append("-" * 65)
            lines.append(f"{'OVERALL':<15} {m['TP']:<4} {m['FP']:<4} {m['FN']:<4} {m['Precision']:<10.3f} {m['Recall']:<10.3f} {m['F1']:<10.3f}")
            
        return "\n".join(lines)

    def save_report(self, result: EvalResult, path: str) -> None:
        metrics = result.compute()
        with open(path, "w") as f:
            json.dump(metrics, f, indent=2)


if __name__ == "__main__":
    try:
        detectors = [
            EmailDetector(), PhoneDetector(), SSNDetector(), CreditCardDetector(),
            DOBDetector(), IPAddressDetector(), NameDetector(), CompanyDetector(),
            AddressDetector()
        ]
    except NameError:
        print("Detectors not available to instantiate.")
        detectors = []
        
    evaluator = Evaluator()
    gold_path = os.path.join(os.path.dirname(__file__), "gold_standard.json")
    if os.path.exists(gold_path):
        with open(gold_path, "r") as f:
            gold_data = json.load(f)
            
        result = evaluator.evaluate(gold_data, detectors)
        print(evaluator.format_report(result))
        evaluator.save_report(result, os.path.join(os.path.dirname(__file__), "eval_results.json"))
    else:
        print(f"Gold standard file not found at {gold_path}")
