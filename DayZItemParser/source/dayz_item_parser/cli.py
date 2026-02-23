from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from dayz_item_parser.cpp_config_parser import extract_scope2_cfg_children
from dayz_item_parser.scanner import ConfigCppMatch, iter_config_cpp_files


def _remap_category(group: str, category: str, class_name: str) -> str:
    if not isinstance(class_name, str):
        return category

    lowered = class_name.lower()

    if group == "weapons":
        # Split ammunition into two JSON outputs based on name prefix.
        if category == "ammunition":
            if lowered.startswith("ammobox_"):
                return "ammobox"
            # Default to ammo bucket for Ammo_* and any other stray entries.
            return "ammo"

        # Split attachments into more specific buckets.
        # Note: Some optics/magazines can be defined in firearm config folders, so this mapping
        # is based on class name patterns rather than source folder.
        if lowered.startswith("mag_"):
            return "magazines"
        if "suppress" in lowered:
            return "suppressors"
        if "optic" in lowered:
            return "optics"
        if "ghillie" in lowered:
            return "ghillie_attachment"
        if "handguard" in lowered:
            return "handguard"
        if "stock" in lowered or "bttstck" in lowered:
            return "buttstock"

        return category

    if group == "gear" and category == "food":
        # Split food into focused buckets.
        # - Canned food class names end with "Can" (avoid matching Candycane by using suffix).
        # - Meat (including fish fillets, animal cuts) ends with "Meat".
        # - Mushrooms contain "Mushroom".
        if lowered.endswith("can"):
            return "food_canned"
        if lowered.endswith("meat"):
            return "food_meats"
        if "mushroom" in lowered:
            return "food_mushrooms"

    return category


def _parse_args(argv: Optional[List[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan a drive for vanilla DayZ config.cpp files and export JSON.",
    )
    parser.add_argument(
        "--root",
        default=r"P:\\dz",
        help=r"Root folder to scan (default: P:\\dz)",
    )
    parser.add_argument(
        "--groups",
        default="gear,weapons",
        help="Comma-separated list of top-level groups to parse (default: gear,weapons)",
    )
    parser.add_argument(
        "--output",
        default=str(Path("output") / "vanilla_dayz_items.json"),
        help="Output file path (single-file mode) OR output directory (when --split)",
    )
    parser.add_argument(
        "--split",
        action="store_true",
        help="Write one JSON per (group, category) under the output directory",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=0,
        help="Limit number of config.cpp files parsed (0 = no limit)",
    )
    return parser.parse_args(argv)


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _is_within_dir(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _clear_output_dir(out_dir: Path) -> None:
    # Safety: only allow clearing under this project's ./output folder.
    project_root = Path(__file__).resolve().parents[2]
    allowed_root = (project_root / "output").resolve()
    out_dir_resolved = out_dir.resolve()

    if not _is_within_dir(out_dir_resolved, allowed_root):
        raise ValueError(
            f"Refusing to clear output outside {allowed_root}. Got: {out_dir_resolved}"
        )

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)

    root = Path(args.root)
    groups = [g.strip().lower() for g in str(args.groups).split(",") if g.strip()]
    out = Path(args.output)

    generated_at = datetime.now(timezone.utc).isoformat()

    matches: list[ConfigCppMatch] = []
    for match in iter_config_cpp_files(root=root, groups=groups):
        matches.append(match)
        if args.max_files and len(matches) >= args.max_files:
            break

    by_group_category: dict[str, dict[str, List[str]]] = {}
    existing_by_group_category: dict[str, dict[str, set[str]]] = {}

    for match in matches:
        try:
            text = match.path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            # Skip unreadable files in this constrained mode
            continue
        else:
            try:
                class_names = extract_scope2_cfg_children(text)
            except Exception as exc:  # keep running across bad files
                continue

        if not class_names:
            continue

        # Bucket + dedup while preserving existing order
        for name in class_names:
            target_category = _remap_category(match.group, match.category, name)

            bucket = by_group_category.setdefault(match.group, {}).setdefault(target_category, [])
            existing = (
                existing_by_group_category
                .setdefault(match.group, {})
                .setdefault(target_category, set(bucket))
            )

            if name not in existing:
                existing.add(name)
                bucket.append(name)

    payload = {
        "root": str(root),
        "generated_at": generated_at,
        "groups": groups,
        "group_category_index": {k: list(v.keys()) for k, v in by_group_category.items()},
        "items": by_group_category,
    }

    if not args.split:
        _write_json(out, payload)
        return 0

    _clear_output_dir(out)
    _write_json(out / "_index.json", {k: list(v.keys()) for k, v in by_group_category.items()})
    for group, categories in by_group_category.items():
        for category, entries in categories.items():
            _write_json(out / group / f"{category}.json", {
                "root": str(root),
                "generated_at": generated_at,
                "group": group,
                "category": category,
                "item_count": len(entries),
                "class_names": entries,
            })

    return 0
