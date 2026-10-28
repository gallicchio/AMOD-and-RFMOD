"""AMOD-N: the second passive board, rev A (Prompt 17).  Eleven tiles on sixteen cells: the RF and analog blocks the
other boards lacked or dropped, every one passive except two that run on the Pmod's own 3.3 V (no USB): a step
attenuator set by hand on a switch or by the FPGA over three Pmod lines, and a one-transistor oscillator.  Prompt 18 gave
the attenuator a second cell for its switch and dropped P15 (two Smith-chart loads): n1's 25 ohm standard and n11's
switched loads cover the Smith chart.

Jason, Prompt 17: "It seems like there is enough pressure that I should make another analog board.  We should really call
this the 2nd board because it's so much simpler than even the active board ... All of the things that you suggested along
with some of the things that we've dropped should go on this new analog board ... SLOT for VNA-type calibration, passive
splitters" and, mid-turn, "If something can run on 3.3V, it could still be plugged into the PMOD port but wouldn't require
an external USB 5V input."

Four layers on JLC04161H-7628 as RF-MOD: L1 the parts and the drawn wires with a ground pour 0.25 mm from every 50 ohm
line (coplanar waveguide over L2), L2 ground, L3 the Pmod's 3.3 V under the whole board, L4 ground with the back-side text
and the Pmod lines.  Every jack has RF-MOD's launch (no plane under its centre pin) except the calibration SHORT, whose pin
is the pour.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, HERE)
import tiles as T
from tiles import Tile, power_header, HDR_VS
import geometry as G
from rf_mod import _coil, _ground

STEM = "amod_n"
LAYERS = 4
F = 0.15                     # fan-out tracks at the QFN
VCC = "/PMOD_VCC"            # the Pmod's 3.3 V, an L3 pour under the whole board


def rf_tile(id, name, cells, subtitle="", supply=None):
    t = Tile(id, name, cells, supply=supply, subtitle=subtitle, sections=[], kind="rf")
    t.top_pour = True
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------- n1 --
def tile_n1():
    """Calibration standards for a vector network analyzer (Jason: "SLOT for VNA-type calibration"): SHORT, OPEN and LOAD
    at the jacks' pins, a 25 ohm check standard, and a THRU.  Calibrating here puts the reference plane at the board's
    surface, so every other tile is measured from its pad with its own jack de-embedded (the jacks are all the same part).
    SHORT: the centre pin is ground, joined all round to the top pour (no launch void).  OPEN: the bare pin with its launch
    void.  LOAD: 4 mm of 50 ohm line into two 100 ohm in parallel (a matched line is still a match).  25 OHM: two 49.9 ohm at
    the end of 4.75 mm of line (VSWR 2, a known mismatch to check a calibration with).  THRU: 19.8 mm of line between two
    jacks."""
    t = rf_tile("n1", "calibration", [(0, 0), (1, 0), (2, 0)])
    t.jack("TL0", "SHORT", "GND", "in", "", launch=False)
    t.jack("BR0", "OPEN", "OPEN", "in", "")
    jl = t.jack("TL1", "LOAD", "LOAD", "in", "")
    jm = t.jack("BR1", "25 OHM", "MIS", "in", "")
    ja = t.jack("TL2", "THRU A", "THRU", "in", "", silk="THRU")
    jb = t.jack("BR2", "THRU B", "THRU", "out", "", silk="THRU")
    # LOAD: the line right from the pin to x 30.6, a 100 ohm up and a 100 ohm down from its end
    x = 30.6
    t.rf("LOAD", [(jl, "1"), (x, 4.75)])
    ra = t.add("R", "R0402 100R", "100", x, 3.5, 90, {"1": "LOAD", "2": "GND"}, label=None)
    rb = t.add("R", "R0402 100R", "100", x, 6.0, 270, {"1": "LOAD", "2": "GND"}, label=None)
    t.wire("LOAD", [(x, 4.75), (ra, "1")], width=0.29)
    t.wire("LOAD", [(x, 4.75), (rb, "1")], width=0.29)
    t.gnd_stub(ra, "2", (x, 2.1), sym=(0, 0))
    t.gnd_stub(rb, "2", (x, 7.4), sym=(0, 0))
    # 25 OHM: the line left from the pin to x 32.0, two 49.9 ohm the same way
    x = 32.0
    t.rf("MIS", [(jm, "1"), (x, 15.25)])
    rc = t.add("R", "R0402 49.9R", "49.9", x, 14.0, 90, {"1": "MIS", "2": "GND"}, label=None)
    rd = t.add("R", "R0402 49.9R", "49.9", x, 16.5, 270, {"1": "MIS", "2": "GND"}, label=None)
    t.wire("MIS", [(x, 15.25), (rc, "1")], width=0.29)
    t.wire("MIS", [(x, 15.25), (rd, "1")], width=0.29)
    t.gnd_stub(rc, "2", (x, 12.6), sym=(0, 0))
    t.gnd_stub(rd, "2", (x, 17.9), sym=(0, 0))
    # THRU: down from A, across, down into B, the corners cut at 45 degrees
    t.rf("THRU", [(ja, "1"), (47.75, 9.0), (48.75, 10.0), (57.25, 10.0), (58.25, 11.0), (jb, "1")])
    t.titles.append("Calibration")
    t.text(14.0, 2.4, "n1", 0.9, 0.17, "center")
    t.info(["SHORT and OPEN", "at the pin"], near=(13.5, 5.0))
    t.info(["2 x 100 ohm"], near=(36.0, 3.0))
    t.info(["VSWR 2:", "2 x 49.9 ohm"], near=(23.0, 13.0))
    t.info(["19.8 mm,", "about 115 ps"], near=(44.0, 14.0))
    t.result = "SHORT, OPEN and LOAD at the jacks' pins and a 19.8 mm THRU: a full SOLT calibration; the 25 ohm standard then reads |S11| = 1/3 (9.5 dB return loss)"
    t.notes = ["Calibration standards at the board surface.  SHORT: the centre pin poured to ground all round.  OPEN: the bare pin",
               "(fringing about 30 fF, to be measured against the NanoVNA's SMA open).  LOAD: 4 mm of 50 ohm line into 2 x 100 ohm.",
               "25 OHM: 2 x 49.9 ohm at the end of 4.75 mm of line, a verification standard (VSWR 2).  THRU: 19.8 mm of 50 ohm line,",
               "about 115 ps (enter it as the thru's delay).  Every jack on the boards is the same part, so a calibration here",
               "measures each tile from its pads with its jacks taken out."]
    return t


# ------------------------------------------------------------------------------------------------------- n2, n3 --
def tile_n2():
    """A resistive splitter: three 16.9 ohm in a star (50 / 3), every port 50 ohm, 6 dB from any port to either other, DC to
    6 GHz, no isolation between the outputs (6 dB of it).  IN at the right cell's top-left, OUT 1 and OUT 2 at the two
    bottom corners, the star between them so both outputs' lines are the same length (8.7 + 4.65 mm)."""
    t = rf_tile("n2", "resistive splitter", [(0, 1), (1, 1)])
    jin = t.jack("TL1", "IN", "IN", "in", "+20 dBm")
    j1 = t.jack("BR0", "OUT 1", "O1", "out", "")
    j2 = t.jack("BR1", "OUT 2", "O2", "out", "")
    xs, ys = 26.0, 10.6
    r0 = t.add("R", "R0402 16.9R", "16.9", xs, 9.25, 270, {"1": "IN", "2": "S"}, label=None)
    r1 = t.add("R", "R0402 16.9R", "16.9", xs - 1.6, ys, 0, {"1": "O1", "2": "S"}, label=None)
    r2 = t.add("R", "R0402 16.9R", "16.9", xs + 1.6, ys, 0, {"1": "S", "2": "O2"}, label=None)
    t.rf("IN", [(jin, "1"), (26.25, 7.0), (xs, 7.25), (r0, "1")])
    t.wire("S", [(r0, "2"), (xs, ys)], width=0.29)
    t.wire("S", [(r1, "2"), (r2, "1")], width=0.29)
    t.rf("O1", [(r1, "1"), (15.25, ys), (j1, "1")])
    t.rf("O2", [(r2, "2"), (36.75, ys), (j2, "1")])
    t.titles.append("Resistive splitter")
    t.text(10.0, 2.4, "n2", 0.9, 0.17, "center")
    t.info(["3 x 16.9 ohm", "DC-6 GHz", "-6 dB each way", "no isolation"], near=(1.2, 5.0))
    t.result = "-6.0 dB from IN to each OUT, DC to 6 GHz, every port 50 ohm; OUT 1 to OUT 2 also -6 dB (no isolation)"
    t.notes = ["Three 16.9 ohm (50 / 3) from a star to the three ports: each port sees 16.9 + (16.9 + 50) / 2 = 50 ohm, and each",
               "output gets half the input's voltage.  Symmetric, so any port is IN.  Compare n3's transformer splitter (3 dB, 25 dB",
               "of isolation, 0.5-400 MHz)."]
    return t


def tile_n3():
    """A transformer splitter: Mini-Circuits ADP-2-1+ (case CD636, 0.5-400 MHz, 3 dB plus 0.3, 25 dB between the outputs),
    turned 270 at the tile's middle so SUM faces the top jack and ports 1 and 2 the bottom corners on lines of the same
    length; pins 2 and 5 joined by a track under the body and kept off ground, as Mini-Circuits' layout PL-116 does."""
    t = rf_tile("n3", "transformer splitter", [(2, 1), (3, 1)])
    js = t.jack("TL1", "SUM", "S", "in", "+20 dBm")
    j1 = t.jack("BR0", "PORT 1", "P1", "out", "")
    j2 = t.jack("BR1", "PORT 2", "P2", "out", "")
    u = t.add("U", "ADP2_1", "ADP-2-1+", 26.0, 12.71, 270, {"1": "S", "3": "P1", "4": "P2", "6": "GND", "2": "TIE", "5": "TIE"},
              hide_value=True, label=None)
    t.rf("S", [(js, "1"), (26.25, 8.85), (23.461, 8.85), (u, "1")])
    t.rf("P1", [(u, "3"), (j1, "1")])
    t.rf("P2", [(u, "4"), (j2, "1")])
    t.wire("TIE", [(u, "2"), (u, "5")], width=0.6, silk=False)
    t.gnd_stub(u, "6", (30.6, 10.17), sym=(0, 0))
    t.titles.append("Transformer splitter")
    t.text(10.0, 2.4, "n3", 0.9, 0.17, "center")
    t.info(["ADP-2-1+", "0.5-400 MHz", "-3.2 dB each", "isolation 25 dB"], near=(1.2, 5.0))
    t.result = "-3.1 to -3.4 dB from SUM to each port, 0.5-400 MHz; 25-34 dB between port 1 and port 2 (the datasheet)"
    t.notes = ["Mini-Circuits ADP-2-1+: a transformer splitter (a centre-tapped winding with a resistor across its ends), so the two",
               "ports are isolated from each other: a combiner for two generators (the two DACs into one amplifier, for a two-tone",
               "intermodulation test) as well as a splitter.  Pins 2 and 5 are joined and must not be grounded."]
    return t


# ------------------------------------------------------------------------------------------------------- n4, n5 --
def tile_n4():
    """A quarter-wave open stub on the line from IN to OUT: 17.3 mm of the same coplanar waveguide, open at its end, a short
    circuit at the junction at 2.45 GHz (and 7.35 GHz): a notch.  The line's effective permittivity (about 3.1 on
    JLC04161H-7628) puts the notch within a few percent of 2.45 GHz; measure where it is."""
    t = rf_tile("n4", "quarter-wave stub", [(0, 2)])
    jin = t.jack("TL", "IN", "L", "in", "")
    jout = t.jack("BR", "OUT", "L", "out", "")
    t.rf("L", [(jin, "1"), (4.75, 9.0), (5.75, 10.0), (14.25, 10.0), (15.25, 11.0), (jout, "1")])
    t.stub("L", [(10.0, 10.0), (10.0, 2.0), (18.0, 2.0), (18.0, 3.3)])
    t.titles.append("Stub")
    t.text(14.0, 5.0, "n4", 0.9, 0.17, "center")
    t.info(["open stub", "17.3 mm", "notch near", "2.45 GHz"], near=(1.2, 12.0))
    t.result = "a notch near 2.45 GHz (and 7.35 GHz) 20 dB or more deep; 0 dB at DC, -3 dB about 0.6 GHz either side"
    t.notes = ["An open stub a quarter wavelength long looks like a short circuit at its other end: the line from IN to OUT is",
               "shorted at its middle at 2.45 GHz.  At DC and at 4.9 GHz (a half wave) it is open and the line passes.  The length",
               "is 17.3 mm for an effective permittivity of 3.1; the coplanar line's real one moves the notch a few percent."]
    return t


def tile_n5():
    """A low-pass: Mini-Circuits LFCN-1000+ (LTCC, 1206), DC-1000 MHz, 3 dB at 1.3 GHz, 30 dB from 1.9 to 5 GHz: the
    harmonics of a 915 MHz synthesizer off, and a clean LO."""
    t = rf_tile("n5", "low-pass", [(1, 2)])
    jin = t.jack("TL", "IN", "IN", "in", "")
    jout = t.jack("BR", "OUT", "OUT", "out", "")
    fl = t.add("FL", "LFCN1000", "LFCN-1000+", 13.0, 6.4, 0, {"1": "IN", "3": "OUT", "2": "GND", "4": "GND"}, hide_value=True, label=None)
    t.rf("IN", [(jin, "1"), (9.4, 4.75), (10.2, 5.55), (10.2, 6.4), (fl, "1")])
    t.rf("OUT", [(fl, "3"), (15.25, 6.4), (jout, "1")])
    t.gnd_stub(fl, "4", (13.0, 3.9), sym=(0, 0))
    t.gnd_stub(fl, "2", (13.0, 8.9), sym=(0, 0))
    t.titles.append("Low-pass")
    t.text(14.0, 2.4, "n5", 0.9, 0.17, "center")
    t.info(["LFCN-1000+", "DC-1 GHz", "-3 dB 1.3 GHz"], near=(1.2, 12.0))
    t.result = "0.3 dB at 500 MHz, 0.8 dB at 1 GHz, 3 dB at 1.3 GHz, 26 dB at 1.5 GHz, 30 dB from 1.9 to 5 GHz (the datasheet)"
    t.notes = ["Mini-Circuits LFCN-1000+, an LTCC low-pass in a 1206: a MAX2871 at 915 MHz has its second harmonic 30 dB down",
               "after it, and the synthesizer's square-ish output becomes a sine."]
    return t


# ------------------------------------------------------------------------------------------------------- n6, n7 --
def tile_n6():
    """A diode detector: 51 ohm across IN (the match), 10 nF in series, a Skyworks SMS7630-006LF pair as a voltage doubler
    (pin 2, an anode, on ground; pin 3, the joint, the RF; pin 1, a cathode, the output), 100 pF and 100 k on the output.
    Zero-bias Schottky: square law below about -20 dBm (the output in volts goes as the power), linear above (as the
    amplitude); 0.9 us of video time constant, so an AM envelope or a pulse comes through."""
    t = rf_tile("n6", "detector", [(2, 2)])
    jin = t.jack("TL", "IN", "IN", "in", "+10 dBm")
    jout = t.jack("BR", "OUT", "V", "out", "")
    r = t.add("R", "R0402 51R", "51", 6.3, 11.3, 270, {"1": "IN", "2": "GND"}, label=None)
    c = t.add("C", "C0402 10nF", "10n", 7.7, 10.0, 0, {"1": "IN", "2": "X"}, label=None)
    d = t.add("D", "SMS7630", "SMS7630", 10.6, 9.8, 180, {"3": "X", "2": "GND", "1": "V"}, hide_value=True, label=None)
    cv = t.add("C", "C0402 100pF", "100p", 13.4, 9.3, 90, {"1": "V", "2": "GND"}, label=None)
    rl = t.add("R", "R0402 100k", "100k", 14.6, 9.3, 90, {"1": "V", "2": "GND"}, label=None)
    t.rf("IN", [(jin, "1"), (4.75, 10.0), (c, "1")])
    t.wire("IN", [(6.3, 10.0), (r, "1")], width=0.29)
    t.gnd_stub(r, "2", (6.3, 12.8), sym=(0, 0))
    t.wire("X", [(c, "2"), (d, "3")], width=0.29)
    t.gnd_stub(d, "2", (11.54, 7.4), sym=(0, 0))
    t.wire("V", [(d, "1"), (11.54, 10.75), (15.25, 10.75), (jout, "1")])
    t.wire("V", [(13.4, 10.75), (cv, "1")])
    t.wire("V", [(14.6, 10.75), (rl, "1")])
    t.gnd_stub(cv, "2", (13.4, 7.6), sym=(0, 0))
    t.gnd_stub(rl, "2", (14.6, 7.6), sym=(0, 0))
    t.titles.append("Detector")
    t.text(15.8, 2.4, "n6", 0.9, 0.17, "center")
    t.info(["SMS7630 x 2", "zero bias", "OUT to a", "high-Z ADC"], near=(1.2, 14.0))
    t.result = "about 1 mV out for -30 dBm in and 0.1 V for -10 dBm (square law, then linear toward 1 V at +10 dBm), 10 MHz to 6 GHz"
    t.notes = ["A voltage doubler of two zero-bias Schottky diodes (SMS7630: Is 5 uA, so about 5 k of video resistance each with",
               "no bias).  Below about -20 dBm the output voltage is proportional to the RF power; above it, to the amplitude.",
               "Read OUT with the ADC at high impedance: 50 ohm would short it.  Compare the AD8318's log output on IQ-MOD."]
    return t


def tile_n7():
    """A bias-T: RF in on the top-left jack through 100 nF to RF+DC on the bottom-right, DC fed onto that line through
    27 nH, 330 nH and 10 uH in series (the 27 nH nearest the line, for the GHz end) from a test loop (a bench supply's clip,
    the GND loop beside it), with 100 nF across the DC.  For an active antenna, an LNA at the end of a cable, a varactor or a
    detector diode's bias."""
    t = rf_tile("n7", "bias-T", [(3, 2)])
    jrf = t.jack("TL", "RF", "RF", "in", "")
    jdc = t.jack("BR", "RF+DC", "RD", "out", "")
    cb = t.add("C", "C0402 100nF", "100n", 7.0, 10.6, 0, {"1": "RF", "2": "RD"}, label=None)
    l1 = t.add("L", "L0402 27nH", "27n", 11.4, 9.4, 90, {"1": "RD", "2": "N1"}, label=None)          # pad 1 down, on the line
    l2 = t.add("L", "L0603 330nH", "330n", 11.4, 6.9, 90, {"1": "N1", "2": "N2"}, label=None)
    l3 = t.add("L", "L1210 10uH", "10u", 14.0, 5.3, 270, {"1": "N2", "2": "DC"}, label=None)          # pad 1 up
    cd = t.add("C", "C0402 100nF", "100n", 16.4, 8.6, 270, {"1": "DC", "2": "GND"}, label=None)        # pad 1 up
    tp = t.loop("DC", 18.4, 5.0, 90, "DC", label_at="hide")
    tg = t.loop("GND", 2.0, 17.0, 90, "GND", label_at="hide")
    t.rf("RF", [(jrf, "1"), (4.75, 10.6), (cb, "1")])
    t.rf("RD", [(cb, "2"), (15.25, 10.6), (jdc, "1")])
    t.wire("RD", [(11.4, 10.6), (l1, "1")])
    t.wire("N1", [(l1, "2"), (l2, "1")])
    t.wire("N2", [(l2, "2"), (11.4, 3.9), (l3, "1")])
    t.wire("DC", [(l3, "2"), (14.0, 7.6), (16.4, 7.6), (cd, "1")])
    t.wire("DC", [(16.4, 7.6), (18.4, 7.6), (tp, "1")])
    t.gnd_stub(cd, "2", (16.4, 10.0), sym=(0, 0))
    t.gnd_stub(tg, "1", (3.6, 15.6), sym=(0, 0))
    t.titles.append("Bias-T")
    t.text(4.4, 16.0, "n7", 0.9, 0.17, "left")
    t.text(18.4, 1.8, "DC", 0.8, 0.15, "center")
    t.text(4.4, 17.8, "GND", 0.8, 0.15, "left")
    t.info(["2 MHz-3 GHz", "100 mA, 16 V"], near=(1.2, 12.2), reach=3.0)
    t.result = "RF to RF+DC within 1 dB from about 2 MHz to 3 GHz; the DC loop's voltage on RF+DC, none on RF"
    t.notes = ["100 nF passes the RF and blocks the DC; 10 uH + 330 nH + 27 nH pass the DC and block the RF (each inductor for its",
               "own decade: 10 uH is 630 ohm at 10 MHz, 27 nH 400 ohm at 2.4 GHz).  Up to 100 mA (the 330 nH's rating) and 16 V (the",
               "capacitors').  A bench supply's clips on the DC and GND loops.  Never put RF+DC into a jack that cannot take the DC."]
    return t


# ------------------------------------------------------------------------------------------------------- n8, n9 --
def tile_n8():
    """A digital step attenuator: pSemi PE43711 (QFN-24 4 x 4), 9 kHz-6 GHz, 0-31.75 dB in 0.25 dB steps, set by hand or by
    the FPGA (Jason, Prompt 18: "If the FPGA pins are high impedance, this would be nice to do manually").  An 8-way DIP
    switch above the chip: way 1 is SPI (P/S: off = parallel, the chip's "direct parallel" mode with LE held high by 100 k,
    which pSemi calls "ideal for manual control ... switches or jumpers"; on = serial), ways 2-8 the seven bits 0.25-16 dB
    (on = that much more attenuation), each pulled down by 100 k standing in the gap beside its line.  In serial mode the
    seven bits must be off (the datasheet: the parallel inputs grounded), and SDATA, SCLK and LE come from Pmod IO2, IO3
    and IO4 (RF-MOD's SPI lines).  Either way the chip needs the Pmod's 3.3 V (150 uA): it is an active switch array.
    100 nF blocks at both RF pins (they must sit at 0 V).  Two cells: IN at the left cell's top-left, OUT at the right
    cell's bottom-right, the chip between them; the plug below the left cell."""
    t = rf_tile("n8", "step attenuator", [(0, 3), (1, 3)], supply="3.3 V")
    t.fine = True
    t.pwr_flags.append("VCC")                    # the host's 3.3 V through the plug: no regulator pin drives it here
    jin = t.jack("TL0", "IN", "IN", "in", "+20 dBm")
    jout = t.jack("BR1", "OUT", "OUT", "out", "")
    cx, cy = 20.75, 16.5
    bits = ["B0", "B1", "B2", "B3", "B4", "B5", "B6"]          # 0.25, 0.5, 1, 2, 4, 8, 16 dB
    pins = {"5": "RA", "14": "RB", "2": VCC, "3": "PS", "16": "/PMOD4", "17": "/PMOD3", "18": "/PMOD2", "25": "GND",
            "1": "B0", "24": "B1", "23": "B2", "22": "B3", "21": "B4", "20": "B5", "19": "B6"}
    for n in ("4", "6", "7", "8", "9", "10", "11", "12", "13", "15"):
        pins[n] = "GND"
    u = t.add("U", "PE43711", "PE43711", cx, cy, 0, pins, hide_value=True, label=None)
    L, R, T = cx - 1.962, cx + 1.962, cy - 1.962
    # the DIP: pads 1-8 along its lower row are the switched nodes (way 1 SPI, ways 2-8 the bits), 9-16 along the upper row
    # the 3.3 V; ON is toward the upper row
    dx0, dy0 = cx, 5.03
    nodes = ["PS"] + bits
    dpins = {str(k): nodes[k - 1] for k in range(1, 9)}
    dpins.update({str(17 - k): VCC for k in range(1, 9)})
    sw = t.add("SW", "DIP8", "SPI / dB", dx0, dy0, 0, dpins, hide_value=True)
    xk = [dx0 + (k - 4.5) * 1.27 for k in range(1, 9)]
    yb = dy0 + 3.81                                            # the lower row's pad centres
    t.wire(VCC, [(sw, "16"), (sw, "9")], width=F)
    t.wire(VCC, [(xk[7], dy0 - 3.81), (27.3, dy0 - 3.81)], width=F)
    t.via(VCC, 27.3, dy0 - 3.81, fine=True)
    # pull-downs: one 100 k in each gap, its lower pad tied left to its line, its upper pad to a ground via above it
    ys = 11.55
    for k in range(8):
        xr = xk[k] + 0.635
        r = t.add("R", "R0402 100k", "100k", xr, ys - 0.51, 90, {"1": nodes[k], "2": "GND"}, label=None)      # pad 1 down
        t.wire(nodes[k], [(r, "1"), (xk[k], ys)], width=F)
        t.gnd_stub(r, "2", (xr, yb + 0.76 + 0.127 + 0.24), sym=(0, 0), fine=True)
    # the lines: from the DIP's lower pads straight down past the pull-downs, then each jogs to its chip pin
    jog = {"B6": 13.65, "B5": 13.25, "B4": 12.85, "B3": 12.45, "B2": 12.05, "B1": 13.65}
    top_pin = {"B1": cx - 1.25, "B2": cx - 0.75, "B3": cx - 0.25, "B4": cx + 0.25, "B5": cx + 0.75, "B6": cx + 1.25}
    pin_of = {"B1": "24", "B2": "23", "B3": "22", "B4": "21", "B5": "20", "B6": "19"}
    for k, net in enumerate(nodes):
        if net in jog:
            t.wire(net, [(sw, str(k + 1)), (xk[k], jog[net]), (top_pin[net], jog[net]), (u, pin_of[net])], width=F)
    t.wire("B0", [(sw, "2"), (xk[1], cy - 1.25), (u, "1")], width=F)                 # C0.25 from the chip's left side
    t.wire("PS", [(sw, "1"), (xk[0], cy - 0.25), (u, "3")], width=F)                 # P/S, the same way, one row lower
    # 3.3 V to VDD: a via between the two left lines; a 100 nF to its left
    t.wire(VCC, [(u, "2"), (xk[0] + 0.635, cy - 0.75)], width=F)
    t.via(VCC, xk[0] + 0.635, cy - 0.75, fine=True)
    cd = t.add("C", "C0402 100nF", "100n", 15.0, 14.6, 90, {"1": VCC, "2": "GND"}, label=None)            # pad 1 down
    t.wire(VCC, [(cd, "1"), (15.0, 15.9)], width=F)
    t.via(VCC, 15.0, 15.9, fine=True)
    t.gnd_stub(cd, "2", (15.0, 13.3), sym=(0, 0), fine=True)
    # ground pins into the exposed pad, four vias in it
    for n, pt in (("4", (L + 0.85, cy + 0.25)), ("6", (L + 0.85, cy + 1.25)), ("13", (R - 0.85, cy + 1.25)), ("15", (R - 0.85, cy + 0.25))):
        t.wire("GND", [(u, n), pt], width=F, silk=False)
    for k, n in enumerate(("7", "8", "9", "10", "11", "12")):
        t.wire("GND", [(u, n), (cx - 1.25 + 0.5 * k, cy + 1.1)], width=F, silk=False)
    for (vx, vy) in ((cx - 0.55, cy - 0.55), (cx + 0.55, cy - 0.55), (cx - 0.55, cy + 0.55), (cx + 0.55, cy + 0.55)):
        t.gnd_stub(u, "25", (vx, vy), sym=(0, 0), fine=True)
    # RF: IN down the left cell and along y cy+0.75 into RF1; RF2 out through the block to the right cell's OUT
    ci = t.add("C", "C0402 100nF", "100n", 16.2, cy + 0.75, 0, {"1": "IN", "2": "RA"}, label=None)
    co = t.add("C", "C0402 100nF", "100n", 24.6, cy + 0.75, 0, {"1": "RB", "2": "OUT"}, label=None)
    t.rf("IN", [(jin, "1"), (4.75, cy + 0.75), (ci, "1")])
    t.wire("RA", [(ci, "2"), (u, "5")], width=0.25)
    t.wire("RB", [(u, "14"), (co, "1")], width=0.25)
    t.rf("OUT", [(co, "2"), (25.6, cy + 0.75), (27.1, 15.25), (jout, "1")])
    # the Pmod plug below the left cell; SI, SCLK and LE from the chip's right side to vias, then on the back down past the
    # chip and west along the bottom edge to the plug's pads (LE nearest the cell, so the lines peel off without crossing)
    pm = t.add("J", "PMOD", "Pmod", 2.97, 24.25, 0, {"6": "/PMOD4", "8": "/PMOD3", "10": "/PMOD2", "3": "GND", "4": "GND", "1": VCC, "2": VCC},
               hide_value=True)
    t.wire(VCC, [(pm, "1"), (pm, "2")], silk=False)
    for n, net, vx, vy, yh, xp, pad in (("18", "/PMOD2", 25.3, cy - 1.25, 20.9, 6.78, "10"),
                                        ("17", "/PMOD3", 24.6, cy - 0.75, 20.3, 4.24, "8"),
                                        ("16", "/PMOD4", 23.9, cy - 0.25, 19.7, 1.70, "6")):
        t.wire(net, [(u, n), (vx, vy)], width=F)
        if net == "/PMOD4":                                  # LE: split where its pull-up joins (a via there)
            t.wire(net, [(vx, vy), (vx, yh), (xp, yh)], width=F, layer="B.Cu", silk=False, fine=True)
            t.wire(net, [(xp, yh), (pm, pad)], width=F, layer="B.Cu", silk=False, fine=True)
        else:
            t.wire(net, [(vx, vy), (vx, yh), (xp, yh), (pm, pad)], width=F, layer="B.Cu", silk=False, fine=True)
    rle = t.add("R", "R0402 100k", "100k", 2.6, 18.6, 90, {"1": "/PMOD4", "2": VCC}, label=None)          # pad 1 down
    t.wire("/PMOD4", [(rle, "1"), (2.6, 19.7), (1.70, 19.7)], width=F)
    t.wire(VCC, [(rle, "2"), (2.6, 17.3)], width=F)
    t.via(VCC, 2.6, 17.3, fine=True)
    t.titles.append("Attenuator")
    t.text(9.0, 10.0, "n8", 0.9, 0.17, "center")
    t.info(["PE43711", "9 kHz-6 GHz", "0-31.75 dB"], near=(6.2, 11.6), reach=4.0)
    t.info(["1: SPI", "2-8: .25 .5 1", "2 4 8 16 dB", "up: on"], near=(28.0, 2.0), reach=4.0)
    t.info(["SPI on: 2-8 off"], near=(26.0, 10.6), reach=4.0)
    t.result = "0 to 31.75 dB in 0.25 dB steps (1.5-2.8 dB of loss at 0 dB, rising with frequency), set by the switches or by an 8-bit word over the Pmod"
    t.notes = ["pSemi PE43711.  By hand: SPI off, the bits on the switch (direct parallel mode: P/S low, LE held high by 100 k when the",
               "FPGA's pin floats).  By the FPGA: every bit off, SPI on, then shift 8 bits (bit 7 = 0, then 4 x dB, least significant",
               "first) on SDATA (IO2) with SCLK (IO3) while LE (IO4) is low, and raise LE.  Either way it needs the Pmod's 3.3 V.",
               "Below 48 MHz it takes less power: about +9.5 dBm under 0.5 MHz and +15 dBm at 5 MHz (+23 dBm above 48 MHz)."]
    return t


def tile_n9():
    """A one-transistor oscillator on the Pmod's 3.3 V (switched): a Clapp (series-tuned Colpitts) on an MMBT3904 as an
    emitter follower, 10 uH in series with a BB133 varactor from the base (through 1 nF) to ground, 220 pF base to emitter
    and 220 pF emitter to ground, 100 k from the supply to the base (about 1.5 mA), 680 ohm in the emitter.  The varactor's
    cathode sits at (3.3 V + TUNE) / 2 through two 100 k, so TUNE's -2..+2 V moves it from 9.6 to 11.5 MHz (about 10.5 MHz
    at 0 V); 2.2 pF from TUNE to the same node lets a tone near the oscillator's frequency pull it into lock.  OUT through
    22 pF from the emitter (about -22 dBm into 50 ohm).  The transistor stands over the switch's FET (collector down, to
    the supply); the tank fills the top-right quarter; the supply reaches the bias and the tank, and the output reaches the
    OUT jack's centre pin, on the back."""
    t = rf_tile("n9", "oscillator", [(3, 0)], supply="3.3 V")
    jt = t.jack("TL", "TUNE", "TUNE", "in", "+-2 V")
    jo = t.jack("BR", "OUT", "OUT", "out", "")
    power_header(t, rail=VCC, local="VS", pour=True)
    q = t.add("Q", "MMBT3904", "MMBT3904", 9.0, 13.6, 270, {"1": "B", "2": "E", "3": "VS"}, hide_value=True, label=None)
    c1 = t.add("C", "C0402 220pF", "220p", 9.0, 11.2, 0, {"1": "E", "2": "B"}, label=None)
    c2 = t.add("C", "C0402 220pF", "220p", 8.8, 9.5, 90, {"1": "E", "2": "GND"}, label=None)               # pad 1 down
    re = t.add("R", "R0402 680R", "680", 6.6, 9.1, 180, {"1": "E", "2": "GND"}, label=None)               # pad 1 right
    co = t.add("C", "C0402 22pF", "22p", 6.6, 10.2, 180, {"1": "E", "2": "OUT"}, label=None)
    cb = t.add("C", "C0402 1nF", "1n", 10.6, 9.6, 270, {"1": "A", "2": "B"}, label=None)                   # pad 1 up
    r1 = t.add("R", "R0402 100k", "100k", 11.5, 11.1, 0, {"1": "B", "2": "VS"}, label=None)
    l1 = t.add("L", "L1210 10uH", "10u", 14.6, 7.6, 180, {"1": "T", "2": "A"}, label=None)                 # pad 1 right
    d1 = t.add("D", "BB133", "BB133", 18.2, 7.6, 270, {"1": "T", "2": "GND"}, hide_value=True, label=None)
    rb = t.add("R", "R0402 100k", "100k", 17.0, 3.4, 270, {"1": "TUNE", "2": "T"}, label=None)
    ci = t.add("C", "C0402 2.2pF", "2.2p", 15.6, 3.4, 270, {"1": "TUNE", "2": "T"}, label=None)
    ra = t.add("R", "R0402 100k", "100k", 18.4, 3.4, 270, {"1": "VS", "2": "T"}, label=None)
    cd = t.add("C", "C0402 100nF", "100n", 10.3, 16.4, 270, {"1": "VS", "2": "GND"}, label=None)
    # the transistor: collector straight up from the FET's drain, the emitter's parts to its left, the base's up and right
    t.wire("VS", [HDR_VS, (9.0, 17.6), (q, "3")])
    t.wire("VS", [(9.0, 15.6), (10.3, 15.6), (cd, "1")])
    t.gnd_stub(cd, "2", (10.3, 18.2), sym=(0, 0))
    t.wire("E", [(q, "2"), (8.05, 11.2), (c1, "1")])
    t.wire("E", [(8.05, 11.2), (7.6, 10.75), (7.6, 9.1), (re, "1")])
    t.wire("E", [(7.6, 10.2), (co, "1")])
    t.wire("E", [(c1, "1"), (8.8, 10.5), (c2, "1")])
    t.gnd_stub(c2, "2", (8.8, 8.0), sym=(0, 0))
    t.gnd_stub(re, "2", (5.0, 9.1), sym=(0, 0))
    t.wire("B", [(q, "1"), (9.95, 11.2), (c1, "2")])
    t.wire("B", [(9.95, 11.2), (10.6, 10.6), (cb, "2")])
    t.wire("B", [(9.95, 11.2), (r1, "1")])
    t.wire("A", [(cb, "1"), (10.6, 7.6), (l1, "2")])
    # the tank's far node T: L1's right pad, the varactor, the bias from the supply and from TUNE, the injection capacitor
    t.wire("T", [(l1, "1"), (17.0, 7.6), (17.0, 5.9), (18.2, 5.9), (d1, "1")])
    t.wire("T", [(17.0, 5.9), (rb, "2")])
    t.wire("T", [(17.0, 4.8), (15.6, 4.8), (ci, "2")])
    t.wire("T", [(17.0, 4.8), (18.4, 4.8), (ra, "2")])
    t.gnd_stub(d1, "2", (18.2, 10.0), sym=(0, 0))
    t.wire("TUNE", [(jt, "1"), (9.0, 4.75), (9.0, 2.0), (17.0, 2.0), (rb, "1")])
    t.wire("TUNE", [(15.6, 2.0), (ci, "1")])
    # the supply on the back round the OUT jack's bottom and right to a via beside R1, then on the front to the base's bias
    # and up the tile's right edge to the tank's
    t.wire("VS", [HDR_VS, (9.4, 19.35), (10.9, 19.35)])
    t.wire("VS", [(10.9, 19.35), (10.9, 20.5), (20.6, 20.5), (20.6, 10.7), (12.9, 10.7)], layer="B.Cu", silk=False)
    t.wire("VS", [(12.9, 10.7), (r1, "2")])
    t.wire("VS", [(12.9, 10.7), (19.6, 10.7), (19.6, 1.2), (18.4, 1.2), (ra, "1")])
    # the output: 22 pF from the emitter, a via, and the back to the OUT jack's centre pin
    t.wire("OUT", [(co, "2"), (5.0, 10.2)])
    t.wire("OUT", [(5.0, 10.2), (9.6, 14.8), (10.05, 15.25), (jo, "1")], layer="B.Cu", silk=False)
    t.titles.append("Oscillator")
    t.text(1.2, 9.6, "n9", 0.9, 0.17, "left")
    t.result = "about 10.5 MHz with TUNE at 0 V, 9.6 MHz at -2 V and 11.5 MHz at +2 V; about -22 dBm into 50 ohm; locks to a tone on TUNE within a few kHz of it"
    t.notes = ["A Clapp oscillator: the emitter follower's 220 pF / 220 pF divider feeds back what the series LC (10 uH and the",
               "BB133) passes at its resonance, f = 1 / (2 pi sqrt(L C)) with C the three capacitors in series.  The varactor's",
               "cathode is at (3.3 V + TUNE) / 2, so TUNE tunes it (an FM transmitter from a DAC, or the control of a PLL closed in",
               "the FPGA); a tone on TUNE near f also couples through 2.2 pF and the oscillator locks to it over a range that grows",
               "with the tone's amplitude (Adler's equation).  Compare its phase noise with the MAX2871's.  The switch turns it off."]
    return t


def tile_n10():
    """A 1:1 transformer (Mini-Circuits TC1-1TG2+, 0.4-500 MHz, separate windings) in the top-right quarter: IN over its
    top onto the primary, the secondary down onto the OUT jack, whose four legs are a ground of their own (an island with
    no plane within 5.6 mm), so OUT floats.  A balun (OUT's centre and shell are the two halves of a dipole, the tutorial's
    on-the-air feed) and a ground-loop breaker between an instrument and the host.  The centre tap is left open."""
    t = rf_tile("n10", "1:1 transformer", [(2, 3)])
    ji = t.jack("TL", "IN", "IN", "in", "+20 dBm")
    jo = t.jack("BR", "OUT", "OUT", "out", "", shield="ISO")
    u = t.add("T", "TC1_1TG2", "TC1-1TG2+", 14.6, 6.4, 180, {"6": "IN", "4": "GND", "1": "OUT", "3": "ISO"}, hide_value=True, label=None)
    t.rf("IN", [(ji, "1"), (9.5, 4.75), (9.5, 2.8), (15.87, 2.8), (u, "6")])
    t.gnd_stub(u, "4", (12.2, 4.9), sym=(0, 0))
    t.wire("OUT", [(u, "1"), (15.87, 9.5), (15.25, 10.1), (jo, "1")], width=0.29)
    t.wire("ISO", [(u, "3"), (13.33, 10.0), (12.7, 10.6), (12.7, 17.8), (17.8, 17.8), (17.8, 12.7)], width=0.4)
    t.voids.append((15.25, 15.25, 5.6, "all"))
    t.titles.append("Balun")
    t.text(1.8, 10.4, "n10", 0.9, 0.17, "left")
    t.info(["TC1-1TG2+", "0.4-500 MHz", "OUT floats"], near=(1.2, 12.5))
    t.result = "0.3 dB of loss at 10 MHz, 0.5 dB at 100 MHz, 1.8 dB at 500 MHz (the datasheet); OUT's shell is not ground"
    t.notes = ["Mini-Circuits TC1-1TG2+: two windings, so OUT's centre and shell are a balanced pair: a balun for a dipole (an SMA",
               "to two-clip lead on OUT), or a break in a ground loop between the host and a mains-earthed instrument.  OUT's legs",
               "are their own net with no copper of the board's ground within 5.6 mm on any layer."]
    return t


def tile_n11():
    """A 1:4 transformer (Mini-Circuits TC4-1W+, 3-800 MHz) in the top-right quarter: IN on the primary, the secondary from
    ground to OUT, so OUT's impedance is four times IN's and its voltage twice.  A DIP switch in the bottom-left quarter puts
    200 ohm (IN then reads 50) or 49.9 ohm (IN reads 12.5) across OUT: the turns ratio squared, measured."""
    t = rf_tile("n11", "1:4 transformer", [(3, 3)])
    ji = t.jack("TL", "IN", "IN", "in", "+20 dBm")
    jo = t.jack("BR", "OUT", "OUT", "out", "")
    u = t.add("T", "TC4_1W", "TC4-1W+", 14.6, 6.4, 180, {"6": "IN", "4": "GND", "1": "OUT", "3": "GND"}, hide_value=True, label=None)
    t.rf("IN", [(ji, "1"), (9.5, 4.75), (9.5, 2.8), (15.87, 2.8), (u, "6")])
    t.gnd_stub(u, "4", (12.2, 4.9), sym=(0, 0))
    t.gnd_stub(u, "3", (12.2, 7.9), sym=(0, 0))
    t.wire("OUT", [(u, "1"), (15.87, 9.5), (15.25, 10.1), (jo, "1")], width=0.29)
    sw = t.add("SW", "DIP2", "LOAD", 6.0, 15.0, 90, {"1": "OUT", "2": "OUT", "4": "L1", "3": "L2"}, hide_value=True)
    r1 = t.add("R", "R0402 200R", "200", 2.19, 18.6, 270, {"1": "L1", "2": "GND"}, label=None)
    r2 = t.add("R", "R0402 49.9R", "49.9", 2.19, 11.4, 90, {"1": "L2", "2": "GND"}, label=None)
    t.wire("OUT", [(15.25, 11.0), (11.0, 11.0), (11.0, 15.0), (sw, "1")])
    t.wire("OUT", [(sw, "1"), (sw, "2")])
    t.wire("L1", [(sw, "4"), (r1, "1")])
    t.wire("L2", [(sw, "3"), (r2, "1")])
    t.gnd_stub(r1, "2", (3.6, 19.1), sym=(0, 0))
    t.gnd_stub(r2, "2", (2.19, 9.6), sym=(0, 0))
    t.titles.append("Transformer")
    t.text(8.6, 11.6, "n11", 0.9, 0.17, "center")
    t.info(["2: 49.9 ohm"], near=(2.9, 9.6), reach=2.0)
    t.info(["1: 200 ohm"], near=(3.6, 18.8), reach=3.0)
    t.result = "IN reads 50 ohm with switch 1 on (200 ohm across OUT) and 12.5 ohm with switch 2; OUT's voltage is twice IN's, 0.8 dB of loss at 10 MHz"
    t.notes = ["Mini-Circuits TC4-1W+: the secondary has twice the primary's turns, so it carries twice the voltage at half the",
               "current and any load on OUT looks a quarter of itself at IN.  200 ohm on OUT (switch 1) is a match; 49.9 ohm (switch 2)",
               "reads 12.5 ohm.  The centre tap is left open."]
    return t


def tiles():
    return [tile_n1(), tile_n2(), tile_n3(), tile_n4(), tile_n5(), tile_n6(), tile_n7(), tile_n8(), tile_n9(), tile_n10(),
            tile_n11()]


PMOD_HOST = "n8's bottom edge"
PMOD_VCC_TEXT = "which powers n8 and n9, the board's only supply; the lines are 3.3 V CMOS):"
PMOD_NAMES = {"/PMOD2": "SDATA (SI) of n8's PE43711", "/PMOD3": "SCLK of n8", "/PMOD4": "LE of n8"}
HANDBOOK_INTRO = [
    "Eleven tiles on sixteen 20 mm cells, four layers, no USB.  Nine of them are passive and need nothing; n8 (the step",
    "attenuator) and n9 (the oscillator) run on the host's 3.3 V through the Pmod plug under n8, so plug the board into the",
    "host's Pmod (or a Pmod cable) to use them, even to set n8 by hand on its switch.  Every tile's input is its top-left jack and its output its bottom-right jack,",
    "every 50 ohm line is coplanar waveguide with a via fence and every jack has RF-MOD's launch (no plane under its centre",
    "pin), except n1's SHORT, whose centre pin is the ground pour.  On the board a tile's label is in mixed case and a port's",
    "name in capitals."]
HANDBOOK_SECTIONS = [
    ["## The tiles together", "",
     "1. **Calibrate first.**  n1's SHORT, OPEN and LOAD and its THRU calibrate a NanoVNA, or IQ-MOD's reflectometer (q1,",
     "   q2 and q5), at the board's surface; the 25 OHM standard checks the result (|S11| = 1/3).  Every tile's jacks are the",
     "   same part, so a tile measured afterwards is measured from its pads.",
     "2. **Impedance.**  n1's 25 OHM standard and n11's transformer with its 200 ohm or 49.9 ohm load on PhMOD's",
     "   reflection bridge (h7) or the VNA: points on the Smith chart, a match across a band, the turns ratio squared.",
     "3. **Splitting and combining.**  n2 (resistive, DC-6 GHz, no isolation) against n3 (transformer, 0.5-400 MHz, 25 dB",
     "   of isolation).  The two DACs combined through n3 into an amplifier make a two-tone intermodulation test, with n8",
     "   setting the level in 0.25 dB steps, by hand on its switch or from the FPGA.",
     "4. **Power.**  n8 makes a known level; n6 turns power into volts (square law at the bottom) to set against IQ-MOD's",
     "   AD8318 (log); compression points and IP3 of every amplifier and mixer on the boards follow.",
     "5. **Lines and filters.**  n4's stub and n5's low-pass swept by RF-MOD's synthesizer into a detector, or on the VNA.",
     "6. **An oscillator.**  n9 on the ADC; a DAC on TUNE tunes it (DC) or locks it (a tone near its frequency): the",
     "   lock range against the tone's amplitude, FM, and its phase noise against the MAX2871's.",
     "7. **On the air.**  n10 feeds the tutorial's HF dipole balanced; n7 powers an active antenna or an LNA through its",
     "   cable.",
     "",
     "Levels to remember: n8 takes +23 dBm above 48 MHz but only about +9.5 dBm below 0.5 MHz, and its switch's way 1",
     "(SPI) must be off for the bits to count, the bits off for SPI; n6 wants +10 dBm at most",
     "and a high-impedance load; n7 passes 100 mA and 16 V; n9 gives about -22 dBm."],
]

GND_LOOPS = [(3.0, 30.0), (3.0, 70.0), (97.0, 30.0), (97.0, 84.0)]
HOLES = []                                    # plugged into a host's Pmod: held by the plug; feet as on RF-MOD
FEET = [(5.0, 5.0), (95.0, 5.0), (95.0, 95.0), (5.0, 85.0)]
SLOTS = []
RAIL_POURS = [(VCC, 0.6, 0.6, 99.4, 99.4, 0)]  # the Pmod's 3.3 V under the whole board on L3
BACK_WIRES = []
FRONT_WIRES = []
FRONT_TEXT = []
BACK_TEXT_X = 50.0
QR_AT = (13.0, 23.6)                           # under n1's left cell and the gutter: no hole between its two jacks and n2's line
BACK_TEXT = ["AMOD-N: passive RF and analog blocks.  IN is each",
             "tile's top-left jack, OUT its bottom-right.  No USB:",
             "n8 and n9 run on the Pmod's 3.3 V when it is plugged",
             "in; everything else needs nothing.  See the handbook."]



import backplots as BP
# The back panels (gen_pcb.back_panels, Prompt 18): under each tile, what a user must know while cabling it.
BACK = {
    "n1": ["SHORT, OPEN,", "LOAD at the pin", "25 OHM: VSWR 2", "THRU 115 ps", "tiles measure", "from their pads"],
    "n2": ["DC-6 GHz", "-6 dB each way", "no isolation", "IN max +20 dBm"],
    "n3": ["0.5-400 MHz", "-3.2 dB each way", "isolation 25 dB", "a combiner too"],
    "n4": ["notch 2.45 GHz", "and 7.35 GHz", "50 ohm"],
    "n5": ["DC-1 GHz", "-3 dB 1.3 GHz", "-30 dB 1.9-5 G"],
    "n6": ["IN < +10 dBm", "OUT to a", "HIGH-Z ADC", "square law", "below -20 dBm"],
    "n7": ["DC 16 V max", "100 mA max", "RF+DC has DC:", "mind its load"],
    "n8": ["NEEDS THE PMOD'S 3.3 V", "by hand: SPI off, bits on", "FPGA: bits off, SPI on", "IN max +23 dBm, +9.5 dBm", "below 0.5 MHz"],
    "n9": ["Pmod 3.3 V", "slide up: on", "TUNE +-2 V", "OUT -22 dBm"],
    "n10": ["OUT floats", "0.4-500 MHz", "0.25 W, 30 mA"],
    "n11": ["3-800 MHz", "OUT: 2x V,", "4x the Z", "1: 200, 2: 49.9"],
}
BACK_PLOTS = {
    "n3": BP.points([(0.5e6, -30.1), (10e6, -34.5), (120e6, -28.2), (200e6, -25.6), (400e6, -25.4)], ylim=(-40.0, 0.0),
                     yt=("0", "-40 dB"), name="isolation"),
    "n4": BP.open_stub(2.45e9),
    "n5": BP.points([(10e6, -0.1), (500e6, -0.3), (1000e6, -0.8), (1300e6, -3.0), (1500e6, -25.9), (2000e6, -49.5), (5000e6, -30.0),
                      (5500e6, -20.0)], ylim=(-60.0, 0.0), yt=("0", "-60 dB"), name=""),
    "n9": BP.clapp(),
}


if __name__ == "__main__":
    ts = tiles()
    cells = [c for t in ts for c in t.cells]
    assert len(cells) == 16 and len(set(cells)) == 16, cells
    jacks = [(t.id + " " + j["label"], *t.to_board((j["x"], j["y"]))) for t in ts for j in t.jacks]
    bad = G.check_spacing(jacks)
    print("%d tiles, %d jacks, %d parts; jack pairs closer than %.1f mm: %s" % (len(ts), len(jacks), sum(len(t.parts) for t in ts), G.MIN_JACK_SPACING, bad or "none"))
    for t in ts:
        print("  %-4s %-20s %2d parts  %s" % (t.id, t.name, len(t.parts), t.result[:90]))
