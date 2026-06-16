import json
import os
import time
from ollama import Client
from dotenv import load_dotenv
from datetime import datetime
from a_input.image_utils import load_images
from b_extraction.extraction_pipeline import _process_image as process_image, run_extraction_pipeline
from b_extraction.prompts.prompt_loader import load_prompts, load_prompt_config
from c_structuring.structuring_pipeline import run_structuring_pipeline

# ------------------------
# LOAD ENV VARIABLES

load_dotenv()
IP_SERVER = os.getenv("IP_SERVER")
#IP_LOCAL = os.getenv("IP_LOCAL")

# ------------------------
# CONFIG

IMAGE_DIR = "/home/ikutswa/data/BRIDGE/patient_documents/Test_conversion/converted_images"
GT_PATH = "/home/ikutswa/BridgeProject2/BRIDGEProject/NAR_metadata.json"
RESUME = True

MODELS = {
    "qwen": "qwen3.5:35b",
    #"gemma": "gemma4:31b", # Not fast/not working
    #"medgemma": "medgemma27-full:latest",
    #"llama": "llama3:latest",
    #"donut": "donut"
}

# ------------------------
# LOAD GT

if os.path.exists(GT_PATH):

    with open(GT_PATH) as f:
        GT = json.load(f)

else:
    GT = None


# ------------------------
# FIX GT FORMAT

if isinstance(GT, list):

    print("GT is still a list — converting...")

    temp = {}

    for item in GT:

        record_id = item["_id"].split("_page")[0]

        temp[record_id] = item

    GT = temp


# ------------------------
# MAIN

if __name__ == "__main__":

    prompts = load_prompts()
    prompt_config = load_prompt_config()
    images = load_images(IMAGE_DIR)
    clients = {label: Client(host=IP_SERVER) for label in MODELS}

    # Extraction
    for image_path in images:
        for model_label, model_name in MODELS.items():
            print(f"\n{'='*60}")
            print(f"IMAGE: {os.path.basename(image_path)} | MODEL: {model_label}")
            print(f"{'='*60}")

            result = process_image(
                image_path=image_path,
                client=clients[model_label],
                model_name=model_name,
                prompts=prompts,
                prompt_config=prompt_config,
                table_name=f"extractions_{model_label}",
                ground_truth=GT,
                resume=RESUME
            )

            if result:
                print(f"Saved {result['record_id']} to extractions_{model_label}")

    # Structuring
    for model_label, model_name in MODELS.items():
        print(f"\n{'=' * 60}")
        print(f"STRUCTURING: {model_label}")
        print(f"{'=' * 60}")

        structured_ids = run_structuring_pipeline(
            model_name=model_name,
            host_url=IP_SERVER,
            table_in=f"extractions_{model_label}",
            table_out=f"structured_{model_label}",
            resume=RESUME,
            run_id=datetime.now().isoformat()
        )

        print(f"\nStructuring complete for {model_label}: {len(structured_ids)} records\n")