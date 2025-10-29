@echo off
echo =====================================
echo Simple Trading Analysis (No Charts)
echo =====================================
echo.

cd /d "z:\DayZ\PythonApps\TradingAnalysis\source\scripts"

echo Installing pandas (basic requirement)...
C:/Python311/python.exe -m pip install pandas numpy --quiet

echo.
echo Running simple trading analysis...
C:/Python311/python.exe simple_trading_analysis.py

echo.
echo Analysis complete! Check the output folder for text reports.
pause