import base64

def image_to_base64(image_path: str) -> str:
    """
    Encodes image file to base64 string.
    """
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")