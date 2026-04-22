import cv2
import glob
import os

# ------------------------
# Paths

INPUT_DIR = "/home/ikutswa/data/BRIDGE/patient_documents/Test_conversion/converted_images"
OUTPUT_DIR = "/home/ikutswa/data/BRIDGE/patient_documents/Test_conversion/grayscale_images"

IMAGE_EXTS = ("*.png", "*.jpg", "*.jpeg")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ------------------------
# Load images

def load_images():
    images = []
    for ext in IMAGE_EXTS:
        images.extend(glob.glob(f"{INPUT_DIR}/{ext}"))
    return sorted(images)

# ------------------------
# Preprocess

def preprocess_image(image_path):
    image = cv2.imread(image_path)

    if image is None:
        print(f"❌ Could not read: {image_path}")
        return

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Convert back to 3-channel (for VLM compatibility)
    processed = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    filename = os.path.basename(image_path)
    output_path = os.path.join(OUTPUT_DIR, filename)

    cv2.imwrite(output_path, processed)

    print(f" Saved: {output_path}")

# ------------------------
# Run

def run():
    images = load_images()

    if not images:
        print("No images found.")
        return

    for img in images:
        preprocess_image(img)

if __name__ == "__main__":
    run()