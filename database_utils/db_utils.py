"""
database_utils/db_utils.py
===========================
Low-level SurrealDB connection and CRUD helpers for the BRIDGE pipeline.

All three pipeline stages (extraction, structuring, evaluation) write to and
read from SurrealDB via these functions.  Connection credentials are read from
environment variables set in ``.env``:

    SURREAL_USER   — database username
    SURREAL_PASS   — database password
    SURREAL_PORT   — WebSocket port (default: 8000)

The namespace and database are fixed to ``BRIDGE`` / ``Results`` for this
project.

Public API
----------
save_record(data, table_name, record_id)   → dict | None
safe_save(record, table, record_id)        → None
fetch_records(table_name)                  → list[dict]
fetch_record(table_name, record_id)        → dict | None
export_each_record_md(table_name, folder)  → None
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from surrealdb import RecordID, Surreal

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Connection configuration

_DB_USER     = os.getenv("SURREAL_USER")
_DB_PASSWORD = os.getenv("SURREAL_PASS")
_DB_PORT     = os.getenv("SURREAL_PORT", "8000")
_NAMESPACE   = "BRIDGE"
_DATABASE    = "Results"


def _db_url() -> str:
    """Return the SurrealDB WebSocket URL from environment configuration."""
    return f"ws://localhost:{_DB_PORT}"


def _connect(db: Surreal) -> None:
    """Authenticate and select the BRIDGE namespace and database."""
    db.use(_NAMESPACE, _DATABASE)
    db.signin({"username": _DB_USER, "password": _DB_PASSWORD})


# ---------------------------------------------------------------------------
# CRUD operations

def save_record(
    data: dict,
    table_name: str,
    record_id: str | None = None,
) -> dict | None:
    """Create a record in SurrealDB and return the created document.

    Parameters
    ----------
    data: Field-value dict to store.
    table_name: SurrealDB table to write to.
    record_id: Explicit record ID.  If ``None``, SurrealDB generates one.

    Returns
    -------
    dict | None
        The created record as returned by SurrealDB, or ``None`` on failure.
    """
    with Surreal(_db_url()) as db:
        _connect(db)
        if record_id is not None:
            result = db.create(RecordID(table_name, record_id), data)
        else:
            result = db.create(table_name, data)
    return result

def safe_save(record: dict, table: str, record_id: str) -> None:
    """Save *record* to *table* in SurrealDB, raising on failure.

    Parameters
    ----------
    record: Field-value dict to persist.
    table: SurrealDB table name.
    record_id: Explicit record identifier.

    Raises
    ------
    Exception
        Re-raises whatever SurrealDB raises so the calling pipeline can
        decide whether to skip the record or abort the run.
    """
    try:
        save_record(record, table, record_id)
        logger.info("Saved %s → %s", record_id, table)
    except Exception:
        logger.exception("DB save failed for %s in table '%s'.", record_id, table)
        raise

def fetch_records(table_name: str) -> list[dict]:
    """Fetch all records from *table_name*.

    Parameters
    ----------
    table_name: SurrealDB table to read from.

    Returns
    -------
    list[dict]
        All records in the table, or an empty list if the table is empty or
        does not exist.
    """
    with Surreal(_db_url()) as db:
        _connect(db)
        result = db.select(table_name)
    logger.debug("fetch_records: %d records from '%s'", len(result or []), table_name)
    return result or []


def fetch_record(table_name: str, record_id: str) -> dict | None:
    """Fetch a single record by ID.

    Parameters
    ----------
    table_name:
        SurrealDB table to read from.
    record_id:
        Record identifier (without table prefix).

    Returns
    -------
    dict | None
        The matching record, or ``None`` if not found.
    """
    with Surreal(_db_url()) as db:
        _connect(db)
        result = db.select(RecordID(table_name, record_id))
    return result


def export_each_record_md(
    table_name: str,
    folder: str = "markdown_exports",
) -> None:
    """Export the ``extracted_text`` field of every record to Markdown files.

    One ``.md`` file is created per record, named after the record ID.
    Useful for manual inspection of VLM extraction output.

    Parameters
    ----------
    table_name:
        SurrealDB table to export from.
    folder:
        Destination directory.  Created automatically if absent.
    """
    output_dir = Path(folder)
    output_dir.mkdir(parents=True, exist_ok=True)

    records = fetch_records(table_name)
    for record in records:
        record_id  = str(record.get("id", "unknown")).replace(":", "_")
        extracted  = record.get("extracted_text", "")
        dest       = output_dir / f"{record_id}.md"
        dest.write_text(extracted, encoding="utf-8")

    logger.info("Exported %d records to %s/", len(records), folder)