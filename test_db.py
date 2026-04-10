from db_utils import save_record, fetch_record, fetch_records

table_name = "extractions"
test_id = "test_image_001"

# ------------------------
# Dummy test data

test_data = {
    "image": "test_image_001.png",
    "extraction": {"name": "Baby A", "weight": "3.2kg"},
    "accuracy": 0.95
}

# ------------------------
# 1. SAVE

print("Saving test record...")
save_record(test_data, table_name, record_id=test_id)

# ------------------------
# 2. FETCH SINGLE

print("\nFetching single record...")
record = fetch_record(table_name, test_id)
print(record)

# ------------------------
# 3. FETCH ALL

print("\nFetching all records...")
all_records = fetch_records(table_name)
print(f"Total records: {len(all_records)}")