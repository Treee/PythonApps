@echo off
echo =====================================
echo Run Chaotic Forge Temperature Simulator
echo =====================================

REM Change to the script directory
cd /d "%~dp0source"

echo Running forge simulator (no interactive plot)...
C:/Python311/python.exe forge_sim.py --seed -1 --no-plot --t-min 700 --t-max 900 --duration 300 --sample-rate 3 --reversion 0.35 --volatility 10.0 --spike-prob 0.18 --spike-std 30 --surge-height 95 --surge-half-life 0.3 --bellows-times 33 89 120 185 250 --out-png ..\output\advanced_forge_birch.png --out-csv ..\output\advanced_forge_birch.csv
C:/Python311/python.exe forge_sim.py --seed -1 --no-plot --t-min 900 --t-max 1100 --duration 300 --sample-rate 3 --reversion 0.35 --volatility 10.0 --spike-prob 0.18 --spike-std 30 --surge-height 95 --surge-half-life 0.3 --bellows-times 33 89 120 185 250 --out-png ..\output\advanced_forge_oak.png --out-csv ..\output\advanced_forge_oak.csv
C:/Python311/python.exe forge_sim.py --seed -1 --no-plot --t-min 1300 --t-max 1500 --duration 300 --sample-rate 3 --reversion 0.35 --volatility 10.0 --spike-prob 0.18 --spike-std 30 --surge-height 95 --surge-half-life 0.3 --bellows-times 33 89 120 185 250 --out-png ..\output\advanced_forge_charcoal.png --out-csv ..\output\advanced_forge_charcoal.csv
C:/Python311/python.exe forge_sim.py --seed -1 --no-plot --t-min 1400 --t-max 1700 --duration 300 --sample-rate 3 --reversion 0.35 --volatility 10.0 --spike-prob 0.18 --spike-std 30 --surge-height 95 --surge-half-life 0.3 --bellows-times 33 89 120 185 250 --out-png ..\output\advanced_forge_coal.png --out-csv ..\output\advanced_forge_coal.csv
C:/Python311/python.exe forge_sim.py --seed -1 --no-plot --t-min 1800 --t-max 2000 --duration 300 --sample-rate 3 --reversion 0.35 --volatility 10.0 --spike-prob 0.18 --spike-std 30 --surge-height 95 --surge-half-life 0.3 --bellows-times 33 89 120 185 250 --out-png ..\output\advanced_forge_coke.png --out-csv ..\output\advanced_forge_coke.csv

echo.
echo Done. Output files:
echo  - %~dp0advanced_forge.png
echo  - %~dp0advanced_forge.csv

pause
