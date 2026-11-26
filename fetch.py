import yfinance as yf, json, datetime
T = {"SAF":"SAF.PA","SPX":"SXR8.DE","EM":"IS3N.DE","SXXP":"EXSA.DE","GOLD":"GOLD.PA",
     "BTC":"BTC-EUR","ETH":"ETH-EUR","XRP":"XRP-EUR","SOL":"SOL-EUR",
     "RNDR":"RENDER-USD","HBAR":"HBAR-USD","BABA":"BABA","AI":"AI.PA","LVMH":"MC.PA","AAPL":"AAPL","FLNC":"FLNC"}
USD = {"RENDER-USD","HBAR-USD","BABA","AAPL","FLNC"}
def close(t, p="2y"):
    return yf.download(t, period=p, progress=False, auto_adjust=True)["Close"].squeeze().dropna()
fx = close("EURUSD=X")
hist, px = {}, {}
for k, t in T.items():
    try:
        c = close(t)
        if t in USD:
            c = c / fx.reindex(c.index).ffill().bfill()
        px[k] = round(float(c.iloc[-1]), 4)
        for d, v in (c.pct_change().dropna() * 100).items():
            hist.setdefault(str(d.date()), {})[k] = round(float(v), 2)
    except Exception as e:
        print("ERREUR", k, t, e)
WATCH = {"Nvidia":("NVDA","$"),"Dell":("DELL","$"),"HPE":("HPE","$"),"HP Inc":("HPQ","$"),"Autodesk":("ADSK","$"),"Workday":("WDAY","$"),"Analog Devices":("ADI","$"),"CrowdStrike":("CRWD","$"),"Zscaler":("ZS","$"),"Marvell":("MRVL","$"),"Salesforce":("CRM","$"),"Deere":("DE","$"),"Dollar Tree":("DLTR","$"),"Best Buy":("BBY","$"),"Sanofi":("SAN.PA","€"),"Clariane":("CLARI.PA","€"),"Volkswagen":("VOW3.DE","€"),"Airbus":("AIR.PA","€")}
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
json.dump({"updated": datetime.date.today().isoformat(), "px": px, "hist": hist, "watch": watch}, open("data/prices.json", "w"))
print("OK", len(px), "actifs")
