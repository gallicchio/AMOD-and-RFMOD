#!/usr/bin/env python3
"""Dump a board's copper to JSON for scripts/rf_survey.py (run under KiCad's Python):

    rf_extract.py hardware/STEM.kicad_pcb out/STEM_rfgeo.json

Tracks (arcs as 0.1 mm chords), vias, every pad's outline, the filled pours by layer and net, and each net's class."""
import json, sys, math
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
MM = 1e-6
def P(v): return (round(v.x * MM, 4), round(v.y * MM, 4))
def poly(sps):
    out = []
    for i in range(sps.OutlineCount()):
        o = sps.Outline(i)
        ring = [P(o.CPoint(k)) for k in range(o.PointCount())]
        holes = []
        for j in range(sps.HoleCount(i)):
            h = sps.Hole(i, j)
            holes.append([P(h.CPoint(k)) for k in range(h.PointCount())])
        out.append({"ring": ring, "holes": holes})
    return out
D = {"segs": [], "vias": [], "pads": [], "fps": [], "fills": [], "netclass": {}}
for t in b.GetTracks():
    net = t.GetNetname()
    if t.GetClass() == "PCB_VIA":
        D["vias"].append([*P(t.GetPosition()), t.GetWidth(pcbnew.F_Cu) * MM, t.GetDrillValue() * MM, net])
    elif t.GetClass() == "PCB_ARC":
        c = t.GetCenter(); r = t.GetRadius()
        a0 = t.GetArcAngleStart().AsRadians(); da = t.GetAngle().AsRadians()
        n = max(4, int(abs(da) * r * MM / 0.1))
        pts = [(c.x + r * math.cos(a0 + da * k / n), c.y + r * math.sin(a0 + da * k / n)) for k in range(n + 1)]
        pts = [(round(x * MM, 4), round(y * MM, 4)) for x, y in pts]
        for p, q in zip(pts, pts[1:]):
            D["segs"].append([*p, *q, t.GetWidth() * MM, t.GetLayerName(), net])
    else:
        D["segs"].append([*P(t.GetStart()), *P(t.GetEnd()), t.GetWidth() * MM, t.GetLayerName(), net])
for f in b.GetFootprints():
    ref = f.GetReference()
    fld = {x.GetName(): x.GetText() for x in f.GetFields()}
    D["fps"].append({"ref": ref, "fpid": f.GetFPIDAsString(), "value": f.GetValue(), "layer": f.GetLayerName(),
                     "x": P(f.GetPosition())[0], "y": P(f.GetPosition())[1], "rot": f.GetOrientationDegrees(),
                     "attr": f.GetAttributes(), "lcsc": fld.get("LCSC", fld.get("LCSC Part #", "")), "dnp": f.IsDNP(),
                     "exclude_bom": f.IsExcludedFromBOM(), "exclude_pos": f.IsExcludedFromPosFiles()})
    for p in f.Pads():
        lays = [b.GetLayerName(l) for l in p.GetLayerSet().CuStack()]
        lay = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
        try:
            sp = p.GetEffectivePolygon(lay, pcbnew.ERROR_INSIDE)
            pl = poly(sp)
        except Exception:
            pl = []
        D["pads"].append({"ref": ref, "num": p.GetNumber(), "net": p.GetNetname(), "x": P(p.GetPosition())[0],
                          "y": P(p.GetPosition())[1], "attr": p.GetAttribute(), "layers": lays,
                          "drill": [p.GetDrillSize().x * MM, p.GetDrillSize().y * MM], "poly": pl,
                          "size": [p.GetSize(lay).x * MM, p.GetSize(lay).y * MM] if hasattr(p, "GetSize") else None})
for z in b.Zones():
    if z.GetIsRuleArea():
        continue
    for l in z.GetLayerSet().Seq():
        fp = z.GetFilledPolysList(l)
        if fp is None or fp.OutlineCount() == 0:
            continue
        D["fills"].append({"net": z.GetNetname(), "layer": b.GetLayerName(l), "polys": poly(fp)})
for name, ni in b.GetNetsByName().items():
    D["netclass"][str(name)] = ni.GetNetClassName()
json.dump(D, open(sys.argv[2], "w"))
print("%s: %d segs, %d vias, %d pads, %d fills" % (sys.argv[1].split("/")[-1], len(D["segs"]), len(D["vias"]), len(D["pads"]), len(D["fills"])))
