import base64
import io
import json
from pathlib import Path

import ollama
from PIL import Image

# =========================================================
# CONFIGURATION
# =========================================================

MODEL_NAME = "qwen3-vl:4b"

IMAGE_PATH = Path(
    "/home/ikutswa/data/BRIDGE/patient_documents/Test_conversion/converted_images/63000002_NAR_16_page_1.png"
)

# Template image size
TEMPLATE_WIDTH = 2480
TEMPLATE_HEIGHT = 3508

# Calibration offsets
OFFSET_X = -420
OFFSET_Y = -47

# =========================================================
# TEMPLATE FIELDS (TOP-LEFT COORDINATES)
# =========================================================

FIELDS = [
    {"id": "1", "label": "name", "x": 850, "y": 543, "width": 844, "height": 94},
    {"id": "4", "label": "ip no", "x": 1899, "y": 543, "width": 800, "height": 90},
    {"id": "7", "label": "date of admission", "x": 850, "y": 637, "width": 690, "height": 87},
    {"id": "8", "label": "time baby seen", "x": 1825, "y": 630, "width": 394, "height": 94},
    {"id": "9", "label": "sex", "x": 2398, "y": 638, "width": 300, "height": 84},
    {"id": "A", "label": "dob", "x": 748, "y": 729, "width": 678, "height": 90},
    {"id": "B", "label": "time of birth", "x": 1660, "y": 727, "width": 372, "height": 90},
    {"id": "C", "label": "gestation", "x": 2206, "y": 723, "width": 172, "height": 88},
    {"id": "D", "label": "age", "x": 2509, "y": 723, "width": 190, "height": 88},
    {"id": "E", "label": "gestation age from", "x": 875, "y": 818, "width": 314, "height": 118},
    {"id": "G", "label": "APGAR", "x": 1343, "y": 818, "width": 508, "height": 116},
    {"id": "H", "label": "bvm resus at birth", "x": 992, "y": 935, "width": 228, "height": 62},
    {"id": "I", "label": "rom", "x": 1360, "y": 935, "width": 492, "height": 60},
    {"id": "J", "label": "delivery", "x": 2045, "y": 814, "width": 656, "height": 120},
    {"id": "K", "label": "if cs", "x": 2215, "y": 929, "width": 486, "height": 64},
    {"id": "L", "label": "multiple delivery", "x": 847, "y": 1002, "width": 246, "height": 126},
    {"id": "M", "label": "if multiple delivery then number", "x": 1308, "y": 1002, "width": 172, "height": 122},
    {"id": "N", "label": "born outside facility", "x": 1777, "y": 1002, "width": 266, "height": 60},
    {"id": "O", "label": "where if born outside facility", "x": 2044, "y": 1065, "width": 654, "height": 57},
]

# =========================================================
# HELPERS
# =========================================================

def image_to_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def compute_scale_factors(image: Image.Image):
    sw, sh = image.size
    return sw / TEMPLATE_WIDTH, sh / TEMPLATE_HEIGHT


def crop_field(image: Image.Image, field: dict, scale_x: float, scale_y: float) -> Image.Image:
    x = field["x"] * scale_x + OFFSET_X
    y = field["y"] * scale_y + OFFSET_Y
    w = field["width"] * scale_x
    h = field["height"] * scale_y

    left = int(x)
    top = int(y)
    right = int(x + w)
    bottom = int(y + h)

    return image.crop((left, top, right, bottom))


def extract_text_with_qwen(cropped: Image.Image) -> str:
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": (
                    "Extract all visible label and handwritten text from this image exactly as written. "
                    "If there is any checkbox, specify only the value which is ticked. "
                    "Return the output in JSON format."
                ),
                "images": [image_to_base64(cropped)],
            }
        ],
        options={"temperature": 0, "seed": 42},
    )

    return response["message"]["content"]

# =========================================================
# MAIN PIPELINE
# =========================================================

def run():
    if not IMAGE_PATH.exists():
        raise FileNotFoundError(f"Image not found: {IMAGE_PATH}")

    image = Image.open(IMAGE_PATH).convert("RGB")
    scale_x, scale_y = compute_scale_factors(image)

    results = {}

    print(f"📄 Processing image: {IMAGE_PATH.name}")
    print(f"🔢 Total fields: {len(FIELDS)}\n")

    for idx, field in enumerate(FIELDS, start=1):
        print(f"➡️  [{idx}/{len(FIELDS)}] Extracting: {field['label']}")

        cropped = crop_field(image, field, scale_x, scale_y)
        extracted_text = extract_text_with_qwen(cropped)

        results[field["label"]] = {
            "field_id": field["id"],
            "text": extracted_text,
        }

        print(f"   ✅ Done: {field['label']}\n")

    print(json.dumps(results, indent=2))


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    run()
