#!/usr/bin/env python3
"""Print JLCPCB's shelf for a list of queries, one compact line per hit.

    python3 scripts/stock.py "MAX2871ETJ+T" "SMA-KE" ...      (cached by jlc_api.py, with the time)
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jlc_api


def line(h):
    p = h.get("componentPrices") or [{}]
    price = p[0].get("productPrice", 0)
    lib = {"base": "Basic", "expand": "Extended"}.get(h.get("componentLibraryType"), h.get("componentLibraryType"))
    pref = " pref" if h.get("preferredComponentFlag") else ""
    return "%-11s %-9s%s stock %7s  $%-8.4f %-28s %-14s %s" % (
        h.get("componentCode"), lib, pref, h.get("stockCount"), price, (h.get("componentModelEn") or "")[:28],
        (h.get("componentSpecificationEn") or "")[:14], (h.get("describe") or h.get("erpComponentName") or "")[:90])


def show(q, n=6):
    try:
        hits, ts = jlc_api.search(q, n)
    except Exception as e:
        print("== %s: ERROR %s" % (q, e)); return
    print("== %s (%d, %s)" % (q, len(hits), ts[:16]))
    for h in hits[:n]:
        print("   " + line(h))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    n = 6
    for q in args:
        show(q, n)
        time.sleep(0.25)
