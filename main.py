import json
import logging
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, date, time

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler("bridge_run.log"),   # saves to file
        logging.StreamHandler(),                  # also prints to terminal
    ],
)

from b_extraction.extraction_pipeline import run_extraction_pipeline
from c_structuring.structuring_pipeline import run_structuring_pipeline
from d_evaluation.run_evaluation_pipeline import run_evaluation

# ------------------------
# Config

IP_SERVER = os.getenv("IP_SERVER")
IMAGE_DIR = "/home/ikutswa/data/BRIDGE/patient_documents/Test_conversion/converted_images"
GT_PATH = "/home/ikutswa/BridgeProject2/BRIDGEProject/NAR_metadata.json"
MODEL_NAME = "qwen3.5:35b"
MODEL_NAME2 = "gemma4:31b"
EXTRACTION_TABLE = "extractions_qwen"
EXTRACTION_TABLE2 = "extractions_gemma"
STRUCTURED_TABLE = "structured_qwen"
STRUCTURED_TABLE2 = "structured_gemma"
MAPPED_TABLE = "mapped"


# ------------------------
# Load and flatten GT

gt = None
if Path(GT_PATH).exists():
    raw = json.loads(Path(GT_PATH).read_text())
    if isinstance(raw, list):
        gt = {item["_id"].split("_page")[0]: item for item in raw}
    else:
        gt = raw

# ------------------------
# Main execution

if __name__ == "__main__":

    # Stage 1 — extract
    print("\n STARTING EXTRACTION...\n")

    processed_ids = run_extraction_pipeline(
        image_dir=IMAGE_DIR,
        model_name=MODEL_NAME,
        table_name=EXTRACTION_TABLE,
        ground_truth=gt,
        resume=True,
    )

    print(f"\n Extraction complete: {len(processed_ids)} records\n")

    # Stage 2 — structure
    print("\n STARTING STRUCTURING PIPELINE...\n")

    structured_ids = run_structuring_pipeline(
        model_name=MODEL_NAME,
        host_url=IP_SERVER,
        table_in=EXTRACTION_TABLE,
        table_out=STRUCTURED_TABLE,
        resume=True,
    )

    print(f"\n Structuring complete: {len(structured_ids)} records\n")

    # Stage 3 — evaluate
    print("\n STARTING EVALUATION PIPELINE...\n")
    run_evaluation(
        gt_path=GT_PATH,
        structured_table=STRUCTURED_TABLE,
        model_label="qwen",
    )

    print("\n Evaluation complete\n")