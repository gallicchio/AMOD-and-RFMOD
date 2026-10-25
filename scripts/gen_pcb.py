#!/usr/bin/env python3
"""Build a board from its tiles: the outline and holes, every tile's parts where its layout puts
them, the tiles' wires as copper AND as silkscreen (clipped round pads and bodies, so the picture
is the netlist), hops on the back layer, a ground via at every ground stub with the schematic's
ground symbol drawn at it, the planes, the tile frames and legends, the jack names in the gutters,
the identity, the QR code and the back text.  No autorouter: every track is a drawn wire.

Runs under KiCad's bundled Python (it needs pcbnew):
    <AppRun> python3.11 scripts/gen_pcb.py amod_p out/amod_p.net hardware/amod_p.kicad_pcb
"""
import json, math, os, sys
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
        t.wires = [(n, [tuple(q) if isinstance(q[0], str) else (float(q[0]), float(q[1])) for q in pts], w) for (n, pts, w) in td["wires"]]
        t.hops = [(n, tuple(a), tuple(b)) for (n, a, b) in td["hops"]]
        t.gnd_stubs = [(tuple(pr), (tuple(pt) if not isinstance(pt[0], list) else [tuple(q) for q in pt]), (tuple(sym) if sym else None))
                       for (pr, pt, sym) in td["gnd_stubs"]]
        t.texts = [tuple(x) for x in td["texts"]]
        tiles.append(t)
    return tiles, d

HW = os.path.abspath(os.path.join(HERE, "..", "hardware"))
LOCAL_FP = os.path.join(HW, "lib", "amod.pretty")
SHARE_FP = None
SILK_W, SILK_CLEAR = 0.3, 0.3
VIA_DIA, VIA_DRILL = 0.6, 0.3
BOARD_RULES = dict(m_MinClearance=0.20, m_HoleClearance=0.30, m_HoleToHoleMin=0.50, m_CopperEdgeClearance=0.30, m_SilkClearance=0.15)
FIDUCIALS = [(3.5, 50.0), (96.5, 10.0), (96.5, 90.0)]
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
        for name, value in BOARD_RULES.items():
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
        self.segments, self.vias, self.hops = [], [], []
        self.stub_dir, self.via_at = {}, {}
        # placements: tile parts in board coordinates, plus the board-level parts
        self.place_table = {}
        for t in self.tiles:
            for ref, p in t.parts.items():
                bx, by = t.to_board((p.x, p.y))
                self.place_table[ref] = (bx, by, p.rot, t, p)
        for i, (hx, hy) in enumerate(G.HOLES):
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
                self.pads[(ref, pad.GetNumber())] = dict(
                    x=tomm(pad.GetPosition().x), y=tomm(pad.GetPosition().y),
                    x0=tomm(b.GetLeft()), y0=tomm(b.GetTop()), x1=tomm(b.GetRight()), y1=tomm(b.GetBottom()),
                    through=pad.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH), net=pad.GetNetname())
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

    def track(self, a, b, width, net, layer=pcbnew.F_Cu):
        if abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) < 1e-6:
            return
        tr = pcbnew.PCB_TRACK(self.board)
        tr.SetStart(pt(*a)); tr.SetEnd(pt(*b))
        tr.SetWidth(mm(width)); tr.SetLayer(layer)
        tr.SetNet(self.netmap[net])
        self.board.Add(tr)
        self.segments.append((net, a, b, layer))

    def via(self, x, y, net):
        key = (round(x, 3), round(y, 3))
        if key in self.via_at:
            assert self.via_at[key] == net, ("two nets want a via at", key)
            return
        self.via_at[key] = net
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(pt(x, y))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
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
            for (net, points, width) in t.wires:
                net = self.kname.get(net, net)
                if net not in self.netmap:
                    self.problems.append("%s: wire names a net that is not in the netlist: %r" % (t.id, net))
                    continue
                pts = [self.resolve(p, net, t) for p in points]
                for a, b in zip(pts, pts[1:]):
                    key = (net, (round(a[0], 3), round(a[1], 3)), (round(b[0], 3), round(b[1], 3)))
                    if key in hops:
                        self.via(*a, net); self.via(*b, net)
                        self.track(a, b, width, net, pcbnew.B_Cu)
                        self.hops.append((net, a, b))
                    else:
                        self.track(a, b, width, net)
            for (padref, path, sym) in t.gnd_stubs:
                pad = self.pads.get(padref)
                if pad is None:
                    raise SystemExit("%s: ground stub from %s: no such pad" % (t.id, padref))
                if pad["net"] != "GND":
                    self.problems.append("%s: ground stub from %s, which is on %r" % (t.id, padref, pad["net"]))
                pts = [(pad["x"], pad["y"])] + [t.to_board(q) for q in (path if isinstance(path, list) else [path])]
                for a, b in zip(pts, pts[1:]):
                    self.track(a, b, t.wires[0][2] if t.wires else 0.35, "GND")
                vx, vy = pts[-1]
                self.via(vx, vy, "GND")
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

    def plane(self):
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
        for ref, fp in self.fps.items():
            ext = None
            for item in fp.GraphicalItems():
                if item.GetLayer() != pcbnew.F_SilkS:
                    continue
                b = item.GetBoundingBox()
                e = (tomm(b.GetLeft()), tomm(b.GetTop()), tomm(b.GetRight()), tomm(b.GetBottom()))
                ext = e if ext is None else (min(ext[0], e[0]), min(ext[1], e[1]), max(ext[2], e[2]), max(ext[3], e[3]))
            if ext is not None:
                self.silk_boxes.append(ext)
        for key, p in self.pads.items():
            boxes.append((p["x0"] - SILK_CLEAR, p["y0"] - SILK_CLEAR, p["x1"] + SILK_CLEAR, p["y1"] + SILK_CLEAR))
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

    def silk_wires(self):
        self.keepouts()
        hopset = set()
        for (_, a, b) in self.hops:
            hopset.add((round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3)))
            hopset.add((round(b[0], 3), round(b[1], 3), round(a[0], 3), round(a[1], 3)))
        for (net, a, b, layer) in self.segments:
            if net == "GND":
                continue
            key = (round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3))
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
        for p in self.pads.values():
            if p["x0"] - reach <= x <= p["x1"] + reach and p["y0"] - reach <= y <= p["y1"] + reach:
                return True
        return False

    def silk_grounds(self):
        for (net, x, y) in self.vias:
            if net != "GND":
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

    def silk_tiles(self):
        """Frames, legends, value labels and jack names."""
        for t in self.tiles:
            x0, y0, w, h = t.x0, t.y0, t.w, t.h
            thick = 0.15 if t.supply is None else 0.6
            inset = 0.3 if t.supply is None else 0.55
            self._rect(x0 + inset, y0 + inset, x0 + w - inset, y0 + h - inset, width=thick)
            for (lx, ly, s, size, thk, just, ang) in t.texts:
                self._text(x0 + lx, y0 + ly, s, size, thk, justify=just, angle=ang)
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
            # the jack names in the gutter above (or below) each jack
            for j in t.jacks:
                if j.get("label_at"):
                    dx, dy, just, size = j["label_at"]
                    self._text(x0 + j["x"] + dx, y0 + j["y"] + dy, j["label"], size, 0.15, justify=just)
                elif j["slot"] in ("TL", "TR", "TM"):
                    self._text(x0 + j["x"], y0 - 0.8, j["label"], 1.0, 0.18, justify="center")
                else:
                    self._text(x0 + j["x"], y0 + h + 0.8, j["label"], 1.0, 0.18, justify="center")
            # the test loops: name where the tile says, else under the loop
            for ref, p in t.parts.items():
                if p.key == "TP" and p.value:
                    if p.label:
                        dx, dy, just, size = p.label[:4]
                        self._text(x0 + p.x + dx, y0 + p.y + dy, p.value, size, 0.15, justify=just, angle=p.label[4] if len(p.label) > 4 else 0)
                    else:
                        self._text(x0 + p.x, y0 + p.y + (1.9 if p.rot in (0, 180) else 2.9), p.value, 0.8, 0.15, justify="center")

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
        self._text(50, 2.6, B["name"].upper() + "   " + B["title"].split(":", 1)[1].strip(), 1.8, 0.3, layer=pcbnew.B_SilkS)
        self._text(50, 5.2, "%s, rev %s, %s   %s" % (parts.AUTHORS, parts.REV, parts.DATE, parts.URL), 1.0, 0.15, layer=pcbnew.B_SilkS)
        lines = self.meta["back_text"]
        for i, line in enumerate(lines):
            self._text(50.0, BACK_Y + i * BACK_PITCH, line, 0.8, 0.15, justify="center", layer=pcbnew.B_SilkS)
        qx, qy = QR_AT
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
        for (x, y) in FIDUCIALS:
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
        self.plane()
        self.silk_wires()
        self.silk_grounds()
        self.silk_tiles()
        self.silk_board()
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
    if b.problems:
        print("  !! %d wiring problem(s):" % len(b.problems))
        for p in b.problems:
            print("     " + p)
        raise SystemExit(1)
