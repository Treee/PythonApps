@echo off
REM Test auto-airbrush on a single tile. Usage:
REM    test_airbrush_single.bat 7_7.png

SETLOCAL
if "%1"=="" (
  set IMAGE=7_7.png
) else (
  set IMAGE=%1
)

echo Running auto-airbrush on single image: %IMAGE%
python "%~dp0source\scripts\airbrush_cli.py" --single %IMAGE% --debug
echo Finished.
pause >nul
ENDLOCAL
