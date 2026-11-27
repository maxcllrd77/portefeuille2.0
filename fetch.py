import yfinance as yf, json, datetime, math

T = {"SAF":"SAF.PA","SPX":"SXR8.DE","EM":"IS3N.DE","SXXP":"EXSA.DE","GOLD":"GOLD.PA",
     "BTC":"BTC-EUR","ETH":"ETH-EUR","XRP":"XRP-EUR","SOL":"SOL-EUR",
     "RNDR":"RENDER-USD","HBAR":"HBAR-USD","BABA":"BABA","AI":"AI.PA","LVMH":"MC.PA","AAPL":"AAPL","FLNC":"FLNC"}
USD = {"RENDER-USD","HBAR-USD","BABA","AAPL","FLNC"}
ADR = {"BABA": 8}  # 1 ADR Alibaba = 8 actions ordinaires (celles que tu detiens)
WATCH = {"Nvidia":("NVDA","$"),"Dell":("DELL","$"),"HPE":("HPE","$"),"HP Inc":("HPQ","$"),"Autodesk":("ADSK","$"),"Workday":("WDAY","$"),"Analog Devices":("ADI","$"),"CrowdStrike":("CRWD","$"),"Zscaler":("ZS","$"),"Marvell":("MRVL","$"),"Salesforce":("CRM","$"),"Deere":("DE","$"),"Dollar Tree":("DLTR","$"),"Best Buy":("BBY","$"),"Sanofi":("SAN.PA","€"),"Clariane":("CLARI.PA","€"),"Volkswagen":("VOW3.DE","€"),"Airbus":("AIR.PA","€")}
MKT = {"S&P 500":"^GSPC","Nasdaq":"^IXIC","CAC 40":"^FCHI","Taux US 10 ans":"^TNX","Dollar (DXY)":"DX-Y.NYB"}
STK = {"SAF":"SAF.PA","LVMH":"MC.PA","AI":"AI.PA","AAPL":"AAPL","BABA":"BABA","FLNC":"FLNC"}

def close(t, p="2y"):
    return yf.download(t, period=p, progress=False, auto_adjust=True)["Close"].squeeze().dropna()

def num(x):
    try:
        x = float(x)
        return None if math.isnan(x) or math.isinf(x) else x
    except Exception:
        return None

fx = close("EURUSD=X")
hist, px = {}, {}
for k, t in T.items():
    try:
        c = close(t)
        if t in USD:
            c = c / fx.reindex(c.index).ffill().bfill()
        c = c / ADR.get(k, 1)
        px[k] = round(float(c.iloc[-1]), 4)
        for d, v in (c.pct_change().dropna() * 100).items():
            hist.setdefault(str(d.date()), {})[k] = round(float(v), 2)
    except Exception as e:
        print("ERREUR", k, t, e)

watch = {}
for n, (t, cur) in WATCH.items():
    try:
        c = close(t, "3mo")
        watch[n] = {"t": t, "c": cur, "px": round(float(c.iloc[-1]), 2),
                    "d": round(float(c.iloc[-1] / c.iloc[-2] - 1) * 100, 2),
                    "w": round(float(c.iloc[-1] / c.iloc[-6] - 1) * 100, 2),
                    "m": round(float(c.iloc[-1] / c.iloc[-22] - 1) * 100, 2)}
    except Exception as e:
        print("ERREUR watch", n, t, e)

# --- indices, taux, dollar, VIX (sentiment) ---
market = {}
for n, t in MKT.items():
    try:
        c = close(t, "3mo")
        if n.startswith("Taux"):
            market[n] = {"px": round(float(c.iloc[-1]), 2), "d": round(float(c.iloc[-1] - c.iloc[-2]), 2),
                         "w": round(float(c.iloc[-1] - c.iloc[-6]), 2), "m": round(float(c.iloc[-1] - c.iloc[-22]), 2), "pts": True}
        else:
            market[n] = {"px": round(float(c.iloc[-1]), 2),
                         "d": round(float(c.iloc[-1] / c.iloc[-2] - 1) * 100, 2),
                         "w": round(float(c.iloc[-1] / c.iloc[-6] - 1) * 100, 2),
                         "m": round(float(c.iloc[-1] / c.iloc[-22] - 1) * 100, 2)}
    except Exception as e:
        print("ERREUR marche", n, t, e)
try:
    v = close("^VIX", "1y")
    market["VIX"] = {"px": round(float(v.iloc[-1]), 2), "d": round(float(v.iloc[-1] - v.iloc[-2]), 2),
                     "avg30": round(float(v.tail(30).mean()), 2), "pct": round(float((v <= v.iloc[-1]).mean() * 100)),
                     "max": round(float(v.max()), 2), "min": round(float(v.min()), 2)}
except Exception as e:
    print("ERREUR VIX", e)

# --- indice Peur & Avidité crypto ---
fng = None
try:
    import requests
    j = requests.get("https://api.alternative.me/fng/?limit=30", timeout=20).json()["data"]
    fng = {"v": int(j[0]["value"]), "c": j[0]["value_classification"], "w": int(j[min(7, len(j) - 1)]["value"]), "m": int(j[-1]["value"])}
except Exception as e:
    print("ERREUR fng", e)

# --- fondamentaux pour les scores et le DCF ---
fund = {}
for k, t in STK.items():
    try:
        i = yf.Ticker(t).info
        price = num(i.get("currentPrice")) or num(i.get("regularMarketPrice"))
        fund[k] = {"t": t, "cur": i.get("currency"), "price": price, "pe": num(i.get("trailingPE")),
                   "roe": num(i.get("returnOnEquity")), "om": num(i.get("operatingMargins")),
                   "rg": num(i.get("revenueGrowth")), "eg": num(i.get("earningsGrowth")),
                   "de": num(i.get("debtToEquity")), "cr": num(i.get("currentRatio")),
                   "dyr": num(i.get("dividendRate")), "pr": num(i.get("payoutRatio")),
                   "rec": num(i.get("recommendationMean")), "tgt": num(i.get("targetMeanPrice")),
                   "fcf": num(i.get("freeCashflow")), "sh": num(i.get("sharesOutstanding"))}
    except Exception as e:
        print("ERREUR fund", k, t, e)

json.dump({"updated": datetime.date.today().isoformat(), "px": px, "hist": hist, "watch": watch,
           "market": market, "fng": fng, "fund": fund}, open("data/prices.json", "w"))
print("OK", len(px), "actifs,", len(market), "indices,", len(fund), "fondamentaux")
