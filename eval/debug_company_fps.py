"""Diagnostic script to extract the exact text of every COMPANY false positive."""

import json
from detectors.companies import CompanyDetector
from eval.evaluate import Evaluator

def main():
    detector = CompanyDetector(threshold=0.28)
    with open("eval/gold_standard.json", "r") as f:
        gold_data = json.load(f)

    fps = []
    tps = []
    
    evaluator = Evaluator()

    for idx, entry in enumerate(gold_data):
        text = entry["text"]
        gold_annotations = [a for a in entry["annotations"] if a["pii_type"] == "COMPANY"]
        
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
                    tps.append((d.text, text))
                    break
                    
        for j, d in enumerate(detections):
            if j not in matched_det:
                fps.append((d.text, text, d.confidence))

    print(f"Total COMPANY Detections: {len(tps) + len(fps)}")
    print(f"True Positives ({len(tps)}):")
    for t, c in tps[:10]:
        print(f"  [TP] '{t}' in context: '{c}'")
        
    print(f"\nFalse Positives ({len(fps)}):")
    fp_text_counts = {}
    for t, c, conf in fps:
        fp_text_counts[t] = fp_text_counts.get(t, 0) + 1
        print(f"  [FP] '{t}' (conf: {conf:.2f}) in context: '{c}'")
        
    print("\n=== False Positive Text Frequencies ===")
    for text, count in sorted(fp_text_counts.items(), key=lambda x: -x[1]):
        print(f"  {count:2d}x : '{text}' (lower: '{text.lower()}')")

if __name__ == "__main__":
    main()
