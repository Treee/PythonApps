"""
Resize vinyl cover images for DayZ PAA conversion.

For images in the input folder (e.g., Z:\\DayZ\\SourceImages\\gear\\camping\\vinyls\\collection):
  1) Resize image to width=1024 while maintaining aspect ratio (typical height ~504 for common sources).
  2) Pad canvas to exactly 1024x512 with the content anchored at the bottom-left, leaving a transparent strip at the top.

Outputs PNG files to the specified output folder (default: <input>_1024x512).

Notes:
- If an image would exceed 512px height after step 1 (rare for this use-case), the script will instead scale the image to fit within 1024x512 while preserving aspect ratio, still anchored bottom-left.
- Supported input formats: PNG, JPG, JPEG, WEBP, TGA, BMP.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps
import shutil


SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".tga", ".bmp"}


def compute_resize_to_width(original_w: int, original_h: int, target_w: int) -> tuple[int, int]:
    """Return new size keeping aspect ratio when constraining by width.

    Rounds height to nearest integer.
    """
    if original_w <= 0 or original_h <= 0:
        raise ValueError("Invalid source dimensions")
    scale = target_w / float(original_w)
    new_h = max(1, round(original_h * scale))
    return target_w, new_h


def compute_fit_within(original_w: int, original_h: int, max_w: int, max_h: int) -> tuple[int, int]:
    """Return new size that fits within the given bounds preserving aspect ratio."""
    if original_w <= 0 or original_h <= 0:
        raise ValueError("Invalid source dimensions")
    scale = min(max_w / float(original_w), max_h / float(original_h))
    new_w = max(1, int(round(original_w * scale)))
    new_h = max(1, int(round(original_h * scale)))
    return new_w, new_h


def process_image(src_path: Path, dst_path: Path, *, target_w: int = 1024, target_h: int = 512, dry_run: bool = False) -> tuple[bool, str]:
    """Resize and pad a single image.

    - Resize to width=target_w (keeping aspect ratio)
    - If height would exceed target_h, fit within target_w x target_h
    - Paste onto transparent RGBA canvas of (target_w, target_h) anchored bottom-left
    - Save as PNG

    Returns (ok, message).
    """
    try:
        with Image.open(src_path) as im:
            im = ImageOps.exif_transpose(im)
            ow, oh = im.size

            # First attempt: force width to target_w
            new_w, new_h = compute_resize_to_width(ow, oh, target_w)

            # If that height is too tall, fit within the bounding box instead
            if new_h > target_h:
                new_w, new_h = compute_fit_within(ow, oh, target_w, target_h)

            if dry_run:
                return True, f"{src_path.name}: {ow}x{oh} -> resized {new_w}x{new_h} -> canvas {target_w}x{target_h}"

            # Resize using high-quality resampling
            im_resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # Ensure we have an alpha channel for proper compositing
            if im_resized.mode not in ("RGBA", "LA"):
                im_resized = im_resized.convert("RGBA")
            else:
                # Normalize to RGBA
                im_resized = im_resized.convert("RGBA")

            # Create transparent canvas and paste at bottom-left (x=0, y=target_h-new_h)
            canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
            paste_y = target_h - new_h
            canvas.paste(im_resized, (0, paste_y), im_resized)

            # Ensure destination directory exists
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            # Save as PNG (lossless, with alpha)
            canvas.save(dst_path, format="PNG", optimize=True)

            return True, f"Saved: {dst_path.name} ({new_w}x{new_h} on {target_w}x{target_h})"
    except Exception as e:
        return False, f"ERROR processing {src_path.name}: {e}"


def find_images(input_dir: Path) -> list[Path]:
    files: list[Path] = []
    for p in sorted(input_dir.rglob("*")):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
            files.append(p)
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resize and pad vinyl cover images to 1024x512 (bottom-left aligned)")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(r"Z:\\DayZ\\SourceImages\\gear\\camping\\vinyls\\collection"),
        help="Input folder containing source images",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output folder for processed images (default: sibling 'output' folder next to the input folder)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clear existing converted images in the output folder before processing",
    )
    parser.add_argument("--width", type=int, default=1024, help="Target canvas width (default: 1024)")
    parser.add_argument("--height", type=int, default=512, help="Target canvas height (default: 512)")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files; just print planned operations")

    args = parser.parse_args(argv)

    input_dir: Path = args.input
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Input directory does not exist: {input_dir}", file=sys.stderr)
        return 2

    # Default output: a 'output' folder adjacent to the input folder
    default_output = input_dir.parent / "output"
    output_dir: Path = args.output or default_output
    target_w, target_h = int(args.width), int(args.height)

    items = find_images(input_dir)
    if not items:
        print(f"No images found in {input_dir}")
        return 0

    processed = 0
    failed = 0

    print(f"Found {len(items)} image(s). Processing to canvas {target_w}x{target_h} (bottom-left anchor)...")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Optionally clean previous outputs (only files matching our naming convention)
    if args.clean:
        removed = 0
        for p in output_dir.glob("iat_vinyl_*_co.png"):
            try:
                p.unlink()
                removed += 1
            except Exception:
                pass
        print(f"Cleaned {removed} existing file(s) in {output_dir}")
    if args.dry_run:
        print("Running in dry-run mode. No files will be written.")

    for src in items:
        # Apply naming convention and place directly in the output folder
        safe_stem = src.stem.replace('-', '_')
        new_name = f"iat_vinyl_{safe_stem}_co.png"
        dst = output_dir / new_name
        ok, msg = process_image(src, dst, target_w=target_w, target_h=target_h, dry_run=args.dry_run)
        print(msg)
        if ok:
            processed += 1
        else:
            failed += 1

    print(f"Done. Processed: {processed}, Failed: {failed}, Output: {output_dir}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
