"""
tests/test_batch_pipeline.py
=============================
Small-batch test harness for BRIDGE pipeline.

This script orchestrates a complete extraction → structuring → evaluation
pipeline run on a configurable batch of N records, stopping at each stage,
then commits evaluation outputs to Git.

Useful for:
- Quick validation before production run
- Pipeline integration testing

Usage
-----
    python tests/test_batch_pipeline.py --batch-size 20 --model qwen

Parameters
----------
batch_size (int) :  Number of records to process (default: 20).
model (str) : Model choice: 'qwen' or 'gemma' (default: 'qwen').

Exit behavior
-----------
- Stages are run sequentially and are blocking.
- If a stage fails, the script exits with non-zero status.
- Evaluation outputs are committed to Git or saved automatically.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add repo root to path so imports work from tests/ subdirectory
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

# -------------- CONFIG & SETUP --------------

load_dotenv()

# Model definitions
MODELS = {
    "qwen": "qwen3.5:35b",
    "gemma": "gemma4:31b",
}

# IP_SERVER from environment
IP_SERVER = os.getenv("IP_SERVER") #, "http://localhost:11434")

# Directories
TEST_RESULTS_DIR = REPO_ROOT / "tests" / "test_results"
TEST_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Data
IMAGE_DIR = "/home/ikutswa/data/BRIDGE/patient_documents/Test_conversion/converted_images"
GT_PATH = REPO_ROOT / "NAR_metadata.json"

# DB table naming
def get_table_names(model_key: str) -> dict[str, str]:
    """Return table names for a given model."""
    return {
        "extraction": f"extractions_{model_key}",
        "structured": f"structured_{model_key}",
        "mapped": f"mapped_{model_key}",
        "evaluation": f"evaluation_{model_key}",
    }

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# -------------- STAGE 1: EXTRACTION --------------

def run_extraction_batch(
    batch_size: int,
    model_name: str,
    model_key: str,
) -> list[str]:
    """
    Run extraction pipeline on first N images, then stop.

    Parameters
    ----------
    batch_size (int) :  Number of images to process.
    model_name (str) : Full model name (e.g., "qwen3.5:35b").
    model_key (str) : Short key for table naming (e.g., "qwen").

    Returns
    -------
    list[str]
        List of processed record IDs.
    """
    logger.info("=" * 70)
    logger.info(f"STAGE 1: EXTRACTION (batch_size={batch_size}, model={model_key})")
    logger.info("=" * 70)

    # Import here to avoid circular dependencies
    from a_input.image_utils import load_images
    from b_extraction.extraction_pipeline import run_extraction_pipeline

    # Load images
    images = load_images(IMAGE_DIR)
    logger.info(f"Found {len(images)} images in {IMAGE_DIR}")

    if len(images) < batch_size:
        logger.warning(
            f"Requested batch_size={batch_size} but only {len(images)} images available. "
            f"Processing all {len(images)}."
        )
        batch_size = len(images)

    # Limit to batch size
    images_batch = images[:batch_size]
    logger.info(f"Processing first {len(images_batch)} images.")

    # Load ground truth if available
    gt = None
    if GT_PATH.exists():
        with open(GT_PATH) as f:
            raw_gt = json.load(f)
        if isinstance(raw_gt, list):
            gt = {}
            for item in raw_gt:
                record_id = item.get("_id", "").split("_page")[0]
                gt[record_id] = item
        else:
            gt = raw_gt
        logger.info(f"Loaded ground truth with {len(gt)} records.")
    else:
        logger.warning(f"Ground truth not found at {GT_PATH}. Skipping accuracy computation.")

    # Get table names
    tables = get_table_names(model_key)

    # Run extraction
    try:
        processed_ids = run_extraction_pipeline(
            image_dir=IMAGE_DIR,
            model_name=model_name,
            table_name=tables["extraction"],
            ground_truth=gt,
            resume=True,
            report_path=str(TEST_RESULTS_DIR / f"extraction_report_{model_key}.md"),
        )
        # Limit to batch size (since pipeline processes all images)
        processed_ids = processed_ids[:batch_size]
    except Exception as e:
        logger.error(f"❌ Extraction failed: {e}", exc_info=True)
        raise

    logger.info(f"✅ Extraction complete: {len(processed_ids)} records processed.")
    return processed_ids


# -------------- STAGE 2: STRUCTURING --------------

def run_structuring_batch(
    model_name: str,
    model_key: str,
) -> list[str]:
    """
    Run structuring pipeline on extracted records.

    Parameters
    ----------
    model_name (str) : Full model name for structuring.
    model_key (str) : Short key for table naming.

    Returns
    -------
    list[str]
        List of structured record IDs.
    """
    logger.info("=" * 70)
    logger.info(f"STAGE 2: STRUCTURING (model={model_key})")
    logger.info("=" * 70)

    from c_structuring.structuring_pipeline import run_structuring_pipeline

    # Get table names
    tables = get_table_names(model_key)

    # Run structuring
    try:
        structured_ids = run_structuring_pipeline(
            model_name=model_name,
            host_url=IP_SERVER,
            table_in=tables["extraction"],
            table_out=tables["structured"],
            resume=True,
        )
    except Exception as e:
        logger.error(f"❌ Structuring failed: {e}", exc_info=True)
        raise

    logger.info(f"✅ Structuring complete: {len(structured_ids)} records structured.")
    return structured_ids


# -------------- STAGE 3: EVALUATION --------------

def run_evaluation_batch(
    model_key: str,
) -> dict[str, Any]:
    """
    Run evaluation pipeline on structured records.

    Parameters
    ----------
    model_key (str): Short model key for table naming.

    Returns
    -------
    dict[str, Any]
        Evaluation results (including file paths to CSV outputs).
    """
    logger.info("=" * 70)
    logger.info(f"STAGE 3: EVALUATION (model={model_key})")
    logger.info("=" * 70)

    from d_evaluation.run_evaluation_pipeline import run_evaluation

    # Get table names
    tables = get_table_names(model_key)

    # Check GT exists
    if not GT_PATH.exists():
        logger.error(f"Ground truth required for evaluation but not found at {GT_PATH}.")
        raise FileNotFoundError(f"GT path: {GT_PATH}")

    # Run evaluation
    try:
        eval_df = run_evaluation(
            gt_path=str(GT_PATH),
            structured_table=tables["structured"],
            model_label=model_key,
        )
    except Exception as e:
        logger.error(f"❌ Evaluation failed: {e}", exc_info=True)
        raise

    logger.info(f" Evaluation complete: {len(eval_df)} rows in results.")

    # Save outputs to test_results
    csv_path = TEST_RESULTS_DIR / f"field_accuracy_{model_key}.csv"
    eval_df.to_csv(csv_path, index=False)
    logger.info(f" Saved evaluation CSV: {csv_path}")

    return {
        "dataframe": eval_df,
        "csv_path": str(csv_path),
        "model_key": model_key,
    }


# -------------- STAGE 4: GIT COMMIT --------------

def commit_evaluation_outputs(
    evaluation_results: list[dict[str, Any]],
    batch_size: int,
) -> bool:
    """
    Commit evaluation CSVs to Git.

    Parameters
    ----------
    evaluation_results (list[dict]) :  List of evaluation result dicts (from run_evaluation_batch).
    batch_size (int) :  Batch size for commit message.

    Returns
    -------
    bool
        True if commit succeeded; False otherwise.
    """
    logger.info("=" * 70)
    logger.info("STAGE 4: GIT COMMIT")
    logger.info("=" * 70)

    try:
        # Change to repo root
        os.chdir(REPO_ROOT)

        # Stage evaluation CSVs
        for result in evaluation_results:
            csv_path = Path(result["csv_path"])
            if csv_path.exists():
                subprocess.run(
                    ["git", "add", str(csv_path)],
                    check=True,
                    capture_output=True,
                )
                logger.info(f"Staged: {csv_path}")

        # Check if anything to commit
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
        )
        if not status.stdout.strip():
            logger.info("No changes to commit (staging area clean).")
            return True

        # Commit
        commit_msg = f"Test batch: {batch_size} records, extraction+structuring+evaluation"
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            check=True,
            capture_output=True,
        )
        logger.info(f" Git commit succeeded: '{commit_msg}'")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Git command failed: {e.stderr.decode() if e.stderr else e}")
        return False
    except Exception as e:
        logger.error(f"❌ Commit failed: {e}", exc_info=True)
        return False


# ============================================================================
# MAIN ORCHESTRATOR

def main(batch_size: int, model_key: str) -> int:
    """
    Orchestrate full extraction → structuring → evaluation → commit pipeline.

    Parameters
    ----------
    batch_size (int) : Number of records to process.
    model_key (str) : Model choice ('qwen' or 'gemma').

    Returns
    -------
    int
        Exit code (0 for success, non-zero for failure).
    """
    logger.info(f"\n{'=' * 70}")
    logger.info(f"BRIDGE TEST BATCH PIPELINE")
    logger.info(f"{'=' * 70}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Model: {model_key} ({MODELS[model_key]})")
    logger.info(f"Results dir: {TEST_RESULTS_DIR}")
    logger.info(f"IP_SERVER: {IP_SERVER}")
    logger.info(f"{'=' * 70}\n")

    model_name = MODELS[model_key]
    evaluation_results = []

    try:
        # Stage 1: Extraction
        extracted_ids = run_extraction_batch(batch_size, model_name, model_key)

        # Stage 2: Structuring
        structured_ids = run_structuring_batch(model_name, model_key)

        # Stage 3: Evaluation
        eval_result = run_evaluation_batch(model_key)
        evaluation_results.append(eval_result)

        # Stage 4: Git commit
        commit_ok = commit_evaluation_outputs(evaluation_results, batch_size)

        if not commit_ok:
            logger.warning("Evaluation complete but Git commit failed. Review manually.")
            return 1

        logger.info(f"\n{'=' * 70}")
        logger.info("✅ ALL STAGES COMPLETE")
        logger.info(f"{'=' * 70}\n")
        return 0

    except Exception as e:
        logger.error(f"\n{'=' * 70}", exc_info=False)
        logger.error(f"❌ PIPELINE FAILED: {e}", exc_info=True)
        logger.error(f"{'=' * 70}\n")
        return 1


# ============================================================================
# CLI
# ============================================================================


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run BRIDGE pipeline on a small batch for testing/thesis."
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Number of records to process (default: 20).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="qwen",
        choices=list(MODELS.keys()),
        help="Model choice: qwen or gemma (default: qwen).",
    )

    args = parser.parse_args()

    exit_code = main(batch_size=args.batch_size, model_key=args.model)
    sys.exit(exit_code)
