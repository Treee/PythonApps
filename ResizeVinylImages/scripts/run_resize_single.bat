@echo off
REM Resize a single vinyl cover to 1024x512 (bottom-left anchored)
SETLOCAL

if "%~1"=="" (
  echo Usage: %~nx0 "^<path-to-image^>" [output_png]
  echo Example: %~nx0 "Z:\DayZ\SourceImages\gear\camping\vinyls\collection\00.jpeg"
  ENDLOCAL
  exit /b 1
)

set INPUT=%~1
set OUTPUT=%~2
set WIDTH=1024
set HEIGHT=512

if "%OUTPUT%"=="" (
  REM Default output to the 'collections' folder next to the source folder
  for %%I in ("%INPUT%") do set SRC_DIR=%%~dpI
  for %%I in ("%SRC_DIR%..") do set PARENT_DIR=%%~fI
  set OUTDIR=%PARENT_DIR%\collections
  if not exist "%OUTDIR%" mkdir "%OUTDIR%"
  for %%I in ("%INPUT%") do set BASENAME=%%~nI
  REM Replace dashes with underscores in BASENAME
  set BASENAME=%BASENAME:-=_%
  set OUTPUT="%OUTDIR%\iat_vinyl_%BASENAME%_co.png"
  python "%~dp0\resize_single_vinyl.py" --input "%INPUT%" --output %OUTPUT% --width %WIDTH% --height %HEIGHT%
) else (
  python "%~dp0\resize_single_vinyl.py" --input "%INPUT%" --output "%OUTPUT%" --width %WIDTH% --height %HEIGHT%
)

ENDLOCAL
