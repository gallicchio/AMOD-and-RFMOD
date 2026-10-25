"""The tile: one circuit on a 20 x 20 mm cell (or two cells) with its SMA jacks, its parts, the
wires that are laid as copper and drawn on the silkscreen, its legend and its expected response.

A tile declares its NETLIST once (every part's pins to local net names); the schematic drawing
(a function of a drawing context, gen_sch.SchCtx) and the board layout (parts at local
coordinates plus the wires) both have to reproduce it, and the build checks both against it:
the exported KiCad netlist against `netlist()`, and every wire endpoint against the pad's net.

Local coordinates are millimetres from the tile's top-left corner, y down.  Reference designators
are the tile's number times 100 plus a counter: P5's parts are R501, C502, J501 ...

The standard two-port layout (see PLAN.md section 2):

    jack IN at slot TL, jack OUT at slot TR, their bodies at y 1.5 .. 8.0
    the tile's number between the jacks at (W/2, 3.0)
    the signal line at y = LINE_Y, from the IN pin's x to the OUT pin's x, series parts on it
    shunts hanging down from the line to a ground via, the ground symbol under it
    the name at y = NAME_Y, the sections at y = SECT_Y, a plot sketch at an end with no shunt
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "sim"))
import geometry as G
import parts as PARTS

LINE_Y = 10.6          # the signal line: the jacks' legs end at y 8.39, an 0805 capacitor's pads on the line start at 9.875
LABEL_Y = 9.0          # series parts' values, above the line: KiCad's box for 0.8 mm text runs 0.5 above and 0.7 below
LOOP_Y = 16.6          # the test loops, lying along x under the jacks (pad 15.5 .. 17.7)
ID_Y = 2.4             # the tile's number between the jacks' legs
SECT_Y0, SECT_PITCH = 4.4, 1.35   # the tutorial sections, one under the other below the number (3.2 mm between the legs)
NAME_Y = 18.6          # the name, under the loops (0.9 mm text: 18.0 .. 19.4; the frame's line is at 19.7)
W_SIG, W_RAIL = 0.35, 0.6
# nominal half pad spacing (centre to pad centre) and body half-width across, by package
PAD = {"0805": 0.95, "0603": 0.775, "0402": 0.485, "1206": 1.4, "1210": 1.4, "2512": 2.95}
BODY_W = {"0805": 1.25, "0603": 0.8, "0402": 0.5, "1206": 1.6, "1210": 2.5, "2512": 3.2}
PITCH = {"0805": 3.6, "0603": 3.0, "0402": 2.2, "1206": 4.6, "1210": 4.6}
HX = {"0805": 1.45, "0603": 1.25, "0402": 0.8, "1206": 1.9, "1210": 2.05, "2512": 3.6}     # a part's half extent along its axis, pads included
# KiCad's courtyards (half extents along the part and across it): what two neighbours must keep apart
CRT = {"0805": (1.68, 0.98), "0603": (1.48, 0.73), "0402": (0.91, 0.46), "1206": (2.28, 1.25), "1210": (2.28, 1.58), "2512": (3.60, 1.90)}


def text_w(s, size=0.8):
    """About how wide KiCad's DRC box for `s` is (an em a character plus a little; the glyphs themselves are narrower)."""
    return len(s) * size + 0.3


class Part:
    def __init__(self, ref, key, value, x, y, rot=0, pins=None, label=None, hide_value=False, hide_ref=True, sch=None):
        self.ref, self.key, self.value = ref, key, value
        self.x, self.y, self.rot = x, y, rot
        self.pins = dict(pins or {})          # pad number (str) -> local net
        self.label = label                    # (dx, dy, justify, size) for the value on the silk, or None
        self.hide_value, self.hide_ref = hide_value, hide_ref
        self.sch = sch                        # anything the schematic drawer wants to remember

    def __repr__(self):
        return "Part(%s %s %s at %.2f,%.2f r%d %r)" % (self.ref, self.key, self.value, self.x, self.y, self.rot, self.pins)


class Tile:
    def __init__(self, id, name, cells, supply=None, subtitle="", sections=(), kind="passive"):
        self.id, self.idx = id, int(id[1:])
        self.name, self.subtitle, self.sections = name, subtitle, list(sections)
        self.cells = list(cells)
        self.supply, self.kind = supply, kind
        self.jacks = []            # dicts: slot, label, net, role, limit, ref
        self.parts = {}            # ref -> Part (insertion ordered)
        self.wires = []            # (net, [points], width, layer); a point is (x, y) or (ref, pad)
        self.vias = []             # (net, x, y): rail vias
        self.routes = []           # (net, [specs], width): for the router
        self.pwr_flags = []        # local nets that drive power pins without a power-output pin (the schematic flags them)
        self.hops = []             # (net, a, b)
        self.gnd_stubs = []        # ((ref, pad), point or [points])
        self.texts = []            # (x, y, text, size, thickness, justify, angle)
        self.notes = []            # schematic notes (strings)
        self.plot = None           # dict(kind, x, y, xlabel, ylabel, title) with x, y in 0..1
        self.result = ""           # the one-line expected result ("-3 dB at 8.9 MHz")
        self.sim = {}              # numbers the documents quote
        self.sch_draw = None       # f(ctx, tile)
        self._counts = {}
        self.x0, self.y0, self.w, self.h = G.tile_frame(self.cells)

    # ---------------------------------------------------------------- nets --
    def net(self, local):
        if local in ("GND",) or local.startswith("+") or local.startswith("-") or local.startswith("/"):
            return local
        return "/%s_%s" % (self.id, local)

    def new_ref(self, prefix):
        n = self._counts.get(prefix, 0) + 1
        self._counts[prefix] = n
        return "%s%d%02d" % (prefix, self.idx, n)

    def add(self, prefix, key, value, x, y, rot=0, pins=None, label=None, ref=None, hide_value=False, hide_ref=True, sch=None):
        ref = ref or self.new_ref(prefix)
        assert ref not in self.parts, ref
        p = Part(ref, key, value, x, y, rot, {str(k): self.net(v) for k, v in (pins or {}).items()}, label, hide_value, hide_ref, sch)
        self.parts[ref] = p
        return ref

    def jack(self, slot, label, net, role="in", limit="", ref=None, label_at=None, silk=None):
        """A jack in a slot; its name goes in the gutter above (top slots) or below (bottom slots) unless label_at =
        (dx, dy, justify, size) puts it elsewhere relative to the jack's centre."""
        x, y = G.slot(self.cells, slot)
        ref = self.add("J", "SMA", label, x, y, 0, {"1": net, "2": "GND"}, ref=ref, hide_value=True)
        self.jacks.append(dict(slot=slot, label=label, net=self.net(net), role=role, limit=limit, ref=ref, x=x, y=y, label_at=label_at, silk=silk or label))
        return ref

    def loop(self, net, x, y, rot=0, label=None, label_at=None):
        """An RH-5019 test loop on `net`; its silk label is the net's name unless given, drawn at label_at =
        (dx, dy, justify, size) from the loop's centre (default: under it; "hide": no silk name)."""
        return self.add("TP", "TP", label if label is not None else net, x, y, rot, {"1": net}, label=label_at, hide_value=False)

    def wire(self, net, pts, width=W_SIG, layer="F.Cu", silk=True):
        """Copper along pts (and silk, when on the front, unless silk=False).  On "B.Cu" the wire runs on the back with
        a via at each end that is a coordinate (a pad end needs none when the pad is through-hole; an SMD pad end gets
        one beside it)."""
        self.wires.append((self.net(net), list(pts), width, layer, silk))

    def via(self, net, x, y):
        """A via on `net` at (x, y): a tile's connection to a rail pour on the inner layer."""
        self.vias.append((self.net(net), x, y))

    def route(self, net, specs, width=W_SIG):
        """Let the board generator find the path between these pads / points (scripts/router.py), on the front where
        it can and on the back with vias where it must; the silk draws what it finds."""
        self.routes.append((self.net(net), list(specs), width))

    def hop(self, net, a, b):
        self.hops.append((self.net(net), a, b))

    def gnd_stub(self, ref, pad, pt, sym=None):
        """Copper from the pad to a ground via at `pt` (or along a path); the ground symbol is drawn on from the via
        in the stub's direction unless `sym` (a unit vector) says otherwise."""
        self.gnd_stubs.append(((ref, str(pad)), pt, sym))

    def text(self, x, y, s, size=0.8, thick=0.15, justify="left", angle=0):
        self.texts.append((x, y, s, size, thick, justify, angle))

    # --------------------------------------------------------------- frame --
    def to_board(self, pt):
        return (self.x0 + pt[0], self.y0 + pt[1])

    def netlist(self):
        out = []
        for p in self.parts.values():
            for pad, net in p.pins.items():
                out.append((p.ref, pad, net))
        return out

    def nets(self):
        return sorted({n for _, _, n in self.netlist()})

    def jack_pin(self, slot):
        return G.slot(self.cells, slot)

    def legend(self, at=None):
        """The standard texts: the number between the jacks (smaller when it has three characters: the legs leave
        3.2 mm), the sections one under the other below it, the name under the loops.  `at` moves the number and the
        sections' column (a tile with one jack)."""
        w = self.w
        x = w / 2 if at is None else at
        size = 1.5 if len(self.id) <= 2 else 0.9           # three characters at 1.5 would reach the legs' pads
        self.text(x, ID_Y, self.id, size, 0.3 if size > 1.3 else 0.17, "center")
        if self.supply:                     # a powered tile: the switch and FET own the bottom-left; a short name at the bottom right
            self.text(w - 1.1, 18.2, (self.name + ((" " + self.subtitle) if self.subtitle else "")).upper(), 0.8, 0.15, "right")
        else:
            self.text(1.2, NAME_Y, self.name.upper() + ((" " + self.subtitle) if self.subtitle else ""), 0.9, 0.17, "left")
        for i, s in enumerate(self.sections[:3]):
            self.text(x, SECT_Y0 + SECT_PITCH * i, s, 0.8, 0.15, "center")


# ------------------------------------------------------------------------------------------------
HDR_SW = (2.75, 15.6)        # the slide switch along the left edge (rot 270: pads at x 4.7, y 13.35 / 16.35 / 17.85; slider up = ON)
HDR_Q = (7.6, 18.1)          # the P-FET right of the switch's foot (rot 0: G 6.66,17.15  S 6.66,19.05  D 8.54,18.1)
HDR_VIA = (5.7, 19.05)       # the rail via between the switch's pads and the FET's source
HDR_VS = (8.54, 18.1)        # where the tile's own rail starts: the drain


def power_header(tile, rail="+5V", local="VS"):
    """A powered tile's switch at the standard places (HDR_*): the MSK12C02 standing along the left edge below the IN
    stub, its common (pad 2) to the P-FET's gate, pad 1 (slider up: ON) to ground and pad 3 to the rail, so the gate
    is either grounded (on) or at the source (off); the AO3401A at the switch's foot with its source on the rail
    through the via beside it and its drain the tile's own `local` rail, which the tile routes on from HDR_VS.
    Returns dict(sw, q)."""
    sx, sy = HDR_SW
    qx, qy = HDR_Q
    sw = tile.add("SW", "SW_SLIDE", "ON", sx, sy, 270, {"1": "GND", "2": "G", "3": rail}, hide_value=True)
    q = tile.add("Q", "PFET", "AO3401A", qx, qy, 0, {"1": "G", "2": rail, "3": local}, hide_value=True)
    tile.gnd_stub(sw, "1", (sx + 1.95, sy - 0.75), sym=(0, 0))          # between pads 1 and 2, no symbol (the switch's own ground)
    tile.via(rail, HDR_VIA[0], HDR_VIA[1])
    tile.wire(rail, [(q, "2"), HDR_VIA])
    tile.wire(rail, [(sw, "3"), (HDR_VIA[0], sy + 2.25), HDR_VIA])
    tile.route("G", [(sw, "2"), (q, "1")])
    tile.pwr_flags.append(local)
    return dict(sw=sw, q=q)


def unit(v):
    """Pretty value: 1.5e-6 -> '1.5u', 220e-12 -> '220p', 61.9 -> '61.9'."""
    for mult, suf in ((1e6, "M"), (1e3, "k"), (1.0, ""), (1e-3, "m"), (1e-6, "u"), (1e-9, "n"), (1e-12, "p")):
        if abs(v) >= mult * 0.9999:
            s = "%.3g" % (v / mult)
            return s + suf
    return "%.3g" % v


def ladder(tile, elements, loops=True, Rs=50.0, Rl=50.0, fspan=(1e4, 1e8), hiz_out=False, line_y=None, xs=None, labels=None):
    """A two-port ladder between the IN (TL) and OUT (TR) jacks.

    elements: a list, in order from IN to OUT, of
        ("series", key, value)                  one part on the line (key: "R0805", "C0805", "L0603" ...)
        ("shunt", [(key, value), ...])          one or two parts in parallel from that node to ground
    The board layout, the netlist, the schematic drawing and the simulated response are all made here.

    The row of series parts is centred between the stubs, their courtyards apart by what leaves the node between
    them (a wire, one shunt, two side by side); `xs` places them by hand instead.  A row wider than the jacks (P7)
    gets an L-shaped entry round each end.  An end node's single shunt hangs outside the stub (at x_in - 1.9), a
    double shunt's second part inside the row.  Values sit above the line (LABEL_Y), slid off the stubs' columns,
    a middle shunt's beside it, a 1210's below; `labels` = {part index: (dx, dy, justify, size)} overrides them.
    The test loops lie under the jacks at LOOP_Y, their names between them."""
    import passive as P
    LY = LINE_Y if line_y is None else line_y
    labels = labels or {}
    series = [e for e in elements if e[0] == "series"]
    n_s = len(series)
    pkgs = [e[1][1:] for e in series]
    x_in, x_out = tile.jack_pin("TL")[0], tile.jack_pin("TR")[0]
    shunt_at, shunt_pkg = {}, {}
    k = 0
    for e in elements:
        if e[0] == "series":
            k += 1
        else:
            shunt_at[k] = len(e[1])
            shunt_pkg[k] = [p[0][1:] for p in e[1]]

    def pair_dx(pk):                        # a pair's parts sit at xm -/+ this: their courtyards 0.4 apart
        return CRT[pk][1] + 0.2

    def room(node):                         # what a node between two series parts needs between their courtyards
        n = shunt_at.get(node, 0)
        if n == 0:
            return 0.3
        pk = shunt_pkg[node][0]
        if n == 1:
            return 2 * CRT[pk][1] + 0.5
        return 2 * (pair_dx(pk) + CRT[pk][1]) + 0.5

    if xs is None and n_s:
        gaps = [CRT[pkgs[i]][0] + CRT[pkgs[i + 1]][0] + room(i + 1) for i in range(n_s - 1)]
        left_in = (2 * CRT[shunt_pkg[0][0]][1] + 0.5) if shunt_at.get(0) == 2 else 0.0
        right_in = (2 * CRT[shunt_pkg[n_s][0]][1] + 0.5) if shunt_at.get(n_s) == 2 else 0.0
        total = left_in + CRT[pkgs[0]][0] + sum(gaps) + CRT[pkgs[-1]][0] + right_in
        x0 = x_in + left_in + CRT[pkgs[0]][0] + (x_out - x_in - total) / 2
        xs = [x0]
        for gp in gaps:
            xs.append(xs[-1] + gp)
    xs = list(xs or [])
    if n_s:
        first_pad, last_pad = xs[0] - PAD[pkgs[0]] - 0.5, xs[-1] + PAD[pkgs[-1]] + 0.5     # the end pads' outer edges
        l_entry = first_pad < x_in + 0.3            # the stub cannot land beside the row: an L round its end
        r_entry = last_pad > x_out - 0.3
    else:
        l_entry = r_entry = False
    assert not (l_entry and shunt_at.get(0)), (tile.id, "no room for IN's shunt beside the row")
    assert not (r_entry and shunt_at.get(n_s)), (tile.id, "no room for OUT's shunt beside the row")
    tile.jack("TL", "IN", "IN", "in", "±4 V")
    tile.jack("TR", "OUT", "OUT", "out", "")

    def node_net(k):
        return "IN" if k == 0 else ("OUT" if k == n_s else "N%d" % k)

    ENTRY_Y = LY - 1.4                              # an L-shaped entry runs here: under the legs, above the pads
    x_left = x_in if not l_entry else xs[0] - PAD[pkgs[0]]           # where the line starts: the stub's foot or pad 1
    x_right = x_out if not r_entry else xs[-1] + PAD[pkgs[-1]]
    if l_entry:
        tile.wire("IN", [("J%d01" % tile.idx, "1"), (x_in, ENTRY_Y), (x_left, ENTRY_Y), (x_left, LY)])
    else:
        tile.wire("IN", [("J%d01" % tile.idx, "1"), (x_in, LY)])
    if r_entry:
        tile.wire("OUT", [("J%d02" % tile.idx, "1"), (x_out, ENTRY_Y), (x_right, ENTRY_Y), (x_right, LY)])
    else:
        tile.wire("OUT", [("J%d02" % tile.idx, "1"), (x_out, LY)])

    def series_label(x, pkg, text):
        """Above the line, centred on the part; slid off a stub's column; a 1210's below its pads."""
        if pkg == "1210":
            return (0, 2.1, "center", 0.8)
        w = text_w(text)
        dy = LABEL_Y - LY
        for sx in (x_in, x_out):
            if x - w / 2 < sx + 0.45 and x + w / 2 > sx - 0.45:
                return (sx - 0.45 - x, dy, "right", 0.8) if x < sx else (sx + 0.45 - x, dy, "left", 0.8)
        return (0, dy, "center", 0.8)

    # the points each node joins along the line: the ends, the series pads, the shunts' tops
    node_items = {k: [] for k in range(n_s + 1)}
    node_items[0].append((x_left, (x_left, LY)))
    node_items[n_s].append((x_right, (x_right, LY)))
    refs, elems_sim = [], []
    k = si = 0
    for e in elements:
        if e[0] == "series":
            key, value = e[1], e[2]
            pkg, prefix = key[1:], key[0]
            x = xs[si]
            fullkey = PARTS.passive_key(prefix, pkg, value)
            vtext = fullkey.split(" ", 1)[1]
            lab = labels.get(len(refs), series_label(x, pkg, vtext))
            ref = tile.add(prefix, fullkey, vtext, x, LY, 0, {"1": node_net(k), "2": node_net(k + 1)}, label=lab, hide_value=False)
            refs.append(ref)
            node_items[k].append((x - PAD[pkg], (ref, "1")))
            node_items[k + 1].append((x + PAD[pkg], (ref, "2")))
            si += 1
            k += 1
            kind = {"R": P.R, "C": P.C, "L": P.L}[prefix]
            elems_sim.append(("series", kind(value) if prefix != "L" else P.L(value, 0.5)))
        else:
            parts_ = e[1]
            pk0 = parts_[0][0][1:]
            if k == 0:
                xa = x_in - 1.9
                xb = (x_in + xs[0] - CRT[pkgs[0]][0]) / 2 if n_s else x_in + 1.9
            elif k == n_s:
                xa = (xs[-1] + CRT[pkgs[-1]][0] + x_out) / 2 if n_s else x_out - 1.9
                xb = x_out + 1.9
            else:
                xm = (xs[si - 1] + CRT[pkgs[si - 1]][0] + xs[si] - CRT[pkgs[si]][0]) / 2
                xa, xb = xm - pair_dx(pk0), xm + pair_dx(pk0)
            if len(parts_) == 1:
                xss = [xa] if k == 0 else ([xb] if k == n_s else [xm])
            else:
                xss = [xa, xb]
            arm = []
            for j, ((key, value), xsh) in enumerate(zip(parts_, xss)):
                pkg, prefix = key[1:], key[0]
                yc = LY + 0.55 + PAD[pkg]
                fullkey = PARTS.passive_key(prefix, pkg, value)
                vtext = fullkey.split(" ", 1)[1]
                if k == 0 and xsh < x_in:
                    lab = (x_in - 0.35 - xsh, LABEL_Y - yc, "right", 0.8)
                elif k == n_s and xsh > x_out:
                    lab = (x_out + 0.35 - xsh, LABEL_Y - yc, "left", 0.8)
                elif k in (0, n_s):                          # the inside part of an end pair: above, off the stub's column
                    lab = series_label(xsh, pkg, vtext)
                    lab = (lab[0] + 0, LABEL_Y - yc, lab[2], 0.8)
                elif len(parts_) == 2 and j == 0:
                    lab = (-(CRT[pkg][1] + 0.15), 0, "right", 0.8)
                else:
                    lab = (CRT[pkg][1] + 0.15, 0, "left", 0.8)
                lab = labels.get(len(refs), lab)
                ref = tile.add(prefix, fullkey, vtext, xsh, yc, 270, {"1": node_net(k), "2": "GND"}, label=lab, hide_value=False)
                refs.append(ref)
                tile.wire(node_net(k), [(xsh, LY), (ref, "1")])
                tile.gnd_stub(ref, "2", (xsh, yc + PAD[pkg] + 0.75))
                node_items[k].append((xsh, (xsh, LY)))
                kind = {"R": P.R, "C": P.C, "L": P.L}[prefix]
                arm.append(kind(value) if prefix != "L" else P.L(value, 0.5))
            elems_sim.append(("shunt", P.parallel_arm(*arm) if len(arm) > 1 else arm[0]))
    for k_, items in node_items.items():
        items.sort(key=lambda it: it[0])
        if len(items) >= 2:
            tile.wire(node_net(k_), [spec for _, spec in items])
    # the test loops under the jacks, their names between them
    if loops:
        for net, xj, xl, lab in (("IN", x_in, x_left, (2.4, 0, "left", 0.8)), ("OUT", x_out, x_right, (-2.4, 0, "right", 0.8))):
            ref = tile.loop(net, xj, LOOP_Y, 0, net, label_at=lab)
            tile.wire(net, [(xl, LY), (xl, LOOP_Y), (ref, "1")])
    # the response
    f = P.logspace(*fspan)
    h = P.response(elems_sim, f, Rs, 1e6 if hiz_out else Rl)
    g = P.db(h)
    tile.sim.update(dict(f=f.tolist(), db=g.tolist(), f3=P.corner(f, g), peak=P.peak(f, g)))
    tile.plot = dict(kind="bode", x=(f - f.min()), y=g, xlabel="f", ylabel="dB")
    tile.elements = elements
    tile.sch_draw = lambda ctx, t: draw_ladder(ctx, t)
    tile.legend()
    return refs


def refs_series(tile, refs):
    return [r for r in refs if tile.parts[r].rot == 0 and tile.parts[r].key[0] in "RCL"]


# --------------------------------------------------------------- the schematic of a ladder --
def draw_ladder(ctx, t):
    """IN jack on the left, the series parts along a line, shunts to ground, OUT on the right."""
    y = ctx.oy + 30.48
    x = ctx.ox + 12.7
    jin = ctx.jack(t.jacks[0]["ref"], x, y, "in", t.jacks[0]["label"], t.jacks[0]["limit"])
    xcur = jin[0] + 5.08
    ctx.wire([jin, (xcur, y)])
    ctx.label(t.jacks[0]["net"].lstrip("/"), xcur, y)
    series_refs = [r for r, p in t.parts.items() if r[0] in "RCL" and p.rot == 0]
    shunt_refs = [r for r, p in t.parts.items() if r[0] in "RCL" and p.rot == 270]
    n_series = sum(1 for e in t.elements if e[0] == "series")
    si = shunt_i = k = 0
    for e in t.elements:
        if e[0] == "series":
            ref = series_refs[si]; si += 1
            pins = ctx.part(ref, xcur + 3.81, y, rot=90)      # horizontal, pin 1 on the left
            ctx.wire([(xcur, y), pins["1"]])
            xcur = pins["2"][0]
            ctx.wire([pins["2"], (xcur + 2.54, y)])
            xcur += 2.54
            k += 1
            if k < n_series:
                ctx.label("%s_N%d" % (t.id, k), xcur, y)
        else:
            n = len(e[1])
            if n == 1:
                ref = shunt_refs[shunt_i]; shunt_i += 1
                xs = xcur + 2.54
                pins = ctx.part(ref, xs, y + 7.62, rot=0, side="right")
                ctx.wire([(xcur, y), (xs, y), pins["1"]])
                ctx.junction(xs, y)
                ctx.gnd(xs, pins["2"][1] + 1.27)
                ctx.wire([pins["2"], (xs, pins["2"][1] + 1.27)])
                ctx.wire([(xs, y), (xs + 2.54, y)])
                xcur = xs + 2.54
            else:
                xa, xb = xcur + 2.54, xcur + 10.16
                ctx.wire([(xcur, y), (xb, y)])
                for xs_, side in ((xa, "left"), (xb, "right")):
                    ref = shunt_refs[shunt_i]; shunt_i += 1
                    pins = ctx.part(ref, xs_, y + 7.62, rot=0, side=side)
                    ctx.wire([(xs_, y), pins["1"]])
                    ctx.junction(xs_, y)
                    ctx.gnd(xs_, pins["2"][1] + 1.27)
                    ctx.wire([pins["2"], (xs_, pins["2"][1] + 1.27)])
                ctx.wire([(xb, y), (xb + 2.54, y)])
                xcur = xb + 2.54
    ctx.label(t.jacks[1]["net"].lstrip("/"), xcur, y)
    jout = ctx.jack(t.jacks[1]["ref"], xcur + 7.62, y, "out", t.jacks[1]["label"], t.jacks[1]["limit"])
    ctx.wire([(xcur, y), jout])
    for r, p in t.parts.items():
        if p.key != "TP":
            continue
        if p.pins["1"] == t.jacks[0]["net"]:
            ctx.loop(r, jin[0] + 2.54, y, p.value)
        elif p.pins["1"] == t.jacks[1]["net"]:
            ctx.loop(r, xcur + 1.27, y, p.value, dx=0.8, justify="left")
    ctx.result_note(t)


def dump(tiles, mod, path):
    """Everything gen_pcb.py needs, as JSON, so it can run under KiCad's own Python (no numpy there)."""
    import json
    out = {"tiles": [], "gnd_loops": list(getattr(mod, "GND_LOOPS", [])), "back_text": list(getattr(mod, "BACK_TEXT", [])),
           "slots": list(getattr(mod, "SLOTS", [])), "front_text": list(getattr(mod, "FRONT_TEXT", [])), "rail_pours": list(getattr(mod, "RAIL_POURS", [])),
           "stem": getattr(mod, "STEM", "")}
    for t in tiles:
        out["tiles"].append(dict(
            id=t.id, idx=t.idx, name=t.name, subtitle=t.subtitle, sections=t.sections, cells=t.cells, supply=t.supply,
            x0=t.x0, y0=t.y0, w=t.w, h=t.h, result=t.result,
            jacks=[dict(j) for j in t.jacks],
            parts=[dict(ref=p.ref, key=p.key, value=p.value, x=p.x, y=p.y, rot=p.rot, pins=p.pins, label=p.label,
                        hide_value=p.hide_value) for p in t.parts.values()],
            wires=[(n, [list(q) for q in pts], w, layer, silk) for (n, pts, w, layer, silk) in t.wires],
            vias=[(n, x, y) for (n, x, y) in t.vias],
            routes=[(n, [list(q) for q in sp], w) for (n, sp, w) in t.routes],
            hops=[(n, list(a), list(b)) for (n, a, b) in t.hops],
            gnd_stubs=[(list(pr), (list(pt) if isinstance(pt, tuple) else [list(q) for q in pt]), (list(sym) if sym else None)) for (pr, pt, sym) in t.gnd_stubs],
            texts=[list(x) for x in t.texts], slots=[list(x) for x in getattr(t, "slots", [])]))
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    return path
