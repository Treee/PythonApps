@echo off
REM Run the SatMapModifier stitcher and forward any arguments to the Python script.
REM Usage: run_stitch_brushed.bat [--input-dir "path"] [--output-name "name.bmp"] [--recursive] [--tile-size 1024]

setlocal

REM Resolve script path relative to this .bat file (works when run from any cwd)
set "SCRIPT=%~dp0source\scripts\_stitch_brushed.py"

if not exist "%SCRIPT%" (
  echo Script not found: "%SCRIPT%"
  exit /b 2
)

REM Call Python and forward all arguments
python "%SCRIPT%" %*

endlocal
