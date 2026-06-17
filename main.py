import json
import os
from dotenv import load_dotenv
from datetime import datetime, date, time
import openpyxl

# ------------------------
# LOAD ENV VARIABLES

load_dotenv()

IP_PAUL = os.getenv("IP_PAUL")
IP_TUTI = os.getenv("IP_TUTI")
IP_SERVER = os.getenv("IP_SERVER")

# ------------------------
# IMPORT PIPELINES

from b_extraction.extraction_pipeline import run_extraction_pipeline
from c_structuring.structuring_pipeline import run_structuring_pipeline
#from d_evaluation.run_evaluation import run_evaluation, load_and_process_meta
from d_evaluation.run_evaluation_pipeline import run_evaluation

# ------------------------
# CONFIG

IMAGE_DIR = "/home/ikutswa/data/BRIDGE/patient_documents/Test_conversion/converted_images"

MODEL_NAME = "qwen3.5:35b"
MODEL_NAME2 = "gemma4:31b"

EXTRACTION_TABLE = "extractions_qwen"
EXTRACTION_TABLE2 = "extractions_gemma"
STRUCTURED_TABLE = "structured_qwen"
STRUCTURED_TABLE2 = "structured_gemma"
MAPPED_TABLE = "mapped"

RESUME = True

# ------------------------
# LOAD GROUND TRUTH*** (TBD)

GT_PATH = "/home/ikutswa/BridgeProject2/BRIDGEProject/NAR_metadata.json"

if os.path.exists(GT_PATH):
    with open(GT_PATH) as f:
        GT = json.load(f)
else:
    GT = None

if isinstance(GT, list):
    print("GT is still a list — converting...")

    temp = {}
    for item in GT:
        record_id = item["_id"].split("_page")[0]
        temp[record_id] = item

    GT = temp

# ------------------------
# MAIN EXECUTION

if __name__ == "__main__":

    print("\n STARTING EXTRACTION...\n")

    processed_ids = run_extraction_pipeline(
        image_dir=IMAGE_DIR,
        model_name=MODEL_NAME,
        table_name=EXTRACTION_TABLE,
        ground_truth=GT,
        resume=RESUME,
        run_id=datetime.now().isoformat()
    )

    print(f"\n Extraction complete: {len(processed_ids)} records\n")

    print("\n STARTING STRUCTURING PIPELINE...\n")

    structured_ids = run_structuring_pipeline(
        model_name=MODEL_NAME,
        host_url=IP_SERVER,
        table_in=EXTRACTION_TABLE,
        table_out=STRUCTURED_TABLE,
        resume=RESUME,
        run_id=datetime.now().isoformat()
    )

    print(f"\n Structuring complete: {len(structured_ids)} records\n")

    print("\n STARTING EVALUATION PIPELINE...\n")
    run_evaluation(
        gt_path=GT_PATH,
        structured_table=STRUCTURED_TABLE
    )

    print("\n Evaluation complete\n")