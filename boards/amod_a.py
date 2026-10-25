"""AMOD-A: the active board.  Sixteen cells, twelve tiles (PLAN.md section 5), four layers: L1 the parts and the
drawn wires, L2 ground, L3 the rails as pours (+5 V everywhere, -5 V and +3.3 V in the gutters the tiles reach
with a via), L4 ground fill with the Pmod lines and the back-side text.  Every powered tile has the standard header
(scripts/tiles.power_header): a slide switch along its left edge and a P-FET between its jacks, so the tile's own
rail is dead until the slider is up.  The dense tiles let scripts/router.py find their wires (Tile.route); the
silk draws whatever it found, as it draws every hand-laid wire.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, os.path.join(HERE, "..", "sim"))
import tiles as T
from tiles import Tile, LINE_Y, LOOP_Y, NAME_Y, PAD, power_header, HDR_VS
import geometry as G

STEM = "amod_a"
LAYERS = 4
USB_X = 100.0 - 2.45           # the USB-C's centre: its face 1.2 mm past the right edge (CostasLink's placement, rot 90)


def rot(dx, dy, r):
    return {0: (dx, dy), 90: (dy, -dx), 180: (-dx, -dy), 270: (-dy, dx)}[r % 360]


def sot23_5(x, y, r):
    """Pad centres of a SOT-23-5 at (x, y, r): 1, 2, 3 down the -x column (y -0.95, 0, +0.95), 4, 5 up the +x column."""
    base = {"1": (-1.1375, -0.95), "2": (-1.1375, 0), "3": (-1.1375, 0.95), "4": (1.1375, 0.95), "5": (1.1375, -0.95)}
    return {k: (x + rot(dx, dy, r)[0], y + rot(dx, dy, r)[1]) for k, (dx, dy) in base.items()}


# ------------------------------------------------------------------------------------------------------------ A1 --
def tile_a1():
    """Power: USB-C on the board's right edge (CC pull-downs ask for 5 V), a 2 A PTC, a 5 V TVS, 2 x 10 uF; the
    LM2664 inverts +5 to -5 V (40 mA) and the TPS7A2033 regulates +3.3 V; a green LED on +5 V and a red one on -5 V;
    a 1 x 5 socket with every rail along the top edge, its pins named in the gutter above.  The rails leave on the
    inner layer: +5 V through a via into the pour that covers the board, -5 V through vias into the strip in the
    gutter above, +3.3 V through a via into the strip in the gutter below."""
    t = Tile("A1", "power", [(3, 1)], subtitle="USB-C 5 V in: +5, -5, +3.3 out", sections=["1.01"])
    t.pwr_flags = ["+5V"]
    ux = USB_X - t.x0
    j = t.add("J", "USBC", "USB-C", ux, 10.0, 90, {"A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS", "A5": "CC1", "B5": "CC2",
                                                   "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "SH": "GND"}, hide_value=True)
    # rot 90 puts the pad row at x = ux - 4.045 (A1/B12 at y 13.25 ... A12/B1 at 6.75) and the shell's holes at
    # (ux - 3.13, 5.68 / 14.32): the two SMD ground pads reach the nearer hole with a short wire
    t.wire("GND", [(j, "A1"), (ux - 3.13, 14.32)])
    t.wire("GND", [(j, "B1"), (ux - 3.13, 5.68)])
    # the CC pull-downs (5.1 k: a USB-C source gives 5 V) left of the pad row
    rc1 = t.add("R", "R0805 5.1k", "5.1k", 17.6, 11.5, 0, {"1": "GND", "2": "CC1"}, label=None)
    rc2 = t.add("R", "R0805 5.1k", "5.1k", 17.6, 9.3, 0, {"1": "GND", "2": "CC2"}, label=None)
    t.wire("CC1", [(j, "A5"), (19.3, 11.25), (19.3, 11.5), (rc1, "2")], width=0.25)
    t.wire("CC2", [(j, "B5"), (19.3, 8.25), (19.3, 9.3), (rc2, "2")], width=0.25)
    t.gnd_stub(rc1, "1", (16.688, 10.4), sym=(0, 0))
    t.gnd_stub(rc2, "1", (15.9, 9.3), sym=(0, 0))
    # VBUS: the two pad pairs joined on the back, then up to the PTC
    t.wire("VBUS", [(j, "B9"), (19.9, 12.45)], width=0.25)
    t.wire("VBUS", [(j, "A9"), (19.9, 7.55)], width=0.25)
    t.wire("VBUS", [(19.9, 12.45), (19.9, 7.55)], layer="B.Cu")
    f = t.add("F", "PTC2A", "2A", 15.5, 6.2, 0, {"1": "+5V", "2": "VBUS"}, label=None)
    t.wire("VBUS", [(19.9, 7.55), (19.9, 6.2), (f, "2")])
    # +5 V: the bus at y 6.2 through the TVS's pad and the rail via to the bulk capacitors
    d = t.add("D", "TVS5V", "SMAJ5.0A", 10.6, 7.6, 270, {"1": "+5V", "2": "GND"}, label=None)        # pad 1 (cathode) up, on the bus
    c1 = t.add("C", "C0805 10uF", "10u", 7.0, 6.2, 180, {"1": "+5V", "2": "GND"}, label=None)        # rot 180: pad 1 at +x, on the bus
    c2 = t.add("C", "C0805 10uF", "10u", 7.0, 8.8, 180, {"1": "+5V", "2": "GND"}, label=None)
    t.wire("+5V", [(f, "1"), (c1, "1")])
    t.via("+5V", 9.1, 6.2)
    t.wire("+5V", [(c1, "1"), (c2, "1")])
    t.gnd_stub(d, "2", (10.6, 11.3), sym=(0, 0))
    t.gnd_stub(c1, "2", (6.05, 4.7), sym=(0, 0))
    t.gnd_stub(c2, "2", (5.0, 8.8), sym=(0, 0))
    # -5 V: the LM2664 with its flying and output capacitors; the output to the strip in the gutter above, on the back
    u1 = t.add("U", "LM2664", "LM2664", 6.0, 12.6, 0, {"1": "GND", "2": "-5V", "3": "CAPN", "4": "+5V", "5": "+5V", "6": "CAPP"}, hide_value=False, label=None)
    cf = t.add("C", "C0805 10uF", "10u", 6.0, 15.4, 0, {"1": "CAPN", "2": "CAPP"}, label=None)
    co = t.add("C", "C0805 10uF", "10u", 2.2, 14.6, 270, {"1": "-5V", "2": "GND"}, label=None)
    t.wire("+5V", [(u1, "4"), (u1, "5")])
    t.route("+5V", [(u1, "5"), (c2, "1")])
    t.route("CAPN", [(u1, "3"), (cf, "1")])
    t.route("CAPP", [(u1, "6"), (cf, "2")])
    t.route("-5V", [(u1, "2"), (co, "1")])
    t.gnd_stub(co, "2", (2.2, 17.0))
    t.gnd_stub(u1, "1", (4.86, 10.2), sym=(0, 0))
    t.via("-5V", 1.1, -0.75)
    t.wire("-5V", [(co, "1"), (1.1, 13.65)])
    t.wire("-5V", [(1.1, 13.65), (1.1, -0.75)], layer="B.Cu")
    # +3.3 V: the LDO with 1 uF in and out; the output to the strip in the gutter below and to the socket, on the back
    u2 = t.add("U", "TPS7A2033", "3.3V", 13.8, 13.0, 0, {"1": "+5V", "2": "GND", "3": "+5V", "5": "+3V3"}, hide_value=False, label=None)
    ci = t.add("C", "C0805 1uF", "1u", 10.4, 15.4, 270, {"1": "+5V", "2": "GND"}, label=None)
    cout = t.add("C", "C0805 1uF", "1u", 17.0, 14.8, 270, {"1": "+3V3", "2": "GND"}, label=None)
    t.gnd_stub(u2, "2", (11.4, 13.0), sym=(0, 0))
    t.route("+5V", [(u2, "1"), (u2, "3")])
    t.route("+5V", [(u2, "1"), (ci, "1")])
    t.via("+5V", 10.4, 12.6)
    t.wire("+5V", [(ci, "1"), (10.4, 12.6)])
    t.gnd_stub(ci, "2", (10.4, 17.6), sym=(0, 0))
    t.route("+3V3", [(u2, "5"), (cout, "1")])
    t.gnd_stub(cout, "2", (17.0, 17.2), sym=(0, 0))
    h = t.add("J", "HDR5", "rails", 2.4, 2.3, 90, {"1": "+5V", "2": "GND", "3": "-5V", "4": "GND", "5": "+3V3"}, hide_value=True)
    t.wire("+3V3", [(cout, "1"), (19.0, 13.85)])
    t.via("+3V3", 19.0, 20.5)
    t.wire("+3V3", [(19.0, 13.85), (19.0, 20.5)], layer="B.Cu")
    t.wire("+3V3", [(19.0, 13.85), (19.0, 4.6), (12.56, 4.6), (h, "5")], layer="B.Cu")
    # the socket's +5 V pin sits in the pour, its grounds in the planes; -5 V needs its own via into the strip above
    t.via("-5V", 7.48, -0.75)
    t.wire("-5V", [(h, "3"), (7.48, -0.75)], silk=False)
    for name, px in zip(["+5", "G", "-5", "G", "3V3"], [2.4, 4.94, 7.48, 10.02, 12.56]):
        t.text(px, -0.8, name, 0.8, 0.15, "center")
    # the LEDs in the margin above the USB-C: red on -5 V (nearest the strip's end), green on +5 V, 1 k each to ground.
    # The -5 V strip stops at x 93.6 so the +5 V pour keeps a path down the right margin past these vias.
    dr = t.add("LED", "LED_R", "-5V", 20.6, 2.6, 270, {"1": "-5V", "2": "LEDR"}, label=None)       # rot 270: K (pad 1) at the top
    rr = t.add("R", "R0805 1k", "1k", 22.6, 2.6, 90, {"1": "LEDR", "2": "GND"}, label=None)
    dg = t.add("LED", "LED_G", "+5V", 24.6, 2.6, 90, {"1": "LEDG", "2": "+5V"}, label=None)        # rot 90: A (pad 2) at the top
    rg = t.add("R", "R0805 1k", "1k", 26.6, 2.6, 90, {"1": "LEDG", "2": "GND"}, label=None)
    t.via("-5V", 20.6, -0.75)
    t.wire("-5V", [(dr, "1"), (20.6, -0.75)], silk=False)
    t.wire("LEDR", [(dr, "2"), (rr, "1")])
    t.gnd_stub(rr, "2", (22.6, 0.6), sym=(0, 0))
    t.via("+5V", 24.6, 0.6)
    t.wire("+5V", [(dg, "2"), (24.6, 0.6)], silk=False)
    t.wire("LEDG", [(dg, "1"), (rg, "1")])
    t.gnd_stub(rg, "2", (26.6, 0.6), sym=(0, 0))
    t.text(17.4, 1.9, "A1", 1.5, 0.3, "center")
    t.text(17.4, 3.4, "1.01", 0.8, 0.15, "center")
    t.text(18.7, 18.6, "POWER", 0.9, 0.17, "right")
    t.result = "+5 V from the USB-C (up to 1.5 A), -5 V at 40 mA, +3.3 V at 300 mA; the green LED says 5 V is in, the red one that -5 V is up"
    t.notes = ["USB-C power only: 5.1 k on each CC asks any source for 5 V.  A 2 A PTC, a 5 V TVS (clamps at 9.2 V) and 20 uF.",
               "The LM2664 charge pump makes -5 V for the op-amp tiles (40 mA: four tiles at 10 mA); it is not switched per tile, an op",
               "amp with its +5 V removed draws nothing.  The TPS7A2033 makes 3.3 V for the comparator and the lines that meet the FPGA.",
               "The socket along the top carries +5, ground, -5, ground, +3.3: the bench's rails for a breadboard experiment."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------- A2, A3 --
def opa_tile(t, rg_key, rg_label):
    """The one-op-amp non-inverting gain tile (A2, A3): 50 ohm at the IN jack, the OPA810 (SOT-23-5, rot 0: OUT top-left,
    V- left, +IN bottom-left, -IN bottom-right, V+ top-right) at (10.5, 12.5), its output over the top at y 9.4 to
    Rf (standing right of it) and on to the 49.9 ohm series resistor under the OUT jack, whose far end feeds the jack
    round the right edge and the test loop under it; Rg lies under Rf to ground; the decoupling capacitors stand beside
    the op amp (VS right, -5 V below).  VS comes from the header's FET on the back (two vias); -5 V goes to the gutter
    strip on the back.  Every clearance here was worked out by hand against the footprints' pads: see the chat."""
    idx = t.idx
    rt = t.add("R", "R0805 49.9R", "49.9", 6.6, 9.3, 0, {"1": "IN", "2": "GND"}, label=None)
    t.wire("IN", [("J%d01" % idx, "1"), (4.75, 9.3), (rt, "1")])
    t.wire("IN", [(4.75, 9.3), (4.75, LINE_Y)])
    t.gnd_stub(rt, "2", (8.5, 9.3), sym=(0, 0))
    u = t.add("U", "OPA810", "OPA810", 10.5, 12.5, 0, {"1": "OUT_A", "2": "-5V", "3": "IN", "4": "FB", "5": "VS"}, hide_value=False, label=None)
    t.wire("IN", [(4.75, LINE_Y), (7.2, LINE_Y), (7.2, 13.45), (u, "3")])
    cp = t.add("C", "C0805 100nF", "100n", 13.62, 11.5, 270, {"1": "VS", "2": "GND"}, label=None)          # pad 1 up
    rf = t.add("R", "R0805 10k", "10k", 15.66, 12.5, 270, {"1": "OUT_A", "2": "FB"}, label=None)           # pad 1 up
    rg = t.add("R", rg_key, rg_label, 14.85, 15.5, 180, {"1": "FB", "2": "GND"}, label=None)      # pad 1 at +x
    cn = t.add("C", "C0805 100nF", "100n", 11.35, 15.9, 0, {"1": "-5V", "2": "GND"}, label=None)           # pad 1 at -x
    ro = t.add("R", "R0805 49.9R", "49.9", 17.5, 9.5, 0, {"1": "OUT_A", "2": "OUT"}, label=None)
    tp = t.loop("OUT", 18.1, 12.9, 90, "OUT", label_at="hide")   # on the OUT wire under the OUT jack: no room for a name, none needed
    # the output: over the op amp to Ro's left pad, with a drop into Rf's top between the decoupling capacitor and Ro
    t.wire("OUT_A", [(u, "1"), (9.363, 9.4), (16.588, 9.4), (ro, "1")])
    t.wire("OUT_A", [(15.2, 9.4), (15.2, 11.588), (rf, "1")])
    # feedback: -IN down to a bus at y 14.3 that ends up in Rf's bottom, with a drop into Rg on the way
    t.wire("FB", [(u, "4"), (11.637, 14.3), (15.762, 14.3), (rg, "1")])
    t.wire("FB", [(15.66, 14.3), (rf, "2")])
    t.gnd_stub(rg, "2", (13.938, 16.9), sym=(0, 0))
    t.gnd_stub(cp, "2", (13.62, 13.6), sym=(0, 0))
    # VS: the FET's drain, right along y 18.5, then on the back up to a via above V+ that feeds the pin and its capacitor
    t.wire("VS", [HDR_VS, (8.54, 18.5), (10.2, 18.5)])
    t.wire("VS", [(10.2, 18.5), (10.2, 10.15), (12.3, 10.15)], layer="B.Cu")
    t.wire("VS", [(12.3, 10.15), (12.3, 10.55), (cp, "1")])
    t.wire("VS", [(12.3, 10.55), (11.637, 10.55), (u, "5")])
    # -5 V: V- through the gap between the pin rows down to Cn, and from Cn's pad to the gutter strip on the back
    t.wire("-5V", [(u, "2"), (10.5, 12.5), (10.5, 15.9), (cn, "1")])
    t.wire("-5V", [(cn, "1"), (9.4, 15.9)])
    t.via("-5V", 9.4, 20.5)
    t.wire("-5V", [(9.4, 15.9), (9.4, 20.5)], layer="B.Cu")
    t.gnd_stub(cn, "2", (12.3, 17.3), sym=(0, 0))
    # OUT: Ro's right pad round the right edge to the jack's pin (between its right legs), and down to the loop
    t.wire("OUT", [("J%d02" % idx, "1"), (19.3, 4.75), (19.3, 9.5), (ro, "2")])
    t.wire("OUT", [(ro, "2"), (18.412, 12.9), (tp, "1")])
    t.legend()
    return u


def tile_a2():
    """Gain x10: an OPA810 (140 MHz GBW) non-inverting, 1.1 k and 10 k, 50 ohm in, 49.9 ohm out (x10 into a high impedance,
    x5 into 50 ohm); 14 MHz."""
    t = Tile("A2", "x10", [(0, 0)], supply="+-5 V", subtitle="14 MHz", sections=["4.06", "5.02"])
    t.jack("TL", "IN", "IN", "in", "±0.4 V", silk="IN 50R"); t.jack("TR", "OUT", "OUT", "out", "")
    power_header(t)
    opa_tile(t, "R0805 1.1k", "1.1k")
    t.result = "x10 (20 dB) into a high impedance, x5 into 50 ohm, -3 dB near 14 MHz; clips at about +-4 V"
    t.notes = ["Non-inverting OPA810: gain 1 + 10 k / 1.1 k = 10.1, bandwidth 140 MHz / 10 = 14 MHz.  50 ohm at the input, 49.9 ohm",
               "in series with the output (a 50 ohm load halves it: x5).  Keep the input under 0.4 V peak: the output clips at 4 V."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


def tile_a3():
    """Gain x100 in one OPA810 stage (100 ohm and 10 k): 1.4 MHz, x100 into a high impedance.  The plan's two stages of
    x10 (9 MHz) did not fit a 20 mm cell beside the switch with 0.2 mm clearances; A4 covers the HF case at x100."""
    t = Tile("A3", "x100", [(1, 0)], supply="+-5 V", subtitle="1.4MHz", sections=["4.06", "5.02"])
    t.jack("TL", "IN", "IN", "in", "±40 mV", silk="IN 50R"); t.jack("TR", "OUT", "OUT", "out", "")
    power_header(t)
    opa_tile(t, "R0805 100R", "100R")
    t.result = "x100 (40 dB) into a high impedance, -3 dB near 1.4 MHz; keep the input under 40 mV peak"
    t.notes = ["Non-inverting OPA810: gain 1 + 10 k / 100 = 101, bandwidth 140 MHz / 100 = 1.4 MHz.  50 ohm at the input, 49.9 ohm",
               "in series with the output.  For 40 dB out to 30 MHz use A4 (the OPA847 LNA); this tile is the FET-input, high-impedance",
               "friendly x100 for everything slower.  (The plan's two stages of x10 did not fit the cell.)"]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ A4 --
def tile_a4():
    """HF LNA: the OPA847 (SOIC-8, rot 90: DIS, V+, OUT, NC along the top, NC, -IN, +IN, V- along the bottom) at x100
    (1 k / 10 ohm), 50 ohm at the input, 49.9 ohm out.  The output goes over the top to Rf standing left of the chip;
    the feedback returns along the bottom through pin 1 (NC on the OPA847, so it may carry the node) into -IN; the
    input comes under Rg to +IN.  VS reaches the top row's DIS pin and the decoupling capacitor on the back.
    No test loop: the cell is full (the OUT jack is the monitor)."""
    t = Tile("A4", "LNA", [(2, 0)], supply="+-5 V", subtitle="30 MHz", sections=["4.06", "5.03"])
    idx = t.idx
    t.jack("TL", "IN", "IN", "in", "±30 mV", silk="IN 50R"); t.jack("TR", "OUT", "OUT", "out", "")
    power_header(t)
    rt = t.add("R", "R0805 49.9R", "49.9", 6.6, 9.3, 0, {"1": "IN", "2": "GND"}, label=None)
    t.wire("IN", [("J%d01" % idx, "1"), (4.75, 9.3), (rt, "1")])
    t.gnd_stub(rt, "2", (7.512, 10.5), sym=(0, 0))
    u = t.add("U", "OPA847", "OPA847", 12.4, 13.0, 90, {"1": "FB", "2": "FB", "3": "IN", "4": "-5V", "6": "OUT_A", "7": "VS", "8": "VS"},
              hide_value=False, label=None)
    rf = t.add("R", "R0805 1k", "1k", 8.4, 12.8, 270, {"1": "OUT_A", "2": "FB"}, label=None)              # pad 1 up
    rg = t.add("R", "R0603 10R", "10R", 7.5, 15.4, 0, {"1": "GND", "2": "FB"}, label=None)
    cp = t.add("C", "C0805 100nF", "100n", 16.2, 12.1, 270, {"1": "VS", "2": "GND"}, label=None)           # pad 1 up
    cn = t.add("C", "C0805 100nF", "100n", 16.2, 15.6, 270, {"1": "-5V", "2": "GND"}, label=None)          # pad 1 up
    ro = t.add("R", "R0805 49.9R", "49.9", 16.9, 9.35, 0, {"1": "OUT_A", "2": "OUT"}, label=None)
    # the input: under the termination, down the left, under the chip and up into +IN
    t.wire("IN", [(4.75, 9.3), (4.75, 10.6), (5.85, 10.6), (5.85, 16.3), (9.0, 16.3), (9.0, 16.9), (13.035, 16.9), (u, "3")])
    # the output over the top: left into Rf's top pad, right into Ro
    t.wire("OUT_A", [(rf, "1"), (8.4, 9.0), (13.035, 9.0), (u, "6")])
    t.wire("OUT_A", [(13.035, 9.0), (15.988, 9.0), (ro, "1")])
    # feedback: Rf's bottom pad down to the bottom row, through pin 1 into -IN; Rg hangs off the corner
    t.wire("FB", [(rf, "2"), (8.4, 15.4), (u, "1"), (u, "2")])
    t.wire("FB", [(rg, "2"), (8.4, 15.4)])
    t.gnd_stub(rg, "1", (6.6, 14.1), sym=(0, 0))
    # VS: DIS and V+ joined along the top row, a via beside DIS, the back down to the FET's drain; the capacitor's own via
    t.wire("VS", [(u, "8"), (u, "7")])
    t.wire("VS", [(u, "8"), (9.6, 10.525)])
    t.via("VS", 9.6, 18.7)
    t.wire("VS", [(9.6, 10.525), (9.6, 18.7)], layer="B.Cu")
    t.wire("VS", [(9.6, 18.7), (17.5, 18.7), (17.5, 11.15)], layer="B.Cu", silk=False)     # under the tile's name
    t.wire("VS", [(17.5, 11.15), (cp, "1")])
    t.wire("VS", [(9.6, 18.7), (8.54, 18.7), HDR_VS])
    t.gnd_stub(cp, "2", (15.3, 13.05), sym=(0, 0))
    # -5 V: V- to Cn (the router), Cn's pad to a via and the gutter strip on the back
    t.route("-5V", [(u, "4"), (cn, "1")])
    t.wire("-5V", [(cn, "1"), (18.4, 14.65)])
    t.via("-5V", 18.4, 20.5)
    t.wire("-5V", [(18.4, 14.65), (18.4, 20.5)], layer="B.Cu", silk=False)
    t.gnd_stub(cn, "2", (16.2, 17.85), sym=(0, 0))
    # OUT: Ro round the right edge to the jack's pin
    t.wire("OUT", [("J%d02" % idx, "1"), (19.3, 4.75), (19.3, 9.35), (ro, "2")])
    t.legend()
    t.result = "x100 (40 dB) from 50 ohm, flat 1-30 MHz, about 3 dB noise figure from 50 ohm; keep the input under 30 mV peak"
    t.notes = ["Non-inverting OPA847 (3.9 GHz GBW at this gain, 0.85 nV/rtHz): 1 k / 10 ohm, so x101 and about 39 MHz.  Its",
               "input noise with the 50 ohm termination's own noise gives a noise figure near 3 dB.  The op amp is stable only at",
               "gains above 12 (it is decompensated): do not change Rg upward.  Pin 1 (no connection) carries the feedback node."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


def tiles():
    return [tile_a2(), tile_a3(), tile_a4(), tile_a1()]


GND_LOOPS = [(3.0, 30.0), (3.0, 70.0), (97.0, 60.0), (97.0, 80.0)]
SLOTS = []
# the rails on L3: +5 V under the whole board; -5 V in the gutter under row 0 (and a strip down the left margin to the
# gutter under row 2, for A9); +3.3 V in the gutter under row 1.  Each tile reaches its rail with a via in the gutter.
RAIL_POURS = [("+5V", 0.6, 0.6, 99.4, 99.4, 0),
              # -5 V, one polygon: the gutter under row 0 (into the right margin as far as A1's red LED, no further, so the
              # +5 V pour keeps its path down that margin), a strip down the left margin, the gutter under row 2 for A9
              ("-5V", [(1.0, 27.75), (93.6, 27.75), (93.6, 29.25), (6.5, 29.25), (6.5, 70.75), (51.0, 70.75), (51.0, 72.25), (1.0, 72.25)], 1),
              ("+3V3", 7.0, 49.25, 93.0, 50.75, 1)]
BACK_TEXT = ["AMOD-A: active building blocks on USB-C power.  Each tile has its own slide switch (slider up: on) and SMA jacks;",
             "cable DAC OUT to a tile's IN and its OUT to ADC IN.  The inputs take what the tile's silk says.  The power tile's socket (top edge)",
             "carries +5, ground, -5, ground, +3.3 V.  The handbook has each tile's expected response and its Pmod pins."]


if __name__ == "__main__":
    ts = tiles()
    cells = [c for t in ts for c in t.cells]
    assert len(set(cells)) == len(cells), cells
    jacks = [(t.id + " " + j["label"], *t.to_board((j["x"], j["y"]))) for t in ts for j in t.jacks]
    bad = G.check_spacing(jacks)
    print("%d tiles, %d cells, %d jacks, %d parts; jack pairs closer than %.1f mm: %s" % (len(ts), len(cells), len(jacks), sum(len(t.parts) for t in ts), G.MIN_JACK_SPACING, bad or "none"))
    for t in ts:
        print("  %-4s %-14s %2d parts  %s" % (t.id, t.name, len(t.parts), t.result[:90]))
