@echo off
echo =====================================
echo Trading Analysis Tool
echo =====================================
echo.

cd /d "z:\DayZ\PythonApps\TradingAnalysis\source\scripts"

echo Installing required packages...
C:/Python311/python.exe -m pip install pandas matplotlib seaborn numpy --quiet

echo.
echo Running trading analysis...
C:/Python311/python.exe trading_analysis_main.py

echo.
echo Analysis complete! Check the output folder for results.
pause