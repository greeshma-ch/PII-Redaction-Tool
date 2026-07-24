"""Step 1 diagnostic: Extract every ADDRESS false negative from the gold standard
and determine whether the missed address spans cross cell boundaries (multi-cell)
or were single-cell misses by GLiNER."""

import json
from detectors.addresses import AddressDetector
from eval.evaluate import Evaluator

def main():
    detector = AddressDetector()
    evaluator = Evaluator()

    with open("eval/gold_standard.json", "r") as f:
        gold_data = json.load(f)

    fn_entries = []  # (gold_text, gold_start, gold_end, block_text, block_idx)
    fp_entries = []
    tp_entries = []

    for idx, entry in enumerate(gold_data):
        text = entry["text"]
        gold_annotations = [a for a in entry["annotations"] if a["pii_type"] == "ADDRESS"]
        detections = detector.detect(text)

        matched_gold = set()
        matched_det = set()

        for i, g in enumerate(gold_annotations):
            for j, d in enumerate(detections):
                if j in matched_det:
                    continue
                if evaluator._iou(g["start"], g["end"], d.start, d.end) > 0.5:
                    matched_gold.add(i)
                    matched_det.add(j)
                    tp_entries.append((g, text, idx))
                    break

        for i, g in enumerate(gold_annotations):
            if i not in matched_gold:
                gold_text = text[g["start"]:g["end"]]
                fn_entries.append((gold_text, g["start"], g["end"], text, idx))

        for j, d in enumerate(detections):
            if j not in matched_det:
                fp_entries.append((d.text, d.start, d.end, text, idx))

    print(f"=== ADDRESS Evaluation Breakdown ===")
    print(f"True Positives: {len(tp_entries)}")
    print(f"False Positives: {len(fp_entries)}")
    print(f"False Negatives: {len(fn_entries)}")

    print(f"\n=== ADDRESS FALSE NEGATIVES ({len(fn_entries)}) ===")
    for i, (gold_text, start, end, block_text, block_idx) in enumerate(fn_entries):
        print(f"\n  FN #{i+1} (block {block_idx}):")
        print(f"    Gold text:  '{gold_text}'")
        print(f"    Span:       [{start}:{end}]")
        print(f"    Full block: '{block_text}'")
        
        # Check if gold text contains typical multi-cell indicators
        has_comma_sep = ", " in gold_text
        has_newline = "\n" in gold_text
        has_pin = any(c.isdigit() for c in gold_text[-6:]) if len(gold_text) >= 6 else False
        print(f"    Indicators: comma_sep={has_comma_sep}, newline={has_newline}, ends_with_digits={has_pin}")

    print(f"\n=== ADDRESS FALSE POSITIVES ({len(fp_entries)}) ===")
    for i, (det_text, start, end, block_text, block_idx) in enumerate(fp_entries):
        print(f"\n  FP #{i+1} (block {block_idx}):")
        print(f"    Detected text: '{det_text}'")
        print(f"    Full block:    '{block_text}'")

if __name__ == "__main__":
    main()
