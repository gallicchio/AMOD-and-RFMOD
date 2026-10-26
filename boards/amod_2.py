"""AMOD-2: HF, magnetic resonance and the reflectometer, rev A.  The second-level HF board, for the ECP5-2ADC-2DAC board,
whose converters sample DC to 30 MHz directly: a 1 W pulse amplifier and a duplexer with a low-noise preamplifier for pulsed
NMR, a coil driver for gradients and Helmholtz pairs, a two-channel HF receiver front end, VLF loop amplifiers, a 50 ohm
reflection bridge for complex S11, coupled and parametric resonators, a switched noise source and a laser driver with an RF
bias-T.  Four layers: L1 parts and drawn wires, L2 ground, L3 the rails (+5 V everywhere, -5 V in the gutter under row 0),
L4 ground with the back-side text; +-15 V only reach the pulse amplifier, on the back from Y1 below it.

Designed for Prompt 13 (the second-level boards, for the ECP5-2ADC-2DAC board).  PLAN_LEVEL2.md section 3 has the reasons and
the changes from Appendix D's first AMOD-2 (the optics tiles moved to a future board).
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, HERE)
import tiles as T
from tiles import Tile, power_header, HDR_VS
import geometry as G
import amod_a

STEM = "amod_2"
LAYERS = 4
USB_X = 100.0 - 2.45
F = 0.15


def gnd(t, ref, pad, pt, w=0.25):
    """A ground stub to a small via, no symbol (the tiles are dense)."""
    t.gnd_stub(ref, pad, pt, sym=(0, 0), width=w, fine=True)


# ------------------------------------------------------------------------------------------------------------ Y2 --
def tile_y2():
    """The pulse amplifier: a THS3491 (VQFN-16 at (12.0, 8.5), rot 0: FB, -IN, +IN down its left, VOUT on its right, +VS on top,
    -VS along the bottom) at gain 10.3 (698 ohm from its FB pin, which is the output, to -IN; 75 ohm to ground) from +-15 V.  IN is
    terminated in 49.9 ohm, so a DAC's +-1 V into 50 ohm becomes +-10 V into a 50 ohm load: 1 W.  OUT is not back-terminated (it
    drives the T/R switch and the probe).  PD from Pmod IO1 through 4.7 k, 10 k to ground: off unless the FPGA holds it high, so it
    is silent between pulses; it heats if left on at full power (pulse it).  +-15 V come up the back from Y1."""
    t = Tile("Y2", "pulse amplifier", [(2, 0)], supply="+-15 V", subtitle="THS3491", sections=[])
    jin = t.jack("TL", "IN", "IN", "in", "+-1 V", silk="IN")
    jout = t.jack("BR", "OUT", "OUT", "out", "+-10 V into 50 ohm", silk="OUT")
    pins = {"1": "FBO", "3": "INN", "4": "IN", "5": "GND", "7": "-15V", "8": "-15V", "10": "OUT", "11": "OUT", "13": "+15V", "14": "+15V",
            "16": "PD", "17": "GND"}
    u = t.add("U", "THS3491", "THS3491", 12.0, 8.5, 0, pins, hide_value=False, label=None)
    for (vx, vy) in ((11.6, 8.1), (12.4, 8.1), (11.6, 8.9), (12.4, 8.9)):
        t.gnd_stub(u, "17", (vx, vy), sym=(0, 0), width=F, fine=True)
    t.wire("GND", [(u, "5"), (11.25, 9.3)], width=F)
    # feedback: 698 ohm from FB (the output) to -IN beside it, 75 ohm from -IN to ground
    rf = t.add("R", "R0402 698R", "698", 9.3, 8.25, 90, {"1": "INN", "2": "FBO"}, label=None)                 # pad 1 down
    rg = t.add("R", "R0402 75R", "75", 7.8, 8.9, 0, {"1": "GND", "2": "INN"}, label=None)
    t.wire("FBO", [(u, "1"), (rf, "2")], width=0.2)
    t.wire("INN", [(u, "3"), (rf, "1")], width=0.2)
    t.wire("INN", [(rg, "2"), (9.3, 8.9)], width=0.2)
    gnd(t, rg, "1", (6.4, 8.9))
    # IN: down from the jack, along y 10.3, up into +IN; 49.9 ohm to ground on the way
    t.wire("IN", [(jin, "1"), (4.75, 10.3), (9.9, 10.3), (10.4, 9.8), (u, "4")], width=0.25)
    rt = t.add("R", "R0402 49.9R", "49.9", 6.0, 11.3, 90, {"1": "GND", "2": "IN"}, label=None)               # pad 2 up
    t.wire("IN", [(6.0, 10.3), (rt, "2")], width=0.25)
    gnd(t, rt, "1", (6.0, 12.7))
    # OUT: the two VOUT pins to the right, down between the OUT jack's legs
    t.wire("OUT", [(u, "11"), (13.875, 8.25), (13.875, 8.75), (u, "10")], width=0.25)
    t.wire("OUT", [(13.875, 8.5), (14.6, 8.5), (15.25, 9.15), (jout, "1")], width=0.5)
    # +15 V: the pair on top to a bus along y 6.0 with 100 nF and 10 uF, a via at its end for Y1's line up the back
    t.wire("+15V", [(u, "14"), (12.25, 6.0), (19.6, 6.0)], width=0.25)
    t.wire("+15V", [(u, "13"), (12.75, 6.0)], width=0.25)
    cp1 = t.add("C", "C0402 100nF", "100n", 13.6, 5.0, 270, {"1": "GND", "2": "+15V"}, label=None)            # pad 1 up
    cp2 = t.add("C", "C0805 10uF", "10u", 16.0, 4.9, 270, {"1": "GND", "2": "+15V"}, label=None)
    t.wire("+15V", [(13.6, 6.0), (cp1, "2")], width=0.25)
    t.wire("+15V", [(16.0, 6.0), (cp2, "2")], width=0.4)
    gnd(t, cp1, "1", (13.6, 3.9))
    gnd(t, cp2, "1", (16.0, 2.6), w=0.4)
    t.via("+15V", 19.6, 6.0)
    # -15 V: the pair below to 100 nF beside them and 10 uF to the left, a via where Y1's line arrives up the back
    cn1 = t.add("C", "C0402 100nF", "100n", 11.2, 11.6, 90, {"1": "GND", "2": "-15V"}, label=None)              # pad 2 up
    cn2 = t.add("C", "C0805 10uF", "10u", 8.6, 12.4, 0, {"1": "GND", "2": "-15V"}, label=None)
    t.wire("-15V", [(u, "7"), (12.25, 10.75), (11.2, 10.8), (cn1, "2")], width=0.25)
    t.wire("-15V", [(u, "8"), (12.75, 10.6), (12.25, 10.6)], width=0.25)
    t.wire("-15V", [(cn1, "2"), (9.55, 11.12), (cn2, "2")], width=0.4)
    gnd(t, cn1, "1", (11.2, 13.0), w=0.2)
    gnd(t, cn2, "1", (7.65, 13.6), w=0.4)
    t.via("-15V", 9.55, 13.75)
    t.wire("-15V", [(cn2, "2"), (9.55, 13.75)], width=0.4)
    # PD: 4.7 k from Pmod IO1 (along the top from the gutter on the left), 10 k to ground
    rpd = t.add("R", "R0402 10k", "10k", 9.7, 5.6, 0, {"1": "GND", "2": "PD"}, label=None)
    rs = t.add("R", "R0402 4.7k", "4.7k", 11.25, 4.3, 90, {"1": "PD", "2": "/PMOD1"}, label=None)              # pad 1 down
    t.wire("PD", [(u, "16"), (11.25, 5.6), (rpd, "2")], width=F)
    t.wire("PD", [(11.25, 5.6), (rs, "1")], width=F)
    gnd(t, rpd, "1", (8.3, 5.6), w=0.2)
    t.wire("/PMOD1", [(-0.75, 0.6), (11.25, 0.6), (rs, "2")], width=F, silk=False)
    t.text(1.2, 15.6, "Y2", 1.2, 0.2, "left")
    t.text(1.2, 17.2, "1 W PULSE", 0.8, 0.15, "left")
    t.text(1.2, 18.5, "IO1: ON", 0.8, 0.15, "left")
    t.result = "gain 10.3 to 30 MHz: a DAC's +-1 V to +-10 V into 50 ohm (1 W); off (PD low) unless Pmod IO1 is high"
    t.notes = ["TI THS3491, current feedback, 900 MHz and 420 mA from +-15 V.  698 ohm from the FB pin (the output, inside) to -IN and",
               "75 ohm to ground set gain 10.3.  The 49.9 ohm input termination makes the DAC's +-1 V into 50 ohm the full +-10 V output.",
               "PD from Pmod IO1 (4.7 k, 10 k to ground): high = on.  Pulse it: 1 W continuous heats the 3 x 3 mm package past its limit."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ Y3 --
def tile_y3():
    """NMR's duplexer and preamplifier, two cells.  Left: TX IN through two pairs of crossed 1N4148W diodes to PROBE: the pulse
    passes (1.4 V drop), the transmitter's noise between pulses does not.  Right: LINE (from the probe through a quarter-wave
    cable, or a short cable and a 6 dB pad) clamped to ground by crossed diodes and terminated in 49.9 ohm, into AMOD-A's
    op-amp tile with an OPA847 at gain 12 (1.1 k / 100 ohm), 49.9 ohm out to RX OUT.  With the quarter-wave line the clamp
    shorts its far end during the pulse, so the probe sees an open there; between pulses the echo reaches the preamplifier."""
    t = Tile("Y3", "duplexer and preamp", [(0, 0), (1, 0)], supply="+5 V", subtitle="OPA847", sections=[])
    jtx = t.jack("TL0", "TX IN", "TX", "in", "+-15 V", silk="TX IN")
    jpr = t.jack("BR0", "PROBE", "PRB", "out", "", silk="PROBE")
    jln = t.jack("TL1", "LINE", "IN", "in", "", silk="LINE")
    jrx = t.jack("BR1", "RX OUT", "OUT", "out", "", silk="RX OUT")
    power_header(t, rail="+5V")
    # the transmit diodes: TX -> M -> PRB, each step an anti-parallel pair
    d1a = t.add("D", "D1N4148", "1N4148W", 11.0, 2.9, 180, {"1": "M", "2": "TX"}, label=None)              # rot 180: cathode at +x
    d1b = t.add("D", "D1N4148", "1N4148W", 11.0, 5.4, 0, {"1": "TX", "2": "M"}, label=None)
    d2a = t.add("D", "D1N4148", "1N4148W", 13.3, 9.0, 90, {"1": "PRB", "2": "M"}, label=None)              # rot 90: cathode down
    d2b = t.add("D", "D1N4148", "1N4148W", 15.8, 9.0, 270, {"1": "M", "2": "PRB"}, label=None)             # rot 270: cathode up
    t.wire("TX", [(jtx, "1"), (8.75, 4.75)], width=0.5)
    t.wire("TX", [(8.75, 2.9), (8.75, 5.4)], width=0.5)
    t.wire("TX", [(8.75, 2.9), (d1a, "2")], width=0.5)
    t.wire("TX", [(8.75, 5.4), (d1b, "1")], width=0.5)
    t.wire("M", [(d1a, "1"), (13.3, 2.9), (13.3, 6.6), (d2a, "2")], width=0.5)
    t.wire("M", [(d1b, "2"), (13.3, 5.4)], width=0.5)
    t.wire("M", [(13.3, 6.6), (15.8, 6.6), (d2b, "1")], width=0.5)
    t.wire("PRB", [(d2a, "1"), (13.3, 11.2), (15.8, 11.2), (d2b, "2")], width=0.5)
    t.wire("PRB", [(15.25, 11.2), (jpr, "1")], width=0.5)
    # the receive side: LINE clamped by crossed diodes, 49.9 ohm, into the OPA847 tile
    d3a = t.add("D", "D1N4148", "1N4148W", 25.0, 9.6, 0, {"1": "GND", "2": "IN"}, label=None)
    d3b = t.add("D", "D1N4148", "1N4148W", 25.0, 12.1, 180, {"1": "IN", "2": "GND"}, label=None)
    t.wire("IN", [(jln, "1"), (26.25, 9.0), (27.4, 9.0), (27.4, 12.1), (d3b, "1")])
    t.wire("IN", [(27.4, 9.6), (d3a, "2")])
    gnd(t, d3a, "1", (22.3, 9.6))
    gnd(t, d3b, "2", (22.3, 12.1))
    rt = t.add("R", "R0402 49.9R", "49.9", 29.2, 12.1, 0, {"1": "IN", "2": "GND"}, label=None)
    t.wire("IN", [(27.4, 12.1), (rt, "1")], width=0.25)
    gnd(t, rt, "2", (30.8, 11.9))
    t.wire("VS", [HDR_VS, (8.54, 19.6), (31.7, 19.6), (31.7, 18.1)], width=0.35, silk=False)
    amod_a.opa_tile_br(t, "R0603 100R", "100R", chip="OPA847", rf_key="R0603 1.1k", jack_in=False, dx=21.5, neg="bottom",
                       in_from=[(27.4, 9.0), (30.5, 9.0), (30.5, 4.75)], legend=False, loop=False, vs_from_header=False)
    t.text(1.2, 9.4, "Y3", 1.2, 0.2, "left")
    t.text(4.1, 9.4, "DUPLEXER", 0.8, 0.15, "left")
    t.text(22.0, 17.3, "x12 OPA847", 0.8, 0.15, "left")
    t.result = ("TX IN passes to PROBE through 1.4 V of diodes; the echo at LINE gains 12 (OPA847, 0.85 nV/rtHz) to RX OUT, about 200 MHz "
                "wide; LINE is clamped to +-0.7 V and terminated in 50 ohm")
    t.notes = ["The classic pulsed-NMR duplexer, broadband except for its one cable: crossed diodes in series with the transmitter, and a",
               "quarter wave of coax from PROBE to LINE (2.6 m of RG-316 at 20 MHz) whose far end the clamp diodes short during the pulse.",
               "Between pulses the diodes are off: the PA's noise does not reach the probe, the echo reaches the OPA847 (1.1 k / 100 ohm:",
               "x12, its minimum stable gain).  Without the cable, a short one and a 6 dB pad work at a few dB of loss."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------- the LMH6629 amp --
def lmh_amp(t, dx=0.0, jack_in=True, in_from=None, term=True, chip="LMH6629", rf=("R0402 240R", "240"), rg=("R0402 27R", "27"),
            rb=("R0402 10k", "10k"), cf=None):
    """A single-supply LMH6629 at gain 9.9 (240 ohm / 27 ohm, the 27 ohm to ground through 1 uF so the output sits at the
    bias) in a cell's top-right quarter.  The IN line along y 4.75: 49.9 ohm to ground (the termination), 1 uF in series,
    +IN biased at half the supply by 10 k / 10 k above the line.  The op amp at (13.2, 6.9), rot 270 (+IN, V-, OUT along the
    top, -IN and V+ along the bottom); OUT round its right side at x 15.1 to Rf under it and to 1 uF and 49.9 ohm into the OUT
    jack at the cell's bottom-right.  VS comes up the back from a via at (10.2, 18.1) that the tile feeds.  term=False leaves
    out the 49.9 ohm termination (a source on the tile drives the line).  `chip`, `rf`, `rg`, `rb` (the bias pair) and `cf` (a
    capacitor across Rf, under it) re-use the core for other gains (Y6)."""
    X = lambda x: x + dx
    sfx = "" if dx == 0 else "B"
    IN, IN2, OUTA, FBN, OUTC, OUT = ("IN" + sfx, "IN2" + sfx, "OA" + sfx, "FB" + sfx, "OC" + sfx, "OUT" + sfx)
    if term:
        rt = t.add("R", "R0402 49.9R", "49.9", X(8.9), 6.1, 270, {"1": IN, "2": "GND"}, label=None)             # pad 1 up
    cin = t.add("C", "C0402 1uF", "1u", X(10.4), 4.75, 0, {"1": IN, "2": IN2}, label=None)
    if jack_in:
        jref = [j["ref"] for j in t.jacks if j["slot"] in (("TL", "TL0") if dx == 0 else ("TL1",))][0]
        t.wire(IN, [(jref, "1"), (cin, "1")], width=0.25)
    else:
        t.wire(IN, list(in_from) + [(cin, "1")], width=0.25)
    if term:
        t.wire(IN, [(X(8.9), 4.75), (rt, "1")], width=0.25)
        t.gnd_stub(rt, "2", (X(8.9), 7.4), sym=(0, 0), width=0.2, fine=True)
    u = t.add("U", chip, chip, X(13.2), 6.9, 270, {"1": OUTA, "2": "GND", "3": IN2, "4": FBN, "5": "VS"}, hide_value=False, label=None)
    t.wire(IN2, [(cin, "2"), (X(12.25), 4.75), (u, "3")], width=0.25)
    rb1 = t.add("R", rb[0], rb[1], X(11.6), 3.3, 90, {"1": IN2, "2": "VS"}, label=None)                        # pad 1 down
    rb2 = t.add("R", rb[0], rb[1], X(12.65), 3.3, 270, {"1": "GND", "2": IN2}, label=None)                     # pad 2 down
    t.wire(IN2, [(X(11.6), 4.75), (rb1, "1")], width=0.2)
    t.wire(IN2, [(rb2, "2"), (X(12.4), 4.4), (X(12.25), 4.75)], width=0.2)
    t.gnd_stub(rb2, "1", (X(12.65), 1.6), sym=(0, 0), width=0.2, fine=True)
    t.via("VS", X(11.6), 1.6, fine=True)
    t.wire("VS", [(rb1, "2"), (X(11.6), 1.6)], width=0.2)
    t.gnd_stub(u, "2", (X(13.4), 4.4), sym=(0, 0), width=0.2, fine=True)
    # the output: up and round the right side at x 15.1 to Rf under the op amp and to 1 uF and 49.9 ohm down into the jack
    rf_ = t.add("R", rf[0], rf[1], X(13.6), 10.2, 0, {"1": FBN, "2": OUTA}, label=None)
    t.wire(OUTA, [(u, "1"), (X(14.15), 4.5), (X(15.1), 4.5), (X(15.1), 10.2), (rf_, "2")], width=0.2)
    rg_ = t.add("R", rg[0], rg[1], X(11.05), 10.9, 270, {"1": FBN, "2": "CG" + sfx}, label=None)                # pad 1 up
    cg = t.add("C", "C0402 1uF", "1u", X(11.05), 12.9, 270, {"1": "CG" + sfx, "2": "GND"}, label=None)
    t.wire(FBN, [(u, "4"), (X(12.25), 10.2), (rf_, "1")], width=0.2)
    t.wire(FBN, [(X(12.25), 10.2), (X(11.05), 10.2), (rg_, "1")], width=0.2)
    t.wire("CG" + sfx, [(rg_, "2"), (cg, "1")], width=0.2)
    if cf:                                                     # across Rf, just under it, clear of the OUT jack's leg
        cf_ = t.add("C", cf[0], cf[1], X(14.2), 11.23, 0, {"1": FBN, "2": OUTA}, label=None)
        t.wire(FBN, [(X(13.12), 10.2), (X(13.72), 10.75), (cf_, "1")], width=0.2, silk=False)
        t.wire(OUTA, [(X(14.08), 10.2), (X(14.68), 10.75), (cf_, "2")], width=0.2, silk=False)
    t.gnd_stub(cg, "2", (X(11.05), 14.2), sym=(0, 0), width=0.2, fine=True)
    co = t.add("C", "C0402 1uF", "1u", X(16.6), 5.6, 270, {"1": OUTA, "2": OUTC}, label=None)                  # pad 1 up
    ro = t.add("R", "R0402 49.9R", "49.9", X(16.6), 7.6, 270, {"1": OUTC, "2": OUT}, label=None)
    t.wire(OUTA, [(X(15.1), 4.5), (X(16.6), 4.5), (co, "1")], width=0.2)
    t.wire(OUTC, [(co, "2"), (ro, "1")], width=0.2)
    jout = [j["ref"] for j in t.jacks if j["slot"] in (("BR", "BR0") if dx == 0 else ("BR1",))][0]
    t.wire(OUT, [(ro, "2"), (X(16.6), 11.0), (X(15.25), 12.35), (jout, "1")], width=0.25)
    # VS to V+ on the back: up x 10.2 from the via at (10.2, 18.1) to a via under V+, on to the bias divider's via
    t.via("VS", X(14.15), 9.15, fine=True)
    t.wire("VS", [(u, "5"), (X(14.15), 9.15)], width=0.2)
    t.wire("VS", [(X(10.2), 18.1), (X(10.2), 9.6), (X(13.7), 9.6), (X(14.15), 9.15)], width=0.25, layer="B.Cu", silk=False, fine=True)
    t.wire("VS", [(X(14.15), 9.15), (X(13.7), 8.7), (X(10.7), 8.7), (X(10.7), 2.4), (X(11.6), 1.6)], width=0.2, layer="B.Cu", silk=False, fine=True)
    cp = t.add("C", "C0402 100nF", "100n", X(9.0), 12.3, 270, {"1": "VS", "2": "GND"}, label=None)              # pad 1 up
    t.via("VS", X(10.2), 11.0, fine=True)
    t.wire("VS", [(cp, "1"), (X(9.0), 11.0), (X(10.2), 11.0)], width=0.2)
    t.gnd_stub(cp, "2", (X(9.0), 13.9), sym=(0, 0), width=0.2, fine=True)


# ------------------------------------------------------------------------------------------------------------ Y5 --
def tile_y5():
    """The two-channel HF receiver front end: two LMH6629 amplifiers (0.69 nV/rtHz, gain 9.9), 50 ohm in and out, from a few
    kHz to 100 MHz, on one switched 5 V; the host's ADCs sample both coherently (the host's own front end rolls off at 23 MHz;
    add a 30 MHz low-pass ahead of it for a station beside an FM transmitter).  It carries the Pmod plug in its bottom margin."""
    t = Tile("Y5", "HF receiver", [(0, 3), (1, 3)], supply="+5 V", subtitle="2 x LMH6629", sections=[])
    t.jack("TL0", "IN A", "IN", "in", "-10 dBm", silk="IN A")
    t.jack("BR0", "OUT A", "OUT", "out", "", silk="OUT A")
    t.jack("TL1", "IN B", "INB", "in", "-10 dBm", silk="IN B")
    t.jack("BR1", "OUT B", "OUTB", "out", "", silk="OUT B")
    power_header(t, rail="+5V")
    t.wire("VS", [HDR_VS, (10.2, 18.1)], width=0.35)
    lmh_amp(t, 0.0)
    lmh_amp(t, 21.5)
    t.wire("VS", [(10.2, 18.1), (10.2, 19.6), (31.7, 19.6), (31.7, 18.1)], width=0.35, silk=False)
    used = PMOD_USED                                       # the lines some tile uses; the others stay open on the plug
    pads = {"12": "/PMOD1", "10": "/PMOD2", "8": "/PMOD3", "6": "/PMOD4", "11": "/PMOD5", "9": "/PMOD6", "7": "/PMOD7", "5": "/PMOD8"}
    pins = {k: v for k, v in pads.items() if v in used}
    pins.update({"3": "GND", "4": "GND", "1": "/PMOD_VCC", "2": "/PMOD_VCC"})
    pm = t.add("J", "PMOD", "Pmod", 2.97, 24.25, 0, pins, hide_value=True)
    t.wire("/PMOD_VCC", [(pm, "1"), (pm, "2")], silk=False)
    t.text(1.2, 9.4, "Y5", 1.2, 0.2, "left")
    t.text(4.1, 9.4, "HF RX", 0.8, 0.15, "left")
    t.text(22.0, 17.3, "x9.9 EACH", 0.8, 0.15, "left")
    t.result = "gain 9.9 (20 dB) on each channel, 50 ohm in and out, about 5 kHz to 100 MHz; 0.7 nV/rtHz at the input (NF about 2.5 dB)"
    t.notes = ["Two TI LMH6629 (0.69 nV/rtHz, 4 GHz at gain 10) on one 5 V: 49.9 ohm terminates each input, 1 uF couples it to +IN at half",
               "the supply, 240 / 27 ohm (the 27 ohm to ground through 1 uF) set the gain, 1 uF and 49.9 ohm feed the output jack.  Two",
               "antennas into IN A and IN B and the host's two ADCs: a coherent two-channel HF receiver (WWV Doppler, direction finding)."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ Y9 --
def tile_y9():
    """A switched HF noise source: the base-emitter junction of an MMBT3904 in avalanche (the base at -5 V, the emitter fed from
    the switched rail VN through 680 ohm: about 8 V across it at 2-3 mA), its noise straight into an LMH6629 at gain 9.9 (the
    Y5 channel without its input termination) and out through 1 uF and 49.9 ohm.  A TPS22917 load switch makes VN from the
    tile's 5 V when Pmod IO8 is high: off is the cold state of a Y-factor measurement (the amplifier's own noise), on the hot.
    The switch and the junction stand in the top-left quarter (no jack there), the amplifier in the top-right; -5 V comes up
    a finger of L3 from the gutter below."""
    t = Tile("Y9", "noise source", [(3, 0)], supply="+5 V", subtitle="MMBT3904 + LMH6629", sections=[])
    t.jack("BR", "OUT", "OUT", "out", "", silk="OUT")
    power_header(t, rail="+5V")
    t.wire("VS", [HDR_VS, (10.2, 18.1)], width=0.35)
    # the switch: TPS22917 (rot 0: VIN 1, GND 2, ON 3 down the left; VOUT 6 top-right; CT and QOD open); ON is Pmod IO8
    sw = t.add("U", "TPS22917", "TPS22917", 3.2, 3.0, 0, {"1": "VS", "2": "GND", "3": "/PMOD8", "6": "VN"}, hide_value=False, label=None)
    t.gnd_stub(sw, "2", (3.2, 3.0), sym=(0, 0), width=0.25, fine=True)
    cvs = t.add("C", "C0402 1uF", "1u", 3.2, 0.6, 180, {"1": "VS", "2": "GND"}, label=None)                  # rot 180: VS pad right
    gnd(t, cvs, "2", (1.6, 0.6), w=0.25)
    t.wire("VS", [(sw, "1"), (2.0625, 1.3), (3.68, 1.3), (cvs, "1")], width=0.25)
    t.wire("VS", [(3.68, 1.3), (11.6, 1.3), (11.6, 1.6)], width=0.25)                  # to the amplifier's bias via
    # VN: down x 5.45 to its 100 nF and the 680 ohm feed
    cvn = t.add("C", "C0402 100nF", "100n", 6.35, 3.3, 0, {"1": "VN", "2": "GND"}, label=None)
    re_ = t.add("R", "R0402 680R", "680", 6.35, 4.9, 0, {"1": "VN", "2": "IN"}, label=None)
    t.wire("VN", [(sw, "6"), (5.45, 2.05), (5.45, 4.9), (re_, "1")], width=0.25)
    t.wire("VN", [(5.45, 3.3), (cvn, "1")], width=0.25)
    gnd(t, cvn, "2", (7.7, 3.3), w=0.25)
    # the junction: MMBT3904 rot 180 (E 2 top-right, B 1 bottom-right, C 3 left and open); E is the noise node IN
    q = t.add("Q", "MMBT3904", "MMBT3904", 6.6, 7.6, 180, {"1": "-5V", "2": "IN"}, hide_value=False, label=None)
    t.wire("IN", [(re_, "2"), (7.54, 4.9)], width=0.25)
    t.wire("IN", [(q, "2"), (7.54, 4.9)], width=0.25)
    cb1 = t.add("C", "C0402 100pF", "100p", 7.54, 10.4, 270, {"1": "-5V", "2": "GND"}, label=None)            # pad 1 up
    cb2 = t.add("C", "C0402 100nF", "100n", 6.4, 10.4, 270, {"1": "-5V", "2": "GND"}, label=None)
    t.wire("-5V", [(q, "1"), (cb1, "1")], width=0.25)
    t.wire("-5V", [(cb2, "1"), (6.4, 9.55), (7.54, 9.55)], width=0.25)
    t.via("-5V", 1.2, 9.55)
    t.wire("-5V", [(6.4, 9.55), (1.2, 9.55)], width=0.25)
    gnd(t, cb1, "2", (7.54, 12.0), w=0.25)
    gnd(t, cb2, "2", (6.4, 12.0), w=0.25)
    lmh_amp(t, 0.0, jack_in=False, in_from=[(7.54, 4.9), (8.0, 4.75)], term=False)
    t.text(1.0, 6.3, "Y9", 1.2, 0.2, "left")
    t.text(1.0, 7.8, "NOISE", 0.8, 0.15, "left")
    t.result = "off: the amplifier's own noise (about 6 nV/rtHz at OUT); on: tens to hundreds of nV/rtHz from 10 kHz to 50 MHz, flat to about 1 dB"
    t.notes = ["An MMBT3904's emitter-base junction breaks down near 8 V; between -5 V and the switched 5 V through 680 ohm it carries",
               "2-3 mA and its avalanche noise, many times kT's, goes straight into an LMH6629 at gain 9.9 and out through 49.9 ohm.  IO8",
               "high turns it on (a TPS22917 switches its 5 V): hot and cold for a Y-factor noise figure, or a broadband stimulus whose",
               "cross-spectrum against the response on the host's second ADC is a transfer function."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ Y7 --
def tile_y7():
    """The reflection bridge, two cells, +-5 V.  DRIVE (the top-left jack) feeds node D; 49.9 ohm from D to A, which runs right
    along y 4.75 to the DUT jack (the right cell's top-left); 49.9 ohm from D to B and 49.9 ohm from B to ground.  With a 50 ohm
    DUT the bridge balances (A = B); in general A - B = B x Gamma.  Two OPA810 (SOT-23-5, rot 270) stand under the line, each
    input a millimetre or two from its node: U1 at gain 2 on B (INC, through 49.9 ohm to the left cell's bottom-right jack) and
    U2 as a difference amplifier, +IN on A and 499 ohm from U1's output to -IN, 499 ohm feedback: 2 A - 2 B (REFL, through
    49.9 ohm along y 10 to the right cell's bottom-right jack).  REFL / INC = Gamma, complex, at every frequency the host
    makes.  -5 V comes down the back from the gutter above at x 14.6 and 19.8; VS up the back from the switch at x 10.2."""
    t = Tile("Y7", "reflection bridge", [(0, 1), (1, 1)], supply="+-5 V", subtitle="2 x OPA810", sections=[])
    jd = t.jack("TL0", "DRIVE", "DRV", "in", "+-1 V into 50 ohm", silk="DRIVE")
    ji = t.jack("BR0", "INC", "INC", "out", "", silk="INC")
    ju = t.jack("TL1", "DUT", "A", "out", "", silk="DUT")
    jr = t.jack("BR1", "REFL", "REFL", "out", "", silk="REFL")
    power_header(t, rail="+5V")
    # the bridge: D at (12.1, 4.75); R1 along the line to A, R2 and R3 down from D to B and ground
    t.wire("DRV", [(jd, "1"), (12.1, 4.75)], width=0.3)
    r1 = t.add("R", "R0402 49.9R", "49.9", 13.1, 4.75, 0, {"1": "DRV", "2": "A"}, label=None)
    r2 = t.add("R", "R0402 49.9R", "49.9", 12.1, 6.3, 270, {"1": "DRV", "2": "B"}, label=None)                 # pad 1 up
    r3 = t.add("R", "R0402 49.9R", "49.9", 12.1, 8.2, 270, {"1": "B", "2": "GND"}, label=None)
    t.wire("DRV", [(12.1, 4.75), (r1, "1")], width=0.3)
    t.wire("DRV", [(12.1, 4.75), (r2, "1")], width=0.3)
    t.wire("B", [(r2, "2"), (r3, "1")], width=0.25)
    gnd(t, r3, "2", (12.1, 9.7), w=0.3)
    t.wire("A", [(r1, "2"), (ju, "1")], width=0.3)
    # U1: INC = 2 B.  rot 270: +IN (13.65, 7.26), V- (14.6, 7.26), OUT (15.55, 7.26); -IN (13.65, 9.54), V+ (15.55, 9.54)
    u1 = t.add("U", "OPA810", "OPA810", 14.6, 8.4, 270, {"1": "O1", "2": "-5V", "3": "B", "4": "N1", "5": "VS"}, hide_value=False, label=None)
    t.wire("B", [(12.1, 7.25), (u1, "3")], width=0.2)
    rf1 = t.add("R", "R0402 499R", "499", 14.8, 11.1, 0, {"1": "N1", "2": "O1"}, label=None)
    rg1 = t.add("R", "R0402 499R", "499", 12.9, 11.1, 0, {"1": "GND", "2": "N1"}, label=None)
    t.wire("N1", [(u1, "4"), (13.65, 11.1)], width=0.2)
    t.wire("N1", [(rg1, "2"), (rf1, "1")], width=0.2)
    gnd(t, rg1, "1", (11.4, 11.6), w=0.2)
    ro1 = t.add("R", "R0402 49.9R", "49.9", 16.9, 10.6, 270, {"1": "O1", "2": "INC"}, label=None)              # pad 1 up
    t.wire("O1", [(u1, "1"), (16.2, 7.26), (16.2, 10.12), (ro1, "1")], width=0.2)
    t.wire("O1", [(16.2, 10.12), (16.2, 10.6), (15.7, 11.1), (rf1, "2")], width=0.2)
    t.wire("INC", [(ro1, "2"), (15.25, 12.73), (ji, "1")], width=0.25)
    # U2: REFL = 2 A - 2 B.  +IN (18.85, 7.26) straight down from A; Rg2 from O1 to -IN, Rf2 under it
    u2 = t.add("U", "OPA810", "OPA810", 19.8, 8.4, 270, {"1": "O2", "2": "-5V", "3": "A", "4": "N2", "5": "VS"}, hide_value=False, label=None)
    t.wire("A", [(18.85, 4.75), (u2, "3")], width=0.2)
    rg2 = t.add("R", "R0402 499R", "499", 17.5, 8.4, 270, {"1": "O1", "2": "N2"}, label=None)                  # pad 1 up
    t.wire("O1", [(16.2, 7.92), (rg2, "1")], width=0.2)
    t.wire("N2", [(rg2, "2"), (17.5, 9.54), (u2, "4")], width=0.2)
    rf2 = t.add("R", "R0402 499R", "499", 19.8, 11.1, 0, {"1": "N2", "2": "O2"}, label=None)
    t.wire("N2", [(u2, "4"), (18.85, 11.1), (rf2, "1")], width=0.2)
    ro2 = t.add("R", "R0402 49.9R", "49.9", 23.5, 10.0, 0, {"1": "O2", "2": "REFL"}, label=None)
    t.wire("O2", [(u2, "1"), (21.8, 7.26), (21.8, 10.0), (ro2, "1")], width=0.2)
    t.wire("O2", [(21.8, 10.0), (21.8, 11.1), (rf2, "2")], width=0.2)
    t.wire("REFL", [(ro2, "2"), (36.75, 10.0), (jr, "1")], width=0.25)
    # -5 V: the V- pins up to vias, up the back to the gutter's L3 strip; 100 nF at a via on the way
    for x, u in ((14.6, u1), (19.8, u2)):
        t.wire("-5V", [(u, "2"), (x, 6.0)], width=0.25)
        t.via("-5V", x, 2.0)
        t.wire("-5V", [(x, 6.0), (x, -0.75)], width=0.3, layer="B.Cu", silk=False)
        cn = t.add("C", "C0402 100nF", "100n", x + 1.0, 2.0, 0, {"1": "-5V", "2": "GND"}, label=None)
        t.wire("-5V", [(x, 2.0), (cn, "1")], width=0.25)
        gnd(t, cn, "2", (x + 2.2, 2.0), w=0.25)
    # VS: the drain to a via, up the back at x 10.2 and along y 10.9 to vias under the V+ pins; 100 nF at each end
    t.wire("VS", [HDR_VS, (10.2, 18.1)], width=0.35)
    for x, u in ((15.55, u1), (20.75, u2)):
        t.wire("VS", [(u, "5"), (x, 10.25)], width=0.2)
    t.wire("VS", [(10.2, 18.1), (10.2, 10.9), (15.0, 10.9), (15.55, 10.25)], width=0.25, layer="B.Cu", silk=False, fine=True)
    t.wire("VS", [(15.55, 10.25), (16.2, 10.9), (20.75, 10.9), (20.75, 10.25)], width=0.25, layer="B.Cu", silk=False, fine=True)
    t.wire("VS", [(20.75, 10.25), (21.3, 10.9), (22.8, 10.9), (22.8, 12.4)], width=0.25, layer="B.Cu", silk=False, fine=True)
    t.via("VS", 10.2, 10.9, fine=True)
    cp1 = t.add("C", "C0402 100nF", "100n", 9.2, 11.6, 270, {"1": "VS", "2": "GND"}, label=None)               # pad 1 up
    t.wire("VS", [(10.2, 10.9), (9.2, 10.9), (cp1, "1")], width=0.25)
    gnd(t, cp1, "2", (9.2, 13.2), w=0.25)
    cp2 = t.add("C", "C0402 100nF", "100n", 22.8, 13.5, 270, {"1": "VS", "2": "GND"}, label=None)
    t.wire("VS", [(22.8, 12.4), (cp2, "1")], width=0.25)
    gnd(t, cp2, "2", (22.8, 15.0), w=0.25)
    t.text(1.2, 9.4, "Y7", 1.2, 0.2, "left")
    t.text(4.1, 9.4, "BRIDGE", 0.8, 0.15, "left")
    t.text(21.6, 17.6, "REFL/INC=S11", 0.8, 0.15, "left")
    t.result = "REFL / INC = Gamma (S11) from DC to about 30 MHz: 0 for 50 ohm, +1 open, -1 short; after open-short-load calibration, better than -35 dB"
    t.notes = ["A 50 ohm resistive bridge: D from DRIVE, 49.9 ohm to A (the DUT jack) and 49.9 + 49.9 ohm from D to ground with B between.",
               "A - B = B x Gamma.  OPA810 U1 at gain 2 on B gives INC; U2, +IN on A and 499 / 499 ohm from U1's output, gives 2 A - 2 B,",
               "REFL; each leaves through 49.9 ohm, so into the host's 50 ohm inputs REFL / INC = Gamma, magnitude and phase.  Calibrate",
               "with an open, a short and a 50 ohm load on DUT (three complex numbers per frequency), then match an NMR probe or an antenna."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ Y8 --
def tile_y8():
    """Coupled and parametric resonators, two cells, passive: two 10 MHz LC tanks (TDK's 10 uH NLV32, Q about 30), each tuned
    by a back-to-back pair of BB133 varactors whose cathodes sit at half the supply through 100 k / 100 k.  Like two cavities
    each has weak capacitive ports: SIG (terminated in 49.9 ohm) drives tank 1 through 2.2 pF, and 2.2 pF from each tank feeds
    its OUT jack, which the host's 50 ohm ADC input loads (about -43 dB, no buffer, no loading of the tank).  TUNE / PUMP
    reaches tank 2's varactor cathodes through 100 k (DC: tank 2's frequency, half the open-circuit voltage) and 1 nF (RF: the
    pump at twice the resonance).  A DIP4 switches 1 pF and 2.2 pF of coupling between the tanks and 2 k of damping across
    either.  Tank 1 in the left cell's top-right quarter on a bus along y 4.75, tank 2 in the right cell's on y 5.5; the
    switch under the right jack, its top row fed along y 8.55 - 9.35 from the left and y 9.0 from the right, its bottom row
    joined to tank 2 round its right side."""
    t = Tile("Y8", "coupled resonators", [(0, 2), (1, 2)], supply="+5 V", subtitle="2 x LC + BB133", sections=[])
    js = t.jack("TL0", "SIG", "SIG", "in", "+-1 V into 50 ohm", silk="SIG")
    jo1 = t.jack("BR0", "OUT 1", "OUT1", "out", "", silk="OUT 1")
    jt = t.jack("TL1", "TUNE / PUMP", "TP", "in", "+-2 V open", silk="TUNE/PUMP")
    jo2 = t.jack("BR1", "OUT 2", "OUT2", "out", "", silk="OUT 2")
    power_header(t, rail="+5V")
    # ---- tank 1: SIG through 2.2 pF onto the bus T1 along y 4.75; L1 and C1 above, the varactors and their bias to the right
    rt = t.add("R", "R0402 49.9R", "49.9", 8.9, 6.1, 270, {"1": "SIG", "2": "GND"}, label=None)                 # pad 1 up
    cs = t.add("C", "C0402 2.2pF", "2.2p", 10.4, 4.75, 0, {"1": "SIG", "2": "T1"}, label=None)
    t.wire("SIG", [(js, "1"), (cs, "1")], width=0.25)
    t.wire("SIG", [(8.9, 4.75), (rt, "1")], width=0.25)
    gnd(t, rt, "2", (8.9, 7.4))
    t.wire("T1", [(cs, "2"), (15.25, 4.75)], width=0.25)
    t.wire("T1", [(15.25, 4.75), (20.0, 4.75)], width=0.25, silk=False)
    c1 = t.add("C", "C0402 4.7pF", "4.7p", 10.9, 2.7, 90, {"1": "T1", "2": "GND"}, label=None)                  # pad 1 down
    t.wire("T1", [(c1, "1"), (10.9, 4.75)], width=0.25)
    gnd(t, c1, "2", (10.9, 1.1))
    l1 = t.add("L", "L1210 10uH", "10u", 13.9, 1.9, 0, {"1": "T1", "2": "GND"}, label=None)
    t.wire("T1", [(l1, "1"), (12.5, 4.75)], width=0.3)
    gnd(t, l1, "2", (15.3, 3.6), w=0.4)
    gnd(t, l1, "2", (15.9, 0.45), w=0.4)
    d1a = t.add("D", "BB133", "BB133", 17.2, 2.8, 270, {"1": "K1", "2": "T1"}, hide_value=True, label=None)      # K up, A down
    d1b = t.add("D", "BB133", "BB133", 19.2, 2.8, 90, {"1": "K1", "2": "GND"}, hide_value=True, label=None)      # K down, A up
    t.wire("T1", [(d1a, "2"), (17.2, 4.75)], width=0.25, silk=False)
    gnd(t, d1b, "2", (19.2, 0.6))
    t.wire("K1", [(d1a, "1"), (18.2, 1.75), (18.2, 3.85), (d1b, "1")], width=0.2)
    rk1a = t.add("R", "R0402 100k", "100k", 21.0, 2.4, 270, {"1": "VS", "2": "K1"}, label=None)                 # pad 1 up
    rk1b = t.add("R", "R0402 100k", "100k", 21.0, 4.4, 270, {"1": "K1", "2": "GND"}, label=None)
    t.wire("K1", [(d1b, "1"), (20.4, 3.85), (21.0, 3.4), (rk1a, "2")], width=0.2)
    t.wire("K1", [(21.0, 3.4), (rk1b, "1")], width=0.2)
    gnd(t, rk1b, "2", (21.0, 5.9))
    t.via("VS", 21.0, 0.85, fine=True)
    t.wire("VS", [(rk1a, "1"), (21.0, 0.85)], width=0.2)
    # T1's ports: 2.2 pF down to OUT 1; 1 pF, 2.2 pF and 2 k down to the switch's top row (pins 8, 7, 6)
    co1 = t.add("C", "C0402 2.2pF", "2.2p", 15.25, 10.6, 270, {"1": "T1", "2": "OUT1"}, label=None)             # pad 1 up
    t.wire("T1", [(15.25, 4.75), (co1, "1")], width=0.25)
    t.wire("OUT1", [(co1, "2"), (jo1, "1")], width=0.25)
    cc1 = t.add("C", "C0402 1pF", "1p", 17.6, 6.4, 270, {"1": "T1", "2": "CA"}, label=None)
    cc2 = t.add("C", "C0402 2.2pF", "2.2p", 18.8, 6.4, 270, {"1": "T1", "2": "CB"}, label=None)
    rd1 = t.add("R", "R0402 2k", "2k", 20.0, 6.4, 270, {"1": "T1", "2": "RDA"}, label=None)
    for x, part in ((17.6, cc1), (18.8, cc2), (20.0, rd1)):
        t.wire("T1", [(x, 4.75), (part, "1")], width=0.2, silk=False)
    sw = t.add("SW", "DIP4", "DIP4", 26.0, 14.3, 0, {"8": "CA", "7": "CB", "6": "RDA", "5": "RDB",
                                                      "1": "T2", "2": "T2", "3": "GND", "4": "GND"}, hide_value=True)
    t.wire("CA", [(cc1, "2"), (17.6, 9.5), (24.095, 9.5), (sw, "8")], width=0.2)
    t.wire("CB", [(cc2, "2"), (18.8, 9.1), (25.365, 9.1), (sw, "7")], width=0.2)
    t.wire("RDA", [(rd1, "2"), (20.0, 8.7), (26.635, 8.7), (sw, "6")], width=0.2)
    gnd(t, sw, "3", (26.635, 16.6))
    gnd(t, sw, "4", (27.905, 16.6))
    # ---- tank 2: TUNE / PUMP right from its jack to 1 nF and 100 k into K2; the varactors stand on the bus T2 along y 5.5
    cp = t.add("C", "C0402 1nF", "1n", 30.7, 2.6, 270, {"1": "K2", "2": "TP"}, label=None)                      # pad 1 up
    rk2b = t.add("R", "R0402 100k", "100k", 31.9, 2.6, 270, {"1": "K2", "2": "TP"}, label=None)
    rk2a = t.add("R", "R0402 100k", "100k", 33.1, 2.6, 270, {"1": "K2", "2": "VS"}, label=None)
    t.wire("TP", [(jt, "1"), (30.0, 4.75), (30.7, 4.05), (31.9, 4.05)], width=0.25)
    t.wire("TP", [(30.7, 4.05), (cp, "2")], width=0.25)
    t.wire("TP", [(31.9, 4.05), (rk2b, "2")], width=0.25)
    t.via("VS", 33.1, 4.1, fine=True)
    t.wire("VS", [(rk2a, "2"), (33.1, 4.1)], width=0.2)
    d2a = t.add("D", "BB133", "BB133", 34.85, 2.8, 270, {"1": "K2", "2": "T2"}, hide_value=True, label=None)      # K up, A down
    d2b = t.add("D", "BB133", "BB133", 37.05, 2.8, 270, {"1": "K2", "2": "GND"}, hide_value=True, label=None)
    t.wire("K2", [(cp, "1"), (30.7, 1.2), (37.05, 1.2), (d2b, "1")], width=0.2)
    t.wire("K2", [(31.9, 1.2), (rk2b, "1")], width=0.2)
    t.wire("K2", [(33.1, 1.2), (rk2a, "1")], width=0.2)
    t.wire("K2", [(34.85, 1.2), (d2a, "1")], width=0.2)
    gnd(t, d2b, "2", (37.05, 4.8))
    l2 = t.add("L", "L1210 10uH", "10u", 39.75, 2.6, 90, {"1": "T2", "2": "GND"}, label=None)                   # rot 90: pad 1 down
    gnd(t, l2, "2", (38.85, 0.45), w=0.4)
    gnd(t, l2, "2", (40.65, 0.45), w=0.4)
    t.wire("T2", [(31.2, 5.5), (39.75, 5.5), (l2, "1")], width=0.3)
    t.wire("T2", [(d2a, "2"), (34.85, 5.5)], width=0.25)
    c2 = t.add("C", "C0402 6.8pF", "6.8p", 38.0, 6.6, 270, {"1": "T2", "2": "GND"}, label=None)
    t.wire("T2", [(38.0, 5.5), (c2, "1")], width=0.25)
    gnd(t, c2, "2", (38.0, 8.0))
    co2 = t.add("C", "C0402 2.2pF", "2.2p", 36.75, 10.6, 270, {"1": "T2", "2": "OUT2"}, label=None)
    t.wire("T2", [(36.75, 5.5), (co2, "1")], width=0.25)
    t.wire("OUT2", [(co2, "2"), (jo2, "1")], width=0.25)
    rd2 = t.add("R", "R0402 2k", "2k", 31.2, 6.6, 270, {"1": "T2", "2": "RDB"}, label=None)
    t.wire("T2", [(31.2, 5.5), (rd2, "1")], width=0.25)
    t.wire("RDB", [(rd2, "2"), (31.2, 9.0), (27.905, 9.0), (sw, "5")], width=0.2)
    # T2 down the switch's right side and along its foot to pins 1 and 2
    t.wire("T2", [(32.6, 5.5), (32.6, 19.4), (24.095, 19.4), (sw, "1")], width=0.25, silk=False)
    t.wire("T2", [(25.365, 19.4), (sw, "2")], width=0.25, silk=False)
    # VS: the drain to a via, up the back at x 10.2, along y 8.75 (under the right jack's feet) to both bias dividers
    t.wire("VS", [HDR_VS, (10.2, 18.1)], width=0.35)
    t.wire("VS", [(10.2, 18.1), (10.2, 8.75), (22.0, 8.75), (22.0, 1.6), (21.0, 0.85)], width=0.25, layer="B.Cu", silk=False, fine=True)
    t.wire("VS", [(33.1, 4.1), (33.1, 8.75), (10.2, 8.75), (10.2, 18.1)], width=0.25, layer="B.Cu", silk=False, fine=True)
    cvs = t.add("C", "C0402 100nF", "100n", 9.0, 12.3, 270, {"1": "VS", "2": "GND"}, label=None)               # pad 1 up
    t.via("VS", 10.2, 11.0, fine=True)
    t.wire("VS", [(cvs, "1"), (9.0, 11.0), (10.2, 11.0)], width=0.2)
    gnd(t, cvs, "2", (9.0, 13.9), w=0.2)
    t.text(1.2, 9.4, "Y8", 1.2, 0.2, "left")
    t.text(4.1, 9.4, "TANKS", 0.8, 0.15, "left")
    t.result = "two 10 MHz tanks (Q about 30); coupled by 1, 2.2 or 3.2 pF they split by 0.4 - 1.2 MHz; TUNE moves tank 2 by +-5 %; a 20 MHz pump on it gives parametric gain"
    t.notes = ["Two LC tanks, 10 uH and about 25 pF each (fixed, two BB133 back to back at 2.5 V, the ports), near 10 MHz, Q about 30.",
               "SIG drives tank 1 through 2.2 pF; each tank feeds its OUT jack through 2.2 pF, -43 dB into the host's 50 ohm.  The DIP:",
               "1 pF and 2.2 pF between the tanks (normal modes, the avoided crossing as TUNE sweeps tank 2), 2 k across tank 1 or tank 2",
               "(a lossy tank coupled to a sharp one: the EIT analogue).  A pump at twice the frequency on TUNE / PUMP: parametric gain."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ----------------------------------------------------------------------------------------------------------- Y10 --
def tile_y10():
    """The laser driver with an RF bias-T, two cells.  SET (terminated, 1 k / 100 nF) drives OPA810 U1 and a 2N7002 that pull
    SET / 1 k through 1 k from VS: REF = VS - SET.  OPA810 U2 holds the AO3401's source at REF (1 k into -IN, 10 nF to its
    output, 100 ohm to the gate), so 10 ohm from VS carries SET / 10 ohm: 100 mA per volt, from 0.  The drain (ID) feeds the
    diode through 330 nH and 27 nH; RF IN reaches it through 100 pF and 47 ohm (about 20 MHz to 3 GHz); an AO3400 from ID to
    ground (Pmod IO5 high) steals the current for microsecond pulses without upsetting the loop; a B5819W guards against
    reverse current.  MON is the diode's voltage through 10 k into the host's 50 ohm (1/200).  The RF line drops from RF IN
    and runs along y 9 to the LD jack's left; the gate and source lines go under it on the back."""
    t = Tile("Y10", "laser driver", [(2, 2), (3, 2)], supply="+5 V", subtitle="current source + bias-T", sections=[])
    jset = t.jack("TL0", "SET", "SET", "in", "0-1 V: 0-100 mA", silk="SET")
    jmon = t.jack("BR0", "MON", "MON", "out", "", silk="MON")
    jrf = t.jack("TL1", "RF IN", "RF", "in", "+10 dBm max", silk="RF IN")
    jld = t.jack("BR1", "LD", "LDN", "out", "100 mA max", silk="LD")
    power_header(t, rail="+5V")
    # ---- U1 and the 2N7002: REF = VS - SET
    rterm = t.add("R", "R0402 49.9R", "49.9", 8.9, 6.1, 270, {"1": "SET", "2": "GND"}, label=None)              # pad 1 up
    rf = t.add("R", "R0402 1k", "1k", 10.4, 4.75, 0, {"1": "SET", "2": "SETF"}, label=None)
    t.wire("SET", [(jset, "1"), (rf, "1")], width=0.25)
    t.wire("SET", [(8.9, 4.75), (rterm, "1")], width=0.25)
    gnd(t, rterm, "2", (8.9, 7.4))
    cf = t.add("C", "C0402 100nF", "100n", 11.6, 3.3, 90, {"1": "SETF", "2": "GND"}, label=None)                # pad 1 down
    t.wire("SETF", [(11.6, 4.75), (cf, "1")], width=0.2)
    gnd(t, cf, "2", (11.6, 1.6), w=0.2)
    ub = t.add("U", "OPA810", "OPA810", 13.2, 6.9, 270, {"1": "GB", "2": "GND", "3": "SETF", "4": "NS", "5": "VS"}, hide_value=False, label=None)
    t.wire("SETF", [(rf, "2"), (12.25, 4.75), (ub, "3")], width=0.2)
    t.gnd_stub(ub, "2", (13.4, 4.4), sym=(0, 0), width=0.2, fine=True)
    q1 = t.add("Q", "NFET_S", "2N7002", 16.9, 7.0, 0, {"1": "GB", "2": "NS", "3": "REF"}, hide_value=False, label=None)
    t.wire("GB", [(ub, "1"), (q1, "1")], width=0.2)
    t.wire("NS", [(q1, "2"), (15.9625, 10.0), (12.25, 10.0), (ub, "4")], width=0.2)
    rref = t.add("R", "R0402 1k", "1k", 15.25, 11.0, 0, {"1": "NS", "2": "GND"}, label=None)
    t.wire("NS", [(14.77, 10.0), (rref, "1")], width=0.2)
    gnd(t, rref, "2", (16.6, 11.0), w=0.2)
    rtop = t.add("R", "R0402 1k", "1k", 19.4, 6.4, 270, {"1": "VS", "2": "REF"}, label=None)                    # pad 1 up
    t.via("VS", 19.4, 4.9, fine=True)
    t.wire("VS", [(rtop, "1"), (19.4, 4.9)], width=0.2)
    t.wire("REF", [(q1, "3"), (rtop, "2")], width=0.2)
    t.wire("REF", [(rtop, "2"), (19.4, 8.9), (24.65, 8.9), (24.65, 11.2625)], width=0.2)
    t.via("VS", 14.15, 9.25, fine=True)
    t.wire("VS", [(ub, "5"), (14.15, 9.25)], width=0.2)
    cpb = t.add("C", "C0402 100nF", "100n", 9.0, 12.3, 270, {"1": "VS", "2": "GND"}, label=None)
    t.via("VS", 10.2, 11.0, fine=True)
    t.wire("VS", [(cpb, "1"), (9.0, 11.0), (10.2, 11.0)], width=0.2)
    gnd(t, cpb, "2", (9.0, 13.9), w=0.2)
    # ---- U2 holds the AO3401's source at REF.  rot 270: +IN (24.65, 11.26), V- (25.6, 11.26), OUT (26.55, 11.26); -IN, V+ below
    ua = t.add("U", "OPA810", "OPA810", 25.6, 12.4, 270, {"1": "GA", "2": "GND", "3": "REF", "4": "NA", "5": "VS"}, hide_value=False, label=None)
    t.gnd_stub(ua, "2", (25.6, 10.1), sym=(0, 0), width=0.2, fine=True)
    riso = t.add("R", "R0402 100R", "100", 28.4, 11.26, 0, {"1": "GA", "2": "GQ"}, label=None)
    t.wire("GA", [(ua, "1"), (riso, "1")], width=0.2)
    ccomp = t.add("C", "C0402 10nF", "10n", 25.6, 15.0, 0, {"1": "NA", "2": "GA"}, label=None)
    t.wire("GA", [(27.2, 11.26), (27.2, 15.0), (ccomp, "2")], width=0.2)
    t.wire("NA", [(ua, "4"), (24.65, 15.0), (ccomp, "1")], width=0.2)
    rcomp = t.add("R", "R0402 1k", "1k", 23.6, 15.0, 0, {"1": "SQ", "2": "NA"}, label=None)
    t.wire("NA", [(rcomp, "2"), (24.65, 15.0)], width=0.2)
    t.via("SQ", 22.4, 15.0, fine=True)
    t.wire("SQ", [(rcomp, "1"), (22.4, 15.0)], width=0.2)
    t.via("VS", 26.55, 14.2, fine=True)
    t.wire("VS", [(ua, "5"), (26.55, 14.2)], width=0.2)
    t.via("GQ", 29.6, 11.26, fine=True)
    t.wire("GQ", [(riso, "2"), (29.6, 11.26)], width=0.2)
    # ---- the AO3401 (rot 0 at (32, 3.5)), its 10 ohm, the AO3400 shunt, the bias-T down to the LD jack
    q2 = t.add("Q", "PFET", "AO3401A", 32.0, 3.2, 0, {"1": "GQ", "2": "SQ", "3": "ID"}, hide_value=False, label=None)
    t.via("GQ", 31.0625, 1.4, fine=True)
    t.wire("GQ", [(q2, "1"), (31.0625, 1.4)], width=0.2)
    t.wire("GQ", [(29.6, 11.26), (30.2, 10.66), (30.2, 2.2), (31.0625, 1.4)], width=0.2, layer="B.Cu", silk=False, fine=True)
    rs = t.add("R", "R0805 10R", "10", 31.0, 6.6, 90, {"1": "VS", "2": "SQ"}, label=None)                         # rot 90: pad 2 up
    t.wire("SQ", [(q2, "2"), (rs, "2")], width=0.4)
    t.via("SQ", 32.2, 6.09, fine=True)
    t.wire("SQ", [(rs, "2"), (32.2, 6.09)], width=0.2)
    t.wire("SQ", [(22.4, 15.0), (22.4, 16.5), (31.6, 16.5), (31.6, 6.7), (32.2, 6.09)], width=0.2, layer="B.Cu", silk=False, fine=True)
    t.via("VS", 32.3, 7.9)
    t.wire("VS", [(rs, "1"), (32.3, 7.9)], width=0.4)
    cbulk = t.add("C", "C0805 10uF", "10u", 34.6, 9.0, 90, {"1": "GND", "2": "VS"}, label=None)                 # rot 90: pad 2 up
    t.wire("VS", [(32.3, 7.9), (34.6, 8.0875)], width=0.4)
    gnd(t, cbulk, "1", (34.6, 11.0), w=0.4)
    q3 = t.add("Q", "NFET", "AO3400A", 35.9, 2.0, 0, {"1": "/PMOD5", "2": "GND", "3": "ID"}, hide_value=False, label=None)
    gnd(t, q3, "2", (34.9625, 3.85), w=0.3)
    t.wire("ID", [(q2, "3"), (33.5, 4.6), (36.75, 4.6), (36.75, 2.0), (q3, "3")], width=0.4)
    la = t.add("L", "L0805 330nH", "330n", 36.75, 8.0, 270, {"1": "ID", "2": "LM"}, label=None)                 # pad 1 up
    lb = t.add("L", "L0402 27nH", "27n", 36.75, 10.75, 270, {"1": "LM", "2": "LDN"}, label=None)
    t.wire("ID", [(36.75, 4.6), (la, "1")], width=0.4)
    t.wire("LM", [(la, "2"), (lb, "1")], width=0.3)
    t.wire("LDN", [(lb, "2"), (jld, "1")], width=0.3)
    dp = t.add("D", "B5819W", "B5819W", 39.2, 3.3, 90, {"1": "ID", "2": "GND"}, hide_value=False, label=None)    # rot 90: K down
    t.wire("ID", [(dp, "1"), (36.75, 4.95)], width=0.3)
    gnd(t, dp, "2", (39.2, 0.5), w=0.4)
    # ---- RF IN: down from its jack, along y 9 through 100 pF and 47 ohm, down x 33 and into the LD jack from the left
    crf = t.add("C", "C0402 100pF", "100p", 28.4, 9.0, 0, {"1": "RF", "2": "RFC"}, label=None)
    rrf = t.add("R", "R0402 47R", "47", 30.4, 9.0, 0, {"1": "RFC", "2": "LDN"}, label=None)
    t.wire("RF", [(jrf, "1"), (26.25, 9.0), (crf, "1")], width=0.35)
    t.wire("RFC", [(crf, "2"), (rrf, "1")], width=0.35)
    t.wire("LDN", [(rrf, "2"), (32.4, 9.0), (32.4, 15.25), (jld, "1")], width=0.35)
    rmon = t.add("R", "R0402 10k", "10k", 31.5, 12.0, 0, {"1": "MON", "2": "LDN"}, label=None)
    t.wire("LDN", [(rmon, "2"), (32.4, 12.0)], width=0.2)
    t.wire("MON", [(rmon, "1"), (30.2, 12.8), (30.2, 19.6), (19.4, 19.6), (19.4, 15.25), (jmon, "1")], width=0.25)
    # ---- IO5 along the top to the shunt's gate, 100 k holding it low
    t.wire("/PMOD5", [(-0.35, 0.25), (34.4, 0.25), (q3, "1")], width=F, silk=False)
    rsd = t.add("R", "R0402 100k", "100k", 22.0, 1.2, 270, {"1": "/PMOD5", "2": "GND"}, label=None)
    t.wire("/PMOD5", [(22.0, 0.25), (rsd, "1")], width=F)
    gnd(t, rsd, "2", (22.0, 2.7), w=0.2)
    # ---- VS on the back: the switch's drain up x 10.2 to U1; on to REF's 1 k, U2 and a 100 nF; along the gutter to the 10 ohm
    t.wire("VS", [HDR_VS, (10.2, 18.1)], width=0.35)
    t.wire("VS", [(10.2, 18.1), (10.2, 9.6), (13.8, 9.6), (14.15, 9.25)], width=0.25, layer="B.Cu", silk=False, fine=True)
    t.wire("VS", [(14.15, 9.25), (18.6, 4.9), (19.4, 4.9)], width=0.25, layer="B.Cu", silk=False, fine=True)
    t.wire("VS", [(19.4, 4.9), (21.0, 6.5), (21.0, 14.2), (26.55, 14.2)], width=0.25, layer="B.Cu", silk=False, fine=True)
    t.wire("VS", [(10.2, 18.1), (10.2, 20.4), (32.3, 20.4), (32.3, 7.9)], width=0.4, layer="B.Cu", silk=False)
    t.via("VS", 21.0, 12.0, fine=True)
    cpa = t.add("C", "C0402 100nF", "100n", 22.2, 12.0, 0, {"1": "VS", "2": "GND"}, label=None)
    t.wire("VS", [(21.0, 12.0), (cpa, "1")], width=0.2)
    gnd(t, cpa, "2", (23.4, 12.0), w=0.2)
    t.text(1.2, 9.4, "Y10", 1.2, 0.2, "left")
    t.text(4.9, 9.4, "LASER", 0.8, 0.15, "left")
    t.result = "0-100 mA from 0-1 V on SET, about 10 kHz of loop bandwidth; IO5 blanks it in about 1 us; RF from about 20 MHz to 3 GHz rides on the current"
    t.notes = ["A high-side current source: REF = VS - SET (OPA810 and a 2N7002 through 1 k / 1 k), OPA810 holds the AO3401's source at",
               "REF so 10 ohm carries SET / 10 ohm, 100 mA per volt (start a VCSEL at a few millivolts).  The drain feeds the diode through",
               "330 nH + 27 nH; RF IN joins through 100 pF + 47 ohm: the modulation for a rubidium CPT clock (3.4 GHz) or NV ODMR.  IO5 high",
               "shorts the drain (the AO3400) for pulses.  MON = the diode's voltage / 200 into 50 ohm: with SET swept, its I-V curve."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ Y6 --
def tile_y6():
    """A VLF / LF loop amplifier, one cell: the loop (or a ferrite rod's coil) on the IN jack through an SMA lead, 1 uF into an
    OPA810 biased at half the supply by 100 k / 100 k (the loop is a low-impedance source; the 50 ohm termination stays off),
    gain 101 (10 k / 100 ohm, the 100 ohm to ground through 1 uF: a 1.6 kHz high-pass), 100 pF across 10 k (a 160 kHz roll-off
    that keeps the AM broadcast band out), 1 uF and 49.9 ohm into OUT.  The LMH6629 tile's core with other values."""
    t = Tile("Y6", "VLF loop amplifier", [(2, 3)], supply="+5 V", subtitle="OPA810 x101", sections=[])
    t.jack("TL", "LOOP", "IN", "in", "mV", silk="LOOP")
    t.jack("BR", "OUT", "OUT", "out", "", silk="OUT")
    power_header(t, rail="+5V")
    t.wire("VS", [HDR_VS, (10.2, 18.1)], width=0.35)
    lmh_amp(t, 0.0, term=False, chip="OPA810", rf=("R0402 10k", "10k"), rg=("R0402 100R", "100"), rb=("R0402 100k", "100k"),
            cf=("C0402 100pF", "100p"))
    t.text(1.2, 9.4, "Y6", 1.2, 0.2, "left")
    t.text(4.1, 9.4, "VLF", 0.8, 0.15, "left")
    t.result = "gain 101 from 1.6 kHz to 160 kHz (the loop's EMF rises with frequency on top): sferics, the Navy's MSK stations near 24 kHz, WWVB at 60 kHz"
    t.notes = ["A loop's EMF is N A dB/dt: a 1 m square of 10 turns gives about 1 uV for 1 pT at 20 kHz.  1 uF into an OPA810 at half",
               "the supply (100 k / 100 k), gain 101 (10 k / 100 ohm to ground through 1 uF), 100 pF across 10 k: 1.6 - 160 kHz.  Sferics",
               "(lightning, thousands of kilometres away), NAA's 24 kHz MSK, WWVB's 60 kHz time code.  Two loops at right angles (this and",
               "Y5's IN A, or two boards) give a lightning stroke's bearing from the ratio of the two signals."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ Y4 --
def tile_y4():
    """The coil driver, one cell in the board's corner: a DRV8876 H-bridge in PH/EN mode (Pmod IO6 enables and is the PWM, IO7
    the direction; 100 k holds both low), nSLEEP and the 5 V divider from the switched rail.  VM through two B5819W: USB's 5 V
    (4.6 V) or 12-18 V on the right-margin terminal, whichever is higher (the 25 V bulk capacitor sets the limit).  IPROPI into
    1.5 k sets the current limit with VREF (5.1 k / 3.3 k: 2 V) and is buffered by an OPA810 (from VM) into MON through 49.9 ohm.
    The coil on the lower terminal.  The chip at (13, 12.5), rot 0: control pins down its left, the charge pump, VM and OUT2
    down its right, OUT1 at its foot; the diodes above it, the buffer beside the MON jack; IO6 / IO7 come down the back at
    x 9.55 / 8.95 to vias beside pins 1 and 2."""
    t = Tile("Y4", "coil driver", [(3, 3)], supply="+5 V or 12-18 V", subtitle="DRV8876", sections=[])
    t.fine = True
    jmon = t.jack("TL", "MON", "MON", "out", "IPROPI", silk="MON")
    power_header(t, rail="+5V")
    t.pwr_flags.append("VM")                                   # VM comes through the two Schottkys
    u = t.add("U", "DRV8876", "DRV8876", 13.0, 12.5, 0, {"1": "/PMOD6", "2": "/PMOD7", "3": "VS", "5": "VREF", "6": "IP", "7": "GND",
                                                         "8": "OUT1", "9": "GND", "10": "OUT2", "11": "VM", "12": "VCP", "13": "CPH",
                                                         "14": "CPL", "15": "GND", "16": "GND", "17": "GND"}, hide_value=False, label=None)
    for (x, y) in ((12.2, 11.0), (13.8, 11.0), (12.2, 12.5), (13.8, 12.5), (12.2, 14.0), (13.8, 14.0)):
        t.gnd_stub(u, "17", (x, y), sym=(0, 0), width=0.3)                          # the PowerPAD's vias
    t.wire("GND", [(u, "9"), (14.5, 14.775)], width=0.3, silk=False)
    t.wire("GND", [(u, "15"), (14.5, 10.875)], width=0.3, silk=False)
    t.wire("GND", [(u, "16"), (15.5, 10.225), (15.5, 10.875)], width=0.25, silk=False)
    t.wire("GND", [(u, "7"), (11.5, 14.125)], width=0.25, silk=False)
    # IO6 / IO7: vias beside pins 1 and 2 (the board's back wires end on them); 100 k pull-downs to one ground via
    t.via("/PMOD6", 9.55, 9.5, fine=True)
    t.wire("/PMOD6", [(9.55, 9.5), (u, "1")], width=F)
    t.via("/PMOD7", 8.95, 10.875, fine=True)
    t.wire("/PMOD7", [(8.95, 10.875), (u, "2")], width=F)
    rpd6 = t.add("R", "R0402 100k", "100k", 7.4, 9.7, 0, {"1": "GND", "2": "/PMOD6"}, label=None)
    t.wire("/PMOD6", [(rpd6, "2"), (9.55, 9.5)], width=F)
    rpd7 = t.add("R", "R0402 100k", "100k", 7.7, 10.9, 0, {"1": "GND", "2": "/PMOD7"}, label=None)
    t.wire("/PMOD7", [(rpd7, "2"), (8.95, 10.875)], width=F)
    gnd(t, rpd6, "1", (6.0, 9.7), w=0.2)
    t.wire("GND", [(rpd7, "1"), (6.4, 10.3), (6.0, 9.7)], width=0.2, silk=False)
    # VS: the drain to a via, on the back under the FET and up x 5.9 to a via; along y 11.52 to nSLEEP and the divider's top
    t.via("VS", 9.0, 17.3, fine=True)
    t.wire("VS", [HDR_VS, (9.0, 17.3)], width=0.3)
    t.via("VS", 5.9, 11.3, fine=True)
    t.wire("VS", [(9.0, 17.3), (6.5, 17.3), (5.9, 16.7), (5.9, 11.3)], width=0.3, layer="B.Cu", silk=False, fine=True)
    rv1 = t.add("R", "R0402 5.1k", "5.1k", 6.2, 12.0, 270, {"1": "VS", "2": "VREF"}, label=None)                 # pad 1 up
    rv2 = t.add("R", "R0402 3.3k", "3.3k", 6.2, 13.95, 270, {"1": "VREF", "2": "GND"}, label=None)
    t.wire("VS", [(5.9, 11.3), (rv1, "1")], width=0.25)
    t.wire("VS", [(rv1, "1"), (u, "3")], width=0.25)
    t.wire("VREF", [(rv1, "2"), (rv2, "1")], width=0.2)
    t.wire("VREF", [(6.2, 12.825), (u, "5")], width=0.2)
    gnd(t, rv2, "2", (7.2, 14.9), w=0.2)
    # IPROPI: 1.5 k to ground, and up the back to the buffer's +IN
    rip = t.add("R", "R0402 1.5k", "1.5k", 8.55, 15.1, 90, {"1": "GND", "2": "IP"}, label=None)                 # pad 2 up
    t.wire("IP", [(u, "6"), (8.55, 13.475), (rip, "2")], width=0.2)
    gnd(t, rip, "1", (8.55, 16.15), w=0.2)
    t.via("IP", 7.9, 13.9, fine=True)
    t.wire("IP", [(8.55, 13.475), (7.9, 13.9)], width=0.2)
    t.wire("IP", [(7.9, 13.9), (10.9, 9.6), (11.65, 6.9)], width=0.2, layer="B.Cu", silk=False, fine=True)
    t.via("IP", 11.65, 6.9, fine=True)
    # the buffer (OPA810 rot 270 at (12.9, 6.9), from VM): OUT round the top-left to -IN, 49.9 ohm to MON
    ub = t.add("U", "OPA810", "OPA810", 12.6, 6.9, 270, {"1": "MO", "2": "GND", "3": "IP", "4": "MO", "5": "VM"}, hide_value=False, label=None)
    t.wire("IP", [(11.65, 6.9), (ub, "3")], width=0.2)
    t.wire("MO", [(ub, "1"), (13.55, 3.6), (10.9, 3.6), (10.9, 8.04), (ub, "4")], width=0.2)
    t.gnd_stub(ub, "2", (12.6, 4.4), sym=(0, 0), width=0.2, fine=True)
    rmo = t.add("R", "R0402 49.9R", "49.9", 9.9, 4.75, 0, {"1": "MON", "2": "MO"}, label=None)
    t.wire("MO", [(10.9, 4.75), (rmo, "2")], width=0.2)
    t.wire("MON", [(rmo, "1"), (jmon, "1")], width=0.25)
    # VM: the two Schottkys above the chip, joined along y 7.3, down x 19.2 into pin 11; the charge pump beside the pins
    dint = t.add("D", "B5819W", "B5819W", 15.9, 5.0, 90, {"1": "VM", "2": "VS"}, hide_value=False, label=None)    # rot 90: K down
    dext = t.add("D", "B5819W", "B5819W", 18.25, 4.2, 90, {"1": "VM", "2": "VEXT"}, hide_value=False, label=None)
    t.wire("VM", [(dint, "1"), (15.9, 7.3), (19.2, 7.3), (19.2, 13.475), (u, "11")], width=0.3)
    t.wire("VM", [(dext, "1"), (18.25, 7.3)], width=0.3)
    t.wire("VM", [(15.9, 7.3), (ub, "5")], width=0.25)
    cvm = t.add("C", "C0805 10uF", "10u", 16.6, 8.75, 0, {"1": "GND", "2": "VM"}, label=None)
    t.wire("VM", [(cvm, "2"), (19.2, 8.75)], width=0.4)
    gnd(t, cvm, "1", (15.2, 9.6), w=0.4)
    ccp = t.add("C", "C0402 22nF", "22n", 17.6, 11.85, 90, {"1": "CPH", "2": "CPL"}, label=None)               # pad 1 down
    t.wire("CPH", [(u, "13"), (17.3, 12.175), (ccp, "1")], width=0.2)
    t.wire("CPL", [(u, "14"), (17.3, 11.525), (ccp, "2")], width=0.2)
    cvcp = t.add("C", "C0402 100nF", "100n", 18.6, 12.75, 90, {"1": "VM", "2": "VCP"}, label=None)              # pad 1 down
    t.wire("VCP", [(u, "12"), (18.1, 12.9), (cvcp, "2")], width=0.2)
    t.wire("VM", [(cvcp, "1"), (19.2, 13.23)], width=0.25)
    # the terminals in the right margin (rot 270: the wires enter from the board's edge): VM in above, the coil below
    tvm = t.add("J", "TERM2", "VM in", 23.4, 9.0, 270, {"1": "VEXT", "2": "GND"}, hide_value=True)
    tco = t.add("J", "TERM2", "coil", 23.4, 21.0, 270, {"1": "OUT2", "2": "OUT1"}, hide_value=True)
    t.wire("VEXT", [(tvm, "1"), (21.4, 2.55), (dext, "2")], width=0.6)
    t.wire("OUT2", [(u, "10"), (19.9, 14.125), (23.4, 17.6), (tco, "1")], width=0.6)
    t.wire("OUT1", [(u, "8"), (10.1, 15.6), (10.1, 19.6), (21.5, 19.6), (23.4, 21.5), (tco, "2")], width=0.6)
    t.via("VS", 15.9, 2.4, fine=True)
    t.wire("VS", [(dint, "2"), (15.9, 2.4)], width=0.3)
    t.wire("VS", [(9.0, 17.3), (19.6, 17.3), (19.6, 2.4), (15.9, 2.4)], width=0.3, layer="B.Cu", silk=False, fine=True)
    t.text(1.2, 21.3, "Y4", 1.2, 0.2, "left")
    t.text(4.1, 21.3, "COIL", 0.8, 0.15, "left")
    t.result = "about 1.3 A either way into a coil, PWM on IO6; MON about 1.5 V per amp"
    t.notes = ["DRV8876 in PH/EN mode: IO6 enables (PWM), IO7 the direction; VM = USB or 12-18 V (two B5819W); IPROPI buffered to MON."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ Y1 --
def tile_y1():
    """Power, two cells, no jacks.  Left: the TPS65131 boost and inverter make +15 and -15 V from the 5 V (1 M / 88.7 k and
    1.3 M / 105 k, TI's 4.7 uH and Schottky rectifiers, 3 x 10 uF on each output), carried up the back to Y2's pulse amplifier
    only.  Right: AMOD-A's USB-C input (5.1 k CC pull-downs, 2 A PTC, 5 V TVS, 2 x 10 uF) and the LM2664 that makes -5 V into the
    strip in the gutter above; a green LED on +5 V, a red one on -5 V, a yellow one on +15 V."""
    t = Tile("Y1", "power", [(2, 1), (3, 1)], subtitle="USB-C 5 V in: +5, -5, +15, -15 out", sections=[])
    t.pwr_flags = ["+5V", "+15V", "-15V", "VINF"]
    # ---- the TPS65131 (rot 180 at (10.0, 9.5)): OUTN, VNEG, FBN, VREF, CN down the left (the inverter's corner, top-left);
    # INN, VIN, PGND, INP down the right (the boost's corner, bottom-right); the enables along the top; AGND, CP, FBP, VPOS,
    # INP along the bottom
    pins = {"1": "SWP", "24": "SWP", "2": "GND", "3": "GND", "4": "VINF", "5": "+5V", "6": "+5V", "8": "VINF", "10": "VINF", "9": "GND",
            "11": "GND", "13": "SWN", "14": "SWN", "15": "-15V", "16": "FBN", "17": "VREF", "18": "CN", "19": "GND", "21": "CP",
            "22": "FBP", "23": "+15V", "25": "GND"}
    u = t.add("U", "TPS65131", "TPS65131", 10.0, 9.5, 180, pins, hide_value=False, label=None)
    for (vx, vy) in ((9.4, 8.9), (10.6, 8.9), (9.4, 10.1), (10.6, 10.1)):
        t.gnd_stub(u, "25", (vx, vy), sym=(0, 0), width=F, fine=True)
    for n, pt in (("3", (10.9, 9.75)), ("2", (10.9, 10.25)), ("19", (8.75, 10.6)), ("11", (9.25, 8.4)), ("9", (10.25, 8.4))):
        t.wire("GND", [(u, n), pt], width=F)
    # the inverter (top-left): OUTN to the 4.7 uH (to ground) and the Schottky's cathode; -15 V along y 4.3 with 3 x 10 uF
    l2 = t.add("L", "L4U7", "4.7u", 3.4, 3.2, 0, {"1": "GND", "2": "SWN"}, hide_value=False, label=None)
    d2 = t.add("D", "B5819W", "B5819W", 9.5, 4.6, 0, {"1": "SWN", "2": "-15V"}, label=None)              # rot 0: cathode at -x
    t.wire("SWN", [(u, "13"), (7.75, 8.25), (7.75, 8.75), (u, "14")], width=0.25)
    t.wire("SWN", [(7.75, 8.5), (6.4, 8.5), (6.4, 4.6), (d2, "1")], width=0.5)
    t.wire("SWN", [(6.4, 4.6), (l2, "2")], width=0.5)
    gnd(t, l2, "1", (1.8, 6.2), w=0.5)
    for x in (13.0, 15.1, 17.2):
        c = t.add("C", "C0805 10uF", "10u", x, 3.0, 90, {"1": "-15V", "2": "GND"}, label=None)               # rot 90: -15 V pad down
        gnd(t, c, "2", (x, 1.0), w=0.4)
    t.wire("-15V", [(d2, "2"), (11.15, 4.3), (17.2, 4.3)], width=0.5)
    t.via("-15V", 12.2, 4.3, fine=True)
    t.via("-15V", 11.15, 5.7)                                                           # Y2's -15 V leaves here, up the back
    t.wire("-15V", [(d2, "2"), (11.15, 5.7)], width=0.4)
    # -15 V's sense and divider: VNEG to a via, R3 and C10 from the divider's top, both on the back to the -15 V line
    t.via("-15V", 7.25, 9.25, fine=True)
    t.wire("-15V", [(u, "15"), (7.25, 9.25)], width=F)
    c8 = t.add("C", "C0402 220nF", "220n", 4.6, 10.25, 0, {"1": "GND", "2": "VREF"}, label=None)
    c7 = t.add("C", "C0402 4.7nF", "4.7n", 4.6, 11.4, 0, {"1": "GND", "2": "CN"}, label=None)
    t.wire("VREF", [(u, "17"), (c8, "2")], width=F)
    t.wire("CN", [(u, "18"), (7.1, 11.3), (c7, "2")], width=F)
    gnd(t, c8, "1", (3.4, 10.25), w=0.2)
    gnd(t, c7, "1", (3.4, 11.4), w=0.2)
    r4 = t.add("R", "R0402 105k", "105k", 6.3, 10.0, 90, {"1": "VREF", "2": "FBN"}, label=None)              # pad 1 down
    t.wire("FBN", [(u, "16"), (6.6, 9.75), (6.5, 9.6)], width=F)
    r3 = t.add("R", "R0402 1.3M", "1.3M", 4.6, 8.9, 0, {"1": "-15V", "2": "FBN"}, label=None)
    c10 = t.add("C", "C0402 7.5pF", "7.5p", 4.6, 7.8, 0, {"1": "-15V", "2": "FBN"}, label=None)
    t.wire("FBN", [(r3, "2"), (5.8, 8.9), (6.3, 9.24)], width=F)
    t.wire("FBN", [(c10, "2"), (5.8, 7.8), (5.8, 8.9)], width=F)
    t.wire("-15V", [(r3, "1"), (3.4, 8.9), (3.4, 7.8), (c10, "1")], width=F)
    t.via("-15V", 3.4, 6.9, fine=True)
    t.wire("-15V", [(3.4, 7.8), (3.4, 6.9)], width=F)
    t.wire("-15V", [(3.4, 6.9), (6.0, 6.9), (11.0, 6.9), (12.2, 5.7), (12.2, 4.3)], width=0.2, layer="B.Cu", silk=False, fine=True)
    t.wire("-15V", [(7.25, 9.25), (7.25, 7.4), (12.2, 5.2), (12.2, 4.3)], width=0.2, layer="B.Cu", silk=False, fine=True)
    # the 5 V side (right column): INN on a via to the pour; VIN through 100 ohm with 100 nF; ENP and ENN on VIN, PSP and PSN on ground
    t.via("+5V", 12.8, 8.5, fine=True)
    t.wire("+5V", [(u, "6"), (u, "5"), (12.8, 8.5)], width=0.25)
    r7 = t.add("R", "R0402 100R", "100", 14.6, 6.6, 0, {"1": "VINF", "2": "+5V"}, label=None)
    c3 = t.add("C", "C0402 100nF", "100n", 14.6, 5.5, 0, {"1": "VINF", "2": "GND"}, label=None)
    t.wire("VINF", [(u, "4"), (13.5, 9.25), (13.5, 6.6), (r7, "1")], width=F)
    t.wire("VINF", [(13.5, 6.6), (13.5, 5.5), (c3, "1")], width=F)
    t.wire("VINF", [(u, "8"), (10.75, 6.6), (13.5, 6.6)], width=F)
    t.wire("VINF", [(u, "10"), (9.75, 6.6), (10.75, 6.6)], width=F)
    t.via("+5V", 15.9, 6.6, fine=True)
    t.wire("+5V", [(r7, "2"), (15.9, 6.6)], width=0.2)
    gnd(t, c3, "2", (15.9, 5.5), w=0.2)
    cin = t.add("C", "C0805 4.7uF", "4.7u", 13.2, 19.0, 0, {"1": "GND", "2": "+5V"}, label=None)
    t.wire("+5V", [(cin, "2"), (16.4, 18.8)], width=0.5)
    gnd(t, cin, "1", (11.3, 19.0), w=0.4)
    # the boost (bottom-right): the INP pair along y 10.75 to the inductor (from the 5 V) and the Schottky to +15 V; 3 x 10 uF
    l1 = t.add("L", "L4U7", "4.7u", 16.4, 15.2, 90, {"1": "+5V", "2": "SWP"}, hide_value=False, label=None)   # rot 90: pad 2 up
    d1 = t.add("D", "B5819W", "B5819W", 16.4, 8.6, 180, {"1": "+15V", "2": "SWP"}, label=None)            # rot 180: cathode at +x
    t.wire("SWP", [(u, "24"), (11.25, 12.2), (12.7, 12.2), (12.7, 10.75)], width=0.25)
    t.wire("SWP", [(u, "1"), (12.6, 10.75)], width=0.25)
    t.wire("SWP", [(12.6, 10.75), (14.75, 10.75), (14.75, 9.2)], width=0.5)
    t.wire("SWP", [(14.75, 10.75), (16.4, 12.4), (l1, "2")], width=0.5)
    t.via("+5V", 16.4, 18.8)
    t.wire("+5V", [(l1, "1"), (16.4, 18.8)], width=0.5)
    for y in (8.6, 10.6, 12.6):
        c = t.add("C", "C0805 10uF", "10u", 21.0, y, 0, {"1": "+15V", "2": "GND"}, label=None)
        gnd(t, c, "2", (22.9, y), w=0.4)
    t.wire("+15V", [(d1, "1"), (20.05, 8.6), (20.05, 13.6)], width=0.5)
    t.via("+15V", 20.05, 13.6)
    t.via("+15V", 20.05, 7.2)
    t.wire("+15V", [(20.05, 8.6), (20.05, 7.2)], width=0.5)
    # +15 V's sense and divider below the chip: CP's 10 nF, FBP's spine at x 10.25 with R2 (to ground), R1 and C9 (to +15 V)
    c6 = t.add("C", "C0402 10nF", "10n", 8.6, 13.4, 90, {"1": "GND", "2": "CP"}, label=None)                 # pad 2 up
    t.wire("CP", [(u, "21"), (9.75, 12.4), (8.6, 12.4), (c6, "2")], width=F)
    gnd(t, c6, "1", (8.6, 14.9), w=0.2)
    r2 = t.add("R", "R0402 88.7k", "88.7k", 9.1, 15.9, 0, {"1": "GND", "2": "FBP"}, label=None)
    r1 = t.add("R", "R0402 1M", "1M", 11.6, 15.6, 0, {"1": "FBP", "2": "+15V"}, label=None)
    c9 = t.add("C", "C0402 6.8pF", "6.8p", 11.6, 16.7, 0, {"1": "FBP", "2": "+15V"}, label=None)
    t.wire("FBP", [(u, "22"), (10.25, 16.7), (c9, "1")], width=F)
    t.wire("FBP", [(10.25, 15.9), (r2, "2")], width=F)
    t.wire("FBP", [(10.25, 15.6), (r1, "1")], width=F)
    gnd(t, r2, "1", (7.8, 15.9), w=0.2)
    t.wire("+15V", [(r1, "2"), (12.9, 15.6), (12.9, 16.7), (c9, "2")], width=F)
    t.via("+15V", 12.9, 17.7, fine=True)
    t.wire("+15V", [(12.9, 16.7), (12.9, 17.7)], width=F)
    t.via("+15V", 11.1, 12.85, fine=True)
    t.wire("+15V", [(u, "23"), (10.75, 12.45), (11.1, 12.85)], width=F)
    t.wire("+15V", [(11.1, 12.85), (11.6, 13.35), (11.6, 17.7), (12.9, 17.7)], width=0.2, layer="B.Cu", silk=False, fine=True)
    t.wire("+15V", [(12.9, 17.7), (18.6, 17.7), (20.05, 16.25), (20.05, 13.6)], width=0.25, layer="B.Cu", silk=False, fine=True)
    # +15 V's yellow LED in the gutter between the cells
    ry = t.add("R", "R0805 4.7k", "4.7k", 21.0, 15.6, 0, {"1": "+15V", "2": "LEDY"}, label=None)
    dy = t.add("LED", "LED_Y", "+15V", 21.0, 17.8, 0, {"1": "GND", "2": "LEDY"}, label=None)              # rot 0: K at -x
    t.wire("+15V", [(20.05, 13.6), (20.05, 15.6), (ry, "1")], width=0.25)
    t.wire("LEDY", [(ry, "2"), (22.6, 15.6), (22.6, 17.8), (dy, "2")], width=0.25)
    gnd(t, dy, "1", (20.06, 18.9))
    # ---- the USB-C input and the LM2664, in the right cell (AMOD-A's A1 moved right by 21.5)
    X = lambda x: x + 21.5
    ux = USB_X - t.x0
    j = t.add("J", "USBC", "USB-C", ux, 10.0, 90, {"A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS", "A5": "CC1", "B5": "CC2",
                                                   "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "SH": "GND"}, hide_value=True)
    t.wire("GND", [(j, "A1"), (ux - 3.13, 14.32)])
    t.wire("GND", [(j, "B1"), (ux - 3.13, 5.68)])
    rc1 = t.add("R", "R0805 5.1k", "5.1k", X(17.6), 11.5, 0, {"1": "GND", "2": "CC1"}, label=None)
    rc2 = t.add("R", "R0805 5.1k", "5.1k", X(17.6), 9.3, 0, {"1": "GND", "2": "CC2"}, label=None)
    t.wire("CC1", [(j, "A5"), (X(19.3), 11.25), (X(19.3), 11.5), (rc1, "2")], width=0.25)
    t.wire("CC2", [(j, "B5"), (X(19.3), 8.25), (X(19.3), 9.3), (rc2, "2")], width=0.25)
    t.gnd_stub(rc1, "1", (X(16.688), 10.4), sym=(0, 0))
    t.gnd_stub(rc2, "1", (X(15.9), 9.3), sym=(0, 0))
    t.wire("VBUS", [(j, "B9"), (X(19.9), 12.45)], width=0.25)
    t.wire("VBUS", [(j, "A9"), (X(19.9), 7.55)], width=0.25)
    t.wire("VBUS", [(X(19.9), 12.45), (X(19.9), 7.55)], layer="B.Cu")
    f = t.add("F", "PTC2A", "2A", X(15.5), 6.2, 0, {"1": "+5V", "2": "VBUS"}, label=None)
    t.wire("VBUS", [(X(19.9), 7.55), (X(19.9), 6.2), (f, "2")])
    d = t.add("D", "TVS5V", "SMAJ5.0A", X(10.6), 7.6, 270, {"1": "+5V", "2": "GND"}, label=None)
    c1 = t.add("C", "C0805 10uF", "10u", X(7.0), 6.2, 180, {"1": "+5V", "2": "GND"}, label=None)
    c2 = t.add("C", "C0805 10uF", "10u", X(7.0), 8.8, 180, {"1": "+5V", "2": "GND"}, label=None)
    t.wire("+5V", [(f, "1"), (c1, "1")])
    t.via("+5V", X(9.1), 6.2)
    t.wire("+5V", [(c1, "1"), (c2, "1")])
    t.gnd_stub(d, "2", (X(10.6), 11.3), sym=(0, 0))
    t.gnd_stub(c1, "2", (X(6.05), 4.7), sym=(0, 0))
    t.gnd_stub(c2, "2", (X(5.0), 8.8), sym=(0, 0))
    u2 = t.add("U", "LM2664", "LM2664", X(6.0), 12.6, 0, {"1": "GND", "2": "-5V", "3": "CAPN", "4": "+5V", "5": "+5V", "6": "CAPP"}, hide_value=False, label=None)
    cf = t.add("C", "C0805 10uF", "10u", X(6.0), 15.4, 0, {"1": "CAPN", "2": "CAPP"}, label=None)
    co = t.add("C", "C0805 10uF", "10u", X(9.6), 15.4, 0, {"1": "-5V", "2": "GND"}, label=None)
    t.wire("+5V", [(u2, "4"), (u2, "5")])
    t.route("+5V", [(u2, "5"), (c2, "1")])
    t.route("CAPN", [(u2, "3"), (cf, "1")])
    t.route("CAPP", [(u2, "6"), (cf, "2")])
    t.wire("-5V", [(u2, "2"), (25.0, 12.6), (25.0, 17.6)], width=0.35)
    t.wire("-5V", [(X(2.6), 17.6), (25.0, 17.6), (X(8.65), 17.6), (co, "1")], width=0.35)
    t.gnd_stub(co, "2", (X(11.4), 15.4), sym=(0, 0))
    t.gnd_stub(u2, "1", (X(4.86), 10.2), sym=(0, 0))
    t.via("-5V", X(2.6), 17.6)
    t.wire("-5V", [(X(2.6), 17.6), (X(2.6), -0.75)], width=0.35, layer="B.Cu", silk=False)
    dr = t.add("LED", "LED_R", "-5V", X(20.6), 2.6, 270, {"1": "-5V", "2": "LEDR"}, label=None)
    rr = t.add("R", "R0805 1k", "1k", X(22.6), 2.6, 90, {"1": "LEDR", "2": "GND"}, label=None)
    dg = t.add("LED", "LED_G", "+5V", X(24.6), 2.6, 90, {"1": "LEDG", "2": "+5V"}, label=None)
    rg = t.add("R", "R0805 1k", "1k", X(26.6), 2.6, 90, {"1": "LEDG", "2": "GND"}, label=None)
    t.via("-5V", X(20.6), -0.75)
    t.wire("-5V", [(dr, "1"), (X(20.6), -0.75)], silk=False)
    t.wire("LEDR", [(dr, "2"), (rr, "1")])
    t.gnd_stub(rr, "2", (X(22.6), 0.6), sym=(0, 0))
    t.via("+5V", X(24.6), 0.6)
    t.wire("+5V", [(dg, "2"), (X(24.6), 0.6)], silk=False)
    t.wire("LEDG", [(dg, "1"), (rg, "1")])
    t.gnd_stub(rg, "2", (X(26.6), 0.6), sym=(0, 0))
    t.text(X(13.0), 18.6, "Y1 POWER", 0.9, 0.17, "center")
    t.text(1.2, 18.6, "+-15 V", 0.8, 0.15, "left")
    t.result = ("+5 V from the USB-C (up to 2 A), -5 V at 40 mA, +15 V and -15 V at about 150 mA each for the pulse amplifier; green: "
                "5 V in, red: -5 V up, yellow: +15 V up")
    t.notes = ["USB-C power only (5.1 k on each CC).  The TPS65131 runs both converters at 1.25 MHz with power-save off (quieter);",
               "+15 V = 1.213 V x (1 + 1 M / 88.7 k) = 14.9 V, -15 V = -1.213 V x 1.3 M / 105 k = -15.0 V.  Only Y2 draws them, through",
               "two back-side tracks; everything else runs from +5 V and the LM2664's -5 V (40 mA: Y3, Y7 and Y9 draw about 30)."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


def tiles():
    return [tile_y3(), tile_y2(), tile_y9(), tile_y7(), tile_y1(), tile_y8(), tile_y10(), tile_y5(), tile_y6(), tile_y4()]


PMOD_USED = {"/PMOD1", "/PMOD5", "/PMOD6", "/PMOD7", "/PMOD8"}
PMOD_HOST = "Y5's bottom edge"
PMOD_NAMES = {"/PMOD1": "Y2's PD (high: the pulse amplifier on)", "/PMOD5": "Y10's shunt (high: the laser's current diverted)",
              "/PMOD6": "Y4's EN (high: the bridge on; PWM it)", "/PMOD7": "Y4's PH (the current's direction)",
              "/PMOD8": "Y9's load switch (high: noise on)"}
HANDBOOK_INTRO = [
    "Ten tiles on sixteen 20 mm cells, four layers, USB-C power on Y1, built for the ECP5-2ADC-2DAC board, whose converters sample",
    "DC to 30 MHz directly: two DACs and two ADCs, so most tiles take one or two DAC channels and give one or two ADC channels.",
    "Every tile's input is its top-left jack and its output its bottom-right jack; a two-cell tile has two of each.  The powered",
    "tiles have the AMOD-A slide switch (up: on).  +5 V is everywhere on L3; -5 V (40 mA, the LM2664) reaches the tiles above and",
    "below the gutter under row 0 (Y3, Y7, Y9); +-15 V from the TPS65131 reach only Y2, on two tracks on the back.  Nothing here",
    "needs more than USB's 5 V except Y4's coil, which may have 12-18 V of its own on its upper terminal."]
HANDBOOK_SECTIONS = [
    ["## The tiles together", "",
     "Every experiment below uses the ECP5 board's converters directly: DAC 1 and DAC 2 make the stimulus, ADC 1 and ADC 2 read the",
     "response, and the gateware does the rest (quadrature demodulation, averaging, lock-in).  One clock, so phase means something.",
     "",
     "1. **Pulsed NMR, 5-25 MHz.**  DAC 1 into Y2 (IO1 high only during the pulse: +-1 V becomes +-10 V, 1 W into 50 ohm), Y2's",
     "   OUT into Y3's TX IN, Y3's PROBE to the probe (match it first with Y7: S11 below -20 dB at the Larmor frequency), a",
     "   quarter-wave cable from a tee at the probe back to LINE; Y3's RX OUT (the OPA847, x12) into ADC 1, demodulated at the",
     "   Larmor frequency in the gateware.  A Halbach or yoke magnet of N52",
     "   cubes (0.3-0.5 T, protons at 13-21 MHz), a 5 mm vial of water with a little copper sulphate: the FID, the spin echo, CPMG,",
     "   T1 by inversion recovery, T2.  Y4 on a gradient coil during the echo: a one-dimensional image.",
     "2. **Earth's-field NMR, 2 kHz.**  Y4 drives a polarizing coil round a litre of water for a few seconds (12 V, an amp), then",
     "   stops (IO6 low); a second, receive coil round the same bottle into Y6 (gain 101) and ADC 1: the protons' precession in the",
     "   Earth's 50 uT, outdoors, away from mains wiring.",
     "3. **ESR of DPPH, 10-100 MHz.**  A small loop round the sample, tuned to the DAC's frequency and read by Y7 (DRIVE from DAC 1,",
     "   INC and REFL into the ADCs); Y4 sweeps a Helmholtz pair through g = 2 (1.07 mT at 30 MHz): the loop's S11 dips on resonance.",
     "4. **The ionosphere.**  Two HF antennas into Y5's IN A and IN B (gain 9.9 each, 0.7 nV/rtHz): WWV's carrier Doppler at 5, 10",
     "   and 15 MHz (HamSCI), the phase between the channels as a bearing, FT8 and WSPR decoded in software.  A VLF loop into Y6:",
     "   sferics from lightning thousands of kilometres away, the Navy's MSK stations near 24 kHz (and their daily phase change at",
     "   sunrise and sunset), sudden ionospheric disturbances from solar flares, WWVB's 60 kHz time code.",
     "5. **Impedance and the Smith chart.**  Y7: DRIVE from DAC 1, REFL and INC into the ADCs; REFL / INC = Gamma at every",
     "   frequency the DAC makes.  Calibrate with an open, a short and 50 ohm on DUT, then a crystal's motional arm, an antenna's",
     "   match, a cable's length (time-domain reflectometry from a step), an NMR probe's tuning.",
     "6. **Coupled and parametric resonators.**  Y8: DAC 1 into SIG, DAC 2 into TUNE / PUMP (a slow ramp, a 20 MHz pump, or both",
     "   added), OUT 1 and OUT 2 into the ADCs.  Normal-mode splitting and the avoided crossing as TUNE sweeps tank 2 through tank",
     "   1 (the DIP's 1 and 2.2 pF set the coupling); damp tank 1 (the DIP's 2 k) and its response shows a transparency window: the",
     "   EIT analogue; pump at twice the frequency: phase-sensitive gain and de-amplification, then parametric oscillation.",
     "7. **Noise.**  Y9 into Y5 (or Y3's preamp) with IO8 toggled: the Y-factor gives the amplifier's noise figure; Y9's noise into",
     "   a filter with ADC 1 on its input and ADC 2 on its output: the transfer function from the cross-spectrum.",
     "8. **Lasers and atoms.**  Y10 drives a VCSEL or a laser diode on its LD jack (SET from DAC 1: 100 mA per volt; start at a few",
     "   millivolts); RF-MOD-2's synthesizer on RF IN puts sidebands on the light: 3.417 GHz on a 795 nm VCSEL through a rubidium",
     "   cell is coherent population trapping, the chip-scale atomic clock's physics; IO5 blanks the light for pulsed ODMR with",
     "   RF-MOD-2's X9 loop; MON (the diode's voltage) with a photodiode on an ADC gives the L-I-V curve and the threshold.",
     "",
     "Levels to remember: Y2 gives 1 W into 50 ohm from +-1 V and is for pulses (keep the duty cycle under 10 %); Y3 lets through",
     "the transmitter above about 0.7 V and gives x12 on the way back; Y5's channels give x9.9 (20 dB); Y6 x101; Y7's REFL and INC",
     "reach the ADCs at half (49.9 ohm into 50 ohm), and so does every output here; Y8's ports are -43 dB; Y10 stops at 100 mA (1 V);",
     "Y4 chops at about 1.3 A."],
]
GND_LOOPS = [(3.0, 30.0), (3.0, 70.0)]
HOLES = []
FEET = [(5.0, 5.0), (95.0, 5.0), (95.8, 71.0), (5.0, 85.0)]
SLOTS = []
RAIL_POURS = [("+5V", 0.6, 0.6, 99.4, 99.4, 0),
              ("-5V", [(8.0, 27.85), (72.65, 27.85), (72.65, 16.75), (74.25, 16.75), (74.25, 27.85), (93.4, 27.85),   # with Y9's finger
                       (93.4, 29.15), (8.0, 29.15)], 1)]
_Y1, _Y2 = G.cell_origin(2, 1), G.cell_origin(2, 0)
# +-15 V from Y1 up to Y2 on the back: +15 V up the gutter at x 70.8, -15 V straight up at Y1 / Y2's local x 10.6 to 11.15
_PM = (G.cell_origin(0, 3)[0] + 2.97, G.cell_origin(0, 3)[1] + 24.25)   # the Pmod plug's centre: pad columns at -6.35 .. 6.35, rows at +-1.27


def _pad(k):
    """Board position of the plug's pad k (odd pads on the row nearer the edge)."""
    col = (k - 1) // 2
    return (round(_PM[0] - 6.35 + 2.54 * col, 3), round(_PM[1] + (1.27 if k % 2 else -1.27), 3))


_Y4 = G.cell_origin(3, 3)
BACK_WIRES = [("+15V", [(_Y1[0] + 20.05, _Y1[1] + 7.2), (_Y1[0] + 20.05, _Y2[1] + 6.45), (_Y2[0] + 19.6, _Y2[1] + 6.0)]),
              ("-15V", [(_Y1[0] + 11.15, _Y1[1] + 5.7), (_Y1[0] + 9.55, _Y1[1] + 4.1), (_Y2[0] + 9.55, _Y2[1] + 13.75)]),
              # IO6 / IO7 to Y4: along the bottom edge, up the left side of the gutter at x 48.6 / 49.0, across the top of Y6
              ("/PMOD6", [_pad(9), (_pad(9)[0], 99.0), (48.6, 99.0), (48.6, _Y4[1] - 0.4), (_Y4[0] + 9.55, _Y4[1] - 0.4), (_Y4[0] + 9.55, _Y4[1] + 9.5)]),
              ("/PMOD7", [_pad(7), (_pad(7)[0], 99.4), (49.0, 99.4), (49.0, _Y4[1] + 0.1), (_Y4[0] + 8.95, _Y4[1] + 0.1), (_Y4[0] + 8.95, _Y4[1] + 10.875)])]
FIDUCIALS = [(3.5, 50.0), (96.5, 10.0), (88.0, 97.0)]          # the third off Y4's coil terminal

# the Pmod lines: along the bottom margin, then up the gutter between columns 1 and 2 (x 49.4 .. 50.6)
_Y9 = G.cell_origin(3, 0)
FRONT_WIRES = [("/PMOD1", [_pad(12), (_pad(12)[0], 93.05), (50.0, 93.05), (50.0, _Y2[1] + 0.6)]),
               # IO5 up the gutter at x 50.4 to Y10's shunt
               ("/PMOD5", [_pad(11), (_pad(11)[0] + 1.27, _PM[1]), (_pad(11)[0] + 1.27, 93.5), (50.4, 93.5), (50.4, G.cell_origin(2, 2)[1] + 0.25),
                           (G.cell_origin(2, 2)[0] - 0.35, G.cell_origin(2, 2)[1] + 0.25)]),
               # IO8 round the left and top margins to Y9's load switch
               ("/PMOD8", [_pad(5), (_pad(5)[0], 99.15), (2.4, 99.15), (2.4, 93.2), (6.0, 93.2), (6.0, 1.5), (71.5, 1.5), (71.5, _Y9[1] + 3.95),
                           (_Y9[0] + 2.0625, _Y9[1] + 3.95)])]
FRONT_TEXT = []
BACK_TEXT_X = 50.0
QR_AT = (61.0, 33.0)
BACK_TEXT = ["AMOD-2: HF, magnetic resonance and the reflectometer.",
             "Jacks at each cell's top-left and bottom-right; powered",
             "tiles have a slide switch (up: on).  USB-C on Y1.  Y2",
             "is the 1 W pulse amplifier: pulse it, do not leave it on."]


if __name__ == "__main__":
    ts = tiles()
    cells = [c for t in ts for c in t.cells]
    assert len(set(cells)) == len(cells), cells
    jacks = [(t.id + " " + j["label"], *t.to_board((j["x"], j["y"]))) for t in ts for j in t.jacks]
    bad = G.check_spacing(jacks)
    dmin = min([math.hypot(a[1] - b[1], a[2] - b[2]) for i, a in enumerate(jacks) for b in jacks[i + 1:]] or [0])
    print("%d tiles, %d cells, %d jacks (closest pair %.2f mm), %d parts; jack pairs closer than %.1f mm: %s"
          % (len(ts), len(cells), len(jacks), dmin, sum(len(t.parts) for t in ts), G.MIN_JACK_SPACING, bad or "none"))
    for t in ts:
        print("  %-4s %-16s %2d parts  %s" % (t.id, t.name, len(t.parts), t.result[:90]))
