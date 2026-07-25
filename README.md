# PII Redaction Tool

A production-grade tool that reads `.docx` documents, detects **9 types of personally identifiable information (PII)**, and produces a redacted copy where every PII instance is replaced with a **consistent fake alternative** — the same real value always maps to the same fake value everywhere it appears.

## Live Demo

**Deployed at:** `https://pii-redactiontool-401039116273.asia-south1.run.app/` — Google Cloud Run

Upload any `.docx` file → view a color-coded before/after diff → download the redacted document.

> **Note:** The submitted redacted `.docx` deliverable in `output/` was generated via direct pipeline execution, not the live web service — see [Limitations](#limitations) for why.

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
| **Names** | GLiNER (`knowledgator/gliner-pii-edge-v1.0`) | Zero-shot NER — catches single-token Indian names, titled names ("Shri Kamal Sharma"), and table-cell text without sentence context |
| **Companies** | GLiNER (`knowledgator/gliner-pii-edge-v1.0`) | Zero-shot NER — eliminates company-as-person misclassifications, preserves exclusion rules for subject company |
| **Addresses** | GLiNER (`knowledgator/gliner-pii-edge-v1.0`) + PIN regex | Zero-shot location address matching + PIN-code context heuristics |

> The lightweight `edge` variant is used in production for memory-constrained deployment (see [Deployment](#deployment)); the original evaluation in [EVALUATION.md](EVALUATION.md) was run against this same variant unless otherwise noted.

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
     │   │   spans within a type     │   │
     │   │   (wider wins)*           │   │
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

*Overlap resolution currently applies within a single detector's own output.
Cross-type deduplication (e.g. suppressing a NAME match when the same span is
already claimed by COMPANY or ADDRESS with higher confidence) is not yet
implemented — see EVALUATION.md's remaining-false-positives analysis, where
3 of 4 residual NAME errors are exactly this case.

### Key modules

| Module | Purpose |
|--------|---------|
| `core/gliner_client.py` | Singleton model loader for `knowledgator/gliner-pii-edge-v1.0` |
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

## Evaluation Results

Full methodology, false-positive/negative root-cause analysis, and the complete
six-stage tuning history are in [EVALUATION.md](EVALUATION.md). Summary of the
final, in-document gold-standard results:

| Type | Precision | Recall | F1 |
|------|-----------|--------|-----|
| EMAIL | 1.000 | 1.000 | 1.000 |
| NAME | 0.918 | 0.957 | 0.938 |
| COMPANY | 1.000 | 0.960 | 0.980 |
| ADDRESS | 1.000 | 1.000 | 1.000 |
| **OVERALL** | **0.967** | **0.975** | **0.971** |

The detection engine evolved through six stages — spaCy baseline → GLiNER
zero-shot swap → threshold/label refinements → empirical false-positive root-cause
fixes → PIN-city address merge → email-boundary filter correction — with overall
F1 improving from 0.580 to 0.971. Each stage's fix was diagnosed from actual
false-positive/negative text rather than assumption; see EVALUATION.md for the
full before/after table and an explicit note on where these numbers may be
optimistic due to iterative tuning against a fixed evaluation sample.

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
├── Dockerfile                 # Container build for Cloud Run
└── README.md
```

---

## Deployment

Deployed on **Google Cloud Run** (containerized via the included `Dockerfile`),
not a buildpack-based host — the GLiNER model's memory footprint exceeded the
512 MB ceiling of typical free-tier PaaS instances, so Cloud Run was chosen for
its configurable per-service memory allocation.

```bash
gcloud run deploy pii-redactiontool \
  --source . \
  --region asia-south1 \
  --memory 4Gi \
  --cpu 4 \
  --timeout 1500 \
  --allow-unauthenticated \
  --port 8080
```

The model is loaded lazily on first request (not at container startup), so the
first request after a cold start includes a one-time model-load delay.

---

## Limitations

- **Processing time on constrained CPU:** full-document processing (~90s on a
  local dev machine) takes considerably longer on Cloud Run's allocated vCPUs —
  budget several minutes for a large, table-heavy document like the sample
  prospectus on a cold instance.
- **Table cell alignment on the live service:** for documents with very large,
  multi-page tables using repeated header rows, the live web service has been
  observed to occasionally misalign redacted content between cells (a
  `python-docx` table-indexing edge case with repeated headers). The submitted
  `output/*.docx` deliverable was generated via direct pipeline execution
  (`python run_redaction.py`), which does not exhibit this issue — only the
  FastAPI web-upload code path is affected. This is a known open issue, not
  fixed as of submission.
- **Tuning generalizability:** see EVALUATION.md's overfitting caveat — several
  detector refinements were built from, and evaluated against, the same
  120-block gold-standard sample.
- **Indian-specific identifiers** (Aadhaar, PAN, passport numbers) are not yet
  supported; would be straightforward regex additions.