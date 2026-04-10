import os
import glob
import json

""" from prompt_config.json
{
  "baseline": "baseline",
  "trial": "baseline",
  "whole": "baseline",
  "A_labels": "labels",
  "B_section_entry": "name",
  "C_ip_no": "ip_no",
  "D_row1": "row1",
  "E_row2": "row2",
  "F_row3": "row3"
}
"""

def load_prompts(prompt_dir="/home/ikutswa/PycharmProjects/BRIDGEProject/base_prompt"):
    if not os.path.exists(prompt_dir):
        print(f"❌ Prompt folder not found: {prompt_dir}")
        return {}

    prompts = {}
    for file in glob.glob(os.path.join(prompt_dir, "*.txt")):
        name = os.path.basename(file).replace(".txt", "")
        with open(file, "r") as f:
            prompts[name] = f.read()

    if not prompts:
        print(f"❌ No .txt files found in {prompt_dir}")
    else:
        print(f"the directory is {prompt_dir}")

    return prompts


def load_prompt_config(config_path="prompt_config.json"):
    if not os.path.exists(config_path):
        print(f"❌ Prompt config not found: {config_path}")
        return {}

    with open(config_path) as f:
        return json.load(f)