"""CLAUDE_PCB.md's RF layout gates measured on the written board (2026-10-29, before rev A's order).

    python3 scripts/rf_survey.py STEM [fmax_GHz]      after: rf_extract.py hardware/STEM.kicad_pcb out/STEM_rfgeo.json

Prints, from the board file's copper (scripts/rf_extract.py): vias in SMD pads; the RF class against the nets on jacks'
centre pins and the nets named RF/LO; gate 24's detours; gates 26/27, each shunt part on an RF net with its branch off
the line, its track to the nearest IC pin (and in degrees at fmax) and its ground pad's distance to a via; gate 28, each
bias choke's cold end and its nearest capacitor; gate 30, the top pour's distance to a ground via near the RF lines; and
gate 32, each RF line's widths, gap to the pour, inner-layer ground under it (outside the jacks' launch voids) and fence
vias per mm.  It measures and flags; it fails nothing (scripts/check_layout.py is the build's gate).  The RF set grows
from the RF class and the jacks' nets through series parts (C, R up to 300 ohm, L that is not a choke)."""
import os
import json, math, sys, collections, heapq, re
import numpy as np
from matplotlib.path import Path
from scipy.spatial import cKDTree

stem = sys.argv[1]
FMAX = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
D = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "%s_rfgeo.json" % stem)))
DEG_PER_MM = 12.0 * FMAX / 5.8          # CLAUDE_PCB.md: 12 degrees per mm of 50 ohm CPWG at 5.8 GHz on JLC04161H-7628
LAM = 300.0 / FMAX / math.sqrt(4.4)     # wavelength in FR4, mm
fp = {f["ref"]: f for f in D["fps"]}
pads = D["pads"]
NC = D["netclass"]
JACK = re.compile(r"SMA|U\.FL|MMCX", re.I)
POWER = re.compile(r"^(GND|\+|-|/VMOT|/VMB|/PMOD_VCC)")
def is_power(n): return bool(POWER.match(n or ""))

def path_of(poly):
    verts, codes = [], []
    for ring in [poly["ring"]] + poly["holes"]:
        if len(ring) < 3: continue
        verts += ring + [ring[0]]
        codes += [Path.MOVETO] + [Path.LINETO] * (len(ring) - 1) + [Path.CLOSEPOLY]
    return Path(np.array(verts), codes)
for p in pads:
    p["path"] = [path_of(q) for q in p["poly"]] if p["poly"] else []
def in_pad(p, pts, r=0.0):
    pts = np.atleast_2d(pts)
    res = np.zeros(len(pts), bool)
    for P in p["path"]:
        res |= P.contains_points(pts, radius=r) | P.contains_points(pts, radius=-r)
    return res

print("=" * 100)
print("%s  (fmax %.1f GHz: %.1f deg/mm, lambda/50 = %.2f mm, lambda/20 = %.2f mm in FR4)" % (stem, FMAX, DEG_PER_MM, LAM / 50, LAM / 20))

# ---------------------------------------------------------------- via in pad (solder wicking at assembly)
pad_by_net = collections.defaultdict(list)
for p in pads: pad_by_net[p["net"]].append(p)
vip = []
for v in D["vias"]:
    x, y, size, drill, net = v
    for p in pad_by_net.get(net, []):
        if p["attr"] != 1 or not p["path"]:      # SMD pads only
            continue
        if abs(p["x"] - x) > 6 or abs(p["y"] - y) > 6:
            continue
        if in_pad(p, (x, y), drill / 2 + 0.05)[0]:  # the hole reaches into the pad's (mask) opening
            area = p["size"][0] * p["size"][1] if p["size"] else 0
            vip.append((p["ref"], p["num"], net, area, fp[p["ref"]]["fpid"].split(":")[1], x, y))
small = [z for z in vip if z[3] < 1.5]
print("\n[via in pad] %d vias with their hole in an SMD pad; %d of them in pads under 1.5 mm2 (not exposed pads):" % (len(vip), len(small)))
for z in sorted(small):
    print("   %-7s pad %-3s %-14s %.2f mm2  %-40s via at (%.2f, %.2f)" % z)

# ---------------------------------------------------------------- net graph
segs = collections.defaultdict(list)
for s in D["segs"]:
    segs[s[6]].append(s)
def key(x, y): return (round(x, 3), round(y, 3))
def graph(net):
    G = collections.defaultdict(dict)
    def add(a, b, L):
        if a == b: return
        if b not in G[a] or G[a][b] > L:
            G[a][b] = L; G[b][a] = L
    ends = []
    for s in segs.get(net, []):
        a, b = key(s[0], s[1]), key(s[2], s[3])
        add(a, b, math.dist(a, b)); ends += [a, b]
    # T-junctions where an end lands mid-segment
    for s in segs.get(net, []):
        a, b = np.array(s[:2]), np.array(s[2:4]); d = b - a; L2 = d @ d
        if L2 < 1e-9: continue
        for e in set(ends):
            t = ((np.array(e) - a) @ d) / L2
            if 1e-3 < t < 1 - 1e-3 and np.linalg.norm(a + t * d - e) < s[4] / 2:
                add(e, key(*a), math.dist(e, a)); add(e, key(*b), math.dist(e, b))
    for p in pad_by_net.get(net, []):
        pk = ("pad", p["ref"], p["num"])
        ue = list(set(ends))
        if ue and p["path"]:
            m = in_pad(p, np.array(ue), 0.01)
            for e, hit in zip(ue, m):
                if hit: add(pk, e, math.dist(e, (p["x"], p["y"])))
    return G
def dijkstra(G, srcs):
    dist = {s: 0.0 for s in srcs}; prev = {}
    h = [(0.0, i, s) for i, s in enumerate(srcs)]; c = len(h)
    while h:
        d, _, u = heapq.heappop(h)
        if d > dist.get(u, 1e9): continue
        for v, L in G[u].items():
            nd = d + L
            if nd < dist.get(v, 1e9):
                dist[v] = nd; prev[v] = u; c += 1; heapq.heappush(h, (nd, c, v))
    return dist, prev

def mst(pts):
    if len(pts) < 2: return 0.0
    d = {j: math.dist(pts[0], pts[j]) for j in range(1, len(pts))}; tot = 0.0
    while d:
        j = min(d, key=d.get); tot += d.pop(j)
        for k in d: d[k] = min(d[k], math.dist(pts[j], pts[k]))
    return tot

# ---------------------------------------------------------------- RF nets
rf = set()
for n, c in NC.items():
    if c == "RF": rf.add(n)
jacknets = set()
for p in pads:
    if JACK.search(fp[p["ref"]]["fpid"]) and p["num"] == "1" and p["net"] and not is_power(p["net"]):
        jacknets.add(p["net"])
named = {n for n in NC if re.search(r"(^|[/_(-])(RF|LO)", n) and not is_power(n)}
def ohms(v):
    m = re.match(r"([0-9.]+)\s*([pnumkKMR]?)", v or "")
    if not m: return None
    x = float(m.group(1)); u = m.group(2)
    return x * {"": 1, "R": 1, "k": 1e3, "K": 1e3, "M": 1e6}.get(u, None) if u in ("", "R", "k", "K", "M") else None
def henries(v):
    m = re.match(r"([0-9.]+)\s*([pnu])", v or "")
    return float(m.group(1)) * {"p": 1e-12, "n": 1e-9, "u": 1e-6}[m.group(2)] if m else None
twoA = collections.defaultdict(list)
for p in pads: twoA[p["ref"]].append(p)
def gnd_cap_on(net):
    for p in pad_by_net.get(net, []):
        if p["ref"].startswith("C") and len(twoA[p["ref"]]) == 2 and any(q["net"] == "GND" for q in twoA[p["ref"]] if q is not p):
            return True
    return False
def is_choke(ref, other):
    if ref[0] not in "LF": return False
    if ref[0] == "F": return True
    h = henries(fp[ref]["value"])
    return is_power(other) or (h is not None and h >= 20e-9 and gnd_cap_on(other) and other not in jacknets)
seed = rf | jacknets
grown = set(seed)
while True:
    add = set()
    for ref, pp in twoA.items():
        if len(pp) != 2: continue
        a, b = pp
        for x, y in ((a, b), (b, a)):
            if x["net"] in grown and y["net"] not in grown and y["net"] and not is_power(y["net"]):
                k = ref[0]
                if k == "C" or (k == "R" and (ohms(fp[ref]["value"]) or 1e9) <= 300) or (k == "L" and not is_choke(ref, y["net"])):
                    add.add(y["net"])
    if not add: break
    grown |= add
print("   joined through series parts (no class of their own): " + ", ".join(sorted(n for n in grown - seed if segs.get(n) or True)))

print("\n[RF net class] %d nets in the RF class; %d nets on a jack's centre pin; %d named RF/LO" % (len(rf), len(jacknets), len(named)))
for n in sorted((jacknets | named) - rf):
    if not segs.get(n): continue
    tl = sum(math.dist(s[:2], s[2:4]) for s in segs[n])
    ws = sorted({round(s[4], 3) for s in segs[n]})
    print("   not RF class: %-28s class %-8s %5.1f mm of track, widths %s, pads %s" % (n, NC.get(n), tl, ws,
          ", ".join("%s.%s" % (p["ref"], p["num"]) for p in pad_by_net[n])))

# ---------------------------------------------------------------- gate 24 detours
print("\n[gate 24] nets over 2x their pads' tree and 15 mm, and RF nets over 1.5x and 10 mm extra (FAIL):")
nfail = 0
for n, ss in sorted(segs.items()):
    if is_power(n) or not n: continue
    tl = sum(math.dist(s[:2], s[2:4]) for s in ss)
    tree = mst([(p["x"], p["y"]) for p in pad_by_net.get(n, [])])
    if tree <= 0: continue
    r = tl / tree
    isrf = n in grown
    bad = isrf and r > 1.5 and tl - tree > 10
    if bad or (r > 2 and tl > 15):
        nfail += bad
        print("   %s %-32s %5.2fx  %6.1f mm for %5.1f%s" % ("FAIL" if bad else "    ", n, r, tl, tree, "  (RF)" if isrf else ""))
print("   %d RF detour failures" % nfail)

# ---------------------------------------------------------------- gates 26 and 27: shunt parts on RF nets
gnd_vias = np.array([(v[0], v[1]) for v in D["vias"] if v[4] == "GND"] + [(p["x"], p["y"]) for p in pads if p["net"] == "GND" and p["drill"][0] > 0])
gtree = cKDTree(gnd_vias) if len(gnd_vias) else None
def ic_pad(p):
    f = fp[p["ref"]]
    npads = sum(1 for q in pads if q["ref"] == p["ref"])
    return npads >= 3 and not JACK.search(f["fpid"])
rows = []
two = collections.defaultdict(list)
for p in pads:
    two[p["ref"]].append(p)
for n in sorted(grown):
    G = graph(n)
    terms, shunts = [], []
    for p in pad_by_net[n]:
        others = [q for q in two[p["ref"]] if q is not p and q["net"] != n]
        is2 = len(two[p["ref"]]) == 2
        if is2 and others and (others[0]["net"] == "GND" or is_power(others[0]["net"]) or others[0]["net"] not in grown):
            shunts.append((p, others[0]))
        else:
            terms.append(p)
    tk = [("pad", p["ref"], p["num"]) for p in terms if ("pad", p["ref"], p["num"]) in G]
    trunk = set(tk)
    for i, s in enumerate(tk):
        dist, prev = dijkstra(G, [s])
        for t in tk[i + 1:]:
            u = t
            while u in prev:
                trunk.add(u); u = prev[u]
    ics = [("pad", p["ref"], p["num"]) for p in terms if ic_pad(p) and ("pad", p["ref"], p["num"]) in G]
    dic, _ = dijkstra(G, ics) if ics else ({}, {})
    for p, o in shunts:
        pk = ("pad", p["ref"], p["num"])
        if pk not in G:
            # no track: the part sits on a pad of the trunk directly (pads overlap) or is unrouted
            branch = 0.0 if any(in_pad(q, (p["x"], p["y"]), 1.0)[0] for q in terms) else float("nan")
            toic = float("nan")
        else:
            dt, _ = dijkstra(G, [pk])
            branch = min((dt[u] for u in trunk if u in dt), default=float("nan"))
            toic = dic.get(pk, float("nan"))
        kind = "gnd" if o["net"] == "GND" else ("rail" if is_power(o["net"]) else ("choke" if is_choke(p["ref"], o["net"]) else "bias"))
        gd = float("nan")
        if kind == "gnd" and gtree is not None:
            # the ground pad's nearest via, from the pad's edge (0 = in or touching it)
            d, i = gtree.query((o["x"], o["y"]), k=6)
            best = 9.9
            for dd, ii in zip(np.atleast_1d(d), np.atleast_1d(i)):
                vx, vy = gnd_vias[ii]
                if in_pad(o, (vx, vy), 0.0)[0]: best = 0.0; break
                for r in np.arange(0.05, 3.0, 0.05):
                    if in_pad(o, (vx, vy), r)[0]:
                        best = min(best, r); break
            gd = best
        rows.append((n, p["ref"], fp[p["ref"]]["value"], kind, o["net"], branch, toic, gd))
print("\n[gate 26/27] shunt parts on RF nets: branch off the line, track to the nearest IC pin (deg at fmax), ground pad to its via")
print("   %-26s %-7s %-10s %-4s %-18s %7s %7s %6s %7s" % ("net", "part", "value", "to", "other net", "branch", "to IC", "deg", "gnd via"))
for (n, ref, val, kind, on, br, ti, gd) in rows:
    flag = []
    if br == br and br > 0.3: flag.append("BRANCH")
    if ref[0] in "CL" and kind == "gnd" and ti == ti and ti > LAM / 50: flag.append(">lambda/50")
    if kind in ("rail", "choke", "bias") and ti == ti and ti > 1.0: flag.append(">1mm")
    if kind == "gnd" and gd == gd and gd > 0.3: flag.append("GND>0.3")
    print("   %-26s %-7s %-10s %-4s %-18s %7.2f %7.2f %6.0f %7.2f  %s" % (n[:26], ref, val[:10], kind, on[:18], br, ti, ti * DEG_PER_MM if ti == ti else float("nan"), gd, " ".join(flag)))

# ---------------------------------------------------------------- gate 28: chokes and ferrites into rails
print("\n[gate 28] inductors/beads with one pad on an RF net: the cold end's nearest capacitor to ground, and vias before it")
caps = [p for p in pads if p["ref"].startswith("C") and len(two[p["ref"]]) == 2]
for (n, ref, val, kind, on, br, ti, gd) in rows:
    if kind != "choke": continue
    cold = next(q for q in two[ref] if q["net"] == on)
    near = []
    for c in caps:
        if c["net"] == on and any(q["net"] == "GND" for q in two[c["ref"]] if q is not c):
            near.append((math.dist((c["x"], c["y"]), (cold["x"], cold["y"])), c["ref"], fp[c["ref"]]["value"]))
    near.sort()
    vias = sorted(math.dist((v[0], v[1]), (cold["x"], cold["y"])) for v in D["vias"] if v[4] == on)
    print("   %-7s %-8s on %-22s cold net %-16s nearest caps: %s; nearest via on the cold net %.2f mm" % (
        ref, val, n[:22], on[:16], ", ".join("%s %s %.2f mm" % (r, v, d) for d, r, v in near[:2]) or "none", vias[0] if vias else float("nan")))

# ---------------------------------------------------------------- gates 30 and 32 (RF nets on F.Cu)
fills = collections.defaultdict(list)
for f in D["fills"]:
    for q in f["polys"]:
        fills[(f["layer"], f["net"])].append(path_of(q))
def inside_any(paths, pts):
    res = np.zeros(len(pts), bool)
    for P in paths:
        bb = P.get_extents()
        m = (pts[:, 0] >= bb.x0) & (pts[:, 0] <= bb.x1) & (pts[:, 1] >= bb.y0) & (pts[:, 1] <= bb.y1)
        if m.any():
            idx = np.where(m)[0]
            res[idx] |= P.contains_points(pts[idx])
    return res
rfsegs = [s for s in D["segs"] if s[6] in grown and s[5] == "F.Cu"]
top = fills.get(("F.Cu", "GND"), [])
if rfsegs and top and gtree is not None:
    # gate 30: pour points within 10 mm of an RF line, distance to the nearest ground via
    step = 0.25
    xs = np.arange(0, 100, step) + step / 2
    pts = np.array([(x, y) for x in xs for y in xs])
    on = inside_any(top, pts)
    sp = []
    for s in rfsegs:
        L = math.dist(s[:2], s[2:4]); k = max(2, int(L / 0.2))
        t = np.linspace(0, 1, k)
        sp += list(np.c_[s[0] + (s[2] - s[0]) * t, s[1] + (s[3] - s[1]) * t])
    rt = cKDTree(np.array(sp))
    near = on & (rt.query(pts)[0] <= 10)
    far = on & ~near
    dn = gtree.query(pts[near])[0]; dfar = gtree.query(pts[far])[0] if far.any() else np.array([0])
    print("\n[gate 30] top pour within 10 mm of RF lines: nearest ground via median %.2f, 95%% %.2f, max %.2f mm; %.0f%% beyond lambda/20 (%.2f mm)" % (
        np.median(dn), np.percentile(dn, 95), dn.max(), 100 * (dn > LAM / 20).mean(), LAM / 20))
    print("          elsewhere: max %.2f mm, %.1f%% beyond lambda/6 (%.2f mm)" % (dfar.max(), 100 * (dfar > LAM / 6).mean(), LAM / 6))
    # worst spots
    worst = np.argsort(-dn)[:5]
    print("          worst near-RF spots: " + ", ".join("(%.1f, %.1f) %.1f mm" % (*pts[near][i], dn[i]) for i in worst))
    # gate 32: per RF net, width vs class, gap to top pour, In1 ground under, fence vias/mm
    edges = []
    for P in top:
        v = P.vertices
        for a, b in zip(v[:-1], v[1:]):
            L = math.dist(a, b); k = max(1, int(L / 0.02))
            t = np.linspace(0, 1, k, endpoint=False)
            edges += list(np.c_[a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t])
    et = cKDTree(np.array(edges))
    in1 = fills.get(("In1.Cu", "GND"), [])
    print("\n[gate 32] RF lines on F.Cu: width, gap to the top pour (median, 5th pct), In1 ground under, fence vias per mm on runs over 2 mm")
    bad32 = 0
    for n in sorted({s[6] for s in rfsegs}):
        ss = [s for s in rfsegs if s[6] == n]
        own = pad_by_net[n]
        allp, wsum, Ltot, fence, Lrun = [], {}, 0, 0, 0
        for s in ss:
            L = math.dist(s[:2], s[2:4]); k = max(1, int(L / 0.05))
            t = (np.arange(k) + 0.5) / k
            p = np.c_[s[0] + (s[2] - s[0]) * t, s[1] + (s[3] - s[1]) * t]
            keep = np.ones(len(p), bool)
            for q in pad_by_net.values():
                pass
            for q in pads:     # samples on any pad measure the pad, not the line
                if abs(q["x"] - p[:, 0].mean()) < 8 and abs(q["y"] - p[:, 1].mean()) < 8 and q["path"]:
                    keep &= ~in_pad(q, p, 0.3)
            p = p[keep]
            wsum[round(s[4], 3)] = wsum.get(round(s[4], 3), 0) + L; Ltot += L
            if len(p): allp.append((p, s[4]))
            if L > 2:
                ux, uy = (s[2] - s[0]) / L, (s[3] - s[1]) / L
                rel = gnd_vias - s[:2]
                al, pe = rel @ (ux, uy), rel @ (-uy, ux)
                fence += int(((al >= 0) & (al <= L) & (abs(pe) >= 0.3) & (abs(pe) <= 1.6)).sum()); Lrun += L
        if not allp:
            continue
        gaps = np.concatenate([et.query(p)[0] - w / 2 for p, w in allp])
        jc = np.array([(q["x"], q["y"]) for q in pads if JACK.search(fp[q["ref"]]["fpid"]) and q["num"] == "1"])
        uu = []
        for p, w in allp:
            m = cKDTree(jc).query(p)[0] > 2.4 if len(jc) else np.ones(len(p), bool)
            if m.any(): uu.append(inside_any(in1, p[m]))
        und = np.concatenate(uu).mean() if uu else float("nan")
        g5 = np.percentile(gaps, 5)
        fl = []
        cls_w = {"RF": 0.29}.get(NC.get(n), None)
        if any(abs(w - 0.29) > 0.005 for w in wsum) : fl.append("WIDTH")
        if abs(np.median(gaps) - 0.25) > 0.02: fl.append("GAP")
        if und < 0.95: fl.append("UNDER")
        if Lrun and fence / Lrun < 1.5: fl.append("FENCE")
        bad32 += bool(fl)
        print("   %-28s %5.1f mm  widths %-22s gap %.2f (5%% %.2f)  In1 %3.0f%%  fence %.2f/mm  %s" % (
            n[:28], Ltot, ",".join("%.2f:%.1f" % kv for kv in sorted(wsum.items())), np.median(gaps), g5, 100 * und,
            fence / Lrun if Lrun else float("nan"), " ".join(fl)))
