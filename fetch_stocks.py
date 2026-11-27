import yfinance as yf, json, datetime, time, math

def num(x):
    try:
        x = float(x)
        return None if math.isnan(x) or math.isinf(x) else round(x, 4)
    except Exception:
        return None

today = datetime.date.today()
tickers = []
for l in open("tickers.txt", encoding="utf-8"):
    l = l.strip()
    if l and not l.startswith("#") and l not in tickers:
        tickers.append(l)

def to_date(v):
    try:
        if isinstance(v, (int, float)):
            return datetime.datetime.utcfromtimestamp(v).date().isoformat()
        return str(v)[:10]
    except Exception:
        return None

out = {}
for t in tickers:
    try:
        c = yf.download(t, period="1y", progress=False, auto_adjust=True)["Close"].squeeze().dropna()
        if len(c) < 5:
            print("PEU DE DONNEES", t)
            continue
        tk = yf.Ticker(t)
        info = {}
        try:
            info = tk.info or {}
        except Exception as e:
            print("info", t, e)
        price = num(info.get("currentPrice")) or num(info.get("regularMarketPrice")) or round(float(c.iloc[-1]), 2)
        f = {"price": price, "pe": num(info.get("trailingPE")), "fpe": num(info.get("forwardPE")),
             "roe": num(info.get("returnOnEquity")), "om": num(info.get("operatingMargins")),
             "rg": num(info.get("revenueGrowth")), "eg": num(info.get("earningsGrowth")),
             "de": num(info.get("debtToEquity")), "cr": num(info.get("currentRatio")),
             "dyr": num(info.get("dividendRate")), "pr": num(info.get("payoutRatio")),
             "rec": num(info.get("recommendationMean")), "tgt": num(info.get("targetMeanPrice")),
             "fcf": num(info.get("freeCashflow")), "sh": num(info.get("sharesOutstanding")),
             "mc": num(info.get("marketCap")), "beta": num(info.get("beta"))}
        news = []
        try:
            for it in (tk.news or [])[:6]:
                c0 = it.get("content") or it
                title = c0.get("title")
                url = (c0.get("canonicalUrl") or {}).get("url") or c0.get("link") or (c0.get("clickThroughUrl") or {}).get("url")
                src = (c0.get("provider") or {}).get("displayName") or c0.get("publisher")
                dt = to_date(c0.get("pubDate") or c0.get("providerPublishTime") or it.get("providerPublishTime"))
                if title:
                    news.append([title, url, src, dt])
        except Exception as e:
            print("news", t, e)
        ev = {"next": None, "past": [], "exdiv": None, "divdate": None}
        try:
            cal = tk.calendar or {}
            ed = cal.get("Earnings Date")
            if ed:
                ds = [to_date(x) for x in (ed if isinstance(ed, (list, tuple)) else [ed])]
                ds = [d for d in ds if d and d >= today.isoformat()]
                ev["next"] = ds[0] if ds else None
            ev["exdiv"] = to_date(cal.get("Ex-Dividend Date")) if cal.get("Ex-Dividend Date") else None
            ev["divdate"] = to_date(cal.get("Dividend Date")) if cal.get("Dividend Date") else None
        except Exception as e:
            print("calendar", t, e)
        try:
            edf = tk.earnings_dates
            if edf is not None:
                for ts, row in edf.iterrows():
                    d = ts.date()
                    rep = num(row.get("Reported EPS"))
                    if d < today and rep is not None:
                        ev["past"].append([d.isoformat(), num(row.get("EPS Estimate")), rep, num(row.get("Surprise(%)"))])
                    elif d >= today and not ev["next"]:
                        ev["next"] = d.isoformat()
                ev["past"] = sorted(ev["past"], reverse=True)[:5]
        except Exception as e:
            print("earnings_dates", t, e)
        out[t] = {"n": info.get("shortName") or info.get("longName") or t, "cur": info.get("currency"),
                  "sec": info.get("sector"), "ind": info.get("industry"),
                  "d": [str(x.date()) for x in c.index], "p": [round(float(x), 2) for x in c.values],
                  "f": f, "news": news, "ev": ev}
    except Exception as e:
        print("ERREUR", t, e)
    time.sleep(0.4)

json.dump({"updated": today.isoformat(), "s": out}, open("data/stocks.json", "w", encoding="utf-8"),
          ensure_ascii=False, separators=(",", ":"))
print("OK", len(out), "entreprises sur", len(tickers))
