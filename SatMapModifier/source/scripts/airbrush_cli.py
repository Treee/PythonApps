#!/usr/bin/env python3
"""
Simple CLI wrapper for the auto_airbrush module.

Usage:
    python airbrush_cli.py --single 7_7.png --debug
    python airbrush_cli.py --all

This script lives in `source/scripts` and imports `auto_airbrush` from the
same folder so it can reuse `process_image_file` and `main()`.
"""
import os
import sys
import argparse

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

import auto_airbrush as ab


def run_single(filename: str, debug: bool = False):
    # script is in SatMapModifier/source/scripts; project root is three levels up
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    input_dir = os.path.join(repo_root, 'output')
    in_path = os.path.join(input_dir, filename)
    out_dir = input_dir  # write outputs next to the original tiles
    out_path = os.path.join(out_dir, filename)
    os.makedirs(out_dir, exist_ok=True)

    if not os.path.isfile(in_path):
        print(f"Input file not found: {in_path}")
        return 2

    print(f"Processing single file: {in_path}")
    ok = ab.process_image_file(in_path, output_dir=out_dir, save_debug=debug)
    print("Done." if ok else "Failed.")
    return 0 if ok else 1


def run_all():
    print("Processing all images in output/ ...")
    ab.main()
    return 0


def parse_args():
    p = argparse.ArgumentParser(description='Run auto-airbrush on output tiles')
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--single', '-s', help='Process a single tile filename (e.g. 7_7.png)')
    group.add_argument('--all', '-a', action='store_true', help='Process all tiles in output/')
    p.add_argument('--debug', '-d', action='store_true', help='Save debug images (mask/inpainted)')
    return p.parse_args()


def main():
    args = parse_args()
    if args.single:
        return run_single(args.single, debug=args.debug)
    if args.all:
        return run_all()
    return 0


if __name__ == '__main__':
    sys.exit(main())
