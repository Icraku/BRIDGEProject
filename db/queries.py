from db.db_utils import fetch_records

def get_processed_ids(table_name: str) -> list[str]:
    """
    Return list of processed record IDs from DB.
    """

    records = fetch_records(table_name)

    ids = set()

    for r in records:
        if "id" not in r:
            continue

        rid = str(r["id"]).split(":")[-1]
        ids.add(rid)

    return list(ids)

