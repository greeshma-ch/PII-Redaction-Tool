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
python -m spacy download en_core_web_sm

# 2. Run the web UI
uvicorn api.main:app --host 0.0.0.0 --port 8000
# Open http://localhost:8000

# 3. Or run the CLI
python run_redaction.py
```

---

## Approach

### Hybrid detection strategy: regex + NER

| PII Type | Method | Rationale |
|----------|--------|-----------|
| **Email** | Regex | Well-defined syntax — regex achieves near-perfect precision/recall |
| **Phone** | Regex | Structured formats (+91, (XXX), international) — regex with format-specific patterns |
| **SSN** | Regex | Exact format (XXX-XX-XXXX) with area-number validation to reject invalid prefixes |
| **Credit Card** | Regex + **Luhn checksum** | Format matching alone produces false positives; Luhn validation eliminates them |
| **DOB** | Regex + context heuristic | Date patterns are ubiquitous; context keywords ("born", "DOB") disambiguate DOBs from other dates |
| **IP Address** | Regex | IPv4 (with octet validation) and IPv6 — well-defined syntax |
| **Names** | spaCy NER (`PERSON`) | Free-form text — no regex pattern exists for names; NER is the only viable approach |
| **Companies** | spaCy NER (`ORG`) | Same reasoning; organization names are irregular and context-dependent |
| **Addresses** | spaCy NER (`GPE`/`LOC`/`FAC`) + regex | NER handles city/state names; regex handles structured Indian addresses (PIN codes near address keywords) |

**Why not a single approach?**
- Pure regex can't detect names or companies (too many patterns, too context-dependent)
- Pure NER misses structured types like emails and IPs (not in NER training data)
- The hybrid approach uses each method where it performs best

### spaCy model choice

Using `en_core_web_sm` (small model). Tradeoffs:
- ✅ Fast (~1 min for 450K-char document)
- ✅ Small footprint for deployment (50 MB vs 400+ MB for transformer model)
- ⚠️ Lower accuracy on Indian names — the model is trained primarily on Western English text
- ⚠️ Some organization names misclassified as person names and vice versa

Upgrading to `en_core_web_trf` (transformer model) would improve NER accuracy ~5-10% but would require GPU for reasonable processing times and increase deploy size significantly.

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
| `detectors/*.py` | One module per PII type, each returns `List[DetectionResult(text, start, end, pii_type, confidence)]` |
| `core/mapper.py` | Hash-seeded Faker generates deterministic fake values; persists to JSON for audit |
| `core/redactor.py` | Walks docx paragraph-by-paragraph and table-cell-by-cell; runs detectors; resolves overlaps; replaces text within existing `Run` objects to preserve formatting |
| `eval/evaluate.py` | Span-based evaluation: IoU > 0.5 matching, per-type precision/recall/F1 |
| `api/main.py` | FastAPI with upload, redaction, text diff extraction, and download |
| `frontend/index.html` | Single-page UI with drag-and-drop, diff view, and animated redaction bars |

---

## Explicit Design Decisions

### 1. Company names: selective redaction

**Decision:** Redact organization names detected by NER, **except** the document's own subject company ("KSH International Limited" and its short forms).

**Rationale:** A Red Herring Prospectus mentions its subject company hundreds of times in structural/legal boilerplate. Redacting these would make the document unreadable without adding privacy value — the company name is public information, printed on the cover page.

The `CompanyDetector` maintains a configurable exclusion set (default: `{'KSH International Limited', 'KSH International', 'KSH'}`). Other organization names (banks, auditors, legal firms mentioned as counterparties or affiliations) **are** redacted because they can identify individuals through association.

### 2. "Order" / "Ticket" numbers: not treated as PII

**Decision:** Sequential identifiers like order numbers, ticket numbers, and reference IDs are **not** redacted.

**Rationale:** These are system-generated identifiers with no intrinsic personal information. Redacting them would produce false positives with no privacy benefit. The credit card detector's Luhn validation specifically prevents long digit sequences (like order numbers) from being misclassified as card numbers.

### 3. Phone numbers: redacted (diverging from the assignment example)

**Decision:** Phone numbers **are** redacted, even though the assignment's one-shot example shows `+91 9876543210 → +91 9876543210` (unchanged).

**Rationale:** The assignment brief explicitly lists phone numbers as one of the 9 PII types to detect and redact. The example appears to be an oversight — phone numbers are clearly PII (especially mobile numbers, which are linked to identity in India via Aadhaar-SIM linking). We treat the type list as authoritative over the single example.

### 4. Missing PII types in the source document

The Red Herring Prospectus contains **no SSNs, credit cards, clean-format phone numbers, or explicit DOBs**. This is expected:
- India doesn't use SSNs (the equivalent, Aadhaar numbers, have a different format)
- IPO filings don't contain payment card numbers or birth dates
- Phone numbers in Indian corporate filings are typically formatted as part of addresses

**How we handle this:** Detectors for SSN/CC/DOB/IP are validated against a **synthetic test set** with known ground truth. Results are clearly labeled as "synthetic validation" in the evaluation report, separate from the in-document metrics.

### 5. Date-of-birth detection: context-gated

**Decision:** Dates are flagged as DOB only when context keywords ("born", "DOB", "date of birth", "birthday") appear within 50 characters before the date, AND the year falls within 1900-2015.

**Rationale:** The prospectus contains hundreds of dates (filing dates, incorporation dates, financial period dates). Flagging all of them as DOBs would produce catastrophic false positives. The context gate reduces false positives to near zero at the cost of missing DOBs without explicit context markers.

---

## How to Extend (Adding a New PII Type)

1. **Create a detector:** Add `detectors/your_type.py` with a class implementing `detect(text) → List[DetectionResult]`
2. **Add the PII type constant** to `detectors/base.py`
3. **Register in the pipeline:** Add an instance to `self.detectors` in `core/redactor.py`
4. **Add faker generation:** Add a lambda to `_generate_fake()` in `core/mapper.py`
5. **Write tests:** Add `tests/test_your_type.py`
6. **Update gold standard:** Add annotated examples to `eval/gold_standard.json`

Total: ~30 minutes for a new type with clean regex, ~2 hours if NER customization is needed.

---

## Evaluation Results

See [EVALUATION.md](EVALUATION.md) for full results with specific false positive/false negative examples.

### Summary

**In-document evaluation** (gold standard — names, emails, companies, addresses):

| Type | Precision | Recall | F1 |
|------|-----------|--------|-----|
| EMAIL | 1.000 | 1.000 | 1.000 |
| NAME | 0.562 | 0.574 | 0.568 |
| COMPANY | 0.481 | 0.520 | 0.500 |
| ADDRESS | 0.250 | 0.125 | 0.167 |
| **OVERALL** | **0.604** | **0.558** | **0.580** |

**Synthetic validation** (SSN, credit card, DOB, IP):

| Type | Precision | Recall | F1 |
|------|-----------|--------|-----|
| SSN | 1.000 | 0.750 | 0.857 |
| CREDIT_CARD | 1.000 | 0.667 | 0.800 |
| DOB | 1.000 | 1.000 | 1.000 |
| IP_ADDRESS | 1.000 | 1.000 | 1.000 |

### Key observations

- **Emails**: Perfect detection — regex is deterministic for well-formed addresses
- **Names**: spaCy misses some Indian names (not in its training data) and occasionally tags organizations or titles as persons
- **Companies**: The exclusion rule works correctly; FPs come from spaCy tagging product names or legal terms as ORGs
- **Addresses**: Hardest type — Indian addresses are free-form and lack consistent structure. NER catches major cities but misses smaller localities
- **Regex types**: 100% precision (zero false positives) thanks to format validation (Luhn, area code checks, context gating)

---

## Tradeoffs

| Decision | Pro | Con |
|----------|-----|-----|
| `en_core_web_sm` over `en_core_web_trf` | Fast, small deploy | ~10% lower NER accuracy |
| Luhn validation on credit cards | Zero false positives | Misses cards with entry errors |
| DOB context gating | Near-zero FP on dates | Misses DOBs without context markers |
| Company exclusion list | Prospectus remains readable | Must be configured per document |
| Overlap resolution (wider wins) | No double-redaction | May occasionally choose wrong span type |

---

## Project Structure

```
├── api/
│   └── main.py              # FastAPI app
├── core/
│   ├── mapper.py             # Real → fake value mapper
│   └── redactor.py           # Document-level pipeline
├── detectors/
│   ├── base.py               # DetectionResult type + constants
│   ├── _nlp_loader.py        # Shared spaCy model singleton
│   ├── names.py              # PERSON NER
│   ├── companies.py          # ORG NER with exclusion list
│   ├── addresses.py          # GPE/LOC NER + regex
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
├── output/                   # Generated redacted files (gitignored)
├── requirements.txt
├── Procfile                  # Render/Heroku process file
├── render.yaml               # Render deploy config
└── README.md
```

---

## License

Built as a take-home assignment. Not licensed for production use.
