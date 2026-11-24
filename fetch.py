import yfinance as yf, json, datetime
# Plusieurs tickers possibles pour une ligne : on essaie dans l'ordre jusqu'au premier qui marche.
T = {"SAF":"SAF.PA","SPX":"SXR8.DE","EM":["AMEM.DE","AEEM.PA"],"SXXP":"EXSA.DE","GOLD":"GOLD.PA",
     "BTC":"BTC-EUR","ETH":"ETH-EUR","XRP":"XRP-EUR","SOL":"SOL-EUR",
     "RNDR":"RENDER-USD","HBAR":"HBAR-USD","BABA":"9988.HK","AI":"AI.PA","LVMH":"MC.PA","AAPL":"AAPL","FLNC":"FLNC"}
CUR = {"RENDER-USD":"USD","HBAR-USD":"USD","AAPL":"USD","FLNC":"USD","9988.HK":"HKD"}
def close(t):
    c = yf.download(t, period="400d", progress=False, auto_adjust=True)["Close"].squeeze().dropna()
    if c.empty:
        raise ValueError("aucune donnee")
    return c
# On repart des anciennes données : si un ticker échoue ce soir, on garde son dernier cours (signalé dans "errors").
try:
    old = json.load(open("data/prices.json"))
except Exception:
    old = {}
px, asof, hist, errors = dict(old.get("px", {})), dict(old.get("asof", {})), old.get("hist", {}), []
fx = {"USD": close("EURUSD=X"), "HKD": close("EURHKD=X")}
for k, cands in T.items():
    ok = False
    for t in (cands if isinstance(cands, list) else [cands]):
        try:
            c = close(t)
            if t in CUR:
                c = c / fx[CUR[t]].reindex(c.index).ffill().bfill()
            px[k] = round(float(c.iloc[-1]), 4)
            asof[k] = str(c.index[-1].date())
            for d, v in (c.pct_change().dropna() * 100).items():
                hist.setdefault(str(d.date()), {})[k] = round(float(v), 2)
            ok = True
            break
        except Exception as e:
            print("ERREUR", k, t, e)
    if not ok:
        errors.append(k)
json.dump({"updated": datetime.date.today().isoformat(), "px": px, "asof": asof, "errors": errors, "hist": hist}, open("data/prices.json", "w"))
print("OK", len(px), "actifs, erreurs :", errors)
