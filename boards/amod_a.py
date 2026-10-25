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
def opa_tile(t, rg_key, rg_label, chip="OPA810", rf_key="R0805 10k", jack_in=True, dx=0.0, vs_feed=True, neg_via=None, neg_route=None):
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
    if jack_in:
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
    if neg_route:                                              # the front path from Cn to the via's column
        t.wire("-5V", [(cn, "1")] + list(neg_route), silk=False)
        t.via("-5V", nx, ny)
        t.wire("-5V", [neg_route[-1], (nx, ny)], layer="B.Cu", silk=False)
    else:
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


def opa_tile_br(t, rg_key, rg_label, chip="OPA810", rf_key="R0603 10k", jack_in=True, dx=0.0, neg="bottom", in_from=None, legend=True, loop=True):
    """The non-inverting gain tile with OUT at the bottom-right jack (rev A after Prompt 12: the jacks in a checkerboard).
    Everything is 0603 and sits in the two quarters the jacks and the power header leave.  The op amp (SOT-23-5 at rot
    270: +IN, V-, OUT along the top, -IN and V+ along the bottom) stands in the top-right quarter at (12.2, 6.9); the IN
    line runs from the jack's pin straight along y 4.75 into +IN, the 49.9 ohm termination hanging from it at x 9.5.
    OUT_A leaves along y 5.76 to a column at x 14.1 that feeds Rf (lying under the op amp, its other end on the
    feedback node with -IN and Rg) and Ro (standing at x 15.25), whose far end drops straight into the OUT jack's pin
    between its top legs, the loop beside it.  -5 V: V- up to a via, Cn on the left of it, on the back to the gutter
    (`neg` = "bottom" for rows 0 and 2, "top" for rows 1 and 3).  VS: the FET's drain to a via, up the back at x 10.2
    to a via under V+; Cp sits between the switch and the jacks on a via in that column.  The number, the sections
    and the name share the top band."""
    idx = t.idx
    X = lambda x: x + dx
    if jack_in:
        rt = t.add("R", "R0603 49.9R", "49.9", X(9.5), 6.4, 270, {"1": "IN", "2": "GND"}, label=None)          # pad 1 up, on the line
        t.wire("IN", [("J%d01" % idx, "1"), (X(11.25), 4.75)])
        t.wire("IN", [(X(9.5), 4.75), (rt, "1")])
        t.gnd_stub(rt, "2", (X(9.5), 8.35), sym=(0, 0))
    elif in_from:
        t.wire("IN", list(in_from) + [(X(11.25), 4.75)])
    pins = {"1": "OUT_A", "2": "-5V", "3": "IN", "4": "FB", "5": "VS"}
    if chip == "OPA847":                                       # SOT-23-6: +VS on pin 6 (where the OPA810 has V+), DIS on pin 5 to +VS
        pins["6"] = "VS"
    u = t.add("U", chip, chip, X(12.2), 6.9, 270, pins, hide_value=False, label=None)
    t.wire("IN", [(X(11.25), 4.75), (u, "3")])
    # -5 V: up from V- to a via, along the back at y 4.1 to the right edge (and on to the gutter strip), Cn standing at the
    # right edge above the loop on a via in that track
    t.via("-5V", X(12.2), 4.1)
    t.wire("-5V", [(u, "2"), (X(12.2), 4.1)])
    t.via("-5V", X(18.6), 4.1)
    if neg == "top":
        t.via("-5V", X(12.2), -0.75)
        t.wire("-5V", [(X(12.2), 4.1), (X(12.2), -0.75)], layer="B.Cu", silk=False)
        t.wire("-5V", [(X(12.2), 4.1), (X(18.6), 4.1)], layer="B.Cu", silk=False)
    else:
        t.via("-5V", X(19.45), 20.5)
        t.wire("-5V", [(X(12.2), 4.1), (X(19.45), 4.1), (X(19.45), 20.5)], layer="B.Cu", silk=False)
    cn = t.add("C", "C0603 100nF", "100n", X(17.5), 5.6, 0, {"1": "GND", "2": "-5V"}, label=None)
    t.wire("-5V", [(cn, "2"), (X(18.6), 5.6), (X(18.6), 4.1)])
    t.gnd_stub(cn, "1", [(X(16.725), 4.9), (X(16.0), 4.9)], sym=(0, 0))
    # the output: the column at x 14.1 into Rf's right end and along to Ro's top
    rf = t.add("R", rf_key, rf_key.split(" ", 1)[1], X(12.6), 10.5, 0, {"1": "FB", "2": "OUT_A"}, label=None)
    ro = t.add("R", "R0603 49.9R", "49.9", X(15.25), 7.6, 270, {"1": "OUT_A", "2": "OUT"}, label=None)      # pad 1 up
    t.wire("OUT_A", [(u, "1"), (X(13.15), 5.76), (X(14.1), 5.76), (X(14.1), 10.5), (rf, "2")])
    t.wire("OUT_A", [(X(14.1), 5.76), (X(15.25), 5.76), (ro, "1")])
    out_jack = [j["ref"] for j in t.jacks if j["slot"] in ("BR", "BR0", "BR1")][0]
    t.wire("OUT", [(ro, "2"), (out_jack, "1")])
    if loop:
        tp = t.loop("OUT", X(17.45), 9.2, 90, "OUT", label_at="hide")
        t.wire("OUT", [(X(15.25), 9.6), (X(16.35), 9.6)])
        t.wire("OUT", [(X(16.35), 9.6), (tp, "1")])
    # feedback: Rf's left end to -IN above it and Rg beside it
    rg = t.add("R", rg_key, rg_label, X(10.3), 10.6, 270, {"1": "FB", "2": "GND"}, label=None)              # pad 1 up
    t.wire("FB", [(rf, "1"), (X(11.25), 10.5), (u, "4")])
    t.wire("FB", [(X(11.25), 10.5), (X(10.3), 10.5), (rg, "1")])
    t.gnd_stub(rg, "2", [(X(10.3), 11.9), (X(9.3), 11.9)], sym=(0, 0))
    # VS: the drain to a via, up the back at x 10.2, a via under V+; Cp on a via in the column
    t.wire("VS", [HDR_VS, (X(10.2), 18.1)] if dx == 0 else [(X(10.2), 18.1)], silk=bool(dx == 0))
    t.via("VS", X(13.15), 9.36)
    t.wire("VS", [(X(10.2), 18.1), (X(10.2), 9.36), (X(13.15), 9.36)], layer="B.Cu", silk=False)
    if chip == "OPA847":
        t.wire("VS", [(X(13.15), 9.36), (u, "6"), (u, "5")])
    else:
        t.wire("VS", [(X(13.15), 9.36), (u, "5")])
    cp = t.add("C", "C0603 100nF", "100n", X(8.0), 13.6, 0, {"1": "GND", "2": "VS"}, label=None)
    t.via("VS", X(10.2), 13.6)
    t.wire("VS", [(cp, "2"), (X(10.2), 13.6)])
    t.gnd_stub(cp, "1", (X(6.4), 13.6), sym=(0, 0))
    if legend:
        t.text(X(9.6), 2.0, t.id, 1.2, 0.24, "center")
        t.text(X(19.0), 1.65, " ".join(t.sections), 0.8, 0.15, "right")
        t.text(X(19.0), 3.0, (t.name + ((" " + t.subtitle) if t.subtitle else "")).upper(), 0.8, 0.15, "right")
    return u


def tile_a2():
    """Gain x10: an OPA810 (140 MHz GBW) non-inverting, 1.1 k and 10 k, 50 ohm in, 49.9 ohm out (x10 into a high impedance,
    x5 into 50 ohm); 14 MHz."""
    t = Tile("A2", "x10", [(0, 0)], supply="+-5 V", subtitle="14 MHz", sections=["4.06", "5.02"])
    t.jack("TL", "IN", "IN", "in", "±0.4 V", silk="IN 50R"); t.jack("BR", "OUT", "OUT", "out", "")
    power_header(t)
    opa_tile_br(t, "R0603 1.1k", "1.1k")
    t.result = "x10 (20 dB) into a high impedance, x5 into 50 ohm, -3 dB near 14 MHz; clips at about +-4 V"
    t.notes = ["Non-inverting OPA810: gain 1 + 10 k / 1.1 k = 10.1, bandwidth 140 MHz / 10 = 14 MHz.  50 ohm at the input, 49.9 ohm",
               "in series with the output (a 50 ohm load halves it: x5).  Keep the input under 0.4 V peak: the output clips at 4 V."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


def tile_a3():
    """Gain x100 in one OPA810 stage (100 ohm and 10 k): 1.4 MHz, x100 into a high impedance.  The plan's two stages of
    x10 (9 MHz) did not fit a 20 mm cell beside the switch with 0.2 mm clearances; A4 covers the HF case at x100."""
    t = Tile("A3", "x100", [(1, 0)], supply="+-5 V", subtitle="1.4MHz", sections=["4.06", "5.02"])
    t.jack("TL", "IN", "IN", "in", "±40 mV", silk="IN 50R"); t.jack("BR", "OUT", "OUT", "out", "")
    power_header(t)
    opa_tile_br(t, "R0603 100R", "100R")
    t.result = "x100 (40 dB) into a high impedance, -3 dB near 1.4 MHz; keep the input under 40 mV peak"
    t.notes = ["Non-inverting OPA810: gain 1 + 10 k / 100 = 101, bandwidth 140 MHz / 100 = 1.4 MHz.  50 ohm at the input, 49.9 ohm",
               "in series with the output.  For 40 dB out to 30 MHz use A4 (the OPA847 LNA); this tile is the FET-input, high-impedance",
               "friendly x100 for everything slower.  (The plan's two stages of x10 did not fit the cell.)"]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ A4 --
def tile_a4():
    """HF LNA: the OPA847 (SOT-23-6) at x101 (1 k / 10 ohm) in the shared checkerboard geometry (opa_tile_br), 50 ohm at
    the input, 49.9 ohm out.  DIS (pin 5) is tied to +VS beside it: enabled.  The feedback pair sits right at the pins,
    as a decompensated amplifier needs."""
    t = Tile("A4", "LNA", [(2, 0)], supply="+-5 V", subtitle="30 MHz", sections=["4.06", "5.03"])
    t.jack("TL", "IN", "IN", "in", "±30 mV", silk="IN 50R"); t.jack("BR", "OUT", "OUT", "out", "")
    power_header(t)
    opa_tile_br(t, "R0603 10R", "10R", chip="OPA847", rf_key="R0603 1k")
    t.result = "x100 (40 dB) from 50 ohm, flat 1-30 MHz, about 3 dB noise figure from 50 ohm; keep the input under 30 mV peak"
    t.notes = ["Non-inverting OPA847 (3.9 GHz GBW at this gain, 0.85 nV/rtHz): 1 k / 10 ohm, so x101 and about 39 MHz.  Its",
               "input noise with the 50 ohm termination's own noise gives a noise figure near 3 dB.  The op amp is stable only at",
               "gains above 12 (it is decompensated): do not change Rg upward.  SOT-23-6, DIS tied to +VS (enabled)."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ A5 --
def tile_a5():
    """10.525 GHz Doppler radar: an HB100 module on three jumper wires to a 1 x 3 header (+5 V from the tile's switch, IF,
    ground), its IF through 1 uF (100 k to ground) into the A2 geometry at x101 (100 ohm / 10 k), 49.9 ohm out.  1 m/s
    toward the module is 70 Hz; walking, a fan's blades, a speaker cone and breathing are all within reach.  (Rev A's
    first A5 was a Johnson-noise amplifier: the ECP5-2ADC-2DAC board has that source and a x100 input of its own.)"""
    t = Tile("A5", "Doppler", [(3, 0)], supply="+-5 V", subtitle="HB100", sections=["5.08"])
    t.jack("BR", "OUT", "OUT", "out", "")
    power_header(t)
    hb = t.add("J", "HDR3", "HB100", 3.0, 2.2, 0, {"1": "VS", "2": "IF", "3": "GND"}, hide_value=True)      # pins at y 2.2, 4.74, 7.28
    cin = t.add("C", "C0805 1uF", "1u", 6.7, 4.74, 0, {"1": "IF", "2": "IN"}, label=None)
    rb = t.add("R", "R0402 100k", "100k", 9.3, 6.4, 270, {"1": "IN", "2": "GND"}, label=None)                  # pad 1 up
    t.wire("IF", [(hb, "2"), (cin, "1")])
    t.wire("IN", [(9.3, 4.75), (rb, "1")])
    t.gnd_stub(rb, "2", (9.3, 7.9), sym=(0, 0))
    t.gnd_stub(hb, "3", (4.0, 8.4), sym=(0, 0))
    opa_tile_br(t, "R0603 100R", "100R", jack_in=False, in_from=[(cin, "2")], legend=False)
    # the module's 5 V: from the op amp's VS via on the back, along y 12.8 and up the left edge to a via beside pin 1
    t.via("VS", 1.4, 2.2)
    t.wire("VS", [(10.2, 13.6), (10.2, 12.8), (1.4, 12.8), (1.4, 2.2)], layer="B.Cu", silk=False)
    t.wire("VS", [(1.4, 2.2), (hb, "1")])
    t.text(4.5, 2.2, "+5", 0.8, 0.15, "left")
    t.text(4.5, 7.28, "G", 0.8, 0.15, "left")
    t.text(7.6, 1.8, "A5", 1.2, 0.24, "center")
    t.text(7.6, 3.15, "5.08", 0.8, 0.15, "center")
    t.text(19.0, 1.65, "DOPPLER 10.5G", 0.8, 0.15, "right")
    t.text(19.0, 3.0, "HB100", 0.8, 0.15, "right")
    t.result = "the Doppler beat of a target moving toward or away: 70 Hz per m/s (19.4 Hz per km/h), tens of mV after x101"
    t.notes = ["HB100: a 10.525 GHz oscillator and mixer on one board; its IF is the beat between what it sends and what comes",
               "back, 2v/lambda = 70 Hz per m/s.  Wire its +5, IF and GND pins to the header; point it at something that moves.",
               "The host's x10 input after this tile's x101 brings a hand at 1 m to the ADC's range."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ A6 --
def tile_a6():
    """Delta-sigma: a TLV3501 compares the integrator node (IN through 10 k, the FPGA's bit back through 10 k, 10 nF to
    ground) with a mid-rail reference (10 k / 10 k / 100 n from VS); its bit goes to Pmod IO7 and a loop; the FPGA's
    bit comes in on Pmod IO8.  +3.3 V so the bit is the FPGA's logic level."""
    t = Tile("A6", "1-bit ADC", [(0, 1)], supply="+3.3 V", sections=["7.05"])
    idx = t.idx
    t.jack("TL", "IN", "IN", "in", "±1.5 V", silk="IN 10K")
    power_header(t, rail="+3V3")
    rin = t.add("R", "R0805 10k", "10k", 6.6, 9.3, 0, {"1": "IN", "2": "NODE"}, label=None)
    t.wire("IN", [("J%d01" % idx, "1"), (4.75, 9.3), (rin, "1")])
    rfb = t.add("R", "R0603 10k", "10k", 6.5, 12.6, 270, {"1": "/PMOD8", "2": "NODE"}, label=None)       # pad 1 up
    cint = t.add("C", "C0805 10nF", "10n", 8.3, 15.3, 0, {"1": "NODE", "2": "GND"}, label=None)
    u = t.add("U", "TLV3501", "TLV3501", 10.5, 12.5, 0, {"1": "VREF", "2": "GND", "3": "NODE", "4": "VS", "5": "/PMOD7", "6": "GND"},
              hide_value=False, label=None)
    t.wire("NODE", [(rin, "2"), (7.4, 9.3), (7.4, 15.3), (cint, "1")])
    t.wire("NODE", [(7.4, 13.45), (u, "3")])
    t.wire("NODE", [(rfb, "2"), (7.4, 13.375)])
    t.wire("/PMOD8", [(rfb, "1"), (6.5, 10.5)])
    t.via("/PMOD8", 6.5, 10.5)
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
    tp = t.loop("/PMOD7", 18.1, 12.9, 90, "BIT", label_at=(0.8, 2.9, "right", 0.8))
    t.wire("/PMOD7", [(u, "5"), (12.8, 12.5), (12.8, 10.1), (18.1, 10.1), (tp, "1")])
    t.wire("/PMOD7", [(tp, "1"), (18.1, 16.5)], silk=False)
    t.via("/PMOD7", 18.1, 16.5)
    t.legend()
    t.result = "a one-bit stream on Pmod IO7 whose density follows IN; the FPGA closes the loop through Pmod IO8 (the handbook's gateware)"
    t.notes = ["First-order delta-sigma: the comparator decides, the FPGA registers the bit and feeds it back through 10 k into the",
               "10 k / 10 nF integrator (1.6 kHz; clock the loop at 1-10 MHz).  IN takes 0 to 3.3 V, or +-1.5 V about the 1.65 V reference",
               "if you AC-couple.  Both Pmod lines are 3.3 V logic; the tile runs on the 3.3 V rail."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ A8 --
def tile_a8():
    """Heater and thermometer: two 15 ohm 2512 in series across VS (0.83 W at 5 V), stacked in the top-left, switched
    by an AO3400 beside them from Pmod IO6 (10 k pull-down); a TMP235 (10 mV/K + 500 mV) straight above the OUT jack,
    its output dropping into the jack's pin.  (The plan's NTC divider did not fit beside the two 2512s.)"""
    t = Tile("A8", "heat", [(2, 1)], supply="+5 V", sections=["5.02", "7.06"])
    idx = t.idx
    t.jack("BR", "OUT", "OUT", "out", "", silk="TEMP OUT")
    power_header(t)
    ra = t.add("R", "R2512_15R", "15R", 6.0, 2.75, 0, {"1": "HTR", "2": "VS"}, label=None)
    rb = t.add("R", "R2512_15R", "15R", 6.0, 6.75, 0, {"1": "HTR", "2": "DRN"}, label=None)
    q = t.add("Q", "NFET", "AO3400A", 12.3, 5.45, 0, {"1": "/PMOD6", "2": "GND", "3": "DRN"}, hide_value=True)
    rpd = t.add("R", "R0603 10k", "10k", 13.2, 2.4, 0, {"1": "/PMOD6", "2": "GND"}, label=None)
    t.wire("HTR", [(ra, "1"), (rb, "1")])
    t.wire("DRN", [(rb, "2"), (8.962, 5.45), (q, "3")])                          # between the FET's gate and source pads
    t.gnd_stub(q, "2", (11.362, 7.55), sym=(0, 0))
    t.wire("/PMOD6", [(q, "1"), (11.362, 2.4), (rpd, "1")])
    t.wire("/PMOD6", [(11.362, 2.4), (11.362, 1.4)])
    t.via("/PMOD6", 11.362, 1.4)                                                  # BACK_WIRES takes it to the plug
    t.gnd_stub(rpd, "2", (15.3, 2.4), sym=(0, 0))
    tmp = t.add("U", "TMP235", "TMP235", 14.3, 9.25, 90, {"1": "VS", "2": "OUT", "3": "GND"}, hide_value=False, label=None)
    cd = t.add("C", "C0603 100nF", "100n", 11.6, 9.4, 90, {"1": "VS", "2": "GND"}, label=None)        # pad 1 down
    t.wire("OUT", [(tmp, "2"), ("J%d01" % idx, "1")])
    t.gnd_stub(tmp, "3", (15.9, 8.3), sym=(0, 0))
    t.gnd_stub(cd, "2", (12.9, 8.6), sym=(0, 0))
    # VS: up the middle on the front to the TMP235 and its capacitor, on under the DRN line on the back to the top heater
    t.wire("VS", [HDR_VS, (8.54, 18.5), (10.2, 18.5), (10.2, 11.0), (13.35, 11.0), (tmp, "1")])
    t.wire("VS", [(cd, "1"), (11.6, 11.0)])
    t.via("VS", 10.2, 11.0)
    t.via("VS", 10.2, 3.6)
    t.wire("VS", [(10.2, 11.0), (10.2, 3.6)], layer="B.Cu", silk=False)
    t.wire("VS", [(10.2, 3.6), (10.2, 2.75), (ra, "2")])
    t.text(7.8, 10.9, "A8", 1.5, 0.3, "center")
    t.text(7.8, 12.9, "5.02", 0.8, 0.15, "center")
    t.text(7.8, 14.25, "7.06", 0.8, 0.15, "center")
    t.text(19.0, 4.5, "HEAT", 0.8, 0.15, "right")
    t.text(19.0, 5.85, "0.8 W", 0.8, 0.15, "right")
    t.result = "0.83 W into the board when Pmod IO6 is high (the FET's drain), 10 mV/K + 500 mV on OUT"
    t.notes = ["Two 15 ohm in series: 30 ohm, 170 mA, 0.83 W from the switched 5 V when Pmod IO6 is high (10 k keeps it off otherwise).",
               "The TMP235 reads 750 mV at 25 C and climbs 10 mV per kelvin.  A feedback-control experiment: hold the TMP235 at a",
               "set point with the FPGA's PWM.  (The plan's NTC divider did not fit the cell beside the two 2512s.)"]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ----------------------------------------------------------------------------------------------------------- A11 --
def tile_a11():
    """40 kHz ultrasound, two cells.  Left: the DRV8837 H-bridge (IN1, IN2 from Pmod IO4 and IO3) drives a transducer in
    pins 1 and 5 of a 1 x 5 socket along the top edge; the Pmod plug hangs off the bottom edge below this cell, and
    the board's Pmod lines come down the back of this cell's right third to it.  Right: the second transducer in its
    socket, 10 nF into the A2 geometry at x100 (100 ohm / 10 k, 3.9 k to ground at +IN) and out to RX OUT at the
    right cell's bottom-right jack.
    +-5 V (the op amp), the bridge on the switched +5 V."""
    t = Tile("A11", "ultrasound", [(0, 3), (1, 3)], supply="+-5 V", sections=["4.06"])
    t.jack("BR1", "OUT", "OUT", "out", "", silk="RX OUT")
    power_header(t)
    # --- transmit: the bridge beside the socket's left end
    jtx = t.add("J", "HDR5", "TX", 2.4, 2.6, 90, {"1": "OUT1", "5": "OUT2"}, hide_value=True)             # pins at x 2.4 ... 12.56
    d = t.add("U", "DRV8837", "DRV8837", 8.0, 8.5, 0, {"1": "VS", "2": "OUT1", "3": "OUT2", "4": "GND", "5": "/PMOD4", "6": "/PMOD3",
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
    t.wire("/PMOD3", [(d, "6"), (10.3, 8.75), (10.3, 8.3), (10.6, 8.3)], width=W)
    t.via("/PMOD3", 10.6, 8.3)
    t.wire("/PMOD4", [(d, "5"), (11.6, 9.25)], width=W)
    t.via("/PMOD4", 11.6, 9.25)
    t.text(17.5, 6.0, "A11", 0.9, 0.17, "center")
    t.text(17.5, 7.4, "4.06", 0.8, 0.15, "center")
    # --- receive: the socket in the right cell's top-left, 10 nF and 3.9 k into the A2 geometry
    jrx = t.add("J", "HDR5", "RX", 21.2, 2.6, 90, {"1": "RXA", "5": "GND"}, hide_value=True)             # pins at x 21.2 ... 31.36
    cin = t.add("C", "C0805 10nF", "10n", 26.0, 9.3, 0, {"1": "RXA", "2": "IN"}, label=None)
    r1 = t.add("R", "R0805 3.9k", "3.9k", 23.0, 11.8, 270, {"1": "IN", "2": "GND"}, label=None)        # pad 1 up
    t.wire("RXA", [(jrx, "1"), (21.2, 9.3), (cin, "1")])
    t.wire("IN", [(cin, "2"), (26.95, 10.888), (r1, "1")])
    t.gnd_stub(r1, "2", (23.0, 14.1), sym=(0, 0))
    t.wire("VS", [HDR_VS, (8.54, 18.5), (31.7, 18.5), (31.7, 18.1)], silk=False)                       # to the helper's back column
    u = opa_tile_br(t, "R0603 100R", "100R", jack_in=False, dx=21.5, neg="top", legend=False,
                    in_from=[(cin, "2"), (28.0, 9.3), (28.0, 4.75)])                                    # under the socket's right end
    t.text(21.6, 16.5, "ULTRASOUND", 0.8, 0.15, "left")
    # --- the Pmod plug, below the left cell in the bottom margin (global 15.4, 96.5), and the board's lines to it:
    # the upper row (even pads) straight down from feeds on the back; the lower row (odd pads) through the upper row's
    # gaps on the front with 0.2 mm tracks (pads 1, 3) or along the bottom edge (pads 5, 7)
    # the plug two columns left of where the feeds were first laid, so they meet pads 5-11 (the IO columns) and ground and
    # 3.3 V sit on pads 1-4 at the left: JLCPCB's numbering of this part runs the other way from KiCad's (see pmod_plug)
    pm = t.add("J", "PMOD", "Pmod", 2.97, 24.25, 0, {"5": "/PMOD8", "7": "/PMOD7", "9": "/PMOD6", "6": "/PMOD4", "8": "/PMOD3",
                                                      "10": "/PMOD2", "3": "GND", "4": "GND", "1": "/PMOD_VCC", "2": "/PMOD_VCC"}, hide_value=True)
    t.wire("/PMOD_VCC", [(pm, "1"), (pm, "2")], silk=False)
    t.wire("/PMOD4", [(11.6, 9.25), (11.6, 20.1), (1.7, 20.1), (pm, "6")], layer="B.Cu", silk=False)
    t.wire("/PMOD3", [(10.6, 8.3), (12.3, 8.3), (12.3, 20.75), (4.24, 20.75), (pm, "8")], layer="B.Cu", silk=False)
    t.via("/PMOD8", 14.05, 20.2)
    t.wire("/PMOD8", [(14.05, 20.2), (2.97, 20.2), (2.97, 24.75), (pm, "5")], width=0.2, silk=False)
    t.via("/PMOD7", 14.75, 20.85)
    t.wire("/PMOD7", [(14.75, 20.85), (5.51, 20.85), (5.51, 24.75), (pm, "7")], width=0.2, silk=False)
    t.via("/PMOD6", 16.55, 25.75)
    t.wire("/PMOD6", [(16.55, 25.75), (16.55, 27.15), (6.78, 27.15), (pm, "9")], width=0.2, silk=False)
    t.via("/PMOD2", 44.25, 21.5)                                                                          # board (52.0, 93.75)
    t.wire("/PMOD2", [(44.25, 21.5), (6.78, 21.5), (pm, "10")], width=0.2, silk=False)
    t.result = "a 40 kHz burst from Pmod IO4/IO3 leaves the TX transducer; its echo arrives x100 on RX OUT (hold a reflector over the board)"
    t.notes = ["Drive IN1/IN2 (Pmod IO4, IO3) in antiphase at 40 kHz for 8-20 cycles: the bridge puts 10 V peak to peak across the TX",
               "transducer.  The RX transducer's 10 nF / 3.9 k high-pass (4 kHz) feeds an OPA810 at x100 (1.4 MHz: the transducer's",
               "own resonance sets the band).  Time of flight at 343 m/s: 5.8 us per mm there and back.  Put the two transducers",
               "in pins 1 and 5 (10.16 mm; their leads are 10 mm apart)."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ A7 --
def tile_a7():
    """PLL: a 74HC4046A in TSSOP-16 (rot 180: VCOin, DEMout, R1, R2, PC2, SIGin, PC3, VCC down the left column; GND,
    C1B, C1A, INH, VCOout, COMPin, PC1, PCP down the right) in the top-right quarter, between the diagonal jacks.  IN
    through 100 n and 1 k (below the IN jack) into SIGin (self-biased); the VCO (R1 10 k, C1 1 nF: about 100 kHz) out
    through 470 ohm (in the right strip, beside C1) to the OUT jack and back into COMPin; PC2's tri-state output up
    through the chip's middle to the 10 k / 100 n lag filter above it, into VCOin.  No loops: probe pin 9 (VCOin,
    the demodulated FM) and pin 13."""
    t = Tile("A7", "PLL 4046", [(1, 1)], supply="+5 V", sections=["4.01"])
    idx = t.idx
    t.jack("TL", "IN", "IN", "in", "±1 V", silk="IN 1K"); t.jack("BR", "OUT", "OUT", "out", "", silk="VCO OUT")
    power_header(t)
    # left column x 10.738: 9 VCOin 4.725, 10 DEM 5.375, 11 R1 6.025, 12 R2 6.675, 13 PC2 7.325, 14 SIG 7.975, 15 PC3 8.625, 16 VCC 9.275
    # right column x 16.462: 8 GND 4.725, 7 C1B 5.375, 6 C1A 6.025, 5 INH 6.675, 4 VCOout 7.325, 3 COMP 7.975, 2 PC1 8.625, 1 PCP 9.275
    u = t.add("U", "HC4046", "74HC4046A", 13.6, 7.0, 180, {"3": "VCO_A", "4": "VCO_A", "5": "GND", "6": "C1A", "7": "C1B", "8": "GND",
                                                       "9": "NODE", "11": "R1", "13": "PC2", "14": "SIG", "16": "VS"}, hide_value=False, label=None)
    cs = t.add("C", "C0402 100nF", "100n", 5.95, 9.6, 0, {"1": "IN", "2": "INA"}, label=None)
    rs = t.add("R", "R0402 1k", "1k", 8.05, 9.6, 0, {"1": "INA", "2": "SIG"}, label=None)
    cf = t.add("C", "C0402 100nF", "100n", 9.4, 2.4, 0, {"1": "GND", "2": "NODE"}, label=None)
    rf = t.add("R", "R0402 10k", "10k", 11.4, 2.4, 0, {"1": "NODE", "2": "PC2"}, label=None)
    r1 = t.add("R", "R0402 10k", "10k", 9.15, 5.515, 90, {"1": "R1", "2": "GND"}, label=None)          # pad 1 down
    c1 = t.add("C", "C0402 1nF", "1n", 18.3, 5.7, 270, {"1": "C1B", "2": "C1A"}, label=None)         # pad 1 up
    ro = t.add("R", "R0402 470R", "470", 18.3, 7.95, 270, {"1": "VCO_A", "2": "OUT"}, label=None)
    cp = t.add("C", "C0402 100nF", "100n", 11.0, 10.6, 0, {"1": "VS", "2": "GND"}, label=None)
    t.wire("IN", [("J%d01" % idx, "1"), (4.75, 9.6), (cs, "1")])
    t.wire("INA", [(cs, "2"), (rs, "1")])
    t.wire("SIG", [(rs, "2"), (9.5, 9.6), (9.5, 7.975), (u, "14")])
    t.wire("PC2", [(u, "13"), (11.91, 7.325), (rf, "2")])
    t.wire("NODE", [(u, "9"), (10.738, 2.4), (rf, "1")])
    t.wire("NODE", [(cf, "2"), (rf, "1")])
    t.gnd_stub(cf, "1", (8.92, 1.45), sym=(0, 0))
    t.wire("R1", [(u, "11"), (9.15, 6.025), (r1, "1")])
    t.gnd_stub(r1, "2", (9.15, 4.0), sym=(0, 0))
    t.wire("C1B", [(u, "7"), (18.3, 5.375), (c1, "1")])
    t.wire("C1A", [(u, "6"), (18.3, 6.025), (c1, "2")])
    t.wire("VCO_A", [(u, "4"), (u, "3")])
    t.wire("VCO_A", [(u, "4"), (18.3, 7.325), (ro, "1")])
    t.wire("OUT", [(ro, "2"), (18.3, 10.6), (15.25, 10.6), ("J%d02" % idx, "1")])
    t.wire("GND", [(u, "8"), (15.3, 4.725), (15.3, 6.675), (u, "5")])
    t.gnd_stub(u, "5", [(15.3, 6.675), (15.3, 5.7), (13.6, 5.7)], sym=(0, 0))
    t.wire("VS", [HDR_VS, (8.54, 18.5), (10.2, 18.5), (10.2, 10.6), (cp, "1")])
    t.wire("VS", [(cp, "1"), (10.738, 10.6), (u, "16")])
    t.gnd_stub(cp, "2", (12.3, 10.4), sym=(0, 0))
    t.text(7.6, 12.4, "A7", 1.2, 0.24, "center")
    t.text(7.6, 14.0, "4.01", 0.8, 0.15, "center")
    t.text(19.0, 3.0, "PLL 4046", 0.8, 0.15, "right")
    t.result = "VCO OUT locks to a 50-200 kHz square or sine on IN; pin 9 is the demodulated FM, pin 13 the phase detector"
    t.notes = ["74HC4046A: R1 10 k, C1 1 nF put the VCO near 100 kHz (R2 open: it can go down to 0).  PC2 (the edge-triggered",
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
    t.jack("BR1", "IF", "IF", "out", "", silk="IF OUT")
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
    co = t.add("C", "C0603 100nF", "100n", 27.4, 15.25, 0, {"1": "OUTA", "2": "IF"}, label=None)
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
    # outputs: OUT+ through the NC pin 7 to the right, to the capacitor and along y 15.25 into the jack between its legs
    t.wire("OUTA", [(u, "6"), (rl1, "1")])
    t.wire("OUTA", [(u, "6"), (u, "7"), (25.3, 14.575), (25.3, 15.25), (co, "1")])
    t.wire("IF", [(co, "2"), ("J%d03" % idx, "1")])
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
    t.wire("VS", [HDR_VS, (8.54, 18.95), (32.4, 18.95)], silk=False)
    t.wire("VS", [(rl1, "2"), (23.29, 18.95)])
    t.wire("VS", [(cp, "1"), (25.225, 18.95)])
    t.wire("VS", [(rl2, "2"), (11.8, 13.412), (11.8, 13.9)])
    t.wire("VS", [(11.8, 13.9), (11.8, 18.4)], layer="B.Cu", silk=False)
    t.wire("VS", [(11.8, 18.4), (11.8, 18.95)])
    t.wire("VS", [(32.4, 18.95), (32.4, 8.4)], layer="B.Cu", silk=False)          # left of the IF jack's legs
    t.wire("VS", [(32.4, 8.4), (rb1, "1")])
    t.text(12.75, 2.4, "A9", 1.5, 0.3, "center")
    t.text(12.75, 4.4, "1.10", 0.8, 0.15, "center")
    t.text(12.75, 5.75, "6.02", 0.8, 0.15, "center")
    t.text(t.w - 1.1, 2.2, "MIXER MC1496", 0.8, 0.15, "right")
    t.result = "IF OUT = RF x LO (sum and difference frequencies, about 0.3 V peak per volt of RF at 0.3 V of LO); a balanced mixer, the carrier mostly cancels"
    t.notes = ["Gilbert cell on +-5 V: signal pair at ground (51 ohm), carrier pair at 2.5 V (51 ohm to the 10 k / 10 k bias), 1 mA",
               "per side (3.9 k), 1.5 k loads.  Keep RF under 0.3 V and LO near 0.3 V peak (above that the carrier pair just switches,",
               "which is fine for a product detector).  IF OUT is single-ended from pin 6 through 100 n: a 1.5 k source, so read it",
               "with a high-impedance input, not 50 ohm.  No carrier-null trimmer: expect -40 dB of LO feedthrough."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ----------------------------------------------------------------------------------------------------------- A10 --
def tile_a10():
    """Impedance and I-V, two cells, +-5 V.  Left: DRIVE IN (50 ohm) into the A2 geometry at x2 (1 k / 1 k): the driven
    node S, which also leaves through 49.9 ohm on S OUT (the bottom-right jack).  Right: a 4-way DIP picks the reference
    resistor (47, 470, 4.7 k, 47 k) from S to X, the part under test between X and ground on the DUT jack, and an
    OPA810 follower brings X out through 49.9 ohm on X OUT.  With the host's two ADCs on S OUT and X OUT (50 ohm: each
    reads half), I = (S - X) / R and Z = R X / (S - X): an impedance analyzer from DC to a few MHz after an open-short
    calibration, and an I-V curve tracer to +-4 V and 40 mA.  (Rev A's first A10 was an LED driver and a photodiode
    amplifier: the ECP5-2ADC-2DAC board has both.)"""
    t = Tile("A10", "impedance", [(2, 2), (3, 2)], supply="+-5 V", subtitle="V and I", sections=["4.02", "4.10"])
    idx = t.idx
    t.jack("TL", "DRIVE", "IN", "in", "+-1 V into 50 ohm", silk="DRIVE IN")
    t.jack("BR0", "S", "OUT", "out", "", silk="S OUT")
    jd = t.jack("TL1", "DUT", "X", "out", "", silk="DUT")
    jx = t.jack("BR1", "X", "XO", "out", "", silk="X OUT")
    power_header(t)
    opa_tile_br(t, "R0603 1k", "1k", rf_key="R0603 1k", legend=False, loop=False)
    # S (the driver's output node) right along y 11.2 to the DIP's bus
    t.wire("OUT_A", [(14.1, 10.5), (14.1, 11.2), (14.5, 11.2)])                     # under S OUT's line on the back
    t.via("OUT_A", 14.5, 11.2)
    t.via("OUT_A", 16.0, 11.2)
    t.wire("OUT_A", [(14.5, 11.2), (16.0, 11.2)], layer="B.Cu", silk=False)
    t.wire("OUT_A", [(16.0, 11.2), (20.2, 11.2), (20.2, 16.305)])
    sw = t.add("SW", "DIP4", "DIP4", 24.8, 14.4, 270, {"1": "OUT_A", "2": "OUT_A", "3": "OUT_A", "4": "OUT_A",
                                                       "8": "R1", "7": "R2", "6": "R3", "5": "R4"}, hide_value=True)
    ys = (12.495, 13.765, 15.035, 16.305)
    for k, y in enumerate(ys):
        t.wire("OUT_A", [(20.2, y), (sw, str(k + 1))])
    for k, (key, val, y) in enumerate(zip(("R0402 47R", "R0402 470R", "R0402 4.7k", "R0402 47k"), ("47", "470", "4.7k", "47k"), ys)):
        r = t.add("R", key, val, 30.7, y, 0, {"1": "R%d" % (k + 1), "2": "X"}, label=None)
        t.wire("R%d" % (k + 1), [(sw, str(8 - k)), (r, "1")])
        t.wire("X", [(r, "2"), (32.0, y)])
    t.wire("X", [(32.0, ys[3]), (32.0, 9.5), (26.25, 9.5), (jd, "1")])
    # the follower on X, its output down into X OUT
    u2 = t.add("U", "OPA810", "OPA810", 35.4, 6.0, 0, {"1": "XF", "2": "-5V", "3": "X", "4": "XF", "5": "VS"}, hide_value=False, label=None)
    ro2 = t.add("R", "R0603 49.9R", "49.9", 37.6, 10.2, 270, {"1": "XF", "2": "XO"}, label=None)              # pad 1 up
    t.wire("X", [(32.0, 9.5), (33.2, 9.5), (33.2, 6.95), (u2, "3")])
    t.wire("XF", [(u2, "1"), (35.1, 5.05), (35.7, 6.95), (u2, "4")], width=0.2)       # under the body: a follower
    t.wire("XF", [(u2, "4"), (37.6, 6.95), (ro2, "1")])
    t.wire("XO", [(ro2, "2"), (37.6, 12.0), (36.75, 12.0), (jx, "1")])
    cp2 = t.add("C", "C0603 100nF", "100n", 39.4, 5.5, 270, {"1": "VS", "2": "GND"}, label=None)              # pad 1 up
    cn2 = t.add("C", "C0603 100nF", "100n", 32.0, 4.4, 90, {"1": "-5V", "2": "GND"}, label=None)              # pad 1 down
    t.wire("VS", [(u2, "5"), (38.5, 5.05), (38.5, 4.725), (cp2, "1")])
    t.gnd_stub(cp2, "2", (39.4, 7.2), sym=(0, 0))
    t.wire("-5V", [(u2, "2"), (32.0, 6.0), (cn2, "1")])
    t.gnd_stub(cn2, "2", (32.0, 2.3), sym=(0, 0))
    # VS along the bottom on the back from the left cell's header; -5 V from the gutter strip below
    t.wire("VS", [(10.2, 18.1), (10.2, 19.4), (40.8, 19.4), (40.8, 2.6), (39.4, 2.6), (cp2, "1")], silk=False)
    t.via("-5V", 31.0, 6.0)
    t.via("-5V", 31.0, 20.5)
    t.wire("-5V", [(32.0, 6.0), (31.0, 6.0)])
    t.wire("-5V", [(31.0, 6.0), (31.0, 20.5)], layer="B.Cu", silk=False)
    t.text(10.4, 2.0, "A10", 1.2, 0.24, "center")
    t.text(19.0, 1.65, "4.02 4.10", 0.8, 0.15, "right")
    t.text(19.0, 3.0, "IMPEDANCE", 0.8, 0.15, "right")
    t.result = "S OUT and X OUT (each half the node's voltage into 50 ohm): Z = R X / (S - X); +-4 V and up to 40 mA for an I-V curve"
    t.notes = ["DRIVE IN x2 is S.  The DIP picks R between S and X (47 ohm for LEDs and diodes, 470 for most parts, 4.7 k and 47 k for",
               "high impedances); the part goes on the DUT jack.  Calibrate with the DUT open and shorted.  An LED's knee against",
               "its colour (P12) gives Planck's constant; a crystal (P8) shows its series and parallel resonances."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ----------------------------------------------------------------------------------------------------------- A12 --
def tile_a12():
    """Audio, two cells.  Left: a PAM8302A class-D amplifier (SOIC-8, rot 270: IN-, IN+, BYP, SD along the top; VO+,
    VDD, GND, VO- along the bottom) driving a speaker on the screw terminal in the right cell's top-left; its input
    is AUDIO IN through 1 u and the one-bit stream from Pmod IO2 through 10 k into 10 n.  Right: an electret in the
    1 x 2 socket (2.2 k bias from VS), 1 u into the A2 geometry at x100 and out to MIC OUT.  +-5 V (the op amp; the
    class-D runs on the switched +5 V).  No 3.5 mm jack: the one-bit stream is heard on the speaker."""
    t = Tile("A12", "audio", [(2, 3), (3, 3)], supply="+-5 V", sections=["1.05", "6.04"])
    idx = t.idx
    t.jack("TL", "AIN", "AIN", "in", "±1 V", silk="AUDIO IN"); t.jack("BR1", "OUT", "OUT", "out", "", silk="MIC OUT")
    power_header(t)
    # --- the class-D amplifier (left cell)
    pa = t.add("U", "PAM8302", "PAM8302A", 10.3, 12.6, 270, {"1": "VS", "2": "BYP", "3": "NODE", "4": "INM", "5": "VOP", "6": "VS", "7": "GND", "8": "VOM"},
               hide_value=False, label=None)
    cin = t.add("C", "C0805 1uF", "1u", 9.665, 5.0, 270, {"1": "AIN", "2": "NODE"}, label=None)             # pad 1 up
    rdac = t.add("R", "R0603 10k", "10k", 18.0, 5.0, 0, {"1": "NODE", "2": "/PMOD2"}, label=None)
    cdac = t.add("C", "C0805 10nF", "10n", 15.2, 6.5, 270, {"1": "NODE", "2": "GND"}, label=None)          # pad 1 up
    cm = t.add("C", "C0603 1uF", "1u", 6.6, 11.5, 270, {"1": "INM", "2": "GND"}, label=None)
    cb = t.add("C", "C0603 1uF", "1u", 12.4, 8.0, 0, {"1": "BYP", "2": "GND"}, label=None)
    c100 = t.add("C", "C0603 100nF", "100n", 11.4, 17.5, 0, {"1": "VS", "2": "GND"}, label=None)
    cvdd = t.add("C", "C0805 10uF", "10u", 14.9, 17.3, 0, {"1": "VS", "2": "GND"}, label=None)
    spk = t.add("J", "TERM2", "SPK", 25.6, 6.6, 90, {"1": "VOP", "2": "VOM"}, hide_value=True)            # pads at (25.6, 9.1) and (25.6, 4.1)
    t.wire("AIN", [("J%d01" % idx, "1"), (8.6, 4.75), (8.6, 4.05), (cin, "1")])
    t.wire("NODE", [(cin, "2"), (9.665, 10.125), (pa, "3")])
    t.wire("NODE", [(9.665, 6.0), (15.2, 6.0), (17.225, 6.0), (rdac, "1")])
    t.gnd_stub(cdac, "2", (16.1, 7.45), sym=(0, 0))
    t.via("/PMOD2", 18.775, 3.9)
    t.wire("/PMOD2", [(rdac, "2"), (18.775, 3.9)])
    t.wire("/PMOD2", [(18.775, 3.9), (22.0, 3.9), (22.0, 20.5), (1.25, 20.5), (1.25, 21.5)], layer="B.Cu", silk=False)
    t.via("/PMOD2", 1.25, 21.5)                                                                           # board (52.0, 93.75)
    t.wire("INM", [(cm, "1"), (8.395, 10.725), (pa, "4")])
    t.gnd_stub(cm, "2", (6.6, 13.4), sym=(0, 0))
    t.wire("BYP", [(pa, "2"), (10.935, 8.9), (11.625, 8.9), (cb, "1")])
    t.gnd_stub(cb, "2", (13.4, 8.9), sym=(0, 0))
    t.via("VS", 12.205, 9.6)
    t.via("VS", 13.95, 16.6)
    t.wire("VS", [(pa, "1"), (12.205, 9.6)])
    t.wire("VS", [(12.205, 9.6), (13.95, 9.6), (13.95, 16.6)], layer="B.Cu", silk=False)
    t.wire("VS", [(13.95, 16.6), (cvdd, "1")])
    t.wire("VS", [(pa, "6"), (9.665, 18.9)])
    t.wire("VS", [(c100, "1"), (10.625, 18.9)])
    t.wire("VS", [(cvdd, "1"), (13.95, 18.9)])
    t.gnd_stub(pa, "7", (10.935, 15.9), sym=(0, 0))
    t.gnd_stub(c100, "2", (12.175, 18.2), sym=(0, 0))
    t.gnd_stub(cvdd, "2", (15.85, 18.2), sym=(0, 0))
    t.via("VOP", 8.395, 16.7)
    t.wire("VOP", [(pa, "5"), (8.395, 16.7)])
    t.wire("VOP", [(8.395, 16.7), (8.395, 17.3), (21.0, 17.3), (21.0, 9.1)], layer="B.Cu", silk=False)
    t.wire("VOP", [(21.0, 9.1), (spk, "1")])
    t.wire("VOM", [(pa, "8"), (14.6, 15.075), (14.6, 8.75), (20.4, 8.75), (20.4, 4.1), (spk, "2")])
    t.text(16.7, 2.4, "A12 1.05", 0.9, 0.17, "center")
    t.text(26.5, 13.0, "SPK", 0.8, 0.15, "center")
    # --- the microphone amplifier (right cell): the electret's socket at the bottom, 2.2 k from VS beside it, the signal up
    # the back past the speaker terminal to 1 uF above it, into the A2 geometry at x100 and down to MIC OUT
    mic = t.add("J", "HDR2", "MIC", 23.6, 17.0, 90, {"1": "MICP", "2": "GND"}, hide_value=True)             # pins at x 23.6, 26.14
    rb = t.add("R", "R0805 2.2k", "2.2k", 29.0, 16.6, 90, {"1": "VS", "2": "MICP"}, label=None)            # pad 1 down
    cc = t.add("C", "C0603 1uF", "1u", 31.5, 2.4, 0, {"1": "MICP", "2": "IN"}, label=None)
    t.wire("MICP", [(mic, "1"), (23.6, 15.0), (29.0, 15.0), (rb, "2")])
    t.wire("MICP", [(rb, "2"), (29.9, 15.65)])
    t.via("MICP", 29.9, 15.65)
    t.via("MICP", 29.9, 3.4)
    t.wire("MICP", [(29.9, 15.65), (29.9, 3.4)], layer="B.Cu", silk=False)
    t.wire("MICP", [(29.9, 3.4), (30.725, 3.4), (cc, "1")])
    t.wire("VS", [HDR_VS, (8.54, 18.9), (31.7, 18.9), (31.7, 18.1)], silk=False)
    t.wire("VS", [(rb, "1"), (29.0, 18.9)], silk=False)
    opa_tile_br(t, "R0603 100R", "100R", jack_in=False, dx=21.5, neg="top", legend=False, in_from=[(cc, "2"), (32.75, 2.4)])
    t.text(22.2, 14.0, "MIC", 0.8, 0.15, "left")
    t.result = "a speaker on SPK follows AUDIO IN (2.5 W into 4 ohm) or the one-bit stream on Pmod IO2 (10 k / 10 n); MIC OUT is the electret x100"
    t.notes = ["PAM8302A: 1 u couples AUDIO IN to IN+ (IN- grounded through 1 u), the one-bit DAC on Pmod IO2 arrives through 10 k",
               "into 10 n (1.6 kHz) at the same node, so both play.  BYP 1 u, SD high: on with the tile.  The electret (pin 1 is the",
               "+ side, 2.2 k from VS) through 1 u into an OPA810 at x100: a few hundred millivolts for speech."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


def tiles():
    return [tile_a2(), tile_a3(), tile_a4(), tile_a5(), tile_a6(), tile_a7(), tile_a8(), tile_a9(), tile_a10(), tile_a11(), tile_a12(), tile_a1()]


GND_LOOPS = [(3.0, 30.0), (3.0, 70.0), (97.0, 50.0), (97.0, 84.0)]
# no mounting holes: the Pmod plug fills the bottom-left corner where one stood, and a board plugged into a host's Pmod is
# held by the plug.  Four stick-on rubber feet instead, circled on the back (the bottom-left one above the plug's pins).
HOLES = []
FEET = [(5.0, 5.0), (95.0, 5.0), (95.0, 95.0), (5.0, 85.0)]
SLOTS = []
# the rails on L3: +5 V under the whole board; -5 V in the gutter under row 0 (and a strip down the left margin to the
# gutter under row 2, for A9); +3.3 V in the gutter under row 1.  Each tile reaches its rail with a via in the gutter.
RAIL_POURS = [("+5V", 0.6, 0.6, 99.4, 99.4, 0),
              # -5 V, one polygon: the gutter under row 0 (into the right margin as far as A1's red LED, no further, so the
              # +5 V pour keeps its path down that margin), a strip down the left margin, the gutter under row 2 for A9
              ("-5V", [(1.0, 27.75), (93.6, 27.75), (93.6, 29.25), (6.5, 29.25), (6.5, 70.75), (93.0, 70.75), (93.0, 72.25), (1.0, 72.25)], 1),
              ("+3V3", 7.0, 49.25, 93.0, 50.75, 1)]
# the Pmod lines on the back, board mm: from a tile's via to the via A11 declares by the plug; A11's own two run inside
# its tile.  Down the back of A9 and A11 at x 21.8 ... 24.3 (left of A9's LO jack and A11's RX socket), kept free there.
BACK_WIRES = [("/PMOD8", [(14.25, 39.75), (14.25, 48.9), (21.8, 48.9), (21.8, 92.45)]),
              ("/PMOD7", [(25.85, 45.75), (25.85, 48.3), (22.5, 48.3), (22.5, 93.1)]),
              ("/PMOD6", [(62.112, 30.65), (70.05, 30.65), (70.05, 50.0), (49.7, 50.0), (49.7, 98.0), (24.3, 98.0)])]
BACK_TEXT_X = 71.0                # right of the QR code's captions
QR_AT = (34.65, 84.25)            # under A11's right cell, left of its jack's legs and below the RX socket: 12.2 mm with no hole
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
