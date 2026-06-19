"""
tests/README.md
===============
Test structure and organization for the BRIDGE project.

Test Types
----------

1. **Unit Tests** (test_*.py)
   - test_database_utils.py: Tests for SurrealDB helper layer
   - test_pipeline_helpers.py: Tests for helper functions (markdown, schema, encoding)
   - Fast, no external dependencies, safe to run in CI/CD

2. **Integration Tests** (test_integration_*.py)
   - test_integration_extraction_structuring.py: Tests extraction and structuring pipelines
   - test_integration_markdown_to_json.py: Tests markdown-to-JSON conversion
   - Require Ollama instances or other external services
   - Marked with docstring notes about requirements
   - Set RUN_INTEGRATION_TESTS=1 to enable in CI/CD

Running Tests
-------------

Run all unit tests:
    pytest tests/test_*.py

Run all integration tests:
    RUN_INTEGRATION_TESTS=1 pytest tests/test_integration_*.py

Run specific test file:
    pytest tests/test_database_utils.py

Run specific test function:
    pytest tests/test_pipeline_helpers.py::test_markdown_to_dict_handles_json_and_key_values

Batch Test Harness (test_batch_pipeline.py)
-------------------------------------------

Small-batch orchestration: run extraction → structuring → evaluation on N records, then commit results to Git.

**Purpose**: Quick validation before 5k-record production run; thesis preliminary data.

**Usage**:

    # Default: 20 records with Qwen
    python tests/test_batch_pipeline.py

    # Custom batch size and model with event logs
    python tests/test_batch_pipeline.py --batch-size 5 --model qwen 2>&1 | tee test_run.log &

    # Run in background, immune to terminal closure while logging to file
    nohup python main.py > bridge_run.log 2>&1 &
    
    # Monitor it from anywhere
    tail -f bridge_run.log
    
    # Custom batch size and model
    python tests/test_batch_pipeline.py --batch-size 10 --model gemma

    # Qwen, 50 records
    python tests/test_batch_pipeline.py --batch-size 50 --model qwen

**Outputs**:
- CSV reports in `tests/test_results/` (e.g., `field_accuracy_qwen.csv`).
- Git auto-commits evaluation results with message: `"Test batch: N records, extraction+structuring+evaluation"`.

**Resource estimate**:
- ~1–2 hours for 20 records (extraction is the bottleneck).
- ~2–4 GB RAM, ~500 MB–1 GB disk (temporary + CSVs).

**Requirements**:
- `.env` with `IP_SERVER` (Ollama host) and optional SurrealDB credentials.
- Ground truth (`NAR_metadata.json`) required for evaluation stage.
- Git initialized in repo root.

**Behavior**:
- Each stage (extraction, structuring, evaluation, commit) is blocking.
- If a stage fails, the pipeline exits with error code 1.
- On success, evaluation CSVs are automatically staged and committed to Git.

Traceback (most recent call last):
  File "<input>", line 108, in _run_prompt
  File "/home/ikutswa/miniconda3/envs/ocr/lib/python3.13/concurrent/futures/_base.py", line 458, in result
    raise TimeoutError()
TimeoutError
During handling of the above exception, another exception occurred:
Traceback (most recent call last):
  File "<input>", line 110, in _run_prompt
TimeoutError: Model did not respond within 420s — skipping image.
During handling of the above exception, another exception occurred:
Traceback (most recent call last):
  File "<input>", line 3, in <module>
  File "<input>", line 293, in run_extraction_pipeline
  File "<input>", line 177, in _process_image
  File "<input>", line 105, in _run_prompt
  File "/home/ikutswa/miniconda3/envs/ocr/lib/python3.13/concurrent/futures/_base.py", line 647, in __exit__
    self.shutdown(wait=True)
    ~~~~~~~~~~~~~^^^^^^^^^^^
  File "/home/ikutswa/miniconda3/envs/ocr/lib/python3.13/concurrent/futures/thread.py", line 238, in shutdown
    t.join()
    ~~~~~~^^
  File "/home/ikutswa/miniconda3/envs/ocr/lib/python3.13/threading.py", line 1092, in join
    self._handle.join(timeout)
    ~~~~~~~~~~~~~~~~~^^^^^^^^^
KeyboardInterrupt