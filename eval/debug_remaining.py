"""Read-only diagnostic: extract exact text of remaining NAME FPs and COMPANY FNs."""

import json
from detectors.names import NameDetector
from detectors.companies import CompanyDetector
from eval.evaluate import Evaluator

def main():
    name_det = NameDetector()
    company_det = CompanyDetector()
    evaluator = Evaluator()

    with open("eval/gold_standard.json", "r") as f:
        gold_data = json.load(f)

    name_fps = []
    company_fns = []

    for idx, entry in enumerate(gold_data):
        text = entry["text"]

        # --- NAME FPs ---
        gold_names = [a for a in entry["annotations"] if a["pii_type"] == "NAME"]
        name_preds = name_det.detect(text)

        matched_det = set()
        for i, g in enumerate(gold_names):
            for j, d in enumerate(name_preds):
                if j in matched_det:
                    continue
                if evaluator._iou(g["start"], g["end"], d.start, d.end) > 0.5:
                    matched_det.add(j)
                    break

        for j, d in enumerate(name_preds):
            if j not in matched_det:
                name_fps.append((d.text, d.start, d.end, d.confidence, text, idx))

        # --- COMPANY FNs ---
        gold_companies = [a for a in entry["annotations"] if a["pii_type"] == "COMPANY"]
        company_preds = company_det.detect(text)

        matched_gold = set()
        for i, g in enumerate(gold_companies):
            for j, d in enumerate(company_preds):
                if evaluator._iou(g["start"], g["end"], d.start, d.end) > 0.5:
                    matched_gold.add(i)
                    break

        for i, g in enumerate(gold_companies):
            if i not in matched_gold:
                gold_text = text[g["start"]:g["end"]]
                company_fns.append((gold_text, g["start"], g["end"], text, idx))

    print(f"=== NAME FALSE POSITIVES ({len(name_fps)}) ===")
    for i, (det_text, start, end, conf, block_text, block_idx) in enumerate(name_fps):
        print(f"  FP #{i+1} (block {block_idx}):")
        print(f"    Text:       '{det_text}'")
        print(f"    Confidence: {conf:.3f}")
        print(f"    Full block: '{block_text}'")

    print(f"\n=== COMPANY FALSE NEGATIVES ({len(company_fns)}) ===")
    for i, (gold_text, start, end, block_text, block_idx) in enumerate(company_fns):
        print(f"  FN #{i+1} (block {block_idx}):")
        print(f"    Gold text:  '{gold_text}'")
        print(f"    Span:       [{start}:{end}]")
        print(f"    Full block: '{block_text}'")

if __name__ == "__main__":
    main()
