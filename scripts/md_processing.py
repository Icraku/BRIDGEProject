import os

from c_structuring.markdown_parser import markdown_to_dict

def process_markdown_folder(folder: str = "markdown_exports") -> list:
    """
    Convert markdown files in a folder to structured dictionaries.
    """

    results = []

    for filename in os.listdir(folder):
        if not filename.endswith(".md"):
            continue

        file_path = os.path.join(folder, filename)

        with open(file_path, "r", encoding="utf-8") as f:
            md = f.read()

        parsed = markdown_to_dict(md)

        results.append({
            "file": filename,
            "data": parsed
        })

    return results