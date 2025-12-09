import argparse
import fnmatch
import os
import glob
import sys
from pathlib import Path
from shutil import copy2

try:
    import yaml  # type: ignore
    YAML_AVAILABLE = True
except Exception:
    YAML_AVAILABLE = False


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    if config_path.suffix.lower() not in {".yml", ".yaml"}:
        raise ValueError("Config must be a YAML file (.yml/.yaml).")
    if not YAML_AVAILABLE:
        raise RuntimeError("PyYAML is required for YAML configs. Install with 'pip install pyyaml'.")
    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict) or "mappings" not in data:
        raise ValueError("Config must be an object with a 'mappings' array.")
    # No global source_root requirement; each mapping may specify its own 'source',
    # or use full-path glob patterns that include directories.
    return data


def ensure_p_drive() -> Path:
    p_drive = Path("P:/dz")
    if not p_drive.exists():
        raise RuntimeError("Destination root 'P:/dz' not found. Ensure the P: drive is mounted (DayZ Tools).")
    return p_drive


def find_matches(src_dir: Path, pattern: str) -> list[Path]:
    # If pattern looks like a full path glob (contains separator or drive), use glob directly
    looks_like_path_glob = (os.sep in pattern) or ("/" in pattern) or (":" in pattern)
    if looks_like_path_glob:
        paths = [Path(p) for p in glob.glob(pattern)]
        return [p for p in paths if p.suffix.lower() == ".p3d" and p.exists()]
    # Otherwise, search recursively and match filenames
    results: list[Path] = []
    for root, _dirs, files in os.walk(src_dir):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                p = Path(root) / name
                if p.suffix.lower() == ".p3d":
                    results.append(p)
    return results


def copy_files(matches: list[Path], dest_root: Path, dest_subfolder: str, dry_run: bool, verbose: bool) -> int:
    count = 0
    # Allow absolute destination paths (e.g., P:/DZ/structures/...)
    dest_dir = Path(dest_subfolder) if ":" in dest_subfolder else (dest_root / dest_subfolder)
    if verbose:
        print(f"Destination folder: {dest_dir}")
    # Do NOT create destination directories; skip if missing
    if not dest_dir.exists():
        if verbose:
            print(f"Skip: destination does not exist -> {dest_dir}")
        return 0
    for src in matches:
        target = dest_dir / src.name
        if verbose:
            print(f"Copy: {src} -> {target}")
        if not dry_run:
            copy2(src, target)
        count += 1
    return count


def run(config_path: Path, dry_run: bool = False, verbose: bool = False) -> int:
    dest_root = ensure_p_drive()
    config = load_config(config_path)
    # Global source directories are optional; default to empty and rely on per-mapping 'source' or full-path patterns
    src_dirs: list[Path] = []
    if "source_roots" in config:
        for r in config["source_roots"]:
            p = Path(r)
            if not p.exists():
                raise FileNotFoundError(f"Source root not found: {p}")
            src_dirs.append(p)
    elif "source_root" in config and config.get("source_root"):
        p = Path(config["source_root"])  # optional
        if not p.exists():
            raise FileNotFoundError(f"Source root not found: {p}")
        src_dirs.append(p)
    total = 0
    mappings = config.get("mappings", [])
    if not isinstance(mappings, list) or not mappings:
        raise ValueError("Config 'mappings' must be a non-empty array.")
    for m in mappings:
        pattern = m.get("pattern")
        destination = m.get("destination")
        if not pattern or not destination:
            raise ValueError("Each mapping requires 'pattern' and 'destination'.")
        # If a mapping specifies its own source directory, use it (1:1 mapping support)
        mapping_sources: list[Path]
        if "source" in m and m["source"]:
            p = Path(m["source"])
            if not p.exists():
                raise FileNotFoundError(f"Mapping source not found: {p}")
            mapping_sources = [p]
        else:
            mapping_sources = src_dirs
        # Gather matches across the selected source directories when using filename patterns.
        # If the pattern is a full path glob, find_matches will ignore src_dir.
        matches: list[Path] = []
        for sdir in mapping_sources:
            matches.extend(find_matches(sdir, pattern))
        if verbose:
            print(f"Pattern '{pattern}' matched {len(matches)} files.")
        total += copy_files(matches, dest_root, destination, dry_run, verbose)
    if verbose:
        print(f"Total files {'to copy' if dry_run else 'copied'}: {total}")
    return total


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Copy road part .p3d files into P:/dz destinations using a YAML config.")
    p.add_argument("config", type=Path, help="YAML config defining source_root and pattern-to-destination mappings")
    p.add_argument("--dry-run", action="store_true", help="Show what would be copied without making changes")
    p.add_argument("--verbose", action="store_true", help="Print matched files and operations")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        return 0 if run(args.config, args.dry_run, args.verbose) >= 0 else 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
