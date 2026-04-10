from pdf2image import convert_from_path
import os

def pdf_to_png(pdf_path):
    # Get PDF file name (e.g. "pdf1" from "pdf1.pdf")
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]

    # Create subfolder called "converted_images" in the same directory as the PDF if it does not exist
    parent_folder = os.path.dirname(pdf_path)
    output_folder = os.path.join(parent_folder, "converted_images")
    os.makedirs(output_folder, exist_ok=True)

    # Convert PDF pages to images using the library
    images = convert_from_path(pdf_path)

    # Save each page with the PDF name included
    for i, image in enumerate(images):
        image_path = os.path.join(output_folder, f"{base_name}_page_{i + 1}.png")
        image.save(image_path, "PNG")
        print(f"Page {i + 1} of {base_name}.pdf saved as {image_path}")

if __name__ == "__main__":
    pdf_file = input("Enter the path of the PDF file: ")

    if not os.path.isfile(pdf_file):
        print("Error: The specified file does not exist.")
    else:
        pdf_to_png(pdf_file)
