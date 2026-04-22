import json
import os
from dotenv import load_dotenv

# ------------------------
# LOAD ENV VARIABLES

load_dotenv()

IP_PAUL = os.getenv("IP_PAUL")
IP_TUTI = os.getenv("IP_TUTI")
IP_SERVER = os.getenv("IP_SERVER")

# ------------------------
# IMPORT PIPELINES

from pipelines.extraction_pipeline import run_extraction_pipeline
from pipelines.structuring_pipeline import run_structuring_pipeline
from evaluation.run_evaluation import run_evaluation, load_structured_outputs
from evaluation.gt_processing import load_and_process_meta

# ------------------------
# CONFIG

IMAGE_DIR = "/home/ikutswa/data/BRIDGE/patient_documents/Test_conversion/converted_images"

MODEL_NAME = "qwen3.5:35b"

EXTRACTION_TABLE = "extractions"
STRUCTURED_TABLE = "structured"
MAPPED_TABLE = "mapped"

RESUME = True

# ------------------------
# LOAD GROUND TRUTH*** (TBD)

GT_PATH = "/home/ikutswa/BRIDGEProject/truth.json"

if os.path.exists(GT_PATH):
    with open(GT_PATH) as f:
        GT = json.load(f)
else:
    GT = None

# ------------------------
# MAIN EXECUTION

if __name__ == "__main__":

    print("\n STARTING EXTRACTION...\n")

    processed_ids = run_extraction_pipeline(
        image_dir=IMAGE_DIR,
        model_name="qwen3.5:35b",
        table_name=EXTRACTION_TABLE,
        ground_truth=GT,
        resume=RESUME
    )

    print(f"\n Extraction complete: {len(processed_ids)} records\n")

    print("\n STARTING STRUCTURING PIPELINE...\n")

    structured_ids = run_structuring_pipeline(
        model_name=MODEL_NAME,
        host_url=IP_SERVER,
        table_in=EXTRACTION_TABLE,
        table_out=STRUCTURED_TABLE,
        resume=RESUME
    )

    print(f"\n Structuring complete: {len(structured_ids)} records\n")

    print("\n STARTING EVALUATION PIPELINE...\n")
    run_evaluation(
        gt_path=GT_PATH,
        structured_table=STRUCTURED_TABLE
    )

    print("\n Evaluation complete\n")