"""
Resize one vinyl cover image to a DayZ-friendly canvas.

Steps:
  1) Resize to width=1024 while maintaining aspect ratio.
  2) If resulting height > 512, instead fit within 1024x512.
  3) Pad to a 1024x512 transparent canvas, anchoring the content at the bottom-left.

Saves PNG output. Useful for testing on a single image.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps


def compute_resize_to_width(original_w: int, original_h: int, target_w: int) -> tuple[int, int]:
    if original_w <= 0 or original_h <= 0:
        raise ValueError("Invalid source dimensions")
    scale = target_w / float(original_w)
    new_h = max(1, round(original_h * scale))
    return target_w, new_h


def compute_fit_within(original_w: int, original_h: int, max_w: int, max_h: int) -> tuple[int, int]:
    if original_w <= 0 or original_h <= 0:
        raise ValueError("Invalid source dimensions")
    scale = min(max_w / float(original_w), max_h / float(original_h))
    new_w = max(1, int(round(original_w * scale)))
    new_h = max(1, int(round(original_h * scale)))
    return new_w, new_h


def process_one(src_path: Path, dst_path: Path, *, target_w: int = 1024, target_h: int = 512, dry_run: bool = False) -> tuple[bool, str]:
    try:
        with Image.open(src_path) as im:
            im = ImageOps.exif_transpose(im)
            ow, oh = im.size

            new_w, new_h = compute_resize_to_width(ow, oh, target_w)
            if new_h > target_h:
                new_w, new_h = compute_fit_within(ow, oh, target_w, target_h)

            if dry_run:
                return True, f"{src_path.name}: {ow}x{oh} -> resized {new_w}x{new_h} -> canvas {target_w}x{target_h}"

            im_resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
            if im_resized.mode not in ("RGBA", "LA"):
                im_resized = im_resized.convert("RGBA")
            else:
                im_resized = im_resized.convert("RGBA")

            canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
            paste_y = target_h - new_h
            canvas.paste(im_resized, (0, paste_y), im_resized)

            dst_path.parent.mkdir(parents=True, exist_ok=True)
            canvas.save(dst_path, format="PNG", optimize=True)

            return True, f"Saved: {dst_path}"
    except Exception as e:
        return False, f"ERROR: {e}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resize a single vinyl image to 1024x512 (bottom-left anchored)")
    parser.add_argument("--input", "-i", type=Path, required=True, help="Path to source image")
    parser.add_argument("--output", "-o", type=Path, default=None, help="Path to save output PNG (default: alongside source with _1024x512 suffix)")
    parser.add_argument("--width", type=int, default=1024, help="Target canvas width (default: 1024)")
    parser.add_argument("--height", type=int, default=512, help="Target canvas height (default: 512)")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files; just print planned operations")

    args = parser.parse_args(argv)

    src: Path = args.input
    if not src.exists() or not src.is_file():
        print(f"Input file not found: {src}", file=sys.stderr)
        return 2

    if args.output is None:
        # Apply naming convention: iat_vinyl_{originalfilename}_co.png next to the source
        # Replace '-' with '_' in the original filename stem
        safe_stem = src.stem.replace('-', '_')
        dst = src.with_name(f"iat_vinyl_{safe_stem}_co.png")
    else:
        dst = args.output

    ok, msg = process_one(src, dst, target_w=args.width, target_h=args.height, dry_run=args.dry_run)
    print(msg)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
