"""
database_utils/queries.py
==========================
Higher-level query helpers built on top of the low-level DB utilities.

These functions encapsulate common read patterns used across the pipeline
(e.g. "which records have already been processed?") so the pipeline stages
do not need to repeat the same filtering logic.

Public API
----------
get_processed_ids(table_name) → list[str]
"""

from __future__ import annotations

import logging
from database_utils.db_utils import fetch_records

logger = logging.getLogger(__name__)


def get_processed_ids(table_name: str) -> list[str]:
    """Return all record IDs currently stored in *table_name*.

    Used by the extraction and structuring pipelines to implement resume
    logic: any ID returned here is skipped on the next run.

    Parameters
    ----------
    table_name: SurrealDB table to query.

    Returns
    -------
    list[str]
        Record IDs (the part after the ``table:`` prefix in SurrealDB),
        deduplicated.
    """
    records = fetch_records(table_name)

    ids: set[str] = set()
    for r in records:
        if "id" not in r:
            continue
        ids.add(str(r["id"]).split(":")[-1])

    logger.debug("get_processed_ids: %d IDs from '%s'", len(ids), table_name)
    return list(ids)