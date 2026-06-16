"""
a_input/image_utils.py
======================
Utilities for loading, converting and preprocessing NAR form images
before they are passed to the extraction pipeline.

Functions
---------
load_images(image_dir, extensions)
    Return a sorted list of image paths from a directory.

pdf_to_png(pdf_path, output_dir)
    Convert a PDF to per-page PNG files.

preprocess_images(image_dir, output_dir, extensions)
    Convert images to grayscale (VLM-compatible 3-channel BGR).

CLI
---
To convert a single PDF, run this file directly as follows:

    python a_input/image_utils.py path/to/file.pdf
    python a_input/image_utils.py path/to/file.pdf --out path/to/output_dir
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
from pdf2image import convert_from_path


IMAGE_EXTENSIONS: tuple[str, ...] = ("png", "jpg", "jpeg")


# ---------------------------------------------------------------------------
# Image loading

def load_images(
    image_dir: str | Path,
    extensions: tuple[str, ...] = IMAGE_EXTENSIONS,
) -> list[str]:
    """Return a sorted list of image file paths from *image_dir*.

    Parameters
    ----------
    image_dir: Directory to search for images.
    extensions:  File extensions to include (without leading dot).

    Returns
    -------
    list[str]
        Sorted absolute paths of matching image files.

    Raises
    ------
    FileNotFoundError
        If *image_dir* does not exist.
    """
    image_dir = Path(image_dir)
    if not image_dir.is_dir():
        raise FileNotFoundError(f"Image directory not found: {image_dir}")

    paths: list[Path] = []
    for ext in extensions:
        paths.extend(image_dir.glob(f"*.{ext}"))

    return sorted(str(p) for p in paths)


# ---------------------------------------------------------------------------
# PDF to PNG conversion

def pdf_to_png(
    pdf_path: str | Path,
    output_dir: str | Path | None = None,
) -> list[str]:
    """Convert every page of a PDF to a PNG file.

    Output files are named ``<pdf_stem>_page_<n>.png`` and saved to
    *output_dir*.  If *output_dir* is ``None`` a subfolder called
    ``converted_images`` is created next to the source PDF.

    Parameters
    ----------
    pdf_path: Path to the source PDF file.
    output_dir: Destination directory.  Created automatically if it does not exist.

    Returns
    -------
    list[str]
        Paths of the saved PNG files, in page order.

    Raises
    ------
    FileNotFoundError
        If *pdf_path* does not exist.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if output_dir is None:
        output_dir = pdf_path.parent / "converted_images"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pages = convert_from_path(pdf_path)
    saved: list[str] = []

    for i, page in enumerate(pages, start=1):
        dest = output_dir / f"{pdf_path.stem}_page_{i}.png"
        page.save(dest, "PNG")
        print(f"  Saved page {i}: {dest}")
        saved.append(str(dest))

    return saved


# ---------------------------------------------------------------------------
# Preprocessing

def preprocess_images(
    image_dir: str | Path,
    output_dir: str | Path,
    extensions: tuple[str, ...] = IMAGE_EXTENSIONS,
) -> list[str]:
    """Convert images to grayscale and re-save as 3-channel BGR PNGs.

    Grayscale conversion reduces noise and improves OCR / VLM accuracy.
    Images are saved back as 3-channel (BGR) files so they remain
    compatible with VLMs that expect colour inputs.

    Parameters
    ----------
    image_dir: Directory containing source images.
    output_dir: Directory to write preprocessed images.  Created if absent.
    extensions: File extensions to process.

    Returns
    -------
    list[str]
        Paths of successfully preprocessed images.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    image_paths = load_images(image_dir, extensions)
    if not image_paths:
        print(f"No images found in: {image_dir}")
        return []

    saved: list[str] = []
    for path in image_paths:
        image = cv2.imread(path)
        if image is None:
            print(f"  Warning: could not read {path} — skipping.")
            continue

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        processed = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        dest = output_dir / Path(path).name
        cv2.imwrite(str(dest), processed)
        print(f"  Preprocessed: {dest}")
        saved.append(str(dest))

    return saved


# ---------------------------------------------------------------------------
# CLI entry point  (python a_input/image_utils.py path/to/file.pdf)

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="image_utils",
        description="Convert a PDF to per-page PNG files.",
    )
    parser.add_argument("pdf", help="Path to the PDF file to convert.")
    parser.add_argument(
        "--out",
        metavar="DIR",
        default=None,
        help=(
            "Output directory for PNG files. "
            "Defaults to a 'converted_images' subfolder next to the PDF."
        ),
    )
    return parser


if __name__ == "__main__":
    args = _build_parser().parse_args()
    try:
        files = pdf_to_png(args.pdf, output_dir=args.out)
        print(f"\nDone — {len(files)} page(s) saved.")
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)