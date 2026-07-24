"""Run the redaction pipeline on the Red Herring Prospectus."""

import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.redactor import RedactionPipeline

INPUT_FILE = "Red Herring Prospectus.docx"
OUTPUT_FILE = "output/Red_Herring_Prospectus_redacted.docx"
MAPPING_FILE = "output/mapping.json"
LOG_FILE = "output/redaction_log.json"

def main():
    os.makedirs("output", exist_ok=True)
    
    print(f"Processing: {INPUT_FILE}")
    print("This may take several minutes for a large document...")
    
    pipeline = RedactionPipeline(mapping_path=MAPPING_FILE)
    summary = pipeline.process(
        input_path=INPUT_FILE,
        output_path=OUTPUT_FILE,
        mapping_output=MAPPING_FILE,
        log_output=LOG_FILE,
    )
    
    print("\n=== Redaction Summary ===")
    print(f"Total redactions: {summary['total_redactions']}")
    print(f"\nBy PII type:")
    for pii_type, count in sorted(summary['by_type'].items()):
        print(f"  {pii_type:15s}: {count}")
    print(f"\nUnique mappings:")
    for pii_type, count in sorted(summary['unique_mappings'].items()):
        print(f"  {pii_type:15s}: {count}")
    print(f"\nTotal mapping uses (including repeats): {summary['total_mapping_uses']}")
    print(f"\nOutput saved to: {OUTPUT_FILE}")
    print(f"Mapping saved to: {MAPPING_FILE}")
    print(f"Redaction log saved to: {LOG_FILE}")

if __name__ == "__main__":
    main()
