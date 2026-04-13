import json
import glob
import base64
import os
import re
import ollama
from difflib import SequenceMatcher

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from tqdm import tqdm
from ollama import Client
from dotenv import load_dotenv

from nar_schema import narP1_schema, schemaP1_template
from nar_schema.narP1_schema import NARRecord
from rerun import structure_with_retry

load_dotenv()
IP_PAUL = os.getenv("IP_PAUL")
IP_TUTI = os.getenv("IP_TUTI")
IP_SERVER = os.getenv("IP_SERVER")

from prompt_loader import load_prompts, load_prompt_config
from db_utils import save_record, fetch_record, fetch_records, export_each_record_md
from md_utils import markdown_to_json

# ------------------------
QWEN_O = "qwen3-vl:4b"
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

def run_all(image_dir, model_name, resume=True):
    prompts = load_prompts()
    prompt_config = load_prompt_config()

    # load images from passed path
    IMAGE_EXTS = ("*.png", "*.jpg", "*.jpeg")
    images = []
    for ext in IMAGE_EXTS:
        images.extend(glob.glob(f"{image_dir}/{ext}"))
    images = sorted(images)

    client_run = Client(host=IP_SERVER)

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
        """safe_save(
            {
                "final_markdown": final_md,
                "accuracy": overall_acc
            },
            record_id + "_FINAL"
        )"""

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
    records = fetch_records(table_name) # Prints the fetched data

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

def get_true_option(field_dict):
    """
    Returns the key where value == True
    """
    if not isinstance(field_dict, dict):
        return None

    for k, v in field_dict.items():
        if v is True:
            return k

    return None

def get_boolean_from_suffix(data, base_key):
    """
    Returns the boolean value from suffix data.
    :param data:
    :param base_key:
    :return:
    """
    return data.get(f"{base_key}_Y", False)

def map_to_schema(structured_output):
    """
    Maps values and keys to schema
    :param structured_output:
    :return:
    """
    infant = (
        structured_output.get("A: Infant Details") or
        structured_output.get("Infant Details") or
        {}
    )

    A_B = (
        structured_output.get("A: B") or
        structured_output.get("A_B") or
        {}
    )

    symptoms = (
        structured_output.get("E: History and examination", {})
        .get("Symptoms", {})
        or
        structured_output.get("History and examination", {})
        .get("Symptoms & History", {})
        or
        {}
    )

    # ------------------------
    # SEX
    sex = None

    if "Sex" in infant:
        sex = get_true_option(infant["Sex"])  # F/M/I

    elif any(k.startswith("Sex_") for k in infant):
        if infant.get("Sex_F"):
            sex = "F"
        elif infant.get("Sex_M"):
            sex = "M"
        elif infant.get("Sex_I"):
            sex = "I"

    # ------------------------
    # DELIVERY
    delivery = None

    if "Delivery" in infant:
        delivery = get_true_option(infant["Delivery"])

    elif any(k.startswith("Delivery_") for k in infant):
        for k in ["SVD", "CS", "Vacuum", "Forceps", "Breech"]:
            if infant.get(f"Delivery_{k}"):
                delivery = k

    # ------------------------
    # BORN OUTSIDE
    born_outside = None

    if "Born outside facility?" in infant:
        born_outside = infant["Born outside facility?"].get("Y", False)

    elif "Born_outside_facility_Y" in infant:
        born_outside = infant.get("Born_outside_facility_Y", False)

    # ------------------------
    # MULTIPLE DELIVERY
    multiple = None

    if "Multiple delivery" in infant:
        multiple = infant["Multiple delivery"].get("Y", False)

    elif "Multiple_delivery_Y" in infant:
        multiple = infant.get("Multiple_delivery_Y", False)

    # ------------------------
    # CRACKLES
    crackles = None

    if "Crackles" in A_B:
        crackles = A_B["Crackles"].get("Y", False)

    elif "Crackles_Y" in infant:
        crackles = infant.get("Crackles_Y", False)

    # ------------------------
    # SYMPTOM EXAMPLE
    reduced_movement = None

    if "Reduced / Absent movement" in symptoms:
        reduced_movement = symptoms["Reduced / Absent movement"].get("Y", False)

    elif "Reduced / Absent movement_Y" in symptoms:
        reduced_movement = symptoms.get("Reduced / Absent movement_Y", False)

    # ------------------------
    return {
        "crackles": crackles,
        "sex": sex,
        "delivery": delivery,
        "born_outside": born_outside,
        "multiple_delivery": multiple,
        "Reduced_movement": reduced_movement
    }

def strip_markdown_fences(text):
    return re.sub(r"```[a-zA-Z]*\n?|```", "", text).strip()

def run_structuring(image_ids, model_name2, resume, table_in="extractions", table_out2="structured_T3"):
    """
    Convert all markdown records in table_in to JSON and save to table_out
        Args:
        image_ids (list): List of record IDs in table_in to process
        model_name2 (str): Model to use for structuring
        resume (bool): Skip if already structured
        table_in (str): Source table name
        table_out (str): Destination table name

        structured_T2- I extracted all the fields from the markdown - the automatic fallback the previous was:
            (2. For blank or unfilled fields:
               - include the key
               - set value as null)
        structured_T3- I changed the instructions for the empty fields
    """
    structured_ids = []
    client_str = Client(host=IP_SERVER)

    # Fetch all records from table_in
    all_records = fetch_records(table_in)

    image_ids = get_processed_ids("extractions")
    image_ids2=set([i.split("_page")[0] for i in image_ids])

    for record_id in tqdm(image_ids2):
        print(f"\n=== Structuring {record_id} ===")

        # ------------------------
        # RESUME
        existing_structured = None

        if resume:
            try:
                existing_structured = fetch_record(table_out2, record_id)
            except Exception as e:
                print(f"Resume check failed: {e}")

        if existing_structured:
            print(f"Structured exists, reusing: {record_id}")

            if isinstance(existing_structured, list):
                structured_output = existing_structured[0].get("structured_text", {})
            else:
                structured_output = existing_structured.get("structured_text", {})

            mapped_output = map_to_schema(structured_output) # WORK ON THE MAPPING LIST

            # Save mapped ONLY
            save_record(
                {
                    "mapped_fields": mapped_output
                },
                "test",
                record_id
            )

            structured_ids.append(record_id)
            continue

        # ------------------------
        # FETCH MARKDOWN FROM SURREAL table_in
        try:
            # Gets the id then joins for page 1 and 2
            record_list = [r for r in all_records
                      if record_id in str(r.get("id")).split(":")[1]]
            record_markdown="\n".join([t['extracted_text'] for t in record_list])


        except Exception as e:
            print(f"Failed to fetch {record_id}: {e}")
            continue

        if not record_list:
            print("No record found, skipping")
            continue

        # Combine markdowns and remove the fences
        markdown_list = [
            strip_markdown_fences(r.get("extracted_text", ""))
            for r in record_list if "extracted_text" in r
        ]
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
        system_prompt=f'Extract information from the provided Markdown. The response MUST be a json. The format should be {NARRecord.model_fields}'.replace("{","{{").replace("}","}}")
        prompt_template = ChatPromptTemplate.from_messages(
            [("system", system_prompt), ("user", "{__text__}")]
        )
        prompt = prompt_template.invoke({'__text__': record_markdown})

        llm = ChatOllama(
            model=QWEN2,
            base_url=IP_SERVER  # Replace with your host IP
        )
        structured_llm=llm.with_structured_output(NARRecord)

        res2=structured_llm.invoke(prompt)
        res2.model_dump_json()


        client_str.chat(model="qwen3.5:35b",messages=prompt.to_messages())

        # ------------------------
        # CALL MODEL
        try:
            response = client_str.chat(
                model=model_name2,
                messages=[
                    {
                        "role":"system",
                        "content":system_prompt
                    },
                    {
                        "role": "user",
                        "content": record_markdown
                    }
                ],
                options={"seed": 42}
            )

            try:
                structured_output = structure_with_retry(md_text, model_name2)

                if structured_output is None:
                    print("Retry failed, attempting fallback normalization...")
                    continue

                # EXTRACT TRUE VALUES + MAP
                mapped_output = map_to_schema(structured_output)

            except json.JSONDecodeError as e:
                print(f"JSON parsing failed: {e}")
                continue

        except Exception as e:
            print(f"Model failed: {e}")
            continue

        if mapped_output is None:
            print("Mapping failed, skipping save")
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

    with open("/home/ikutswa/BRIDGEProject/truth.json") as f:
        GT = json.load(f)

    run_all(image_dir=IMAGE_DIR, model_name=QWEN2, resume=RESUME)
    image_ids = get_processed_ids("extractions")
    #export_each_record_md("extractions") ---is an export logic that exports to markdown_exports
    structured_ids = run_structuring(
        image_ids=image_ids,
        model_name2=QWEN2,
        resume=True
    )


    print("Structured:", structured_ids)

    #parsed_results = process_markdown_folder()

    #with open("parsed_from_md.json", "w") as f:
        #json.dump(parsed_results, f, indent=4)