// Uses Yahoo Finance Chart API: https://query1.finance.yahoo.com/v8/finance/chart/{symbol}
// No API keys; subject to Yahoo availability and CORS.

const el = (id) => document.getElementById(id);

const statusEl = el("status");
const tableBody = document.querySelector("#resultsTable tbody");

const fmtUSD = (n) => (n ?? 0).toLocaleString(undefined, { style: "currency", currency: "USD" });
const fmtNum = (n) => (n ?? 0).toLocaleString(undefined, { maximumFractionDigits: 6 });
const fmtDate = (d) => d.toISOString().slice(0, 10);

document.addEventListener("DOMContentLoaded", () => {
    el("computeBtn").addEventListener("click", onCompute);
});

async function onCompute() {
    clearResults();
    const symbol = el("symbol").value.trim().toUpperCase();
    const startStr = el("start").value + "T00:00";
    const endStr = el("end").value + "T00:00";
    const intervalChoice = el("interval").value;
    const contribution = Number(el("contribution").value);
    const spendOverage = el("spendOverage").checked;

    if (!symbol || !startStr || !endStr || !(contribution > 0)) {
        setStatus("Please provide symbol, dates, and a positive contribution.");
        return;
    }

    const startDate = new Date(startStr);
    const endDate = new Date(endStr);
    if (startDate > endDate) {
        setStatus("Start date must be before end date.");
        return;
    }

    setStatus("Fetching price data from Yahoo Finance…");
    try {
        const intervalDates = buildIntervalDates(startDate, endDate, intervalChoice);
        const { pricesByDate, tzOffset } = await fetchYahooPrices(symbol, startDate, endDate);

        // Simulation
        let runningBalance = 0;
        let totalSpent = 0;
        let totalShares = 0;

        for (const d of intervalDates) {
            const nearest = nearestTradingDate(d, pricesByDate);
            const price = nearest ? pricesByDate.get(nearest) : undefined;

            // Add this interval's contribution
            runningBalance += contribution;
            let sharesPurchased = 0;

            if (price && price > 0) {
                // Buy ONLY whole shares from the interval contribution
                const contributionWholeShares = Math.floor(contribution / price);
                if (contributionWholeShares > 0) {
                    const spentThisInterval = contributionWholeShares * price;
                    sharesPurchased += contributionWholeShares;
                    runningBalance -= spentThisInterval; // spend from the newly added contribution
                    totalSpent += spentThisInterval;
                }

                // When toggle is enabled, also spend surplus on whole shares
                if (spendOverage && runningBalance >= price) {
                    const extraWholeShares = Math.floor(runningBalance / price);
                    if (extraWholeShares > 0) {
                        const extraSpend = extraWholeShares * price;
                        runningBalance -= extraSpend;
                        totalSpent += extraSpend;
                        sharesPurchased += extraWholeShares;
                    }
                }
            }

            totalShares += sharesPurchased;

            addRow({
                date: nearest || fmtDate(d),
                price: price ?? null,
                shares: sharesPurchased,
                remaining: runningBalance,
                totalRemaining: runningBalance,
            });
        }

        const dca = totalShares > 0 ? totalSpent / totalShares : 0;
        el("totalShares").textContent = fmtNum(totalShares);
        el("totalSpent").textContent = (totalSpent ?? 0).toFixed(2);
        el("dca").textContent = (dca ?? 0).toFixed(4);
        // Fetch today's price (average of open/close) to value the position
        try {
            const todayPrice = await fetchTodayAvgPrice(symbol);
            const positionValue = totalShares * (todayPrice || 0);
            el("positionValue").textContent = (positionValue ?? 0).toFixed(2);
            // Show profits as a positive number when position value exceeds total spend
            const rawDelta = (positionValue ?? 0) - (totalSpent ?? 0);
            let profits = rawDelta;
            if (totalSpent < positionValue) profits = Math.abs(rawDelta);
            el("profits").textContent = (profits ?? 0).toFixed(2);
        } catch (e) {
            el("positionValue").textContent = "-";
            el("profits").textContent = "-";
        }
        setStatus("Done.");
    } catch (err) {
        console.error(err);
        setStatus(`Error: ${err.message || err}`);
    }
}

async function fetchTodayAvgPrice(symbol) {
    // Query a short recent window to get the latest trading day's open/close
    const now = new Date();
    const start = new Date(now);
    start.setDate(start.getDate() - 7);
    const { pricesByDate } = await fetchYahooPrices(symbol, start, now);
    // Find the most recent date key
    const dates = Array.from(pricesByDate.keys()).sort();
    if (dates.length === 0) return null;
    const latest = dates[dates.length - 1];
    return pricesByDate.get(latest) ?? null;
}

function buildIntervalDates(start, end, interval) {
    const dates = [];
    const d = setNYOpenTime(new Date(start));
    const endBell = setNYOpenTime(new Date(end));
    switch (interval) {
        case "monthly": {
            while (d.getTime() <= endBell.getTime()) {
                dates.push(new Date(d));
                d.setMonth(d.getMonth() + 1);
                setNYOpenTime(d);
            }
            break;
        }
        case "biweekly": {
            while (d.getTime() <= endBell.getTime()) {
                dates.push(new Date(d));
                d.setDate(d.getDate() + 14);
                setNYOpenTime(d);
            }
            break;
        }
        case "weekly": {
            while (d.getTime() <= endBell.getTime()) {
                dates.push(new Date(d));
                d.setDate(d.getDate() + 7);
                setNYOpenTime(d);
            }
            break;
        }
        default:
            dates.push(setNYOpenTime(new Date(start)));
            break;
    }
    return dates;
}

function setNYOpenTime(date) {
    // Set date time to 9:30 AM America/New_York, handling EST/EDT offsets.
    const nyOffsetHours = getNYUtcOffsetHours(date); // -5 for EST, -4 for EDT
    // Build an ISO string with the proper UTC offset
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    const sign = nyOffsetHours <= 0 ? "-" : "+";
    const abs = Math.abs(nyOffsetHours);
    const offsetStr = `${sign}${String(abs).padStart(2, "0")}:00`;
    const isoWithOffset = `${y}-${m}-${d}T09:30:00${offsetStr}`;
    const adjusted = new Date(isoWithOffset);
    return adjusted;
}

function getNYUtcOffsetHours(date) {
    // Detect EST vs EDT via timeZoneName
    try {
        const parts = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", timeZoneName: "short" }).formatToParts(date);
        const tzPart = parts.find((p) => p.type === "timeZoneName");
        const name = tzPart ? tzPart.value : "";
        // EST => UTC-5, EDT => UTC-4
        if (name.includes("EST")) return -5;
        if (name.includes("EDT")) return -4;
    } catch (e) {
        // Fallback: assume EST
    }
    return -5;
}

async function fetchYahooPrices(symbol, startDate, endDate) {
    const period1 = Math.floor(startDate.getTime() / 1000);
    const period2 = Math.floor(endDate.getTime() / 1000) + 86400 * 3;
    const directUrl = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?period1=${period1}&period2=${period2}&interval=1d&includePrePost=false&events=div%2Csplits`;
    const proxyBase = window.PROXY_URL || "http://127.0.0.1:5001/chart";
    const proxyUrl = `${proxyBase}?symbol=${encodeURIComponent(symbol)}&period1=${period1}&period2=${period2}&interval=1d&includePrePost=false&events=div%2Csplits`;

    // Try proxy first to avoid CORS; fall back to direct if proxy unavailable
    let res;
    try {
        res = await fetch(proxyUrl, { method: "GET" });
    } catch (e) {
        res = await fetch(directUrl, { method: "GET" });
    }
    if (!res.ok) throw new Error(`Yahoo request failed: ${res.status}`);
    const data = await res.json();

    const result = data?.chart?.result?.[0];
    if (!result) throw new Error("No chart data found for symbol.");

    const timestamps = result.timestamp || [];
    const quote = result.indicators?.quote?.[0] || {};
    const opens = quote.open || [];
    const closes = quote.close || [];
    const tzOffset = result.meta?.gmtoffset || 0;

    const map = new Map();
    for (let i = 0; i < timestamps.length; i++) {
        const ts = timestamps[i];
        const o = opens[i];
        const c = closes[i];
        // Use average of open/close when both exist; fallback to whichever is available
        let price = null;
        if (o != null && c != null) price = (o + c) / 2;
        else if (c != null) price = c;
        else if (o != null) price = o;
        if (ts && price != null) {
            const dateStr = new Date(ts * 1000).toISOString().slice(0, 10);
            map.set(dateStr, price);
        }
    }
    return { pricesByDate: map, tzOffset };
}

function nearestTradingDate(targetDate, pricesByDate) {
    // Try exact match first; else prefer forward days to keep range inclusive
    const exact = fmtDate(targetDate);
    if (pricesByDate.has(exact)) return exact;
    // Prefer next trading day within a week
    for (let fwd = 1; fwd <= 7; fwd++) {
        const d = new Date(targetDate);
        d.setDate(d.getDate() + fwd);
        const s = fmtDate(d);
        if (pricesByDate.has(s)) return s;
    }
    // If no forward match, fall back to previous trading day
    for (let back = 1; back <= 7; back++) {
        const d = new Date(targetDate);
        d.setDate(d.getDate() - back);
        const s = fmtDate(d);
        if (pricesByDate.has(s)) return s;
    }
    return null;
}

function clearResults() {
    tableBody.innerHTML = "";
    el("totalShares").textContent = "0";
    el("totalSpent").textContent = "0.00";
    el("dca").textContent = "0.00";
    setStatus("");
}

function addRow({ date, price, shares, remaining, totalRemaining }) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
    <td>${date}</td>
    <td>${price != null ? fmtUSD(price) : "-"}</td>
    <td>${fmtNum(shares)}</td>
    <td>${fmtUSD(remaining)}</td>
    <td>${fmtUSD(totalRemaining)}</td>
  `;
    tableBody.appendChild(tr);
}

function setStatus(msg) {
    statusEl.textContent = msg || "";
}
