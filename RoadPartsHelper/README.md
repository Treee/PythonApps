# RoadPartsHelper

Copy DayZ road part `.p3d` files from a source directory into static destinations within `P:\dz` using a simple pattern mapping config.

## Overview

-   Source directory is scanned recursively for `.p3d` files.
-   A YAML/JSON config maps filename patterns to destination subfolders under `P:\dz`.
-   Supports `--dry-run` and `--verbose` flags.

## Prerequisites

-   Ensure the DayZ Tools `P:` drive is mounted and `P:\dz` exists.
-   Python 3.10+ in this workspace. For YAML configs, install `PyYAML`.

```powershell
# Activate the workspace venv if available
& Z:/DayZ/PythonApps/.venv/Scripts/Activate.ps1

# Optional: install PyYAML for YAML configs
pip install pyyaml
```

## Config

Edit `source/destinations.yaml` to define mappings:

```yaml
mappings:
	- pattern: "road_*.p3d"
		destination: "roads/parts"
	- pattern: "bridge_*.p3d"
		destination: "roads/bridges"
```

-   `pattern`: filename glob matched against `.p3d` names (not paths).
-   `destination`: subfolder under `P:\dz` where files are copied.

You can also use a JSON file with the same structure.

## Quick Start

Use the batch file or Python to run the CLI:

```powershell
# Dry run to preview operations (batch)
z:/DayZ/PythonApps/RoadPartsHelper/scripts/run_copy_road_parts.bat `
	z:/DayZ/PythonApps/RoadPartsHelper/source/destinations.yaml `
	--dry-run --verbose

# Perform the copy (batch)
z:/DayZ/PythonApps/RoadPartsHelper/scripts/run_copy_road_parts.bat `
	z:/DayZ/PythonApps/RoadPartsHelper/source/destinations.yaml `
	--verbose

# Alternatively run with Python
python z:/DayZ/PythonApps/RoadPartsHelper/source/road_parts_helper.py `
	z:/DayZ/PythonApps/RoadPartsHelper/source/destinations.yaml `
	--verbose
```

## Notes

-   Destination folders must already exist; missing destinations are skipped (no folders are created).
-   Copies use `copy2` to preserve timestamps where possible.
-   If `P:\dz` is not found, the program exits with an error.
