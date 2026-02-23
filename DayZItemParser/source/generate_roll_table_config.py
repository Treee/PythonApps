from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


_ALLOWED_MAX_ROLLS = [6, 8, 10, 12, 20, 50, 100, 200]


@dataclass(frozen=True)
class SplitCategory:
    group: str
    category: str
    class_names: list[str]


def _safe_table_name(name: str) -> str:
    # Keep names stable + simple for DayZ configs.
    safe = re.sub(r"[^A-Za-z0-9_]+", "_", name)
    safe = re.sub(r"_+", "_", safe).strip("_")
    return safe or "_unnamed"


def _choose_max_roll(item_count: int) -> int:
    if item_count <= 0:
        return _ALLOWED_MAX_ROLLS[0]
    for v in _ALLOWED_MAX_ROLLS:
        if item_count <= v:
            return v
    return _ALLOWED_MAX_ROLLS[-1]


def _iter_split_categories(split_dir: Path) -> Iterable[SplitCategory]:
    for p in sorted(split_dir.rglob("*.json")):
        if p.name == "_index.json":
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue

        group = str(data.get("group") or "").strip()
        category = str(data.get("category") or "").strip()
        names = data.get("class_names")
        if not group or not category or not isinstance(names, list) or not names:
            continue

        class_names = [n for n in names if isinstance(n, str) and n]
        if not class_names:
            continue

        yield SplitCategory(group=group, category=category, class_names=class_names)


def generate_roll_table_config(*, split_dir: Path, out_path: Path) -> None:
    roll_table_map: dict[str, dict] = {}

    for cat in _iter_split_categories(split_dir):
        table_key = _safe_table_name(f"{cat.group}_{cat.category}")
        max_roll = _choose_max_roll(len(cat.class_names))

        roll_table_map[table_key] = {
            "m_TableName": table_key,
            "m_MaxRoll": max_roll,
            "m_ListOfProbabilities": [
                {
                    "m_MinRollRange": 1,
                    "m_MaxRollRange": max_roll,
                    "m_Results": cat.class_names,
                }
            ],
        }

    out_payload = {"m_RollTableMap": roll_table_map}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out_payload, indent=4, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    split_dir = project_root / "output" / "split"
    out_path = project_root / "output" / "RollTableConfig_SplitOutputs.json"

    if not split_dir.exists() or not split_dir.is_dir():
        raise SystemExit(f"Split output dir not found: {split_dir}")

    generate_roll_table_config(split_dir=split_dir, out_path=out_path)
    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
