import json
import base64
import ollama
from PIL import Image
import io, re, glob, os

MODEL_NAME = "qwen3-vl:4b"

ANNOTATION_PATH = "/home/ikutswa/PycharmProjects/BRIDGEProject/annotation.json"

IMAGE_DIR = "/home/ikutswa/data/BRIDGE/patient_documents/Test_conversion/converted_images/"
IMAGE_EXTS = ("*.png", "*.jpg", "*.jpeg")

IMAGE_PATHS = []
for ext in IMAGE_EXTS:
    IMAGE_PATHS.extend(glob.glob(f"{IMAGE_DIR}/{ext}"))

def pil_to_base64(img):
    """
    Decode PIL image into base64 encoded string
    :param img:
    :return: decoded base64 string
    """
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def crop_box(image, box):
    """
    Crop a box around the image
    :param image, box:
    :return: cropped image
    """
    x = float(box["x"])
    y = float(box["y"])
    w = float(box["width"])
    h = float(box["height"])
    cropped = image.crop((
        x - w / 2,
        y - h / 2,
        x + w / 2,
        y + h / 2
    ))
    print(f"  Cropped '{box['label']}' at ({x},{y},{w},{h})")
    return cropped

def compute_confidence(value, field_label):
    """
    Heuristic confidence score for extracted fields
    Returns float between 0.0 and 1.0
    """
    if not value or value == "N/A":
        return 0.0

    score = 0.0

    # 1. Presence
    score += 0.4

    # 2. Not just the label repeated
    if value.lower() != field_label.lower():
        score += 0.2

    # 3. Character cleanliness
    clean_chars = re.sub(r"[^a-zA-Z0-9+./\- ]", "", value)
    cleanliness_ratio = len(clean_chars) / max(len(value), 1)
    score += 0.3 * cleanliness_ratio

    # 4. Length heuristic
    if len(value.strip()) >= 2:
        score += 0.1

    return round(min(score, 1.0), 2)

def normalize_field(value, field_label):
    """
    Normalize a field value
    :param value, field_label:
    :return: value as a string to enforce strict JSON
    """
    if not value:
        return ""

    if isinstance(value, str):
        value = value.strip()

        # Try parsing inner JSON
        if value.startswith("{") and value.endswith("}"):
            try:
                parsed = json.loads(value)
            except Exception:
                return value

            # Priority 1: checked_value
            if "checked_value" in parsed and parsed["checked_value"]:
                return parsed["checked_value"].strip()

            # Priority 2: any meaningful value
            for k, v in parsed.items():
                if not v:
                    continue
                if isinstance(v, str):
                    v_clean = v.strip()
                    if v_clean.lower() != field_label.lower() and ":" not in v_clean:
                        return v_clean

            return ""

        return value

    return str(value)

def extract_field(cropped_img, label):
    """
    Extract fields from cropped image
    :param cropped_img:
    :param label:
    :return: value of the fields as a string using the prompt
    """
    print(f"    Sending '{label}' to Qwen for extraction...")
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{
            "role": "user",
            "content": f"Extract all visible {label} and handwritten text from this image exactly as written, if there is any checkbox, specify only the value which is ticked. Return the output strictly in JSON format. If the value part is not given only use N/A and nothing else",
            "images": [pil_to_base64(cropped_img)]
        }],
        options={"temperature": 0, "seed": 42}
    )
    value = response["message"]["content"].strip()
    print(f"    Extracted value for '{label}': '{value}'")
    return value

def run():
    """
    Runs the whole pipeline
    :return: final output as JSON
    """
    print(f"Loading annotation JSON: {ANNOTATION_PATH}")
    with open(ANNOTATION_PATH) as f:
        annotation = json.load(f)

    all_results = []

    for image_path in IMAGE_PATHS:
        print(f"\n=== Processing image: {image_path} ===")
        image = Image.open(image_path).convert("RGB")

        image_output = {}
        confidences = []

        print(f"Processing {len(annotation['boxes'])} boxes...")
        for idx, box in enumerate(annotation["boxes"], 1):
            label = box["label"]
            print(f"\n[{idx}/{len(annotation['boxes'])}] Processing field: '{label}'")

            cropped = crop_box(image, box)
            raw_value = extract_field(cropped, label)

            normalized = normalize_field(raw_value, label)
            confidence = compute_confidence(normalized, label)

            image_output[label] = {
                "value": normalized,
                "confidence": confidence
            }

            confidences.append(confidence)
            del cropped  # free memory immediately

        image_confidence = round(
            sum(confidences) / max(len(confidences), 1), 2
        )

        all_results.append({
            "image": os.path.basename(image_path),
            "fields": image_output,
            "image_confidence": image_confidence
        })

    print("\n=== Final Extracted JSON ===")
    print(json.dumps(all_results, indent=2))

if __name__ == "__main__":
    run()
