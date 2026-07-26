import math, statistics, datetime

def step(marche, etat, now):
    fermes = []
    try:
        if not isinstance(etat, dict):
            etat = {}
        hist = etat.get('_fh')
        if not isinstance(hist, list):
            hist = []
        # collecte funding courant de tous les coins pour l'historique roulant
        cur = []
        for c, d in marche.items():
            try:
                f = float(d.get('funding', 0.0))
                cur.append(f)
            except Exception:
                pass
        for f in cur:
            hist.append(f)
        # fenetre bornee
        if len(hist) > 4000:
            hist = hist[-4000:]
        etat['_fh'] = hist

        def pct(sorted_list, q):
            if not sorted_list:
                return None
            k = (len(sorted_list) - 1) * q
            lo = int(math.floor(k))
            hi = int(math.ceil(k))
            if lo == hi:
                return sorted_list[lo]
            return sorted_list[lo] * (hi - k) + sorted_list[hi] * (k - lo)

        pos_vals = sorted([x for x in hist if x > 0])
        neg_vals = sorted([x for x in hist if x < 0])
        p80 = pct(pos_vals, 0.80) if len(pos_vals) >= 40 else None
        p20 = pct(neg_vals, 0.20) if len(neg_vals) >= 40 else None
        med = statistics.median(hist) if len(hist) >= 40 else None

        # --- gestion des sorties ---
        for c in list(etat.keys()):
            if c.startswith('_'):
                continue
            p = etat.get(c)
            if not isinstance(p, dict):
                continue
            d = marche.get(c)
            if d is None:
                continue
            try:
                mark = float(d.get('mark', 0.0))
                ret = float(d.get('ret24h', 0.0))
                fund = float(d.get('funding', 0.0))
                entry = float(p.get('entry', mark))
                side = p.get('side', 'short')
                ts = p.get('ts')
                t0 = datetime.datetime.fromisoformat(ts)
                elapsed_h = (now - t0).total_seconds() / 3600.0
            except Exception:
                etat.pop(c, None)
                continue
            close = False
            if med is not None:
                if side == 'short' and ret <= med:
                    close = True
                if side == 'long' and ret >= med:
                    close = True
            if elapsed_h >= 8.0:
                close = True
            if close and entry > 0:
                size = 100.0
                # pnl prix
                if side == 'short':
                    price_pnl = (entry - mark) / entry * size
                else:
                    price_pnl = (mark - entry) / entry * size
                # funding gagne/paye pendant la detention (approx: funding courant * heures)
                # short encaisse funding positif ; long encaisse funding negatif
                fund_pnl = 0.0
                try:
                    if side == 'short':
                        fund_pnl = fund * elapsed_h * size
                    else:
                        fund_pnl = -fund * elapsed_h * size
                except Exception:
                    fund_pnl = 0.0
                pnl = price_pnl + fund_pnl - 2 * 0.00035 * size
                cap = 0.5 * size
                if pnl > cap:
                    pnl = cap
                if pnl < -cap:
                    pnl = -cap
                fermes.append({'market': c, 'side': side, 'size_usd': size, 'entry_price': entry, 'pnl': pnl})
                etat.pop(c, None)

        # --- entree : un seul coin, le plus extreme ---
        if p80 is not None and p20 is not None:
            best = None
            best_score = 0.0
            best_side = None
            for c, d in marche.items():
                try:
                    if c in etat:
                        continue
                    fund = float(d.get('funding', 0.0))
                    ret = float(d.get('ret24h', 0.0))
                    mark = float(d.get('mark', 0.0))
                    if mark <= 0:
                        continue
                except Exception:
                    continue
                if fund >= p80 and ret > 0:
                    sc = fund - p80
                    if sc > best_score:
                        best_score = sc; best = c; best_side = 'short'
                elif fund <= p20 and ret < 0:
                    sc = p20 - fund
                    if sc > best_score:
                        best_score = sc; best = c; best_side = 'long'
            if best is not None:
                try:
                    mk = float(marche[best].get('mark', 0.0))
                    if mk > 0:
                        etat[best] = {'entry': mk, 'side': best_side, 'ts': now.isoformat()}
                except Exception:
                    pass
    except Exception:
        return fermes
    return fermes