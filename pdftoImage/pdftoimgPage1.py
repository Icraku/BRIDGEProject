from pdf2image import convert_from_path
import os
import glob

def batch_pdf_to_png_first_page(
    pdf_dir,
    output_subdir="converted_images",
    dpi=300,
    skip_existing=True
):
    """
    Converts the FIRST PAGE of all PDFs in a directory to PNG images.

    Returns:
        List of image paths
    """

    pdf_paths = glob.glob(os.path.join(pdf_dir, "*.pdf"))
    image_paths = []

    if not pdf_paths:
        print("No PDF files found.")
        return image_paths

    for pdf_path in pdf_paths:
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        parent_folder = os.path.dirname(pdf_path)
        output_folder = os.path.join(parent_folder, output_subdir)
        os.makedirs(output_folder, exist_ok=True)

        image_path = os.path.join(output_folder, f"{base_name}_page_1.png")

        if skip_existing and os.path.exists(image_path):
            print(f"Skipping (already exists): {image_path}")
            image_paths.append(image_path)
            continue

        try:
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                first_page=1,
                last_page=1
            )

            images[0].save(image_path, "PNG")
            image_paths.append(image_path)

            print(f"Converted: {pdf_path} → {image_path}")

        except Exception as e:
            print(f"Failed to convert {pdf_path}: {e}")

    return image_paths

if __name__ == "__main__":
    pdf_folder = "/home/ikutswa/data/BRIDGE/patient_documents/Test_conversion"
    image_paths = batch_pdf_to_png_first_page(pdf_folder)

    print("\nGenerated images:")
    for p in image_paths:
        print(p)