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
def lmh_amp(t, dx=0.0, jack_in=True, in_from=None):
    """A single-supply LMH6629 at gain 9.9 (240 ohm / 27 ohm, the 27 ohm to ground through 1 uF so the output sits at the
    bias) in a cell's top-right quarter.  The IN line along y 4.75: 49.9 ohm to ground (the termination), 1 uF in series,
    +IN biased at half the supply by 10 k / 10 k above the line.  The op amp at (13.2, 6.9), rot 270 (+IN, V-, OUT along the
    top, -IN and V+ along the bottom); OUT round its right side at x 15.1 to Rf under it and to 1 uF and 49.9 ohm into the OUT
    jack at the cell's bottom-right.  VS comes up the back from a via at (10.2, 18.1) that the tile feeds."""
    X = lambda x: x + dx
    sfx = "" if dx == 0 else "B"
    IN, IN2, OUTA, FBN, OUTC, OUT = ("IN" + sfx, "IN2" + sfx, "OA" + sfx, "FB" + sfx, "OC" + sfx, "OUT" + sfx)
    rt = t.add("R", "R0402 49.9R", "49.9", X(8.9), 6.1, 270, {"1": IN, "2": "GND"}, label=None)                 # pad 1 up
    cin = t.add("C", "C0402 1uF", "1u", X(10.4), 4.75, 0, {"1": IN, "2": IN2}, label=None)
    if jack_in:
        jref = [j["ref"] for j in t.jacks if j["slot"] in (("TL", "TL0") if dx == 0 else ("TL1",))][0]
        t.wire(IN, [(jref, "1"), (cin, "1")], width=0.25)
    else:
        t.wire(IN, list(in_from) + [(cin, "1")], width=0.25)
    t.wire(IN, [(X(8.9), 4.75), (rt, "1")], width=0.25)
    t.gnd_stub(rt, "2", (X(8.9), 7.4), sym=(0, 0), width=0.2, fine=True)
    u = t.add("U", "LMH6629", "LMH6629", X(13.2), 6.9, 270, {"1": OUTA, "2": "GND", "3": IN2, "4": FBN, "5": "VS"}, hide_value=False, label=None)
    t.wire(IN2, [(cin, "2"), (X(12.25), 4.75), (u, "3")], width=0.25)
    rb1 = t.add("R", "R0402 10k", "10k", X(11.6), 3.3, 90, {"1": IN2, "2": "VS"}, label=None)                  # pad 1 down
    rb2 = t.add("R", "R0402 10k", "10k", X(12.65), 3.3, 270, {"1": "GND", "2": IN2}, label=None)               # pad 2 down
    t.wire(IN2, [(X(11.6), 4.75), (rb1, "1")], width=0.2)
    t.wire(IN2, [(rb2, "2"), (X(12.4), 4.4), (X(12.25), 4.75)], width=0.2)
    t.gnd_stub(rb2, "1", (X(12.65), 1.6), sym=(0, 0), width=0.2, fine=True)
    t.via("VS", X(11.6), 1.6, fine=True)
    t.wire("VS", [(rb1, "2"), (X(11.6), 1.6)], width=0.2)
    t.gnd_stub(u, "2", (X(13.4), 4.4), sym=(0, 0), width=0.2, fine=True)
    # the output: up and round the right side at x 15.1 to Rf under the op amp and to 1 uF and 49.9 ohm down into the jack
    rf = t.add("R", "R0402 240R", "240", X(13.6), 10.2, 0, {"1": FBN, "2": OUTA}, label=None)
    t.wire(OUTA, [(u, "1"), (X(14.15), 4.5), (X(15.1), 4.5), (X(15.1), 10.2), (rf, "2")], width=0.2)
    rg = t.add("R", "R0402 27R", "27", X(11.05), 10.9, 270, {"1": FBN, "2": "CG" + sfx}, label=None)           # pad 1 up
    cg = t.add("C", "C0402 1uF", "1u", X(11.05), 12.9, 270, {"1": "CG" + sfx, "2": "GND"}, label=None)
    t.wire(FBN, [(u, "4"), (X(12.25), 10.2), (rf, "1")], width=0.2)
    t.wire(FBN, [(X(12.25), 10.2), (X(11.05), 10.2), (rg, "1")], width=0.2)
    t.wire("CG" + sfx, [(rg, "2"), (cg, "1")], width=0.2)
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
    return [tile_y3(), tile_y2(), tile_y1(), tile_y5()]


PMOD_USED = {"/PMOD1"}
PMOD_HOST = "Y5's bottom edge"
PMOD_NAMES = {}
HANDBOOK_INTRO = []
HANDBOOK_SECTIONS = []
GND_LOOPS = [(3.0, 30.0), (3.0, 70.0)]
HOLES = []
FEET = [(5.0, 5.0), (95.0, 5.0), (95.0, 70.0), (5.0, 85.0)]
SLOTS = []
RAIL_POURS = [("+5V", 0.6, 0.6, 99.4, 99.4, 0),
              ("-5V", 8.0, 27.85, 93.4, 29.15, 1)]
_Y1, _Y2 = G.cell_origin(2, 1), G.cell_origin(2, 0)
# +-15 V from Y1 up to Y2 on the back: +15 V up the gutter at x 70.8, -15 V straight up at Y1 / Y2's local x 10.6 to 11.15
BACK_WIRES = [("+15V", [(_Y1[0] + 20.05, _Y1[1] + 7.2), (_Y1[0] + 20.05, _Y2[1] + 6.45), (_Y2[0] + 19.6, _Y2[1] + 6.0)]),
              ("-15V", [(_Y1[0] + 11.15, _Y1[1] + 5.7), (_Y1[0] + 9.55, _Y1[1] + 4.1), (_Y2[0] + 9.55, _Y2[1] + 13.75)])]
_PM = (G.cell_origin(0, 3)[0] + 2.97, G.cell_origin(0, 3)[1] + 24.25)   # the Pmod plug's centre: pad columns at -6.35 .. 6.35, rows at +-1.27


def _pad(k):
    """Board position of the plug's pad k (odd pads on the row nearer the edge)."""
    col = (k - 1) // 2
    return (round(_PM[0] - 6.35 + 2.54 * col, 3), round(_PM[1] + (1.27 if k % 2 else -1.27), 3))


# the Pmod lines: along the bottom margin, then up the gutter between columns 1 and 2 (x 49.4 .. 50.6)
FRONT_WIRES = [("/PMOD1", [_pad(12), (_pad(12)[0], 93.05), (50.0, 93.05), (50.0, _Y2[1] + 0.6)])]
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
