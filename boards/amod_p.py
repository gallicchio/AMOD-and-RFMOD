"""AMOD-P: the passive board.  Sixteen cells, thirteen tiles (PLAN.md section 4), 27 SMA jacks,
two layers.  Every tile here is a ladder (scripts/tiles.ladder) or a hand-laid circuit using the
same Tile model; the responses the silkscreen and the handbook quote come from sim/passive.py.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, os.path.join(HERE, "..", "sim"))
import tiles as T
from tiles import Tile, ladder, LINE_Y, PAD, unit
import passive as P
import geometry as G

STEM = "amod_p"
LAYERS = 2


def rot(dx, dy, r):
    """A footprint-local offset turned by KiCad's rotation r (degrees CCW on a y-down board)."""
    return {0: (dx, dy), 90: (dy, -dx), 180: (-dx, -dy), 270: (-dy, dx)}[r % 360]


def dip_pads(n, x, y, r):
    """Pad centres of our DSHP0n footprint placed at (x, y, r): {pad: (x, y)}.  At rot 0 the pins run along x at
    1.27 mm, pads 1..n along the +y row (pin 1 left), 2n..n+1 along the -y row; way k = pads k and 2n+1-k, one above
    the other.  Rot 90 turns the rows into columns: pins 1..n up the +x column (pin 1 at the bottom); rot 270: pins
    1..n down the -x column (pin 1 at the top), 2n..n+1 down the +x column."""
    out = {}
    for k in range(1, n + 1):
        dx = (k - (n + 1) / 2.0) * 1.27
        for num, dy in ((k, 3.81), (2 * n + 1 - k, -3.81)):
            ox, oy = rot(dx, dy, r)
            out[str(num)] = (x + ox, y + oy)
    return out


def pad2(pkg, x, y, r, pad):
    """Centre of pad 1 or 2 of a two-terminal part at (x, y, r): rot 0 pad 1 at -x, rot 270 pad 1 at -y (top)."""
    d = PAD[pkg] * (-1 if pad == "1" else 1)
    ox, oy = rot(d, 0, r)
    return (x + ox, y + oy)


def tile_p1():
    t = Tile("P1", "pi pad", [(0, 0)], subtitle="-20 dB", sections=["6.12", "5.06"])
    ladder(t, [("shunt", [("R0805", 61.9)]), ("series", "R0805", 249), ("shunt", [("R0805", 61.9)])], out_slot="BR")
    t.result = "-20 dB flat, 50 ohm both ways"
    t.notes = ["A pi attenuator: 61.9 / 249 / 61.9 ohm is -20.0 dB and 50.0 ohm in a 50 ohm system (6.12's $10 pad, on the board).",
               "Into a high-impedance load it is only -14 dB: the pad assumes 50 ohm on both sides."]
    return t


def tile_p2():
    t = Tile("P2", "RC low-pass", [(1, 0)], subtitle="159 kHz", sections=["4.02", "4.08", "7.06"])
    ladder(t, [("series", "R0805", 1000), ("shunt", [("C0805", 1e-9)])], hiz_out=True, fspan=(1e3, 1e8), out_slot="BR")
    t.result = "-3 dB at 159 kHz, then -20 dB/decade; OUT into the ADC's high impedance"
    t.notes = ["1 k and 1 nF: f = 1 / (2 pi R C) = 159 kHz.  Measure OUT with the ADC on its high-impedance setting: a 50 ohm",
               "load would make a 1 k / 50 divider of it.  The lag plant of 4.08 and 7.06; the step response is 1 - exp(-t / 1 us)."]
    return t


def tile_p3():
    t = Tile("P3", "RC high-pass", [(2, 0)], subtitle="159 kHz", sections=["4.02"])
    ladder(t, [("series", "C0805", 1e-9), ("shunt", [("R0805", 1000)])], hiz_out=True, fspan=(1e3, 1e8), out_slot="BR")
    t.result = "-3 dB at 159 kHz, +20 dB/decade below; OUT into high impedance"
    t.notes = ["The mirror image of P2: the same 1 k and 1 nF the other way round.  A step in gives a spike that decays in 1 us."]
    return t


def tile_p4():
    """Series RLC between the jacks: 100 uH and 220 pF, with 47 pF and 100 pF switched in parallel with the capacitor by a
    2-way DIP.  The line runs 0.65 mm high so the 1210 clears both jacks; the switch lies across the top-right quarter
    the OUT jack left (its ways as columns), its left column on the L-C node through the gap between the two parts, its
    right column to the two capacitors standing under it, whose other ends are on the OUT line.  The number, the
    sections and the IN loop take the bottom-left; no OUT loop (the switch has its corner: OUT is the jack)."""
    t = Tile("P4", "series RLC", [(3, 0)], subtitle="100uH 220pF", sections=["4.02", "7.06"])
    LY = 9.95
    ladder(t, [("series", "L1210", 100e-6), ("series", "C0805", 220e-12)], fspan=(1e5, 1e7), xs=[9.0, 13.2], loops=False,
           labels={0: None, 1: None}, out_slot="BR", line_y=LY, legend=False)
    # the switch at rot 90: pads 4 / 3 down its left column (x 10.49), 1 / 2 down its right column (x 18.11)
    sw = t.add("SW", "DIP2", "DIP2", 14.3, 4.0, 90, {"3": "N1", "4": "N1", "1": "S1", "2": "S2"}, hide_value=True)
    pads = dip_pads(2, 14.3, 4.0, 90)
    xn = 11.39                                                  # between the coil's pad 2 (11.025) and the capacitor's pad 1 (11.75)
    t.wire("N1", [(xn, LY), (xn, pads["4"][1]), pads["4"], pads["3"]], width=0.25)
    cu = t.add("C", "C0603 100pF", "100p", 16.3, 8.2, 270, {"1": "S2", "2": "OUT"}, label=None)      # pad 1 up
    cl = t.add("C", "C0603 47pF", "47p", 17.95, 8.2, 270, {"1": "S1", "2": "OUT"}, label=None)
    t.wire("OUT", [(15.25, LY), (17.95, LY), (cl, "2")])
    t.wire("OUT", [(16.3, LY), (cu, "2")])
    t.wire("S2", [pads["2"], (16.3, pads["2"][1]), (cu, "1")], width=0.25)
    t.wire("S1", [pads["1"], (pads["1"][0], 6.6), (17.95, 6.6), (cl, "1")], width=0.25)
    tp = t.loop("IN", 6.6, 14.2, 0, "IN", label_at="hide")
    t.wire("IN", [(4.75, LY), (4.75, 14.2), (tp, "1")])
    t.text(2.3, 12.0, t.id, 1.5, 0.3, "center")
    for k, sct in enumerate(t.sections):
        t.text(2.3, 13.9 + 1.35 * k, sct, 0.8, 0.15, "center")
    t.text(1.2, 17.4, t.name.upper(), 0.8, 0.15, "left")
    t.text(1.2, 18.7, t.subtitle, 0.8, 0.15, "left")
    # the responses for the four switch states
    f = P.logspace(1e5, 1e7, 1200)
    res = {}
    for name, cadd in (("off", 0), ("1", 47e-12), ("2", 100e-12), ("1+2", 147e-12)):
        g = P.db(P.response([("series", P.series_arm(P.L(100e-6, 10.0), P.C(220e-12 + cadd)))], f))
        res[name] = P.peak(f, g)
    t.sim["peaks"] = {k: v[0] for k, v in res.items()}
    t.plot = dict(kind="bode", x=f, y=P.db(P.response([("series", P.series_arm(P.L(100e-6, 10.0), P.C(220e-12)))], f)))
    t.result = "a peak at %.2f MHz (switches off), %.2f with 1, %.2f with 2, %.2f with both; Q about 6" % (
        res["off"][0] / 1e6, res["1"][0] / 1e6, res["2"][0] / 1e6, res["1+2"][0] / 1e6)
    t.notes = ["Series L C between 50 ohm ports: a band-pass at f = 1 / (2 pi sqrt(L C)) whose Q = sqrt(L/C) / (100 + R_coil) is about 6",
               "(the 10 ohm coil would give 60 by itself).  The DIP switch adds 47 pF (way 1) and 100 pF (way 2) across the 220 pF to move",
               "the peak; a resonant plant for 7.06, a lockbox's cavity before the real one.  No OUT loop (the switch took its corner)."]
    t.sch_draw = draw_p4
    return t


def draw_p4(ctx, t):
    T.draw_ladder(ctx, t)
    ctx.note(t, ["the DIP switch and its two capacitors are drawn on the right: way 1 adds 47 pF, way 2 adds 100 pF across C",
                 "(each way from the L-C node to the OUT node through its capacitor)"])
    ctx.dip_caps(t)


def tile_p5():
    t = Tile("P5", "LC low-pass", [(0, 1)], subtitle="9 MHz", sections=["1.06", "6.10", "4.02"])
    ladder(t, [("shunt", [("C0805", 220e-12)]), ("series", "L0805", 1.5e-6), ("shunt", [("C0805", 680e-12)]),
               ("series", "L0805", 1.5e-6), ("shunt", [("C0805", 220e-12)])], fspan=(1e5, 1e8), out_slot="BR",
           labels={2: (-1.13, 0, "right", 0.8)})                  # the middle capacitor's value on its left, off the OUT jack
    t.result = "-3 dB at %.1f MHz, -30 dB at 18 MHz: the anti-alias filter in front of a 25 MS/s ADC" % (t.sim["f3"] / 1e6)
    t.notes = ["5th-order Butterworth, 50 ohm: 220 pF, 1.5 uH, 680 pF, 1.5 uH, 220 pF (the exact values are 219 pF, 1.43 uH, 707 pF).",
               "Before the ADC it removes 6.10's ghost; after the DAC it smooths the steps."]
    return t


def tile_p6():
    t = Tile("P6", "LC low-pass", [(1, 1)], subtitle="100 kHz", sections=["7.05", "4.02"])
    ladder(t, [("shunt", [("C0805", 10e-9), ("C0805", 10e-9)]), ("series", "L1210", 150e-6), ("shunt", [("C0805", 10e-9), ("C0805", 10e-9)])],
           fspan=(1e3, 1e7), labels={1: None, 2: (0.6, -2.3, "center", 0.8), 3: None}, out_slot="BR", line_y=9.95,   # the inner pair unlabelled
           loop_at={"IN": (8.9, 14.6, 90, [(7.4, 9.95), (7.4, 13.0), (8.9, 13.0)])})       # the line up 0.65: the 1210 clears both jacks
    # a third 10 nF on each side would make 30 nF (the design value for 3rd-order Butterworth at 106 kHz with 150 uH);
    # two cells of 10 nF (20 nF) give 125 kHz: use the simulated number
    t.result = "-3 dB at %.0f kHz: the reconstruction filter after a one-bit DAC" % (t.sim["f3"] / 1e3)
    t.notes = ["3rd-order pi, 50 ohm: 2 x 10 nF, 150 uH, 2 x 10 nF, all C0G (JLCPCB stocks no 22 nF C0G in 0805 or 1206).",
               "Turns 7.05's one-bit stream into a tone; the slow plant of 7.06 with P2."]
    return t


def tile_p7():
    """Four 0603 series parts cannot fit between the stubs (10.5 mm): the row is laid by hand from x 2.3 to 17.7 and the
    stubs enter round its ends; the outer parts' values go under them, out of the entries' way."""
    t = Tile("P7", "band-pass", [(2, 1)], subtitle="4.7-7.5 MHz", sections=["6.10", "5.07", "6.12"])
    ladder(t, [("series", "L0603", 2.7e-6), ("series", "C0603", 270e-12), ("shunt", [("L0603", 330e-9), ("C0603", 2.2e-9)]),
               ("series", "L0603", 2.7e-6), ("series", "C0603", 270e-12)], fspan=(1e6, 3e7),
           xs=[2.3, 6.6, 13.4, 17.7], labels={0: (-0.35, 2.2, "left", 0.8), 1: None, 2: None, 3: None,
                                              4: (0, -1.6, "center", 0.8), 5: (-0.8, -3.0, "right", 0.8)},
           out_slot="BR", line_y=10.0, entry_y=8.95, r_turn=11.05,
           loop_at={"IN": (5.9, 14.3, 0), "OUT": (18.3, 6.0, 90, [(18.3, 10.0)])})
    fpk, gpk = t.sim["peak"]
    t.result = "Chapter 6's band: a peak at %.1f MHz, 3 dB from %.1f to %.1f MHz" % (fpk / 1e6, *band(t.sim))
    t.notes = ["3rd-order Butterworth band-pass, 6.05 MHz centre, 3.1 MHz wide: series 2.7 uH + 270 pF, shunt 330 nH || 2.2 nF, series 2.7 uH + 270 pF",
               "(the exact values: 2.57 uH, 269 pF, 337 nH, 2.05 nF).  6.10's filtered chips in copper; the transmitter's harmonics and the",
               "receiver's front end of 5.07 and 6.12."]
    return t


def band(sim, down=3.0):
    import numpy as np
    f, g = np.array(sim["f"]), np.array(sim["db"])
    pk = g.max()
    sel = f[g > pk - down]
    return sel.min() / 1e6, sel.max() / 1e6


def tile_p8():
    """A 4 MHz crystal in series between the jacks: the sharpest resonance on the board.  An HC-49S is 11.5 mm long, more
    than either quarter of a cell the jacks leave, so it lies at 45 degrees across the cell, from the bottom-left to the
    top-right, and the two jacks sit 0.5 mm further out along the other diagonal (TLo, BRo) so its courtyard clears
    theirs.  Each jack's stub runs straight to the crystal's near pad; the loops stand on the stubs, the number in the
    top-right corner, the name in the bottom-left, the sections in the gutter above."""
    t = Tile("P8", "quartz crystal", [(3, 1)], subtitle="4 MHz", sections=["4.03", "4.09", "4.10"])
    jin = t.jack("TLo", "IN", "IN", "in", "±4 V")
    jout = t.jack("BRo", "OUT", "OUT", "out", "")
    y1 = t.add("Y", "XTAL4M", "4 MHz", 10.0, 10.0, 45, {"1": "IN", "2": "OUT"}, label=None)   # pad 1 at (6.78, 13.22), pad 2 at (13.22, 6.78)
    t.wire("IN", [(jin, "1"), (4.25, 13.22), (y1, "1")])
    t.wire("OUT", [(y1, "2"), (15.75, 6.78), (jout, "1")])
    a = t.loop("IN", 2.0, 10.2, 90, "IN", label_at="hide")
    t.wire("IN", [(4.25, 10.2), (a, "1")])
    b = t.loop("OUT", 18.0, 9.8, 90, "OUT", label_at="hide")
    t.wire("OUT", [(15.75, 9.8), (b, "1")])
    t.text(17.4, 2.0, t.id, 1.5, 0.3, "center")
    t.text(17.4, 3.75, t.subtitle, 0.8, 0.15, "center")
    t.text(9.6, -0.8, " ".join(t.sections[:2]), 0.8, 0.15, "center")
    t.text(1.2, 17.4, "QUARTZ", 0.8, 0.15, "left")
    t.text(1.2, 18.7, "CRYSTAL", 0.8, 0.15, "left")
    import numpy as np
    fx = np.linspace(3.994e6, 4.006e6, 6001)
    g = P.db(P.response([("series", P.crystal(4.0e6, 15e-15, 50000, 4e-12))], fx))
    fp, gp = P.peak(fx, g)
    fn = float(fx[int(np.argmin(g))])
    t.sim["crystal"] = dict(f_s=fp, db=gp, f_p=fn)
    t.plot = dict(kind="bode", x=fx, y=g)
    t.result = "a sharp pass at the series resonance near 4.000 MHz (%.1f dB) and a notch %.1f kHz above it, the parallel resonance" % (gp, (fn - fp) / 1e3)
    t.notes = ["The crystal in series between 50 ohm ports: it passes at its series resonance f_s (R_m about 50 ohm: -3.5 dB) and blocks at",
               "the parallel resonance f_p = f_s (1 + C_m / 2 C_0) a few kHz above.  A capacitor across OUT (a tee at the ADC) pulls f_p",
               "down toward f_s and leaves f_s alone: the pulling that 4.09 measures.  Model: C_m 15 fF, Q 50 000, C_0 4 pF (typical HC-49S)."]
    t.sch_draw = lambda ctx, tt: ctx.generic_series(tt)
    return t


def tile_p9():
    """A 455 kHz ceramic resonator in series between the jacks, at 45 degrees across the cell (bottom-left to top-right)
    between the IN jack (top-left) and the OUT jack (bottom-right); each stub runs to the resonator's near lead."""
    t = Tile("P9", "ceramic res.", [(0, 2)], subtitle="455 kHz", sections=["4.02", "4.03"])
    jin = t.jack("TL", "IN", "IN", "in", "±4 V")
    jout = t.jack("BR", "OUT", "OUT", "out", "")
    y1 = t.add("Y", "RES455", "455 kHz", 10.0, 10.0, 45, {"1": "IN", "2": "OUT"}, label=None)   # pad 1 at (8.23, 11.77), pad 2 at (11.77, 8.23)
    t.wire("IN", [(jin, "1"), (4.75, 11.77), (y1, "1")])
    t.wire("OUT", [(y1, "2"), (15.25, 8.23), (jout, "1")])
    a = t.loop("IN", 4.0, 14.6, 0, "IN", label_at="hide")
    t.wire("IN", [(4.75, 11.77), (4.75, 14.6), (a, "1")])
    b = t.loop("OUT", 15.25, 4.6, 90, "OUT", label_at="hide")
    t.wire("OUT", [(15.25, 8.23), (b, "1")])
    t.text(11.5, 2.2, t.id, 1.5, 0.3, "center")
    for k, sct in enumerate(t.sections):
        t.text(11.5, 4.0 + 1.35 * k, sct, 0.8, 0.15, "center")
    t.text(1.2, 17.4, t.name.upper(), 0.8, 0.15, "left")
    t.text(1.2, 18.7, t.subtitle, 0.8, 0.15, "left")
    import numpy as np
    fx = np.linspace(4.0e5, 5.2e5, 3001)
    g = P.db(P.response([("series", P.crystal(455e3, 7e-12, 400, 250e-12))], fx))
    fp, gp = P.peak(fx, g)
    t.sim["res"] = (fp, gp, float(fx[int(np.argmin(g))]))
    t.plot = dict(kind="bode", x=fx, y=g)
    t.result = "a pass near 455 kHz and a notch a few kHz above: a resonator with a Q of a few hundred, between P4's LC and P8's quartz"
    t.notes = ["A two-terminal 455 kHz ceramic resonator in series (JLCPCB stocks no three-terminal 455 kHz filter).  It is the superhet's IF",
               "element, and here a resonance whose Q (hundreds) sits between the LC's and the crystal's.  Model: C_m 7 pF, Q 400, C_0 250 pF."]
    t.sch_draw = lambda ctx, tt: ctx.generic_series(tt)
    return t


def tile_p10():
    """A 1 k series resistor and two 1N4148W antiparallel to ground: 4.04's clipper.  The diodes stand up from the OUT line
    into the top-right quarter, either side of the OUT loop's lead, each to its own ground via above it."""
    t = Tile("P10", "clipper", [(3, 3)], subtitle="1N4148 ±0.6 V", sections=["4.04"])
    ladder(t, [("series", "R0805", 1000)], hiz_out=True, xs=[8.0], out_slot="BR", legend=False)
    t.text(10.7, 2.1, t.id, 1.2, 0.24, "center")
    t.text(9.7, T.SECT_Y0, t.sections[0], 0.8, 0.15, "center")             # left of the first diode's ground symbol
    t.text(1.2, 17.4, t.name.upper(), 0.8, 0.15, "left")
    t.text(1.2, 18.7, t.subtitle, 0.8, 0.15, "left")
    LY = LINE_Y
    d1 = t.add("D", "D1N4148", "1N4148W", 12.0, 8.4, 270, {"1": "GND", "2": "OUT"}, label=None)      # rot 270: pad 1 (K) up, to ground
    d2 = t.add("D", "D1N4148", "1N4148W", 17.2, 8.4, 90, {"1": "OUT", "2": "GND"}, label=None)       # rot 90: pad 1 (K) down, on OUT
    t.wire("OUT", [(12.0, LY), (d1, "2")])
    t.wire("OUT", [(15.25, LY), (17.2, LY), (d2, "1")])
    t.gnd_stub(d1, "1", (12.0, 5.0), sym=(0, -1))
    t.gnd_stub(d2, "2", (17.2, 5.4), sym=(1, 0))
    t.result = "a sine of more than 1 V comes out flat-topped at about ±0.6 V; the ADC on high impedance"
    t.notes = ["1 k in series, then a 1N4148W each way to ground: whatever goes in, OUT stays within a diode drop.  4.04's harmonics: the",
               "clipped sine's spectrum against the amplitude; the 1 k limits the diode current to a few milliamps from a ±4 V source."]
    t.sch_draw = lambda ctx, tt: ctx.generic_series(tt)
    return t


def tile_p11():
    """20 LC sections of 1 uH and 390 pF (50 ohm, 20 ns each): a 400 ns tapped delay line on three cells.  Each section is
    an 0603 inductor on the line and an 0402 capacitor hanging from the node after it, 4.0 mm a section.  The jacks sit
    on the checkerboard: IN at the first cell's top-left, OUT at its bottom-right, the 100 and 200 ns taps at the second
    and third cells' top-left, the 300 ns tap at the third cell's bottom-right.  Row A runs right along the line from IN
    under the top jacks (twelve sections), drops left of the 300 ns jack, and row B runs back along y = 15.25 (eight)
    into OUT; row B's capacitors stand up, between row A's.  Each tap leaves its node through 470 ohm: nodes 5 and 10
    up past row A to a resistor beside their jack, node 15 down under row B and along the bottom edge into its jack
    from below."""
    t = Tile("P11", "delay line", [(1, 2), (2, 2), (3, 2)], subtitle="400 ns, a tap every 100", sections=["4.05", "6.05", "6.10", "7.06"])
    jin = t.jack("TL", "IN", "IN", "in", "±4 V")
    j1 = t.jack("TL1", "100ns", "T1J", "out", "")
    j2 = t.jack("TL2", "200ns", "T2J", "out", "")
    j3 = t.jack("BR2", "300ns", "T3J", "out", "")
    jout = t.jack("BR0", "OUT", "OUT", "out", "")
    pitch, cap_dx, yA, yB = 4.0, 2.0, LINE_Y, 15.25
    xA0 = 6.5                                 # L1's centre
    nA = 12                                   # sections in row A
    xB0 = xA0 + (nA - 1) * pitch + cap_dx     # L13 under C12, so the two rows' parts line up
    def net(k):
        return {0: "IN", 20: "OUT", 5: "T1", 10: "T2", 15: "T3"}.get(k, "N%d" % k)
    nodes = {0: (4.75, yA)}
    xd = xB0 + 1.5                            # the drop from row A's end to row B's start, left of the 300 ns jack's legs
    start_b = (xd, yB)
    for k in range(1, 21):
        if k <= nA:
            x, y, sgn = xA0 + (k - 1) * pitch, yA, 1
        else:
            x, y, sgn = xB0 - (k - nA - 1) * pitch, yB, -1
        l = t.add("L", "L0603 1uH", "1u", x, y, 0 if sgn > 0 else 180, {"1": net(k - 1), "2": net(k)}, hide_value=True)
        cx = x + cap_dx * sgn
        csg = -1 if (sgn > 0 and 11.0 < cx < 19.5) else sgn      # row A's capacitors over the OUT jack stand up instead
        c = t.add("C", "C0402 390pF", "390p", cx, y + PAD["0402"] * csg, 270 if csg > 0 else 90, {"1": net(k), "2": "GND"}, hide_value=True)
        t.wire(net(k - 1), [start_b if k == nA + 1 else nodes[k - 1], (l, "1")])
        nodes[k] = (cx, y)
        t.wire(net(k), [(l, "2"), (c, "1")])
        t.gnd_stub(c, "2", (cx, y + (2 * PAD["0402"] + 0.8) * csg))
    t.wire("IN", [(jin, "1"), (4.75, yA)])
    t.wire("N%d" % nA, [nodes[nA], (xd, yA), (xd, yB)])
    t.wire("OUT", [nodes[20], (jout, "1")])
    # the taps
    r1 = t.add("R", "R0805 470R", "470", 20.0, 4.75, 0, {"1": "T1", "2": "T1J"}, label=None)
    t.wire("T1", [nodes[5], (nodes[5][0], 9.0), (18.4, 9.0), (18.4, 4.75), (r1, "1")])
    t.wire("T1J", [(r1, "2"), (j1, "1")])
    r2 = t.add("R", "R0805 470R", "470", 41.5, 4.75, 0, {"1": "T2", "2": "T2J"}, label=None)
    t.wire("T2", [nodes[10], (nodes[10][0], 9.0), (39.9, 9.0), (39.9, 4.75), (r2, "1")])
    t.wire("T2J", [(r2, "2"), (j2, "1")])
    r3 = t.add("R", "R0805 470R", "470", 46.0, 17.4, 0, {"1": "T3", "2": "T3J"}, label=None)
    t.wire("T3", [nodes[15], (nodes[15][0], 17.4), (r3, "1")])
    t.wire("T3J", [(r3, "2"), (53.5, 17.4), (53.5, 19.3), (58.25, 19.3), (j3, "1")])
    tp = t.loop("IN", 4.75, 15.5, 90, "IN", label_at=(1.6, 0, "left", 0.8))
    t.wire("IN", [(4.75, yA), (tp, "1")])
    tx = 57.0
    t.text(tx, 2.2, t.id, 1.5, 0.3, "center")
    t.text(tx, 4.0, "DELAY LINE", 0.9, 0.17, "center")
    t.text(tx, 5.6, "4.05  6.05", 0.8, 0.15, "center")
    t.text(tx, 6.95, "6.10  7.06", 0.8, 0.15, "center")
    t.text(30.5, 17.35, "400 ns, 50 ohm: 20 x 1uH + 390pF", 0.8, 0.15, "center")
    t.text(30.5, 18.7, "20 ns a section, taps via 470 ohm", 0.8, 0.15, "center")
    import numpy as np
    f = P.logspace(1e5, 1e8, 800)
    sec = []
    for k in range(20):
        sec += [("series", P.L(1e-6, 0.6)), ("shunt", P.C(390e-12))]
    g = P.db(P.response(sec, f))
    t.sim.update(f=f.tolist(), db=g.tolist(), f3=P.corner(f, g), delay_ns=20 * (1e-6 * 390e-12) ** 0.5 * 1e9, z0=(1e-6 / 390e-12) ** 0.5)
    t.plot = dict(kind="bode", x=f, y=g)
    t.result = "a pulse arrives at OUT %.0f ns late, at the taps every %.0f ns; flat to about %.0f MHz, then it disperses" % (t.sim["delay_ns"], t.sim["delay_ns"] / 4, t.sim["f3"] / 1e6)
    t.notes = ["Twenty sections of 1.0 uH and 390 pF: Z0 = sqrt(L/C) = %.0f ohm, %.0f ns a section, cut-off 1 / (pi sqrt(LC)) = 16 MHz." % (t.sim["z0"], t.sim["delay_ns"] / 20),
               "400 ns is 260 ft of RG-58.  Leave OUT open and a pulse comes back the same way up; short it and it comes back inverted;",
               "50 ohm on OUT and nothing comes back (4.05).  The taps are 6.05's echo and 6.10's radar target; near 16 MHz the",
               "phase velocity falls and a chirp spreads (7.06's pure-delay plant below that).  A tap through 470 ohm: x1 into a",
               "high-impedance scope, /10 into 50 ohm."]
    t.sch_draw = lambda ctx, tt: ctx.delay_line(tt)
    return t


def tile_p12():
    """Four LEDs on a 4-way DIP from one jack through 100 ohm: V_f against wavelength is Planck's constant.  The switch
    stands with its ways as rows (pins 1-4 down its left column), the LEDs in a column to its left at the ways' order,
    each to its own ground via at the tile's edge; the LED loop sits in the empty top-right slot."""
    t = Tile("P12", "LEDs", [(0, 3)], subtitle="", sections=["4.10"])
    idx = t.idx
    jin = t.jack("TL", "IN", "IN", "in", "0-5 V")
    LY = LINE_Y
    r1 = t.add("R", "R0805 100R", "100", 7.3, LY, 0, {"1": "IN", "2": "BUS"}, label=(0, T.LABEL_Y - LY, "center", 0.8))
    t.wire("IN", [(jin, "1"), (4.75, LY), (r1, "1")])
    sw = t.add("SW", "DIP4", "DIP4", 14.3, 14.6, 270, {"1": "L1", "2": "L2", "3": "L3", "4": "L4", "5": "BUS", "6": "BUS", "7": "BUS", "8": "BUS"}, hide_value=True)
    pads = dip_pads(4, 14.3, 14.6, 270)
    t.wire("BUS", [(r1, "2"), (pads["8"][0], LY), pads["8"], pads["5"]])
    for k, (key, name) in enumerate((("LED_R", "red"), ("LED_Y", "yellow"), ("LED_G", "green"), ("LED_B", "blue")), 1):
        px, py = pads[str(k)]
        ry = 12.6 + 2.0 * (k - 1)
        d = t.add("LED", key, name, 6.7, ry, 0, {"1": "GND", "2": "L%d" % k}, label=None)   # rot 0: pad 1 (K) at -x, pad 2 (A) at +x
        if k == 1:
            t.wire("L1", [(px, py), (9.3, py), (9.3, ry), (d, "2")])
        elif k == 4:
            t.wire("L4", [(px, py), (px, ry), (d, "2")])
        else:
            xj = {2: 9.3, 3: 8.75}[k]
            t.wire("L%d" % k, [(px, py), (xj, py), (xj, ry), (d, "2")])
        t.gnd_stub(d, "1", (4.4, ry), sym=(-1, 0))
    tp = t.loop("BUS", 14.2, 5.0, 0, "LED", label_at=(2.4, 0, "left", 0.8))
    t.wire("BUS", [(14.2, LY), (tp, "1")])
    t.text(10.5, T.ID_Y, t.id, 1.5, 0.3, "center")
    t.text(10.5, T.SECT_Y0 + 0.5, t.sections[0], 0.8, 0.15, "center")
    t.text(18.8, 18.8, "LEDs", 0.9, 0.17, "right")
    t.result = "one LED at a time; the voltage where it starts to glow against 1/wavelength is h/e"
    t.notes = ["100 ohm from the jack to the four LEDs; the 4-way switch picks one.  Drive from the DAC through the ECP5 board's unipolar",
               "LED output or a bench supply: the knee voltage of each colour against c / lambda gives Planck's constant (4.10).",
               "Way 1 red 630 nm (AlGaInP), 2 yellow 596 (AlGaInP), 3 green 525 (InGaN), 4 blue 469 nm (InGaN): the InGaN pair lie",
               "above the line.  The LED loop is after the 100 ohm: the LED's own voltage.  The colours are not on the silk: light them."]
    t.sch_draw = lambda ctx, tt: ctx.leds(tt)
    return t


def tile_p13():
    """An AM loopstick: a 3-way terminal for the ferrite rod's coil (ends and tap), 47 / 100 / 220 / 470 pF across it on a
    4-way DIP, the jack on the tap; the rod lies along the board's bottom edge under two pairs of cable-tie slots.  The
    terminal's pins are named in the margin below it, where the wires come in."""
    t = Tile("P13", "AM loopstick", [(1, 3), (2, 3)], subtitle="0.5-1.7 MHz", sections=["1.10"])
    idx = t.idx
    jack = t.jack("TL", "OUT", "TAP", "out", "to A4")
    j = t.add("J", "TERM3", "coil", 10.5, 15.2, 180, {"1": "HOT", "2": "TAP", "3": "GND"}, hide_value=True)     # wires enter from the bottom edge
    sw = t.add("SW", "DIP4", "DIP4", 25.0, 13.0, 270, {"1": "HOT", "2": "HOT", "3": "HOT", "4": "HOT", "5": "C4", "6": "C3", "7": "C2", "8": "C1"}, hide_value=True)
    pads = dip_pads(4, 25.0, 13.0, 270)
    t.wire("HOT", [(j, "1"), (19.3, 15.2), (19.3, pads["1"][1]), pads["1"], pads["4"]])
    rows = (9.9, 12.0, 14.1, 16.2)
    xj = (30.0, 30.3, 30.3, 30.0)
    for k, (val, key) in enumerate((("47p", "C0805 47pF"), ("100p", "C0805 100pF"), ("220p", "C0805 220pF"), ("470p", "C0805 470pF")), 1):
        px, py = pads[str(9 - k)]
        ry = rows[k - 1]
        c = t.add("C", key, val, 31.9, ry, 0, {"1": "C%d" % k, "2": "GND"}, label=None)
        t.wire("C%d" % k, [(px, py), (xj[k - 1], py), (xj[k - 1], ry), (c, "1")])
        t.gnd_stub(c, "2", [(34.0, ry), (34.0, 8.4)], sym=(0, -1))
        t.text(35.1, ry, "%d: %s" % (k, val), 0.8, 0.15, "left")
    t.gnd_stub(j, "3", (1.7, 15.2), sym=(0, -1))
    t.wire("TAP", [(j, "2"), (10.5, 10.2), (4.75, 10.2), (jack, "1")])
    a = t.loop("TAP", 14.0, 7.7, 0, "TAP", label_at=(2.4, 0, "left", 0.8))
    t.wire("TAP", [(10.5, 10.2), (14.0, 10.2), (a, "1")])
    b = t.loop("HOT", 25.0, 6.5, 0, "HOT", label_at=(2.4, 0, "left", 0.8))
    t.wire("HOT", [pads["1"], (pads["1"][0], 6.5), (b, "1")])
    for x, s in ((5.5, "GND"), (10.5, "TAP"), (15.5, "HOT")):
        t.text(x, 20.8, s, 0.8, 0.15, "center")                    # in the margin below, where the wires come in
    t.text(11.5, T.ID_Y, t.id, 1.5, 0.3, "center")
    t.text(11.5, T.SECT_Y0 + 0.5, t.sections[0], 0.8, 0.15, "center")
    t.text(40.3, T.NAME_Y, "AM LOOPSTICK 0.5-1.7 MHz", 0.9, 0.17, "right")
    import numpy as np
    L = 330e-6
    t.sim["f_res"] = {k: 1 / (2 * np.pi * np.sqrt(L * c)) for k, c in (("1", 47e-12), ("2", 100e-12), ("3", 220e-12), ("4", 470e-12), ("3+4", 690e-12), ("all", 837e-12))}
    t.result = "with a 330 uH loopstick: 1.28 MHz on 1, 0.88 on 2, 0.59 on 3, 0.40 MHz on 4, and the sums between (the AM band)"
    t.notes = ["Any ferrite-rod AM antenna coil (about 330 uH; 50 to 100 mm long) screws into the terminal, its tap (a quarter of the turns",
               "from the ground end) to the jack.  The switch's capacitors tune it: f = 1 / (2 pi sqrt(L C)), 1.28 MHz with 47 pF down to",
               "0.40 MHz with 470 pF; combine positions for the steps between.  Into A4's LNA and 1.10's AM radio: a real station."]
    t.sch_draw = lambda ctx, tt: ctx.loopstick(tt)
    return t


def tiles():
    return [tile_p1(), tile_p2(), tile_p3(), tile_p4(), tile_p5(), tile_p6(), tile_p7(), tile_p8(), tile_p9(), tile_p10(),
            tile_p11(), tile_p12(), tile_p13()]


# Board-level items that are not tiles: the holes, the identity, the ground loops in the side margins, and the
# cable-tie slots in the bottom margin that hold P13's ferrite rod along the board's edge (3.4 mm along x, a tie's
# width; two rows 5 mm apart so the tie goes down through one and up through the other, round the rod).
GND_LOOPS = [(3.0, 30.0), (3.0, 70.0), (97.0, 30.0), (97.0, 70.0)]       # board mm, one per scope channel
SLOTS = [(30.0, 92.9), (30.0, 98.6), (70.0, 92.9), (70.0, 98.6)]
FRONT_TEXT = [(50.0, 96.0, "ferrite rod along this edge, cable ties through the slots")]
BACK_TEXT = ["AMOD-P: passive building blocks for the FPGA tutorial's converters.  Each tile is one circuit with its own SMA jacks:",
             "cable DAC OUT to a tile's IN and its OUT to ADC IN.  Every jack takes +-4 V.  No power.  The handbook has each tile's",
             "expected response.  P13 wants a ferrite-rod coil (about 330 uH) along this edge, under cable ties through the slots."]


if __name__ == "__main__":
    ts = tiles()
    cells = [c for t in ts for c in t.cells]
    assert len(cells) == 16 and len(set(cells)) == 16, cells
    jacks = [(t.id + " " + j["label"], *t.to_board((j["x"], j["y"]))) for t in ts for j in t.jacks]
    bad = G.check_spacing(jacks)
    print("%d tiles, %d jacks, %d parts; jack pairs closer than %.1f mm: %s" % (len(ts), len(jacks), sum(len(t.parts) for t in ts), G.MIN_JACK_SPACING, bad or "none"))
    for t in ts:
        print("  %-4s %-18s %2d parts  %s" % (t.id, t.name, len(t.parts), t.result[:90]))
