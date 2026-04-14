from db.db_utils import save_record
import logging

logger = logging.getLogger(__name__)

def safe_save(record: dict, table: str, record_id: str) -> None:
    """
    Save record to DB with proper error logging.
    Raises exception if it fails.
    """
    try:
        save_record(record, table, record_id)
        logger.info(f"Saved record: {record_id} -> {table}")

    except Exception as e:
        logger.error(f"DB save failed for {record_id}: {e}")
        raise