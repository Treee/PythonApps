@echo off
echo Starting SatMap Image Slicer...
echo.

REM Change to the scripts directory
cd /d "%~dp0source\scripts"

REM Run the Python script
python image_slicer.py

echo.
echo Script completed. Press any key to exit...
pause >nul