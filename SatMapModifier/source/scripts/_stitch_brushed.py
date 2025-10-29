#!/usr/bin/env python3
"""
Stitch brushed (tiled) images back into a single bitmap.

Usage:
  python _stitch_brushed.py [--input-dir PATH] [--output-name NAME] [--recursive]

This script looks for image files in the input directory, extracts integer
coordinates from filenames when possible, and pastes tiles into a single
stitched image saved into the same output directory (default name starts
with an underscore so it sorts to the top: `_stitched_brushed.bmp`).

It attempts to be forgiving with tile filename formats. If it cannot find
coordinate pairs in filenames, it falls back to arranging tiles in a
rectangular grid (if count matches a rectangular factorization).
"""
from __future__ import annotations

import argparse
import math
import os
import re
import sys
from glob import glob
from typing import Dict, List, Optional, Tuple

try:
    from PIL import Image
except Exception as e:  # pragma: no cover - friendly import error message
    print("Pillow is required. Install with: pip install Pillow")
    raise


IMAGE_GLOBS = ("*.png", "*.jpg", "*.jpeg", "*.tif", "*.tiff", "*.bmp")


def find_images(input_dir: str, recursive: bool) -> List[str]:
    files = []
    if recursive:
        for root, _, _ in os.walk(input_dir):
            for g in IMAGE_GLOBS:
                files.extend(glob(os.path.join(root, g)))
    else:
        for g in IMAGE_GLOBS:
            files.extend(glob(os.path.join(input_dir, g)))

    # Filter to only include images whose filename (without extension)
    # ends with the `_brushed` suffix — this keeps unrelated images out.
    def is_brushed(path: str) -> bool:
        base = os.path.splitext(os.path.basename(path))[0]
        return base.endswith('_brushed')

    files = [f for f in files if is_brushed(f)]
    return sorted(files)


def parse_coords_from_name(name: str) -> Optional[Tuple[int, int]]:
    """Try to extract two integers from the filename. Returns (row,col) or None.

    Strategy: find all integer substrings; if there are two or more, take the
    last two as (row, col). The project naming uses row then col (e.g.
    `tile_3_5_brushed.png` means row=3, col=5). If only one integer or none,
    return None.
    """
    base = os.path.splitext(os.path.basename(name))[0]
    nums = re.findall(r"-?\d+", base)
    if len(nums) >= 2:
        # Use the last two numbers as coordinates (row, col)
        row = int(nums[-2])
        col = int(nums[-1])
        return row, col
    return None


def arrange_by_coords(files: List[str]) -> Optional[Tuple[Dict[Tuple[int, int], str], int, int, int, int]]:
    mapping: Dict[Tuple[int, int], str] = {}
    xs = set()
    ys = set()
    for f in files:
        coords = parse_coords_from_name(f)
        if coords is None:
            return None
        # parse_coords returns (row, col) per project convention; map to (x=col, y=row)
        row, col = coords
        mapping[(col, row)] = f
        xs.add(col)
        ys.add(row)
    if not mapping:
        return None
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    return mapping, min_x, min_y, max_x, max_y


def fallback_grid(files: List[str]) -> Tuple[Dict[Tuple[int, int], str], int, int, int, int]:
    # Arrange by filename order into a grid. Try to find factorization (rows x cols)
    n = len(files)
    # Try to find a rectangular shape where cols >= rows and cols-rows minimal
    best = None
    for rows in range(1, int(math.sqrt(n)) + 2):
        if n % rows == 0:
            cols = n // rows
            best = (rows, cols)
    if best is None:
        # fallback: use square-ish grid
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)
    else:
        rows, cols = best

    mapping: Dict[Tuple[int, int], str] = {}
    idx = 0
    for r in range(rows):
        for c in range(cols):
            if idx >= n:
                break
            mapping[(c, r)] = files[idx]
            idx += 1
    min_x, min_y = 0, 0
    max_x, max_y = cols - 1, rows - 1
    return mapping, min_x, min_y, max_x, max_y


def stitch(mapping: Dict[Tuple[int, int], str], min_x: int, min_y: int, max_x: int, max_y: int, out_path: str, fill_color=(0, 0, 0, 0), tile_size: Optional[int] = None) -> None:
    # Determine tile size: if tile_size is provided, use it; otherwise inspect first tile.
    if tile_size is not None:
        tile_w = tile_h = int(tile_size)
    else:
        first_tile_path = next(iter(mapping.values()))
        with Image.open(first_tile_path) as im:
            tile_w, tile_h = im.size

    cols = max_x - min_x + 1
    rows = max_y - min_y + 1
    total_w = cols * tile_w
    total_h = rows * tile_h

    # Choose mode: use RGBA only when a 4-tuple (with alpha) is provided,
    # otherwise use RGB which is safe for BMP output.
    mode = 'RGBA' if isinstance(fill_color, tuple) and len(fill_color) == 4 else 'RGB'
    stitched = Image.new(mode, (total_w, total_h), color=fill_color)

    for (x, y), path in mapping.items():
        try:
            with Image.open(path) as tile:
                tile = tile.convert(mode)
                px = (x - min_x) * tile_w
                py = (y - min_y) * tile_h
                stitched.paste(tile, (px, py))
        except Exception:
            print(f"Warning: failed to open/paste {path}")

    # If saving as BMP, ensure the image is RGB (BMP commonly uses 24-bit RGB).
    if out_path.lower().endswith('.bmp') and stitched.mode != 'RGB':
        stitched = stitched.convert('RGB')

    stitched.save(out_path)
    print(f"Saved stitched image to: {out_path}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Stitch brushed tiles into one image")
    default_input = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'output'))
    parser.add_argument('--input-dir', '-i', default=default_input, help='Directory with tiles (default: SatMapModifier/output)')
    parser.add_argument('--output-name', '-o', default='_stitched_brushed.bmp', help='Output filename (created inside input dir). Defaults to start with underscore and will be saved as BMP.')
    parser.add_argument('--recursive', '-r', action='store_true', help='Search for images recursively inside input dir')
    parser.add_argument('--tile-size', '-t', type=int, default=1024, help='Tile size in pixels (tiles are square). Default: 1024')
    parser.add_argument('--background', '-b', default=None, help='Background/fill color (e.g. "#000000" or "255,255,255")')
    args = parser.parse_args(argv)

    input_dir = os.path.abspath(args.input_dir)
    if not os.path.isdir(input_dir):
        print(f"Input directory does not exist: {input_dir}")
        return 2

    files = find_images(input_dir, args.recursive)
    if not files:
        print(f"No image files found in: {input_dir}")
        return 3

    arranged = arrange_by_coords(files)
    if arranged is None:
        print("Could not parse coordinates from filenames, falling back to grid arrangement by filename order.")
        mapping, min_x, min_y, max_x, max_y = fallback_grid(files)
    else:
        mapping, min_x, min_y, max_x, max_y = arranged

    out_path = os.path.join(input_dir, args.output_name)

    bg = None
    if args.background:
        s = args.background.strip()
        if s.startswith('#'):
            s = s[1:]
        if ',' in s:
            parts = [int(p) for p in s.split(',')]
            bg = tuple(parts)
        else:
            # hex
            if len(s) in (6, 8):
                r = int(s[0:2], 16)
                g = int(s[2:4], 16)
                b = int(s[4:6], 16)
                if len(s) == 8:
                    a = int(s[6:8], 16)
                    bg = (r, g, b, a)
                else:
                    bg = (r, g, b)

    if bg is None:
        bg = (0, 0, 0, 0)

    stitch(mapping, min_x, min_y, max_x, max_y, out_path, fill_color=bg, tile_size=args.tile_size)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
