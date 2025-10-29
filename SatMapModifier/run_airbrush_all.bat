@echo off
REM Run auto-airbrush on all tiles in the output folder.

echo Running auto-airbrush on all images in output\ ...
python "%~dp0source\scripts\airbrush_cli.py" --all
echo Finished.
pause >nul
