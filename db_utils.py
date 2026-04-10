import os

from dotenv import load_dotenv
from surrealdb import Surreal, RecordID

load_dotenv()
DB_USER = os.getenv("SURREAL_USER")
DB_PASSWORD = os.getenv("SURREAL_PASS")
DB_PORT = os.getenv("SURREAL_PORT")

namespace="BRIDGE"
database="Results"


# save to surrealdb

def save_record(data,table_name:str,record_id=None):
    with Surreal(f"ws://localhost:{DB_PORT}") as db:
        db.use(namespace, database)
        db.signin({"username": DB_USER, "password": DB_PASSWORD})
        if record_id is not None:
            result=db.create(RecordID(table_name, record_id), data)
        else:
            result = db.create(table_name,data)

# fetch records from surrealdb

def fetch_records(table_name:str):
    with Surreal(f"ws://localhost:{DB_PORT}") as db:
        db.use(namespace, database)
        db.signin({"username": DB_USER, "password": DB_PASSWORD})
        result = db.select(table_name)
        print(result)
        return result

# fetch a record from surrealdb
def fetch_record(table_name:str,id:str):
    with Surreal(f"ws://localhost:{DB_PORT}") as db:
        db.use(namespace, database)
        db.signin({"username": DB_USER, "password": DB_PASSWORD})
        result = db.select(RecordID(table_name,id))
        return result

# export records from surrealdb

def export_each_record_md(table_name: str, folder="markdown_exports"):
    os.makedirs(folder, exist_ok=True)

    records = fetch_records(table_name)

    for record in records:
        record_id = str(record.get("id")).replace(":", "_")
        extracted = record.get("extracted_text", "")

        file_path = os.path.join(folder, f"{record_id}.md")

        with open(file_path, "w") as f:
            f.write(extracted)

    print(f"Exported {len(records)} records to {folder}/")