from a_input.load_images import load_images

IMAGE_DIR = "/home/ikutswa/data/BRIDGE/patient_documents/Test_conversion/converted_images"

images = load_images(IMAGE_DIR)
print(len(images))
print(images[:2])

image_path = images[0] #pick 1 img
print(image_path)

from utils.image_encoding import image_to_base64 # convert to base64

image_base64 = image_to_base64(image_path)
print(len(image_base64))

from b_extraction.prompts.prompt_loader import load_prompts, load_prompt_config # loading the prompts

prompts = load_prompts()
prompt_config = load_prompt_config()

print(prompts.keys())

from ollama import Client
import os
QWEN2 = "qwen3.5:35b"
IP_PAUL = os.getenv("IP_PAUL")
IP_TUTI = os.getenv("IP_TUTI")
IP_SERVER = os.getenv("IP_SERVER")

client = Client(host=IP_SERVER)
# response=client.list() ---- models available in the client
model_name = QWEN2
model_name = 'qwen3.5:35b'
QWEN = "qwen3.5:27b"

prompt_name, prompt_text = list(prompts.items())[0]

from b_extraction.extraction_pipeline import run_prompt

md_output = run_prompt(client, model_name, prompt_text, image_base64)

print(md_output)

from c_structuring.markdown_parser import markdown_to_dict # parsing

parsed = markdown_to_dict(md_output)

print(parsed)

import json # accuracy test

with open("/home/ikutswa/BRIDGEProject/truth.json") as f:
    GT = json.load(f)

gt_key = prompt_config.get(prompt_name)
truth = GT.get(gt_key)

from d_evaluation.accuracy import compute_accuracy

acc = compute_accuracy(parsed, truth)
print(acc)

parsed_predictions = [] # multi-prompts

for name, text in prompts.items():
    print("Running:", name)

    md = run_prompt(client, model_name, text, image_base64)
    parsed = markdown_to_dict(md)

    parsed_predictions.append(parsed)

from b_extraction.merge_extraction import merge_predictions

merged = merge_predictions(parsed_predictions)

print(merged)

from c_structuring.markdown_formatter import dict_to_markdown # output formatter

final_md = dict_to_markdown(merged)
print(final_md)

from b_extraction.extraction_pipeline import process_image # full extraction test

result = process_image(
    image_path=image_path,
    client=client,
    model_name=model_name,
    prompts=prompts,
    prompt_config=prompt_config,
    table_name="extractions",
    ground_truth=GT,
    resume=False
)

print(result)

from database_utils.db_utils import fetch_records # fetch md records

records = fetch_records("extractions")
print(len(records))

record_id = "---" #pick 1 record

from c_structuring.structuring_pipeline import fetch_markdown_for_record #get md

md = fetch_markdown_for_record(record_id, records)
print(md[:500])

from c_structuring.structuring_pipeline import structure_record # structure the md

structured = structure_record(
    record_id,
    md,
    model_name="qwen3.5:35b",
    base_url=IP_SERVER
)

print(structured)

from c_structuring.nar_schema_mapper import map_to_schema # MAP TO SCHEMA... SHOULD WORK ON THIS ESP sex, delivery... or might remove completely

mapped = map_to_schema(structured)
print(mapped)

from d_evaluation.run_evaluation import run_evaluation
GT_PATH = "/home/ikutswa/data/BRIDGE/patient_documents/Test_conversion/metadata/metadata.json"
df = run_evaluation(
    gt_path=GT_PATH,
    structured_table="structured"
)
print(df.head())
print(df.mean(numeric_only=True)) # get field averages

#OR
from d_evaluation.run_evaluation import load_structured_outputs

predictions = load_structured_outputs("structured")

print(len(predictions))

import json # load ground truth

with open("/home/ikutswa/BRIDGEProject/truth.json") as f:
    ground_truth = json.load(f)

print(len(ground_truth))

from d_evaluation.field_accuracy import build_accuracy_table # EVALUATION core

df = build_accuracy_table(predictions, ground_truth)

print(df.columns) # inspect table
print(df.head())

df.to_csv("field_accuracy.csv", index=False) # manual save

record_id = list(predictions.keys())[0] # Test 1 record

pred = predictions[record_id]
truth = ground_truth[record_id]

from d_evaluation.field_accuracy import compute_field_accuracy

result = compute_field_accuracy(pred, truth)

print(result)