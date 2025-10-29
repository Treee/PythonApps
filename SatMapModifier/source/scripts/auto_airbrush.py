#!/usr/bin/env python3
"""
Auto Airbrush - Attempts to replace man-made gray/white areas with natural green/grass

This script scans all PNG images in the repository `output/` directory, detects
likely man-made light/gray regions (houses, roads, parking lots) and tries to
replace them so the tiles look more natural (grass/trees).

Approach (conservative/simple):
- Build a mask of gray/white pixels using RGB and HSV heuristics (low saturation,
  relatively high value / brightness, and channels close to each other).
- Smooth the mask with morphological ops to reduce noise.
- Use OpenCV inpainting (Telea) to fill the masked regions using nearby textures.
  Inpainting will borrow surrounding pixels (if nearby grass exists, great).
- Optionally blend the inpainted region towards a green tint to encourage a
  greener result.

This is a heuristic tool — results will vary depending on how much surrounding
natural texture exists. It is intended as a quick batch touch-up.

Requirements:
- opencv-python
- numpy
- Pillow (for optional extra saving/loading)

Usage:
    python auto_airbrush.py

Outputs are written to `output/airbrushed/` with the same filenames.
"""

import os
import cv2
import numpy as np
from PIL import Image


# Configuration (tweak these thresholds for your data)
SAT_THRESHOLD = 40          # HSV saturation below this is considered low (0-255)
VAL_THRESHOLD = 120         # HSV value (brightness) above this suggests light pixels
RGB_DIFF_THRESHOLD = 20     # Max difference between RGB channels to consider 'grayish'
MORPH_KERNEL = 3            # Morphological kernel size
DILATE_ITER = 2             # Expand mask slightly so we cover edges
GREEN_TINT = (60, 160, 60)  # BGR green tint used for blending if needed
BLEND_ALPHA = 0.55          # How strongly to pull towards green tint (0..1)
INPAINT_RADIUS = 3         # Radius for inpainting


def is_grayish_mask_bgr(img_bgr):
    """Return a binary mask of gray/white-ish pixels using BGR/RGB + HSV heuristics."""
    # img_bgr: numpy array BGR uint8
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    # Condition 1: low saturation and fairly bright
    cond1 = (s <= SAT_THRESHOLD) & (v >= VAL_THRESHOLD)

    # Condition 2: RGB channels close to each other -> neutral/gray
    b, g, r = cv2.split(img_bgr)
    bg_diff = cv2.absdiff(b, g)
    br_diff = cv2.absdiff(b, r)
    gr_diff = cv2.absdiff(g, r)
    cond2 = (bg_diff <= RGB_DIFF_THRESHOLD) & (br_diff <= RGB_DIFF_THRESHOLD) & (gr_diff <= RGB_DIFF_THRESHOLD)

    mask = (cond1 & cond2).astype(np.uint8) * 255
    return mask


def refine_mask(mask):
    """Apply morphological ops to clean up mask."""
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (MORPH_KERNEL, MORPH_KERNEL))
    # Close small holes then remove small noise
    closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel, iterations=1)
    # Dilate a bit to cover edges of man-made objects
    dilated = cv2.dilate(opened, kernel, iterations=DILATE_ITER)
    return dilated


def compute_mean_green(img_bgr, green_mask):
    """Compute mean BGR color from green-like pixels, fallback to global mean if none."""
    # Identify green-like pixels using HSV
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    # Hue range for green roughly 35..85 (in degrees mapped to 0..179 scale)
    green_h_min = int(35 / 2)
    green_h_max = int(85 / 2)
    green_h_mask = (h >= green_h_min) & (h <= green_h_max) & (s >= 80) & (v >= 60)

    # Combine with optional external mask to focus sampling area
    if green_mask is not None:
        combined = green_h_mask & (green_mask > 0)
    else:
        combined = green_h_mask

    if combined.any():
        mean_b = int(np.mean(img_bgr[:, :, 0][combined]))
        mean_g = int(np.mean(img_bgr[:, :, 1][combined]))
        mean_r = int(np.mean(img_bgr[:, :, 2][combined]))
        return (mean_b, mean_g, mean_r)

    # fallback: sample overall image but prefer greener pixels by weighting
    mean_b = int(np.mean(img_bgr[:, :, 0]))
    mean_g = int(np.mean(img_bgr[:, :, 1]))
    mean_r = int(np.mean(img_bgr[:, :, 2]))
    return (mean_b, mean_g, mean_r)


def process_image_file(input_path, output_dir=None, save_debug=False):
    """Process a single image: detect man-made areas and try to replace them.

    Outputs are written into `output_dir` (if provided) or into the same
    folder as the input image. The final image will be saved with the
    suffix "_brushed.png" and the mask with "_mask.png" so they stay
    grouped with the original tile.
    """
    # Read image as BGR
    img = cv2.imread(input_path, cv2.IMREAD_COLOR)
    if img is None:
        print(f"Failed to read {input_path}")
        return False

    if output_dir is None:
        output_dir = os.path.dirname(input_path)

    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    out_brushed = os.path.join(output_dir, f"{base_name}_brushed.png")
    out_mask = os.path.join(output_dir, f"{base_name}_mask.png")
    out_inpainted = os.path.join(output_dir, f"{base_name}_inpainted.png")

    orig = img.copy()

    # Build mask of gray/white regions
    mask = is_grayish_mask_bgr(img)
    mask = refine_mask(mask)

    # If nothing found, just copy (save as _brushed to keep naming consistent)
    if cv2.countNonZero(mask) == 0:
        print(f"No gray/white areas detected in {os.path.basename(input_path)}; copying")
        cv2.imwrite(out_brushed, img)
        # still save an empty mask for inspection
        cv2.imwrite(out_mask, mask)
        return True

    # Inpaint the original image using the mask - this borrows nearby texture
    inpainted = cv2.inpaint(img, mask, INPAINT_RADIUS, cv2.INPAINT_TELEA)

    # Compute a mean green color from the image (prefer existing greens)
    mean_green = compute_mean_green(orig, None)

    # Blend the inpainted result towards a green tint over masked regions
    green_arr = np.array(mean_green, dtype=np.uint8)

    # Make a copy that we'll modify
    blended = inpainted.copy()

    # Create green image
    green_img = np.zeros_like(inpainted, dtype=np.uint8)
    green_img[:, :] = green_arr

    # Where mask==255, blend: result = alpha*green + (1-alpha)*inpainted
    alpha = BLEND_ALPHA
    mask_bool = mask.astype(bool)
    blended[mask_bool] = (alpha * green_img[mask_bool] + (1 - alpha) * inpainted[mask_bool]).astype(np.uint8)

    # Optionally smooth the boundary a bit
    blended = cv2.GaussianBlur(blended, (3, 3), 0)

    # Save result and mask next to original tile
    cv2.imwrite(out_brushed, blended)
    cv2.imwrite(out_mask, mask)

    if save_debug:
        # Save intermediate debug images next to output
        cv2.imwrite(out_inpainted, inpainted)

    return True


def main():
    # script is in SatMapModifier/source/scripts; project root is three levels up
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    input_dir = os.path.join(repo_root, 'output')
    # We now write results next to the original tiles in `output/` so files
    # are grouped together. The function `process_image_file` appends
    # "_brushed" and "_mask" to generated filenames.
    output_dir = input_dir

    if not os.path.isdir(input_dir):
        print(f"Input directory not found: {input_dir}")
        return

    os.makedirs(output_dir, exist_ok=True)

    # Process common image types
    exts = ('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')

    files = [f for f in os.listdir(input_dir) if f.lower().endswith(exts) and os.path.isfile(os.path.join(input_dir, f))]
    if not files:
        print(f"No image files found in {input_dir}")
        return

    print(f"Processing {len(files)} files from {input_dir} -> {output_dir}")
    for fname in files:
        in_path = os.path.join(input_dir, fname)
        print(f"Processing {fname}...")
        try:
            ok = process_image_file(in_path, output_dir=output_dir, save_debug=False)
            if not ok:
                print(f"Failed: {fname}")
        except Exception as e:
            print(f"Error processing {fname}: {e}")

    print("Done.")


if __name__ == '__main__':
    main()
