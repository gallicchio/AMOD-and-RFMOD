#!/usr/bin/env python3
"""Build a board from its tiles: the outline and holes, every tile's parts where its layout puts
them, the tiles' wires as copper AND as silkscreen (clipped round pads and bodies, so the picture
is the netlist), hops on the back layer, a ground via at every ground stub with the schematic's
ground symbol drawn at it, the planes, the tile frames and legends, the jack names on their tiles' frames,
the identity, the QR code and the back text.  No autorouter: every track is a drawn wire.

Runs under KiCad's bundled Python (it needs pcbnew):
    <AppRun> python3.11 scripts/gen_pcb.py amod_p out/amod_p.net hardware/amod_p.kicad_pcb
"""
import json, math, os, sys
import kienv
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pcbnew
from sexp_parse import parse_file
import parts
import geometry as G


class NS:
    """A tile (or a part, or a jack) read back from out/<stem>_tiles.json, with attribute access."""

    def __init__(self, d):
        for k, v in d.items():
            setattr(self, k, v)

    def to_board(self, pt):
        return (self.x0 + pt[0], self.y0 + pt[1])


def load_tiles(path):
    d = json.load(open(path))
    tiles = []
    for td in d["tiles"]:
        t = NS(td)
        t.parts = {pd["ref"]: NS(pd) for pd in td["parts"]}
        t.wires = [(w[0], [tuple(q) if isinstance(q[0], str) else (float(q[0]), float(q[1])) for q in w[1]], w[2], (w[3] if len(w) > 3 else "F.Cu"),
                    (w[4] if len(w) > 4 else True), (w[5] if len(w) > 5 else False))
                   for w in td["wires"]]
        t.vias = [(v[0], float(v[1]), float(v[2]), (v[3] if len(v) > 3 else False)) for v in td.get("vias", [])]
        t.routes = [(r[0], [tuple(q) if isinstance(q[0], str) else (float(q[0]), float(q[1])) for q in r[1]], r[2]) for r in td.get("routes", [])]
        t.hops = [(n, tuple(a), tuple(b)) for (n, a, b) in td["hops"]]
        t.gnd_stubs = [(tuple(g[0]), (tuple(g[1]) if not isinstance(g[1][0], list) else [tuple(q) for q in g[1]]), (tuple(g[2]) if g[2] else None),
                        (g[3] if len(g) > 3 else None), (g[4] if len(g) > 4 else False))
                       for g in td["gnd_stubs"]]
        t.texts = [tuple(x) for x in td["texts"]]
        tiles.append(t)
    return tiles, d

HW = os.path.abspath(os.path.join(HERE, "..", "hardware"))
LOCAL_FP = os.path.join(HW, "lib", "amod.pretty")
SHARE_FP = None
SILK_W, SILK_CLEAR = 0.3, 0.3
VIA_DIA, VIA_DRILL = 0.6, 0.3
FINE_VIA_DIA, FINE_VIA_DRILL = 0.45, 0.25     # beside a 0.5 mm pitch QFN (JLCPCB: 0.35 / 0.2 at least)
FOOT_R = 4.0                           # an 8 mm adhesive bumper (3M SJ5303 class, about 2 mm tall)
RF_W = 0.29                            # tiles.RF_W: a wire this wide is a 50 ohm line and gets a via fence
RF_GAP = 0.25                          # the top pour's distance from it (the RF net class says the same)
FENCE_OFF, FENCE_PITCH = RF_W / 2 + RF_GAP + 0.45, 1.0      # fence vias: 0.845 off the line's centre, every 1.0 mm
LAUNCH_R_INNER, LAUNCH_R_TOP = 2.2, 1.9                      # no copper under a jack's centre pin on L2-L4, and the top pour this far away
BOARD_RULES = dict(m_MinClearance=0.20, m_HoleClearance=0.30, m_HoleToHoleMin=0.50, m_CopperEdgeClearance=0.30, m_SilkClearance=0.15)
# the RF board carries a 0.5 mm pitch QFN: the floor drops to JLCPCB's 0.127 mm there, the net classes keep 0.2 for everything
# but the synthesizer's own nets (gen_project.py says the same in the project file)
FINE_BOARD_RULES = dict(m_MinClearance=0.127, m_TrackMinWidth=0.127, m_ViasMinSize=0.45, m_ViasMinAnnularWidth=0.10,
                        m_MinThroughDrill=0.20, m_HoleClearance=0.25)
BOARD_RULES_BY_STEM = {s: FINE_BOARD_RULES for s, b in parts.BOARDS.items() if b.get("fine")}
FIDUCIALS = [(3.5, 50.0), (96.5, 10.0), (96.5, 90.0)]
JACK_SIZE, JACK_THICK = 0.9, 0.18      # the jacks' names, on their tiles' frames
TITLE_SIZE, TITLE_THICK = 0.9, 0.18    # a tile's title in words, on its top frame
QR_AT, QR_MODULE = (23.2, 80.0), 0.42       # under P12's switch, between its jack's legs and P13's: 14 mm with no hole
BACK_Y, BACK_PITCH = 94.2, 1.4       # between the two rows of cable-tie slots


def mm(v):
    return pcbnew.FromMM(float(v))


def pt(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def tomm(v):
    return pcbnew.ToMM(v)


def find_share():
    here = os.path.dirname(os.path.abspath(pcbnew.__file__))
    for up in range(2, 8):
        base = os.path.abspath(os.path.join(here, *([".."] * up)))
        for sub in ("share/kicad/footprints", "usr/share/kicad/footprints"):
            cand = os.path.join(base, sub)
            if os.path.isdir(cand):
                return cand
    env = os.environ.get("KICAD_SHARE_DIR")
    if env and os.path.isdir(os.path.join(env, "footprints")):
        return os.path.join(env, "footprints")
    raise SystemExit("cannot find KiCad's footprint libraries")


def load_fp(fpid):
    lib, name = fpid.split(":")
    path = LOCAL_FP if lib == "amod" else os.path.join(SHARE_FP, lib + ".pretty")
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise SystemExit("footprint %s not found in %s" % (fpid, path))
    # a library footprint whose STEP file KiCad does not ship: point it at our stand-in body of the same name
    share = kienv.share_dir()
    keep, changed = [], False
    for m in fp.Models():
        fname = str(m.m_Filename)
        real = fname.replace("${KICAD10_3DMODEL_DIR}", os.path.join(share, "3dmodels")).replace("${KICAD9_3DMODEL_DIR}", os.path.join(share, "3dmodels"))
        if not os.path.exists(real):
            stand_in = os.path.join(HW, "lib", "amod.3dshapes", os.path.splitext(os.path.basename(fname))[0] + ".wrl")
            if os.path.exists(stand_in):
                fname = "${KIPRJMOD}/lib/amod.3dshapes/" + os.path.basename(stand_in)
                changed = True
                k = 1 / 2.54                                  # a stand-in is drawn in mm, VRML's unit is 2.54 mm
                keep.append((fname, (k, k, k), (0, 0, 0), (0, 0, 0), m.m_Show))
                continue
        # copy the vectors' numbers, not the SWIG proxies: those die with the list and leave garbage in the board file
        keep.append((fname, (m.m_Scale.x, m.m_Scale.y, m.m_Scale.z), (m.m_Rotation.x, m.m_Rotation.y, m.m_Rotation.z),
                     (m.m_Offset.x, m.m_Offset.y, m.m_Offset.z), m.m_Show))
    if changed:
        fp.Models().clear()
        for (fname, scale, rot, off, show) in keep:
            m = pcbnew.FP_3DMODEL()
            m.m_Filename, m.m_Show = fname, show
            m.m_Scale = pcbnew.VECTOR3D(*scale); m.m_Rotation = pcbnew.VECTOR3D(*rot); m.m_Offset = pcbnew.VECTOR3D(*off)
            fp.Models().push_back(m)
    return fp


def read_netlist(path):
    root = parse_file(path)
    comps = {}
    for c in root.first("components").kids("comp"):
        fields = {}
        fl = c.first("fields")
        if fl is not None:
            for f in fl.kids("field"):
                nm = f.first("name").atom(0)
                val = f.atom(0)
                if nm not in ("Footprint", "Datasheet", "Description") and val:
                    fields[nm] = val
        ts = c.first("tstamps")
        val = c.first("value").atom(0)
        comps[c.first("ref").atom(0)] = {"value": "" if val == "~" else val, "footprint": c.first("footprint").atom(0),
                                         "fields": fields, "tstamp": ts.atom(0) if ts is not None else ""}
    nets = {}
    for n in root.first("nets").kids("net"):
        name = n.first("name").atom(0)
        nets[name] = [(x.first("ref").atom(0), x.first("pin").atom(0)) for x in n.kids("node")]
    return comps, nets


class Board:
    def __init__(self, stem, netlist_path, out_path):
        global SHARE_FP
        SHARE_FP = find_share()
        self.stem = stem
        self.B = parts.BOARDS[stem]
        self.tiles, self.meta = load_tiles(os.path.join(os.path.dirname(netlist_path), stem + "_tiles.json"))
        self.comps, self.nets = read_netlist(netlist_path)
        self.board = pcbnew.CreateEmptyBoard()
        self.board.SetCopperLayerCount(self.B["layers"])
        ds = self.board.GetDesignSettings()
        rules = dict(BOARD_RULES); rules.update(BOARD_RULES_BY_STEM.get(stem, {}))
        for name, value in rules.items():
            if hasattr(ds, name):
                setattr(ds, name, mm(value))
        self.out_path = out_path
        self.netmap = {}
        for name in sorted(self.nets):
            ni = pcbnew.NETINFO_ITEM(self.board, name)
            self.board.Add(ni)
            self.netmap[name] = ni
        self.pad_net = {}
        for name, nodes in self.nets.items():
            for node in nodes:
                self.pad_net[node] = name
        self.fps, self.pads, self.problems = {}, {}, []
        # the tiles name their nets ("/P5_N1"); KiCad names an unlabelled net after a pad ("Net-(R501-Pad2)").
        # Map each declared net to KiCad's name through any pad on it.
        self.kname = {}
        for t in self.tiles:
            for p in t.parts.values():
                for pad, net in p.pins.items():
                    kn = self.pad_net.get((p.ref, pad))
                    if kn is None:
                        continue
                    if net in self.kname and self.kname[net] != kn:
                        self.problems.append("%s: %s is both %s and %s in the netlist" % (t.id, net, self.kname[net], kn))
                    self.kname[net] = kn
        self.segments, self.vias, self.hops, self.back = [], [], [], []
        self.rf_segs, self.fence_vias = [], set()
        self.pad_list, self.nosilk = [], set()
        self.stub_dir, self.via_at = {}, {}
        # placements: tile parts in board coordinates, plus the board-level parts
        self.place_table = {}
        for t in self.tiles:
            for ref, p in t.parts.items():
                bx, by = t.to_board((p.x, p.y))
                self.place_table[ref] = (bx, by, p.rot, t, p)
        for i, (hx, hy) in enumerate(self.meta.get("holes", G.HOLES)):
            self.place_table["MH%d" % (i + 1)] = (hx, hy, 0, None, None)
        for i, (gx, gy) in enumerate(self.meta["gnd_loops"]):
            self.place_table["TP%d" % (9901 + i)] = (gx, gy, 0, None, None)
        for i, (sx, sy) in enumerate(self.meta.get("slots", [])):
            self.place_table["H%d" % (9901 + i)] = (sx, sy, 90, None, None)

    # ---------------------------------------------------------------- parts --
    def place(self):
        for ref, info in sorted(self.comps.items()):
            if ref not in self.place_table:
                raise SystemExit("%s is in the netlist but no tile places it" % ref)
            x, y, rot, t, p = self.place_table[ref]
            fp = load_fp(info["footprint"])
            fp.SetFPIDAsString(info["footprint"])
            if info["tstamp"]:
                fp.SetPath(pcbnew.KIID_PATH("/" + info["tstamp"]))
            fp.SetSheetname("/")
            fp.SetSheetfile(os.path.basename(self.out_path).replace(".kicad_pcb", ".kicad_sch"))
            fp.SetReference(ref)
            fp.SetValue(info["value"])
            for fname, fval in info["fields"].items():
                fp.SetField(fname, fval)
            for f in fp.GetFields():
                if f.GetName() in ("Reference", "Value"):
                    continue
                f.SetVisible(False)
                f.SetLayer(pcbnew.F_Fab)
            if fp.HasField("Description"):
                fp.SetField("Description", "")
            self.board.Add(fp)
            fp.SetPosition(pt(x, y))
            if rot:
                fp.SetOrientationDegrees(rot)
            for pad in fp.Pads():
                key = (ref, pad.GetNumber())
                if key in self.pad_net:
                    pad.SetNet(self.netmap[self.pad_net[key]])
            if ref[:2] == "MH" or ref[:1] == "H":
                fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
                fp.Value().SetVisible(False)
                fp.Reference().SetVisible(False)
            self.fps[ref] = fp
        for ref in self.place_table:
            if ref not in self.fps and not ref.startswith("MH") and not ref.startswith("H99"):
                self.problems.append("%s is placed by a tile but not in the netlist" % ref)
        for ref, fp in self.fps.items():
            fp.Reference().SetVisible(False)
            fp.Reference().SetLayer(pcbnew.F_Fab)
            if ref[:2] in ("TP", "MH") or ref[:1] == "H":
                fp.Value().SetVisible(False)
            for pad in fp.Pads():
                b = pad.GetBoundingBox()
                d = dict(x=tomm(pad.GetPosition().x), y=tomm(pad.GetPosition().y),
                         x0=tomm(b.GetLeft()), y0=tomm(b.GetTop()), x1=tomm(b.GetRight()), y1=tomm(b.GetBottom()),
                         through=pad.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH), net=pad.GetNetname(),
                         round=(pad.GetShape() == pcbnew.PAD_SHAPE_CIRCLE))
                self.pad_list.append(d)                       # every pad: the SMA's four legs are all "2", the USB-C has four "SH"
                self.pads.setdefault((ref, pad.GetNumber()), d)    # the first of a number: where a wire or route ends
        self.board.GetDesignSettings().SetAuxOrigin(pt(0, G.BOARD))
        self.outline()

    def outline(self):
        w = h = G.BOARD
        r = G.CORNER_R
        for (a, b) in (((r, 0), (w - r, 0)), ((w, r), (w, h - r)), ((w - r, h), (r, h)), ((0, h - r), (0, r))):
            s = pcbnew.PCB_SHAPE(self.board)
            s.SetShape(pcbnew.SHAPE_T_SEGMENT)
            s.SetStart(pt(*a)); s.SetEnd(pt(*b))
            s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1))
            self.board.Add(s)
        for (cx, cy, a0) in ((r, r, 180), (w - r, r, 270), (w - r, h - r, 0), (r, h - r, 90)):
            s = pcbnew.PCB_SHAPE(self.board)
            s.SetShape(pcbnew.SHAPE_T_ARC)
            s.SetCenter(pt(cx, cy))
            s.SetStart(pt(cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))))
            s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T), True)
            s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1))
            self.board.Add(s)

    # ---------------------------------------------------------------- copper --
    def resolve(self, p, net, t):
        if isinstance(p[0], str):
            pad = self.pads.get((p[0], p[1]))
            if pad is None:
                raise SystemExit("%s: wire on %s: no pad %s.%s" % (t.id, net, p[0], p[1]))
            if pad["net"] != net:
                self.problems.append("%s: wire on %s ends on %s.%s, which is on %r" % (t.id, net, p[0], p[1], pad["net"]))
            return (pad["x"], pad["y"])
        return t.to_board((float(p[0]), float(p[1])))

    def track(self, a, b, width, net, layer=pcbnew.F_Cu, shape=False):
        if abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6:
            return
        if shape:                     # copper that ends in the open on purpose (a stub): a graphic line with a net, not a track
            tr = pcbnew.PCB_SHAPE(self.board)
            tr.SetShape(pcbnew.SHAPE_T_SEGMENT)
        else:
            tr = pcbnew.PCB_TRACK(self.board)
        tr.SetStart(pt(*a)); tr.SetEnd(pt(*b))
        tr.SetWidth(mm(width)); tr.SetLayer(layer)
        tr.SetNet(self.netmap[net])
        self.board.Add(tr)
        self.segments.append((net, a, b, layer))

    def via(self, x, y, net, fine=False):
        key = (round(x, 3), round(y, 3))
        if key in self.via_at:
            assert self.via_at[key] == net, ("two nets want a via at", key)
            return
        self.via_at[key] = net
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(pt(x, y))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        if fine:
            v.SetDrill(mm(FINE_VIA_DRILL)); v.SetWidth(mm(FINE_VIA_DIA))
        else:
            v.SetDrill(mm(VIA_DRILL)); v.SetWidth(mm(VIA_DIA))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(self.netmap[net])
        v.SetFrontTentingMode(pcbnew.TENTING_MODE_TENTED)
        v.SetBackTentingMode(pcbnew.TENTING_MODE_TENTED)
        self.board.Add(v)
        self.vias.append((net, x, y))

    def wires(self):
        for t in self.tiles:
            hops = {}
            for (n, a, b) in t.hops:
                n = self.kname.get(n, n)
                A, B = t.to_board(a), t.to_board(b)
                hops[(n, (round(A[0], 3), round(A[1], 3)), (round(B[0], 3), round(B[1], 3)))] = True
                hops[(n, (round(B[0], 3), round(B[1], 3)), (round(A[0], 3), round(A[1], 3)))] = True
            for (net, points, width, layer, silk, fine) in t.wires:
                net = self.kname.get(net, net)
                if net not in self.netmap:
                    self.problems.append("%s: wire names a net that is not in the netlist: %r" % (t.id, net))
                    continue
                pts = [self.resolve(p, net, t) for p in points]
                if not silk:
                    for a, b in zip(pts, pts[1:]):
                        self.nosilk.add((round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3)))
                if layer == "B.Cu":
                    for end, spec in ((pts[0], points[0]), (pts[-1], points[-1])):
                        if not isinstance(spec[0], str) or self.pads[(spec[0], spec[1])]["through"] is False:
                            self.via(*end, net, fine=fine)
                    for a, b in zip(pts, pts[1:]):
                        self.track(a, b, width, net, pcbnew.B_Cu)
                        self.back.append((net, a, b))
                    continue
                shape = layer == "F.Cu:shape"
                for a, b in zip(pts, pts[1:]):
                    if abs(width - RF_W) < 1e-6:
                        self.rf_segs.append((net, a, b))
                    if shape:
                        self.track(a, b, width, net, shape=True)
                        continue
                    key = (net, (round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3)))
                    key = (net, (round(a[0], 3), round(a[1], 3)), (round(b[0], 3), round(b[1], 3)))
                    if key in hops:
                        self.via(*a, net); self.via(*b, net)
                        self.track(a, b, width, net, pcbnew.B_Cu)
                        self.hops.append((net, a, b))
                    else:
                        self.track(a, b, width, net)
            for (net, vx, vy, fine) in t.vias:
                net = self.kname.get(net, net)
                if net not in self.netmap:
                    self.problems.append("%s: via on a net that is not in the netlist: %r" % (t.id, net))
                    continue
                bx, by = t.to_board((vx, vy))
                self.via(bx, by, net, fine=fine)
            for (padref, path, sym, swidth, sfine) in t.gnd_stubs:
                pad = self.pads.get(padref)
                if pad is None:
                    raise SystemExit("%s: ground stub from %s: no such pad" % (t.id, padref))
                if pad["net"] != "GND":
                    self.problems.append("%s: ground stub from %s, which is on %r" % (t.id, padref, pad["net"]))
                pts = [(pad["x"], pad["y"])] + [t.to_board(q) for q in (path if isinstance(path, list) else [path])]
                for a, b in zip(pts, pts[1:]):
                    self.track(a, b, swidth or (t.wires[0][2] if t.wires else 0.35), "GND")
                vx, vy = pts[-1]
                self.via(vx, vy, "GND", fine=sfine)
                dx, dy = vx - pts[-2][0], vy - pts[-2][1]
                n = math.hypot(dx, dy) or 1.0
                self.stub_dir[(round(vx, 3), round(vy, 3))] = sym or (dx / n, dy / n)
        # the ground loops in the margins: a via at the pad's end
        for ref in self.fps:
            if ref.startswith("TP99"):
                pad = self.pads[(ref, "1")]
                self.track((pad["x"], pad["y"]), (pad["x"], pad["y"] + 1.6), 0.35, "GND")
                self.via(pad["x"], pad["y"] + 1.6, "GND")
                self.stub_dir[(round(pad["x"], 3), round(pad["y"] + 1.6, 3))] = (0, 1)

    def back_wires(self):
        """The board module's BACK_WIRES: (net, [(x, y), ...]) in board mm on the back, between vias or through-hole pads
        that already exist (the Pmod's lines from the plug to the tiles' vias).  Silk: none (they cross tiles)."""
        for (net, pts) in self.meta.get("back_wires", []):
            if net not in self.netmap:
                self.problems.append("back wire on %s, which is not in the netlist" % net)
                continue
            for a, b in zip(pts, pts[1:]):
                a, b = (float(a[0]), float(a[1])), (float(b[0]), float(b[1]))
                self.track(a, b, 0.15 if parts.BOARDS[self.meta.get("stem")].get("fine") else 0.35, net, pcbnew.B_Cu)
                self.nosilk.add((round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3)))

    def front_wires(self):
        """The board module's FRONT_WIRES: like BACK_WIRES but on the front (a line that must cross the back's), no silk."""
        for (net, pts) in self.meta.get("front_wires", []):
            if net not in self.netmap:
                self.problems.append("front wire on %s, which is not in the netlist" % net)
                continue
            for a, b in zip(pts, pts[1:]):
                a, b = (float(a[0]), float(a[1])), (float(b[0]), float(b[1]))
                self.track(a, b, 0.15, net, pcbnew.F_Cu)
                self.nosilk.add((round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3)))

    def autoroute(self):
        """scripts/router.py over each tile's declared routes, one at a time, each avoiding everything laid so far."""
        import router as R
        for t in self.tiles:
            if not t.routes:
                continue
            x0, y0, x1, y1 = t.x0 - 1.2, t.y0 - 1.2, t.x0 + t.w + 1.2, t.y0 + t.h + 1.2
            for ref, p in t.parts.items():                   # parts the tile puts past its frame (the USB-C in the margin)
                bx, by = t.to_board((p.x, p.y))
                x0, y0, x1, y1 = min(x0, bx - 4.0), min(y0, by - 4.0), max(x1, bx + 4.0), max(y1, by + 4.0)
            x0, y0, x1, y1 = max(0.5, x0), max(0.5, y0), min(G.BOARD - 0.5, x1), min(G.BOARD - 0.5, y1)
            for (net, specs, width) in t.routes:
                net = self.kname.get(net, net)
                if net not in self.netmap:
                    self.problems.append("%s: route on a net that is not in the netlist: %r" % (t.id, net)); continue
                pts = []
                for sp in specs:
                    if isinstance(sp[0], str):
                        pad = self.pads.get((sp[0], sp[1]))
                        if pad is None:
                            raise SystemExit("%s: route on %s: no pad %s.%s" % (t.id, net, sp[0], sp[1]))
                        if pad["net"] != net:
                            self.problems.append("%s: route on %s ends on %s.%s, which is on %r" % (t.id, net, sp[0], sp[1], pad["net"]))
                        pts.append(("pad", pad))
                    else:
                        bx, by = t.to_board(sp)
                        pts.append(("pt", (bx, by)))
                for a, b in zip(pts, pts[1:]):
                    grid = self._grid(x0, y0, x1, y1, net, width)
                    starts = self._cells_of(grid, a, width)
                    goals = self._cells_of(grid, b, width)
                    path = R.search(grid, starts, goals, width)
                    if path is None:
                        sfree = sum(1 for (i, j, l) in starts if grid.cost[l][i][j] >= 0)
                        gfree = sum(1 for (i, j, l) in goals if grid.cost[l][i][j] >= 0)
                        self.problems.append("%s: no route for %s between %r and %r (start cells %d/%d free, goal cells %d/%d free)" % (
                            t.id, net, specs[pts.index(a)], specs[pts.index(b)], sfree, len(starts), gfree, len(goals)))
                        self._dump_grid(grid, starts, goals, "%s_%s" % (t.id, net.strip("/").replace("/", "_")))
                        with open(os.path.join(os.path.dirname(self.out_path), "..", "build", "route_%s_segments.txt" % t.id), "w") as fh:
                            for (n2, sa, sb, layer) in self.segments:
                                if x0 <= sa[0] <= x1 and y0 <= sa[1] <= y1:
                                    fh.write("%s %s %s %s\n" % (n2, sa, sb, "F" if layer == pcbnew.F_Cu else "B"))
                            for (n2, vx, vy) in self.vias:
                                if x0 <= vx <= x1 and y0 <= vy <= y1:
                                    fh.write("via %s %s %s\n" % (n2, vx, vy))
                        continue
                    path = R.simplify(path)
                    for (i, j, l), (i2, j2, l2) in zip(path, path[1:]):
                        p, q = grid.xy(i, j), grid.xy(i2, j2)
                        if l != l2:
                            self.via(p[0], p[1], net)
                            continue
                        layer = pcbnew.F_Cu if l == 0 else pcbnew.B_Cu
                        self.track(p, q, width, net, layer)
                        if l == 1:
                            self.back.append((net, p, q))

    def _dump_grid(self, grid, starts, goals, name):
        """An ASCII map of the front layer for a failed route (build/route_<name>.txt): . free, # blocked, + soft, S/G ends."""
        ss = {(i, j) for (i, j, l) in starts if l == 0}; gs = {(i, j) for (i, j, l) in goals if l == 0}
        rows = []
        for j in range(grid.ny):
            row = []
            for i in range(grid.nx):
                c = grid.cost[0][i][j]
                ch = "#" if c < 0 else ("+" if c > 1.5 else ".")
                if (i, j) in ss: ch = "S"
                if (i, j) in gs: ch = "G"
                row.append(ch)
            rows.append("".join(row))
        path = os.path.join(os.path.dirname(self.out_path), "..", "build", "route_%s.txt" % name)
        with open(path, "w") as fh:
            fh.write("\n".join(rows) + "\n")

    def _cells_of(self, grid, spec, width):
        kind, v = spec
        if kind == "pt":
            i, j = grid.ij(*v)
            grid.free(0, v[0] - 0.15, v[1] - 0.15, v[0] + 0.15, v[1] + 0.15)       # the point is on this net's own copper
            return [(i, j, 0)]
        if v["through"]:                                      # a through-hole pad: its centre, on either layer
            i, j = grid.ij(v["x"], v["y"])
            grid.cost[0][i][j] = 1.0; grid.cost[1][i][j] = 1.0
            return [(i, j, 0), (i, j, 1)]
        out = []
        for i, j in grid.cells_inside(v["x0"] + 0.05, v["y0"] + 0.05, v["x1"] - 0.05, v["y1"] - 0.05):
            out.append((i, j, 0))
        if not out:
            i, j = grid.ij(v["x"], v["y"])
            out = [(i, j, 0)]
        return out

    def _grid(self, x0, y0, x1, y1, net, width):
        import router as R
        grid = R.Grid(x0, y0, x1, y1)
        grow = R.CLEAR + width / 2 + 0.05
        dbg = os.environ.get("ROUTE_DEBUG")
        for p in self.pad_list:
            if p["through"]:                                  # no via near any hole, whatever its net
                grid.no_via(p["x0"], p["y0"], p["x1"], p["y1"], 0.5 + R.VIA_D / 2 + 0.05)
            if p["net"] == net:
                continue
            if dbg and p["x1"] + grow > x0 and p["x0"] - grow < x1 and p["y1"] + grow > y0 and p["y0"] - grow < y1 and (p["x1"] - p["x0"] > 3 or p["y1"] - p["y0"] > 3):
                print("   big pad near grid:", p["net"], p["x0"], p["y0"], p["x1"], p["y1"])
            if p.get("round"):
                rad = (p["x1"] - p["x0"]) / 2 + grow
                for l in ((0, 1) if p["through"] else (0,)):
                    grid.block_circle(l, p["x"], p["y"], rad)
                grid.no_via(p["x0"], p["y0"], p["x1"], p["y1"], R.CLEAR + R.VIA_D / 2 + 0.05)
            elif p["through"]:
                grid.block(0, p["x0"], p["y0"], p["x1"], p["y1"], grow)
                grid.block(1, p["x0"], p["y0"], p["x1"], p["y1"], grow)
                grid.no_via(p["x0"], p["y0"], p["x1"], p["y1"], R.CLEAR + R.VIA_D / 2 + 0.05)
            else:
                grid.block(0, p["x0"], p["y0"], p["x1"], p["y1"], grow)
                grid.no_via(p["x0"], p["y0"], p["x1"], p["y1"], R.CLEAR + R.VIA_D / 2 + 0.05)
        for (n2, a, b, layer) in self.segments:
            if n2 == net:
                continue
            l = 0 if layer == pcbnew.F_Cu else 1
            hw = 0.18
            grid.block(l, min(a[0], b[0]) - hw, min(a[1], b[1]) - hw, max(a[0], b[0]) + hw, max(a[1], b[1]) + hw, grow)
            grid.no_via(min(a[0], b[0]) - hw, min(a[1], b[1]) - hw, max(a[0], b[0]) + hw, max(a[1], b[1]) + hw, R.CLEAR + R.VIA_D / 2 + 0.05)
        for (n2, vx, vy) in self.vias:
            grid.no_via(vx - 0.3, vy - 0.3, vx + 0.3, vy + 0.3, 0.5 + R.VIA_D / 2 + 0.05)
            if n2 == net:
                continue
            grid.block_circle(0, vx, vy, 0.3 + grow)
            grid.block_circle(1, vx, vy, 0.3 + grow)
            grid.no_via(vx - 0.3, vy - 0.3, vx + 0.3, vy + 0.3, R.CLEAR + R.VIA_D / 2 + 0.05)
        for ref, fp in self.fps.items():
            poly = fp.GetCourtyard(pcbnew.F_CrtYd)
            if poly.OutlineCount():
                bb = poly.BBox()
                grid.soft(0, tomm(bb.GetLeft()), tomm(bb.GetTop()), tomm(bb.GetRight()), tomm(bb.GetBottom()), 6.0)
                grid.no_via(tomm(bb.GetLeft()), tomm(bb.GetTop()), tomm(bb.GetRight()), tomm(bb.GetBottom()), 0.0)
        # same-net pads are reachable whatever lies near them
        for p in self.pad_list:
            if p["net"] == net:
                for (i, j) in grid.cells_inside(p["x0"], p["y0"], p["x1"], p["y1"]):
                    grid.cost[0][i][j] = 1.0
                    if p["through"]:
                        grid.cost[1][i][j] = 1.0
        return grid

    def rf_fences(self):
        """Ground vias along every 50 ohm line (the RF_W wires), FENCE_OFF each side every FENCE_PITCH, wherever one fits:
        clear of every pad, of other nets' tracks, of other vias and of the launch under a jack."""
        jacks = [t.to_board((j["x"], j["y"])) for t in self.tiles if t.top_pour for j in t.jacks]
        voids = [(*t.to_board((v[0], v[1])), v[2]) for t in self.tiles for v in getattr(t, "voids", [])]
        placed = []

        def seg_dist(p, a, b):
            (px, py), (ax, ay), (bx, by) = p, a, b
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            u = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
            return math.hypot(px - (ax + u * dx), py - (ay + u * dy))

        def fits(x, y):
            if any(math.hypot(x - jx, y - jy) < LAUNCH_R_INNER + 0.4 for (jx, jy) in jacks):
                return False
            if any(math.hypot(x - vx, y - vy) < vr + 0.4 for (vx, vy, vr) in voids):
                return False
            for p in self.pad_list:
                if p["x0"] - 0.6 <= x <= p["x1"] + 0.6 and p["y0"] - 0.6 <= y <= p["y1"] + 0.6:
                    return False
            for (n2, a, b, layer) in self.segments:
                if n2 != "GND" and seg_dist((x, y), a, b) < 0.75:
                    return False
            for (n2, vx, vy) in self.vias:
                if math.hypot(x - vx, y - vy) < 0.9:
                    return False
            return all(math.hypot(x - px, y - py) >= 0.9 for (px, py) in placed)

        for (net, a, b) in self.rf_segs:
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if L < 0.8:
                continue
            ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            nx, ny = -uy, ux
            k = 0
            while 0.4 + k * FENCE_PITCH <= L - 0.4:
                d = 0.4 + k * FENCE_PITCH
                for sgn in (1, -1):
                    x, y = a[0] + ux * d + sgn * nx * FENCE_OFF, a[1] + uy * d + sgn * ny * FENCE_OFF
                    if fits(x, y):
                        self.via(x, y, "GND")
                        placed.append((x, y))
                        self.fence_vias.add((round(x, 3), round(y, 3)))
                k += 1

    def rf_voids(self):
        """Rule areas under every jack of an RF tile: no fill within LAUNCH_R_INNER of the centre pin on L2, L3 and L4, none within
        LAUNCH_R_TOP on L1, so the pin's pad does not sit on 0.6 pF of plane (CostasLink's gen/rf_launch.py)."""
        def circle(z, cx, cy, r):
            o = z.Outline(); o.NewOutline()
            for i in range(32):
                a = 2 * math.pi * i / 32
                o.Append(mm(cx + r * math.cos(a)), mm(cy + r * math.sin(a)))

        inner = (pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu) if self.B["layers"] == 4 else (pcbnew.B_Cu,)
        for t in self.tiles:                                   # a tile's own voids: a loop that must not see its image in a plane
            for (vx, vy, r, which) in getattr(t, "voids", []):
                cx, cy = t.to_board((vx, vy))
                z = pcbnew.ZONE(self.board)
                z.SetIsRuleArea(True)
                z.SetDoNotAllowZoneFills(True)
                z.SetDoNotAllowTracks(False); z.SetDoNotAllowVias(False); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
                ls = pcbnew.LSET()
                for l in {"inner": inner, "top": (pcbnew.F_Cu,), "all": inner + (pcbnew.F_Cu,)}[which]:
                    ls.AddLayer(l)
                z.SetLayerSet(ls)
                circle(z, cx, cy, r)
                self.board.Add(z)
        for t in self.tiles:
            if not t.top_pour:
                continue
            for j in t.jacks:
                if j.get("launch", True) is False:             # a short at the pin: the pour and the planes come to it
                    continue
                cx, cy = t.to_board((j["x"], j["y"]))
                for layers, r in (((pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu) if self.B["layers"] == 4 else (pcbnew.B_Cu,), LAUNCH_R_INNER),
                                  ((pcbnew.F_Cu,), LAUNCH_R_TOP)):
                    z = pcbnew.ZONE(self.board)
                    z.SetIsRuleArea(True)
                    z.SetDoNotAllowZoneFills(True)
                    z.SetDoNotAllowTracks(False); z.SetDoNotAllowVias(False); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
                    ls = pcbnew.LSET()
                    for l in layers:
                        ls.AddLayer(l)
                    z.SetLayerSet(ls)
                    circle(z, cx, cy, r)
                    self.board.Add(z)

    def top_pours(self):
        """Ground on L1 over each RF tile (inside its frame), RF_GAP from every track and pad, solid to the ground pads."""
        for t in self.tiles:
            if not t.top_pour:
                continue
            z = pcbnew.ZONE(self.board)
            z.SetLayer(pcbnew.F_Cu)
            z.SetNet(self.netmap["GND"])
            z.SetAssignedPriority(0)
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
            z.SetLocalClearance(mm(RF_GAP)); z.SetMinThickness(mm(0.2))
            z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
            o = z.Outline(); o.NewOutline()
            m = 0.9
            pts = [(t.x0 + m, t.y0 + m), (t.x0 + t.w - m, t.y0 + m), (t.x0 + t.w - m, t.y0 + t.h - m)]
            pb = getattr(t, "pour_below", None)
            if pb:                                             # a tongue below the frame round a line that runs in the margin
                sx0, sx1, sy1 = pb
                pts += [(t.x0 + sx1, t.y0 + t.h - m), (t.x0 + sx1, t.y0 + sy1), (t.x0 + sx0, t.y0 + sy1), (t.x0 + sx0, t.y0 + t.h - m)]
            pts.append((t.x0 + m, t.y0 + t.h - m))
            for (x, y) in pts:
                o.Append(mm(x), mm(y))
            self.board.Add(z)

    def plane(self):
        self.rf_voids()
        self.top_pours()
        # the rails: pours on In2 from the board module (net, x0, y0, x1, y1, priority); the lowest priority covers the board
        for spec in self.meta.get("rail_pours", []):
            if len(spec) == 3:                                 # (net, [(x, y), ...], priority): a polygon
                net, pts, prio = spec
            else:                                              # (net, x0, y0, x1, y1, priority): a rectangle
                net, x0, y0, x1, y1, prio = spec
                pts = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
            if net not in self.netmap:
                self.problems.append("rail pour on %s, which is not in the netlist" % net)
                continue
            z = pcbnew.ZONE(self.board)
            z.SetLayer(pcbnew.In2_Cu)
            z.SetNet(self.netmap[net])
            z.SetAssignedPriority(prio)
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
            z.SetLocalClearance(mm(0.3)); z.SetMinThickness(mm(0.2))
            z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
            o = z.Outline(); o.NewOutline()
            for (x, y) in pts:
                o.Append(mm(x), mm(y))
            self.board.Add(z)
        for layer in ([pcbnew.B_Cu] if self.B["layers"] == 2 else [pcbnew.In1_Cu, pcbnew.B_Cu]):
            z = pcbnew.ZONE(self.board)
            z.SetLayer(layer)
            z.SetNet(self.netmap["GND"])
            z.SetAssignedPriority(0)
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
            z.SetThermalReliefGap(mm(0.3)); z.SetThermalReliefSpokeWidth(mm(0.5))
            z.SetLocalClearance(mm(0.3)); z.SetMinThickness(mm(0.2))
            z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
            o = z.Outline(); o.NewOutline()
            m = 0.3
            for (x, y) in ((m, m), (G.BOARD - m, m), (G.BOARD - m, G.BOARD - m), (m, G.BOARD - m)):
                o.Append(mm(x), mm(y))
            self.board.Add(z)
        self.board.BuildConnectivity()
        pcbnew.ZONE_FILLER(self.board).Fill(self.board.Zones())

    # ------------------------------------------------------------- silkscreen --
    def _line(self, a, b, layer=pcbnew.F_SilkS, width=SILK_W):
        if abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6:
            return
        s = pcbnew.PCB_SHAPE(self.board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pt(*a)); s.SetEnd(pt(*b))
        s.SetLayer(layer); s.SetWidth(mm(width))
        self.board.Add(s)

    def _circle(self, cx, cy, r, filled=False, width=SILK_W, layer=pcbnew.F_SilkS):
        s = pcbnew.PCB_SHAPE(self.board)
        s.SetShape(pcbnew.SHAPE_T_CIRCLE)
        s.SetCenter(pt(cx, cy)); s.SetEnd(pt(cx + r, cy))
        s.SetFilled(filled); s.SetWidth(mm(width)); s.SetLayer(layer)
        self.board.Add(s)

    def _arc(self, cx, cy, r, a0, sweep, width=SILK_W):
        s = pcbnew.PCB_SHAPE(self.board)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        s.SetCenter(pt(cx, cy))
        s.SetStart(pt(cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0))))
        s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(sweep, pcbnew.DEGREES_T), True)
        s.SetLayer(pcbnew.F_SilkS); s.SetWidth(mm(width))
        self.board.Add(s)

    def _rect(self, x0, y0, x1, y1, width=0.15, layer=pcbnew.F_SilkS):
        for (a, b) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
            for (p, q) in self.clip(a, b):
                self._line(p, q, layer, width)

    def _text(self, x, y, txt, size, thickness=0.15, justify="center", angle=0, layer=pcbnew.F_SilkS):
        t = pcbnew.PCB_TEXT(self.board)
        t.SetText(txt)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
        t.SetTextThickness(mm(thickness))
        t.SetLayer(layer)
        if layer == pcbnew.B_SilkS:
            t.SetMirrored(True)
        t.SetTextAngleDegrees(angle)
        t.SetHorizJustify({"center": pcbnew.GR_TEXT_H_ALIGN_CENTER, "left": pcbnew.GR_TEXT_H_ALIGN_LEFT, "right": pcbnew.GR_TEXT_H_ALIGN_RIGHT}[justify])
        t.SetPosition(pt(x, y))
        self.board.Add(t)
        return t

    def keepouts(self):
        boxes = []
        self.silk_boxes = []
        self.silk_items = []
        for ref, fp in self.fps.items():
            ext = None
            for item in fp.GraphicalItems():
                if item.GetLayer() != pcbnew.F_SilkS:
                    continue
                b = item.GetBoundingBox()
                e = (tomm(b.GetLeft()), tomm(b.GetTop()), tomm(b.GetRight()), tomm(b.GetBottom()))
                self.silk_items.append(e)
                ext = e if ext is None else (min(ext[0], e[0]), min(ext[1], e[1]), max(ext[2], e[2]), max(ext[3], e[3]))
            if ext is not None:
                self.silk_boxes.append(ext)
        for p in self.pad_list:
            boxes.append((p["x0"] - SILK_CLEAR, p["y0"] - SILK_CLEAR, p["x1"] + SILK_CLEAR, p["y1"] + SILK_CLEAR))
        for (sx0, sy0, sx1, sy1) in self.silk_items:          # a wire's silk stops short of a footprint's own silk
            boxes.append((sx0 - 0.3, sy0 - 0.3, sx1 + 0.3, sy1 + 0.3))
        for ref, fp in self.fps.items():
            if ref[:2] in ("TP", "MH"):
                continue
            poly = fp.GetCourtyard(pcbnew.F_CrtYd)
            if poly.OutlineCount():
                bb = poly.BBox()
                boxes.append((tomm(bb.GetLeft()) - 0.3, tomm(bb.GetTop()) - 0.3, tomm(bb.GetRight()) + 0.3, tomm(bb.GetBottom()) + 0.3))
        self.boxes = boxes
        return boxes

    def clip(self, a, b):
        """Pieces of segment a-b outside every keep-out box (Liang-Barsky)."""
        (x1, y1), (x2, y2) = a, b
        dx, dy = x2 - x1, y2 - y1
        cuts = []
        for (bx0, by0, bx1, by1) in self.boxes:
            t0, t1, ok = 0.0, 1.0, True
            for p, q in ((-dx, x1 - bx0), (dx, bx1 - x1), (-dy, y1 - by0), (dy, by1 - y1)):
                if abs(p) < 1e-9:
                    if q < 0:
                        ok = False
                        break
                    continue
                r = q / p
                if p < 0:
                    t0 = max(t0, r)
                else:
                    t1 = min(t1, r)
            if ok and t0 < t1:
                cuts.append((max(0.0, t0), min(1.0, t1)))
        cuts.sort()
        pieces, t = [], 0.0
        for (c0, c1) in cuts:
            if c0 > t:
                pieces.append((t, c0))
            t = max(t, c1)
        if t < 1.0:
            pieces.append((t, 1.0))
        out = []
        for (p0, p1) in pieces:
            if (p1 - p0) * math.hypot(dx, dy) < 0.25:
                continue
            out.append(((x1 + dx * p0, y1 + dy * p0), (x1 + dx * p1, y1 + dy * p1)))
        return out

    def trim_edge_silk(self):
        """Silk of a footprint that overhangs the board (the USB-C's face) would sit on the edge: drop those lines."""
        for ref, fp in self.fps.items():
            for item in list(fp.GraphicalItems()):
                if item.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                    continue
                b = item.GetBoundingBox()
                if tomm(b.GetRight()) > G.BOARD - 0.3 or tomm(b.GetLeft()) < 0.3 or tomm(b.GetBottom()) > G.BOARD - 0.3 or tomm(b.GetTop()) < 0.3:
                    fp.Remove(item)

    def silk_wires(self):
        self.keepouts()
        hopset = set()
        for (_, a, b) in self.hops:
            hopset.add((round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3)))
            hopset.add((round(b[0], 3), round(b[1], 3), round(a[0], 3), round(a[1], 3)))
        backset = {(round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3)) for (_, a, b) in self.back}
        for (net, a, b, layer) in self.segments:
            if net == "GND":
                continue
            key = (round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3))
            if key in self.nosilk:
                continue
            if key in backset:
                for (p, q) in self.clip(a, b):
                    self._line(p, q, width=0.12)
                continue
            if key in hopset:
                cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
                r = 0.5
                if abs(a[1] - b[1]) < 1e-6:
                    self._line(a, (cx - r, cy)); self._line((cx + r, cy), b); self._arc(cx, cy, r, 180, 180)
                else:
                    self._line(a, (cx, cy - r)); self._line((cx, cy + r), b); self._arc(cx, cy, r, 270, 180)
                continue
            for (p, q) in self.clip(a, b):
                self._line(p, q)
        # junction dots where three or more ends of one net meet, or an end lies on another segment of its net
        count = {}
        for (net, a, b, layer) in self.segments:
            for e in (a, b):
                k = (net, round(e[0], 2), round(e[1], 2))
                count[k] = count.get(k, 0) + 1
        for (net, a, b, layer) in self.segments:
            if net == "GND":
                continue
            for e in (a, b):
                for (n2, c, d, l2) in self.segments:
                    if n2 != net or (c, d) == (a, b):
                        continue
                    if self._interior(e, c, d):
                        k = (net, round(e[0], 2), round(e[1], 2))
                        count[k] = max(count[k], 3)
        for (net, x, y), n in count.items():
            if net != "GND" and n >= 3 and not self._on_pad(x, y) and not self._on_silk(x, y, 0.65):
                self._circle(x, y, 0.45, filled=True, width=0)

    def _on_silk(self, x, y, r):
        for (x0, y0, x1, y1) in self.silk_boxes:
            if x0 - r <= x <= x1 + r and y0 - r <= y <= y1 + r:
                return True
        return False

    @staticmethod
    def _interior(p, a, b, tol=0.01):
        (px, py), (ax, ay), (bx, by) = p, a, b
        if abs(ay - by) < tol and abs(py - ay) < tol:
            return min(ax, bx) + tol < px < max(ax, bx) - tol
        if abs(ax - bx) < tol and abs(px - ax) < tol:
            return min(ay, by) + tol < py < max(ay, by) - tol
        return False

    def _on_pad(self, x, y, reach=0.55):
        for p in self.pad_list:
            if p["x0"] - reach <= x <= p["x1"] + reach and p["y0"] - reach <= y <= p["y1"] + reach:
                return True
        return False

    def silk_grounds(self):
        for (net, x, y) in self.vias:
            if net != "GND" or (round(x, 3), round(y, 3)) in self.fence_vias:
                continue
            ux, uy = self.stub_dir.get((round(x, 3), round(y, 3)), (0, 1))
            self.ground_symbol(x, y, ux, uy)

    def ground_symbol(self, x, y, ux, uy, start=0.5):
        px, py = -uy, ux
        s0 = start + 0.35
        self._line((x + ux * start, y + uy * start), (x + ux * s0, y + uy * s0))
        for i, w in enumerate((1.3, 0.85, 0.4)):
            s = s0 + i * 0.35
            cx, cy = x + ux * s, y + uy * s
            self._line((cx - px * w / 2, cy - py * w / 2), (cx + px * w / 2, cy + py * w / 2), width=0.25)

    def _hits(self, obst, box, clear):
        """Whether a box (board mm) comes within `clear` of any obstacle: a box, or a segment with its half-width."""
        rects, segs = obst
        x0, y0, x1, y1 = box
        for (a, b, c, d) in rects:
            if a - clear < x1 and c + clear > x0 and b - clear < y1 and d + clear > y0:
                return True
        for (ax, ay, bx, by, hw) in segs:
            r = hw + clear
            if max(ax, bx) + r < x0 or min(ax, bx) - r > x1 or max(ay, by) + r < y0 or min(ay, by) - r > y1:
                continue
            n = max(1, int(math.hypot(bx - ax, by - ay) / 0.1))
            for k in range(n + 1):
                px, py = ax + (bx - ax) * k / n, ay + (by - ay) * k / n
                if x0 - r < px < x1 + r and y0 - r < py < y1 + r:
                    return True
        return False

    def frame_texts(self):
        """Where every jack's name and every tile's title go: ON the tile's own frame line, the frame broken round them.
        A jack's name stands beside its jack (clear of its legs), slid sideways if a drawn wire is under it; a title on the
        top frame as far right as it fits, clear of pads, bodies, wires, the jack names (its own and the neighbours' across
        the gutter, by 0.8 mm along and 0.5 mm across) and the other titles.  A name in a frame belongs to that frame; in
        the gutter it read as the neighbour's (Prompt 14)."""
        obst = self._obstacles()
        out, taken = {}, []
        for t in self.tiles:
            h = t.h
            names = []
            for j in t.jacks:
                if j.get("label_at"):
                    continue
                name = j.get("silk") or j["label"]
                top = j["y"] < h / 2
                b = self._text_box(name, JACK_SIZE, JACK_THICK, "center")
                ay = t.y0 + j["y"] - 3.64 - 0.22 - b[3] if top else t.y0 + j["y"] + 3.64 + 0.22 - b[1]
                ax = t.x0 + j["x"]
                for dx in [0.0] + [k * 0.25 * sgn for k in range(1, 19) for sgn in (1, -1)]:     # up to 4.5 mm (R10's OUT A-)
                    box = (ax + dx + b[0], ay + b[1], ax + dx + b[2], ay + b[3])
                    if abs(dx) > 3.0 and (box[0] < t.x0 + 0.6 or box[2] > t.x0 + t.w - 0.6):
                        continue                               # the long slides stay inside the tile (the first 3 mm as before)
                    if not self._hits(obst, box, 0.2):
                        ax += dx
                        break
                else:
                    self.problems.append("%s: the jack name %r has no clear place on the frame" % (t.id, name))
                    for dx in (-4.0, -3.0, -2.0, 0.0, 2.0):           # what is in the way, in tile mm
                        box = (ax + dx + b[0], ay + b[1], ax + dx + b[2], ay + b[3])
                        hit = [tuple(round(v - o, 2) for v, o in zip(r, (t.x0, t.y0, t.x0, t.y0))) for r in obst[0]
                               if r[0] - 0.2 < box[2] and r[2] + 0.2 > box[0] and r[1] - 0.2 < box[3] and r[3] + 0.2 > box[1]]
                        segs = [tuple(round(v, 2) for v in (sx0 - t.x0, sy0 - t.y0, sx1 - t.x0, sy1 - t.y0)) for (sx0, sy0, sx1, sy1, hw) in obst[1]
                                if min(sx0, sx1) - hw - 0.2 < box[2] and max(sx0, sx1) + hw + 0.2 > box[0] and min(sy0, sy1) - hw - 0.2 < box[3] and max(sy0, sy1) + hw + 0.2 > box[1]]
                        self.problems.append("   dx %.1f box %s: rects %s segs %s" % (dx, tuple(round(v, 2) for v in (box[0] - t.x0, box[1] - t.y0, box[2] - t.x0, box[3] - t.y0)), hit[:4], segs[:4]))
                names.append((ax, ay, name, JACK_SIZE, JACK_THICK, (ax + b[0], ay + b[1], ax + b[2], ay + b[3])))
            out[t.id] = names
            taken += [n[5] for n in names]
        for t in self.tiles:
            inset = 0.3 if t.supply is None else 0.55
            for title in getattr(t, "titles", None) or []:
                b = self._text_box(title, TITLE_SIZE, TITLE_THICK, "left")
                placed = False
                for yc in (inset, 0.2):                        # centred on the frame line, else level with the jacks' names
                    ay = t.y0 + yc - (b[1] + b[3]) / 2.0
                    x = t.x0 + t.w - 0.9 - b[2]
                    while x + b[0] > t.x0 + 1.0:
                        box = (x + b[0], ay + b[1], x + b[2], ay + b[3])
                        if not self._hits(obst, box, 0.2) and \
                                not any(c - 0.8 < box[2] and a + 0.8 > box[0] and d - 0.5 < box[3] and bb + 0.5 > box[1] for (a, bb, c, d) in taken):
                            placed = True
                            break
                        if t.id in os.environ.get("TITLE_DEBUG", "").split(","):
                            hit = [tuple(round(v - o, 2) for v, o in zip(r, (t.x0, t.y0, t.x0, t.y0))) for r in obst[0]
                                   if r[0] - 0.2 < box[2] and r[2] + 0.2 > box[0] and r[1] - 0.2 < box[3] and r[3] + 0.2 > box[1]]
                            nm = [tuple(round(v - o, 2) for v, o in zip(r, (t.x0, t.y0, t.x0, t.y0))) for r in taken
                                  if r[2] - 0.8 < box[2] and r[0] + 0.8 > box[0] and r[3] - 0.5 < box[3] and r[1] + 0.5 > box[1]]
                            print("   title %s y %.2f x %.2f: rects %s names %s" % (t.id, yc, x - t.x0, hit[:3], nm[:2]))
                        x -= 0.25
                    if placed:
                        break
                if not placed:
                    self.warnings.append("%s: no room on the frame for the title %r" % (t.id, title))
                    continue
                out[t.id].append((x, ay, title, TITLE_SIZE, TITLE_THICK, box, "left"))
                taken.append(box)
        return out

    def silk_tiles(self):
        """Frames, legends, value labels and jack names."""
        self.warnings = []
        on_frame = self.frame_texts()
        for t in self.tiles:
            x0, y0, w, h = t.x0, t.y0, t.w, t.h
            thick = 0.15 if t.supply is None else 0.6
            inset = 0.3 if t.supply is None else 0.55
            # each jack's name sits ON its own tile's frame, beside the jack, the frame broken round it: a name in a frame
            # belongs to that frame, where a name in the gutter read as the neighbour's (Prompt 14)
            names = on_frame.get(t.id, [])
            for n in names:
                bx0, by0, bx1, by1 = n[5]
                self.boxes.append((bx0 - 0.35, by0 - 0.1, bx1 + 0.35, by1 + 0.1))
            # and any of the tile's own texts that sits on the frame line breaks it the same way (A1's socket pins)
            for (lx, ly, s_, size, thk, just, ang) in t.texts:
                if ang:
                    continue
                b = self._text_box(s_, size, thk, just)
                bx0, by0, bx1, by1 = x0 + lx + b[0], y0 + ly + b[1], x0 + lx + b[2], y0 + ly + b[3]
                for fy in (y0 + inset, y0 + h - inset):
                    if by0 - 0.05 < fy < by1 + 0.05 and bx1 > x0 and bx0 < x0 + w:
                        self.boxes.append((bx0 - 0.35, by0 - 0.1, bx1 + 0.35, by1 + 0.1))
            self._rect(x0 + inset, y0 + inset, x0 + w - inset, y0 + h - inset, width=thick)
            for n in names:
                self._text(n[0], n[1], n[2], n[3], n[4], justify=n[6] if len(n) > 6 else "center")
            for (lx, ly, s, size, thk, just, ang) in t.texts:
                self._text(x0 + lx, y0 + ly, s, size, thk, justify=just, angle=ang)
            for d in getattr(t, "draws", []):                  # a symbol drawn on the silk (the mixer's diode ring)
                if d[0] == "line":
                    for a, b in zip(d[1][:-1], d[1][1:]):
                        self._line((x0 + a[0], y0 + a[1]), (x0 + b[0], y0 + b[1]), width=0.15)
                elif d[0] == "arc":
                    self._arc(x0 + d[1], y0 + d[2], d[3], d[4], d[5], width=0.15)
            for ref, p in t.parts.items():
                fp = self.fps.get(ref)
                if fp is None:
                    continue
                fp.Reference().SetVisible(False)
                v = fp.Value()
                v.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8))); v.SetTextThickness(mm(0.15)); v.SetTextAngleDegrees(0)
                v.SetLayer(pcbnew.F_SilkS)
                if p.key == "TP":
                    v.SetVisible(False)
                    continue
                if p.label is None or p.hide_value:
                    v.SetVisible(False)
                    continue
                dx, dy, just, size = p.label[:4]
                v.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
                v.SetVisible(True)
                v.SetPosition(pt(x0 + p.x + dx, y0 + p.y + dy))
                v.SetTextAngleDegrees(p.label[4] if len(p.label) > 4 else 0)
                v.SetHorizJustify({"left": pcbnew.GR_TEXT_H_ALIGN_LEFT, "right": pcbnew.GR_TEXT_H_ALIGN_RIGHT, "center": pcbnew.GR_TEXT_H_ALIGN_CENTER}[just])
            # a jack's name where the tile puts it; the rest are placed inside the tile by place_labels()
            for j in t.jacks:
                name = j.get("silk") or j["label"]
                if j.get("label_at"):
                    dx, dy, just, size = j["label_at"]
                    self._text(x0 + j["x"] + dx, y0 + j["y"] + dy, name, size, 0.15, justify=just)
            # the test loops: name where the tile says, else under the loop
            for ref, p in t.parts.items():
                if p.key == "TP" and p.value:
                    if p.label == "hide":
                        continue
                    if p.label:
                        dx, dy, just, size = p.label[:4]
                        self._text(x0 + p.x + dx, y0 + p.y + dy, p.value, size, 0.15, justify=just, angle=p.label[4] if len(p.label) > 4 else 0)
                    else:
                        self._text(x0 + p.x, y0 + p.y + (1.9 if p.rot in (0, 180) else 2.9), p.value, 0.8, 0.15, justify="center")

    # ------------------------------------------------------- label placement --
    def _text_box(self, txt, size, thickness, justify):
        """KiCad's box for `txt` drawn at (0, 0) with this justification, in mm relative to the anchor."""
        t = pcbnew.PCB_TEXT(self.board)
        t.SetText(txt)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
        t.SetTextThickness(mm(thickness))
        t.SetLayer(pcbnew.F_SilkS)
        t.SetHorizJustify({"center": pcbnew.GR_TEXT_H_ALIGN_CENTER, "left": pcbnew.GR_TEXT_H_ALIGN_LEFT, "right": pcbnew.GR_TEXT_H_ALIGN_RIGHT}[justify])
        t.SetPosition(pt(0, 0))
        b = t.GetBoundingBox()
        return (tomm(b.GetLeft()), tomm(b.GetTop()), tomm(b.GetRight()), tomm(b.GetBottom()))

    def _obstacles(self):
        """Everything a label must not touch, in board mm: every front silk line (as a segment with its half-width), every
        other front silk item, footprint text, pad and courtyard (as a box)."""
        rects, segs = [], []
        def box(b):
            return (tomm(b.GetLeft()), tomm(b.GetTop()), tomm(b.GetRight()), tomm(b.GetBottom()))
        for d in self.board.GetDrawings():
            d = d.Cast() if hasattr(d, "Cast") else d
            if d.GetLayer() != pcbnew.F_SilkS:
                continue
            if isinstance(d, pcbnew.PCB_SHAPE) and d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
                a, b = d.GetStart(), d.GetEnd()
                segs.append((tomm(a.x), tomm(a.y), tomm(b.x), tomm(b.y), tomm(d.GetWidth()) / 2.0))
            else:
                rects.append(box(d.GetBoundingBox()))
        for ref, fp in self.fps.items():
            for item in fp.GraphicalItems():
                if item.GetLayer() == pcbnew.F_SilkS:
                    rects.append(box(item.GetBoundingBox()))
            for f in (fp.Value(), fp.Reference()):
                if f.IsVisible() and f.GetLayer() == pcbnew.F_SilkS:
                    rects.append(box(f.GetBoundingBox()))
            if ref[:1] == "J" and fp.GetFPID().GetLibItemName().wx_str().startswith("SMA"):
                continue                                       # a jack: its pads (below) and its body (the pads' extent) only
            poly = fp.GetCourtyard(pcbnew.F_CrtYd)
            if poly.OutlineCount():
                rects.append(box(poly.BBox()))
        for p in self.pad_list:
            rects.append((p["x0"], p["y0"], p["x1"], p["y1"]))
        return rects, segs                                     # vias are tented: text may cross them

    LBL_RES = 0.1                                              # the placement raster, mm
    LBL_CLEAR = 0.22                                           # silk to anything (the rule is 0.15; KiCad's text box is not the glyphs)

    def _raster(self, t, rects, segs):
        """A tile's free area as rows of bytes (1 = taken) at LBL_RES, its frame and outside it taken."""
        R, C = self.LBL_RES, self.LBL_CLEAR
        nx, ny = int(round(t.w / R)), int(round(t.h / R))
        grid = [bytearray(nx) for _ in range(ny)]
        def mark(x0, y0, x1, y1):
            i0, i1 = max(0, int(math.floor((x0 - t.x0) / R))), min(nx, int(math.ceil((x1 - t.x0) / R)))
            j0, j1 = max(0, int(math.floor((y0 - t.y0) / R))), min(ny, int(math.ceil((y1 - t.y0) / R)))
            if i0 >= i1:
                return
            ones = b"\x01" * (i1 - i0)
            for j in range(j0, j1):
                grid[j][i0:i1] = ones
        for (x0, y0, x1, y1) in rects:
            if x1 < t.x0 or x0 > t.x0 + t.w or y1 < t.y0 or y0 > t.y0 + t.h:
                continue
            mark(x0 - C, y0 - C, x1 + C, y1 + C)
        for (ax, ay, bx, by, hw) in segs:
            if max(ax, bx) < t.x0 or min(ax, bx) > t.x0 + t.w or max(ay, by) < t.y0 or min(ay, by) > t.y0 + t.h:
                continue
            r = hw + C
            if abs(ax - bx) < 1e-6 or abs(ay - by) < 1e-6:
                mark(min(ax, bx) - r, min(ay, by) - r, max(ax, bx) + r, max(ay, by) + r)
            else:
                n = int(math.hypot(bx - ax, by - ay) / 0.05) + 1
                for k in range(n + 1):
                    x, y = ax + (bx - ax) * k / n, ay + (by - ay) * k / n
                    mark(x - r, y - r, x + r, y + r)
        inset = (0.3 + 0.075 if t.supply is None else 0.55 + 0.3) + C   # the frame's inner edge
        mark(t.x0, t.y0, t.x0 + t.w, t.y0 + inset)
        mark(t.x0, t.y0 + t.h - inset, t.x0 + t.w, t.y0 + t.h)
        mark(t.x0, t.y0, t.x0 + inset, t.y0 + t.h)
        mark(t.x0 + t.w - inset, t.y0, t.x0 + t.w, t.y0 + t.h)
        return grid, mark

    def _free(self, t, grid, x0, y0, x1, y1):
        R = self.LBL_RES
        nx, ny = len(grid[0]), len(grid)
        i0, i1 = int(math.floor((x0 - t.x0) / R)), int(math.ceil((x1 - t.x0) / R))
        j0, j1 = int(math.floor((y0 - t.y0) / R)), int(math.ceil((y1 - t.y0) / R))
        if i0 < 0 or j0 < 0 or i1 > nx or j1 > ny:
            return False
        for j in range(j0, j1):
            if grid[j].find(1, i0, i1) != -1:
                return False
        return True

    def _search(self, t, grid, boxes, prefer, reach, ok=None):
        """The anchor nearest `prefer` (board mm), within `reach` of it, where every box (relative to the anchor) is free."""
        px, py = prefer
        step = 0.2
        n = int(reach / step)
        cands = []
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                d = math.hypot(i, j * 1.3)                     # a little more willing to slide sideways than up and down
                if d * step <= reach:
                    cands.append((d, px + i * step, py + j * step))
        cands.sort()
        for (_, ax, ay) in cands:
            if ok and not ok(ax, ay):
                continue
            if all(self._free(t, grid, ax + b[0], ay + b[1], ax + b[2], ay + b[3]) for b in boxes):
                return ax, ay
        return None

    def place_labels(self):
        """Each tile's information lines (what it is, its ranges and levels) in the nearest free place to where the tile
        asks: nothing touches a pad, a body or another silk item."""
        rects, segs = self._obstacles()
        placed = []
        for t in self.tiles:
            grid, mark = self._raster(t, rects, segs)
            if t.id in os.environ.get("LABEL_DEBUG", "").split(","):         # the tile's free area as a picture, for a label that will not fit
                with open(os.path.join(HW, "..", "out", "label_debug_%s.pbm" % t.id), "w") as fh:
                    fh.write("P1\n%d %d\n" % (len(grid[0]), len(grid)))
                    for row in grid:
                        fh.write(" ".join(str(v) for v in row) + "\n")
            for info in getattr(t, "infos", None) or []:
                size = info.get("size", 0.8)
                pitch = size * 1.75
                just = info.get("justify", "left")
                prefer = (t.x0 + info["near"][0], t.y0 + info["near"][1])
                at, lines = None, list(info["lines"])
                while lines:                                   # the whole block, else without its last lines (a warning)
                    boxes = []
                    for k, line in enumerate(lines):
                        b = self._text_box(line, size, 0.15, just)
                        boxes.append((b[0], b[1] + k * pitch, b[2], b[3] + k * pitch))
                    at = self._search(t, grid, boxes, prefer, info.get("reach", 30.0))
                    if at is not None:
                        break
                    lines.pop()
                if at is None:
                    self.warnings.append("%s: no room for any of %r" % (t.id, info["lines"]))
                    continue
                if len(lines) < len(info["lines"]):
                    self.warnings.append("%s: dropped %r (no room)" % (t.id, info["lines"][len(lines):]))
                for k, line in enumerate(lines):
                    self._text(at[0], at[1] + k * pitch, line, size, 0.15, justify=just)
                for b in boxes:
                    mark(at[0] + b[0] - self.LBL_CLEAR, at[1] + b[1] - self.LBL_CLEAR, at[0] + b[2] + self.LBL_CLEAR, at[1] + b[3] + self.LBL_CLEAR)
                placed.append((t.id, lines[0], round(at[0] - t.x0, 2), round(at[1] - t.y0, 2)))
        self.label_places = placed

    def silk_board(self):
        """Identity along the top margin, the ground loops' names, the corners."""
        B = self.B
        self._text(50, 1.7, B["name"] + "   " + B["title"].split(":", 1)[1].strip(), 1.5, 0.28)
        self._text(50, 3.9, "%s   rev %s   %s   %s" % (parts.AUTHORS, parts.REV, parts.DATE, parts.URL), 0.9, 0.15)
        self._text(50, 5.4, B["subtitle"], 0.8, 0.15)
        for i, (gx, gy) in enumerate(self.meta["gnd_loops"]):
            self._text(gx, gy - 1.9, "GND", 0.9, 0.15)
        for (fx, fy, s) in self.meta.get("front_text", []):
            self._text(fx, fy, s, 0.8, 0.15)

    def silk_back(self):
        """The back: the name and the makers in the top margin, the user's notes in the bottom margin, the QR code
        under a cell with no holes in its lower half (every other place on the back has a jack's five holes)."""
        B = self.B
        self._text(50, 2.6, B["name"] + "   " + B["title"].split(":", 1)[1].strip(), 1.8, 0.3, layer=pcbnew.B_SilkS)
        self._text(50, 5.2, "%s, rev %s, %s   %s" % (parts.AUTHORS, parts.REV, parts.DATE, parts.URL), 1.0, 0.15, layer=pcbnew.B_SilkS)
        lines = self.meta["back_text"]
        for i, line in enumerate(lines):
            self._text(self.meta.get("back_text_x", 50.0), BACK_Y + i * BACK_PITCH, line, 0.8, 0.15, justify="center", layer=pcbnew.B_SilkS)
        # stick-on rubber feet where a board has no mounting holes: an 8 mm circle on the back for each, clear of every hole
        for (fx, fy) in self.meta.get("feet", []):
            self._circle(fx, fy, FOOT_R, layer=pcbnew.B_SilkS)
            self._text(fx, fy, "FOOT", 0.8, 0.15, justify="center", layer=pcbnew.B_SilkS)
            for key, p in self.pads.items():
                if p["through"] and math.hypot(p["x"] - fx, p["y"] - fy) < FOOT_R + 1.0:
                    self.problems.append("foot at (%.1f, %.1f): through-hole pad %s under it" % (fx, fy, key))
            for (n2, vx, vy) in self.vias:
                pass                                          # tented vias under a foot are fine
        qx, qy = self.meta.get("qr_at") or QR_AT
        n, rects = self.add_qr("https://" + parts.URL, qx, qy, QR_MODULE)
        half = n * QR_MODULE / 2
        for i, line in enumerate(("github.com/gallicchio/", "AMOD-and-RFMOD", "handbook and generator")):
            self._text(qx, qy + half + 1.5 + 1.4 * i, line, 0.8, 0.15, justify="center", layer=pcbnew.B_SilkS)

    def add_qr(self, url, cx, cy, module):
        import qrcode_gen
        m = qrcode_gen.encode(url, "L")
        n = len(m)
        x0, y0 = cx - n * module / 2.0, cy - n * module / 2.0
        rects = []
        for r in range(n):
            c = 0
            while c < n:
                if not m[r][c]:
                    c += 1
                    continue
                a = c
                while c < n and m[r][c]:
                    c += 1
                sh = pcbnew.PCB_SHAPE(self.board)
                sh.SetShape(pcbnew.SHAPE_T_RECT)
                sh.SetStart(pt(x0 + (n - c) * module, y0 + r * module))
                sh.SetEnd(pt(x0 + (n - a) * module, y0 + (r + 1) * module))
                sh.SetFilled(True); sh.SetWidth(0); sh.SetLayer(pcbnew.B_SilkS)
                self.board.Add(sh)
                rects.append((x0 + (n - c) * module, y0 + r * module, x0 + (n - a) * module, y0 + (r + 1) * module))
        for key, p in self.pads.items():
            if p["through"] and x0 - 1 < p["x"] < x0 + n * module + 1 and y0 - 1 < p["y"] < y0 + n * module + 1:
                self.problems.append("QR: through-hole pad %s is under the code" % (key,))
        return n, len(rects)

    def fiducials(self):
        for (x, y) in (self.meta.get("fiducials") or FIDUCIALS):              # a board may move them off its parts
            for layer, r in ((pcbnew.F_Cu, 0.5), (pcbnew.F_Mask, 1.0)):
                c = pcbnew.PCB_SHAPE(self.board)
                c.SetShape(pcbnew.SHAPE_T_CIRCLE)
                c.SetLayer(layer)
                c.SetStart(pt(x, y)); c.SetEnd(pt(x + r, y))
                c.SetFilled(True); c.SetWidth(0)
                self.board.Add(c)

    # ------------------------------------------------------------------ all --
    def build(self):
        self.place()
        self.wires()
        self.back_wires()
        self.front_wires()
        self.autoroute()
        self.rf_fences()
        self.trim_edge_silk()
        self.plane()
        self.silk_wires()
        self.silk_grounds()
        self.silk_tiles()
        self.silk_board()
        self.place_labels()
        self.silk_back()
        self.fiducials()
        stabilise_uuids(self.board)
        pcbnew.SaveBoard(self.out_path, self.board)
        self.export_geometry()
        return self

    def export_geometry(self):
        pads = [dict(ref=k[0], pad=k[1], net=p["net"], x=p["x"], y=p["y"], w=p["x1"] - p["x0"], h=p["y1"] - p["y0"], through=p["through"])
                for k, p in self.pads.items()]
        path = os.path.join(os.path.dirname(self.out_path), "..", "out", self.stem + "_geom.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump({"board_w": G.BOARD, "board_h": G.BOARD, "layers": self.B["layers"], "pads": pads, "tracks": len(self.segments),
                   "vias": len(self.vias), "hops": len(self.hops)}, open(path, "w"), indent=1)


def stabilise_uuids(board):
    import uuid as _uuid

    def kiid(key):
        return pcbnew.KIID(str(_uuid.uuid5(_uuid.NAMESPACE_URL, "amod-pcb://" + key)))

    def mm2(pos):
        return "%.4f,%.4f" % (tomm(pos.x), tomm(pos.y))

    n = 0
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        fp.SetUuid(kiid("fp/" + ref))
        for pad in fp.Pads():
            n += 1
            pad.SetUuid(kiid("fp/%s/pad/%s/%s/%d" % (ref, pad.GetNumber(), mm2(pad.GetPosition()), n)))
        for i, it in enumerate(fp.GraphicalItems()):
            it.SetUuid(kiid("fp/%s/gfx/%d/%s" % (ref, i, it.GetClass())))
        for f in fp.GetFields():
            f.SetUuid(kiid("fp/%s/field/%s" % (ref, f.GetName())))
    for i, t in enumerate(board.GetTracks()):
        if isinstance(t, pcbnew.PCB_VIA):
            t.SetUuid(kiid("via/%s/%s/%d" % (mm2(t.GetPosition()), t.GetNetname(), i)))
        else:
            t.SetUuid(kiid("trk/%s/%s/%s/%s/%d" % (t.GetLayerName(), mm2(t.GetStart()), mm2(t.GetEnd()), t.GetNetname(), i)))
    for i, z in enumerate(board.Zones()):
        z.SetUuid(kiid("zone/%s/%s/%d" % (z.GetLayerName(), z.GetNetname(), i)))
    for i, d in enumerate(board.GetDrawings()):
        txt = d.GetText() if hasattr(d, "GetText") else ""
        d.SetUuid(kiid("gfx/%s/%s/%s/%s/%d" % (d.GetLayerName(), d.GetClass(), mm2(d.GetPosition()), txt[:40], i)))


if __name__ == "__main__":
    stem = sys.argv[1]
    netlist = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HW, "..", "out", stem + ".net")
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HW, stem + ".kicad_pcb")
    b = Board(stem, netlist, out).build()
    ntr = sum(1 for t in b.board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA))
    print("  wrote %s: %d footprints, %d tracks, %d vias, %d hops" % (os.path.relpath(out), len(b.fps), ntr, len(b.vias), len(b.hops)))
    for w in getattr(b, "warnings", []):
        print("  silk: " + w)
    if b.problems:
        print("  !! %d wiring problem(s):" % len(b.problems))
        for p in b.problems:
            print("     " + p)
        raise SystemExit(1)
