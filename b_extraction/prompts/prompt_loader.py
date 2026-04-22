import os
import glob
import json

def load_prompts(prompt_dir="/home/ikutswa/BridgeProject2/BRIDGEProject/b_extraction/prompts"):
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
        print(f"the prompt directory is {prompt_dir}")

    return prompts


def load_prompt_config(config_path="/home/ikutswa/BridgeProject2/BRIDGEProject/b_extraction/prompts/prompt_config.json"):
    if not os.path.exists(config_path):
        print(f"❌ Prompt config not found: {config_path}")
        return {}

    with open(config_path) as f:
        return json.load(f)