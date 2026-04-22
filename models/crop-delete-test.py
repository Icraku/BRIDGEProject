import json
import base64
import ollama
from PIL import Image
from pathlib import Path
import io

MODEL_NAME = "qwen3-vl:4b"

IMAGE_PATH = "/home/ikutswa/data/BRIDGE/patient_documents/Test_conversion/converted_images/40000176_NAR_2919_page_1.png"
ANNOTATION_PATH = "/home/ikutswa/PycharmProjects/BRIDGEProject/annotation.json"

def image_to_base64(img):
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def crop_first_box(image, annotation):
    box = annotation["boxes"][10]

    x = float(box["x"])
    y = float(box["y"])
    w = float(box["width"])
    h = float(box["height"])

    left = x - w / 2
    top = y - h / 2
    right = x + w / 2
    bottom = y + h / 2

    return image.crop((left, top, right, bottom))

def run():
    image = Image.open(IMAGE_PATH).convert("RGB")

    with open(ANNOTATION_PATH) as f:
        annotation = json.load(f)

    cropped = crop_first_box(image, annotation)

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": "Extract all visible label and handwritten text from this image exactly as written, if there is any checkbox, specify only the value which is ticked. Return the output in JSON format",
                "images": [image_to_base64(cropped)]
            }
        ],
        options={"temperature": 0, "seed": 42}
    )

    result = {
        "field": annotation["boxes"][10]["label"],
        "extracted_text": response["message"]["content"]
    }

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    run()
