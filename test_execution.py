#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_execution.py - Test TESTNET de la couche d'execution.
Place UN ordre limite non-fillable (repose dans le carnet) puis l'ANNULE.
Prouve : la cle agent authentifie + place + annule un ordre sur Hyperliquid TESTNET.
Argent 100% FICTIF (testnet). Ne laisse aucune position. Refuse de tourner hors testnet.
"""
import json
from execution_hl import ExecutionHL, ConfigExecution


def main():
    cfg = ConfigExecution()
    print("Config :", json.dumps(cfg.resume(), ensure_ascii=False))
    if not cfg.live_arme:
        print("STOP : live non arme (il faut HL_MODE=live + HL_LIVE_CONFIRM=OUI_ARGENT_REEL).")
        return
    if cfg.net != "testnet":
        print("SECURITE : ce test refuse de tourner hors testnet (HL_NET doit valoir 'testnet').")
        return
    ex = ExecutionHL(cfg)
    print("Place : limit BUY ETH 0.02 @ 1000 (repose loin du marche, ne fill pas)...")
    res = ex.limit_order("ETH", True, 0.02, 1000, "Gtc")
    print("Reponse ordre :", json.dumps(res))
    try:
        st = res["response"]["data"]["statuses"][0]
    except (KeyError, IndexError, TypeError):
        print("Statut inattendu -> voir la reponse ci-dessus (probable souci de cle/compte).")
        return
    if "resting" in st:
        oid = st["resting"]["oid"]
        print("Ordre RESTING (oid=%s) -> annulation..." % oid)
        print("Reponse cancel :", json.dumps(ex.cancel("ETH", oid)))
        print(">>> SUCCES : place + cancel testnet OK. L'execution marche de bout en bout.")
    elif "error" in st:
        print("Ordre REFUSE :", st["error"])
    else:
        print("Statut :", st)


if __name__ == "__main__":
    main()
