import os
from tqdm import tqdm
from ollama import Client

IP_PAUL = os.getenv("IP_PAUL")
IP_TUTI = os.getenv("IP_TUTI")
IP_SERVER = os.getenv("IP_SERVER")

from input.image_loader import load_images
from utils.encoding import image_to_base64
from parsing.markdown_parser import markdown_to_dict
from evaluation.accuracy import compute_accuracy
from processing.merge_pred import merge_predictions
from formatters.markdown_formatter import dict_to_markdown
from db.db_save import safe_save
from db.db_utils import fetch_record
from prompt_loader import load_prompts, load_prompt_config


# ------------------------
# CORE: LLM CALL

def run_prompt(client: Client, model_name: str, prompt_text: str, image_base64: str) -> str:
    """
    Run a single prompt against the model.
    """
    response = client.chat(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": prompt_text,
                "images": [image_base64]
            }
        ],
        options={"seed": 42}
    )

    return response["message"]["content"]


# ------------------------
# CORE: PROCESS ONE IMAGE

def process_image(
    image_path: str,
    client: Client,
    model_name: str,
    prompts: dict,
    prompt_config: dict,
    table_name: str,
    ground_truth: dict | None = None,
    resume: bool = True
):
    """
    Process a single image through all prompts.
    """

    import os

    image_name = os.path.basename(image_path)
    record_id = os.path.splitext(image_name)[0]

    print(f"\n=== Processing {image_name} ===")

    # ------------------------
    # RESUME CHECK
    if resume:
        try:
            existing = fetch_record(table_name, record_id + "_base")
            if existing:
                print("Skipping (already processed)")
                return None
        except Exception:
            pass

    image_base64 = image_to_base64(image_path)

    parsed_predictions = []
    accuracies = []
    markdown_outputs = []

    # ------------------------
    # RUN PROMPTS
    for prompt_name, prompt_text in prompts.items():
        print(f"\n--- {prompt_name} ---")

        md_output = run_prompt(client, model_name, prompt_text, image_base64)
        markdown_outputs.append(md_output)

        print(md_output)

        # ------------------------
        # SAVE RAW OUTPUT
        safe_save(
            {
                "extracted_text": md_output,
                "prompt": prompt_name
            },
            table_name,
            f"{record_id}_{prompt_name}"
        )

        # ------------------------
        # PARSE
        parsed = markdown_to_dict(md_output)
        parsed_predictions.append(parsed)

        # ------------------------
        # ACCURACY
        if ground_truth:
            gt_key = prompt_config.get(prompt_name)
            truth = ground_truth.get(gt_key) if gt_key else None

            if truth:
                acc = compute_accuracy(parsed, truth)
                accuracies.append(acc)

    # ------------------------
    # MERGE
    if len(parsed_predictions) == 1:
        merged = parsed_predictions[0]
        final_md = markdown_outputs[0]
    else:
        merged = merge_predictions(parsed_predictions)
        final_md = dict_to_markdown(merged)

    overall_acc = round(sum(accuracies) / len(accuracies), 3) if accuracies else 0

    return {
        "record_id": record_id,
        "final_markdown": final_md,
        "accuracy": overall_acc
    }


# ------------------------
# CORE: ORCHESTRATOR

def run_extraction_pipeline(
    image_dir: str,
    model_name: str,
    table_name: str,
    ground_truth: dict | None = None,
    resume: bool = True
):
    """
    Main extraction pipeline.
    """

    prompts = load_prompts()
    prompt_config = load_prompt_config()

    images = load_images(image_dir)
    #client = Client(host=IP_TUTI)
    client = Client()

    results_md = ""
    processed_ids = []

    for image_path in tqdm(images):
        result = process_image(
            image_path=image_path,
            client=client,
            model_name=model_name,
            prompts=prompts,
            prompt_config=prompt_config,
            table_name=table_name,
            ground_truth=ground_truth,
            resume=resume
        )

        if result is None:
            continue

        processed_ids.append(result["record_id"])

        # ------------------------
        # REPORT BUILDING
        results_md += f"# {result['record_id']}\n\n"
        results_md += result["final_markdown"] + "\n\n"
        results_md += f"**Accuracy:** {result['accuracy']}\n\n---\n\n"

    # ------------------------
    # SAVE REPORT
    with open("results.md", "w") as f:
        f.write(results_md)

    return processed_ids


"""from pipelines.extraction_pipeline import run_extraction_pipeline

processed_ids = run_extraction_pipeline(
    image_dir=IMAGE_DIR,
    model_name=QWEN2,
    table_name="extractions",
    ground_truth=GT,
    resume=True
)"""