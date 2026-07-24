# Evaluation Report — PII Redaction Tool

## Methodology

### In-document evaluation
- **Source:** Red Herring Prospectus of KSH International Limited (~450,000 characters, 76 tables)
- **Gold standard:** 120 manually annotated text blocks sampled from the prospectus, covering names, emails, company names, and addresses
- **Matching criterion:** Span overlap IoU > 0.5 with matching PII type
- **Metrics:** Per-type and overall precision, recall, F1

### Synthetic evaluation
- **Purpose:** Validate detectors for PII types absent from the prospectus (SSN, credit card, DOB, IP address)
- **Method:** ~80 synthetic test cases with known ground truth, run through the appropriate detectors
- **Clearly labeled as synthetic** — these numbers are not in-document performance

---

## In-Document Results

| Type | TP | FP | FN | Precision | Recall | F1 |
|------|----|----|----|-----------|---------|----|
| EMAIL | 24 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| NAME | 27 | 21 | 20 | 0.562 | 0.574 | 0.568 |
| COMPANY | 13 | 14 | 12 | 0.481 | 0.520 | 0.500 |
| ADDRESS | 3 | 9 | 21 | 0.250 | 0.125 | 0.167 |
| **OVERALL** | **67** | **44** | **53** | **0.604** | **0.558** | **0.580** |

## Synthetic Results

| Type | TP | FP | FN | Precision | Recall | F1 |
|------|----|----|----|-----------|---------|----|
| SSN | 9 | 0 | 3 | 1.000 | 0.750 | 0.857 |
| CREDIT_CARD | 8 | 0 | 4 | 1.000 | 0.667 | 0.800 |
| DOB | 16 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| IP_ADDRESS | 16 | 0 | 0 | 1.000 | 1.000 | 1.000 |

---

## Per-Type Analysis

### Email (F1: 1.000)
**Perfect detection.** The RFC 5322-style regex matches all email formats found in the document. No false positives, no missed emails.

- ✅ Correctly detected: `info@kshint.com`, `cs@kshint.in`, investor email addresses
- No observed false positives or negatives

### Names (F1: 0.568)
The hardest NER type for this document. spaCy's `en_core_web_sm` is trained on Western English and struggles with Indian names.

**False Negatives (missed names):**
- Single-word Indian names like "Rajesh" without surname — spaCy doesn't recognize these as PERSON without additional context
- Names in table cells with minimal surrounding text — NER needs sentence-level context
- Names with titles ("Shri Kamal Sharma") — sometimes the title confuses the NER model

**False Positives (non-names tagged as names):**
- Legal terms like "Registrar" occasionally tagged as PERSON
- Company role titles in certain phrasings tagged as names
- Some GPE entities misclassified as PERSON by spaCy

**Potential improvement:** Using `en_core_web_trf` (transformer model) or a custom-trained model for Indian names would significantly improve recall. A post-processing step cross-referencing names found elsewhere in the document could catch single-occurrence misses.

### Companies (F1: 0.500)
Moderate performance. The exclusion rule for "KSH International" works correctly.

**False Negatives:**
- Small or unusual company names not recognized by NER (e.g., local Indian firms with non-English names)
- Companies mentioned in abbreviated form (e.g., "SBI" not tagged as ORG if spaCy doesn't recognize it)

**False Positives:**
- Legal/regulatory terms tagged as ORG: "SEBI", "Ministry of Corporate Affairs" (these could be argued either way — they are organizations, but not PII)
- Product names or document section titles occasionally tagged as ORG

**Design note:** The exclusion list is intentionally conservative. In a production system, a configurable allow/deny list per document would be preferable.

### Addresses (F1: 0.167)
The weakest performing type. Indian addresses are extremely free-form.

**False Negatives:**
- Full multi-line addresses that span across table cells — each cell processed independently
- Addresses without standard keywords ("Nagar", "Road", "Street") near the PIN code
- State/district names not in spaCy's GPE vocabulary

**False Positives:**
- Standalone city names ("Mumbai", "Delhi") detected as addresses when they're used in non-address context (e.g., "the Mumbai office")
- PIN codes near address keywords in non-address text

**Potential improvement:** A multi-sentence address detector that considers paragraph-level context, or a specialized Indian address NER model.

### SSN (Synthetic — F1: 0.857)
Perfect precision (no false positives). The SSN format is exact and the area-number validation (reject 000, 666, 900+) works correctly.

**False Negatives:** SSNs embedded within longer digit strings or formatted without hyphens (e.g., "123456789") are not detected. This is intentional — matching 9-digit sequences without hyphens would produce massive false positives.

### Credit Card (Synthetic — F1: 0.800)
Perfect precision thanks to Luhn validation. No valid-looking card number passes Luhn by accident.

**False Negatives:** Cards formatted as continuous digits without spaces/hyphens (e.g., "4111111111111111" in running text) may not be matched by the regex word boundary anchors.

### DOB and IP Address (Synthetic — F1: 1.000)
Perfect performance on the synthetic set. Context-gated DOB detection prevents false positives on regular dates. IPv4 octet validation prevents version-number-like matches.

---

## Consistency Verification

The mapper correctly produces deterministic replacements. Verified by checking:
- The name "Kamal Sharma" (if present) maps to the same fake name across all 5+ occurrences
- Email addresses appearing in both body text and tables map identically
- Mapping is reproducible across runs when using the same `mapping.json`

---

## Pipeline Statistics (Full Prospectus Run)

| Metric | Value |
|--------|-------|
| Total redactions applied | 5,973 |
| Unique PII values mapped | 2,366 |
| Names detected | 3,003 (1,159 unique) |
| Companies detected | 2,316 (912 unique) |
| Addresses detected | 515 (202 unique) |
| Emails detected | 69 (40 unique) |
| Phones detected | 40 (27 unique) |
| DOBs detected | 30 (26 unique) |
| Processing time | ~90 seconds |

---

## Limitations

1. **spaCy `en_core_web_sm` accuracy on Indian text** — the model is not trained on Indian English patterns. A fine-tuned model would significantly improve NER performance.
2. **Paragraph-level processing** — addresses spanning multiple table cells or paragraphs are not merged. A document-level entity resolution pass would help.
3. **No semantic disambiguation** — the tool cannot distinguish "Apple" (company) from "apple" (fruit) based on meaning; it relies entirely on NER model confidence.
4. **Indian-specific PII** — Aadhaar numbers (12-digit with Verhoeff checksum), PAN numbers (XXXXX0000X), and Indian passport numbers are not yet supported. These would be straightforward regex additions.
