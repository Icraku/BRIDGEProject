import glob
import os

def load_images(image_dir: str, extensions=("png", "jpg", "jpeg")) -> list[str]:
    """
    Loads sorted image paths from a directory.
    """
    images = []

    for ext in extensions:
        images.extend(glob.glob(os.path.join(image_dir, f"*.{ext}")))

    return sorted(images)