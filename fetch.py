import yfinance as yf, json, datetime
# Plusieurs tickers possibles pour une ligne : on essaie dans l'ordre jusqu'au premier qui marche.
T = {"SAF":"SAF.PA","SPX":"SXR8.DE","EM":["AMEM.DE","AEEM.PA"],"SXXP":"EXSA.DE","GOLD":"GOLD.PA",
     "BTC":"BTC-EUR","ETH":"ETH-EUR","XRP":"XRP-EUR","SOL":"SOL-EUR",
     "RNDR":"RENDER-USD","HBAR":"HBAR-USD","BABA":"9988.HK","AI":"AI.PA","LVMH":"MC.PA","AAPL":"AAPL","FLNC":"FLNC"}
# Cours cotés dans une autre monnaie : on les convertit en euros.
CUR = {"RENDER-USD":"USD","HBAR-USD":"USD","AAPL":"USD","FLNC":"USD","9988.HK":"HKD"}
def close(t):
    c = yf.download(t, period="400d", progress=False, auto_adjust=True)["Close"].squeeze().dropna()
    if c.empty:
        raise ValueError("aucune donnee")
    return c
fx = {"USD": close("EURUSD=X"), "HKD": close("EURHKD=X")}
hist, px = {}, {}
for k, cands in T.items():
    for t in (cands if isinstance(cands, list) else [cands]):
        try:
            c = close(t)
            if t in CUR:
                c = c / fx[CUR[t]].reindex(c.index).ffill().bfill()
            px[k] = round(float(c.iloc[-1]), 4)
            for d, v in (c.pct_change().dropna() * 100).items():
                hist.setdefault(str(d.date()), {})[k] = round(float(v), 2)
            break
        except Exception as e:
            print("ERREUR", k, t, e)
json.dump({"updated": datetime.date.today().isoformat(), "px": px, "hist": hist}, open("data/prices.json", "w"))
print("OK", len(px), "actifs")
