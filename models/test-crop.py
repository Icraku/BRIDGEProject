import json
import base64
import ollama
from pathlib import Path

MODEL_NAME = "qwen3-vl:4b"

IMAGE_PATHS = [
    "/home/ikutswa/Pictures/Screenshots/Screenshot from 2026-01-13 10-42-35.png",
    "/home/ikutswa/Pictures/Screenshots/Screenshot from 2026-01-13 10-43-07.png",
    "/home/ikutswa/Pictures/Screenshots/Screenshot from 2026-01-13 10-43-27.png",
]

def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def run_baseline():
    results = []

    for image_path in IMAGE_PATHS:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": "Extract all visible label and handwritten text from this image exactly as written, if there is any checkbox, specify only the value which is ticked. Return the output in JSON format",
                    "images": [image_to_base64(image_path)]
                }
            ],
            options={"temperature": 0, "seed": 42}
        )

        output = response["message"]["content"]

        results.append({
            "image": Path(image_path).name,
            "raw_output": output
        })

        print(f"\n=== {Path(image_path).name} ===\n")
        print(output)

    with open("qwen_baseline_outputs.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_baseline()
