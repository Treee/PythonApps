@echo off
REM Run the vinyl collection resizer with defaults
SETLOCAL

REM Adjust these if your paths differ
set INPUT=Z:\DayZ\SourceImages\gear\camping\vinyls\collection
set WIDTH=1024
set HEIGHT=512

REM Use the workspace python if on PATH; otherwise, you can replace `python` with a full path
python "%~dp0\resize_vinyl_collection.py" --input "%INPUT%" --width %WIDTH% --height %HEIGHT%

ENDLOCAL
