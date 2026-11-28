import yfinance as yf, json, datetime, time, math

def num(x):
    try:
        x = float(x)
        return None if math.isnan(x) or math.isinf(x) else round(x, 4)
    except Exception:
        return None

def to_date(v):
    try:
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return datetime.datetime.utcfromtimestamp(v).date().isoformat()
        return str(v)[:10]
    except Exception:
        return None

today = datetime.date.today()

CAC = "AI.PA AIR.PA ALO.PA BN.PA BNP.PA CA.PA CAP.PA CS.PA DG.PA DSY.PA EL.PA EN.PA ENGI.PA ERF.PA GLE.PA HO.PA KER.PA LR.PA MC.PA ML.PA OR.PA ORA.PA PUB.PA RI.PA RMS.PA RNO.PA SAF.PA SAN.PA SGO.PA STMPA.PA SU.PA TEP.PA TTE.PA VIE.PA VIV.PA".split()
SBF = "ACA.PA ATO.PA AF.PA AKE.PA BVI.PA BOL.PA DIM.PA ETL.PA FDJ.PA FGR.PA FR.PA GFC.PA IPN.PA IPS.PA MERY.PA NEX.PA RCO.PA RXL.PA SESG.PA SK.PA SOP.PA SW.PA TE.PA TFI.PA UBI.PA VK.PA VIRP.PA COV.PA EDEN.PA ELIS.PA ERA.PA EXA.PA TRI.PA AMUN.PA NK.PA CLARI.PA SPIE.PA".split()
EURO = "ASML.AS ADYEN.AS PRX.AS INGA.AS SAP.DE SIE.DE ALV.DE MBG.DE BMW.DE VOW3.DE DTE.DE BAS.DE ADS.DE IFX.DE MUV2.DE RMS.PA NESN.SW ROG.SW NOVN.SW NVO SHEL.L AZN.L HSBA.L ULVR.L BP.L RIO.L DGE.L GSK.L ENEL.MI ISP.MI RACE.MI SAN.MC ITX.MC IBE.MC TSM BABA 0700.HK 9988.HK 7203.T 005930.KS".split()
US_FALLBACK = "AAPL MSFT NVDA GOOGL AMZN META TSLA AVGO AMD NFLX JPM V MA JNJ PG KO PEP XOM WMT COST UNH LLY CRM ADBE ORCL INTC DIS NKE MCD DELL HPQ HPE ADSK WDAY CRWD ZS MRVL ZM DE FLNC BA CAT GE HD LOW PFE MRK ABBV TMO ABT CVX BAC WFC C GS MS T VZ CMCSA QCOM TXN IBM NOW PANW SNOW UBER ABNB PYPL SHOP SQ COIN PLTR".split()

tickers = []
def add(lst):
    for t in lst:
        t = t.strip()
        if t and t not in tickers:
            tickers.append(t)

add(CAC); add(SBF); add(EURO)
try:
    import pandas as pd
    sp = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]["Symbol"].tolist()
    add([s.replace(".", "-") for s in sp])
    print("S&P 500 :", len(sp))
except Exception as e:
    print("S&P 500 indisponible, liste reduite", e)
    add(US_FALLBACK)
try:
    for l in open("tickers.txt", encoding="utf-8"):
        l = l.strip()
        if l and not l.startswith("#"):
            add([l])
except Exception:
    pass

KEEP_HIST = {"SAF.PA", "MC.PA", "AI.PA", "AAPL", "BABA", "FLNC"}  # historique conserve (secours si le reseau du navigateur echoue)
out = {}
for t in tickers:
    try:
        tk = yf.Ticker(t)
        info = tk.info or {}
        price = num(info.get("currentPrice")) or num(info.get("regularMarketPrice"))
        if price is None and not info.get("shortName"):
            continue
        ned = to_date(info.get("earningsTimestamp") or info.get("earningsTimestampStart"))
        if ned and ned < today.isoformat():
            ned = None
        e = {"n": info.get("shortName") or info.get("longName") or t, "cur": info.get("currency"),
             "sec": info.get("sector"), "ind": info.get("industry"),
             "f": {"price": price, "pe": num(info.get("trailingPE")), "fpe": num(info.get("forwardPE")),
                   "roe": num(info.get("returnOnEquity")), "om": num(info.get("operatingMargins")),
                   "rg": num(info.get("revenueGrowth")), "eg": num(info.get("earningsGrowth")),
                   "de": num(info.get("debtToEquity")), "cr": num(info.get("currentRatio")),
                   "dyr": num(info.get("dividendRate")), "pr": num(info.get("payoutRatio")),
                   "rec": num(info.get("recommendationMean")), "tgt": num(info.get("targetMeanPrice")),
                   "tlo": num(info.get("targetLowPrice")), "thi": num(info.get("targetHighPrice")),
                   "nan": num(info.get("numberOfAnalystOpinions")),
                   "fcf": num(info.get("freeCashflow")), "sh": num(info.get("sharesOutstanding")),
                   "mc": num(info.get("marketCap")), "beta": num(info.get("beta")),
                   "ned": ned, "exd": to_date(info.get("exDividendDate")), "dvd": to_date(info.get("dividendDate"))}}
        if t in KEEP_HIST:
            c = yf.download(t, period="1y", progress=False, auto_adjust=False)["Close"].squeeze().dropna()
            e["d"] = [str(x.date()) for x in c.index]
            e["p"] = [round(float(x), 2) for x in c.values]
        out[t] = e
    except Exception as ex:
        print("ERREUR", t, ex)
    time.sleep(0.15)

json.dump({"updated": today.isoformat(), "s": out}, open("data/stocks.json", "w", encoding="utf-8"),
          ensure_ascii=False, separators=(",", ":"))
print("OK", len(out), "entreprises sur", len(tickers))
