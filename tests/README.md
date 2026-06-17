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
