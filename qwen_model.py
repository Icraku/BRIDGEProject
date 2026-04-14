import json
import glob
import base64
import os
import re
from difflib import SequenceMatcher
from tqdm import tqdm
from ollama import Client
from dotenv import load_dotenv

load_dotenv()
IP_PAUL = os.getenv("IP_PAUL")
IP_TUTI = os.getenv("IP_TUTI")
IP_SERVER = os.getenv("IP_SERVER")

from prompt_loader import load_prompts, load_prompt_config
from db.db_utils import save_record, fetch_record, fetch_records
from md_utils import markdown_to_json

# ------------------------
QWEN = "qwen3.5:27b"
QWEN2 = "qwen3.5:35b"
MEDGEMMA_T = "medgemma27-full:latest"
MEDGEMMA = "puyangwang/medgemma-27b-it:q8"
table_name = "extractions"
IMAGE_DIR = "/home/ikutswa/data/BRIDGE/patient_documents/Test_conversion/converted_images"

#client = Client(host=IP_PAUL)

RESUME=True
# ------------------------
# LOAD IMAGES

def load_images():
    IMAGE_EXTS = ("*.png", "*.jpg", "*.jpeg")
    images = []
    for ext in IMAGE_EXTS:
        images.extend(glob.glob(f"{IMAGE_DIR}/{ext}"))
    return sorted(images)

def image_to_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# ------------------------
# MARKDOWN to DICT for accuracy scores

def markdown_to_dict(text):
    """
    Converts markdown into dict
    for accuracy scores
    """
    # Remove ```json fences if present
    text = re.sub(r"```(\w+)?", "", text).strip()

    # ------------------------
    # Try JSON
    try:
        return json.loads(text)
    except:
        pass

    # ------------------------
    # Markdown fallback
    data = {}
    for line in text.split("\n"):
        match = re.match(r"-\s*(.*?):\s*(.*)", line)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()

            if value.lower() in ["", "-", "n/a", "na"]:
                value = "N/A"

            data[key] = value

    return data

# ------------------------
# ACCURACY

def fuzzy_equal(a, b, threshold=0.85):
    """Return True if a and b match with ≥ threshold similarity."""
    return SequenceMatcher(None, str(a), str(b)).ratio() >= threshold


def compute_accuracy(pred, truth):
    if not isinstance(pred, dict) or not isinstance(truth, dict):
        return 0.0

    correct = 0

    for key in truth:
        if key in pred:
            if pred[key] == truth[key] or fuzzy_equal(pred[key], truth[key]):
                correct += 1

    return correct / len(truth)

def merge_predictions(pred_dicts):
    """
    Merge using majority voting (for multi-prompt)
    """

    merged = {}

    all_keys = set()
    for d in pred_dicts:
        all_keys.update(d.keys())

    for key in all_keys:
        values = [d.get(key, "N/A") for d in pred_dicts]

        # count frequency
        freq = {}
        for v in values:
            freq[v] = freq.get(v, 0) + 1

        # pick most common
        best_value = max(freq, key=freq.get)

        merged[key] = best_value

    return merged

def dict_to_markdown(data):
    """ Converts dict into markdown results"""
    md = "## Final Extraction\n\n"
    for k, v in data.items():
        md += f"- {k}: {v}\n"
    return md

def safe_save(record, record_id):
    """
    Save a record to Surreal
    :param record:
    :param record_id:
    :return:
    """
    try:
        save_record(record, table_name, record_id)
        print(f"Saved: {record_id}")
        return True
    except Exception as e:
        print(f"Save failed ({record_id}): {e}")
        return False

def process_markdown_folder(folder="markdown_exports"):
    """
    Process Markdown exports
    :param folder:
    :return:
    """
    results = []

    for filename in os.listdir(folder):
        if not filename.endswith(".md"):
            continue

        file_path = os.path.join(folder, filename)

        with open(file_path, "r", encoding="utf-8") as f:
            md = f.read()

        parsed = markdown_to_json(md)

        results.append({
            "file": filename,
            "data": parsed
        })

    return results

# ------------------------
# MAIN

"""def run_all():
    prompts = load_prompts()
    prompt_config = load_prompt_config()
    images = load_images()

    client = Client(host=IP_PAUL)

    results_md = ""

    for image_path in tqdm(images):
        image_name = os.path.basename(image_path)
        record_id = os.path.splitext(image_name)[0]

        print(f"\n=== Processing {image_name} ===")

        # ------------------------
        # RESUME
        if RESUME:
            try:
                existing = fetch_record(table_name, record_id + "_base")
                if existing:
                    print("Skipping (already processed)")
                    continue
            except:
                pass

        image_base64 = image_to_base64(image_path)

        parsed_predictions = []
        accuracies = []
        markdown_outputs = []

        # ------------------------
        # RUN PROMPTS
        for prompt_name, prompt_text in prompts.items():
            print(f"\n--- {prompt_name} ---")

            response = client.chat(
                model=QWEN,
                messages=[
                    {
                        "role": "user",
                        "content": prompt_text,
                        "images": [image_base64]
                    }
                ],
                options={"seed": 42}
            )

            md_output = response["message"]["content"]
            markdown_outputs.append(md_output)

            print(md_output)

            # Save raw markdown per prompt
            if safe_save(
                {
                    "extracted_text": md_output,
                    "prompt": prompt_name
                },
                record_id + "_" + prompt_name
            ):
                print(f" Saved to DB: {record_id}_{prompt_name}")

            else:
                print(f"Failed permanently: {id}")

            # Print raw output from model
            print("Raw model output:\n", md_output) -----

            # Parse
            parsed = markdown_to_dict(md_output)
            parsed_predictions.append(parsed)

            # Accuracy
            gt_key = prompt_config.get(prompt_name)
            truth = GT.get(gt_key) if gt_key else None

            if truth:
                acc = compute_accuracy(parsed, truth)
                print(f"Accuracy: {acc}")
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

        print("\n=== FINAL MERGED ===\n")
        print(final_md)

        # ------------------------
        # SAVE FINAL
        safe_save(
            {
                "final_markdown": final_md,
                "accuracy": overall_acc
            },
            record_id + "_FINAL"
        )

        # ------------------------
        # SAVE REPORT
        results_md += f"# {image_name}\n\n"
        results_md += final_md + "\n\n"
        results_md += f"**Accuracy:** {overall_acc}\n\n---\n\n"

    # ------------------------
    # WRITE FILE
    with open("results.md", "w") as f:
        f.write(results_md)"""

def run_all(image_dir, model_name, resume=True):
    prompts = load_prompts()
    prompt_config = load_prompt_config()

    # load images from passed path
    IMAGE_EXTS = ("*.png", "*.jpg", "*.jpeg")
    images = []
    for ext in IMAGE_EXTS:
        images.extend(glob.glob(f"{image_dir}/{ext}"))
    images = sorted(images)

    client_run = Client(host=IP_TUTI)

    results_md = ""
    processed_ids = []

    for image_path in tqdm(images):
        image_name = os.path.basename(image_path)
        record_id = os.path.splitext(image_name)[0]

        print(f"\n=== Processing {image_name} ===")

        # ------------------------
        # RESUME
        if resume:
            try:
                existing = fetch_record(table_name, record_id + "_base")
                if existing:
                    print("Skipping (already processed)")
                    processed_ids.append(record_id)
                    continue
            except:
                pass

        image_base64 = image_to_base64(image_path)

        parsed_predictions = []
        accuracies = []
        markdown_outputs = []

        # ------------------------
        # RUN PROMPTS
        for prompt_name, prompt_text in prompts.items():
            print(f"\n--- {prompt_name} ---")

            response = client_run.chat(
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

            md_output = response["message"]["content"]
            markdown_outputs.append(md_output)

            print(md_output)

            # Save raw markdown per prompt
            if safe_save(
                {
                    "extracted_text": md_output,
                    "prompt": prompt_name
                },
                record_id + "_" + prompt_name
            ):
                print(f" Saved to DB: {record_id}_{prompt_name}")

            else:
                print(f"Failed permanently: {id}")

            # Print raw output from model
            print("Raw model output:\n", md_output)

            # Parse
            parsed = markdown_to_dict(md_output)
            parsed_predictions.append(parsed)

            # Accuracy
            gt_key = prompt_config.get(prompt_name)
            truth = GT.get(gt_key) if gt_key else None

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

        # ------------------------
        # SAVE FINAL
        safe_save(
            {
                "final_markdown": final_md,
                "accuracy": overall_acc
            },
            record_id + "_FINAL"
        )

        processed_ids.append(record_id)

        # ------------------------
        # REPORT
        results_md += f"# {image_name}\n\n"
        results_md += final_md + "\n\n"
        results_md += f"**Accuracy:** {overall_acc}\n\n---\n\n"

    # ------------------------
    # WRITE FILE (optional, keep it)
    with open("results.md", "w") as f:
        f.write(results_md)

    return processed_ids

def get_processed_ids(table_name="extractions"):
    records = fetch_records(table_name)

    ids = set()

    for r in records:
        rid = str(r.get("id")).split(":")[1]
        ids.add(rid)

    image_ids = list(ids)

    return list(ids)

def normalize_json_quotes(raw_text: str) -> str:
    """
    Convert single quotes to double quotes ONLY where appropriate,
    so the string becomes valid JSON.
    """
    # Replace single-quoted values with double quotes
    fixed = re.sub(r":\s*'([^']*)'", r': "\1"', raw_text)

    # Replace single-quoted keys if any
    fixed = re.sub(r"'([^']*)'\s*:", r'"\1":', fixed)

    return fixed

def extract_true_values(data):
    """
    Recursively extract only keys where value == True.
    Returns a simplified dict.
    """
    if isinstance(data, dict):
        result = {}

        for key, value in data.items():
            if isinstance(value, dict):
                nested = extract_true_values(value)

                # If nested dict has true values, keep it
                if nested:
                    result[key] = nested

            elif value is True:
                result[key] = True

        return result

    return {}

def flatten_true_fields(data):
    """
    Convert {A: {X: true}} → {A: [X]}
    """
    flattened = {}

    for key, value in data.items():
        if isinstance(value, dict):
            true_keys = [k for k, v in value.items() if v is True]

            if true_keys:
                flattened[key] = true_keys

    return flattened

def map_to_schema(structured_output):
    infant = structured_output.get("A: Infant Details", {})

    extracted_true = extract_true_values(infant)
    flattened = flatten_true_fields(extracted_true)

    mapped = {
        "sex": flattened.get("Sex", []),
        "delivery": flattened.get("Delivery", []),
        "born_outside": flattened.get("Born outside facility?", []),
        "multiple_delivery": flattened.get("Multiple delivery", [])
    }

    return mapped

def run_structuring(image_ids, model_name2, resume, table_in="extractions", table_out2="structured_T3"):
    """
    Convert all markdown records in table_in to JSON and save to table_out
        Args:
        image_ids (list): List of record IDs in table_in to process
        model_name2 (str): Model to use for structuring
        resume (bool): Skip if already structured
        table_in (str): Source table name
        table_out (str): Destination table name
    """
    structured_ids = []
    client_str = Client(host=IP_SERVER)

    # Fetch all records from table_in
    all_records = fetch_records(table_in)

    image_ids = get_processed_ids("extractions")

    for record_id in tqdm(image_ids):
        print(f"\n=== Structuring {record_id} ===")

        # ------------------------
        # RESUME
        if resume:
            try:
                existing = fetch_record(table_out2, record_id)
                if existing:
                    print("Skipping {record_id} (already structured)")
                    structured_ids.append(record_id)
                    continue
            except Exception as e:
                print(f"Resume check skipped for {record_id} (table may not exist): {e}")

        # ------------------------
        # FETCH MARKDOWN FROM SURREAL table_in
        try:

            record_list = [r for r in all_records
                      if str(r.get("id")).split(":")[1] == record_id]

        except Exception as e:
            print(f"Failed to fetch {record_id}: {e}")
            continue

        if not record_list:
            print("No record found, skipping")
            continue

        # Combine markdowns
        markdown_list = [r.get("extracted_text", "") for r in record_list if "extracted_text" in r]
        md_text = "\n\n".join(markdown_list)

        if not md_text:
            print("Empty markdown, skipping")
            continue

        # ------------------------
        # PROMPT FOR STRUCTURING
        prompt = f"""
                You are an expert medical document structuring system.

                Your task is to convert the provided Markdown into a COMPLETE structured JSON.

                ---

                ## CORE INSTRUCTION

                Extract ALL information from the Markdown.

                - Do NOT lose any information
                - Do NOT summarize
                - Do NOT skip any fields
                - Preserve the original structure as much as possible

                ---

                ## EXTRACTION RULES

                1. Extract EVERY field, including:
                   - filled values
                   - blank/unfilled fields
                   - unclear or messy text

                2. For blank or unfilled fields:
                   - include the key
                   - set value as false for the options especially in checkboxes
                   for example:
                       - N [ ] → false
                       - Y [ ] → false
                       - Unknown [ ] → false

                3. For unclear/unreadable text:
                   - include it exactly as written (e.g. "[unclear]", "?")

                4. Extract checkboxes:
                   - [x] → true
                   - [ ] → false

                5. Keep original section groupings such as:
                   - "Infant Details"
                   - "Mother's Details"
                   - "History and examination"
                   - etc.

                6. Do NOT rename keys
                7. Do NOT map to any external schema
                8. Do NOT drop any fields

                ---

                ## OUTPUT RULES

                - Return ONLY valid JSON
                - No explanations
                - No markdown
                - Use double quotes for ALL keys and values
                - Use null for missing values
                - Do NOT use single quotes

                ---

                ## INPUT

                {md_text}
                """

        # ------------------------
        # CALL MODEL
        try:
            response = client_str.chat(
                model=model_name2,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={"seed": 42}
            )

            raw_output = response["message"]["content"]

            # Remove ```json ... ``` wrapper
            cleaned = re.sub(r"^```json\s*|\s*```$", "", raw_output.strip(), flags=re.DOTALL)

            # Normalize quotes
            normalized = normalize_json_quotes(cleaned)
            mapped_output = None

            try:
                structured_output = json.loads(normalized)
                # EXTRACT TRUE VALUES + MAP
                mapped_output = map_to_schema(structured_output)

            except json.JSONDecodeError as e:
                print(f"JSON parsing failed: {e}")
                print("Raw output was:", raw_output)
                continue

        except Exception as e:
            print(f"Model failed: {e}")
            continue

        # ------------------------
        # SAVE RESULT
        try:
            #record = NARRecord(**structured_output)
            save_record(
                {
                    "structured_text": structured_output
                },
                table_out2,
                record_id
            )

            # ------------------------
            # SAVE MAPPED (clean schema)
            save_record(
                {
                    "mapped_fields": mapped_output
                },
                "test",
                record_id
            )

            print(f"Saved structured + mapped: {record_id}")

            print(f"Saved structured: {record_id}")
            structured_ids.append(record_id)

        except Exception as e:
            print(f"Save failed: {e}")
            continue

    return structured_ids

# ------------------------

if __name__ == "__main__":

    with open("/home/ikutswa/PycharmProjects/BRIDGEProject/truth.json") as f:
        GT = json.load(f)

    run_all(image_dir=IMAGE_DIR, model_name=QWEN, resume=RESUME)
    #export_each_record_md("extractions") ---is an export logic that exports to markdown_exports
    structured_ids = run_structuring(
        image_ids=image_ids,
        model_name2=MEDGEMMA_T,
        resume=True
    )

    print("Structured:", structured_ids)

    #parsed_results = process_markdown_folder()

    #with open("parsed_from_md.json", "w") as f:
        #json.dump(parsed_results, f, indent=4)