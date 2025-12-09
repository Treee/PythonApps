@echo off
setlocal

REM Ensure Python can import the project modules when run from repo root
set "PYTHONPATH=%~dp0..;%~dp0..\..;%PYTHONPATH%"

REM Usage: run_copy_road_parts.bat <config.yaml> [--dry-run] [--verbose]
if "%~1"=="" (
    echo Usage: %~nx0 ^<config.yaml^> [--dry-run] [--verbose]
    exit /b 1
)

python "%~dp0..\source\road_parts_helper.py" "%~1" %~2 %~3 %~4 %~5

endlocal