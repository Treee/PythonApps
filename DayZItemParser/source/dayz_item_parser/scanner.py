from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Set, Tuple


@dataclass(frozen=True)
class ConfigCppMatch:
    path: Path
    group: str  # gear | weapons (for now)
    category: str  # first subfolder under group


def _path_parts_lower(path: Path) -> List[str]:
    return [p.lower() for p in path.parts]


def _extract_group_category(path: Path, groups: Set[str]) -> Optional[Tuple[str, str]]:
    parts = _path_parts_lower(path)

    for group in groups:
        try:
            idx = parts.index(group)
        except ValueError:
            continue

        category = "_uncategorized"
        if idx + 1 < len(path.parts):
            category = path.parts[idx + 1]
        return group, category

    return None


def _category_from_group_dir(file_path: Path, group_dir: Path) -> str:
    try:
        rel = file_path.relative_to(group_dir)
    except ValueError:
        return "_uncategorized"

    # Category is the first subfolder under group, e.g. gear\clothing\...\config.cpp
    if len(rel.parts) >= 2:
        return rel.parts[0]
    return "_uncategorized"


def iter_config_cpp_files(*, root: Path, groups: Iterable[str]) -> Iterator[ConfigCppMatch]:
    groups_set = {g.lower() for g in groups}
    if not root.exists():
        return

    # Restrict traversal to only the requested group subtrees (e.g. root\gear and root\weapons)
    for group in sorted(groups_set):
        group_dir = root / group
        if not group_dir.exists() or not group_dir.is_dir():
            continue

        for file_path in group_dir.rglob("config.cpp"):
            if not file_path.is_file():
                continue
            category = _category_from_group_dir(file_path, group_dir)
            yield ConfigCppMatch(path=file_path, group=group, category=category)
