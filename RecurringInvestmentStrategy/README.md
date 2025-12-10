# Recurring Investment Strategy (Web)

A simple client-side web app to simulate recurring investments for a given stock symbol using Yahoo Finance's unofficial chart API.

## Features

-   Enter stock symbol and date range
-   Choose interval: monthly, biweekly, weekly
-   Set contribution per interval (USD)
-   Toggle spending surplus when it reaches/ exceeds current price
-   Results table: Interval Date, Price, Shares Purchased, Remaining Balance, Total Remaining Balance
-   Summary totals: Total Shares, Total Spent, Dollar Cost Average (DCA)

## Run

Option 1: Open `src/index.html` in your browser.

If you see a CORS error, use the local proxy and serve the frontend:

1. Start the proxy (first time, install deps):

```powershell
cd Z:\DayZ\PythonApps\RecurringInvestmentStrategy\proxy
"Z:\DayZ\PythonApps\.venv\Scripts\python.exe" -m pip install -r requirements.txt
"Z:\DayZ\PythonApps\.venv\Scripts\python.exe" server.py
```

2. Serve the frontend:

```powershell
cd Z:\DayZ\PythonApps\RecurringInvestmentStrategy\src
python -m http.server 8000
```

Open `http://localhost:8000/index.html`. The app defaults to using `http://127.0.0.1:5001/chart` to avoid CORS.

## Notes

-   Uses Yahoo Finance chart endpoint: `https://query1.finance.yahoo.com/v8/finance/chart/{symbol}` — availability or CORS can change.
-   Prices use the nearest trading day to each interval date.
-   Fractional shares are purchased from each interval contribution; surplus may purchase whole shares if enabled.
