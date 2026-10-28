#!/usr/bin/env python3
"""Draw a board's schematic: one A1 sheet, a block per tile laid out as the tiles sit on the board
(four columns, four rows), each block with its jacks, its circuit, its loops, its expected response
and the design note.  Every block is drawn by the tile's own `sch_draw(ctx, tile)` through the
SchCtx helpers below, from the same parts and nets the board uses; scripts/check_circuit.py then
compares KiCad's exported netlist with what the tiles declared.

    python3 scripts/gen_sch.py amod_p        writes hardware/amod_p.kicad_sch
"""
import importlib, math, os, sys, textwrap
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import kienv, parts
from schlib import Sheet

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.join(HERE, "..", "hardware")
G = 2.54
RAILS = ("+5V", "-5V", "+3V3", "+8V", "+15V", "-15V")      # nets drawn as KiCad power symbols (global)
BLOCK_W, BLOCK_H = 190.5, 127.0         # one cell's block on the sheet (75 x 50 grid units)
OX0, OY0 = 25.4, 30.48                  # the top-left block
LIB = parts.LIB


def g(n):
    return round(n * G, 4)


def snap(v):
    return round(round(v / 1.27) * 1.27, 4)


class SchCtx:
    """What a tile's drawing function gets: its block's origin and the helpers that place symbols and wires."""

    def __init__(self, sheet, tile, ox, oy, w, h):
        self.s, self.t, self.ox, self.oy, self.w, self.h = sheet, tile, ox, oy, w, h
        self.pwr_n = [0]
        self.flagged = set()
        self.notes_y = oy + h - 2.54

    # ------------------------------------------------------------- symbols --
    def _fields(self, key):
        d = parts.info(key)
        f = {}
        if d.get("lcsc"):
            f["LCSC"] = d["lcsc"]
        if d.get("mpn"):
            f["MPN"] = d["mpn"]
        return f, d

    def part(self, ref, x, y, rot=0, side="right", mirror=None, value=None, label_off=None, unit=1):
        """Place the tile's part `ref` at (x, y, rot); returns {pin: (x, y)} on the sheet.
        Two-terminal parts: rot 0 vertical (pin 1 up), rot 90 horizontal (pin 1 left)."""
        p = self.t.parts[ref]
        fields, d = self._fields(p.key)
        sym = d["symbol"]
        val = value if value is not None else (p.value if p.value else d.get("value", ""))
        if p.key in ("TP",):
            val = p.value
        hide_value = p.key in ("SMA", "DIP2", "DIP4", "DIP6", "MH", "TERM2", "TERM3") and p.key != "TP"
        if rot == 0 and sym in ("Device:R_US", "Device:C", "Device:L"):
            dx = 2.54 if side == "right" else -2.54
            j = "left" if side == "right" else "right"
            ro, vo = (dx, -1.27), (dx, 1.27)
        elif rot == 90 and sym in ("Device:R_US", "Device:C", "Device:L"):
            ro, vo, j = (0, -2.54), (0, 2.54), None
        elif sym in ("Device:LED", "Diode:1N4148W", "Device:Crystal"):
            if rot in (0, 180):
                ro, vo, j = (0, -2.8), (0, 2.8), None
            else:
                dx = 2.8 if side == "right" else -2.8
                j = "left" if side == "right" else "right"
                ro, vo = (dx, -1.27), (dx, 1.27)
        else:
            ro, vo, j = (0, -7.62), (0, 7.62), None
            if label_off:
                ro, vo = label_off
        self.s.place(sym, ref, val, x, y, rot=rot, mirror=mirror, footprint=d["footprint"], fields=fields, unit=unit,
                     ref_off=ro, val_off=vo, ref_justify=j, val_justify=j, hide_value=hide_value, in_bom=d.get("in_bom", True))
        return self.pins(ref)

    def pins(self, ref):
        p = self.t.parts[ref]
        d = parts.info(p.key)
        nums = self.s.all_pin_numbers(d["symbol"])
        return {n: self.s.pin(ref, 1, n) for n in nums}

    def jack(self, ref, x, y, role, label, limit=""):
        """An SMA jack.  An input is mirrored so its pin faces the circuit (right); an output faces left.  Returns pin 1."""
        p = self.t.parts[ref]
        fields, d = self._fields(p.key)
        mirror = "y" if role == "in" else None
        if role == "in":
            ro, vo, j = (-3.0, 1.6), (-3.0, 3.4), "right"
        else:
            ro, vo, j = (3.0, 1.6), (3.0, 3.4), "left"
        self.s.place(d["symbol"], ref, "SMA", x, y, mirror=mirror, footprint=d["footprint"], fields=fields,
                     ref_off=ro, val_off=vo, ref_justify=j, val_justify=j, hide_value=True)
        pin1, pin2 = self.s.pin(ref, 1, "1"), self.s.pin(ref, 1, "2")
        self.gnd(pin2[0], pin2[1] + 2.54)
        self.s.wire(pin2, (pin2[0], pin2[1] + 2.54))
        tx = x - 5.08 if role == "in" else x + 5.08
        self.s.text(label, tx, y - 6.2, size=2.5, justify="right" if role == "in" else "left")
        if limit:
            self.s.text(limit, tx, y - 3.0, size=1.1, justify="right" if role == "in" else "left")
        return pin1

    def loop(self, ref, x, y, name, rot=0, dx=-0.8, dy=-3.2, justify="right"):
        p = self.t.parts[ref]
        fields, d = self._fields(p.key)
        self.s.place(d["symbol"], ref, name, x, y, rot=rot, footprint=d["footprint"], fields=fields,
                     hide_ref=True, val_off=(dx, dy), val_justify=justify)
        self.s.junction(x, y)

    def gnd(self, x, y, up=False):
        self.pwr_n[0] += 1
        self.s.place("power:GND", "#PWR%s%03d" % (self.t.idx, self.pwr_n[0]), "GND", x, y, rot=180 if up else 0,
                     in_bom=False, on_board=False, hide_ref=True, hide_value=True)

    def wire(self, pts):
        self.s.wire(*[(round(a, 4), round(b, 4)) for a, b in pts])

    def junction(self, x, y):
        self.s.junction(x, y)

    def label(self, txt, x, y, justify="left"):
        self.s.label(txt, x, y, size=1.27, justify=justify)

    def text(self, txt, x, y, size=1.3, justify="left", bold=False):
        self.s.text(txt, x, y, size=size, justify=justify, bold=bold)

    # --------------------------------------------------------------- notes --
    def header(self):
        t = self.t
        self.s.rect(self.ox, self.oy, self.ox + self.w, self.oy + self.h, width=0.25)
        self.s.text("%s   %s%s" % (t.id, t.name, (", " + t.subtitle) if t.subtitle else ""), self.ox + 2.54, self.oy + 3.3, size=2.2, bold=True)
        if t.sections:
            self.s.text("tutorial " + ", ".join(t.sections) + ("   (%s)" % t.supply if t.supply else ""), self.ox + 2.54, self.oy + 6.6, size=1.3)
        self.s.text("cell%s %s" % ("s" if len(t.cells) > 1 else "", ", ".join("(%d,%d)" % c for c in t.cells)), self.ox + self.w - 2.54, self.oy + 3.3, size=1.1, justify="right")

    def _wrap(self, lines, size=1.2):
        width = int((self.w - 5.08) / (size * 0.92))
        out = []
        for line in lines:
            out += textwrap.wrap(line, width) or [""]
        return out

    def result_note(self, t, above=None):
        """The expected result and the notes along the block's bottom; smaller when the drawing above (`above`: its
        lowest y) leaves no room for 1.2 mm text."""
        for size in (1.2, 1.0, 0.9, 0.8):
            lines = self._wrap(["EXPECT: " + t.result], size) + self._wrap(t.notes, size)
            pitch = size * 2.2
            y = self.oy + self.h - 2.54 - pitch * (len(lines) - 1)
            if above is None or y - pitch >= above:
                break
        for i, line in enumerate(lines):
            self.s.text(line, self.ox + 2.54, y + pitch * i, size=size, bold=(i == 0))
        self.notes_y = y - pitch

    def note(self, t, lines):
        """Extra note lines above the result note."""
        for line in reversed(self._wrap(lines)):
            self.notes_y -= 2.6
            self.s.text(line, self.ox + 2.54, self.notes_y, size=1.2)

    # ------------------------------------------------------- drawers for the hand-laid tiles --
    def _chain(self):
        """Order the tile's two-terminal series parts from IN to OUT by following their nets."""
        t = self.t
        jin = [j for j in t.jacks if j["role"] == "in"][0]["net"]
        jout = [j for j in t.jacks if j["role"] == "out"][0]["net"]
        two = {r: p for r, p in t.parts.items() if r[0] in "RCLY" and len(p.pins) == 2 and "GND" not in p.pins.values()}
        chain, net, used = [], jin, set()
        while net != jout:
            nxt = [(r, p) for r, p in two.items() if r not in used and net in p.pins.values()]
            if not nxt:
                break
            r, p = nxt[0]
            other = [n for pin, n in p.pins.items() if n != net][0]
            pin_in = [pin for pin, n in p.pins.items() if n == net][0]
            chain.append((r, pin_in, other))
            used.add(r)
            net = other
        return chain

    def generic_series(self, t):
        """IN jack, the series chain of two-terminal parts, shunts (parts with a GND pin) at their node, OUT jack."""
        y = self.oy + 30.48
        x = self.ox + 12.7
        jin_j = [j for j in t.jacks if j["role"] == "in"][0]
        jout_j = [j for j in t.jacks if j["role"] == "out"][0]
        pin_in = self.jack(jin_j["ref"], x, y, "in", jin_j["label"], jin_j["limit"])
        xcur = pin_in[0] + 5.08
        self.wire([pin_in, (xcur, y)])
        self.label(jin_j["net"].lstrip("/"), xcur, y)
        loop_x = {jin_j["net"]: pin_in[0] + 2.54}
        node_x = {jin_j["net"]: xcur}
        shunts = {r: p for r, p in t.parts.items() if r[0] in "RCLD" and "GND" in p.pins.values() and len(p.pins) == 2}
        for r, pin_i, other in self._chain():
            p = t.parts[r]
            net_before = [n for pin, n in p.pins.items() if pin == pin_i][0]
            xcur = self._draw_shunts(shunts, net_before, xcur, y)
            rot = 90 if r[0] in "RCL" else 0
            pins = self.part(r, xcur + 3.81, y, rot=rot)
            left = min(pins, key=lambda k: pins[k][0]); right = max(pins, key=lambda k: pins[k][0])
            if left != pin_i:
                self.s.items.pop(); self.s.symbols.pop()
                pins = self.part(r, xcur + 3.81, y, rot=rot, mirror="y")
                left = min(pins, key=lambda k: pins[k][0]); right = max(pins, key=lambda k: pins[k][0])
            self.wire([(xcur, y), pins[left]])
            xcur = pins[right][0] + 2.54
            self.wire([pins[right], (xcur, y)])
            node_x[other] = xcur
            if other != jout_j["net"]:
                self.label(other.lstrip("/"), xcur, y)
        xcur = self._draw_shunts(shunts, jout_j["net"], xcur, y)
        pin_out = self.jack(jout_j["ref"], xcur + 7.62, y, "out", jout_j["label"], jout_j["limit"])
        self.wire([(xcur, y), pin_out])
        self.label(jout_j["net"].lstrip("/"), xcur, y)
        loop_x[jout_j["net"]] = xcur + 1.27
        for r, p in t.parts.items():
            if p.key == "TP" and p.pins["1"] in loop_x:
                if p.pins["1"] == jout_j["net"]:
                    self.loop(r, loop_x[p.pins["1"]], y, p.value, dx=0.8, justify="left")
                else:
                    self.loop(r, loop_x[p.pins["1"]], y, p.value)
        self.result_note(t)
        return node_x

    def _draw_shunts(self, shunts, net, xcur, y):
        here = [r for r, p in shunts.items() if net in p.pins.values()]
        for i, r in enumerate(here):
            p = self.t.parts[r]
            xs = xcur + 2.54
            top = [pin for pin, n in p.pins.items() if n == net][0]
            side = "right"
            if r[0] in "RCL":
                pins = self.part(r, xs, y + 7.62, rot=0 if top == "1" else 180, side=side)
            else:                                             # a diode: K is pin 1, on the left at rot 0; rot 90 puts pin 1 at the bottom
                pins = self.part(r, xs, y + 7.62, rot=90 if top == "2" else 270, side=side)
            self.wire([(xcur, y), (xs, y), pins[top]])
            self.junction(xs, y)
            bottom = [pin for pin in p.pins if pin != top][0]
            self.gnd(xs, pins[bottom][1] + 1.27)
            self.wire([pins[bottom], (xs, pins[bottom][1] + 1.27)])
            self.wire([(xs, y), (xs + 10.16, y)])
            xcur = xs + 10.16
            shunts.pop(r)
        return xcur

    # ------------------------------------------------------- the generic drawer for the active tiles --
    def netlist_block(self, t, chips_y=45.72, row_y=66.04):
        """Every part of the tile on the sheet with a label on every pin: the jacks at the left and right on a
        signal row, the chips (any part whose symbol is not a plain two-terminal) side by side on a second row, the
        two-terminal parts in rows below, each pin's net written at its end (ground as a ground symbol, the rails as
        power symbols).  Correct by construction and checked against the declared netlist like every other drawing;
        it is the first drawing of every active tile and some will stay this way."""
        s, ox, oy, w, h = self.s, self.ox, self.oy, self.w, self.h
        y_sig = oy + 30.48
        jin = [j for j in t.jacks if j["role"] == "in"]
        jout = [j for j in t.jacks if j["role"] != "in"]
        used_loops = set()
        for i, j in enumerate(jin):
            p = self.jack(j["ref"], ox + 12.7 + i * 25.4, y_sig, "in", j["label"], j["limit"])
            self.wire([p, (p[0] + 5.08, y_sig)])
            self.label(j["net"].lstrip("/"), p[0] + 5.08, y_sig)
        for i, j in enumerate(jout):
            p = self.jack(j["ref"], ox + w - 25.4 - i * 25.4, y_sig, "out", j["label"], j["limit"])
            self.wire([(p[0] - 5.08, y_sig), p])
            self.label(j["net"].lstrip("/"), p[0] - 5.08, y_sig, justify="right")
        simple = ("Device:R_US", "Device:C", "Device:L", "Device:LED", "Diode:1N4148W", "Device:Crystal", "Device:FerriteBead",
                  "Device:Thermistor_NTC", "Device:D_Photo", "Device:Polyfuse", "Diode:SMAJ5.0A", "Device:C_Polarized")
        chips, twos, loops = [], [], []
        for r, p in t.parts.items():
            if p.key in ("SMA", "MH", "SLOT"):
                continue
            if p.key == "TP":
                loops.append(r); continue
            d = parts.info(p.key)
            (twos if d["symbol"] in simple else chips).append(r)
        # the chips: side by side, each unit its own symbol (higher when the tile has no jacks: the signal row is empty)
        if not t.jacks:
            chips_y -= 12.7
        x = ox + 25.4
        row_h = 0.0
        low = oy + row_y - 7.62                               # the lowest chip value label: the two-terminal rows start below it
        for r in chips:
            d = parts.info(t.parts[r].key)
            lib = d["symbol"]
            for unit in s.units_of(lib):
                dirs = s.pin_dirs(lib, unit)
                if not dirs:
                    continue
                xs = [v[0] for v in dirs.values()]; ys = [v[1] for v in dirs.values()]
                half_w = max(abs(min(xs)), abs(max(xs)))

                def side_w(rot_in):                           # how far this side's labels reach past its pins
                    wmax = 1.27
                    for num, (px, py, rot) in dirs.items():
                        if int(rot) % 360 != rot_in:
                            continue
                        net = t.parts[r].pins.get(str(num))
                        if net is None:
                            continue
                        wmax = max(wmax, 5.08 if net == "GND" or net in RAILS else 3.81 + 1.0 * len(net.lstrip("/")))
                    return wmax
                lw, rw = side_w(0), side_w(180)
                if x > ox + 25.4 and x + lw + 2 * half_w + rw > ox + w - 2.54:    # no room left in this row: start another below
                    chips_y += row_h + 22.86
                    x = ox + 25.4
                    row_h = 0.0
                row_h = max(row_h, max(ys) - min(ys))
                xc = 2.54 * math.ceil((x + max(lw, 5.08) + half_w) / 2.54 - 1e-6)       # on the 2.54 grid
                pins = self.part(r, xc, oy + chips_y, rot=0, unit=unit, label_off=((0, -(max(ys) + 5.08)), (0, -(min(ys) - 5.08))))
                low = max(low, oy + chips_y - min(ys) + 5.08)
                done = set()
                seen = {}                                     # (side, net) -> the end of the first such pin's stub
                for num, (px, py, rot) in sorted(dirs.items(), key=lambda kv: (kv[1][2], kv[1][1], kv[1][0])):
                    if num not in pins or (round(pins[num][0], 2), round(pins[num][1], 2)) in done:
                        continue                              # stacked pins (a USB-C's four VBUS) get one label
                    done.add((round(pins[num][0], 2), round(pins[num][1], 2)))
                    net = t.parts[r].pins.get(str(num))
                    key = (int(rot) % 360, net)
                    near = False
                    if net is not None and net != "GND" and key in seen:
                        ex, ey = seen[key]
                        dx0, dy0 = {0: (-2.54, 0), 180: (2.54, 0), 90: (0, 2.54), 270: (0, -2.54)}[int(rot) % 360]
                        mx, my = pins[num][0] + dx0, pins[num][1] + dy0          # this stub's end
                        near = (abs(ex - mx) < 0.01 and abs(ey - my) <= 2.55) or (abs(ey - my) < 0.01 and abs(ex - mx) <= 2.55)
                    if near:
                        dx, dy = {0: (-2.54, 0), 180: (2.54, 0), 90: (0, 2.54), 270: (0, -2.54)}[int(rot) % 360]
                        end = (pins[num][0] + dx, pins[num][1] + dy)
                        self.wire([pins[num], end]); self.wire([end, seen[key]])    # a neighbour on the same net: one label
                        seen[key] = end
                        continue
                    self._pin_label(t, r, num, pins[num], rot)
                    if net is not None:
                        dx, dy = {0: (-2.54, 0), 180: (2.54, 0), 90: (0, 2.54), 270: (0, -2.54)}[int(rot) % 360]
                        seen[key] = (pins[num][0] + dx, pins[num][1] + dy)
                x = xc + half_w + rw + 2.54
        # the two-terminal parts in rows, horizontal, pin 1 on the left (symbols drawn vertical turn 90)
        vertical = ("Device:R_US", "Device:C", "Device:L", "Device:FerriteBead", "Device:Thermistor_NTC", "Device:Polyfuse", "Device:C_Polarized")
        x, y = ox + 15.24, max(oy + row_y, oy + 2.54 * math.ceil((low - oy + 7.62) / 2.54))
        longest = max([len(n.lstrip("/")) for r in twos for n in t.parts[r].pins.values() if n not in (("GND",) + RAILS)] or [4])
        pitch = max(30.48, 2.54 * math.ceil((12.7 + 2 * 1.0 * (longest + 1) + 2.54) / 2.54))      # two labels back to back between parts
        per_row = max(1, int((w - 25.4 - 15.24) // pitch) + 1)
        rows = -(-len(twos) // per_row)
        note_h = max(22.0, 2.54 + 1.98 * len(self._wrap(["EXPECT: " + t.result], 0.9) + self._wrap(t.notes, 0.9)) + 8.0)   # the result note at 0.9 mm
        step = 12.7 if rows < 2 or y + (rows - 1) * 12.7 < oy + h - note_h else max(7.62, 2.54 * math.floor((oy + h - note_h - y) / (rows - 1) / 2.54))
        for r in twos:
            if x > ox + w - 25.4:
                x, y = ox + 15.24, y + step
            d = parts.info(t.parts[r].key)
            pins = self.part(r, x + 3.81, y, rot=90 if d["symbol"] in vertical else 0)
            lo = min(pins, key=lambda k: pins[k][0]); hi = max(pins, key=lambda k: pins[k][0])
            self._pin_label(t, r, lo, pins[lo], 0)
            self._pin_label(t, r, hi, pins[hi], 180)
            x += pitch
        # the loops: beside the two-terminal rows' end
        for r in loops:
            if x > ox + w - 25.4:
                x, y = ox + 15.24, y + 12.7
            p = t.parts[r]
            self.loop(r, x + 2.54, y, p.value, dx=0.8, justify="left")
            self.wire([(x + 2.54, y), (x + 2.54, y + 2.54)])
            self.label(p.pins["1"].lstrip("/"), x + 2.54, y + 2.54)
            x += 30.48
        self.result_note(t, above=y + 10.16)

    def _pin_label(self, t, ref, num, pos, rot_into_body):
        """A 2.54 stub out of a pin and the net's name (or a ground / rail symbol) at its end."""
        net = t.parts[ref].pins.get(str(num))
        if net is None:
            self.s.no_connect(pos[0], pos[1])
            return
        dx, dy = {0: (-2.54, 0), 180: (2.54, 0), 90: (0, 2.54), 270: (0, -2.54)}[int(rot_into_body) % 360]
        end = (pos[0] + dx, pos[1] + dy)
        self.wire([pos, end])
        if net == "GND":
            self.gnd(end[0], end[1])
        elif net in RAILS:
            self.rail(net, end[0], end[1], up=not net.startswith("-"))
            self._flag(net, end)
        else:
            self._flag(net, end)
            just = "right" if dx < 0 else "left"
            if dy:
                self.label(net.lstrip("/"), end[0], end[1], justify="left")
            else:
                self.label(net.lstrip("/"), end[0], end[1], justify=just)

    def _flag(self, net, end):
        """A PWR_FLAG on a net the tile says drives power pins (once per net)."""
        local = net.split("_", 1)[-1] if net.startswith("/") else net
        if local not in self.t.pwr_flags or net in self.flagged:
            return
        self.flagged.add(net)
        self.pwr_n[0] += 1
        self.s.place("power:PWR_FLAG", "#FLG%s%03d" % (self.t.idx, self.pwr_n[0]), "PWR_FLAG", end[0], end[1], in_bom=False, on_board=False,
                     hide_ref=True, val_off=(0, -3.81))

    def rail(self, net, x, y, up=True):
        self.pwr_n[0] += 1
        self.s.place("power:" + net, "#PWR%s%03d" % (self.t.idx, self.pwr_n[0]), net, x, y, rot=0 if up else 180,
                     in_bom=False, on_board=False, hide_ref=True, hide_value=False)

    def dip_caps(self, t):
        """A DIP switch whose poles put capacitors across two nodes of the chain (P4, P8): drawn under the line, each
        switch pad wired to the net its pin declares (a label for the chain's nets, the capacitor itself for the
        switched ones), the capacitors beside the pads whose net they share."""
        sw = [r for r, p in t.parts.items() if p.key.startswith("DIP")][0]
        swp = t.parts[sw]
        x0, y0 = self.ox + 50.8, self.oy + 55.88
        pins = self.part(sw, x0, y0, label_off=((0, -7.62), (0, 7.62)))
        caps = {r: p for r, p in t.parts.items() if r[0] == "C" and any(("_S" in n) and n in swp.pins.values() for n in p.pins.values())}
        chain_nets = {n for r, p in t.parts.items() if r[0] in "RCLY" and r not in caps for n in p.pins.values()} | {j["net"] for j in t.jacks}
        for pad, net in sorted(swp.pins.items(), key=lambda kv: int(kv[0])):
            px, py = pins[pad]
            left = px < x0
            cap = [r for r, p in caps.items() if net in p.pins.values()]
            if cap:
                r = cap[0]
                cp = self.part(r, px + (-7.62 if left else 7.62), py, rot=90)
                mine = [k for k, n in t.parts[r].pins.items() if n == net][0]
                near = min(cp, key=lambda k: abs(cp[k][0] - px))
                if near != mine:
                    self.s.items.pop(); self.s.symbols.pop()
                    cp = self.part(r, px + (-7.62 if left else 7.62), py, rot=90, mirror="y")
                other = [k for k in cp if k != mine][0]
                onet = t.parts[r].pins[other]
                self.wire([(px, py), cp[mine]])
                end = (cp[other][0] + (-2.54 if left else 2.54), py)
                self.wire([cp[other], end])
                self.label(onet.lstrip("/"), end[0], end[1], justify="right" if left else "left")
            else:
                end = (px + (-5.08 if left else 5.08), py)
                self.wire([(px, py), end])
                self.label(net.lstrip("/"), end[0], end[1], justify="right" if left else "left")

    def delay_line(self, t):
        """P11: the twenty sections as two rows of ten, the taps and the jacks."""
        y = self.oy + 25.4
        x = self.ox + 10.16
        jin = [j for j in t.jacks if j["label"] == "IN"][0]
        p1 = self.jack(jin["ref"], x, y, "in", "IN", jin["limit"])
        xcur = x + 7.62
        self.wire([p1, (xcur, y)])
        for k in range(1, 21):
            l = "L%d%02d" % (t.idx, k); c = "C%d%02d" % (t.idx, k)
            if k == 11:
                # drop to the second row and run back to its start, under row A's capacitors
                self.wire([(xcur, y), (xcur, y + 16.51), (self.ox + 15.24, y + 16.51), (self.ox + 15.24, y + 25.4), (self.ox + 17.78, y + 25.4)])
                y += 25.4
                xcur = self.ox + 17.78
            lp = self.part(l, xcur + 3.81, y, rot=90)
            self.wire([(xcur, y), lp["1"]])
            nx = lp["2"][0] + 1.27
            self.wire([lp["2"], (nx, y)])
            cp = self.part(c, nx, y + 6.35, rot=0, side="right")
            self.wire([(nx, y), cp["1"]])
            self.junction(nx, y)
            self.gnd(nx, cp["2"][1] + 1.27)
            self.wire([cp["2"], (nx, cp["2"][1] + 1.27)])
            xcur = nx + 1.27
            if k < 20:
                self.wire([(nx, y), (xcur, y)])
            if k in (5, 10, 15, 20):
                name = {5: "T1", 10: "T2", 15: "T3", 20: "OUT"}[k]
                self.label("%s_%s" % (t.id, name), nx, y)
            if k == 10:
                self.wire([(xcur, y), (xcur + 2.54, y)])
                xcur += 2.54
        # the taps: resistors up to their jacks, drawn under the rows
        yj = self.oy + 83.82
        xj = self.ox + 17.78
        for i, (net, lab) in enumerate((("T1", "100ns"), ("T2", "200ns"), ("T3", "300ns"))):
            jj = [j for j in t.jacks if j["label"] == lab][0]
            r = [r for r, p in t.parts.items() if p.key.startswith("R0805") and "/%s_%s" % (t.id, net) in p.pins.values()][0]
            xr = xj + i * 40.64
            jpin = [k for k, n in t.parts[r].pins.items() if n.endswith("J")][0]
            rp = self.part(r, xr, yj, rot=90, mirror=("y" if jpin == "1" else None))     # the jack's pin on the right
            tpin = [k for k in rp if k != jpin][0]
            self.label("%s_%s" % (t.id, net), rp[tpin][0] - 5.08, yj)
            self.wire([(rp[tpin][0] - 5.08, yj), rp[tpin]])
            pj = self.jack(jj["ref"], rp[jpin][0] + 10.16, yj, "out", lab, "")
            self.wire([rp[jpin], pj])
        jo = [j for j in t.jacks if j["label"] == "OUT"][0]
        pj = self.jack(jo["ref"], xj + 3 * 40.64 + 10.16, yj, "out", "OUT", "open, short or 50 ohm")
        self.wire([(pj[0] - 7.62, yj), pj])
        self.label("%s_OUT" % t.id, pj[0] - 7.62, yj)
        tp = [r for r, p in t.parts.items() if p.key == "TP"][0]
        self.loop(tp, p1[0] + 1.27, self.oy + 25.4, "IN")
        self.result_note(t)

    def fan_down(self, sp, pads, refs, top_pin, y_bus):
        """Parts hanging one per column from switch pads `pads` (their left ends), `top_pin` at the top, the other
        pin to a ground bus at y_bus; labels alternate sides so the 7.62 mm columns do not collide."""
        xg = sp[pads[0]][0] - 12.7 * (len(refs) + 1)
        for i, (pad, r) in enumerate(zip(pads, refs)):
            px, py = sp[pad]
            xc = px - 12.7 * (i + 1)
            horiz = r[0] in ("L", "D") and not r.startswith("L0") and parts.info(self.t.parts[r].key)["symbol"] in ("Device:LED", "Diode:1N4148W")
            if horiz:
                rot_ = 90 if top_pin == "2" else 270
            else:
                rot_ = 0 if top_pin == "1" else 180
            pins_ = self.part(r, xc, y_bus - 10.16, rot=rot_, side="right")
            self.wire([(px, py), (xc, py), pins_[top_pin]])
            bottom = [k for k in pins_ if k != top_pin][0]
            self.wire([pins_[bottom], (xc, y_bus)])
            if i > 0:
                self.junction(xc, y_bus)
        self.wire([(sp[pads[0]][0] - 12.7, y_bus), (sp[pads[0]][0] - 12.7 * len(refs), y_bus)])
        self.gnd(sp[pads[0]][0] - 12.7 * len(refs), y_bus)
        return xg

    def fan_right(self, sp, pads, refs, top_pin, y_bus):
        """As fan_down, but the columns hang to the RIGHT of the switch's right column."""
        for i, (pad, r) in enumerate(zip(pads, refs)):
            px, py = sp[pad]
            xc = px + 12.7 * (i + 1)
            rot_ = 0 if top_pin == "1" else 180
            pins_ = self.part(r, xc, y_bus - 10.16, rot=rot_, side="right")
            self.wire([(px, py), (xc, py), pins_[top_pin]])
            bottom = [k for k in pins_ if k != top_pin][0]
            self.wire([pins_[bottom], (xc, y_bus)])
            if i > 0:
                self.junction(xc, y_bus)
        self.wire([(sp[pads[0]][0] + 12.7, y_bus), (sp[pads[0]][0] + 12.7 * len(refs), y_bus)])
        self.gnd(sp[pads[0]][0] + 12.7 * len(refs), y_bus)

    def leds(self, t):
        """P12: the jack, the 100 ohm, the 4-way switch and the four LEDs to ground."""
        y = self.oy + 30.48
        x = self.ox + 12.7
        jin = t.jacks[0]
        p1 = self.jack(jin["ref"], x, y, "in", "IN", jin["limit"])
        r = [r for r, p in t.parts.items() if p.key.startswith("R0805")][0]
        rp = self.part(r, x + 11.43, y, rot=90)
        self.wire([p1, rp["1"]])
        sw = [r for r, p in t.parts.items() if p.key.startswith("DIP")][0]
        sp = self.part(sw, x + 45.72, y + 20.32, label_off=((0, -8.89), (0, 8.89)))
        # right column (5..8) is the bus, fed from the resistor along the line and down the switch's right side
        xb = sp["5"][0] + 2.54
        self.wire([rp["2"], (xb, y), (xb, sp["5"][1])])
        self.label("%s_BUS" % t.id, rp["2"][0] + 5.08, y)
        for pin in ("5", "6", "7", "8"):
            self.wire([sp[pin], (xb, sp[pin][1])])
            if pin != "5":
                self.junction(xb, sp[pin][1])
        leds = [r for r, p in t.parts.items() if p.key.startswith("LED")]
        self.fan_down(sp, ["1", "2", "3", "4"], leds, "2", sp["4"][1] + 17.78)
        tp = [r for r, p in t.parts.items() if p.key == "TP"][0]
        self.loop(tp, rp["2"][0] + 2.54, y, "LED", dx=0.8, justify="left")
        self.result_note(t)

    def loopstick(self, t):
        """P13: the terminal, the capacitor bank on the 4-way switch, the tap to the jack."""
        y = self.oy + 30.48
        x = self.ox + 20.32
        term = [r for r, p in t.parts.items() if p.key == "TERM3"][0]
        tp_ = self.part(term, x, y, mirror="y", label_off=((0, -7.62), (0, 7.62)))
        # pins face right after the mirror: 1 HOT (top), 2 TAP, 3 GND
        hot, tap, gnd = tp_["1"], tp_["2"], tp_["3"]
        self.gnd(gnd[0] + 2.54, gnd[1] + 2.54)
        self.wire([gnd, (gnd[0] + 2.54, gnd[1]), (gnd[0] + 2.54, gnd[1] + 2.54)])
        self.text("1 coil end", hot[0] - 12.7, hot[1], 1.1, "right"); self.text("2 tap", tap[0] - 12.7, tap[1], 1.1, "right"); self.text("3 coil end", gnd[0] - 12.7, gnd[1], 1.1, "right")
        sw = [r for r, p in t.parts.items() if p.key.startswith("DIP")][0]
        sp = self.part(sw, x + 50.8, y + 8.89, label_off=((0, -8.89), (0, 8.89)))
        xb = sp["1"][0] - 2.54
        self.wire([hot, (hot[0] + 5.08, hot[1]), (hot[0] + 5.08, y - 10.16), (xb, y - 10.16), (xb, sp["4"][1])])
        self.label("%s_HOT" % t.id, hot[0] + 5.08, y - 10.16)
        for pin in ("1", "2", "3", "4"):
            self.wire([sp[pin], (xb, sp[pin][1])])
            if pin != "1":
                self.junction(xb, sp[pin][1])
        caps = [r for r, p in t.parts.items() if p.key.startswith("C0805")]
        self.fan_right(sp, ["8", "7", "6", "5"], caps, "1", sp["5"][1] + 17.78)
        tv = [r for r, p in t.parts.items() if p.key == "TERM2"]
        if tv:                                         # VAR C: an external tuning capacitor across the coil, beside the bank
            vp = self.part(tv[0], x, y + 17.78, mirror="y", label_off=((0, -5.08), (0, 5.08)))
            self.wire([vp["1"], (vp["1"][0] + 5.08, vp["1"][1])])
            self.label("%s_HOT" % t.id, vp["1"][0] + 5.08, vp["1"][1])
            self.wire([vp["2"], (vp["2"][0] + 2.54, vp["2"][1]), (vp["2"][0] + 2.54, vp["2"][1] + 2.54)])
            self.gnd(vp["2"][0] + 2.54, vp["2"][1] + 2.54)
            self.text("VAR C: external tuning C", vp["1"][0] - 12.7, vp["1"][1], 1.1, "right")
        jo = t.jacks[0]
        pj = self.jack(jo["ref"], x + 121.92, y + 35.56, "out", "OUT", jo["limit"])
        self.wire([tap, (tap[0] + 7.62, tap[1]), (tap[0] + 7.62, y + 35.56), pj])
        self.label("%s_TAP" % t.id, tap[0] + 7.62, y + 35.56)
        for r, p in t.parts.items():
            if p.key == "TP":
                if p.pins["1"] == t.net("TAP"):
                    self.loop(r, pj[0] - 7.62, y + 35.56, "TAP")
                else:
                    self.loop(r, hot[0] + 5.08 + 5.08, y - 10.16, "HOT")
        self.result_note(t)


def build(stem):
    B = parts.BOARDS[stem]
    mod = importlib.import_module("boards." + stem)
    ts = mod.tiles()
    s = Sheet(kienv.share_dir(), paper="A1", title=B["title"], date=parts.DATE, rev=parts.REV,
              company="Board: %s  |  open hardware, CERN-OHL-P-2.0  |  %s" % (parts.AUTHORS, parts.URL),
              comments=[B["subtitle"], "Every tile is one circuit with its own SMA jacks; the board's silkscreen draws each tile's wires as they are laid.",
                        "Drawn by scripts/gen_sch.py from boards/%s.py; the expected responses from sim/passive.py" % stem], project=stem)
    s.add_local_lib(os.path.join(HERE, "..", "hardware", "lib", "amod.kicad_sym"), "amod")
    for t in ts:
        c0 = min(c for c, r in t.cells); r0 = t.cells[0][1]
        ox = OX0 + c0 * BLOCK_W
        oy = OY0 + r0 * BLOCK_H
        w = len(t.cells) * BLOCK_W - 5.08
        h = BLOCK_H - 5.08
        ctx = SchCtx(s, t, ox, oy, w, h)
        ctx.header()
        t.sch_draw(ctx, t)
        for i, (ref, p) in enumerate([(r, p) for r, p in t.parts.items() if p.key == "SLOT"]):
            d = parts.info("SLOT")
            s.place(d["symbol"], ref, "slot", ox + w - 15.24 + 0 - i * 7.62, oy + 12.7, footprint=d["footprint"], in_bom=False,
                    ref_off=(0, -3.5), val_off=(0, 3.5), hide_value=True)
    # board-level: the mounting holes and the ground loops, in a strip under the blocks
    y = OY0 + 4 * BLOCK_H + 2.54
    holes = getattr(mod, "HOLES", [(0, 0)] * 4)
    for i, (hx, hy) in enumerate(holes):
        s.place("Mechanical:MountingHole", "MH%d" % (i + 1), "MountingHole", OX0 + 10.16 + i * 12.7, y + 2.54,
                footprint=parts.PARTS["MH"]["footprint"], in_bom=False, ref_off=(0, -3.5), val_off=(0, 3.5), hide_value=True)
    s.text("M3 mounting holes, one per corner" if holes else "no mounting holes: four stick-on rubber feet, marked on the back",
           OX0 + 10.16 + 4 * 12.7, y + 2.54, size=1.2)
    for i, (gx, gy) in enumerate(getattr(mod, "GND_LOOPS", [])):
        ref = "TP%d" % (9900 + i + 1)
        x = OX0 + 101.6 + i * 15.24
        d = parts.info("TP")
        s.place(d["symbol"], ref, "GND", x, y, rot=0, footprint=d["footprint"], fields={"LCSC": d["lcsc"], "MPN": d["mpn"]},
                hide_ref=True, val_off=(1.8, -3.0), val_justify="left")
        s.wire((x, y), (x, y + 2.54))
        s.place("power:GND", "#PWR9%02d" % (i + 1), "GND", x, y + 2.54, in_bom=False, on_board=False, hide_ref=True, hide_value=True)
    s.text("ground loops for the scope's clips, one per channel, in the board's margins", OX0 + 101.6 + 4 * 15.24, y, size=1.2)
    for i, (sx, sy) in enumerate(getattr(mod, "SLOTS", [])):
        d = parts.info("SLOT")
        s.place(d["symbol"], "H%d" % (9901 + i), "slot", OX0 + 10.16 + (4 + i) * 12.7, y + 12.7, footprint=d["footprint"], in_bom=False,
                ref_off=(0, -3.5), val_off=(0, 3.5), hide_value=True)
    if getattr(mod, "SLOTS", []):
        s.text("slots for cable ties", OX0 + 10.16 + 8 * 12.7, y + 12.7, size=1.2)
    s.place("power:PWR_FLAG", "#FLG01", "PWR_FLAG", OX0 + 101.6 + 4 * 15.24 + 76.2, y, in_bom=False, on_board=False, hide_ref=True, val_off=(0, -3.81))
    s.wire((OX0 + 101.6 + 4 * 15.24 + 76.2, y), (OX0 + 101.6 + 4 * 15.24 + 76.2, y + 2.54))
    s.place("power:GND", "#PWR999", "GND", OX0 + 101.6 + 4 * 15.24 + 76.2, y + 2.54, in_bom=False, on_board=False, hide_ref=True, hide_value=True)
    return s, ts


def main():
    stem = sys.argv[1] if len(sys.argv) > 1 else "amod_p"
    s, ts = build(stem)
    added = s.add_missing_junctions()
    bad = s.check_grid()
    if bad:
        print("  !! %d off-grid endpoint(s):" % len(bad))
        for what, pt in bad[:12]:
            print("       %s at %s" % (what, pt))
        raise SystemExit("off-grid endpoints would confuse KiCad's connectivity")
    out = os.path.join(HW, stem + ".kicad_sch")
    os.makedirs(HW, exist_ok=True)
    s.write(out)
    import tiles as TILES
    mod = importlib.import_module("boards." + stem)
    os.makedirs(os.path.join(HW, "..", "out"), exist_ok=True)
    TILES.dump(ts, mod, os.path.join(HW, "..", "out", stem + "_tiles.json"))
    print("  wrote %s (%d symbols, %d junctions added)" % (os.path.relpath(out), len(s.symbols), added))


if __name__ == "__main__":
    main()
