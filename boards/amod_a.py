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
def opa_tile(t, rg_key, rg_label, chip="OPA810", rf_key="R0805 10k", jack_in=True, dx=0.0, vs_feed=True, neg_via=None):
    """The one-op-amp non-inverting gain tile (A2, A3): 50 ohm at the IN jack, the OPA810 (SOT-23-5, rot 0: OUT top-left,
    V- left, +IN bottom-left, -IN bottom-right, V+ top-right) at (10.5, 12.5), its output over the top at y 9.4 to
    Rf (standing right of it) and on to the 49.9 ohm series resistor under the OUT jack, whose far end feeds the jack
    round the right edge and the test loop under it; Rg lies under Rf to ground; the decoupling capacitors stand beside
    the op amp (VS right, -5 V below).  VS comes from the header's FET on the back (two vias); -5 V goes to the gutter
    strip on the back.  Every clearance here was worked out by hand against the footprints' pads: see the chat."""
    idx = t.idx
    X = lambda x: x + dx
    if jack_in:
        rt = t.add("R", "R0805 49.9R", "49.9", X(6.6), 9.3, 0, {"1": "IN", "2": "GND"}, label=None)
        t.wire("IN", [("J%d01" % idx, "1"), (X(4.75), 9.3), (rt, "1")])
        t.wire("IN", [(X(4.75), 9.3), (X(4.75), LINE_Y)])
        t.gnd_stub(rt, "2", (X(8.5), 9.3), sym=(0, 0))
        t.wire("IN", [(X(4.75), LINE_Y), (X(7.2), LINE_Y)])
    pins = {"1": "OUT_A", "2": "-5V", "3": "IN", "4": "FB", "5": "VS"}
    if chip == "LT6230":
        pins["6"] = "VS"
    u = t.add("U", chip, chip, X(10.5), 12.5, 0, pins, hide_value=False, label=None)
    t.wire("IN", [(X(7.2), LINE_Y), (X(7.2), 13.45), (u, "3")])
    cp = t.add("C", "C0805 100nF", "100n", X(13.62), 11.5, 270, {"1": "VS", "2": "GND"}, label=None)          # pad 1 up
    rf = t.add("R", rf_key, rf_key.split(" ", 1)[1], X(15.66), 12.5, 270, {"1": "OUT_A", "2": "FB"}, label=None)   # pad 1 up
    rg = t.add("R", rg_key, rg_label, X(14.85), 15.5, 180, {"1": "FB", "2": "GND"}, label=None)      # pad 1 at +x
    cn = t.add("C", "C0805 100nF", "100n", X(11.35), 15.9, 0, {"1": "-5V", "2": "GND"}, label=None)           # pad 1 at -x
    ro = t.add("R", "R0805 49.9R", "49.9", X(17.5), 9.5, 0, {"1": "OUT_A", "2": "OUT"}, label=None)
    tp = t.loop("OUT", X(18.1), 12.9, 90, "OUT", label_at="hide")   # on the OUT wire under the OUT jack: no room for a name, none needed
    # the output: over the op amp to Ro's left pad, with a drop into Rf's top between the decoupling capacitor and Ro
    t.wire("OUT_A", [(u, "1"), (X(9.363), 9.4), (X(16.588), 9.4), (ro, "1")])
    t.wire("OUT_A", [(X(15.2), 9.4), (X(15.2), 11.588), (rf, "1")])
    # feedback: -IN down to a bus at y 14.3 that ends up in Rf's bottom, with a drop into Rg on the way
    t.wire("FB", [(u, "4"), (X(11.637), 14.3), (X(15.762), 14.3), (rg, "1")])
    t.wire("FB", [(X(15.66), 14.3), (rf, "2")])
    t.gnd_stub(rg, "2", (X(13.938), 16.9), sym=(0, 0))
    t.gnd_stub(cp, "2", (X(13.62), 13.6), sym=(0, 0))
    # VS: the FET's drain, right along y 18.5, then on the back up to a via above V+ that feeds the pin and its capacitor
    if vs_feed:
        t.wire("VS", [HDR_VS, (8.54, 18.5), (X(10.2), 18.5)])
    t.wire("VS", [(X(10.2), 18.5), (X(10.2), 10.15), (X(12.3), 10.15)], layer="B.Cu")
    t.wire("VS", [(X(12.3), 10.15), (X(12.3), 10.55), (cp, "1")])
    if chip == "LT6230":                                       # SHDN-bar (top right) to V+ (right middle), both on VS
        t.wire("VS", [(X(12.3), 10.55), (X(11.637), 10.55), (u, "6"), (u, "5")])
    else:
        t.wire("VS", [(X(12.3), 10.55), (X(11.637), 10.55), (u, "5")])
    # -5 V: V- through the gap between the pin rows down to Cn, and from Cn's pad to the gutter strip on the back
    t.wire("-5V", [(u, "2"), (X(10.5), 12.5), (X(10.5), 15.9), (cn, "1")])
    nx, ny = neg_via if neg_via else (X(9.4), 20.5)
    t.wire("-5V", [(cn, "1"), (nx, 15.9)])
    t.via("-5V", nx, ny)
    t.wire("-5V", [(nx, 15.9), (nx, ny)], layer="B.Cu")
    t.gnd_stub(cn, "2", (X(12.3), 17.3), sym=(0, 0))
    # OUT: Ro's right pad round the right edge to the jack's pin (between its right legs), and down to the loop
    out_jack = [j["ref"] for j in t.jacks if j["slot"] == "TR"][0]
    t.wire("OUT", [(out_jack, "1"), (X(19.3), 4.75), (X(19.3), 9.5), (ro, "2")])
    t.wire("OUT", [(ro, "2"), (X(18.412), 12.9), (tp, "1")])
    if jack_in:
        t.legend()
    else:
        t.text(t.w - 1.1, 18.2, (t.name + ((" " + t.subtitle) if t.subtitle else "")).upper(), 0.8, 0.15, "right")
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


# ------------------------------------------------------------------------------------------------------------ A5 --
def tile_a5():
    """Johnson noise: the source resistor (10 k or 1 k by a 2-way DIP, or your own in the 1 x 2 socket) at the +IN of an
    LT6230 (1.1 nV/rtHz) at x100 (1 k / 10 ohm) in the A2 geometry, 49.9 ohm out.  No IN jack: the socket and DIP sit
    in its place.  The amplifier's 2 MHz is the noise bandwidth; the bias current (600 nA) makes 10 k a sensible upper
    limit (0.6 V of DC at the output)."""
    t = Tile("A5", "noise", [(3, 0)], supply="+-5 V", subtitle="x100", sections=["5.08", "7.05"])
    t.jack("TR", "OUT", "OUT", "out", "")
    power_header(t)
    h = t.add("J", "HDR2", "R", 2.6, 2.6, 90, {"1": "IN", "2": "GND"}, hide_value=True)                      # pins at x 2.6, 5.14
    sw = t.add("SW", "DIP2", "DIP2", 5.6, 7.1, 270, {"1": "R1K", "2": "R10K", "3": "IN", "4": "IN"}, hide_value=True)   # pads 1, 2 left; 3, 4 right
    r10 = t.add("R", "R0603 10k", "10k", 2.4, 10.3, 0, {"1": "R10K", "2": "GND"}, label=None)
    r1 = t.add("R", "R0603 1k", "1k", 5.5, 10.3, 0, {"1": "R1K", "2": "GND"}, label=None)
    t.wire("IN", [(sw, "3"), (sw, "4"), (9.41, 5.6), (2.6, 5.6), (h, "1")])
    t.wire("IN", [(sw, "3"), (7.2, 7.735), (7.2, LINE_Y)])
    t.wire("R10K", [(sw, "2"), (1.79, 10.3), (r10, "1")])
    t.wire("R1K", [(sw, "1"), (4.4, 6.465), (4.4, 10.3), (r1, "1")])
    t.gnd_stub(r10, "2", (3.175, 9.3), sym=(0, 0))
    t.gnd_stub(r1, "2", (6.275, 11.5), sym=(0, 0))
    opa_tile(t, "R0603 10R", "10R", chip="LT6230", rf_key="R0805 1k", jack_in=False)
    t.text(10.0, 2.4, "A5", 1.5, 0.3, "center")
    t.text(10.0, 4.4, "5.08", 0.8, 0.15, "center")
    t.result = "the source resistor's Johnson noise x100: about 1.3 mV rms from 10 k, 0.4 mV from 1 k, 0.16 mV (the amplifier itself) shorted"
    t.notes = ["4kTR: 12.9 nV/rtHz from 10 k at room temperature, x100 and the LT6230's 2 MHz: 1.3 mV rms.  Both DIP ways off",
               "with nothing in the socket leaves +IN open: switch one on, or plug a resistor (100 ohm to 10 k) into the socket.",
               "Keep the scope AC-coupled: 600 nA of bias current puts 0.6 V of DC on the output with 10 k."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ A6 --
def tile_a6():
    """Delta-sigma: a TLV3501 compares the integrator node (IN through 10 k, the FPGA's bit back through 10 k, 10 nF to
    ground) with a mid-rail reference (10 k / 10 k / 100 n from VS); its bit goes to Pmod 2 and a loop; the FPGA's
    bit comes in on Pmod 1.  +3.3 V so the bit is the FPGA's logic level."""
    t = Tile("A6", "1-bit ADC", [(0, 1)], supply="+3.3 V", sections=["7.05"])
    idx = t.idx
    t.jack("TL", "IN", "IN", "in", "±1.5 V", silk="IN 10K")
    power_header(t, rail="+3V3")
    rin = t.add("R", "R0805 10k", "10k", 6.6, 9.3, 0, {"1": "IN", "2": "NODE"}, label=None)
    t.wire("IN", [("J%d01" % idx, "1"), (4.75, 9.3), (rin, "1")])
    rfb = t.add("R", "R0603 10k", "10k", 6.5, 12.6, 270, {"1": "/PMOD1", "2": "NODE"}, label=None)       # pad 1 up
    cint = t.add("C", "C0805 10nF", "10n", 8.3, 15.3, 0, {"1": "NODE", "2": "GND"}, label=None)
    u = t.add("U", "TLV3501", "TLV3501", 10.5, 12.5, 0, {"1": "VREF", "2": "GND", "3": "NODE", "4": "VS", "5": "/PMOD2", "6": "GND"},
              hide_value=False, label=None)
    t.wire("NODE", [(rin, "2"), (7.4, 9.3), (7.4, 15.3), (cint, "1")])
    t.wire("NODE", [(7.4, 13.45), (u, "3")])
    t.wire("NODE", [(rfb, "2"), (7.4, 13.375)])
    t.wire("/PMOD1", [(rfb, "1"), (6.5, 10.5)])
    t.via("/PMOD1", 6.5, 10.5)
    t.gnd_stub(cint, "2", (10.0, 16.6), sym=(0, 0))
    t.gnd_stub(u, "2", (8.3, 12.5), sym=(0, 0))
    t.gnd_stub(u, "6", (11.637, 10.5), sym=(0, 0))
    # VS: the FET's drain on the back to the comparator's capacitor and, round the jack's right side, to the divider
    cp = t.add("C", "C0805 100nF", "100n", 14.3, 13.9, 90, {"1": "VS", "2": "GND"}, label=None)             # pad 1 down
    t.wire("VS", [HDR_VS, (8.54, 18.5), (10.2, 18.5)])
    t.wire("VS", [(10.2, 18.5), (14.3, 18.5), (14.3, 16.4)], layer="B.Cu", silk=False)
    t.wire("VS", [(10.2, 18.5), (9.0, 18.5), (9.0, 2.5), (14.1, 2.5)], layer="B.Cu", silk=False)
    t.wire("VS", [(14.3, 16.4), (cp, "1")])
    t.wire("VS", [(cp, "1"), (12.4, 14.85), (12.4, 13.45), (u, "4")])
    t.gnd_stub(cp, "2", (14.3, 11.6), sym=(0, 0))
    r1 = t.add("R", "R0805 10k", "10k", 14.1, 4.5, 270, {"1": "VS", "2": "VREF"}, label=None)                # pad 1 up
    r2 = t.add("R", "R0805 10k", "10k", 14.1, 8.0, 270, {"1": "VREF", "2": "GND"}, label=None)
    cref = t.add("C", "C0805 100nF", "100n", 16.6, 8.0, 270, {"1": "VREF", "2": "GND"}, label=None)
    t.wire("VS", [(14.1, 2.5), (r1, "1")])
    t.wire("VREF", [(r1, "2"), (r2, "1")])
    t.wire("VREF", [(r2, "1"), (16.6, 7.088), (cref, "1")])
    t.wire("VREF", [(14.1, 6.25), (12.2, 6.25), (12.2, 9.4), (9.363, 9.4), (u, "1")])
    t.gnd_stub(r2, "2", (15.35, 8.9), sym=(0, 0))
    t.gnd_stub(cref, "2", (15.35, 8.9), sym=(0, 0))
    # the bit: over the top to the loop under the (absent) OUT jack and to the Pmod via below it
    tp = t.loop("/PMOD2", 18.1, 12.9, 90, "BIT", label_at=(0.8, 2.9, "right", 0.8))
    t.wire("/PMOD2", [(u, "5"), (12.8, 12.5), (12.8, 10.1), (18.1, 10.1), (tp, "1")])
    t.wire("/PMOD2", [(tp, "1"), (18.1, 16.5)], silk=False)
    t.via("/PMOD2", 18.1, 16.5)
    t.legend()
    t.result = "a one-bit stream on Pmod 2 whose density follows IN; the FPGA closes the loop through Pmod 1 (the handbook's gateware)"
    t.notes = ["First-order delta-sigma: the comparator decides, the FPGA registers the bit and feeds it back through 10 k into the",
               "10 k / 10 nF integrator (1.6 kHz; clock the loop at 1-10 MHz).  IN takes 0 to 3.3 V, or +-1.5 V about the 1.65 V reference",
               "if you AC-couple.  Both Pmod lines are 3.3 V logic; the tile runs on the 3.3 V rail."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ A8 --
def tile_a8():
    """Heater and thermometers: two 15 ohm 2512 in series across VS (0.83 W at 5 V) switched by an AO3400 from Pmod 3
    (10 k pull-down); a 10 k NTC in a divider with 10 k to a loop; a TMP235 (10 mV/K + 500 mV) to the OUT jack.  The
    heaters lie in the middle of the cell, the NTC against their left pads."""
    t = Tile("A8", "heat", [(2, 1)], supply="+5 V", sections=["5.02", "7.06"])
    idx = t.idx
    t.jack("TR", "OUT", "OUT", "out", "", silk="TEMP OUT")
    power_header(t)
    ra = t.add("R", "R2512_15R", "15R", 11.3, 10.2, 0, {"1": "HTR", "2": "VS"}, label=None)
    rb = t.add("R", "R2512_15R", "15R", 11.3, 14.35, 0, {"1": "HTR", "2": "DRN"}, label=None)
    q = t.add("Q", "NFET", "AO3400A", 17.2, 14.35, 0, {"1": "/PMOD3", "2": "GND", "3": "DRN"}, hide_value=True)
    rpd = t.add("R", "R0603 10k", "10k", 18.5, 11.0, 270, {"1": "/PMOD3", "2": "GND"}, label=None)          # pad 1 up
    t.wire("HTR", [(ra, "1"), (rb, "1")])
    t.wire("DRN", [(rb, "2"), (q, "3")])
    t.gnd_stub(q, "2", (16.262, 16.7), sym=(0, 0))
    t.wire("/PMOD3", [(q, "1"), (16.262, 11.6)])
    t.via("/PMOD3", 16.262, 11.6)
    t.wire("/PMOD3", [(16.262, 11.6), (17.3, 11.6), (17.3, 10.225), (rpd, "1")])
    t.gnd_stub(rpd, "2", (18.5, 13.1), sym=(0, 0))
    # VS on the back: the FET's drain to the top heater's right pad and, up the left, to the TMP235
    t.wire("VS", [HDR_VS, (8.54, 18.5), (10.2, 18.5)])
    t.via("VS", 15.5, 9.0)
    t.via("VS", 3.462, 2.2)
    t.wire("VS", [(10.2, 18.5), (15.5, 18.5), (15.5, 9.0)], layer="B.Cu", silk=False)
    t.wire("VS", [(10.2, 18.5), (6.3, 18.5), (6.3, 2.2), (3.462, 2.2)], layer="B.Cu", silk=False)
    t.wire("VS", [(15.5, 9.0), (15.5, 10.2), (ra, "2")])
    tmp = t.add("U", "TMP235", "TMP235", 4.4, 4.6, 0, {"1": "VS", "2": "OUT", "3": "GND"}, hide_value=False, label=None)
    cd = t.add("C", "C0603 100nF", "100n", 1.6, 4.1, 270, {"1": "VS", "2": "GND"}, label=None)
    t.wire("VS", [(3.462, 2.2), (tmp, "1")])
    t.wire("VS", [(tmp, "1"), (1.6, 3.65), (cd, "1")])
    t.gnd_stub(cd, "2", (1.6, 6.2), sym=(0, 0))
    t.gnd_stub(tmp, "3", (5.338, 6.0), sym=(0, 0))
    t.wire("OUT", [(tmp, "2"), (3.462, 7.6), (11.2, 7.6), (11.2, 4.75), ("J%d01" % idx, "1")])
    t.text(8.5, 2.4, "A8", 1.5, 0.3, "center")
    t.text(8.5, 4.4, "5.02", 0.8, 0.15, "center")
    t.text(8.5, 5.75, "7.06", 0.8, 0.15, "center")
    t.text(t.w - 1.1, 18.2, "HEAT 0.8 W", 0.8, 0.15, "right")
    t.result = "0.83 W into the board when Pmod 3 is high (the FET's drain), 10 mV/K + 500 mV on OUT"
    t.notes = ["Two 15 ohm in series: 30 ohm, 170 mA, 0.83 W from the switched 5 V when Pmod 3 is high (10 k keeps it off otherwise).",
               "The TMP235 reads 750 mV at 25 C and climbs 10 mV per kelvin.  A feedback-control experiment: hold the TMP235 at a",
               "set point with the FPGA's PWM.  (The plan's NTC divider did not fit the cell beside the two 2512s.)"]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ----------------------------------------------------------------------------------------------------------- A11 --
def tile_a11():
    """40 kHz ultrasound, two cells.  Left: the DRV8837 H-bridge (IN1, IN2 from Pmod 5 and 6) drives a transducer in
    pins 1 and 5 of a 1 x 5 socket along the top edge; the Pmod plug hangs off the bottom edge below this cell, and
    the board's Pmod lines come down the back of this cell's right third to it.  Right: the second transducer in its
    socket, 10 nF into the A2 geometry at x100 (100 ohm / 10 k, 3.9 k to ground at +IN) and out to RX OUT.
    +-5 V (the op amp), the bridge on the switched +5 V."""
    t = Tile("A11", "ultrasound", [(0, 3), (1, 3)], supply="+-5 V", sections=["4.06"])
    t.jack("TR", "OUT", "OUT", "out", "", silk="RX OUT")
    power_header(t)
    # --- transmit: the bridge beside the socket's left end
    jtx = t.add("J", "HDR5", "TX", 2.4, 2.6, 90, {"1": "OUT1", "5": "OUT2"}, hide_value=True)             # pins at x 2.4 ... 12.56
    d = t.add("U", "DRV8837", "DRV8837", 8.0, 8.5, 0, {"1": "VS", "2": "OUT1", "3": "OUT2", "4": "GND", "5": "/PMOD5", "6": "/PMOD6",
                                                       "7": "VS", "8": "VS", "9": "GND"}, hide_value=False, label=None)
    cvcc = t.add("C", "C0603 100nF", "100n", 11.2, 7.0, 0, {"1": "VS", "2": "GND"}, label=None)
    cvm = t.add("C", "C0603 100nF", "100n", 10.4, 5.3, 0, {"1": "VS", "2": "GND"}, label=None)
    W = 0.25                                                                                              # 0.5 mm pitch pins
    t.wire("OUT1", [(d, "2"), (5.9, 8.25), (5.9, 5.5), (2.4, 5.5), (jtx, "1")], width=W)
    t.wire("OUT2", [(d, "3"), (5.5, 8.75), (5.5, 10.6), (14.0, 10.6), (14.0, 5.0), (12.56, 5.0), (jtx, "5")], width=W)
    t.gnd_stub(d, "4", (6.4, 9.9), sym=(0, 0))
    t.gnd_stub(d, "9", (8.0, 8.5), sym=(0, 0))                                                           # in the thermal pad
    t.wire("VS", [(d, "8"), (9.55, 7.75), (9.55, 7.0), (cvcc, "1")], width=W)
    t.wire("VS", [(d, "7"), (9.55, 8.25), (9.55, 7.75)], width=W)
    t.wire("VS", [(9.55, 7.0), (9.9, 7.0), (9.9, 6.3)], width=W)
    t.wire("VS", [(d, "1"), (6.4, 7.75), (6.4, 6.3), (9.9, 6.3)], width=W)
    t.wire("VS", [(9.9, 6.3), (9.9, 5.3), (cvm, "1")], width=W)
    t.via("VS", 9.9, 6.3)
    t.via("VS", 9.9, 17.3)
    t.wire("VS", [(9.9, 6.3), (9.9, 17.3)], layer="B.Cu", silk=False)
    t.wire("VS", [(9.9, 17.3), (9.9, 18.5)])
    t.gnd_stub(cvcc, "2", (12.9, 7.0), sym=(0, 0))
    t.gnd_stub(cvm, "2", (11.175, 4.1), sym=(0, 0))
    t.wire("/PMOD6", [(d, "6"), (10.3, 8.75), (10.3, 8.3), (10.6, 8.3)], width=W)
    t.via("/PMOD6", 10.6, 8.3)
    t.wire("/PMOD5", [(d, "5"), (11.6, 9.25)], width=W)
    t.via("/PMOD5", 11.6, 9.25)
    t.text(17.5, 6.0, "A11", 0.9, 0.17, "center")
    t.text(17.5, 7.4, "4.06", 0.8, 0.15, "center")
    # --- receive: the socket in the right cell's top-left, 10 nF and 3.9 k into the A2 geometry
    jrx = t.add("J", "HDR5", "RX", 21.2, 2.6, 90, {"1": "RXA", "5": "GND"}, hide_value=True)             # pins at x 21.2 ... 31.36
    cin = t.add("C", "C0805 10nF", "10n", 26.0, 9.3, 0, {"1": "RXA", "2": "IN"}, label=None)
    r1 = t.add("R", "R0805 3.9k", "3.9k", 23.0, 11.8, 270, {"1": "IN", "2": "GND"}, label=None)        # pad 1 up
    t.wire("RXA", [(jrx, "1"), (21.2, 9.3), (cin, "1")])
    t.wire("IN", [(cin, "2"), (26.95, 10.888), (r1, "1")])
    t.wire("IN", [(cin, "2"), (28.7, 9.3), (28.7, LINE_Y)])
    t.gnd_stub(r1, "2", (23.0, 14.1), sym=(0, 0))
    t.wire("VS", [HDR_VS, (8.54, 18.5), (31.7, 18.5)], silk=False)                                     # under the tile's name
    opa_tile(t, "R0805 100R", "100R", jack_in=False, dx=21.5, vs_feed=False, neg_via=(30.1, -0.75))
    # --- the Pmod plug, below the left cell in the bottom margin (global 15.4, 96.5), and the board's lines to it:
    # the upper row (even pads) straight down from feeds on the back; the lower row (odd pads) through the upper row's
    # gaps on the front with 0.2 mm tracks (pads 1, 3) or along the bottom edge (pads 5, 7)
    pm = t.add("J", "PMOD", "Pmod", 8.05, 24.25, 0, {"1": "/PMOD1", "3": "/PMOD2", "5": "/PMOD3", "2": "/PMOD5", "4": "/PMOD6",
                                                      "9": "GND", "10": "GND", "11": "/PMOD_VCC", "12": "/PMOD_VCC"}, hide_value=True)
    t.wire("/PMOD_VCC", [(pm, "11"), (pm, "12")], silk=False)
    t.wire("/PMOD5", [(11.6, 9.25), (11.6, 20.1), (1.7, 20.1), (pm, "2")], layer="B.Cu", silk=False)
    t.wire("/PMOD6", [(10.6, 8.3), (12.3, 8.3), (12.3, 20.75), (4.24, 20.75), (pm, "4")], layer="B.Cu", silk=False)
    t.via("/PMOD1", 14.05, 20.2)
    t.wire("/PMOD1", [(14.05, 20.2), (2.97, 20.2), (2.97, 24.75), (pm, "1")], width=0.2, silk=False)
    t.via("/PMOD2", 14.75, 20.85)
    t.wire("/PMOD2", [(14.75, 20.85), (5.51, 20.85), (5.51, 24.75), (pm, "3")], width=0.2, silk=False)
    t.via("/PMOD3", 16.55, 26.5)
    t.wire("/PMOD3", [(16.55, 26.5), (16.55, 27.15), (6.78, 27.15), (pm, "5")], width=0.2, silk=False)
    t.result = "a 40 kHz burst from Pmod 5/6 leaves the TX transducer; its echo arrives x100 on RX OUT (hold a reflector over the board)"
    t.notes = ["Drive IN1/IN2 (Pmod 5, 6) in antiphase at 40 kHz for 8-20 cycles: the bridge puts 10 V peak to peak across the TX",
               "transducer.  The RX transducer's 10 nF / 3.9 k high-pass (4 kHz) feeds an OPA810 at x100 (1.4 MHz: the transducer's",
               "own resonance sets the band).  Time of flight at 343 m/s: 5.8 us per mm there and back.  Put the two transducers",
               "in pins 1 and 5 (10.16 mm; their leads are 10 mm apart)."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ A7 --
def tile_a7():
    """PLL: a CD74HC4046A (SOIC-16 lying across the cell, rot 270: GND, C1, INH, VCOout, COMPin, PC1, PCP along the
    top; VCOin, R1, PC2, SIGin, VCC along the bottom).  IN through 100 n and 1 k into SIGin (self-biased); the VCO
    (R1 10 k, C1 1 nF: about 100 kHz) out through 470 ohm and back into COMPin; PC2's tri-state output through the
    10 k / 100 n lag filter into VCOin.  The three wires that must cross the chip run in the gap between its pin
    rows; the loop filter and the input network stand in the column left of the chip (0402s).  No loops: probe
    pin 9 (VCOin, the demodulated FM) and pin 13."""
    t = Tile("A7", "PLL 4046", [(1, 1)], supply="+5 V", sections=["4.01"])
    idx = t.idx
    t.jack("TL", "IN", "IN", "in", "±1 V", silk="IN 1K"); t.jack("TR", "OUT", "OUT", "out", "", silk="VCO OUT")
    power_header(t)
    u = t.add("U", "HC4046", "HC4046", 12.6, 12.15, 270, {"3": "VCO_A", "4": "VCO_A", "5": "GND", "6": "C1A", "7": "C1B", "8": "GND",
                                                        "9": "NODE", "11": "R1", "13": "PC2", "14": "SIG", "16": "VS"}, hide_value=False, label=None)
    cs = t.add("C", "C0402 100nF", "100n", 6.5, 9.4, 270, {"1": "IN", "2": "INA"}, label=None)          # pad 1 up
    rs = t.add("R", "R0402 1k", "1k", 6.5, 11.3, 270, {"1": "INA", "2": "SIG"}, label=None)
    rf = t.add("R", "R0402 10k", "10k", 6.5, 13.5, 270, {"1": "PC2", "2": "NODE"}, label=None)
    cf = t.add("C", "C0402 100nF", "100n", 6.5, 15.35, 270, {"1": "NODE", "2": "GND"}, label=None)
    c1 = t.add("C", "C0402 1nF", "1n", 10.06, 7.9, 0, {"1": "C1B", "2": "C1A"}, label=None)
    r1 = t.add("R", "R0402 10k", "10k", 11.2, 16.6, 0, {"1": "R1", "2": "GND"}, label=None)
    cp = t.add("C", "C0402 100nF", "100n", 17.3, 16.6, 0, {"1": "VS", "2": "GND"}, label=None)
    ro = t.add("R", "R0402 470R", "470", 18.5, 11.0, 270, {"1": "OUT", "2": "VCO_A"}, label=None)
    t.wire("IN", [("J%d01" % idx, "1"), (4.75, 9.0), (6.5, 9.0), (cs, "1")])
    t.wire("INA", [(cs, "2"), (rs, "1")])
    t.wire("SIG", [(rs, "2"), (14.505, 11.78), (u, "14")])
    t.wire("PC2", [(u, "13"), (13.235, 12.5), (6.5, 12.5), (rf, "1")])
    t.wire("NODE", [(rf, "2"), (cf, "1")])
    t.wire("NODE", [(6.5, 14.4), (8.155, 14.4), (u, "9")])
    t.wire("C1B", [(u, "7"), (9.425, 7.9), (c1, "1")])
    t.wire("C1A", [(u, "6"), (10.695, 7.9), (c1, "2")])
    t.wire("R1", [(u, "11"), (r1, "1")])
    t.wire("VCO_A", [(u, "4"), (13.235, 11.2), (18.2, 11.2), (18.2, 11.51), (ro, "2")])
    t.wire("VCO_A", [(14.505, 11.2), (u, "3")])
    t.wire("OUT", [(ro, "1"), (18.5, 9.3), (19.3, 9.3), (19.3, 4.75), ("J%d02" % idx, "1")])
    t.gnd_stub(u, "8", (7.5, 9.8), sym=(0, 0))
    t.gnd_stub(u, "5", (11.965, 11.1), sym=(0, 0))
    t.gnd_stub(r1, "2", (11.71, 17.5), sym=(0, 0))
    t.gnd_stub(cp, "2", (18.3, 17.3), sym=(0, 0))
    t.gnd_stub(cf, "2", (5.7, 15.5), sym=(0, 0))
    t.wire("VS", [HDR_VS, (8.54, 18.5), (10.2, 18.5)])
    t.wire("VS", [(10.2, 18.5), (16.82, 18.5), (16.82, 17.6)], layer="B.Cu", silk=False)
    t.wire("VS", [(16.82, 17.6), (cp, "1"), (u, "16")])
    t.text(10.0, 2.2, "A7", 1.5, 0.3, "center")
    t.text(10.0, 3.9, "4.01", 0.8, 0.15, "center")
    t.text(t.w - 1.1, 18.2, "PLL 4046", 0.8, 0.15, "right")
    t.result = "VCO OUT locks to a 50-200 kHz square or sine on IN; pin 9 is the demodulated FM, pin 13 the phase detector"
    t.notes = ["CD74HC4046A: R1 10 k, C1 1 nF put the VCO near 100 kHz (R2 open: it can go down to 0).  PC2 (the edge-triggered",
               "tri-state detector) through 10 k / 100 n into VCOin: a lag filter, so expect ringing on lock.  IN self-biases",
               "through 100 n / 1 k (any level above 0.4 V peak).  VCO OUT is 5 V CMOS through 470 ohm.  Probe pins 9 and 13."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ A9 --
def tile_a9():
    """Mixer: the MC1496 (SOIC-14 across the cell, rot 90: SIG+, GAIN, GAIN, SIG-, BIAS, OUT+, NC along the bottom;
    VEE, NC, OUT-, NC, CAR-, NC, CAR+ along the top) on +-5 V.  RF IN through 100 n into SIG+, 51 ohm from each signal
    input to ground; LO IN through 100 n into CAR+, 51 ohm from each carrier input to a 2.5 V bias (10 k / 10 k /
    100 n); 1 k between the gain pins, 3.9 k from BIAS to -5 V (1 mA), 1.5 k loads to the switched 5 V; OUT+ through
    100 n to IF OUT (high impedance: 1.5 k source).  The board's Pmod lines pass down the back of this tile's middle
    x 14 ... 16.5, which the layout keeps free there.  No carrier-null trimmer."""
    t = Tile("A9", "mixer", [(0, 2), (1, 2)], supply="+-5 V", subtitle="MC1496", sections=["1.10", "6.02"])
    idx = t.idx
    t.jack("TL", "RF", "RF", "in", "±0.3 V", silk="RF IN"); t.jack("TM", "LO", "LO", "in", "±0.3 V", silk="LO IN")
    t.jack("TR", "IF", "IF", "out", "", silk="IF OUT")
    power_header(t)
    u = t.add("U", "MC1496", "MC1496", 20.75, 12.1, 90, {"1": "SIGA", "2": "GAIN2", "3": "GAIN3", "4": "SIGB", "5": "BIAS", "6": "OUTA", "7": "OUTA",
                                                        "8": "CARA", "10": "CARB", "12": "OUTB", "14": "-5V"}, hide_value=False, label=None)
    cs = t.add("C", "C0603 100nF", "100n", 9.0, 13.5, 0, {"1": "RF", "2": "SIGA"}, label=None)
    cl = t.add("C", "C0603 100nF", "100n", 26.5, 7.0, 270, {"1": "LO", "2": "CARA"}, label=None)             # pad 1 up
    rs1 = t.add("R", "R0402 51R", "51", 16.94, 16.9, 270, {"1": "SIGA", "2": "GND"}, label=None)              # the bottom column: pad 1 up
    rg = t.add("R", "R0402 1k", "1k", 18.21, 16.9, 270, {"1": "GAIN2", "2": "GAIN3"}, label=None)
    rs2 = t.add("R", "R0402 51R", "51", 20.75, 16.9, 270, {"1": "SIGB", "2": "GND"}, label=None)
    rb = t.add("R", "R0402 3.9k", "3.9k", 22.02, 16.9, 270, {"1": "BIAS", "2": "-5V"}, label=None)
    rl1 = t.add("R", "R0402 1.5k", "1.5k", 23.29, 16.9, 270, {"1": "OUTA", "2": "VS"}, label=None)
    rl2 = t.add("R", "R0805 1.5k", "1.5k", 14.5, 12.5, 270, {"1": "OUTB", "2": "VS"}, label=None)             # pad 1 up
    rc2 = t.add("R", "R0402 51R", "51", 26.2, 12.5, 270, {"1": "CARB", "2": "CB"}, label=None)
    rc1 = t.add("R", "R0402 51R", "51", 29.0, 11.0, 270, {"1": "CARA", "2": "CB"}, label=None)
    cb = t.add("C", "C0603 100nF", "100n", 30.8, 13.0, 270, {"1": "CB", "2": "GND"}, label=None)
    rb1 = t.add("R", "R0603 10k", "10k", 32.4, 10.3, 270, {"1": "VS", "2": "CB"}, label=None)
    rb2 = t.add("R", "R0603 10k", "10k", 32.4, 13.4, 270, {"1": "CB", "2": "GND"}, label=None)
    cp = t.add("C", "C0603 100nF", "100n", 26.0, 17.0, 0, {"1": "VS", "2": "GND"}, label=None)
    co = t.add("C", "C0603 100nF", "100n", 36.0, 15.3, 0, {"1": "OUTA", "2": "IF"}, label=None)
    # inputs
    t.wire("RF", [("J%d01" % idx, "1"), (4.75, 9.3), (7.2, 9.3), (7.2, 13.5), (cs, "1")])
    t.wire("SIGA", [(cs, "2"), (10.6, 13.5), (10.6, 14.6), (16.94, 14.6), (u, "1")])
    t.wire("SIGA", [(u, "1"), (rs1, "1")])
    t.wire("GAIN2", [(u, "2"), (rg, "1")])
    t.wire("GAIN3", [(rg, "2"), (19.48, 17.38), (u, "3")])
    t.wire("SIGB", [(u, "4"), (rs2, "1")])
    t.wire("BIAS", [(u, "5"), (rb, "1")])
    t.wire("LO", [("J%d02" % idx, "1"), (26.5, 4.75), (cl, "1")])
    t.wire("CARA", [(cl, "2"), (26.5, 9.625), (u, "8")])
    t.wire("CARA", [(26.5, 9.625), (29.0, 9.625), (rc1, "1")])
    t.wire("CARB", [(u, "10"), (22.02, 11.65), (26.2, 11.65), (rc2, "1")])
    # the carrier bias
    t.wire("CB", [(rc2, "2"), (29.0, 12.98), (rc1, "2")])
    t.wire("CB", [(29.0, 12.225), (32.4, 12.225), (rb2, "1")])
    t.wire("CB", [(rb1, "2"), (rb2, "1")])
    t.gnd_stub(cb, "2", (30.8, 14.4), sym=(0, 0))
    t.gnd_stub(rb2, "2", (33.3, 14.175), sym=(0, 0))
    # outputs: OUT+ through the NC pin 7 to the right, along the bottom of the right cell to the capacitor and the jack
    t.wire("OUTA", [(u, "6"), (rl1, "1")])
    t.wire("OUTA", [(u, "6"), (u, "7"), (25.3, 14.575), (25.3, 15.3), (co, "1")])
    t.wire("IF", [(co, "2"), (40.8, 15.3), (40.8, 4.75), ("J%d03" % idx, "1")])
    t.wire("OUTB", [(u, "12"), (19.48, 11.4), (14.5, 11.4), (rl2, "1")])
    # rails: -5 V from the gutter below on the back (VEE and the bias resistor); VS along the bottom on the front
    t.wire("-5V", [(u, "14"), (12.9, 9.625)])
    t.via("-5V", 12.9, 20.5)
    t.wire("-5V", [(12.9, 9.625), (12.9, 20.5)], layer="B.Cu", silk=False)
    t.wire("-5V", [(rb, "2"), (22.5, 18.0)])
    t.via("-5V", 22.5, 20.5)
    t.wire("-5V", [(22.5, 18.0), (22.5, 20.5)], layer="B.Cu", silk=False)
    t.gnd_stub(rs1, "2", (17.3, 18.1), sym=(0, 0))
    t.gnd_stub(rs2, "2", (20.75, 18.15), sym=(0, 0))
    t.gnd_stub(cp, "2", (27.5, 17.0), sym=(0, 0))
    t.wire("VS", [HDR_VS, (8.54, 18.95), (34.0, 18.95)], silk=False)
    t.wire("VS", [(rl1, "2"), (23.29, 18.95)])
    t.wire("VS", [(cp, "1"), (25.225, 18.95)])
    t.wire("VS", [(rl2, "2"), (11.8, 13.412), (11.8, 13.9)])
    t.wire("VS", [(11.8, 13.9), (11.8, 18.4)], layer="B.Cu", silk=False)
    t.wire("VS", [(11.8, 18.4), (11.8, 18.95)])
    t.wire("VS", [(34.0, 18.95), (34.0, 9.525)], layer="B.Cu", silk=False)
    t.wire("VS", [(34.0, 9.525), (rb1, "1")])
    t.text(12.75, 2.4, "A9", 1.5, 0.3, "center")
    t.text(12.75, 4.4, "1.10", 0.8, 0.15, "center")
    t.text(12.75, 5.75, "6.02", 0.8, 0.15, "center")
    t.text(t.w - 1.1, 18.2, "MIXER MC1496", 0.8, 0.15, "right")
    t.result = "IF OUT = RF x LO (sum and difference frequencies, about 0.3 V peak per volt of RF at 0.3 V of LO); a balanced mixer, the carrier mostly cancels"
    t.notes = ["Gilbert cell on +-5 V: signal pair at ground (51 ohm), carrier pair at 2.5 V (51 ohm to the 10 k / 10 k bias), 1 mA",
               "per side (3.9 k), 1.5 k loads.  Keep RF under 0.3 V and LO near 0.3 V peak (above that the carrier pair just switches,",
               "which is fine for a product detector).  IF OUT is single-ended from pin 6 through 100 n: a 1.5 k source, so read it",
               "with a high-impedance input, not 50 ohm.  No carrier-null trimmer: expect -40 dB of LO feedthrough."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


def tiles():
    return [tile_a2(), tile_a3(), tile_a4(), tile_a5(), tile_a6(), tile_a7(), tile_a8(), tile_a9(), tile_a11(), tile_a1()]


GND_LOOPS = [(3.0, 30.0), (3.0, 70.0), (97.0, 60.0), (97.0, 80.0)]
SLOTS = []
# the rails on L3: +5 V under the whole board; -5 V in the gutter under row 0 (and a strip down the left margin to the
# gutter under row 2, for A9); +3.3 V in the gutter under row 1.  Each tile reaches its rail with a via in the gutter.
RAIL_POURS = [("+5V", 0.6, 0.6, 99.4, 99.4, 0),
              # -5 V, one polygon: the gutter under row 0 (into the right margin as far as A1's red LED, no further, so the
              # +5 V pour keeps its path down that margin), a strip down the left margin, the gutter under row 2 for A9
              ("-5V", [(1.0, 27.75), (93.6, 27.75), (93.6, 29.25), (6.5, 29.25), (6.5, 70.75), (51.0, 70.75), (51.0, 72.25), (1.0, 72.25)], 1),
              ("+3V3", 7.0, 49.25, 93.0, 50.75, 1)]
# the Pmod lines on the back, board mm: from a tile's via to the via A11 declares by the plug; A11's own two run inside
# its tile.  Down the back of A9 and A11 at x 21.8 ... 24.3 (left of A9's LO jack and A11's RX socket), kept free there.
BACK_WIRES = [("/PMOD1", [(14.25, 39.75), (14.25, 48.9), (21.8, 48.9), (21.8, 92.45)]),
              ("/PMOD2", [(25.85, 45.75), (25.85, 48.3), (22.5, 48.3), (22.5, 93.1)]),
              ("/PMOD3", [(67.012, 40.85), (70.05, 40.85), (70.05, 50.0), (49.7, 50.0), (49.7, 98.75), (24.3, 98.75)])]
BACK_TEXT_X = 71.0                # right of the QR code's captions
QR_AT = (39.5, 87.3)              # under A11's right cell: the op amp's lower half has no holes
BACK_TEXT = ["AMOD-A: active blocks on USB-C power.  Each tile",
             "has a slide switch (up: on) and SMA jacks: cable",
             "DAC OUT to IN, OUT to ADC IN.  The Pmod plug (left)",
             "takes the FPGA's lines; the handbook has the rest."]


if __name__ == "__main__":
    ts = tiles()
    cells = [c for t in ts for c in t.cells]
    assert len(set(cells)) == len(cells), cells
    jacks = [(t.id + " " + j["label"], *t.to_board((j["x"], j["y"]))) for t in ts for j in t.jacks]
    bad = G.check_spacing(jacks)
    print("%d tiles, %d cells, %d jacks, %d parts; jack pairs closer than %.1f mm: %s" % (len(ts), len(cells), len(jacks), sum(len(t.parts) for t in ts), G.MIN_JACK_SPACING, bad or "none"))
    for t in ts:
        print("  %-4s %-14s %2d parts  %s" % (t.id, t.name, len(t.parts), t.result[:90]))
