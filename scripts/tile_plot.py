#!/usr/bin/env python3
"""Draw a board's tiles from their definitions alone (no KiCad): courtyards, pads, hand-drawn wires, vias.
    python3 scripts/tile_plot.py amod_a [A1 A2 ...]      -> build/tiles_<stem>_<id>.png
"""
import os, sys, re, glob, importlib, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
import parts as PARTS
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

MOUNT = glob.glob("/tmp/.mount_kicad*/usr/share/kicad/footprints")
_cache = {}


def fp_geom(fpid):
    """(courtyard (x0,y0,x1,y1), [(pad, x, y, w, h, through)]) from the .kicad_mod, in the footprint's own frame."""
    if fpid in _cache:
        return _cache[fpid]
    lib, name = fpid.split(":", 1)
    if lib == "amod":
        path = os.path.join(HERE, "..", "hardware", "lib", "amod.pretty", name + ".kicad_mod")
    else:
        cands = [os.path.join(m, lib + ".pretty", name + ".kicad_mod") for m in MOUNT]
        path = next((c for c in cands if os.path.exists(c)), None)
    if not path or not os.path.exists(path):
        _cache[fpid] = ((-1, -1, 1, 1), [])
        return _cache[fpid]
    t = open(path).read()
    pads = []
    for m in re.finditer(r'\(pad "([^"]*)"\s+(\w+)\s+\w+\s*\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)\s*\(size ([-\d.]+) ([-\d.]+)\)', t):
        num, kind, x, y, prot, w, h = m.groups()
        w, h = float(w), float(h)
        if prot and abs(float(prot)) % 180 == 90:
            w, h = h, w
        pads.append((num, float(x), float(y), w, h, kind != "smd"))
    xs, ys = [], []
    for m in re.finditer(r'\(fp_(?:line|rect)\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)(.*?)\(layer "F\.CrtYd"\)', t, re.S):
        if "(fp_" in m.group(5):
            continue
        xs += [float(m.group(1)), float(m.group(3))]; ys += [float(m.group(2)), float(m.group(4))]
    if not xs:
        for (_, x, y, w, h, _) in pads:
            xs += [x - w / 2 - 0.25, x + w / 2 + 0.25]; ys += [y - h / 2 - 0.25, y + h / 2 + 0.25]
    crt = (min(xs), min(ys), max(xs), max(ys)) if xs else (-1, -1, 1, 1)
    _cache[fpid] = (crt, pads)
    return _cache[fpid]


def rot(dx, dy, r):
    r = r % 360
    return {0: (dx, dy), 90: (dy, -dx), 180: (-dx, -dy), 270: (-dy, dx)}[r]


def draw(t, out):
    fig, ax = plt.subplots(figsize=(t.w / 2.0 + 1, t.h / 2.0 + 1), dpi=110)
    ax.set_xlim(-1.5, t.w + 1.5); ax.set_ylim(t.h + 1.5, -1.5); ax.set_aspect("equal")
    ax.add_patch(Rectangle((0.3, 0.3), t.w - 0.6, t.h - 0.6, fill=False, lw=0.8, color="k"))
    padpos = {}
    for ref, p in t.parts.items():
        d = PARTS.info(p.key)
        crt, pads = fp_geom(d["footprint"])
        corners = [rot(cx, cy, p.rot) for cx, cy in ((crt[0], crt[1]), (crt[2], crt[1]), (crt[2], crt[3]), (crt[0], crt[3]))]
        xs = [p.x + c[0] for c in corners]; ys = [p.y + c[1] for c in corners]
        ax.add_patch(Rectangle((min(xs), min(ys)), max(xs) - min(xs), max(ys) - min(ys), fill=True, alpha=0.12, color="orange", lw=0.5))
        for (num, px, py, w, h, thr) in pads:
            ox, oy = rot(px, py, p.rot)
            pw, ph = (w, h) if p.rot % 180 == 0 else (h, w)
            cx, cy = p.x + ox, p.y + oy
            ax.add_patch(Rectangle((cx - pw / 2, cy - ph / 2), pw, ph, fill=True, alpha=0.5, color="red" if not thr else "gold", lw=0))
            padpos[(ref, num)] = (cx, cy)
            net = p.pins.get(num, "")
            ax.text(cx, cy, net.split("_", 1)[-1][:6] if net else "", fontsize=4, ha="center", va="center", color="blue")
        ax.text(p.x, p.y - 0.4, ref, fontsize=5, ha="center", color="k")
    def pt(q):
        if isinstance(q[0], str):
            return padpos.get((q[0], str(q[1])), (0, 0))
        return (q[0], q[1])
    for (net, pts, w, layer, *_) in t.wires:
        P = [pt(q) for q in pts]
        ax.plot([a[0] for a in P], [a[1] for a in P], color="green" if layer == "F.Cu" else "purple", lw=1.4 if layer == "F.Cu" else 0.9, ls="-" if layer == "F.Cu" else "--")
    for (net, pts, w) in t.routes:
        P = [pt(q) for q in pts]
        ax.plot([a[0] for a in P], [a[1] for a in P], color="gray", lw=0.7, ls=":")
        ax.text(P[0][0], P[0][1], net.split("_", 1)[-1][:5], fontsize=4, color="gray")
    for (net, x, y) in t.vias:
        ax.add_patch(Circle((x, y), 0.3, color="purple", alpha=0.7))
    for ((ref, pad), path, sym) in t.gnd_stubs:
        P = [padpos.get((ref, pad), (0, 0))] + (path if isinstance(path, list) else [path])
        ax.plot([a[0] for a in P], [a[1] for a in P], color="green", lw=1.0)
        ax.add_patch(Circle(P[-1], 0.3, color="green", alpha=0.7))
    for (x, y, s, size, thk, just, ang) in t.texts:
        ax.text(x, y, s, fontsize=5, ha={"left": "left", "right": "right", "center": "center"}[just], va="center", color="brown", rotation=ang)
    ax.set_title(t.id, fontsize=8)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def main():
    stem = sys.argv[1]
    want = sys.argv[2:]
    mod = importlib.import_module("boards." + stem)
    for t in mod.tiles():
        if want and t.id not in want:
            continue
        out = os.path.join(HERE, "..", "build", "tiles_%s_%s.png" % (stem, t.id))
        draw(t, out)
        print("  wrote", os.path.relpath(out))


if __name__ == "__main__":
    main()
