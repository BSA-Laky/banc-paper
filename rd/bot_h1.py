import math
import statistics
from datetime import datetime

def _pct(sorted_vals, p):
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)

def step(marche, etat, now):
    trades = []
    try:
        if not isinstance(etat, dict):
            etat = {}
        hist = etat.get("_hist")
        if hist is None:
            hist = {}
            etat["_hist"] = hist
        pos = etat.get("_pos")
        if pos is None:
            pos = {}
            etat["_pos"] = pos
        MAXLEN = 400
        MINOBS = 40
        HOLD_H = 12.0
        FEE = 2 * 0.00035 * 100.0
        for coin, d in (marche or {}).items():
            try:
                if not isinstance(d, dict):
                    continue
                fund = float(d.get("funding", 0.0) or 0.0)
                mark = float(d.get("mark", 0.0) or 0.0)
                vol = float(d.get("vol", 0.0) or 0.0)
                if mark <= 0:
                    continue
                af = abs(fund)
                hl = hist.get(coin)
                if hl is None:
                    hl = []
                    hist[coin] = hl
                hl.append(af)
                if len(hl) > MAXLEN:
                    del hl[0:len(hl) - MAXLEN]
                sv = sorted(hl)
                p80 = _pct(sv, 0.80)
                p50 = _pct(sv, 0.50)
                have = coin in pos
                if not have:
                    if len(hl) >= MINOBS and p80 is not None and af >= p80 and af > 0 and vol > 0:
                        side = "short" if fund > 0 else "long"
                        pos[coin] = {"entry": mark, "ts": now.isoformat(), "side": side, "f0": fund}
                else:
                    p = pos[coin]
                    try:
                        t0 = datetime.fromisoformat(p.get("ts"))
                        hrs = (now - t0).total_seconds() / 3600.0
                    except Exception:
                        hrs = 0.0
                    exit_now = False
                    if p50 is not None and af <= p50:
                        exit_now = True
                    if hrs >= HOLD_H:
                        exit_now = True
                    if exit_now:
                        entry = float(p.get("entry", mark))
                        side = p.get("side", "short")
                        f0 = float(p.get("f0", fund))
                        # funding pnl: on encaisse le funding sur la duree, side contre le funding
                        # approx: taux horaire moyen ~ f0, applique sur heures detenues
                        avg_f = (f0 + fund) / 2.0
                        fund_pnl = abs(avg_f) * hrs * 100.0
                        # composante prix: si prix bouge contre nous cela reduit
                        if entry > 0:
                            pchg = (mark - entry) / entry
                        else:
                            pchg = 0.0
                        if side == "long":
                            price_pnl = pchg * 100.0
                        else:
                            price_pnl = -pchg * 100.0
                        pnl = fund_pnl + price_pnl - FEE
                        if pnl > 50.0:
                            pnl = 50.0
                        if pnl < -50.0:
                            pnl = -50.0
                        trades.append({"market": coin, "side": side, "size_usd": 100.0, "entry_price": entry, "pnl": pnl})
                        del pos[coin]
            except Exception:
                continue
    except Exception:
        return []
    return trades