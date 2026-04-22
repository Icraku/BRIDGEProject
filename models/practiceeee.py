import json
import base64
import ollama
from PIL import Image
import io

MODEL_NAME = "qwen3-vl:4b"

IMAGE_PATH = "/home/ikutswa/data/BRIDGE/patient_documents/Test_conversion/converted_images/40000176_NAR_2919_page_1.png"
ANNOTATION_PATH = "/home/ikutswa/PycharmProjects/BRIDGEProject/annotation.json"

def pil_to_base64(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def crop_box(image, box):
    x = float(box["x"])
    y = float(box["y"])
    w = float(box["width"])
    h = float(box["height"])

    left = x - w / 2
    top = y - h / 2
    right = x + w / 2
    bottom = y + h / 2

    return image.crop((left, top, right, bottom))

def extract_field(cropped_img, label):
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{
            "role": "user",
            "content": f"Extract all visible {label} and handwritten text from this image exactly as written, if there is any checkbox, specify only the value which is ticked. Return the output in JSON format",
            "images": [pil_to_base64(cropped_img)]
        }],
        options={"temperature": 0, "seed": 42}
    )
    return response["message"]["content"].strip()

def run():
    image = Image.open(IMAGE_PATH).convert("RGB")

    with open(ANNOTATION_PATH) as f:
        annotation = json.load(f)

    output = {}

    for box in annotation["boxes"]:
        label = box["label"]
        cropped = crop_box(image, box)
        value = extract_field(cropped, label)
        output[label] = value
        del cropped

    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    run()
