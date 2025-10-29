#!/usr/bin/env python3
"""
Image Slicer - Splits large bitmap images into smaller chunks

This script takes a large bitmap image and slices it into smaller 1024x1024 pixel chunks.
The output files are saved as PNG format with naming convention: row_col.png

Usage:
    python image_slicer.py

Requirements:
    - Pillow (PIL) library
"""

import os
from PIL import Image
import math

# Pillow raises a DecompressionBombError when an image's pixel count exceeds
# ``Image.MAX_IMAGE_PIXELS`` to avoid potential decompression bomb DoS attacks.
# This project intentionally works with very large satellite images, so we
# disable that safety limit here. If you prefer to set a very large cap
# instead of disabling, assign an integer value to Image.MAX_IMAGE_PIXELS.
# Set to None to disable the check.
Image.MAX_IMAGE_PIXELS = None


def slice_image(input_path, output_dir, chunk_size=1024):
    """
    Slice a large image into smaller chunks.

    Args:
        input_path (str): Path to the input image file
        output_dir (str): Directory where chunks will be saved
        chunk_size (int): Size of each chunk (default: 1024x1024)
    """

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Open the source image
    print(f"Opening image: {input_path}")
    try:
        img = Image.open(input_path)
    except Exception as e:
        print(f"Error opening image: {e}")
        return

    # Get image dimensions
    width, height = img.size
    print(f"Image dimensions: {width} x {height} pixels")

    # Calculate number of chunks needed
    cols = math.ceil(width / chunk_size)
    rows = math.ceil(height / chunk_size)

    print(f"Will create {rows} rows and {cols} columns of chunks")
    print(f"Total chunks: {rows * cols}")

    chunk_count = 0

    # Slice the image
    for row in range(rows):
        for col in range(cols):
            # Calculate the boundaries of this chunk
            left = col * chunk_size
            top = row * chunk_size
            right = min(left + chunk_size, width)
            bottom = min(top + chunk_size, height)

            # Crop the chunk
            chunk = img.crop((left, top, right, bottom))

            # If the chunk is smaller than chunk_size (edge pieces),
            # pad it with a transparent background
            if chunk.size != (chunk_size, chunk_size):
                # Create a new image with the desired size
                padded_chunk = Image.new('RGBA', (chunk_size, chunk_size), (0, 0, 0, 0))
                # Paste the cropped chunk onto the padded image
                padded_chunk.paste(chunk, (0, 0))
                chunk = padded_chunk

            # Create output filename
            filename = f"{row}_{col}.png"
            output_path = os.path.join(output_dir, filename)

            # Save the chunk
            chunk.save(output_path, 'PNG')
            chunk_count += 1

            # Progress indicator
            if chunk_count % 10 == 0:
                print(f"Processed {chunk_count}/{rows * cols} chunks...")

    print(f"\nCompleted! Created {chunk_count} image chunks in {output_dir}")


def main():
    """Main function to run the image slicer."""

    # Define paths relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))

    input_image = os.path.join(project_root, 'source', 'images', 'gtt_satmap.bmp')
    output_directory = os.path.join(project_root, 'output')

    print("=== Image Slicer ===")
    print(f"Input image: {input_image}")
    print(f"Output directory: {output_directory}")
    print(f"Chunk size: 1024x1024 pixels")
    print()

    # Check if input file exists
    if not os.path.exists(input_image):
        print(f"Error: Input image not found at {input_image}")
        print("Please ensure the image file exists in the source/images folder.")
        return

    # Start slicing
    slice_image(input_image, output_directory, chunk_size=1024)


if __name__ == "__main__":
    main()