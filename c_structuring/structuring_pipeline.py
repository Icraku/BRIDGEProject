"""
c_structuring/structuring_pipeline.py
=======================================
Second stage of the BRIDGE pipeline: convert extracted markdown into structured
JSON records validated against the NAR schema.

Pipeline
--------
1. Read all raw extraction records from SurrealDB (``table_in``).
2. For each base record ID, combine page-1 and page-2 markdown into a
   single string.
3. Send the combined markdown to a LangChain-wrapped Ollama LLM with
   ``NARFullRecord`` as the structured-output schema.
4. Post-process boolean fields via ``nullify_unticked_bools``.
5. Split the 120-field output into three subsets and persist to DB:
   - ``table_out``              — all 120 fields + inclusion map + timings
   - ``"structured_required"``  — 98 NARRecord fields (used for GT evaluation)
   - ``"structured_supplementary"`` — 22 extra fields
   - ``"mapped"``               — schema-mapped subset (legacy downstream use)

Public API
----------
run_structuring_pipeline(model_name, host_url, ...)
    Orchestrate structuring for all records in *table_in*.
"""

from __future__ import annotations

import logging
import time
from datetime import date, datetime
from datetime import time as dt_time

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from tqdm import tqdm

from c_structuring.bool_nullifier import BOOL_FIELD_LABELS, nullify_unticked_bools
from c_structuring.nar_schema_mapper import map_to_schema
from database_utils.db_save import safe_save
from database_utils.db_utils import fetch_record, fetch_records
from database_utils.queries import get_processed_ids
from schemas.neonatal_admission_form.nar_full_schema import (
    NAR_REQUIRED_FIELDS,
    NARFullRecord,
    inclusion_status,
)
# Required downstream schema (structured subset)
from schemas.neonatal_admission_form.nar_schema_included import NARRecord
from schemas.internal_transfer_form.itf_schema import ITFRecord
from utils.text_cleaning import strip_markdown_fences

logger = logging.getLogger(__name__)

# Pre-compute the set of bool field names once at import time so
# ``clean_for_db`` does not rebuild it on every call.
_BOOL_FIELDS: frozenset[str] = frozenset(BOOL_FIELD_LABELS.keys())

# ---------------------------------------------------------------------------
# DB serialisation helper

def clean_for_db(value: object, _bool_fields: frozenset[str] = _BOOL_FIELDS) -> object:
    """Recursively prepare a value for SurrealDB storage.

    SurrealDB coerces Python ``None`` booleans to ``false``.  This function
    stores ``None`` bool fields as the string ``"null"`` so the evaluation
    layer can differentiate between "blank / unknown" from an explicit ``False``.

    Date and time objects are serialised to strings because SurrealDB's
    Python driver does not accept them natively.

    Parameters
    ----------
    value: Any Python value produced by ``NARFullRecord.model_dump()``.

    Returns
    -------
    object
        A DB-safe representation of *value*.
    """
    if value is None:
        return None
    if isinstance(value, dict):
        result: dict = {}
        for k, v in value.items():
            cleaned = clean_for_db(v)
            # Store None bool fields as "null" to prevent SurrealDB coercion
            result[k] = "null" if (cleaned is None and k in _bool_fields) else cleaned
        return result
    if isinstance(value, list):
        return [clean_for_db(item) for item in value]
    if isinstance(value, datetime):
        return value.strftime("%d-%m-%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d-%m-%Y")
    if isinstance(value, dt_time):
        return value.strftime("%H:%M")
    return value


# ---------------------------------------------------------------------------
# Internal helpers

def _fetch_markdown_for_record(record_id: str, all_records: list) -> str | None:
    """Combine page-1 and page-2 markdown for *record_id* into one string.

    Matches records whose DB ``id`` field contains *record_id* (handles the
    ``table:record_id_page1`` SurrealDB ID format).

    Parameters
    ----------
    record_id:
        Base record ID without page suffix (e.g. ``"NAR_40000001"``).
    all_records:
        All extraction records fetched from SurrealDB.

    Returns
    -------
    str | None
        Combined markdown string, or ``None`` if no matching records exist.
    """
    matching = [
        r for r in all_records
        if record_id in str(r.get("id", "")).split(":")[-1]
    ]
    if not matching:
        return None

    pages = [
        strip_markdown_fences(r["extracted_text"])
        for r in matching
        if "extracted_text" in r
    ]
    return "\n\n".join(pages) if pages else None


def _structure_record(
    record_id: str,
    markdown_text: str,
    model_name: str,
    base_url: str,
) -> dict:
    """Send markdown to the LLM and return a structured extraction result.

    Uses LangChain's ``with_structured_output`` to enforce ``NARFullRecord``
    as the response schema, then splits the 120-field output into required
    and supplementary subsets.

    Parameters
    ----------
    record_id: Used for logging only.
    markdown_text: Combined page-1 + page-2 markdown for this record.
    model_name: Ollama model tag (e.g. ``"qwen2-vl:7b"``).
    base_url: Ollama server base URL.

    Returns
    -------
    dict with keys:
        ``full_content``, ``required_content``, ``supplementary_content``,
        ``inclusion_map``, ``runtime_seconds``.
    """
    system_prompt = (
        "Extract information from the provided Markdown. "
        "The response MUST be a JSON. "
        f"The format should be {NARFullRecord.model_fields}"
    ).replace("{", "{{").replace("}", "}}")

    # f"If the field has not been filled, return N/A, Example born_where: N/A "
    # f"If you cannot read a field correctly, return the question mark symbol in its place, Example: Date of Admission: 12/??/2024 "

    prompt_template = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("user", "{__text__}")]
    )
    prompt = prompt_template.invoke({"__text__": markdown_text})

    llm = ChatOllama(model=model_name, base_url=base_url)
    structured_llm = llm.with_structured_output(NARFullRecord)

    start = time.perf_counter()
    result: NARFullRecord = structured_llm.invoke(prompt)
    runtime = time.perf_counter() - start

    full_dict: dict = result.model_dump()
    required_dict = {k: v for k, v in full_dict.items() if k in NAR_REQUIRED_FIELDS}
    supplementary_dict = {k: v for k, v in full_dict.items() if k not in NAR_REQUIRED_FIELDS}
    inclusion_map = {field: inclusion_status(field) for field in full_dict}

    return {
        "full_content": full_dict,
        "required_content": required_dict,
        "supplementary_content": supplementary_dict,
        "inclusion_map": inclusion_map,
        "runtime_seconds": runtime,
    }


# ---------------------------------------------------------------------------
# Public API

def run_structuring_pipeline(
    model_name: str,
    host_url: str,
    table_in: str = "extractions",
    table_out: str = "structured_Q",
    resume: bool = True,
) -> list[str]:
    """Convert extracted markdown records to structured JSON and persist to DB.

    Reads all records from *table_in*, structures each one with the LLM,
    and writes results to four SurrealDB tables.

    Parameters
    ----------
    model_name: Ollama model tag for the structuring LLM.
    host_url: Ollama server URL (e.g. ``"http://192.168.1.10:11434"``).
    table_in: SurrealDB table containing raw extraction records.
    table_out: SurrealDB table for full 120-field structured output.
    resume: If ``True``, skip records that already exist in *table_out*.

    Returns
    -------
    list[str]
        Record IDs that were successfully structured in this run.
    """
    all_records = fetch_records(table_in)

    # Derive unique base IDs (strip ``_page1`` / ``_page2`` suffixes)
    raw_ids = get_processed_ids(table_in)
    base_ids = list({rid.split("_page")[0] for rid in raw_ids})

    logger.info(
        "Structuring: model=%s, records=%d, table_in=%s, table_out=%s",
        model_name, len(base_ids), table_in, table_out,
    )

    structured_ids: list[str] = []

    for record_id in tqdm(base_ids, desc="Structuring"):
        record_start = time.perf_counter()
        logger.info("Structuring %s", record_id)

        # --- Resume check ---------------------------------------------------
        if resume:
            existing = fetch_record(table_out, record_id)
            if existing:
                logger.info("  Skipping %s — already in DB.", record_id)
                structured_ids.append(record_id)
                continue

        # --- Fetch markdown -------------------------------------------------
        markdown_text = _fetch_markdown_for_record(record_id, all_records)
        if not markdown_text:
            logger.warning("  No markdown found for %s — skipping.", record_id)
            continue

        # --- Structure ------------------------------------------------------
        try:
            s = _structure_record(record_id, markdown_text, model_name, host_url)
        except Exception:
            logger.exception("  Structuring failed for %s.", record_id)
            continue

        full_dict          = s["full_content"]
        required_dict      = s["required_content"]
        supplementary_dict = s["supplementary_content"]
        inclusion_map      = s["inclusion_map"]
        llm_runtime        = s["runtime_seconds"]

        # Post-process: correct blank booleans that LLM defaulted to False
        required_dict = nullify_unticked_bools(required_dict, markdown_text)

        # --- Schema mapping (legacy downstream use) -------------------------
        try:
            mapped_output = map_to_schema(required_dict)
        except Exception:
            logger.exception("  Schema mapping failed for %s.", record_id)
            continue

        total_runtime = time.perf_counter() - record_start

        # --- Prepare for DB -------------------------------------------------
        clean_full          = clean_for_db(full_dict)
        clean_required      = clean_for_db(required_dict)
        clean_supplementary = clean_for_db(supplementary_dict)
        clean_mapped        = clean_for_db(mapped_output)

        nulled_fields = [k for k, v in clean_required.items() if v is None]
        if nulled_fields:
            logger.debug("  Nulled fields: %s", nulled_fields)

        # --- Persist to DB --------------------------------------------------
        try:
            safe_save(
                {
                    "structured_text": clean_full,
                    "inclusion_map": inclusion_map,
                    "llm_runtime_seconds": llm_runtime,
                    "total_record_runtime_seconds": total_runtime,
                },
                table_out,
                record_id,
            )
            safe_save(
                {"structured_text": clean_required},
                "structured_required",
                record_id,
            )
            safe_save(
                {"structured_text": clean_supplementary},
                "structured_supplementary",
                record_id,
            )
            safe_save(
                {"mapped_fields": clean_mapped},
                "mapped",
                record_id,
            )
        except Exception:
            logger.exception("  DB save failed for %s.", record_id)
            continue

        structured_ids.append(record_id)
        logger.info("  Saved %s.", record_id)

    logger.info("Structuring complete — %d record(s) processed.", len(structured_ids))
    return structured_ids