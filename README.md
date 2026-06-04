# BRIDGEProject

End-to-end pipeline for extracting structured clinical data from neonatal admission forms. The system converts PDFs to images, performs visual-language extraction, structures outputs into schema-aligned JSON, and evaluates accuracy against ground truth.

## Key capabilities

- Image-based extraction using LLM/VLM prompts (Ollama backends supported).
- Schema-aligned structuring with Pydantic models.
- Field-level evaluation with accuracy reporting and CSV exports.
- SurrealDB persistence for raw, structured, and evaluation results.

## Repository structure

```
BRIDGEProject/
├── a_input/                 # PDF → image utilities and preprocessing
├── b_extraction/            # VLM extraction pipeline and prompts
├── c_structuring/           # Markdown parsing and schema mapping
├── d_evaluation/            # Accuracy and evaluation reports
├── database_utils/          # SurrealDB access helpers
├── schemas/                 # Pydantic schemas
├── scripts/                 # Ad-hoc utilities (markdown processing, comparisons)
├── tests/                   # Tests and experiments
├── utils/                   # Shared helpers
├── main.py                                          # Orchestrates extraction → structuring → evaluation
├── run_complete_pipeline.py                         # Batch extraction pipeline runner
├── run_complete_pipeline_with_c_stucturing_logic.py # Batch structuring pipeline runner
└── docker-compose.yml                               # Optional local services
```

## Requirements

- Python 3.10+ (project uses typing and modern stdlib features).
- Ollama server for model inference (e.g., `qwen3.5` / `gemma` families).
- SurrealDB for persistence (optional but recommended).

> If you plan to run the full pipeline, install the libraries referenced in the `requirements.txt` by running `pip install -r requirements.txt`

> Note: Some of the modules require GPU capacity of RAM 8GB and above.

## Environment variables

Create a `.env` file at the repo root (or export variables in your shell):

- `IP_SERVER` — Ollama host URL (e.g., `http://localhost:01234`)
- `IP_PAUL/IP_SERVER01`, `IP_TUTI/IP_SERVER02` — optional alternate Ollama hosts
- `SURREAL_USER`, `SURREAL_PASS`, `SURREAL_PORT` — SurrealDB credentials

## Quick start

The pipeline is typically run in three stages: extraction → structuring → evaluation.

### 1) Run full pipeline

```bash
 python main.py
```

### 2) Run extraction only

```bash
 python run_complete_pipeline.py
```

### 3) Run structuring with existing logic

```bash
 python run_complete_pipeline_with_c_stucturing_logic.py
```

### 4) Run evaluation

```bash
 python d_evaluation/run_evaluation.py
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

Current tests are located in `tests/`. To run them:

```bash
 pytest
```

> Some tests require a running SurrealDB instance and may be integration-style.


## Troubleshooting

- **Ollama connection errors**: verify `IP_SERVER` and that the model is pulled and running.
- **SurrealDB errors**: ensure credentials in `.env` match the running instance.
- **PDF conversion issues**: install `poppler` for `pdf2image` and check file permissions.


## License

See `LICENSE` for details.