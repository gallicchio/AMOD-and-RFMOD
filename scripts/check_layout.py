#!/usr/bin/env python3
"""Layout checks DRC cannot make, on the written board (run under KiCad's Python after DRC).

    check_layout.py STEM BOARD.kicad_pcb

1. No via's hole in, or touching, an SMD pad that is not an exposed or thermal pad.  The vias are tented and JLCPCB's
   economic assembly does not fill them, so a hole inside a pad's mask opening drinks that pad's solder: a starved or
   tombstoned joint.  Rev A's first release had ten, from wire ends dropped at pad edges (a12, m2, b2, r9, h4, h7, h10).
2. Every RF net's routed length against the shortest tree through its pads (CLAUDE_PCB.md gate 24, CostasLink rev A's
   LO TX MON tap: 115.6 mm for 12.3, 25.7 dB low at 5.8 GHz).  An RF-class net fails at 1.5x its tree and 10 mm extra;
   the nets on a jack's centre pin outside the class are printed.  DETOUR_OK lists the ones meant to be long.
"""
import math, re, sys
import pcbnew

MM = 1e-6
HOLE_MARGIN = 0.0                  # mm from a hole's edge to a pad's copper: a hole overlapping the pad fails
NEAR = 0.05                        # closer than this is printed (JLCPCB's mask registration)
JACK = re.compile(r"SMA|U\.FL|MMCX", re.I)
DETOUR_OK = {"/q9_LOOP": "q9's loop: the ODMR antenna is the track"}


def ring(pad, layer):
    sps = pad.GetEffectivePolygon(layer, pcbnew.ERROR_INSIDE)
    out = []
    for i in range(sps.OutlineCount()):
        o = sps.Outline(i)
        out.append([(o.CPoint(k).x * MM, o.CPoint(k).y * MM) for k in range(o.PointCount())])
    return out


def inside(pt, poly):
    x, y = pt
    c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def edge_dist(pt, poly):
    best = 1e9
    for (ax, ay), (bx, by) in zip(poly, poly[1:] + poly[:1]):
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy or 1e-12
        t = max(0.0, min(1.0, ((pt[0] - ax) * dx + (pt[1] - ay) * dy) / L2))
        best = min(best, math.hypot(ax + t * dx - pt[0], ay + t * dy - pt[1]))
    return best


def mst(pts):
    if len(pts) < 2:
        return 0.0
    d = {j: math.dist(pts[0], pts[j]) for j in range(1, len(pts))}
    tot = 0.0
    while d:
        j = min(d, key=d.get)
        tot += d.pop(j)
        for k in d:
            d[k] = min(d[k], math.dist(pts[j], pts[k]))
    return tot


def main(stem, path):
    b = pcbnew.LoadBoard(path)
    problems, notes = [], []
    # ---- 1. via holes in pads
    smd = []                                           # (pad, ref, polys) for every SMD pad that is not an exposed pad
    for f in b.GetFootprints():
        pads = [p for p in f.Pads() if p.GetNumber() and (p.IsOnLayer(pcbnew.F_Cu) or p.IsOnLayer(pcbnew.B_Cu))]
        polys = [ring(p, pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu) for p in pads]
        area = [sum(abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(q, q[1:] + q[:1]))) / 2 for q in pl) for pl in polys]
        a = sorted(area) or [0]
        med = a[len(a) // 2]
        big = {p.GetNumber() for p, ar in zip(pads, area) if len(pads) >= 3 and ar >= 2.5 * med}       # exposed pads and tabs: vias meant
        for p, pl in zip(pads, polys):
            if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or p.GetNumber() in big:
                continue
            smd.append((p, f.GetReference(), pl))
    nv, near = 0, []
    for t in b.GetTracks():
        if t.GetClass() != "PCB_VIA":
            continue
        nv += 1
        v = (t.GetPosition().x * MM, t.GetPosition().y * MM)
        r = t.GetDrillValue() * MM / 2
        for p, ref, polys in smd:
            c = (p.GetPosition().x * MM, p.GetPosition().y * MM)
            if abs(c[0] - v[0]) > 3 or abs(c[1] - v[1]) > 3:
                continue
            for poly in polys:
                d = -edge_dist(v, poly) if inside(v, poly) else edge_dist(v, poly)
                if HOLE_MARGIN <= d - r < NEAR:
                    near.append("%s.%s %.2f" % (ref, p.GetNumber(), d - r))
                if d < r + HOLE_MARGIN:
                    problems.append("%s: the via at (%.2f, %.2f) on %s has its hole %s %s pad %s (%.2f mm from the pad's edge to "
                                    "the hole's; %.2f wanted)" % (stem, v[0], v[1], t.GetNetname(), "in" if d < r else "against",
                                                                   ref, p.GetNumber(), d - r, HOLE_MARGIN))
    if not problems:
        notes.append("%s: %d vias, none with its hole in an SMD pad (exposed pads aside)" % (stem, nv))
    if near:
        notes.append("%s: holes within %.2f mm of a pad's edge, outside it: %s" % (stem, NEAR, ", ".join(sorted(near))))
    # ---- 2. RF detours
    length, padsxy, rf, jack = {}, {}, set(), set()
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            continue
        length[t.GetNetname()] = length.get(t.GetNetname(), 0.0) + t.GetLength() * MM
    for f in b.GetFootprints():
        for p in f.Pads():
            n = p.GetNetname()
            padsxy.setdefault(n, []).append((p.GetPosition().x * MM, p.GetPosition().y * MM))
            if JACK.search(f.GetFPIDAsString()) and p.GetNumber() == "1":
                jack.add(n)
    for n, ni in b.GetNetsByName().items():
        if ni.GetNetClassName() == "RF":
            rf.add(str(n))
    worst = []
    for n in sorted(rf | jack):
        tl = length.get(n, 0.0)
        tree = mst(padsxy.get(n, []))
        if tl <= 0 or tree <= 0:
            continue
        worst.append((tl / tree, n))
        if tl / tree > 1.5 and tl - tree > 10:
            if n in DETOUR_OK:
                notes.append("%s: %s routed %.1f mm for a %.1f mm tree, as meant (%s)" % (stem, n, tl, tree, DETOUR_OK[n]))
            elif n in rf:
                problems.append("%s: RF net %s is routed %.1f mm for a %.1f mm tree through its pads (%.1fx)" % (stem, n, tl, tree, tl / tree))
            else:
                notes.append("%s: %s (a jack's net outside the RF class) is routed %.1f mm for a %.1f mm tree" % (stem, n, tl, tree))
    if worst:
        r, n = max(worst)
        notes.append("%s: %d RF and jack nets measured against their pads' trees; the most roundabout %s at %.2fx" % (stem, len(worst), n, r))
    for s in notes:
        if s:
            print("  ok   " + s)
    for s in problems:
        print("  FAIL " + s)
    print("  layout checks: %s" % ("passed" if not problems else "%d problem(s)" % len(problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
