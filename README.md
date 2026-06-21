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

## Running the pipeline

### Full pipeline — all stages, one model (recommended for weekend runs)

```bash
cd ~/BridgeProject2/BRIDGEProject

# Run in background and get logs
nohup python main.py > bridge_run.log 2>&1 &

# Save PID
echo $! > bridge.pid

# Monitor progress
tail -f bridge_run.log

# Check if still running
kill -0 $(cat bridge.pid) && echo "RUNNING" || echo "FINISHED or CRASHED"
```

### Small-batch test run

```bash
# Run 5 records with Qwen, log to file
python tests/test_batch_pipeline.py --batch-size 5 --model qwen 2>&1 | tee test_run.log

# Run 5 records with Gemma
python tests/test_batch_pipeline.py --batch-size 5 --model gemma 2>&1 | tee test_run_gemma.log
```

### Run individual stages separately

**Stage A — Extraction only (Qwen):**
```bash
python -c "
from b_extraction.extraction_pipeline import run_extraction_pipeline
import os
run_extraction_pipeline(
    image_dir='/path/to/images',
    model_name='qwen3.5:35b',
    table_name='extractions_qwen',
    resume=True,
)
"
```

**Stage A — Extraction only (Gemma):**
```bash
python -c "
from b_extraction.extraction_pipeline import run_extraction_pipeline
run_extraction_pipeline(
    image_dir='/path/to/images',
    model_name='gemma4:31b',
    table_name='extractions_gemma',
    resume=True,
)
"
```

**Stage A — Extraction only (MedGemma):**
```bash
python -c "
from b_extraction.extraction_pipeline import run_extraction_pipeline
run_extraction_pipeline(
    image_dir='/path/to/images',
    model_name='medgemma:27b',
    table_name='extractions_medgemma',
    resume=True,
)
"
```

**Stage B — Structuring only (Qwen):**
```bash
python -c "
from c_structuring.structuring_pipeline import run_structuring_pipeline
import os
run_structuring_pipeline(
    model_name='qwen3.5:35b',
    host_url=os.getenv('IP_SERVER'),
    table_in='extractions_qwen',
    table_out='structured_qwen',
    resume=True,
)
"
```

**Stage B — Structuring only (Gemma):**
```bash
python -c "
from c_structuring.structuring_pipeline import run_structuring_pipeline
import os
run_structuring_pipeline(
    model_name='gemma4:31b',
    host_url=os.getenv('IP_SERVER'),
    table_in='extractions_gemma',
    table_out='structured_gemma',
    resume=True,
)
"
```

**Stage B — Structuring only (MedGemma):**
```bash
python -c "
from c_structuring.structuring_pipeline import run_structuring_pipeline
import os
run_structuring_pipeline(
    model_name='medgemma:27b',
    host_url=os.getenv('IP_SERVER'),
    table_in='extractions_medgemma',
    table_out='structured_medgemma',
    resume=True,
)
"
```

**Stage C — Full evaluation suite (all models):**
```bash
python -m d_evaluation.evaluation_pipeline
```

**Stage C — Evaluation for one model only:**
```bash
python -c "
from d_evaluation.evaluation_pipeline import run_evaluation
run_evaluation(
    gt_path='NAR_metadata.json',
    structured_table='structured_qwen_required',   # for qwen
    model_label='qwen',
)
"
```

### Stratified analysis (after evaluation is complete)

```bash
# Qwen
python -m d_evaluation.stratified_analysis --model qwen --out results/

# Gemma
python -m d_evaluation.stratified_analysis --model gemma --out results/

# MedGemma (when ready)
python -m d_evaluation.stratified_analysis --model medgemma --out results/
```

### Raw extraction comparison (Qwen vs Gemma, no GT needed)

```bash
python -c "from d_evaluation.model_comparison import run_comparison; run_comparison()"
```

### Export raw markdown from DB (for manual inspection)

```bash
python -c "
from database_utils.db_utils import export_each_record_md
export_each_record_md('extractions_qwen', folder='markdown_exports/qwen')
export_each_record_md('extractions_gemma', folder='markdown_exports/gemma')
"
```

---

## Database tables reference

All tables live in the `BRIDGE` namespace, `Results` database in SurrealDB.

| Table                               | Written by          | Content |
|-------------------------------------|---------------------|---------|
| `extractions_qwen`                  | Stage A (Qwen)      | Raw markdown per image page + runtime |
| `extractions_gemma`                 | Stage A (Gemma)     | Raw markdown per image page + runtime |
| `extractions_medgemma`              | Stage A (MedGemma)  | Raw markdown per image page + runtime |
| `structured_qwen`                   | Stage B (Qwen)      | All 120 NARFullRecord fields + inclusion map + timings |
| `structured_qwen_required`          | Stage B (Qwen)      | 98 NARRecord fields only — used for GT evaluation |
| `structured_qwen_supplementary`     | Stage B (Qwen)      | 22 supplementary fields not in NARRecord |
| `structured_gemma`                  | Stage B (Gemma)     | All fields + timings (single table for Gemma) |
| `structured_gemma_required`         | Stage B (Gemma)      | 98 NARRecord fields only — used for GT evaluation |
| `structured_gemma_supplementary`    | Stage B (Gemma)      | 22 supplementary fields not in NARRecord |
| `structured_medgemma`               | Stage B (MedGemma)  | All fields + timings |
| `structured_medgemma_required`      | Stage B (Medgemma)  | 22 supplementary fields not in NARRecord |
| `structured_medgemma_supplementary` | Stage B (Medgemma)      | 22 supplementary fields not in NARRecord |
| `mapped`                            | Stage B             | Schema-mapped output (legacy downstream format) |
| `evaluation_qwen`                   | Stage C             | Per-record accuracy, by field type and NAR inclusion |
| `evaluation_gemma`                  | Stage C             | Per-record accuracy |
| `evaluation_medgemma`               | Stage C             | Per-record accuracy |
| `comparison`                        | model_comparison.py | Field-level Qwen vs Gemma agreement on raw markdown |

**Note on Qwen table split:** All models use two structured tables (`structured_{model}` for the full 120-field output and `structured_{model}required` for the 98-field GT evaluation subset) because it was the first model run and the pipeline was designed with this split explicitly.

---

## Output files reference

All CSV files are written to the working directory unless `--out` is specified.

### Stage C — Evaluation pipeline

| File | Produced by | Description |
|------|------------|-------------|
| `field_accuracy_{model}.csv` | `run_evaluation` | One row per (record, field): correct?, has_gt, scorable, normalised values |
| `all_fields_{model}.csv` | `run_evaluation` | All 120 fields grouped by inclusion status and GT availability |
| `metrics_{model}.csv` | `classification_metrics` | TP/FP/FN/TN + F1/Precision/Recall per field |
| `summary_metrics_{model}.csv` | `classification_metrics` | Macro F1/P/R by field_type and NAR inclusion |
| `cer_wer_{model}.csv` | `text_metrics` | Per-(record, field) CER and WER for free-text fields |
| `text_field_summary_{model}.csv` | `text_metrics` | Per-field mean/median CER and WER |
| `compliance_report_{model}.csv` | `schema_compliance` | Per-record field coverage and type compliance |
| `compliance_summary_{model}.csv` | `schema_compliance` | Per-field presence rate across all records |
| `runtime_summary_{model}.csv` | `runtime_analysis` | Per-record LLM and total pipeline runtimes |
| `runtime_by_model.csv` | `runtime_analysis` | Cross-model timing comparison |
| `hallucinations_{model}.csv` | `hallucination_detector` | Every flagged (record, field, value, reason) |
| `hallucination_summary_{model}.csv` | `hallucination_detector` | Per-field hallucination rate |
| `cross_model_summary.csv` | `run_full_metrics_suite` | One row per model: all headline metrics combined |

### Stratified analysis

| File | Description |
|------|-------------|
| `table1_by_field_type_{model}.csv` | Mean accuracy per field type (bool, int, str, float, date, time) |
| `table2_by_facility_{model}.csv` | Mean accuracy per hospital facility |
| `table3_by_scan_period_{model}.csv` | Mean accuracy per admission month and quarter |
| `table4_facility_x_field_type_{model}.csv` | Cross-tabulation: facility × field type |
| `table_combined_{model}.csv` | All three stratified tables stacked for thesis appendix |

### Extraction comparison

| File | Description |
|------|-------------|
| `extraction_comparison.csv` | Field-level Qwen vs Gemma raw value agreement |

---

### Quick CSV viewer
```bash
python utils/view_csv.py cross_model_summary.csv
python utils/view_csv.py metrics_qwen.csv --filter "nar_inclusion=included" --sort f1
python utils/view_csv.py hallucinations_qwen.csv --cols field,field_type,raw_value,reason
```

## Tests

Tests are in `tests/`. The integration test harness runs a complete mini-pipeline.

**Small-batch integration test (requires Ollama + SurrealDB):**
```bash
# 5 records, Qwen
python tests/test_batch_pipeline.py --batch-size 5 --model qwen

# 5 records, Gemma
python tests/test_batch_pipeline.py --batch-size 5 --model gemma

# 20 records, Qwen, background run
python tests/test_batch_pipeline.py --batch-size 20 --model qwen 2>&1 | tee test_run.log &
```

**Unit tests (no external dependencies):**
```bash
pytest tests/ -v
```

---

## Troubleshooting

**Pipeline hangs on one image**
The VLM call has a 7-minute timeout per image. If the pipeline stops responding beyond that, the Ollama client timeout may not be firing. Verify:
```bash
# Check if the model is running on GPU (should show GPU-Util > 0%)
ssh user@IP_SERVER "nvidia-smi"

# Check Ollama is serving the model
ssh user@IP_SERVER "ollama ps"

# Check Ollama logs
ssh user@IP_SERVER "journalctl -u ollama -f"
```

**`ModuleNotFoundError` when running a script directly**
Always run scripts as modules from the project root:
```bash
cd ~/BridgeProject2/BRIDGEProject
python -m d_evaluation.stratified_analysis --model qwen
# NOT: python d_evaluation/stratified_analysis.py
```

**`summary_metrics_{model}.csv` not found**
This file is only produced by `run_full_metrics_suite`, not by `run_evaluation` alone. Ensure `main.py` calls `run_full_metrics_suite` in Stage C, not just `run_evaluation`.

**Ollama connection errors**
```bash
# Verify IP_SERVER is reachable
curl http://$IP_SERVER/api/tags

# Verify the specific model is available
curl http://$IP_SERVER/api/tags | python -m json.tool | grep name
```

**SurrealDB errors**
```bash
# Test connection
surreal sql --conn ws://localhost:8000 --user $SURREAL_USER --pass $SURREAL_PASS \
  --ns BRIDGE --db Results "SELECT * FROM extractions_qwen LIMIT 1"
```

**PDF conversion fails**
```bash
# Verify poppler is installed
which pdftoppm
# If missing: sudo apt-get install poppler-utils
```

**`jiwer` not installed (text metrics skipped)**
```bash
pip install jiwer --break-system-packages
```

---

## License

See `LICENSE` for details.