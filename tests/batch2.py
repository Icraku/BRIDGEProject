from __future__ import annotations

import os
import sys
import json
import logging
from pathlib import Path
from queue import Queue
from threading import Thread, Lock
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

# ---------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

load_dotenv()

IMAGE_DIR = "/home/ikutswa/data/BRIDGE/patient_documents/Test_conversion/converted_images"

TEST_RESULTS_DIR = REPO_ROOT / "tests" / "test_results"
TEST_RESULTS_DIR.mkdir(exist_ok=True, parents=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("prod_parallel")


# ---------------------------------------------------------------------
# CONFIG (IMPORTANT TUNING POINT)
# ---------------------------------------------------------------------

MAX_WORKERS = 3   # 👈 SAFE for Qwen 35B
RETRY_LIMIT = 2


# ---------------------------------------------------------------------
# LOAD PIPELINE COMPONENT
# ---------------------------------------------------------------------

from b_extraction.extraction_pipeline import run_extraction_pipeline
from a_input.image_utils import load_images


# ---------------------------------------------------------------------
# THREAD-SAFE DB WRITER (VERY IMPORTANT)
# ---------------------------------------------------------------------

db_lock = Lock()


def safe_db_write(func, *args, **kwargs):
    """
    Ensures DB writes don't collide across threads.
    """
    with db_lock:
        return func(*args, **kwargs)


# ---------------------------------------------------------------------
# WORKER FUNCTION
# ---------------------------------------------------------------------

def worker(image_path: str, model_name: str, table_name: str):

    attempt = 0

    while attempt <= RETRY_LIMIT:
        try:
            logger.info(f"Processing {image_path} (attempt {attempt+1})")

            result = run_extraction_pipeline(
                image_dir=IMAGE_DIR,
                model_name=model_name,
                table_name=table_name,
                resume=True,
            )

            return {
                "image": image_path,
                "result": result,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Error on {image_path}: {e}")
            attempt += 1

    return {
        "image": image_path,
        "result": None,
        "status": "failed",
    }


# ---------------------------------------------------------------------
# PARALLEL ENGINE (CONTROLLED)
# ---------------------------------------------------------------------

def run_parallel_extraction(images, model_name, table_name):

    results = []

    logger.info(f"Starting parallel extraction with {MAX_WORKERS} workers")
    logger.info(f"Total images: {len(images)}")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        futures = {
            executor.submit(worker, img, model_name, table_name): img
            for img in images
        }

        completed = 0

        for future in as_completed(futures):
            res = future.result()
            results.append(res)

            completed += 1
            if completed % 5 == 0:
                logger.info(f"Progress: {completed}/{len(images)}")

    return results


# ---------------------------------------------------------------------
# PIPELINE STAGE
# ---------------------------------------------------------------------

def run_extraction_batch(batch_size: int, model_name: str, model_key: str):

    images = load_images(IMAGE_DIR)[:batch_size]

    if not images:
        raise ValueError("No images found. Check IMAGE_DIR.")

    logger.info(f"Loaded {len(images)} images")

    results = run_parallel_extraction(
        images=images,
        model_name=model_name,
        table_name=f"extractions_{model_key}",
    )

    success = [r for r in results if r["status"] == "success"]

    logger.info(f"Extraction complete: {len(success)}/{len(images)} successful")

    return success


# ---------------------------------------------------------------------
# MAIN ENTRY
# ---------------------------------------------------------------------

def main(batch_size: int = 10):

    model_name = "qwen3.5:35b"

    try:
        extracted = run_extraction_batch(batch_size, model_name, "qwen")

        logger.info("STAGE COMPLETE: extraction")

        # You can plug your structuring + evaluation here unchanged
        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=10)

    parser.add_argument(
        "--model",
        type=str,
        default="qwen",
        choices=["qwen", "gemma"]
    )

    args = parser.parse_args()

    sys.exit(main(args.batch_size))