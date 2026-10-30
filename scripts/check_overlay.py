#!/usr/bin/env python3
"""Does JLCPCB's part land on our pads?  Place JLCPCB's own drawing of each part (scripts/easyeda.py) where the
rotation table and datum put it in our footprint's frame, and require every one of their pads' centres to lie inside
our pad of the same number (or, for a part numbered differently, inside one of our pads).

    python3 scripts/check_overlay.py [stem ...]        (default: every board)

check_rotations.py finds the turn by pad number and reports a residual but never fails on it, so a wrong package with
the right pin order passes: AMOD-A's PAM8302AASCR (C113367) is an MSOP-8 on our SOIC-8 footprint, fitted at +270 with
0.77 mm rms and reported ok; JLCPCB's placement preview showed its leads half-way between our pads (Prompt 22).
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import parts, easyeda
from sexp_parse import parse_file
from check_rotations import lcsc_of, turn, UNPOLAR

TOL = 0.05                  # mm a centre may stand outside our pad
OTHER_NUMBERING = {         # their pad numbers mean something else: positions only
    "C496549": "BWSMA-KE-Z001: their four posts are numbered apart from ours (all 2 on our side)",
    "C206667": "ADL5350: the footprint is JLCPCB's drawing with its pads renumbered to theirs",
    "C2297": "KT-0805G: numbered the other way round (read at 0 in GPiBridge's preview)",
    "C2296": "KT-0805Y: the KT-0805G's family drawing",
    "C2293": "KT-0805B: the KT-0805G's family drawing",
    "C474881": "KF301-2P: turned for its wire openings, their pin 1 in our hole 2",
    "C474882": "KF301-3P: turned for its wire-entry arrows, their pin 1 in our hole 3",
    "C13774": "HC-49S crystal: two pads, no polarity",
}


def footprints(stem):
    """{ref: (fpid, [(num, x, y, w, h, local angle, [polygons])])}, positions footprint-local; a custom pad's primitives
    (a SOT-89's tab is pad 2's) as polygons in the footprint's frame."""
    root = parse_file(os.path.join(ROOT, "hardware", stem + ".kicad_pcb"))
    out = {}
    for fp in root.kids("footprint"):
        at = fp.first("at")
        frot = float(at.atom(2)) if at.atom(2) else 0.0
        ref = next((pr.atom(1) for pr in fp.kids("property") if pr.atom(0) == "Reference"), None)
        pads = []
        for pd in fp.kids("pad"):
            pa, sz = pd.first("at"), pd.first("size")
            ang = (float(pa.atom(2)) if pa.atom(2) else 0.0) - frot
            x, y = float(pa.atom(0)), float(pa.atom(1))
            polys = []
            prim = pd.first("primitives")
            if prim is not None:
                for gp in prim.kids("gr_poly"):
                    pts = [(float(xy.atom(0)), float(xy.atom(1))) for xy in gp.first("pts").kids("xy")]
                    polys.append([(x + q[0], y + q[1]) for q in (turn(p, ang) for p in pts)])
            pads.append((pd.atom(0), x, y, float(sz.atom(0)), float(sz.atom(1)), ang, polys))
        out[ref] = (fp.atom(0), pads)
    return out


def inside(pt, poly):
    c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > pt[1]) != (y2 > pt[1]) and pt[0] < (x2 - x1) * (pt[1] - y1) / (y2 - y1) + x1:
            c = not c
    return c


def outside(pt, pad):
    """How far pt stands outside the pad: its anchor rectangle and any primitives (0 inside)."""
    num, x, y, w, h, ang, polys = pad
    if any(inside(pt, p) for p in polys):
        return 0.0
    dx, dy = turn((pt[0] - x, pt[1] - y), -ang)
    return math.hypot(max(abs(dx) - w / 2, 0.0), max(abs(dy) - h / 2, 0.0))


def main(stems):
    seen, bad, n = set(), [], 0
    for stem in stems:
        fps, codes = footprints(stem), lcsc_of(stem)
        for ref, (fpid, pads) in sorted(fps.items()):
            code = codes.get(ref)
            if not code or code in seen:
                continue
            seen.add(code)
            ours = [p for p in pads if p[0]]
            if len(ours) < 2 or (len(ours) == 2 and fpid.startswith(UNPOLAR)):
                continue
            lp, _ = easyeda.land_pattern(code)
            if not lp or not lp["pads"]:
                print("  ?     %-10s %-6s no drawing" % (code, ref))
                continue
            T = parts.JLC_ROTATION.get(code, (0,))[0]
            a = (360 - T) % 360                              # their drawing is our footprint turned by a
            dat = parts.JLC_DATUM.get(code, (0.0, 0.0))[:2]
            worst, where = 0.0, ""
            for q in lp["pads"]:
                p = turn((q["x"], q["y"]), -a)
                p = (p[0] + dat[0], p[1] + dat[1])
                same = [o for o in ours if o[0] == q["number"]] if code not in OTHER_NUMBERING else []
                d = min(outside(p, o) for o in (same or ours))
                if d > worst:
                    worst, where = d, "their pad %s" % q["number"]
            n += 1
            ok = worst <= TOL
            if not ok:
                bad.append((stem, ref, code))
            print("  %-5s %-10s %-7s %-7s %-46s %s" % ("ok" if ok else "FAIL", code, stem, ref, fpid[:46],
                  "every pad on ours" if ok else "%s stands %.2f mm outside our pad (%s)" % (where, worst, lp.get("package", ""))))
    print("\n%d codes overlaid; %d do not land on our pads" % (n, len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or list(parts.BOARDS)))
