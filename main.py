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
from d_evaluation.evaluation_pipeline import run_evaluation, run_full_metrics_suite

# ------------------------
# Config

IP_SERVER = os.getenv("IP_SERVER")
IMAGE_DIR = "/home/ikutswa/data/BRIDGE/patient_documents/Test_conversion/converted_images"
IMAGE_DIR_TEST = "/home/ikutswa/data/BRIDGE/patient_documents/converted_images/test" #"/home/ikutswa/data/BRIDGE/patient_documents/converted_images/"
GT_PATH = "/home/ikutswa/BridgeProject2/BRIDGEProject/NAR_metadata.json"
MODEL_NAME = "qwen3.5:35b"
MODEL_NAME2 = "gemma4:31b"
EXTRACTION_TABLE = "extractions_qwen" # extractions_qwen
EXTRACTION_TABLE2 = "extractions_gemma" # extractions_gemma
STRUCTURED_TABLE = "structured_qwen" # structured_qwen
STRUCTURED_TABLE2 = "structured_gemma" # structured_gemma
MAPPED_TABLE = "mapped_qwen" # mapped_qwen
MAPPED_TABLE2 = "mapped_gemma" # mapped_gemma

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

    #QWEN-----------------------------------------------------------------------------------
    # Stage 1 — extract
    print("\n STARTING EXTRACTION...\n")

    processed_ids_Q = run_extraction_pipeline(
        image_dir=IMAGE_DIR,
        model_name=MODEL_NAME,
        table_name=EXTRACTION_TABLE,
        ground_truth=gt,
        resume=True,
    )

    print(f"\n Extraction complete: {len(processed_ids_Q)} records\n")

    # Stage 2 — structure
    print("\n STARTING STRUCTURING PIPELINE...\n")

    structured_ids_Q= run_structuring_pipeline(
        model_name=MODEL_NAME,
        host_url=IP_SERVER,
        table_in=EXTRACTION_TABLE,
        table_out=STRUCTURED_TABLE,
        table_required="structured_qwen_required",
        table_supplementary="structured_qwen_supplementary",
        table_mapped="mapped_qwen",
        resume=True,
    )

    print(f"\n Structuring complete: {len(structured_ids_Q)} records\n")

    # Stage 3 — evaluate
    print("\n STARTING EVALUATION PIPELINE...\n")
    run_evaluation(
        gt_path=GT_PATH,
        structured_table=STRUCTURED_TABLE,
        model_label="qwen",
    )

    print("\n Evaluation complete\n")

    # Stage 4 — full evaluation suite (produces ALL metric CSVs)
    run_full_metrics_suite(
        gt_path=GT_PATH,
        model_configs=[
            {
                "model_label": "qwen",
                "eval_table":  "structured_qwen_required",
                "full_table":  "structured_qwen",
            },
        ]
    )

    # GEMMA-----------------------------------------------------------------------------------
    # Stage 1 — extract
    print("\n STARTING EXTRACTION...\n")

    processed_ids_G = run_extraction_pipeline(
        image_dir=IMAGE_DIR,
        model_name=MODEL_NAME2,
        table_name=EXTRACTION_TABLE2,
        ground_truth=gt,
        resume=True,
    )

    print(f"\n Extraction complete: {len(processed_ids_G)} records\n")

    # Stage 2 — structure
    print("\n STARTING STRUCTURING PIPELINE...\n")

    structured_ids_G = run_structuring_pipeline(
        model_name=MODEL_NAME2,
        host_url=IP_SERVER,
        table_in=EXTRACTION_TABLE2,
        table_out=STRUCTURED_TABLE2,
        table_required="structured_gemma_required",
        table_supplementary="structured_gemma_supplementary",
        table_mapped="mapped_gemma",
        resume=True,
    )

    print(f"\n Structuring complete: {len(structured_ids_G)} records\n")

    # Stage 3 — evaluate
    print("\n STARTING EVALUATION PIPELINE...\n")
    run_evaluation(
        gt_path=GT_PATH,
        structured_table=STRUCTURED_TABLE2,
        model_label="gemma",
    )

    print("\n Evaluation complete\n")

    # Stage 4 — full evaluation suite (produces ALL metric CSVs)
    run_full_metrics_suite(
        gt_path=GT_PATH,
        model_configs=[
            {
                "model_label": "gemma",
                "eval_table": "structured_gemma_required",
                "full_table": "structured_gemma",
            },
        ]
    )

    # MEDGEMMA (uncomment when ready)
    # run_structuring_pipeline(
    #     model_name="medgemma:27b",
    #     host_url=IP_SERVER,
    #     table_in="extractions_medgemma",
    #     table_out="structured_medgemma",
    #     table_required="structured_medgemma_required",
    #     table_supplementary="structured_medgemma_supplementary",
    #     table_mapped="mapped_medgemma",
    #     resume=True,
    # )
