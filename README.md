# PII Redaction Tool

A production-grade tool that reads `.docx` documents, detects **9 types of personally identifiable information (PII)**, and produces a redacted copy where every PII instance is replaced with a **consistent fake alternative** — the same real value always maps to the same fake value everywhere it appears.

## Live Demo

**Deployed at:** *(Render URL — add after deployment)*

Upload any `.docx` file → view a color-coded before/after diff → download the redacted document.

---

## Quick Start (Local)

```bash
# 1. Clone and install
git clone <repo-url>
cd pii-redaction-tool
pip install -r requirements.txt

# 2. Run the web UI
uvicorn api.main:app --host 0.0.0.0 --port 8000
# Open http://localhost:8000

# 3. Or run the CLI
python run_redaction.py
```

---

## Approach

### Hybrid detection strategy: regex + GLiNER Zero-Shot NER

| PII Type | Method | Rationale |
|----------|--------|-----------|
| **Email** | Regex | Well-defined syntax — regex achieves near-perfect precision/recall |
| **Phone** | Regex | Structured formats (+91, (XXX), international) — regex with format-specific patterns |
| **SSN** | Regex | Exact format (XXX-XX-XXXX) with area-number validation to reject invalid prefixes |
| **Credit Card** | Regex + **Luhn checksum** | Format matching alone produces false positives; Luhn validation eliminates them |
| **DOB** | Regex + context heuristic | Date patterns are ubiquitous; context keywords ("born", "DOB") disambiguate DOBs from other dates |
| **IP Address** | Regex | IPv4 (with octet validation) and IPv6 — well-defined syntax |
| **Names** | GLiNER (`knowledgator/gliner-pii-small-v1.0`) | Zero-shot NER — catches single-token Indian names, titled names ("Shri Kamal Sharma"), and table-cell text without sentence context |
| **Companies** | GLiNER (`knowledgator/gliner-pii-small-v1.0`) | Zero-shot NER — eliminates company-as-person misclassifications, preserves exclusion rules for subject company |
| **Addresses** | GLiNER (`knowledgator/gliner-pii-small-v1.0`) + PIN regex | Zero-shot location address matching + PIN-code context heuristics |

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                   FastAPI App                    │
│                  POST /redact                    │
└──────────────────────┬──────────────────────────┘
                       │
            ┌──────────▼──────────┐
            │  RedactionPipeline  │
            │   (core/redactor)   │
            └──────────┬──────────┘
                       │
     ┌─────────────────▼─────────────────┐
     │         For each paragraph /       │
     │           table cell:              │
     │                                    │
     │   ┌────────────────────────────┐   │
     │   │   Run all 9 detectors     │   │
     │   │   → List[DetectionResult] │   │
     │   └────────────┬───────────────┘   │
     │                │                   │
     │   ┌────────────▼───────────────┐   │
     │   │   Resolve overlapping     │   │
     │   │   spans (wider wins)      │   │
     │   └────────────┬───────────────┘   │
     │                │                   │
     │   ┌────────────▼───────────────┐   │
     │   │   PIIMapper: real → fake  │   │
     │   │   (deterministic, seeded) │   │
     │   └────────────┬───────────────┘   │
     │                │                   │
     │   ┌────────────▼───────────────┐   │
     │   │   Replace within Runs     │   │
     │   │   (preserve formatting)   │   │
     │   └────────────────────────────┘   │
     └────────────────────────────────────┘
```

### Key modules

| Module | Purpose |
|--------|---------|
| `core/gliner_client.py` | Singleton model loader for `knowledgator/gliner-pii-small-v1.0` (with fallback to edge model) |
| `detectors/*.py` | One module per PII type, each returns `List[DetectionResult(text, start, end, pii_type, confidence)]` |
| `core/mapper.py` | Hash-seeded Faker generates deterministic fake values; persists to JSON for audit |
| `core/redactor.py` | Walks docx paragraph-by-paragraph and table-cell-by-cell; runs detectors; resolves overlaps; replaces text within existing `Run` objects to preserve formatting |
| `eval/evaluate.py` | Span-based evaluation: IoU > 0.5 matching, per-type precision/recall/F1 |
| `api/main.py` | FastAPI with upload, redaction, text diff extraction, and download |
| `frontend/index.html` | Single-page UI with drag-and-drop, diff view, and animated redaction bars |

---

## Explicit Design Decisions

### 1. Company names: selective redaction
**Decision:** Redact organization names detected by GLiNER, **except** the document's own subject company ("KSH International Limited" and its short forms).
**Rationale:** The prospectus mentions its subject company hundreds of times in structural boilerplate. Redacting these would make the document unreadable.

### 2. "Order" / "Ticket" numbers: not treated as PII
Sequential identifiers with no intrinsic personal info are not redacted.

### 3. Phone numbers: redacted
Mobile and corporate phone numbers are redacted per assignment requirements.

### 4. Missing PII types in source document
SSN, credit card, DOB, and IP detectors are validated via a synthetic test set with ground truth.

---

## Evaluation Benchmark (spaCy vs GLiNER)

See [EVALUATION.md](EVALUATION.md) for detailed evaluation logs and per-type analysis.

### In-Document Gold Standard Comparison

| PII Type | spaCy Precision | spaCy Recall | spaCy F1 | GLiNER Precision | GLiNER Recall | GLiNER F1 | Delta (F1) |
|---|---|---|---|---|---|---|---|
| **NAME** | 0.562 | 0.574 | 0.568 | 0.464 | **0.957** | **0.625** | **+10.0%** |
| **COMPANY** | 0.481 | 0.520 | 0.500 | **0.722** | 0.520 | **0.605** | **+21.0%** |
| **ADDRESS** | 0.250 | 0.125 | 0.167 | **0.727** | **0.667** | **0.696** | **+316.8%** |
| **EMAIL** | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.0% |
| **OVERALL** | 0.604 | 0.558 | 0.580 | 0.609 | **0.817** | **0.698** | **+20.3%** |

---

## Project Structure

```
├── api/
│   └── main.py              # FastAPI app
├── core/
│   ├── gliner_client.py     # GLiNER zero-shot model loader
│   ├── mapper.py             # Real → fake value mapper
│   └── redactor.py           # Document-level pipeline
├── detectors/
│   ├── base.py               # DetectionResult type + constants
│   ├── names.py              # GLiNER Person Name detector
│   ├── companies.py          # GLiNER Company detector with exclusion list
│   ├── addresses.py          # GLiNER Address detector + PIN regex
│   ├── emails.py             # Regex
│   ├── phones.py             # Regex (Indian + US + international)
│   ├── ssn.py                # Regex with area validation
│   ├── credit_card.py        # Regex + Luhn checksum
│   ├── dob.py                # Regex + context heuristic
│   └── ip_address.py         # Regex (IPv4 + IPv6)
├── eval/
│   ├── evaluate.py           # Evaluation harness
│   ├── gold_standard.json    # Manual annotations
│   └── synthetic_test.py     # Synthetic SSN/CC/DOB/IP tests
├── frontend/
│   └── index.html            # Web UI
├── tests/                    # Unit tests per detector
├── output/                   # Generated redacted files
├── requirements.txt
├── Procfile                  # Render process file
├── render.yaml               # Render deploy config
└── README.md
```
