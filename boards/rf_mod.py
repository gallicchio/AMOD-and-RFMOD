"""RF-MOD: 915 MHz and 2.4 GHz, rev A.  Four layers: L1 the parts, the drawn wires and, on the RF tiles, a ground pour
0.25 mm from every 50 ohm line (coplanar waveguide over L2); L2 ground; L3 the rails (+5 V everywhere, +7.8 V in the
gutter under row 1); L4 ground with the back-side text.  Every jack of an RF tile has a launch void under its centre pin
(no copper on L2-L4 within 2.2 mm, the top pour 1.9 mm away) and every 50 ohm line a fence of ground vias.

Every tile keeps IN at the top-left slot and takes OUT at the bottom-right slot (not top-right as the AMOD boards do):
the jacks then form a checkerboard whose closest pair is 14.85 mm apart instead of 10.5, room for fingers and a wrench.

Rev A builds what JLCPCB had in stock on 2026-10-25: a splitter (R1), the two filters (R2, R4), the QPL9547 LNA (R5)
and a GALI-84+ gain block (R12), the power and reference tile (R9), two ADL5350 mixers (R7, R8), a MAX2871 synthesizer
(R10, which carries the Pmod plug) and the TRF3722 quadrature transmitter (R13: Jason's "Yes. Add that tile.", Prompt 13).
The printed antennas, the RFX2401C front end and the LTC5510 mixers stayed out.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, os.path.join(HERE, "..", "sim"))
import tiles as T
from tiles import Tile, power_header, HDR_VS
import geometry as G

STEM = "rf_mod"
LAYERS = 4
USB_X = 100.0 - 2.45           # the USB-C's centre: its face 1.2 mm past the right edge (AMOD-A's placement, rot 90)


# -------------------------------------------------------------------------------------------------------- R2, R4 --
def filter_tile(id, cell, key, value, pins, name, lines):
    """A filter between the IN jack (top-left) and the OUT jack (bottom-right): the part at the cell's centre on a line
    at y 10, the jacks' stubs down and up to it between their legs; both ground pads to vias (the top pour carries them too)."""
    t = Tile(id, name, [cell], subtitle="", sections=[], kind="rf")
    t.top_pour = True
    jin = t.jack("TL", "IN", "IN", "in", "+10 dBm")
    jout = t.jack("BR", "OUT", "OUT", "out", "")
    fl = t.add("FL", key, value, 10.0, 10.0, 0, pins, hide_value=False, label=None)
    return t, jin, jout, fl


def tile_r2():
    """2.45 GHz band-pass: Murata LFB212G45SG8A127 LTCC (2.0 x 1.25 mm), 1.7 dB loss, 2.4-2.5 GHz, 50 ohm both sides;
    pads 4 in, 2 out, 1 and 3 ground (as JLCPCB numbers them)."""
    t, jin, jout, fl = filter_tile("R2", (2, 0), "LTCC2G4", "LFB212", {"4": "IN", "2": "OUT", "1": "GND", "3": "GND"}, "2.45 GHz filter", [])
    t.rf("IN", [(jin, "1"), (4.75, 10.0), (fl, "4")])
    t.rf("OUT", [(fl, "2"), (15.25, 10.0), (jout, "1")])
    t.gnd_stub(fl, "1", (10.0, 8.4), sym=(0, -1))
    t.gnd_stub(fl, "3", (10.0, 11.6), sym=(0, 1))
    t.text(12.6, 2.4, "R2", 1.5, 0.3, "center")
    t.text(12.6, 4.3, "2.45 GHz", 0.8, 0.15, "center")
    t.text(12.6, 5.6, "LTCC BPF", 0.8, 0.15, "center")
    t.text(1.2, 18.6, "2.4-2.5 GHz", 0.9, 0.17, "left")
    t.text(1.2, 17.2, "1.7 dB LOSS", 0.8, 0.15, "left")
    t.text(1.2, 15.8, "LFB212G45", 0.8, 0.15, "left")
    t.result = "1.7 dB of loss from 2.4 to 2.5 GHz, 30 dB or more below 2.2 GHz and above 2.7 GHz (the datasheet); 50 ohm in and out"
    t.notes = ["Murata LFB212G45SG8A127, a 2012-size LTCC band-pass.  The line to each jack is 50 ohm coplanar waveguide (0.29 mm",
               "wide, 0.25 to the ground pour) with a via fence; the jack's centre pin has no plane under it (a 2.2 mm void).",
               "Sweep it with R10 or R13 into a power meter, or with a DAC harmonic comb and the ADC."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


def tile_r4():
    """915 MHz band-pass: RF360 B39921B2672P810 SAW (1.4 x 1.1 mm, 5 pads), 902-928 MHz, 1.1 dB loss; pad 1 in, 3 out,
    2, 4 and 5 ground.  The output pad sits 0.29 mm above the line: a short 45 degree jog brings it back."""
    t, jin, jout, fl = filter_tile("R4", (3, 0), "SAW915", "B39921", {"1": "IN", "3": "OUT", "2": "GND", "4": "GND", "5": "GND"}, "915 MHz filter", [])
    t.rf("IN", [(jin, "1"), (4.75, 10.0), (9.2, 10.0)])
    t.wire("IN", [(9.2, 10.0), (fl, "1")], width=0.2)                     # the last 0.3 mm narrower: ground pads 0.25 away
    t.wire("OUT", [(fl, "3"), (10.75, 10.287)], width=0.2)
    t.rf("OUT", [(10.75, 10.287), (10.9, 10.287), (11.19, 10.0), (15.25, 10.0), (jout, "1")])
    t.gnd_stub(fl, "5", (10.0, 8.5), sym=(0, -1), width=0.2)
    t.gnd_stub(fl, "2", (10.0, 11.5), sym=(0, 1), width=0.2)
    t.text(12.6, 2.4, "R4", 1.5, 0.3, "center")
    t.text(12.6, 4.3, "915 MHz", 0.8, 0.15, "center")
    t.text(12.6, 5.6, "SAW BPF", 0.8, 0.15, "center")
    t.text(1.2, 18.6, "902-928 MHz", 0.9, 0.17, "left")
    t.text(1.2, 17.2, "1.1 dB LOSS", 0.8, 0.15, "left")
    t.text(1.2, 15.8, "B39921B2672", 0.8, 0.15, "left")
    t.result = "1.1 dB of loss from 902 to 928 MHz, 40 dB or more 30 MHz outside the band (the datasheet); 50 ohm in and out"
    t.notes = ["RF360 B39921B2672P810: a surface-acoustic-wave filter for the 915 MHz ISM band, 26 MHz wide, in a 1411 package;",
               "its skirts are much steeper than the LTCC's.  Lines, fences and launch voids as on R2."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------- R5, R12 --
def gali_tile(id, cell):
    """A GALI-84+ gain block (SOT-89, rot 90: IN left, OUT right on y 10.5, the tab up).  100 pF blocks at both ports;
    the output pin carries the DC: a 27 nH choke up to the 100 pF-bypassed node VD, 22 ohm (2512, 0.2 W) from the tile's
    switched 7.8 V (VS) to VD, 10 uF on VS.  VS crosses the tile on the back from the header's FET to the resistor.
    The IN line runs down from the jack between its legs, the OUT line down to the bottom-right jack."""
    t = Tile(id, "gain block", [cell], supply="+8 V", subtitle="GALI-84+", sections=[], kind="rf")
    t.top_pour = True
    jin = t.jack("TL", "IN", "IN", "in", "0 dBm")
    jout = t.jack("BR", "OUT", "OUT", "out", "")
    power_header(t, rail="+8V")
    u = t.add("U", "GALI84", "GALI-84+", 11.5, 8.55, 90, {"1": "IN_A", "2": "GND", "3": "OUT_A"}, hide_value=False, label=None)
    cin = t.add("C", "C0402 100pF", "100p", 6.45, 10.5, 0, {"1": "IN", "2": "IN_A"}, label=None)
    cout = t.add("C", "C0402 100pF", "100p", 15.0, 10.5, 0, {"1": "OUT_A", "2": "OUT"}, label=None)
    l = t.add("L", "L0402 27nH", "27n", 14.6, 8.4, 270, {"1": "VD", "2": "OUT_A"}, label=None)          # pad 1 up
    cb = t.add("C", "C0402 100pF", "100p", 16.1, 6.7, 0, {"1": "VD", "2": "GND"}, label=None)
    rb = t.add("R", "R2512_22R", "22R", 14.5, 3.5, 0, {"1": "VS", "2": "VD"}, label=None)
    c10 = t.add("C", "C0805 10uF", "10u", 10.7, 14.4, 270, {"1": "GND", "2": "VS"}, label=None)         # pad 1 up
    t.rf("IN", [(jin, "1"), (4.75, 10.5), (cin, "1")])
    t.rf("IN_A", [(cin, "2"), (u, "1")])
    t.rf("OUT_A", [(u, "3"), (cout, "1")])
    t.rf("OUT", [(cout, "2"), (15.48, 15.25), (jout, "1")])
    t.wire("OUT_A", [(14.6, 10.5), (l, "2")], width=0.25)
    t.wire("VD", [(l, "1"), (14.6, 6.7), (cb, "1")], width=0.25)
    t.wire("VD", [(14.6, 6.7), (14.6, 5.8), (17.46, 5.8), (rb, "2")], width=0.25)
    t.gnd_stub(cb, "2", (17.5, 6.7), sym=(0, 0))
    t.gnd_stub(u, "2", [(11.5, 6.3), (12.1, 6.3), (12.1, 5.75)], sym=(0, 0))
    t.gnd_stub(u, "2", (11.5, 11.9), sym=(0, 0))
    t.wire("VS", [HDR_VS, (8.54, 17.0), (10.7, 17.0), (c10, "2")])
    t.via("VS", 10.7, 17.0)
    t.via("VS", 11.54, 1.3)
    t.wire("VS", [(10.7, 17.0), (10.7, 1.3), (11.54, 1.3)], layer="B.Cu", silk=False)
    t.wire("VS", [(11.54, 1.3), (rb, "1")])
    t.gnd_stub(c10, "1", [(10.0, 13.45), (10.0, 12.9)], sym=(0, 0))
    t.text(17.0, 8.3, id, 1.2, 0.2, "center")
    t.text(5.9, 11.85, "GALI-84+", 0.8, 0.15, "left")
    t.text(7.6, 13.1, "20 dB", 0.8, 0.15, "center")
    t.result = "20 dB of gain from 50 MHz to 2.5 GHz (datasheet: 21.9 dB at 1 GHz, 1 dB compression at +20 dBm out); 97 mA from 7.8 V"
    t.notes = ["Mini-Circuits GALI-84+: a Darlington MMIC that sets its own current; the 22 ohm from the 7.8 V rail drops to its",
               "5.8 V device voltage (0.2 W in the 2512).  The 27 nH choke (415 ohm at 2.45 GHz, 155 at 915 MHz) feeds the",
               "output pin; 100 pF blocks keep the DC off the jacks.  Keep the input under 0 dBm for linear gain.  The slide",
               "switch and P-FET gate the tile's 7.8 V as on AMOD-A."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


def qpl_tile(id, cell):
    """The QPL9547 low-noise amplifier (DFN-8 2 x 2 at (12.6, 9.25), rot 0: RF in on pin 2 and RF out on pin 7, both on
    y 9.0, Vbias on pin 1 above the input).  Qorvo's evaluation circuit: 100 pF blocks at both ports, an 18 nH wire-wound
    choke feeding 5 V (VS) into the output pin, 3.3 k from VS to Vbias (65 mA), shutdown (pin 6) and the NC pins
    grounded into the paddle.  VS runs up the back from the header's FET to a via beside the bias resistor.  The
    output pin's short run to its block is a plain track (the RF class's 0.25 mm would not clear the paddle)."""
    t = Tile(id, "LNA", [cell], supply="+5 V", subtitle="QPL9547", sections=[], kind="rf")
    t.top_pour = True
    t.fine = True
    jin = t.jack("TL", "IN", "IN", "in", "-20 dBm")
    jout = t.jack("BR", "OUT", "OUT", "out", "")
    power_header(t, rail="+5V")
    # pins (KiCad's footprint): 1 (11.588, 8.5) 2 (11.588, 9.0) 3 (11.588, 9.5) 4 (11.588, 10.0); 5 (13.612, 10.0) 6 (13.612, 9.5)
    # 7 (13.612, 9.0) 8 (13.612, 8.5); the paddle x 12.15-13.05, y 8.45-10.05
    u = t.add("U", "QPL9547", "QPL9547", 12.6, 9.25, 0, {"1": "VB", "2": "IN_A", "7": "OUT_A", "3": "GND", "4": "GND", "5": "GND", "6": "GND",
                                                      "8": "GND", "9": "GND"}, hide_value=False, label=None)
    F = 0.15
    t.gnd_stub(u, "9", (12.6, 9.25), sym=(0, 0), fine=True)
    for n, pt in (("3", (12.3, 9.5)), ("4", (12.3, 10.0)), ("5", (12.9, 10.0)), ("6", (12.9, 9.5)), ("8", (12.9, 8.5))):
        t.wire("GND", [(u, n), pt], width=F)                                      # into the paddle
    cin = t.add("C", "C0402 100pF", "100p", 9.0, 9.0, 0, {"1": "IN", "2": "IN_A"}, label=None)
    cout = t.add("C", "C0402 100pF", "100p", 15.25, 10.2, 270, {"1": "OUT_A", "2": "OUT"}, label=None)       # pad 1 up
    l1 = t.add("L", "L0402 18nH", "18n", 14.85, 7.55, 270, {"1": "VS", "2": "OUT_A"}, label=None)               # pad 1 up
    c3 = t.add("C", "C0402 100pF", "100p", 16.4, 6.4, 0, {"1": "VS", "2": "GND"}, label=None)
    c4 = t.add("C", "C0402 1uF", "1u", 16.4, 5.3, 0, {"1": "VS", "2": "GND"}, label=None)
    r4 = t.add("R", "R0402 3.3k", "3.3k", 11.588, 6.8, 90, {"1": "VB", "2": "VS"}, label=None)                   # pad 1 down
    cvb = t.add("C", "C0402 100pF", "100p", 10.1, 7.31, 0, {"1": "GND", "2": "VB"}, label=None)
    t.rf("IN", [(jin, "1"), (4.75, 9.0), (cin, "1")])
    t.wire("IN_A", [(cin, "2"), (u, "2")], width=0.2)
    t.wire("OUT_A", [(u, "7"), (15.25, 9.0), (cout, "1")], width=0.25)
    t.wire("OUT_A", [(14.85, 9.0), (l1, "2")], width=0.25)
    t.rf("OUT", [(cout, "2"), (jout, "1")])
    t.wire("VS", [(l1, "1"), (14.85, 6.4), (c3, "1")], width=0.25)
    t.wire("VS", [(14.85, 6.4), (14.85, 5.3), (c4, "1")], width=0.25)
    t.wire("VS", [(14.85, 6.4), (11.588, 6.4), (r4, "2")], width=0.25)
    t.wire("VB", [(r4, "1"), (u, "1")], width=F)
    t.wire("VB", [(r4, "1"), (cvb, "2")], width=F)
    t.gnd_stub(cvb, "1", (9.62, 6.3), sym=(0, 0), fine=True)
    t.gnd_stub(c3, "2", (17.9, 6.4), sym=(0, 0), fine=True)
    t.gnd_stub(c4, "2", (17.9, 5.3), sym=(0, 0), fine=True)
    c10 = t.add("C", "C0805 10uF", "10u", 10.7, 14.4, 270, {"1": "GND", "2": "VS"}, label=None)                  # pad 1 up
    t.wire("VS", [HDR_VS, (8.54, 17.0), (10.7, 17.0), (c10, "2")])
    t.via("VS", 10.7, 17.0)
    t.via("VS", 10.7, 6.4)
    t.wire("VS", [(10.7, 17.0), (10.7, 6.4)], layer="B.Cu", silk=False)
    t.wire("VS", [(10.7, 6.4), (11.588, 6.4)], width=0.25)
    t.gnd_stub(c10, "1", [(10.0, 13.45), (10.0, 12.9)], sym=(0, 0))
    t.text(11.6, 3.2, id, 1.2, 0.2, "center")
    t.text(19.0, 3.2, "QPL9547", 0.8, 0.15, "right")
    t.text(5.6, 11.3, "NF 0.3 dB", 0.8, 0.15, "left")
    t.result = "19.5 dB of gain and a 0.3-0.5 dB noise figure from 0.5 to 3 GHz (datasheet: 0.3 dB at 1.9 GHz, OIP3 +39 dBm); 65 mA from 5 V"
    t.notes = ["Qorvo QPL9547: a GaAs pHEMT LNA, internally matched to 50 ohm, 0.1-6 GHz.  It sets the noise figure of every receiver",
               "here, so put it first (before the filter) unless a strong neighbour overloads it; +39 dBm OIP3 makes that rare.",
               "The 18 nH wire-wound choke (Qorvo's value) feeds 5 V into the output pin; 3.3 k from 5 V to Vbias sets 65 mA.",
               "Never cable a transmitter into it without 30 dB of attenuation (22 dBm absolute maximum at the input)."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


def tile_r5():
    return qpl_tile("R5", (0, 1))


def tile_r12():
    return gali_tile("R12", (1, 1))


# ------------------------------------------------------------------------------------------------------------ R9 --
def tile_r9():
    """Power and reference, two cells.  Right cell: AMOD-A's USB-C input (CC pull-downs, 2 A PTC, 5 V TVS, 2 x 10 uF) and
    an MT3608 boost (22 uH, SS34, 12 k / 1 k: 7.8 V) with 10 uF out, feeding the +8V strip in the gutter below through
    two vias (its own and the divider's); a yellow LED says 7.8 V is up, a green one that 5 V is in.  Left cell: a
    TPS7A2033 makes 3.3 V for a TC32H4 25 MHz TCXO whose output a 74LVC1G17 buffers through 51 ohm to the REF OUT jack
    (top-left); the synthesizers' REF IN jacks are unterminated, so one REF OUT drives both through R1's splitter."""
    t = Tile("R9", "power", [(2, 1), (3, 1)], subtitle="USB-C 5 V in: +5, +7.8 V; 25 MHz reference", sections=[])
    t.pwr_flags = ["+5V", "+8V"]
    ux = USB_X - t.x0
    # ---- the USB-C input, AMOD-A's A1 geometry moved into the right cell (+21.5)
    j = t.add("J", "USBC", "USB-C", ux, 10.0, 90, {"A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS", "A5": "CC1", "B5": "CC2",
                                                   "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "SH": "GND"}, hide_value=True)
    t.wire("GND", [(j, "A1"), (ux - 3.13, 14.32)])
    t.wire("GND", [(j, "B1"), (ux - 3.13, 5.68)])
    rc1 = t.add("R", "R0805 5.1k", "5.1k", 39.1, 11.5, 0, {"1": "GND", "2": "CC1"}, label=None)
    rc2 = t.add("R", "R0805 5.1k", "5.1k", 39.1, 9.3, 0, {"1": "GND", "2": "CC2"}, label=None)
    t.wire("CC1", [(j, "A5"), (40.8, 11.25), (40.8, 11.5), (rc1, "2")], width=0.25)
    t.wire("CC2", [(j, "B5"), (40.8, 8.25), (40.8, 9.3), (rc2, "2")], width=0.25)
    t.gnd_stub(rc1, "1", (38.188, 10.4), sym=(0, 0))
    t.gnd_stub(rc2, "1", (37.4, 9.3), sym=(0, 0))
    t.wire("VBUS", [(j, "B9"), (41.4, 12.45)], width=0.25)
    t.wire("VBUS", [(j, "A9"), (41.4, 7.55)], width=0.25)
    t.wire("VBUS", [(41.4, 12.45), (41.4, 7.55)], layer="B.Cu")
    f = t.add("F", "PTC2A", "2A", 37.0, 6.2, 0, {"1": "+5V", "2": "VBUS"}, label=None)
    t.wire("VBUS", [(41.4, 7.55), (41.4, 6.2), (f, "2")])
    d = t.add("D", "TVS5V", "SMAJ5.0A", 32.1, 7.6, 270, {"1": "+5V", "2": "GND"}, label=None)
    c1 = t.add("C", "C0805 10uF", "10u", 28.5, 6.2, 180, {"1": "+5V", "2": "GND"}, label=None)
    c2 = t.add("C", "C0805 10uF", "10u", 28.5, 8.8, 180, {"1": "+5V", "2": "GND"}, label=None)
    t.wire("+5V", [(f, "1"), (c1, "1")])
    t.via("+5V", 30.6, 6.2)
    t.wire("+5V", [(c1, "1"), (c2, "1")])
    t.gnd_stub(d, "2", (32.1, 11.3), sym=(0, 0))
    t.gnd_stub(c1, "2", (27.55, 4.7), sym=(0, 0))
    t.gnd_stub(c2, "2", (26.5, 8.8), sym=(0, 0))
    # ---- the boost: 5 V in from the pour beside its input capacitor, the inductor, the MT3608 (rot 0: SW, GND, FB down
    # the left; EN, IN, NC down the right), the SS34 to the output capacitor and the +8V via in the gutter below
    cin3 = t.add("C", "C0805 10uF", "10u", 24.5, 10.0, 0, {"1": "+5V", "2": "GND"}, label=None)
    t.via("+5V", 22.3, 10.0)
    t.wire("+5V", [(22.3, 10.0), (cin3, "1")])
    t.gnd_stub(cin3, "2", (26.3, 10.0), sym=(0, 0))
    l = t.add("L", "L22U", "22u", 24.5, 13.4, 0, {"1": "+5V", "2": "SW"}, hide_value=False, label=None)
    t.wire("+5V", [(22.3, 10.0), (22.3, 12.3), (l, "1")], width=0.5)
    u1 = t.add("U", "MT3608", "MT3608", 24.0, 17.7, 0, {"1": "SW", "2": "GND", "3": "FB", "4": "+5V", "5": "+5V"}, hide_value=False, label=None)
    t.wire("SW", [(l, "2"), (26.1, 15.85), (21.9, 15.85), (21.9, 16.75), (u1, "1")], width=0.5)
    dd = t.add("D", "SS34", "SS34", 30.0, 17.6, 180, {"1": "+8V", "2": "SW"}, label=None)             # rot 180: cathode at +x
    t.wire("SW", [(26.1, 15.85), (28.0, 15.85), (dd, "2")], width=0.5)
    t.wire("+5V", [(u1, "4"), (u1, "5")])
    t.via("+5V", 25.1375, 19.5)
    t.wire("+5V", [(u1, "4"), (25.1375, 19.5)])
    t.gnd_stub(u1, "2", (21.6, 17.7), sym=(0, 0))
    co1 = t.add("C", "C0805 10uF", "10u", 35.3, 17.6, 0, {"1": "+8V", "2": "GND"}, label=None)
    t.wire("+8V", [(dd, "1"), (co1, "1")], width=0.5)
    t.gnd_stub(co1, "2", (37.1, 17.6), sym=(0, 0))
    t.via("+8V", 34.35, 20.5)
    t.wire("+8V", [(co1, "1"), (34.35, 20.5)], width=0.5, silk=False)
    r2 = t.add("R", "R0402 1k", "1k", 20.5, 17.5, 270, {"1": "GND", "2": "FB"}, label=None)             # pad 1 up
    r1 = t.add("R", "R0402 12k", "12k", 18.8, 18.65, 0, {"1": "+8V", "2": "FB"}, label=None)
    t.wire("FB", [(u1, "3"), (20.5, 18.65), (r1, "2")], width=0.25)
    t.wire("FB", [(r2, "2"), (20.5, 18.65)], width=0.25)
    t.gnd_stub(r2, "1", (19.8, 16.99), sym=(0, 0))
    t.via("+8V", 18.29, 20.5)
    t.wire("+8V", [(r1, "1"), (18.29, 20.5)], silk=False)
    ry = t.add("R", "R0805 1k", "1k", 35.3, 15.2, 0, {"1": "+8V", "2": "LEDY"}, label=None)
    dy = t.add("LED", "LED_Y", "+8V", 38.9, 15.2, 180, {"1": "GND", "2": "LEDY"}, label=None)          # rot 180: anode at -x
    t.wire("+8V", [(co1, "1"), (ry, "1")])
    t.wire("LEDY", [(ry, "2"), (dy, "2")])
    t.gnd_stub(dy, "1", (40.8, 15.2), sym=(0, 0))
    # ---- 3.3 V, the TCXO and its buffer (left cell)
    jr = t.jack("TL", "REF OUT", "REF", "out", "25 MHz, 1.6 Vpp into 50 ohm", silk="REF OUT")
    u2 = t.add("U", "TPS7A2033", "3.3V", 14.1, 13.2, 0, {"1": "+5V", "2": "GND", "3": "+5V", "5": "+3V3"}, hide_value=False, label=None)
    ci = t.add("C", "C0805 1uF", "1u", 10.4, 15.4, 270, {"1": "+5V", "2": "GND"}, label=None)
    cout = t.add("C", "C0805 1uF", "1u", 17.3, 14.8, 270, {"1": "+3V3", "2": "GND"}, label=None)
    t.gnd_stub(u2, "2", (11.7, 13.2), sym=(0, 0))
    t.route("+5V", [(u2, "1"), (u2, "3")])
    t.route("+5V", [(u2, "1"), (ci, "1")])
    t.via("+5V", 10.4, 12.6)
    t.wire("+5V", [(ci, "1"), (10.4, 12.6)])
    t.gnd_stub(ci, "2", (10.4, 17.6), sym=(0, 0))
    t.gnd_stub(cout, "2", (17.3, 17.2), sym=(0, 0))
    x1 = t.add("X", "TCXO25", "25 MHz", 14.8, 7.2, 180, {"2": "GND", "3": "OSC", "4": "+3V3"}, hide_value=False, label=None)   # rot 180: GND 2 top-left, OUT 3 bottom-left, VCC 4 bottom-right; pad 1 (E/D or N.C.) floats as on CostasLink
    cx = t.add("C", "C0603 100nF", "100n", 17.8, 9.6, 270, {"1": "+3V3", "2": "GND"}, label=None)        # pad 1 up
    t.wire("+3V3", [(u2, "5"), (15.2375, 9.6), (15.9, 9.6), (x1, "4")])
    t.wire("+3V3", [(x1, "4"), (17.8, 8.05), (cx, "1")])
    t.gnd_stub(cx, "2", (17.8, 11.4), sym=(0, 1))
    t.gnd_stub(x1, "2", [(13.7, 5.6), (12.0, 5.6)], sym=(0, 0))
    u3 = t.add("U", "LVC1G17", "74LVC1G17", 10.4, 9.2, 180, {"2": "OSC", "3": "GND", "4": "BUF", "5": "+3V3"}, hide_value=False, label=None)   # rot 180: IN 2 right-middle, GND 3 right-top, OUT 4 left-top, VCC 5 left-bottom
    t.wire("OSC", [(x1, "3"), (13.7, 9.2), (u3, "2")], width=0.25)
    t.gnd_stub(u3, "3", (12.3, 8.25), sym=(0, 0))
    cb3 = t.add("C", "C0603 100nF", "100n", 7.6, 12.3, 0, {"1": "GND", "2": "+3V3"}, label=None)
    t.wire("+3V3", [(cb3, "2"), (8.375, 10.15), (u3, "5")])
    t.gnd_stub(cb3, "1", (6.0, 12.3), sym=(0, 0))
    t.via("+3V3", 8.375, 11.2)
    t.via("+3V3", 16.5, 11.2)
    t.wire("+3V3", [(8.375, 11.2), (16.5, 11.2)], layer="B.Cu", silk=False)
    t.wire("+3V3", [(16.5, 11.2), (16.5, 13.85), (cout, "1")])
    t.wire("+3V3", [(u2, "5"), (16.5, 12.25)])
    rs1 = t.add("R", "R0402 51R", "51R", 9.2625, 6.4, 270, {"1": "REF", "2": "BUF"}, label=None)        # pad 1 up
    t.wire("BUF", [(u3, "4"), (rs1, "2")], width=0.25)
    t.wire("REF", [(rs1, "1"), (9.2625, 4.75), (jr, "1")])
    # ---- the LEDs in the right margin above the USB-C: green on +5 V
    dg = t.add("LED", "LED_G", "+5V", 46.1, 2.6, 90, {"1": "LEDG", "2": "+5V"}, label=None)          # rot 90: anode (pad 2) at the top
    rg = t.add("R", "R0805 1k", "1k", 48.1, 2.6, 90, {"1": "LEDG", "2": "GND"}, label=None)
    t.via("+5V", 46.1, 0.6)
    t.wire("+5V", [(dg, "2"), (46.1, 0.6)], silk=False)
    t.wire("LEDG", [(dg, "1"), (rg, "1")])
    t.gnd_stub(rg, "2", (48.1, 0.6), sym=(0, 0))
    t.text(10.5, 2.4, "R9", 1.5, 0.3, "center")
    t.text(19.2, 4.4, "REF 25 MHz", 0.8, 0.15, "right")
    t.text(41.0, 18.6, "POWER", 0.8, 0.15, "right")
    t.text(23.5, 5.0, "BOOST", 0.8, 0.15, "center")
    t.text(23.5, 6.4, "7.8 V", 0.8, 0.15, "center")
    t.result = "+5 V from the USB-C (up to 1.5 A), +7.8 V at 250 mA for the gain blocks (yellow LED), a 25 MHz square wave on REF OUT"
    t.notes = ["USB-C power only: 5.1 k on each CC asks any source for 5 V; a 2 A PTC, a 5 V TVS and 20 uF.  The MT3608 boosts to 7.8 V",
               "(0.6 V x 13 from 12 k / 1 k) for the GALI-84+ tile, R12 (100 mA); the +8V rail is a strip under row 1 that their",
               "headers reach with a via.  The TPS7A2033 makes 3.3 V for the TC32H4 TCXO (+-2 ppm) and the 74LVC1G17 that drives",
               "REF OUT (51 ohm: 1.6 Vpp into 50 ohm, 3.3 Vpp into a synthesizer's unterminated REF IN; R1 feeds both synthesizers).",
               "The TCXO's pad 1 (enable or no connection on the drawing) floats, as CostasLink's review settled."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------ R10, R13 --
def synth_tile(id, cells, host, share_ref=None, pmod_extra=None, ref_slot="TM"):
    """A MAX2871 synthesizer on two cells: OUT A at the top-left jack, REF IN at the top-middle one, the switch and
    P-FET header in the right cell with a TPS7A2033 making the tile's 3.3 V (V33, an island on L3 under the chip).
    The QFN sits in the left cell (rot 270: RF outputs on its left, the digital pins on its right, the SPI and charge
    pump along the top, TUNE and the filter pins along the bottom); every side fans out at 45 degrees to 0402 parts on
    a 1.2 mm pitch with 0.15 mm tracks (the "Fine" net class).  RFOUTA+ goes through 27 nH to V33 and 100 pF to the
    50 ohm line; RFOUTA- is terminated the same way into 51 ohm; RFOUTB is left open (disable it in software).  The
    loop filter (C1 470 p, R2 820 + C2 6.8 n, R3 470, C3 100 p: 80-120 kHz, 61 deg across both bands) sits above the
    chip at CP_OUT; its output hops to TUNE on the back.  CE and RFOUT_EN are tied to V33; LE has 100 k to ground;
    LD lights a red LED.  The host (R10) carries the 2 x 6 Pmod plug in the bottom margin; R13's SPI lines reach it
    on the back (gutter above the tiles, bottom margin).  `share_ref` (default: the host) puts REF IN on the board-wide
    /REF25 net with a via for a back wire; `pmod_extra` adds the plug's other pads (pad: net); `ref_slot` "BR1" moves
    REF IN to the right cell's bottom corner (the tile above may then use its BR0), its line on the back."""
    share_ref = host if share_ref is None else share_ref
    t = Tile(id, "synthesizer", cells, supply="+5 V", subtitle="MAX2871", sections=[], kind="rf")
    t.top_pour = True
    t.fine = True
    jout = t.jack("TL", "OUT A", "OUTA", "out", "", silk="OUT A")
    REFN = "/REF25" if share_ref else "REF"                             # the host's REF IN also feeds R13's TRF3722 (a back wire)
    jref = t.jack(ref_slot, "REF IN", REFN, "in", "25 MHz, 3.3 V CMOS", silk="REF IN")
    power_header(t, rail="+5V", dx=20.0)
    SCLK, SDATA = "/PMOD3", "/PMOD2"
    LE, MUX = ("/PMOD4", "/PMOD1") if host else ("/PMOD6", "/PMOD5")
    # ---- the LDO in the right cell: VS (the switched 5 V) in, V33 out to the island through a via
    ldo = t.add("U", "TPS7A2033", "3.3V", 30.5, 14.0, 0, {"1": "VS", "2": "GND", "3": "VS", "5": "V33"}, hide_value=False, label=None)
    ci = t.add("C", "C0805 1uF", "1u", 27.5, 10.9, 0, {"1": "VS", "2": "GND"}, label=None)
    cox, coy = (31.6, 10.9) if ref_slot == "TM" else (32.5, 10.7)       # with REF IN at BR1: right of the V33 track, clear of the jack
    co = t.add("C", "C0805 1uF", "1u", cox, coy, 0, {"1": "V33", "2": "GND"}, label=None)
    t.route("VS", [("Q%d01" % t.idx, "3"), (ldo, "3")])
    t.route("VS", [(ldo, "1"), (ldo, "3")])
    t.route("VS", [(ldo, "1"), (ci, "1")])
    t.gnd_stub(ldo, "2", (28.1, 14.0), sym=(0, 0))
    t.gnd_stub(ci, "2", (28.45, 9.8), sym=(0, -1))
    t.gnd_stub(co, "2", (cox + 1.9, coy), sym=(0, 0))
    t.wire("V33", [(ldo, "5"), (31.6375, 11.6), (cox - 0.95, 11.6), (co, "1")])
    t.via("V33", 30.65, 12.6)
    t.wire("V33", [(cox - 0.95, 11.6), (30.65, 12.6)] if cox != 31.6 else [(co, "1"), (30.65, 12.6)])
    # ---- the chip (rot 270 at (13.5, 10.5)): pins as the datasheet names them; 5 (SW), 14, 15 (RFOUTB) open
    u = t.add("U", "MAX2871", "MAX2871", 13.5, 10.5, 270,
              {"1": SCLK, "2": SDATA, "3": LE, "4": "V33", "6": "V33", "7": "CP", "8": "GND", "9": "GND", "10": "V33", "11": "GND",
               "12": "AP", "13": "AN", "16": "V33", "17": "V33", "18": "GND", "19": "NF", "20": "TN", "21": "GND", "22": "RS", "23": "BF",
               "24": "REG", "25": "LD", "26": "V33", "27": "GND", "28": "V33", "29": "REFI", "30": MUX, "31": "GND", "32": "V33", "33": "GND"},
              hide_value=False, label=None)
    F = 0.15                                                   # the fan-out tracks
    for (vx, vy) in ((12.9, 9.9), (14.1, 9.9), (12.9, 11.1), (14.1, 11.1)):     # the exposed pad's vias
        t.gnd_stub(u, "33", (vx, vy), sym=(0, 0))
    for n, pt in (("8", (12.1, 9.3)), ("9", (12.05, 8.75)), ("11", (12.2, 9.75)), ("18", (12.25, 11.8)), ("21", (13.75, 11.8)),
                  ("27", (14.8, 11.25)), ("31", (14.8, 9.25))):                   # the ground pins straight into the exposed pad
        t.wire("GND", [(u, n), pt], width=F)
    # ---- top row (y 8.06, left to right 8 7 6 5 4 3 2 1): the charge pump and its filter, VCC_CP, CE, the SPI
    c1 = t.add("C", "C0603 470pF", "470p", 12.25, 5.5, 90, {"1": "CP", "2": "GND"}, label=None)              # pad 1 down
    t.wire("CP", [(u, "7"), (12.25, 7.3), (c1, "1")], width=F)
    t.gnd_stub(c1, "2", (12.25, 3.9), sym=(0, -1), fine=True)
    r3 = t.add("R", "R0402 470R", "470", 10.9, 4.6, 270, {"1": "TN", "2": "CP"}, label=None)                 # pad 1 up
    r2 = t.add("R", "R0402 820R", "820", 9.4, 5.3, 270, {"1": "N2", "2": "CP"}, label=None)
    c2 = t.add("C", "C0603 6.8nF", "6.8n", 9.4, 2.6, 90, {"1": "N2", "2": "GND"}, label=None)                 # pad 1 down
    t.wire("CP", [(12.25, 7.3), (10.9, 7.3), (r3, "2")], width=F)
    t.wire("CP", [(10.9, 6.4), (9.4, 6.4), (r2, "2")], width=F)
    t.wire("N2", [(r2, "1"), (c2, "1")], width=F)
    t.gnd_stub(c2, "2", (9.4, 1.2), sym=(0, 0), fine=True)
    t.via("TN", 10.9, 3.2, fine=True)
    t.wire("TN", [(r3, "1"), (10.9, 3.2)], width=F)
    t.via("TN", 13.0, 14.7, fine=True)
    t.wire("TN", [(10.9, 3.2), (10.9, 9.0), (13.5, 9.0), (13.5, 14.2), (13.0, 14.7)], width=F, layer="B.Cu", silk=False, fine=True)
    c6 = t.add("C", "C0402 100nF", "100n", 13.6, 5.5, 90, {"1": "V33", "2": "GND"}, label=None)              # pad 1 down
    t.wire("V33", [(u, "6"), (12.75, 7.5), (13.6, 6.65), (c6, "1")], width=F)
    t.via("V33", 13.6, 6.9, fine=True)
    t.gnd_stub(c6, "2", (13.6, 4.2), sym=(0, 0), fine=True)
    t.via("V33", 14.6, 5.0, fine=True)
    t.wire("V33", [(u, "4"), (13.75, 7.5), (14.6, 6.65), (14.6, 5.0)], width=F)
    t.via(LE, 15.1, 4.3, fine=True)
    t.wire(LE, [(u, "3"), (14.25, 7.5), (15.1, 6.65), (15.1, 4.3)], width=F)
    t.via(SCLK, 16.1, 5.6, fine=True)
    t.wire(SCLK, [(u, "1"), (15.25, 7.5), (16.1, 6.65), (16.1, 5.6)], width=F)
    if host:
        t.via(SDATA, 16.6, 2.4, fine=True)
        t.wire(SDATA, [(u, "2"), (14.75, 7.5), (15.6, 6.65), (15.6, 3.4), (16.6, 2.4)], width=F)
    else:
        t.via(SDATA, 15.6, 3.4, fine=True)
        t.wire(SDATA, [(u, "2"), (14.75, 7.5), (15.6, 6.65), (15.6, 3.4)], width=F)
    rle = t.add("R", "R0402 100k", "100k", 14.3, 3.4, 0, {"1": "GND", "2": LE}, label=None)                 # left of the LE via
    t.wire(LE, [(15.1, 4.3), (15.1, 3.4), (rle, "2")], width=F)
    t.gnd_stub(rle, "1", (13.79, 2.5), sym=(0, 0), fine=True)
    # ---- right column (x 15.94, top to bottom 32 31 30 29 28 27 26 25): VCC_SD, MUX, REF_IN, VCC_DIG, RFOUT_EN, LD
    c32 = t.add("C", "C0402 100nF", "100n", 17.6, 9.15, 0, {"1": "V33", "2": "GND"}, label=None)
    t.wire("V33", [(u, "32"), (16.6, 8.75), (17.0, 9.15), (c32, "1")], width=F)
    t.via("V33", 17.09, 8.4, fine=True)
    t.wire("V33", [(c32, "1"), (17.09, 8.4)], width=F)
    t.gnd_stub(c32, "2", (18.8, 9.15), sym=(0, 0), fine=True)
    t.via(MUX, 18.3, 10.55, fine=True)
    t.wire(MUX, [(u, "30"), (16.6, 9.75), (17.4, 10.55), (18.3, 10.55)], width=F)
    cref = t.add("C", "C0402 100nF", "100n", 19.2, 11.3, 0, {"1": "REFI", "2": REFN}, label=None)
    t.wire("REFI", [(u, "29"), (16.6, 10.25), (17.65, 11.3), (cref, "1")], width=F)
    if ref_slot == "TM":
        t.wire(REFN, [(jref, "1"), (20.75, 11.3), (cref, "2")], width=0.25)
    else:                                                               # along the back from the jack's pin to a via beside cref
        t.wire(REFN, [(jref, "1"), (36.4, 15.6), (20.75, 15.6), (20.75, 11.3)], width=0.25, layer="B.Cu", silk=False)
        t.wire(REFN, [(20.75, 11.3), (cref, "2")], width=0.25)
    if share_ref:
        t.via(REFN, 20.75, 11.3, fine=True)                             # down the back and along the bottom margin to R13
    c28 = t.add("C", "C0402 100nF", "100n", 19.5, 12.9, 90, {"1": "V33", "2": "GND"}, label=None)             # pad 1 down
    t.wire("V33", [(u, "28"), (16.6, 10.75), (19.2, 13.35), (c28, "1")], width=F)
    t.via("V33", 19.5, 14.3, fine=True)
    t.wire("V33", [(c28, "1"), (19.5, 14.3)], width=F)
    t.via("V33", 17.6, 12.5, fine=True)
    t.wire("V33", [(u, "26"), (16.85, 11.75), (17.6, 12.5)], width=F)
    rld = t.add("R", "R0402 1k", "1k", 18.3, 14.0, 270, {"1": "LD", "2": "LEDA"}, label=None)                  # pad 1 up
    led = t.add("LED", "LED_R", "LOCK", 18.3, 16.9, 90, {"1": "GND", "2": "LEDA"}, label=None)                   # rot 90: anode (pad 2) up
    t.wire("LD", [(u, "25"), (16.6, 12.25), (17.84, 13.49), (rld, "1")], width=F)
    t.wire("LEDA", [(rld, "2"), (led, "2")], width=F)
    t.gnd_stub(led, "1", (19.2, 17.84), sym=(0, 0))
    # ---- left column (x 11.06, top to bottom 9 10 11 12 13 14 15 16): RFOUTA+ to the jack, RFOUTA- terminated, VCC_RF
    la = t.add("L", "L0402 27nH", "27n", 9.8, 8.6, 270, {"1": "V33", "2": "AP"}, label=None)                  # pad 1 up
    ca = t.add("C", "C0402 100pF", "100p", 8.9, 10.6, 90, {"1": "OUTA", "2": "AP"}, label=None)                 # pad 1 down
    t.wire("AP", [(u, "12"), (8.9, 10.25)], width=F)
    t.wire("AP", [(la, "2"), (9.8, 10.25)], width=F)
    t.via("V33", 9.8, 7.3, fine=True)
    t.wire("V33", [(la, "1"), (9.8, 7.3)], width=F)
    t.wire("V33", [(u, "10"), (10.4, 9.25), (10.4, 8.115), (la, "1")], width=F)                                # VCC_PLL shares the choke's node
    t.rf("OUTA", [(ca, "1"), (8.9, 11.6), (4.75, 11.6), (jout, "1")])
    lb = t.add("L", "L0402 27nH", "27n", 9.7, 13.3, 270, {"1": "AN", "2": "V33"}, label=None)                  # pad 1 up
    cb = t.add("C", "C0402 100pF", "100p", 8.5, 13.3, 270, {"1": "AN", "2": "TRM"}, label=None)
    rb = t.add("R", "R0402 51R", "51R", 8.5, 15.3, 270, {"1": "TRM", "2": "GND"}, label=None)
    t.wire("AN", [(u, "13"), (10.1, 10.75), (10.1, 12.3), (9.7, 12.3), (lb, "1")], width=F)
    t.wire("AN", [(9.7, 12.3), (8.5, 12.3), (cb, "1")], width=F)
    t.wire("TRM", [(cb, "2"), (rb, "1")], width=F)
    t.gnd_stub(rb, "2", (8.5, 16.7), sym=(0, 1), fine=True)
    t.via("V33", 9.7, 14.7)
    t.wire("V33", [(lb, "2"), (9.7, 14.7)], width=F)
    c16 = t.add("C", "C0402 100nF", "100n", 10.8, 14.7, 270, {"1": "V33", "2": "GND"}, label=None)             # pad 1 up: VCC_RF and VCC_VCO
    t.wire("V33", [(u, "16"), (10.5, 12.25), (10.5, 13.3), (10.8, 13.6), (c16, "1")], width=F)
    t.wire("V33", [(u, "17"), (11.75, 13.6), (11.14, 14.21), (c16, "1")], width=F)
    t.via("V33", 11.0, 13.3)
    t.wire("V33", [(10.5, 13.3), (11.0, 13.3)], width=F)
    t.gnd_stub(c16, "2", (10.8, 15.6), sym=(0, 0), fine=True)
    # ---- bottom row (y 12.94, left to right 17 18 19 20 21 22 23 24): NOISE_FILT, TUNE (C3), RSET, BIAS_FILT, REG
    for n, px, X, key, val, net in (("19", 12.75, 11.6, "C0402 1uF", "1u", "NF"), ("20", 13.25, 13.0, "C0603 100pF", "100p", "TN"),
                                    ("22", 14.25, 14.4, "R0402 5.1k", "5.1k", "RS"), ("23", 14.75, 15.6, "C0402 1uF", "1u", "BF"),
                                    ("24", 15.25, 16.8, "C0402 1uF", "1u", "REG")):
        pfx = key[0]
        ref = t.add(pfx, key, val, X, 16.9, 270, {"1": net, "2": "GND"}, label=None)                              # pad 1 up
        t.wire(net, [(u, n), (px, 13.5), (X, 13.5 + abs(X - px)), (ref, "1")], width=F)
        if X < 15.0:                                                                                           # the SPI lines pass the others on the back
            t.gnd_stub(ref, "2", (X, 18.4), sym=(0, 0), fine=True)
    # ---- the Pmod plug (the host) and the lines to it on the back: the leftmost line turns highest (no crossings)
    if host:
        # two columns left of the feeds' first layout: they meet pads 5-12, ground and 3.3 V are pads 1-4 (see pmod_plug)
        pins = {"6": LE, "8": SCLK, "10": SDATA, "12": MUX, "9": "/PMOD6", "11": "/PMOD5", "3": "GND", "4": "GND", "1": "/PMOD_VCC", "2": "/PMOD_VCC"}
        pins.update(pmod_extra or {})
        pm = t.add("J", "PMOD", "Pmod", 2.97, 24.25, 0, pins, hide_value=True)
        t.wire("/PMOD_VCC", [(pm, "1"), (pm, "2")], silk=False)
        t.wire(LE, [(15.1, 4.3), (15.1, 20.6), (1.7, 20.6), (pm, "6")], width=F, layer="B.Cu", silk=False, fine=True)
        t.wire(SCLK, [(16.1, 5.6), (16.1, 20.95), (4.24, 20.95), (pm, "8")], width=F, layer="B.Cu", silk=False, fine=True)
        t.wire(SDATA, [(16.6, 2.4), (16.6, 21.3), (6.78, 21.3), (pm, "10")], width=F, layer="B.Cu", silk=False, fine=True)
        t.wire(MUX, [(18.3, 10.55), (18.3, 21.65), (9.32, 21.65), (pm, "12")], width=F, layer="B.Cu", silk=False, fine=True)
    else:
        t.via(MUX, 18.3, 21.0)                                                   # down the back, then the front along the bottom edge
        t.wire(MUX, [(18.3, 10.55), (18.3, 21.0)], width=F, layer="B.Cu", silk=False, fine=True)
    t.text(1.2, 13.3, id, 1.0, 0.18, "left")
    t.text(1.2, 14.6, "MAX2871", 0.8, 0.15, "left")
    t.result = "any frequency from 23.5 MHz to 6 GHz on OUT A (-4 to +5 dBm in steps), locked to the 25 MHz on REF IN; the red LED says locked"
    t.notes = ["MAX2871 as CostasLink built it: fractional-N PLL with four VCOs, programmed over SPI from the Pmod (SCLK, SDATA,",
               "LE; MUXOUT back).  The loop filter is third order, 80-120 kHz with 61 degrees of margin for both 915 MHz (VCO / 4)",
               "and 2.4 GHz (VCO / 2) at ICP 2.56 mA (RSET 5.1 k, CP = 7).  RFOUTA+ feeds the jack through 27 nH to 3.3 V and",
               "100 pF; RFOUTA- is terminated in 51 ohm the same way; RFOUTB is open and must stay disabled.  CE and RFOUT_EN are",
               "tied high, LE has 100 k down.  REF IN is unterminated: one REF OUT drives both synthesizers through R1."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


def tile_r10():
    return synth_tile("R10", [(0, 3), (1, 3)], host=True)


def trf_tile(id, cells):
    """The TRF3722: an I/Q modulator with its own PLL and VCO, 400-4200 MHz, on two cells.  The chip (VQFN-48, rot 90 at
    (13.4, 10.45)) has its baseband I pair on the top edge, Q on the bottom, RFOUT on the right (y 10.7, straight along
    a 50 ohm line to the bottom-right jack through TI's 4.7 pF), the reference, serial port and charge pump on the
    left, VTUNE top-left.  Each baseband input takes the host's DAC (+-1 V into 50 ohm: 56 ohm at the jack) through
    270 ohm to a node that 910 ohm from 3.3 V and 100 ohm to ground hold at 0.245 V: +-0.25 V there for +-1 V at the
    jack, the chip's 0.25 V common mode and 0.5 Vpp differential; the negative input sits at the same 0.25 V through
    910 / 75 ohm.  Loop filter (TI's fractional one, its third pole dropped): 1 nF, 1.1 k + 10 nF, 1.1 k / 330 pF, its
    output on the back to VTUNE.  3.3 V from a TLV75733 in the right cell onto an island on L3 under everything; every
    supply pin has a via to it and the modulator's four a 100 nF and a 100 pF.  The 25 MHz reference comes from R10's
    REF IN on the back; the serial lines share R10's SCLK and SDATA (Pmod IO3, IO2) with LE on IO6 and readback on IO5.
    The LO outputs and EXT_VCO are unused."""
    t = Tile(id, "I/Q transmitter", cells, supply="+5 V", subtitle="TRF3722", sections=[], kind="rf")
    t.top_pour = True
    t.fine = True
    F = 0.15
    jI = t.jack("TL", "I IN", "BBI", "in", "+-1 V into 50 ohm", silk="I IN")
    jQ = t.jack("TL1", "Q IN", "BBQ", "in", "+-1 V into 50 ohm", silk="Q IN")
    jRF = t.jack("BR1", "RF OUT", "RFOUT", "out", "", silk="RF OUT")
    power_header(t, rail="+5V", dx=20.0)
    CX, CY = 13.4, 10.45
    pins = {"1": "GND", "2": "/PMOD5", "3": "LD", "4": "V33", "5": "GND", "6": "V33", "7": "GND", "8": "BQN", "10": "BQP", "11": "GND",
            "14": "V33", "15": "GND", "16": "V33", "17": "GND", "18": "RFO", "19": "GND", "20": "GND", "21": "V33", "22": "GND", "23": "V33",
            "26": "GND", "27": "BIP", "29": "BIN", "30": "GND", "32": "V33", "33": "V33", "34": "VT", "35": "V33",
            "37": "GND", "40": "GND", "41": "CP", "42": "V33", "43": "GND", "44": "REFI", "45": "GND", "46": "/PMOD6", "47": "/PMOD2",
            "48": "/PMOD3", "49": "GND"}
    u = t.add("U", "TRF3722", "TRF3722", CX, CY, 90, pins, hide_value=False, label=None)

    def P(n):                                                 # a pin's centre at rot 90
        if n <= 12:
            xo, yo = -3.438, -2.75 + 0.5 * (n - 1)
        elif n <= 24:
            xo, yo = -2.75 + 0.5 * (n - 13), 3.438
        elif n <= 36:
            xo, yo = 3.438, 2.75 - 0.5 * (n - 25)
        else:
            xo, yo = 2.75 - 0.5 * (n - 37), -3.438
        return (round(CX + yo, 3), round(CY - xo, 3))
    # ---- grounds into the exposed pad, and its vias
    for (vx, vy) in [(x, y) for x in (12.2, 13.4, 14.6) for y in (9.25, 10.45, 11.65)]:
        t.gnd_stub(u, "49", (vx, vy), sym=(0, 0), fine=True)
    for n in (15, 17, 19, 20, 22):
        t.wire("GND", [(u, str(n)), (15.7, P(n)[1])], width=F)
    for n in (5, 7, 11):
        t.wire("GND", [(u, str(n)), (P(n)[0], 12.9)], width=F)
    t.wire("GND", [(u, "1"), (P(1)[0], 13.35), (11.0, 12.95)], width=F)          # PD low: on
    t.wire("GND", [(u, "37"), (10.4, P(37)[1]), (10.95, 7.95)], width=F)       # inward between pins 36 and 38
    for n in (40, 43, 45):
        t.wire("GND", [(u, str(n)), (11.0, P(n)[1])], width=F)
    for n in (26, 30):
        t.wire("GND", [(u, str(n)), (P(n)[0], 8.0)], width=F)
    # ---- the modulator's supplies (right edge, two pairs) and the RF output between them
    cA = t.add("C", "C0402 100nF", "100n", 19.0, 7.9, 0, {"1": "V33", "2": "GND"}, label=None)
    cB = t.add("C", "C0402 100pF", "100p", 19.0, 9.45, 0, {"1": "V33", "2": "GND"}, label=None)
    cC = t.add("C", "C0402 100pF", "100p", 19.0, 11.95, 0, {"1": "V33", "2": "GND"}, label=None)
    cD = t.add("C", "C0402 100nF", "100n", 19.0, 13.5, 0, {"1": "V33", "2": "GND"}, label=None)
    t.wire("V33", [(u, "23"), (17.7, P(23)[1]), (17.7, P(21)[1]), (u, "21")], width=F)
    t.wire("V33", [(17.7, P(23)[1]), (17.7, 7.9), (cA, "1")], width=F)
    t.wire("V33", [(17.7, P(21)[1]), (17.7, 9.45), (cB, "1")], width=F)
    t.via("V33", 17.7, 8.7, fine=True)
    t.wire("V33", [(u, "16"), (17.7, P(16)[1]), (17.7, P(14)[1]), (u, "14")], width=F)
    t.wire("V33", [(17.7, P(16)[1]), (17.7, 11.95), (cC, "1")], width=F)
    t.wire("V33", [(17.7, P(14)[1]), (17.7, 13.5), (cD, "1")], width=F)
    t.via("V33", 17.7, 12.2, fine=True)
    for c, y in ((cA, 7.9), (cB, 9.45), (cC, 11.95), (cD, 13.5)):
        t.gnd_stub(c, "2", (20.4, y), sym=(0, 0), fine=True)
    crf = t.add("C", "C0402 4.7pF", "4.7p", 18.6, 10.7, 0, {"1": "RFO", "2": "RFOUT"}, label=None)
    t.wire("RFO", [(u, "18"), (crf, "1")], width=0.25)
    t.rf("RFOUT", [(crf, "2"), (36.75, 10.7), (jRF, "1")])
    # ---- the other supplies: a via each to the island, a 100 nF where there is room
    t.wire("V33", [(u, "4"), (P(4)[0], 14.7), (P(6)[0], 14.7), (u, "6")], width=F)               # VCC_DIG, VCC_LO1
    t.wire("V33", [(12.65, 14.7), (12.65, 15.25)], width=F)
    t.via("V33", 12.65, 15.25, fine=True)
    cF = t.add("C", "C0402 100nF", "100n", 7.6, 10.1, 0, {"1": "GND", "2": "V33"}, label=None)    # VCC_PLL
    t.wire("V33", [(u, "42"), (8.9, P(42)[1]), (8.4, 10.1), (cF, "2")], width=F)
    t.via("V33", 8.9, P(42)[1], fine=True)
    t.gnd_stub(cF, "1", (6.2, 10.1), sym=(0, 0), fine=True)
    t.wire("V33", [(u, "33"), (P(33)[0], 6.3), (P(32)[0], 6.3), (u, "32")], width=F)              # VCC_VCO, VCC_TK (3.3 V)
    t.wire("V33", [(12.4, 6.3), (12.4, 5.85)], width=F)
    t.via("V33", 12.4, 5.85, fine=True)
    cG = t.add("C", "C0402 100nF", "100n", 12.4, 4.6, 90, {"1": "V33", "2": "GND"}, label=None)   # pad 1 down
    t.wire("V33", [(12.4, 5.85), (cG, "1")], width=F)
    t.gnd_stub(cG, "2", (12.4, 3.0), sym=(0, 0), fine=True)
    t.wire("V33", [(u, "35"), (P(35)[0], 6.3), (10.75, 6.0)], width=F)                           # VCC_LO2
    t.via("V33", 10.75, 6.0, fine=True)
    # ---- the loop filter above-left: CP up the left edge, VTUNE back on the back
    c1 = t.add("C", "C0402 1nF", "1n", 8.82, 4.6, 90, {"1": "CP", "2": "GND"}, label=None)
    r2 = t.add("R", "R0402 1.1k", "1.1k", 9.92, 4.6, 90, {"1": "CP", "2": "N2"}, label=None)
    c2 = t.add("C", "C0402 10nF", "10n", 9.92, 2.5, 90, {"1": "N2", "2": "GND"}, label=None)
    r3 = t.add("R", "R0402 1.1k", "1.1k", 11.02, 4.6, 90, {"1": "CP", "2": "VT"}, label=None)
    c3 = t.add("C", "C0402 330pF", "330p", 11.02, 2.5, 90, {"1": "VT", "2": "GND"}, label=None)
    t.wire("CP", [(u, "41"), (9.1, P(41)[1]), (9.1, 5.11), (c1, "1")], width=F)
    t.wire("CP", [(9.1, 5.11), (r2, "1"), (r3, "1")], width=F)
    t.wire("N2", [(r2, "2"), (c2, "1")], width=F)
    t.wire("VT", [(r3, "2"), (c3, "1")], width=F)
    t.gnd_stub(c1, "2", (8.82, 3.1), sym=(0, 0), fine=True)
    t.gnd_stub(c2, "2", (9.92, 0.95), sym=(0, 0), fine=True)
    t.gnd_stub(c3, "2", (11.02, 0.95), sym=(0, 0), fine=True)
    t.wire("VT", [(11.75, 3.4), (11.02, 3.4)], width=F)
    t.via("VT", 11.75, 3.4, fine=True)
    t.via("VT", 11.6, 6.1, fine=True)
    t.wire("VT", [(11.75, 3.4), (11.6, 3.9), (11.6, 6.1)], width=F, layer="B.Cu", silk=False, fine=True)
    t.wire("VT", [(11.6, 6.1), (u, "34")], width=F)
    # ---- the baseband networks: I above the chip, Q below
    nets = {"top": ("BIN", "BIP", "BBI", 4.9, 90, 6.2, 3.4, 2.6), "bot": ("BQN", "BQP", "BBQ", 16.0, 270, 14.75, 17.6, 18.4)}
    for side, (NN, NP, J, yr, rr, ybus, yv, yt) in nets.items():
        r2n = t.add("R", "R0402 75R", "75", 13.45, yr, rr, {"1": NN, "2": "GND"}, label=None)
        r1n = t.add("R", "R0402 910R", "910", 14.55, yr, rr, {"1": NN, "2": "V33"}, label=None)
        r3p = t.add("R", "R0402 270R", "270", 15.65, yr, rr, {"1": NP, "2": J}, label=None)
        r1p = t.add("R", "R0402 910R", "910", 16.75, yr, rr, {"1": NP, "2": "V33"}, label=None)
        r2p = t.add("R", "R0402 100R", "100", 17.85, yr, rr, {"1": NP, "2": "GND"}, label=None)
        rt = t.add("R", "R0402 56R", "56", 16.7, yt, 0, {"1": J, "2": "GND"}, label=None)
        pn, pp = ("29", "27") if side == "top" else ("8", "10")
        t.wire(NN, [(u, pn), (P(int(pn))[0], ybus), (14.55, ybus), (r1n, "1")], width=F)
        t.wire(NN, [(P(int(pn))[0], ybus), (13.45, ybus), (r2n, "1")], width=F)
        t.wire(NP, [(u, pp), (P(int(pp))[0], ybus), (15.65, ybus), (r3p, "1")], width=F)
        t.wire(NP, [(15.65, ybus), (16.75, ybus), (r1p, "1")], width=F)
        t.wire(NP, [(16.75, ybus), (17.85, ybus), (r2p, "1")], width=F)
        t.wire(J, [(r3p, "2"), (15.65, yt), (rt, "1")], width=F)
        t.wire("V33", [(r1n, "2"), (14.55, yv)], width=F)
        t.via("V33", 14.55, yv, fine=True)
        t.wire("V33", [(r1p, "2"), (16.75, yv)], width=F)
        t.via("V33", 16.75, yv, fine=True)
        t.gnd_stub(r2n, "2", (13.45, yv), sym=(0, 0), fine=True)
        t.gnd_stub(r2p, "2", (17.85, yv), sym=(0, 0), fine=True)
        t.gnd_stub(rt, "2", (18.1, yt), sym=(0, 0), fine=True)
        t.route(J, [((jI if side == "top" else jQ), "1"), (rt, "1")], width=0.2)
    # ---- the reference, the serial port, readback and lock detect: short escapes, then the router
    cref = t.add("C", "C0402 100nF", "100n", 7.6, 11.2, 0, {"1": "/REF25", "2": "REFI"}, label=None)
    t.wire("REFI", [(u, "44"), (cref, "2")], width=F)
    # the serial port fanned out by hand: LE down the back to its exit, SDATA and SCLK straight out to the gutter
    t.wire("/PMOD6", [(u, "46"), (8.6, P(46)[1])], width=F)
    t.via("/PMOD6", 8.6, P(46)[1], fine=True)
    t.wire("/PMOD2", [(u, "47"), (-1.05, P(47)[1])], width=F)
    t.via("/PMOD2", -1.05, P(47)[1], fine=True)
    t.wire("/PMOD3", [(u, "48"), (-0.45, P(48)[1])], width=F)
    t.via("/PMOD3", -0.45, P(48)[1], fine=True)
    t.wire("/PMOD5", [(u, "2"), (P(2)[0], 14.9), (7.0, 14.9), (7.0, 20.6)], width=F, silk=False)
    t.via("/REF25", 3.0, 20.6, fine=True)
    t.route("/REF25", [(3.0, 20.6), (cref, "1")], width=0.2)
    rld = t.add("R", "R0402 1k", "1k", P(3)[0], 17.0, 270, {"1": "LD", "2": "LEDA"}, label=None)   # pad 1 up
    led = t.add("LED", "LED_R", "LOCK", 9.4, 17.9, 0, {"1": "GND", "2": "LEDA"}, label=None)        # anode right
    t.wire("LEDA", [(rld, "2"), (P(3)[0], 17.9), (led, "2")], width=F)
    t.gnd_stub(led, "1", (7.6, 17.9), sym=(0, 0))
    t.wire("LD", [(u, "3"), (rld, "1")], width=F)
    # ---- 3.3 V: the LDO in the right cell, VS from the header's FET
    ldo = t.add("U", "TLV75733", "3.3V", 30.0, 13.6, 0, {"1": "V33", "3": "GND", "4": "VS", "6": "VS", "7": "GND"}, hide_value=False, label=None)
    ci = t.add("C", "C0603 1uF", "1u", 32.4, 13.6, 90, {"1": "VS", "2": "GND"}, label=None)          # pad 1 down
    co = t.add("C", "C0603 1uF", "1u", 27.6, 13.6, 90, {"1": "GND", "2": "V33"}, label=None)
    t.wire("VS", [(ldo, "6"), (31.6, 12.95), (31.6, 14.25), (ldo, "4")], width=0.3)
    t.wire("VS", [(31.6, 14.25), (31.6, 14.375), (ci, "1")], width=0.3)
    t.route("VS", [("Q%d01" % t.idx, "3"), (ldo, "4")], width=0.35)
    t.wire("V33", [(ldo, "1"), (27.6, 12.95), (co, "2")], width=0.3)
    t.via("V33", 28.4, 12.95)
    t.gnd_stub(ldo, "3", (29.113, 15.3), sym=(0, 0))
    t.gnd_stub(ldo, "7", (30.0, 13.6), sym=(0, 0), fine=True)
    t.gnd_stub(ci, "2", (32.4, 11.9), sym=(0, 0))
    t.gnd_stub(co, "1", (27.6, 15.5), sym=(0, 0))
    t.text(35.2, 2.6, id, 1.2, 0.2, "center")
    t.text(35.2, 4.3, "TRF3722", 0.8, 0.15, "center")
    t.text(35.2, 5.65, "I/Q MODULATOR", 0.8, 0.15, "center")
    t.text(35.2, 7.0, "0.4-4.2 GHz", 0.8, 0.15, "center")
    t.result = "I + jQ from two DACs on 0.4-4.2 GHz, about -3 dBm, image-free (-42 dBc untrimmed)"
    t.notes = ["TRF3722 (PLL, VCO, I/Q modulator) on SPI from the Pmod (LE IO6, readback IO5); reference from R10's REF IN.  Each DAC:",
               "56 ohm at the jack, 270 ohm to a node held at 0.25 V (+-0.25 V for +-1 V).  DC on I alone is a CW carrier."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


def tile_r13():
    return trf_tile("R13", [(2, 3), (3, 3)])


# -------------------------------------------------------------------------------------------------------- R7, R8 --
def mixer_tile(id, cells, name):
    """An ADL5350 passive mixer on two cells, used either way: RF at the top-left jack, LO at the right cell's top-left one, IF at
    the bottom-right (the checkerboard: every jack 14.85 mm or more from every other).  The chip's RF and IF pins are one node; a crossover separates them (the datasheet's Figure 63 scaled to
    a 200 MHz corner): 15 pF series and 47 nH shunt toward the RF jack, 47 nH series and 15 pF shunt toward the IF, then
    100 nF to the IF jack, so one tile serves 915 MHz and 2.4 GHz with an IF anywhere the ADC reaches.  The LO goes in
    through 0 ohm (fit 3-8 nH to tune a band) and 100 pF; the LO buffer's bias comes through 10 nH from the tile's 3.3 V
    (TPS7A2033 behind the switch and FET in the right cell).  Pins 4 and 7 (no connect) are grounded as the datasheet
    recommends; the paddle has its via; the IF line crosses the header's cell on the back."""
    t = Tile(id, name, cells, supply="+5 V", subtitle="ADL5350", sections=[], kind="rf")
    t.top_pour = True
    t.fine = True
    t.pwr_flags = ["VPOS"]                                                               # fed through the choke, not by a regulator pin
    jrf = t.jack("TL", "RF", "RFN", "in", "+10 dBm", silk="RF")
    jlo = t.jack("TL1", "LO", "LOJ", "in", "0 to +6 dBm", silk="LO")
    jif = t.jack("BR", "IF", "IF", "out", "", silk="IF")
    power_header(t, rail="+5V", dx=20.0)
    ldo = t.add("U", "TPS7A2033", "3.3V", 30.5, 14.0, 0, {"1": "VS", "2": "GND", "3": "VS", "5": "V33"}, hide_value=False, label=None)
    ci = t.add("C", "C0805 1uF", "1u", 27.5, 10.9, 0, {"1": "VS", "2": "GND"}, label=None)
    co = t.add("C", "C0805 4.7uF", "4.7u", 31.4, 10.6, 0, {"1": "V33", "2": "GND"}, label=None)
    t.route("VS", [("Q%d01" % t.idx, "3"), (ldo, "3")])
    t.route("VS", [(ldo, "1"), (ldo, "3")])
    t.route("VS", [(ldo, "1"), (ci, "1")])
    t.gnd_stub(ldo, "2", (28.1, 14.0), sym=(0, 0))
    t.gnd_stub(ci, "2", (28.45, 9.8), sym=(0, 0))                    # no symbol: the LO jack's leg is above it
    t.gnd_stub(co, "2", (33.3, 10.6), sym=(0, 0))
    t.wire("V33", [(ldo, "5"), (31.6375, 11.4), (30.55, 11.4), (30.55, 12.6)])
    t.wire("V33", [(co, "1"), (30.55, 11.4)])
    t.via("V33", 30.55, 12.6)
    F = 0.15
    u = t.add("U", "ADL5350", "ADL5350", 12.5, 10.0, 0, {"1": "RFIF", "8": "RFIF", "3": "LON", "6": "VPOS", "2": "GND", "5": "GND", "4": "GND", "7": "GND", "9": "GND"},
              hide_value=False, label=None)
    t.gnd_stub(u, "9", (12.5, 10.0), sym=(0, 0), fine=True)                              # the paddle's via
    for n in ("2", "4", "5"):                                                            # the ground pins into the paddle
        t.wire("GND", [(u, n), (12.249 if n == "2" else 13.249, 10.0)], width=F)
    t.gnd_stub(u, "7", [(12.249, 11.55), (11.9, 11.9)], sym=(0, 0), width=F, fine=True)
    t.wire("RFIF", [(u, "1"), (11.2, 9.098), (11.2, 10.902), (u, "8")], width=0.2)
    # the RF side: 15 pF series, 47 nH shunt, the 50 ohm line down from the jack
    c1 = t.add("C", "C0402 15pF", "15p", 9.7, 10.0, 0, {"1": "RFN", "2": "RFIF"}, label=None)
    l1 = t.add("L", "L0402 47nH", "47n", 8.2, 11.4, 270, {"1": "RFN", "2": "GND"}, label=None)        # pad 1 up
    t.wire("RFIF", [(c1, "2"), (11.2, 10.0)], width=0.2)
    t.rf("RFN", [(jrf, "1"), (4.75, 10.0), (c1, "1")])
    t.wire("RFN", [(8.2, 10.0), (l1, "1")], width=0.2)
    t.gnd_stub(l1, "2", (8.2, 12.7), sym=(0, 0), fine=True)
    # the IF side: 47 nH series, 15 pF shunt, 100 nF block, then across the tile on the back to the IF jack
    l2 = t.add("L", "L0402 47nH", "47n", 11.2, 13.0, 270, {"1": "RFIF", "2": "IFN"}, label=None)       # pad 1 up
    c2 = t.add("C", "C0402 15pF", "15p", 12.1, 15.0, 270, {"1": "IFN", "2": "GND"}, label=None)
    c6 = t.add("C", "C0402 100nF", "100n", 14.6, 14.1, 0, {"1": "IFN", "2": "IF"}, label=None)
    t.wire("RFIF", [(11.2, 10.902), (l2, "1")], width=0.2)
    t.wire("IFN", [(l2, "2"), (11.2, 14.1), (12.1, 14.1), (c2, "1")], width=0.2)
    t.wire("IFN", [(12.1, 14.1), (c6, "1")], width=0.2)
    t.gnd_stub(c2, "2", (12.1, 16.4), sym=(0, 0), fine=True)
    t.via("IF", 17.0, 14.1)
    t.wire("IF", [(c6, "2"), (17.0, 14.1)], width=0.25)
    t.wire("IF", [(17.0, 14.1), (17.0, 15.7), (33.0, 15.7), (33.0, 15.25), (jif, "1")], width=0.25, layer="B.Cu", silk=False)
    # the LO: 0 ohm (a band's inductor if wanted), 100 pF, the 50 ohm line along y 8.9 and up into the right cell's jack
    l3 = t.add("R", "R0402 0R", "0R", 15.3, 8.9, 0, {"1": "LON", "2": "LOC"}, label=None)
    c3 = t.add("C", "C0402 100pF", "100p", 17.3, 8.9, 0, {"1": "LOC", "2": "LOJ"}, label=None)
    t.wire("LON", [(u, "3"), (12.749, 8.2), (14.79, 8.2), (l3, "1")], width=F)
    t.wire("LOC", [(l3, "2"), (c3, "1")], width=0.2)
    t.rf("LOJ", [(c3, "2"), (26.25, 8.9), (jlo, "1")])
    # the LO buffer's supply: 10 nH from 3.3 V, 100 pF at the pin
    l4 = t.add("L", "L0402 10nH", "10n", 12.75, 12.6, 270, {"1": "VPOS", "2": "V33"}, label=None)      # pad 1 up
    c4 = t.add("C", "C0402 100pF", "100p", 14.3, 12.0, 0, {"1": "VPOS", "2": "GND"}, label=None)
    t.wire("VPOS", [(u, "6"), (l4, "1")], width=F)
    t.wire("VPOS", [(12.75, 11.5), (13.69, 11.5), (c4, "1")], width=F)
    t.gnd_stub(c4, "2", (15.5, 12.0), sym=(0, 0), fine=True)
    t.via("V33", 13.3, 13.6, fine=True)
    t.wire("V33", [(l4, "2"), (12.75, 13.6), (13.3, 13.6)], width=F)
    t.wire("V33", [(30.55, 12.6), (14.0, 12.6), (13.3, 13.3), (13.3, 13.6)], width=0.2, layer="B.Cu", silk=False, fine=True)
    t.text(1.2, 13.3, id, 1.0, 0.18, "left")
    t.text(1.2, 14.6, "ADL5350", 0.8, 0.15, "left")
    t.text(1.2, 15.9, name.upper(), 0.8, 0.15, "left")
    t.result = "RF x LO to IF (or IF x LO to RF) with 7-9 dB of loss from 400 MHz to 2.5 GHz and an IF of 0.1-30 MHz; +4 dBm of LO is enough"
    t.notes = ["ADL5350: a GaAs FET switch mixer with its own LO buffer; the RF and IF pins are one node, split by a crossover",
               "(series 15 pF + shunt 47 nH toward RF, series 47 nH + shunt 15 pF toward IF, corner 200 MHz) in place of the",
               "datasheet's band-tuned tanks: a few dB more loss, every band at once.  The LO's series element is 0 ohm (fit the",
               "datasheet's 3-8 nH for one band); the LO bias choke is 10 nH (the datasheet: 24 nH at 780 MHz, 2 nH at 2 GHz).",
               "Passive, so the same tile up-converts a DAC tone (IF in, RF out) or down-converts an antenna's signal (RF in, IF out).",
               "Both images appear: filter the RF side with R2 or R4."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


def tile_r7():
    return mixer_tile("R7", [(0, 2), (1, 2)], "TX mixer")


def tile_r8():
    return mixer_tile("R8", [(2, 2), (3, 2)], "RX mixer")


# ------------------------------------------------------------------------------------------------------------ R1 --
def tile_r1():
    """A resistive three-port splitter and combiner: 18 ohm from each jack to one node (50/3 ohm would be exact), 6 dB from
    any port to any other, matched at every port, DC to 6 GHz.  One reference or LO feeds two tiles; two tones combine
    for an intermodulation test on a gain block; a 6 dB pad between any two ports.  The 915 MHz antenna the plan put
    here is rev B (the handbook says why)."""
    t = Tile("R1", "splitter", [(0, 0), (1, 0)], subtitle="3 x 18 ohm, 6 dB", sections=[], kind="rf")
    t.top_pour = True
    j1 = t.jack("TL", "P1", "P1", "in", "+20 dBm", silk="P1")
    j2 = t.jack("TM", "P2", "P2", "out", "", silk="P2")
    j3 = t.jack("BR", "P3", "P3", "out", "", silk="P3")
    r1 = t.add("R", "R0402 18R", "18R", 15.0, 10.0, 0, {"1": "P1", "2": "N"}, label=None)
    r2 = t.add("R", "R0402 18R", "18R", 17.0, 10.0, 0, {"1": "N", "2": "P2"}, label=None)
    r3 = t.add("R", "R0402 18R", "18R", 16.0, 11.6, 270, {"1": "N", "2": "P3"}, label=None)            # pad 1 up
    t.rf("P1", [(j1, "1"), (4.75, 10.0), (r1, "1")])
    t.rf("P2", [(j2, "1"), (20.75, 10.0), (r2, "2")])
    t.rf("P3", [(r3, "2"), (16.0, 15.25), (36.75, 15.25), (j3, "1")])
    t.wire("N", [(r1, "2"), (r2, "1")], width=0.25)
    t.wire("N", [(16.0, 10.0), (r3, "1")], width=0.25)
    t.text(1.2, 13.3, "R1", 1.0, 0.18, "left")
    t.text(1.2, 14.6, "SPLITTER / COMBINER", 0.8, 0.15, "left")
    t.text(1.2, 17.3, "ANY PORT TO ANY: -6 dB", 0.8, 0.15, "left")
    t.text(1.2, 18.6, "3 x 18R, DC - 6 GHz", 0.8, 0.15, "left")
    t.result = "6.2 dB from any port to either other port, every port within 2 ohm of 50, DC to 6 GHz (the resistors' parasitics set the top)"
    t.notes = ["Three 18 ohm resistors to one node: the textbook resistive divider, 6 dB per path and no isolation between the two",
               "outputs beyond those 6 dB (a Wilkinson would give 3 dB and 20 dB of isolation, at one band).  Feed R9's REF OUT to",
               "both synthesizers' REF IN, one synthesizer's OUT A to both mixers, or two tones into one gain block."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


def tiles():
    return [tile_r1(), tile_r2(), tile_r4(), tile_r5(), tile_r12(), tile_r9(), tile_r7(), tile_r8(), tile_r10(), tile_r13()]


PMOD_NAMES = {"/PMOD6": "LE of R13 (TRF3722)", "/PMOD5": "readback of R13", "/PMOD4": "LE of R10", "/PMOD3": "SCLK to R10 and R13",
              "/PMOD2": "SDATA to R10 and R13", "/PMOD1": "MUXOUT of R10"}
HANDBOOK_INTRO = [
    "Ten tiles on sixteen 20 mm cells, four layers, USB-C power on R9.  Every tile's input is its top-left jack and its output its",
    "bottom-right jack, so neighbouring jacks are at least 14.85 mm apart.  Every 50 ohm line is coplanar waveguide (0.29 mm on",
    "0.21 mm of prepreg over ground, 0.25 mm gaps, a via fence) and every jack's centre pin has no plane under it.  The powered",
    "tiles have the AMOD-A slide switch (up: on) and P-FET.  Rev A built what JLCPCB stocked on 2026-10-25: a QPL9547 LNA and a",
    "GALI-84+ gain block, two ADL5350 mixers, a MAX2871 synthesizer and a TRF3722 quadrature transmitter fed by the ECP5 board's",
    "two DACs.  The printed antennas moved off the board (see the end of this handbook)."]
HANDBOOK_SECTIONS = [
    ["## The tiles together", "",
     "The board is one end of a radio link, or both ends on a cable.  One 25 MHz reference drives everything, so every",
     "frequency on the board is locked to every other and phase means something.",
     "",
     "1. **Reference.**  R9's REF OUT into R10's REF IN (the ECP5 board's CLK OUT works as well); a trace on the back takes it",
     "   on to R13's TRF3722, so both synthesizers share it.  R1 splits it to a second board.",
     "2. **Transmitter, image-free.**  The ECP5 board's DAC 1 into R13's I IN and DAC 2 into Q IN (+-1 V into 50 ohm each); R13's",
     "   RF OUT through R2 (2.45 GHz) or R4 (915 MHz), then R12 for 20 dB if a cable needs it.  Chapter 6's waveforms with",
     "   no image: the sideband suppression is about 42 dB untrimmed, better after the DACs' gain and phase are trimmed.",
     "3. **Receiver.**  The antenna or cable into R5 (the QPL9547: 0.3 dB of noise figure, 19.5 dB of gain), then R4 or R2, then",
     "   R8's RF; R10 into R8's LO; R8's IF into an ADC.  R7 is a second, identical mixer: on R10's output through R1 it is a",
     "   second coherent receive channel (direction finding), or a transmit mixer for a real IF.",
     "4. **Instruments.**  R10 or R13 alone is a signal generator; R13 at f (a DC on I) and R10 at f - IF into R8 is a network",
     "   analyzer and a stepped-frequency radar on one reference; R10 swept into R8 behind R5 is a spectrum analyzer that sees",
     "   Wi-Fi, Bluetooth and LoRa; two tones from R13's I and Q into R12 show its intermodulation.",
     "",
     "Levels to remember: a synthesizer gives -4 to +5 dBm; R13 gives about -3 dBm at full scale; an ADL5350 wants +4 dBm of LO",
     "and loses 7-9 dB; a GALI-84+ gives 20 dB and compresses at +20 dBm out; the QPL9547 takes no more than +22 dBm at its input",
     "(put 30 dB of attenuation before it on any cable from a transmitter); the filters lose 1-2 dB; the splitter 6 dB."],
    ["## Antennas", "",
     "The plan's printed inverted-F antennas (TI DN023 at 915 MHz, AN043 at 2.4 GHz) need bare board on every layer for a",
     "quarter of the board and a pi network tuned on the bench, and TI's dimensions are for their stack, not this one.  Use",
     "SMA whip antennas on R12's OUT and R5's IN instead (a 2.4 GHz 'rubber duck' is $2; 915 MHz ones are as cheap), or make",
     "a monopole from a jack and 31 mm (2.4 GHz) or 78 mm (915 MHz) of wire."],
]


GND_LOOPS = [(3.0, 30.0), (3.0, 70.0), (97.0, 50.0), (97.0, 84.0)]
# no mounting holes: the Pmod plug fills the bottom-left corner where one stood, and a board plugged into a host's Pmod is
# held by the plug.  Four stick-on rubber feet instead, circled on the back (the bottom-left one above the plug's pins).
HOLES = []
FEET = [(5.0, 5.0), (95.0, 5.0), (95.0, 95.0), (5.0, 85.0)]
SLOTS = []
# the rails on L3: +5 V under the whole board; +7.8 V in the gutter under row 1, from R9's vias to the gain blocks' headers
def _island(c0):
    """A synthesizer's V33 island on L3: under its chip and LDO, inside the tile at column c0 of row 3."""
    x0, y0 = G.cell_origin(c0, 3)
    return (x0 + 9.0, y0 + 2.0, x0 + 31.5, y0 + 18.4)


RAIL_POURS = [("+5V", 0.6, 0.6, 99.4, 99.4, 0),
              ("+8V", 30.0, 49.25, 93.0, 50.75, 1),              # R12 only: R5 is the 5 V QPL9547
              ("/R10_V33", *_island(0), 2),
              ("/R13_V33", G.cell_origin(2, 3)[0] + 8.5, G.cell_origin(2, 3)[1] + 1.6, G.cell_origin(2, 3)[0] + 33.0, G.cell_origin(2, 3)[1] + 18.4, 2)]
_R10, _R13 = G.cell_origin(0, 3), G.cell_origin(2, 3)
# R13's SDATA and SCLK up the gutter between R10 and R13 and along the gutter above row 3 into R10's vias (the
# outer line turns last: no crossing); its LE down to the bottom edge and into the plug's pad 9 on the back, its
# readback the same way on the front into pad 11; the 25 MHz from a via on R10's REF IN trace down R10's middle gutter
# and along the bottom margin to R13
BACK_WIRES = [("/PMOD3", [(_R13[0] - 0.45, _R13[1] + 13.2), (_R13[0] - 0.45, 71.1), (_R10[0] + 16.1, 71.1), (_R10[0] + 16.1, _R10[1] + 5.6)]),
              ("/PMOD2", [(_R13[0] - 1.05, _R13[1] + 12.7), (_R13[0] - 1.05, 71.5), (_R10[0] + 16.6, 71.5), (_R10[0] + 16.6, _R10[1] + 2.4)]),
              ("/PMOD6", [(_R13[0] + 8.6, _R13[1] + 12.2), (_R13[0] + 8.6, 99.25), (_R10[0] + 6.78, 99.25), (_R10[0] + 6.78, _R10[1] + 25.52)]),
              ("/REF25", [(_R10[0] + 20.75, _R10[1] + 11.3), (_R10[0] + 20.75, 93.25), (_R13[0] + 3.0, 93.25), (_R13[0] + 3.0, _R13[1] + 20.6)])]
FRONT_WIRES = [("/PMOD5", [(_R13[0] + 7.0, _R13[1] + 20.6), (_R13[0] + 7.0, 99.05), (_R10[0] + 9.32, 99.05), (_R10[0] + 9.32, _R10[1] + 25.52)])]
FRONT_TEXT = []
BACK_TEXT_X = 50.0
QR_AT = (80.0, 40.5)              # under R9's right cell: the boost and the USB-C input, no jack within 10 mm
BACK_TEXT = ["RF-MOD: 915 MHz and 2.4 GHz.  IN is each tile's top-left",
             "jack, OUT its bottom-right; the powered tiles have a slide",
             "switch (up: on).  Power: USB-C on R9.  The handbook has",
             "the rest."]


if __name__ == "__main__":
    ts = tiles()
    cells = [c for t in ts for c in t.cells]
    assert len(set(cells)) == len(cells), cells
    jacks = [(t.id + " " + j["label"], *t.to_board((j["x"], j["y"]))) for t in ts for j in t.jacks]
    bad = G.check_spacing(jacks)
    import math
    dmin = min(math.hypot(a[1] - b[1], a[2] - b[2]) for i, a in enumerate(jacks) for b in jacks[i + 1:])
    print("%d tiles, %d cells, %d jacks (closest pair %.2f mm), %d parts; jack pairs closer than %.1f mm: %s"
          % (len(ts), len(cells), len(jacks), dmin, sum(len(t.parts) for t in ts), G.MIN_JACK_SPACING, bad or "none"))
    for t in ts:
        print("  %-4s %-16s %2d parts  %s" % (t.id, t.name, len(t.parts), t.result[:90]))
