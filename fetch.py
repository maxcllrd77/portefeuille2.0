import yfinance as yf, json, datetime, os, urllib.request, urllib.parse
# Plusieurs tickers possibles pour une ligne : on essaie dans l'ordre jusqu'au premier qui marche.
T = {"SAF":"SAF.PA","SPX":"SXR8.DE","EM":["AMEM.DE","AEEM.PA"],"SXXP":"EXSA.DE","GOLD":"GOLD.PA",
     "BTC":"BTC-EUR","ETH":"ETH-EUR","XRP":"XRP-EUR","SOL":"SOL-EUR",
     "RNDR":"RENDER-USD","HBAR":"HBAR-USD","BABA":"9988.HK","AI":"AI.PA","LVMH":"MC.PA","AAPL":"AAPL","FLNC":"FLNC"}
CUR = {"RENDER-USD":"USD","HBAR-USD":"USD","AAPL":"USD","FLNC":"USD","9988.HK":"HKD"}
def news(t):
    out = []
    try:
        for n in (yf.Ticker(t).news or [])[:3]:
            c = n.get("content", n)
            link = (c.get("canonicalUrl") or c.get("clickThroughUrl") or {}).get("url") or c.get("link")
            src = (c.get("provider") or {}).get("displayName") or c.get("publisher", "")
            d = (c.get("pubDate") or "")[:10]
            if not d and c.get("providerPublishTime"):
                d = datetime.date.fromtimestamp(c["providerPublishTime"]).isoformat()
            if c.get("title") and link:
                out.append({"t": c["title"], "l": link, "s": src, "d": d})
    except Exception as e:
        print("NEWS", t, e)
    return out
STOCKS = ["SAF","AI","LVMH","AAPL","FLNC","BABA"]
SEUIL_JOUR = 6.0  # alerte Telegram si un cours bouge de plus de X % en un jour
def events(t):
    out = []
    try:
        cal = yf.Ticker(t).calendar
        cal = cal if isinstance(cal, dict) else {}
        for key, lab in [("Earnings Date", "Resultats"), ("Ex-Dividend Date", "Detachement du dividende"), ("Dividend Date", "Paiement du dividende")]:
            v = cal.get(key)
            if v is None:
                continue
            for d in (v if isinstance(v, (list, tuple)) else [v]):
                out.append({"d": str(d)[:10], "t": lab})
    except Exception as e:
        print("CAL", t, e)
    return out
def notify(msg):
    tok, cid = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not (tok and cid):
        return
    try:
        urllib.request.urlopen("https://api.telegram.org/bot%s/sendMessage" % tok, urllib.parse.urlencode({"chat_id": cid, "text": msg}).encode(), timeout=20)
    except Exception as e:
        print("TELEGRAM", e)
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
nw, cal = {}, {}
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
            nw[k] = news(t)
            if k in STOCKS:
                cal[k] = events(t)
            ok = True
            break
        except Exception as e:
            print("ERREUR", k, t, e)
    if not ok:
        errors.append(k)
json.dump({"updated": datetime.date.today().isoformat(), "px": px, "asof": asof, "errors": errors, "hist": hist}, open("data/prices.json", "w"))
json.dump(nw, open("data/news.json", "w"))
json.dump(cal, open("data/calendar.json", "w"))
if hist:
    last = max(hist)
    big = ["%s %+.1f %%" % (k, v) for k, v in hist[last].items() if abs(v) >= SEUIL_JOUR]
    if big or errors:
        notify("Portefeuille %s\n" % last + ("Gros mouvements : " + ", ".join(big) + "\n" if big else "") + ("Cours non mis a jour : " + ", ".join(errors) if errors else ""))
print("OK", len(px), "actifs, erreurs :", errors)
