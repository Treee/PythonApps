# SatMapModifier

A Python utility for slicing large bitmap images into smaller, manageable chunks for easier processing.

## Overview

This project contains a Python script that takes a large bitmap image and splits it into 1024x1024 pixel chunks. This is useful for processing very large satellite maps or other high-resolution images that might be too large to process as a whole.

## Features

-   Slices large images into 1024x1024 pixel chunks
-   Handles edge cases by padding smaller edge pieces
-   Outputs chunks as PNG files with clear naming convention (`row_col.png`)
-   Progress tracking during processing
-   Automatic output directory creation

## Structure

```
SatMapModifier/
├── source/
│   ├── images/
│   │   └── gtt_satmap.bmp          # Your large source image
│   └── scripts/
│       └── image_slicer.py         # Main slicing script
├── output/                         # Generated chunks go here
├── requirements.txt                # Python dependencies
├── run_image_slicer.bat           # Windows batch script for easy execution
└── README.md                      # This file
```

## Installation

1. Make sure you have Python 3.6+ installed
2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Method 1: Using the batch script (Windows)

Simply double-click `run_image_slicer.bat` or run it from command prompt.

### Method 2: Running Python directly

```bash
cd source/scripts
python image_slicer.py
```

## Output

The script will create PNG files in the `output/` directory with the naming convention:

-   `0_0.png` (top-left chunk)
-   `0_1.png` (top row, second column)
-   `1_0.png` (second row, first column)
-   etc.

Each chunk will be exactly 1024x1024 pixels. Edge pieces that are smaller than 1024x1024 will be padded with transparent pixels.

## Requirements

-   Python 3.6+
-   Pillow (PIL) library

## Notes

-   The script automatically detects the size of your input image and calculates how many chunks are needed
-   Progress is displayed every 10 chunks processed
-   All chunks are saved as PNG format for better compatibility and smaller file sizes
-   The script handles very large images efficiently by processing one chunk at a time
