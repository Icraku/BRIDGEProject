# BRIDGEProject

End-to-end pipeline for extracting structured clinical data from handwritten Neonatal Admission Record (NAR) forms using Vision-Language Models (VLMs). The system converts scanned form images through three sequential stages (extraction → structuring → evaluation) and compares three models (Qwen-VL, Gemma, MedGemma) against a ground-truth annotation set.

## Table of contents

1. [Project overview](#project-overview)
2. [Repository structure](#repository-structure)
3. [Requirements and setup](#requirements-and-setup)
4. [Environment variables](#environment-variables)
5. [Running the pipeline](#running-the-pipeline)
6. [Database tables reference](#database-tables-reference)
7. [Output files reference](#output-files-reference)
8. [Running individual modules](#running-individual-modules)
9. [Tests](#tests)
10. [Troubleshooting](#troubleshooting)

## Project overview

The BRIDGE pipeline processes two-page NAR forms through three stages:

```
Scanned images
     │
     ▼
┌─────────────┐
│  Stage A    │  a_input/ + b_extraction/
│  Extraction │  VLM reads image → markdown text
└──────┬──────┘
       │  saved to: extractions_{model}
       ▼
┌─────────────┐
│  Stage B    │  c_structuring/
│ Structuring │  markdown → NARFullRecord JSON (120 fields)
└──────┬──────┘
       │  saved to: structured_{model}, structured_{model}_required, structured_{model}_supplementary, mapped_{model}
       ▼
┌─────────────┐
│  Stage C    │  d_evaluation/
│ Evaluation  │  structured JSON vs ground truth → accuracy metrics
└──────┬──────┘
       │  saved to: evaluation_{model}
       ▼
  CSV reports + analysis tables
```

**Models compared**

| Model | Ollama tag | Role |
|-------|-----------|------|
| Qwen-VL | `qwen3.5:35b` | Primary VLM, general-purpose |
| Gemma | `gemma4:31b` | General-purpose comparison |
| MedGemma | `medgemma:27b` | Medical fine-tune comparison |

---

## Key capabilities

- Image-based extraction using LLM/VLM prompts (Ollama backends supported).
- Schema-aligned structuring with Pydantic models.
- Field-level evaluation with accuracy reporting and CSV exports.
- SurrealDB persistence for raw, structured, and evaluation results.

## Repository structure

```
BRIDGEProject/
│
├── main.py                          # Orchestrates all three stages end-to-end
│
├── a_input/
│   └── image_utils.py               # PDF → PNG conversion; image loading and preprocessing
│   ├── image_encoding.py            # image_to_base64()
│
├── b_extraction/
│   ├── extraction_pipeline.py       # Stage A: VLM → markdown, saves to DB
│   └── prompts/
│       ├── base.txt                 # Primary extraction prompt
│       ├── prompt_config.json       # Maps prompt name → ground-truth section key
│       └── prompt_loader.py         # Loads prompt files from this directory
│
├── c_structuring/
│   ├── structuring_pipeline.py      # Stage B: markdown → NARFullRecord JSON, saves to 4 DB tables
│   ├── bool_nullifier.py            # Corrects LLM-defaulted False booleans to None
│   ├── markdown_utils.py            # markdown ↔ dict conversion utilities
│   ├── nar_schema_mapper.py         # Maps raw LLM output to flat schema field names
│   ├── schema_helpers.py            # get_true_option() for schema mapping
│   └── text_cleaning.py             # strip_markdown_fences()
│
├── d_evaluation/
│   ├── evaluation_pipeline.py       # Stage C orchestrator: calls all 5 metric modules
│   ├── field_accuracy.py            # Core accuracy table + shared DB loader
│   ├── classification_metrics.py    # F1, Precision, Recall per field and field type
│   ├── text_metrics.py              # CER + WER for free-text fields (requires jiwer)
│   ├── schema_compliance.py         # Field coverage and type validity checks
│   ├── runtime_analysis.py          # LLM inference and total pipeline timing
│   ├── hallucination_detector.py    # Out-of-allowlist / out-of-range value detection
│   ├── model_comparison.py          # Raw markdown extraction comparison (Qwen vs Gemma)
│   ├── stratified_analysis.py       # Accuracy by field type / facility / scan period
│   └── accuracy_plots.py            # Matplotlib figures for thesis
│
├── database_utils/
│   ├── db_utils.py                  # SurrealDB CRUD helpers (save, fetch, export) and safe_save() wrapper with error logging
│   └── queries.py                   # get_processed_ids() for resume logic
│
├── schemas/
│   ├── neonatal_admission_form/
│   │   ├── nar_full_schema.py       # NARFullRecord: 120-field LLM extraction schema
│   │   ├── nar_schema_included.py   # NARRecord: 98-field GT evaluation schema
│   │   └── field_types.py           # FIELD_TYPES dict + hospital code utilities
│   └── internal_transfer_form/
│       └── itf_schema.py            # ITFRecord schema (future use)
│
├── tests/
│   ├── test_batch_pipeline.py       # Small-batch integration test harness (N records)
│   └── test_results/                # Output directory for test run CSVs
│
├── NAR_metadata.json                # Ground-truth annotations
├── .env                             # Environment variables (not committed to git)
├── requirements.txt                 # Python dependencies
└── docker-compose.yml               # Optional: local SurrealDB instance
```

---

## Requirements and setup

**Python version:** 3.10 or higher

**System dependencies:**
- `poppler` — required by `pdf2image` for PDF conversion
  ```bash
  # Ubuntu/Debian
  sudo apt-get install poppler-utils

  # macOS
  brew install poppler
  ```
- `opencv` — required by `preprocess_images` in `image_utils.py`
  ```bash
  pip install opencv-python-headless
  ```

**Python dependencies:**
```bash
pip install -r requirements.txt

# jiwer is required for text metrics (CER/WER) — install separately if missing
pip install jiwer --break-system-packages
```

**Ollama server:** must be running and reachable at `IP_SERVER` with the relevant models pulled:
```bash
# On the Ollama server machine
ollama pull qwen3.5:35b
ollama pull gemma4:31b
ollama pull medgemma:27b

# Verify models are loaded
ollama ps
```

**SurrealDB:** must be running and accessible on `SURREAL_PORT`:
```bash
# Using docker-compose (recommended)
docker-compose up -d

# Or run directly
surreal start --log info --user root --pass root memory
```

---

## Environment variables

Create a `.env` file at the repo root:

```env
# Ollama server
IP_SERVER=http://192.168.1.10:11434

# SurrealDB credentials
SURREAL_USER=root
SURREAL_PASS=root
SURREAL_PORT=8000

# Optional: alternate Ollama hosts (for multi-server setups)
IP_SERVER01=http://{server_url i.e, htt}
IP_SERVER=http://

# Optional: ground truth path override (defaults to NAR_metadata.json in repo root)
GT_PATH=/path/to/NAR_metadata.json
```

## Quick start

The pipeline is typically run in three stages: extraction → structuring → evaluation.

### 1) Run full pipeline

```bash
python main.py
```

### 2) Run evaluation

```bash
python d_evaluation/evaluation_pipeline.py
```

## Inputs and outputs

**Inputs**
- Source PDFs or images (see `a_input/` for PDF conversion helpers).
- Ground truth JSON (example: `NAR_metadata.json`).
- Prompt templates in `b_extraction/prompts/`.

**Outputs**
- Markdown extraction outputs in `markdown_exports/`.
- CSV accuracy reports such as `field_accuracy.csv`.
- DB tables: `extractions`, `structured`, `mapped`, `evaluation`.

## Tests

Tests are organized into two categories:

**Unit Tests** (fast, no external dependencies):
- `test_database_utils.py` — SurrealDB helper layer tests
- `test_pipeline_helpers.py` — Helper function tests (markdown, schema, encoding)

**Integration Tests** (require Ollama and/or SurrealDB):
- `test_integration_extraction_structuring.py` — Extraction and structuring pipeline tests
- `test_integration_markdown_to_json.py` — Markdown-to-JSON conversion tests

Run unit tests:
```bash
pytest tests/test_*.py
```

Run integration tests (set `RUN_INTEGRATION_TESTS=1` in `.env`):
```bash
pytest tests/test_integration_*.py
```

For more information, see [tests/README.md](tests/README.md).


## Troubleshooting

- **Ollama connection errors**: verify `IP_SERVER` and that the model is pulled and running.
- **SurrealDB errors**: ensure credentials in `.env` match the running instance.
- **PDF conversion issues**: install `poppler` for `pdf2image` and check file permissions.


## License

See `LICENSE` for details.