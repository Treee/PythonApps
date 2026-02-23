# DayZItemParser

Parses vanilla DayZ `config.cpp` files from a local drive (e.g. `P:\dz\...`) and exports JSON.

Current focus:

- `config.cpp` under `...\gear\...` and `...\weapons\...`
- The first subfolder under `gear/` or `weapons/` is treated as the **category**
- Output is currently constrained to **public item class names** (`scope = 2`) grouped by category

## Setup

1. (Optional) create/activate a venv
2. Install requirements:

```bat
pip install -r requirements.txt
```

## Run

Default parses `P:\dz` and writes one JSON file to `output\vanilla_dayz_items.json`:

```bat
run_parse_vanilla_dayz.bat
```

Or run from `scripts\`:

```bat
scripts\run_parse_vanilla_dayz.bat
scripts\run_parse_vanilla_dayz_split.bat
```

CLI usage:

```bat
python source\run_parser.py --root P:\dz --output output\vanilla_dayz_items.json
python source\run_parser.py --root P:\dz --split --output output
```

Notes:

- `--split` writes one JSON per `(group, category)` under the output directory.
- Use `--max-files` during development to limit parsing.
