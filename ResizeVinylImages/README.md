# Resize Vinyl Images for DayZ

This tool resizes vinyl cover images to a DayZ-friendly canvas for PAA conversion.

What it does:

-   Resizes input images to width 1024 while keeping aspect ratio (typical height ends up ~504).
-   Pads the image to a 1024x512 transparent canvas with the content anchored at the bottom-left (transparent strip at the top).
-   Saves PNG outputs (lossless with alpha), preserving the folder structure under the output directory.

Default input folder:

-   `Z:\\DayZ\\SourceImages\\gear\\camping\\vinyls\\collection`

## Install

Install dependencies (Pillow):

```powershell
pip install -r .\ResizeVinylImages\requirements.txt
```

## Run

Quick start (uses default input and 1024x512 canvas):

```powershell
.\ResizeVinylImages\scripts\run_resize_collection.bat
```

Or run the Python script directly and customize options:

```powershell
python .\ResizeVinylImages\scripts\resize_vinyl_collection.py --input "Z:\\DayZ\\SourceImages\\gear\\camping\\vinyls\\collection" --width 1024 --height 512
```

Dry-run to preview planned operations without writing files:

```powershell
python .\ResizeVinylImages\scripts\resize_vinyl_collection.py --dry-run
```

Output folder defaults to a `collections` folder next to your input folder. You can supply `--output` to override.

To clear previous conversion outputs before regenerating, use `--clean`:

```powershell
python .\ResizeVinylImages\scripts\resize_vinyl_collection.py --clean
```

Output file naming convention:

    -   Collection processing saves each file as `iat_vinyl_{originalfilename}_co.png` in the mirrored folder structure under the output directory.
    -   Single-image processing (without --output) saves next to the source as `iat_vinyl_{originalfilename}_co.png`.
    -   Note: Any '-' characters in the original filename are converted to '_' in the output filename.

### Run on a single image (for testing)

Using the batch helper (saves into a `collections` folder next to the image's folder by default):

```powershell
.\ResizeVinylImages\scripts\run_resize_single.bat "Z:\\DayZ\\SourceImages\\gear\\camping\\vinyls\\collection\\example.jpg"
```

Optionally specify an explicit output path:

```powershell
.\ResizeVinylImages\scripts\run_resize_single.bat "Z:\\DayZ\\SourceImages\\gear\\camping\\vinyls\\collection\\example.jpg" "Z:\\DayZ\\SourceImages\\gear\\camping\\vinyls\\collection\\example_1024x512.png"
```

Or run the Python script directly:

```powershell
python .\ResizeVinylImages\scripts\resize_single_vinyl.py --input "Z:\\DayZ\\SourceImages\\gear\\camping\\vinyls\\collection\\example.jpg"
```

## Notes

-   If resizing to width 1024 would make the height exceed 512, the script automatically scales to fit within 1024x512 while preserving aspect ratio, still anchored bottom-left.
-   Supported input formats: PNG, JPG, JPEG, WEBP, TGA, BMP.
