from flask import Flask, request, Response
import requests
import time

app = Flask(__name__)

YF_BASE = "https://query1.finance.yahoo.com/v8/finance/chart/"

@app.route("/chart")
def chart():
    symbol = request.args.get("symbol")
    period1 = request.args.get("period1")
    period2 = request.args.get("period2")
    interval = request.args.get("interval", "1d")
    includePrePost = request.args.get("includePrePost", "false")
    events = request.args.get("events", "div%2Csplits")

    if not symbol or not period1 or not period2:
        return Response("Missing required params", status=400)

    url = f"{YF_BASE}{requests.utils.quote(symbol)}?period1={period1}&period2={period2}&interval={interval}&includePrePost={includePrePost}&events={events}"

    headers = {
        # Use a common browser UA to avoid trivial bot blocking
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

    # Basic retry/backoff on 429 or transient errors
    attempts = 0
    last_r = None
    while attempts < 3:
        attempts += 1
        try:
            r = requests.get(url, timeout=20, headers=headers)
            last_r = r
            if r.status_code != 429:
                break
            # Backoff before retrying on rate limit
            time.sleep(1.5 * attempts)
        except requests.RequestException:
            time.sleep(0.8 * attempts)
            continue
    r = last_r if last_r is not None else requests.Response()

    resp = Response(r.content, status=r.status_code, content_type=r.headers.get("Content-Type", "application/json"))
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "*"
    return resp

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)
