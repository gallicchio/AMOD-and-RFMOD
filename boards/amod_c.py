"""AMOD-C: conversion, rev A (Prompt 19).  Sixteen cells, four layers, USB-C power on c1 as AMOD-A's a1.  Power
conversion (a buck and an LDO under an electronic load, a charge pump the FPGA clocks) and data conversion (a
second-order delta-sigma with its integrators on jacks, a track-and-hold, a comparator that makes the host's DAC a SAR
or tracking ADC), the switched capacitors both use (a filter chip and a capacitor-and-two-switches resistor), and the
component-level stages Analog Devices' university labs teach (a differential pair on a current mirror, common emitter
against cascode, a precision rectifier, a 555).  `docs/ADI_LABS_SURVEY.md` has the survey; PLAN.md sections 12 and 13
the decisions.

Jason, Prompt 18: "Whole areas that we are missing include power regulation and other component-level circuits, but
something like a switched capacitor filter or details of their Delta - Sigma Modulator, if there is room, might be
worth it."

L1 the parts and the drawn wires, L2 ground, L3 the rails (+5 V under the board; -5 V in the gutter under row 0, down
the left margin and along the bottom margin; +3.3 V in the gutters under rows 1 and 2, joined down the right margin),
L4 ground with the Pmod lines and the back-side text.  Every powered tile has the standard header
(tiles.power_header): a slide switch and a P-FET, so its rail is dead until the slider is up.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, HERE)
import tiles as T
from tiles import Tile, power_header, HDR_VS
import geometry as G
from amod_a import power_tile

STEM = "amod_c"
LAYERS = 4


# ------------------------------------------------------------------------------------------------------------ c1 --
def tile_c1():
    return power_tile("c1", sections=["Regulators", "Switched capacitors"])


def vs_up(t, x=10.6, y=9.0, dx=0.0):
    """VS from the header's FET: on the front to a via at (x, 18.5), up the back to a via at (x, y); returns (x, y)."""
    t.wire("VS", [HDR_VS, (8.54, 18.5), (x, 18.5)])
    t.wire("VS", [(x, 18.5), (x, y)], layer="B.Cu", silk=False)
    return (x, y)


def rail(t, net, pt, gutter):
    """A rail from a point in the tile to its strip: a via at the point, the back to a via in the gutter at the same x
    (gutter: "below" 20.5, "above" -0.75, "margin" 21.0, the bottom margin under row 3)."""
    y = {"below": 20.5, "above": -0.75, "margin": 21.0}[gutter]
    t.wire(net, [pt, (pt[0], y)], layer="B.Cu", silk=False)
    t.via(net, pt[0], y)


# ------------------------------------------------------------------------------------------------------------ c4 --
def tile_c4():
    """A switched-capacitor filter: the MAX7410 (5th-order Butterworth, fc = fCLK / 100, 5 V) clocked from Pmod IO3
    through an SN74LV1T34 (the clock pin wants 4.5 V); IN terminated in 49.9 ohm and AC-coupled into the chip's input,
    biased at COM (2.5 V) by 100 k; OS on COM; OUT AC-coupled through 1 uF and 49.9 ohm to the OUT jack.  The chip at
    rot 0 (COM, IN, GND, VDD down its left at 12.8; CLK, SHDN, OS, OUT down its right at 17.2), the buffer above its
    right side, VS up the back along the tile's right edge to SHDN and the buffer."""
    t = Tile("c4", "SC filter", [(0, 0)], supply="+5 V", subtitle="MAX7410", sections=["Switched capacitors"])
    t.jack("TL", "IN", "IN", "in", "±1 V", silk="IN 50R")
    t.jack("BR", "OUT", "OUT", "out", "")
    power_header(t)
    W = 0.25
    u = t.add("U", "MAX7410", "MAX7410", 15.0, 5.6, 0, {"1": "COM", "2": "INC", "3": "GND", "4": "VS", "5": "OUTF", "6": "COM", "7": "VS", "8": "CLK"},
              hide_value=False, label=None)
    b = t.add("U", "LV1T34", "LV1T34", 17.6, 2.7, 0, {"2": "/PMOD3", "3": "GND", "4": "CLK", "5": "VS"}, hide_value=True, label=None)
    rt = t.add("R", "R0402 49.9R", "49.9", 9.2, 5.8, 90, {"1": "GND", "2": "IN"}, label=None)              # pad 2 up, on the line
    ci = t.add("C", "C0402 1uF", "1u", 10.6, 5.275, 0, {"1": "IN", "2": "INC"}, label=None)
    rb = t.add("R", "R0402 100k", "100k", 10.85, 3.6, 0, {"1": "COM", "2": "INC"}, label=None)
    cc = t.add("C", "C0402 100nF", "100n", 13.4, 2.9, 0, {"1": "COM", "2": "GND"}, label=None)
    cv = t.add("C", "C0402 100nF", "100n", 13.4, 7.85, 0, {"1": "VS", "2": "GND"}, label=None)
    co = t.add("C", "C0402 1uF", "1u", 18.5, 8.3, 90, {"1": "OUTC", "2": "OUTF"}, label=None)              # pad 2 up
    rp = t.add("R", "R0402 100k", "100k", 17.0, 8.4, 0, {"1": "GND", "2": "OUTC"}, label=None)
    ro = t.add("R", "R0402 49.9R", "49.9", 17.0, 9.6, 0, {"1": "OUT", "2": "OUTC"}, label=None)
    t.wire("IN", [("J%d01" % t.idx, "1"), (8.0, 4.75), (8.6, 5.275), (ci, "1")])
    t.wire("INC", [(ci, "2"), (u, "2")], width=W)
    t.wire("INC", [(rb, "2"), (11.48, 5.275)], width=W)
    t.wire("COM", [(rb, "1"), (10.52, 2.9), (12.4, 2.9), (12.4, 4.625)], width=W)
    t.wire("COM", [(12.4, 2.9), (cc, "1")], width=W)
    t.wire("GND", [(u, "3"), (11.3, 6.1)], width=W)
    t.via("GND", 11.3, 6.1)
    t.wire("VS", [(u, "4"), (12.3, 6.575), (12.3, 7.85), (cv, "1")], width=W)
    t.wire("CLK", [(b, "4"), (18.55, 4.0), (17.925, 4.625)], width=W)
    t.wire("VS", [(b, "5"), (19.4, 2.05), (19.4, 5.275), (u, "7")], width=W)
    t.wire("VS", [(19.4, 5.275), (19.4, 6.0)], width=W)
    t.wire("OUTF", [(u, "5"), (18.5, 6.575), (co, "2")], width=W)
    t.wire("OUTC", [(co, "1"), (18.5, 9.6), (ro, "2")], width=W)
    t.wire("OUTC", [(rp, "2"), (17.9, 8.4), (18.5, 9.0)], width=W)
    t.wire("OUT", [(ro, "1"), (15.25, 9.6), ("J%d02" % t.idx, "1")])
    t.gnd_stub(rt, "1", (9.2, 7.2), sym=(0, 0))
    t.gnd_stub(cc, "2", (14.7, 2.9), sym=(0, 0))
    t.gnd_stub(cv, "2", (14.7, 7.85), sym=(0, 0))
    t.gnd_stub(rp, "1", (15.9, 8.4), sym=(0, 0))
    t.gnd_stub(b, "3", (15.7, 3.6), sym=(0, 0))
    t.via("/PMOD3", 15.6, 2.3)
    t.wire("/PMOD3", [(15.6, 2.3), (16.0, 2.7), (b, "2")], width=W)
    # VS: up the back from the header to the chip's VDD capacitor, and on along the bottom and up the right edge to SHDN
    t.wire("VS", [HDR_VS, (8.54, 18.5), (10.4, 18.5)])
    t.wire("VS", [(10.4, 18.5), (10.4, 8.6)], layer="B.Cu", silk=False)
    t.wire("VS", [(10.4, 8.6), (12.3, 8.6), (12.3, 7.85)])
    t.wire("VS", [(10.4, 18.5), (10.4, 19.3), (19.4, 19.3), (19.4, 6.0)], layer="B.Cu", silk=False)
    # OS to COM: off the chip's right side, under it on the back, up to a via beside COM's capacitor
    t.wire("COM", [(u, "6"), (18.5, 5.925)], width=W)
    t.wire("COM", [(18.5, 5.925), (14.4, 5.925), (13.2, 4.7), (13.2, 3.7)], layer="B.Cu", silk=False, width=W)
    t.wire("COM", [(13.2, 3.7), (12.4, 3.7)], width=W)
    t.text(6.0, 10.6, "c4", 1.5, 0.3, "center")
    t.titles.append("SC filter")
    t.result = "a 5th-order Butterworth low-pass at fCLK / 100 (up to 15 kHz from a 1.5 MHz clock on IO3); the clock's images near fCLK"
    t.notes = ["MAX7410: a switched-capacitor ladder whose corner is the clock divided by 100, clocked from IO3 through an SN74LV1T34.",
               "IN and OUT sit at COM (2.5 V), so both are AC-coupled.  Sweep the clock and watch the corner follow; alias a tone."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ c5 --
def tile_c5():
    """A switched-capacitor resistor and integrator, two cells along the top: a TMUX4053 (three SPDTs on +-5 V, 3.3 V logic)
    switches 1 nF between IN and ground on one side (phi1, Pmod IO4) and between ground and the integrator's summing node on
    the other (phi2, IO8): the parasitic-insensitive integrator, whose resistor is 1 / (f C).  An OPA810 with 10 nF (C0G)
    and 1 M across it integrates; OUT through 49.9 ohm.  The FPGA makes the two phases, so it can make them overlap on
    purpose.  The third switch is grounded.  The chip turned 180 in the right cell's top-left quarter (SEL3, SEL2, SEL1, S1A,
    S1B, D1, D2, VDD down its left at 24.14; GND, VSS, EN, S3A, D3, S3B, S2A, S2B down its right at 29.86), its grounds
    joined under its body; IN along y 4.75 from the jack; the capacitor standing left of D1 and D2.  The integrator below
    (the OPA810 at rot 270: +IN, V-, OUT along its top, -IN and V+ along its bottom), the summing node coming down from S2B
    to a column on its left, the feedback pair lying under it, OUT over to the right and on to the jack between its top
    legs.  VS up the back from the header; -5 V on the back to the right edge and the gutter."""
    t = Tile("c5", "SC integrator", [(1, 0), (2, 0)], supply="+-5 V", subtitle="TMUX4053", sections=["Switched capacitors"])
    t.jack("TL0", "IN", "IN", "in", "±1 V", silk="IN 50R")
    t.jack("BR1", "OUT", "OUT", "out", "")
    power_header(t)
    t.fine = True
    W = 0.25
    u = t.add("U", "TMUX4053", "TMUX4053", 27.0, 5.0, 180, {"9": "GND", "10": "/PMOD8", "11": "/PMOD4", "12": "GND", "13": "IN", "14": "CT",
                                                            "15": "CB", "16": "VS", "8": "GND", "7": "-5V", "6": "GND", "5": "GND", "4": "GND",
                                                            "3": "GND", "2": "GND", "1": "VG"}, hide_value=False, label=None)
    rt = t.add("R", "R0402 49.9R", "49.9", 9.4, 5.3, 90, {"1": "GND", "2": "IN"}, label=None)              # pad 2 up, on the line
    cs = t.add("C", "C0603 1nF", "1n", 21.6, 6.75, 270, {"1": "CT", "2": "CB"}, label=None)               # pad 1 up, level with D1
    cdd = t.add("C", "C0402 100nF", "100n", 24.1375, 8.7, 270, {"1": "VS", "2": "GND"}, label=None)       # pad 1 up, under VDD
    css = t.add("C", "C0402 100nF", "100n", 31.7, 4.2, 270, {"1": "-5V", "2": "GND"}, label=None)         # pad 1 up
    t.wire("IN", [("J%d01" % t.idx, "1"), (22.6, 4.75), (23.15, 5.325), (u, "13")])
    t.wire("IN", [(9.4, 4.75), (rt, "2")])
    t.gnd_stub(rt, "1", (9.4, 6.8), sym=(0, 0))
    # the grounds: SEL3 and S1A to a bus under the chip's left row, GND, EN and the unused switches to one under its right
    t.wire("GND", [(u, "9"), (25.4, 2.725), (25.4, 4.675), (u, "12")], width=W, silk=False)
    t.gnd_stub(u, "9", [(25.4, 2.725), (25.4, 3.7)], sym=(0, 0), width=W)
    t.wire("GND", [(u, "8"), (28.6, 2.725), (28.6, 6.625), (u, "2")], width=W, silk=False)
    for pin, y in (("6", 4.025), ("5", 4.675), ("4", 5.325), ("3", 5.975)):
        t.wire("GND", [(u, pin), (28.6, y)], width=W, silk=False)
    t.gnd_stub(u, "8", [(28.6, 2.725), (28.6, 4.35)], sym=(0, 0), width=W)
    t.wire("-5V", [(u, "7"), (31.0, 3.375), (css, "1")], width=W)
    t.wire("-5V", [(css, "1"), (32.6, 3.375)], width=W)
    t.gnd_stub(css, "2", (31.7, 5.6), sym=(0, 0))
    t.via("/PMOD4", 22.1, 3.9)
    t.via("/PMOD8", 22.9, 2.75)
    t.wire("/PMOD4", [(u, "11"), (23.0, 4.025), (22.1, 3.9)], width=W)
    t.wire("/PMOD8", [(u, "10"), (23.3, 3.375), (22.9, 2.75)], width=W)
    t.wire("CT", [(u, "14"), (cs, "1")], width=W)
    t.wire("CB", [(u, "15"), (22.5, 6.625), (cs, "2")], width=W)
    t.wire("VS", [(u, "16"), (cdd, "1")], width=W)
    t.wire("VS", [(23.0, 8.22), (cdd, "1")], width=W)
    t.gnd_stub(cdd, "2", (25.2, 9.18), sym=(0, 0))
    # the integrator
    oa = t.add("U", "OPA810", "OPA810", 26.0, 13.3, 270, {"1": "OA", "2": "-5V", "3": "GND", "4": "VG", "5": "VS"}, hide_value=False, label=None)
    ci = t.add("C", "C0603 10nF", "10n", 26.4, 16.9, 0, {"1": "VG", "2": "OA"}, label=None)
    rl = t.add("R", "R0402 1M", "1M", 26.4, 18.1, 0, {"1": "VG", "2": "OA"}, label=None)
    ro = t.add("R", "R0603 49.9R", "49.9", 31.8, 10.6, 0, {"1": "OA", "2": "OUT"}, label=None)
    cvn = t.add("C", "C0402 100nF", "100n", 29.6, 13.0, 270, {"1": "-5V", "2": "GND"}, label=None)        # pad 1 up
    cvp = t.add("C", "C0402 100nF", "100n", 20.6, 15.75, 0, {"1": "GND", "2": "VS"}, label=None)
    t.wire("VG", [(u, "1"), (29.8625, 9.9), (23.6, 9.9), (23.6, 18.1), (rl, "1")], width=W)
    t.wire("VG", [(23.6, 14.4375), (oa, "4")], width=W)
    t.wire("VG", [(23.6, 16.9), (ci, "1")], width=W)
    t.wire("OA", [(oa, "1"), (28.2, 12.1625)], width=W)
    t.wire("OA", [(ro, "1"), (28.2, 10.6), (28.2, 18.1), (rl, "2")], width=W)
    t.wire("OA", [(28.2, 16.9), (ci, "2")], width=W)
    t.wire("OUT", [(ro, "2"), (36.75, 10.6), ("J%d02" % t.idx, "1")])
    t.gnd_stub(oa, "3", (24.9, 10.9), sym=(0, 0))
    t.via("-5V", 26.0, 10.9)
    t.wire("-5V", [(oa, "2"), (26.0, 10.9)], width=W)
    t.via("-5V", 29.6, 11.6)
    t.wire("-5V", [(29.6, 11.6), (cvn, "1")], width=W)
    t.gnd_stub(cvn, "2", (29.6, 14.5), sym=(0, 0))
    t.wire("-5V", [(26.0, 10.9), (26.7, 11.6), (29.6, 11.6)], layer="B.Cu", silk=False)
    t.wire("-5V", [(29.6, 11.6), (30.3, 10.9), (40.9, 10.9), (40.9, 20.5)], layer="B.Cu", silk=False)
    t.wire("-5V", [(32.6, 3.375), (40.9, 3.375), (40.9, 20.5)], layer="B.Cu", silk=False)
    t.via("-5V", 40.9, 20.5)
    # VS: the FET's drain to a via, along the back under the cells' bottom and up to the switch's capacitor; a branch to a
    # via under V+, with its capacitor on the way
    t.wire("VS", [HDR_VS, (8.54, 18.5), (10.6, 18.5)])
    t.wire("VS", [(10.6, 18.5), (22.4, 18.5), (22.4, 8.7), (23.0, 8.22)], layer="B.Cu", silk=False)
    t.wire("VS", [(22.4, 15.75), (26.95, 15.75)], layer="B.Cu", silk=False)
    t.wire("VS", [(oa, "5"), (26.95, 15.75)], width=W)
    t.wire("VS", [(cvp, "2"), (22.4, 15.75)], width=W)
    t.gnd_stub(cvp, "1", (19.2, 15.75), sym=(0, 0))
    t.text(6.0, 10.6, "c5", 1.5, 0.3, "center")
    t.titles.append("SC integrator")
    t.info(["R = 1 / f C", "IO4, IO8"], near=(36.0, 3.0), reach=6.0)
    t.result = "an integrator whose input resistor is 1 / (f x 1 nF): 1 M at 1 kHz, 1 k at 1 MHz; OUT = -(1 / R C) x the integral of IN"
    t.notes = ["phi1 (IO4) connects the 1 nF's top plate to IN, phi2 (IO8) its bottom plate to the summing node: C x Vin per cycle at f,",
               "a resistor of 1 / (f C).  Make the phases non-overlapping, or overlap them and watch IN leak through.  1 M sets the DC gain."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ c6 --
def tile_c6():
    """A second-order delta-sigma modulator with its insides on jacks, two cells.  Both OPA2810 integrators sit on a 1.65 V
    virtual ground (VMID: the board's +3.3 V halved by two 0.1 % 10 k), so each one-bit DAC is just an SN74LVC1G3157
    switching 10 k between +3.3 V and ground: +-165 uA about VMID, ratiometric with VMID, with no negative reference; 10 k
    from +3.3 V into the first node cancels IN's own offset from VMID.  IN through 10 k into 220 pF, the first output
    through 6.8 k into 330 pF; a TLV3501 compares the second output with VMID; a 74LVC1G79 registers it on the FPGA's clock
    (Pmod IO1) and hands the bit to IO7 and to both switches (the first wired the other way round, so both loops are
    negative).  INT1 and INT2 on their jacks through 3.3 k / 1 k (read at high impedance: about a quarter, offset by 0.38
    V).  Full scale +-1.65 V; clock 1 MHz.  The OPA2810 (SOIC-8 at rot 0: OUT A, -IN A, +IN A, V- down its left at 24.5;
    V+, OUT B, -IN B, +IN B down its right at 29.5) in the right cell's top-left quarter: the first integrator's parts on
    a column left of it, the second's right of it; OUT A crosses under the body and out of its bottom to the 6.8 k and
    INT1's divider; +IN A and +IN B on vias under the body joined on the back, V+ on a via under the body.  The
    comparator and the register over the right cell's top-right, the second switch under the second integrator, the
    first switch beside its 10 k; VMID's divider in the right cell's bottom-left quarter.  VS comes along the bottom edge
    and up the back; the bit and IO1 leave on the back for the Pmod plug."""
    t = Tile("c6", "delta-sigma", [(1, 1), (2, 1)], supply="+-5 V", subtitle="second order", sections=["Trading speed for bits"])
    t.jack("TL0", "IN", "IN", "in", "±1 V", silk="IN 10K")
    t.jack("BR0", "INT1", "I1J", "out", "", silk="INT1 /4")
    t.jack("BR1", "INT2", "I2J", "out", "", silk="INT2 /4")
    power_header(t)
    t.pwr_flags.append("VM")
    W = 0.25
    WF = 0.2
    # ---- the integrators
    u = t.add("U", "OPA2810", "OPA2810", 27.0, 5.0, 0, {"1": "I1", "2": "S1", "3": "VM", "4": "-5V", "5": "VM", "6": "S2", "7": "I2", "8": "VS"},
              hide_value=False, label=None)
    c1 = t.add("C", "C0402 220pF", "220p", 22.6, 3.73, 90, {"1": "S1", "2": "I1"}, label=None)              # pad 2 up
    rin = t.add("R", "R0402 10k", "10k", 21.8, 5.6, 0, {"1": "IN", "2": "S1"}, label=None)
    rd1 = t.add("R", "RP0603 10k", "10k", 21.8, 7.3, 0, {"1": "D1", "2": "S1"}, label=None)
    roff = t.add("R", "RP0603 10k", "10k", 21.8, 9.0, 0, {"1": "+3V3", "2": "S1"}, label=None)
    cu1n = t.add("C", "C0402 100nF", "100n", 21.3, 2.35, 0, {"1": "GND", "2": "-5V"}, label=None)
    c2 = t.add("C", "C0402 330pF", "330p", 31.4, 5.0, 90, {"1": "S2", "2": "I2"}, label=None)               # pad 2 up
    r12 = t.add("R", "R0402 6.8k", "6.8k", 31.4, 7.0, 90, {"1": "I1", "2": "S2"}, label=None)               # pad 2 up
    rd2 = t.add("R", "R0402 10k", "10k", 32.9, 6.0, 0, {"1": "S2", "2": "D2"}, label=None)
    cu1p = t.add("C", "C0402 100nF", "100n", 32.2, 3.1, 0, {"1": "VS", "2": "GND"}, label=None)
    ro1 = t.add("R", "R0402 3.3k", "3.3k", 27.0, 10.6, 90, {"1": "I1J", "2": "I1"}, label=None)             # pad 2 up
    rg1 = t.add("R", "R0402 1k", "1k", 19.6, 16.6, 90, {"1": "GND", "2": "I1J"}, label=None)                # pad 2 up
    # IN: from its jack along y 4.0 to the 10 k
    t.wire("IN", [("J%d01" % t.idx, "1"), (8.8, 4.75), (9.4, 4.0), (20.6, 4.0), (rin, "1")])
    # the first integrator: its capacitor between OUT A and -IN A, a column down from -IN A to the three 10 k
    t.wire("I1", [(u, "1"), (c1, "2")], width=WF)
    t.wire("S1", [(u, "2"), (23.0, 4.365), (23.0, 9.0), (roff, "2")], width=WF)
    t.wire("S1", [(23.0, 4.365), (c1, "1")], width=WF)
    t.wire("S1", [(23.0, 5.6), (rin, "2")], width=WF)
    t.wire("S1", [(23.0, 7.3), (rd1, "2")], width=WF)
    # OUT A under the body and out of its bottom: to the 6.8 k and down to INT1's 3.3 k
    t.wire("I1", [(u, "1"), (27.0, 3.6), (27.0, 8.4), (31.4, 8.4), (r12, "1")], width=WF)
    t.wire("I1", [(27.0, 8.4), (ro1, "2")], width=WF)
    t.wire("I1J", [(ro1, "1"), (27.0, 12.2), (19.6, 12.2), (19.6, 15.25), ("J%d02" % t.idx, "1")])
    t.wire("I1J", [(19.6, 15.25), (rg1, "2")])
    t.gnd_stub(rg1, "1", (20.9, 17.2), sym=(0, 0))
    # +IN A and +IN B on vias under the body, joined on the back; V- to a via under the body, on the back to the -5 V strip
    t.via("VM", 26.1, 5.635)
    t.via("VM", 27.9, 6.905)
    t.wire("VM", [(u, "3"), (26.1, 5.635)], width=WF, silk=False)
    t.wire("VM", [(u, "5"), (27.9, 6.905)], width=WF, silk=False)
    t.wire("VM", [(26.1, 5.635), (27.9, 6.905)], layer="B.Cu", silk=False, width=WF)
    t.via("-5V", 26.1, 7.3)
    t.wire("-5V", [(u, "4"), (26.1, 7.3)], width=WF, silk=False)
    t.wire("-5V", [(26.1, 7.3), (22.8, 7.3), (22.8, -0.75)], layer="B.Cu", silk=False)
    t.via("-5V", 22.8, -0.75)
    t.via("-5V", 22.8, 2.4)
    t.wire("-5V", [(22.8, 2.4), (cu1n, "2")], width=W)
    t.gnd_stub(cu1n, "1", (19.9, 2.35), sym=(0, 0))
    # the second integrator: its capacitor between OUT B and -IN B, the 6.8 k and DAC2's 10 k on -IN B
    t.wire("S2", [(u, "6"), (c2, "1")], width=WF)
    t.wire("S2", [(c2, "1"), (r12, "2")], width=WF)
    t.wire("S2", [(31.4, 6.0), (rd2, "1")], width=WF)
    t.wire("I2", [(u, "7"), (c2, "2")], width=WF)
    t.wire("VS", [(u, "8"), (cu1p, "1")], width=W)
    t.gnd_stub(cu1p, "2", (33.6, 3.1), sym=(0, 0))
    # ---- the decision: TLV3501 (SOT-23-6 at rot 0: -IN, V-, +IN down its left; SHDN, OUT, V+ up its right) right of the
    # second integrator, OUT under its body to the register below; V- and SHDN joined under the body
    cmp_ = t.add("U", "TLV3501", "TLV3501", 36.4, 4.2, 0, {"1": "VM", "2": "GND", "3": "I2", "4": "+3V3", "5": "DEC", "6": "GND"}, hide_value=False, label=None)
    ccmp = t.add("C", "C0402 100nF", "100n", 39.75, 5.5, 90, {"1": "GND", "2": "+3V3"}, label=None)       # pad 2 up
    t.wire("I2", [(c2, "2"), (33.9, 4.52), (34.6, 5.15), (cmp_, "3")], width=WF)
    t.via("VM", 34.5, 2.3)
    t.wire("VM", [(34.5, 2.3), (cmp_, "1")], width=WF)
    t.wire("GND", [(cmp_, "2"), (35.925, 4.2), (36.875, 3.25), (cmp_, "6")], width=WF, silk=False)
    t.gnd_stub(cmp_, "6", (38.9, 3.25), sym=(0, 0))
    t.wire("+3V3", [(cmp_, "4"), (ccmp, "2")], width=W)
    t.gnd_stub(ccmp, "1", (38.9, 5.9), sym=(0, 0))
    t.via("+3V3", 40.9, 5.0)
    t.wire("+3V3", [(40.9, 5.0), (ccmp, "2")], width=W)
    rail(t, "+3V3", (40.9, 5.0), "below")
    # the register (SOT-23-5 at rot 0: D, CLK, GND down its left; VCC, Q up its right) below the comparator
    ff = t.add("U", "LVC1G79", "74LVC1G79", 37.1, 8.0, 0, {"1": "DEC", "2": "/PMOD1", "3": "GND", "4": "/PMOD7", "5": "+3V3"}, hide_value=False, label=None)
    cff = t.add("C", "C0402 100nF", "100n", 39.75, 8.6, 90, {"1": "GND", "2": "+3V3"}, label=None)        # pad 2 up
    t.wire("DEC", [(cmp_, "5"), (36.875, 4.2), (36.4, 4.9), (36.4, 6.5), (ff, "1")], width=WF, silk=False)
    t.gnd_stub(ff, "3", (34.9, 9.9), sym=(0, 0))
    t.wire("+3V3", [(ff, "5"), (39.75, 7.05), (cff, "2")], width=W)
    t.wire("+3V3", [(39.75, 7.05), (40.9, 7.05), (40.9, 5.0)], width=W)
    t.gnd_stub(cff, "1", (39.75, 10.0), sym=(0, 0))
    # the second switch (SOT-23-6 at rot 0: B2, GND, B1 down its left; S, VCC, A up its right) under the second
    # integrator: A under its body and up to DAC2's 10 k
    sw2 = t.add("U", "LVC1G3157", "74LVC1G3157", 32.0, 10.0, 0, {"1": "+3V3", "2": "GND", "3": "GND", "4": "D2", "5": "+3V3", "6": "/PMOD7"},
                hide_value=True, label=None)
    t.wire("D2", [(sw2, "4"), (32.15, 10.95), (32.15, 6.9), (33.41, 6.9), (rd2, "2")], width=WF, silk=False)
    t.via("+3V3", 34.4, 10.6)
    t.wire("+3V3", [(sw2, "5"), (34.4, 10.6)], width=WF)
    t.wire("+3V3", [(34.4, 10.6), (34.9, 11.1), (40.9, 11.1), (40.9, 20.5)], layer="B.Cu", silk=False, width=W)
    t.via("+3V3", 29.6, 9.05)
    t.wire("+3V3", [(29.6, 9.05), (sw2, "1")], width=WF)
    rail(t, "+3V3", (29.6, 9.05), "below")
    t.wire("GND", [(sw2, "2"), (sw2, "3")], width=WF)
    t.gnd_stub(sw2, "3", (30.5, 12.0), sym=(0, 0))
    # the first switch (rot 90: B2, GND, B1 along its bottom; S, VCC, A along its top) beside DAC1's 10 k; B1 straight to
    # the offset resistor's +3.3 V end, A to DAC1's 10 k
    sw1 = t.add("U", "LVC1G3157", "74LVC1G3157", 18.3, 7.6, 90, {"1": "GND", "2": "GND", "3": "+3V3", "4": "D1", "5": "+3V3", "6": "/PMOD7"},
                hide_value=True, label=None)
    csw1 = t.add("C", "C0402 100nF", "100n", 19.5, 5.0, 0, {"1": "+3V3", "2": "GND"}, label=None)
    t.wire("D1", [(sw1, "4"), (19.6, 6.6), (rd1, "1")], width=WF)
    t.wire("+3V3", [(sw1, "3"), (roff, "1")], width=WF)
    t.via("+3V3", 18.0, 5.0)
    t.wire("+3V3", [(sw1, "5"), (18.3, 5.6), (18.0, 5.0), (csw1, "1")], width=WF)
    t.gnd_stub(csw1, "2", (20.4, 6.0), sym=(0, 0))
    t.wire("GND", [(sw1, "1"), (sw1, "2")], width=WF)
    t.gnd_stub(sw1, "2", (18.3, 10.0), sym=(0, 0))
    t.via("+3V3", 20.2, 9.9)
    t.wire("+3V3", [(roff, "1"), (20.2, 9.9)], width=WF)
    t.wire("+3V3", [(18.0, 5.0), (19.5, 6.5), (19.5, 9.2), (20.2, 9.9), (20.2, 20.5)], layer="B.Cu", silk=False)
    t.via("+3V3", 20.2, 20.5)
    # VMID in the right cell's bottom-left quarter: 10 k / 10 k (0.1 %) from +3.3 V with 1 uF; +IN B's via comes down the back
    rv1 = t.add("R", "RP0603 10k", "10k", 24.4, 18.2, 0, {"1": "+3V3", "2": "VM"}, label=None)
    rv2 = t.add("R", "RP0603 10k", "10k", 27.6, 18.2, 0, {"1": "VM", "2": "GND"}, label=None)
    cvm = t.add("C", "C0603 1uF", "1u", 28.1, 16.4, 0, {"1": "VM", "2": "GND"}, label=None)
    t.wire("VM", [(rv1, "2"), (rv2, "1")], width=W)
    t.wire("VM", [(26.0, 18.2), (26.6, 17.4), (cvm, "1")], width=W)
    t.via("+3V3", 22.5, 17.4)
    t.wire("+3V3", [(22.5, 17.4), (rv1, "1")], width=W)
    t.wire("+3V3", [(22.5, 17.4), (22.5, 20.5)], layer="B.Cu", silk=False)
    t.via("+3V3", 22.5, 20.5)
    t.gnd_stub(rv2, "2", (30.3, 18.2), sym=(0, 0))
    t.gnd_stub(cvm, "2", (30.3, 16.4), sym=(0, 0))
    t.via("VM", 27.4, 15.4)
    t.wire("VM", [(27.9, 6.905), (27.4, 7.6), (27.4, 15.4)], layer="B.Cu", silk=False, width=WF)
    t.wire("VM", [(27.4, 15.4), (cvm, "1")], width=WF)
    # INT2: 3.3 k / 1 k into its jack between the left legs
    ro2 = t.add("R", "R0402 3.3k", "3.3k", 31.6, 15.25, 0, {"1": "I2", "2": "I2J"}, label=None)
    rg2 = t.add("R", "R0402 1k", "1k", 32.6, 16.8, 90, {"1": "GND", "2": "I2J"}, label=None)               # pad 2 up
    t.wire("I2J", [(ro2, "2"), ("J%d03" % t.idx, "1")])
    t.wire("I2J", [(32.6, 15.25), (rg2, "2")])
    t.gnd_stub(rg2, "1", (32.6, 18.4), sym=(0, 0))
    # VS: the FET's drain along the bottom edge to a via, up the back to a via under the chip's body by V+
    t.wire("VS", [HDR_VS, (8.54, 19.35), (28.6, 19.35)], silk=False)
    t.wire("VS", [(28.6, 19.35), (28.6, 4.1), (27.9, 3.6)], layer="B.Cu", silk=False)
    t.wire("VS", [(27.9, 3.6), (28.5, 3.095)], width=WF, silk=False)
    # VMID: +IN A's via over the top on the back to the comparator's -IN
    t.wire("VM", [(26.1, 5.635), (26.1, 1.4), (34.5, 1.4), (34.5, 2.3)], layer="B.Cu", silk=False, width=WF)
    # the bit and the clock: vias at the tile's top-right corner for the lines to the plug (BACK_WIRES), the router between
    # the register, the switches and them
    t.via("/PMOD7", 41.1, 1.9)
    t.via("/PMOD1", 41.1, 3.1)
    for net, a2, b2 in (("/PMOD7", (ff, "4"), (sw2, "6")), ("/PMOD7", (sw2, "6"), (sw1, "6")), ("/PMOD7", (ff, "4"), (41.1, 1.9)),
                        ("/PMOD1", (ff, "2"), (41.1, 3.1))):
        t.route(net, [a2, b2], width=W)
    # I2: a via beside the comparator, down the back left of the INT2 jack's legs to its 3.3 k
    t.via("I2", 33.4, 4.52)
    t.wire("I2", [(33.4, 4.52), (32.7, 5.22), (32.7, 13.6), (31.09, 14.3)], layer="B.Cu", silk=False, width=WF)
    t.wire("I2", [(31.09, 14.3), (ro2, "1")], width=WF)
    t.text(6.0, 10.6, "c6", 1.5, 0.3, "center")
    t.titles.append("Delta-sigma")
    t.result = "a one-bit stream on IO7 whose density follows IN (+-1.65 V full scale), its noise shaped at 40 dB per decade"
    t.notes = ["Clock IO1 at about 1 MHz and count IO7's ones.  The second integrator pushes the quantization noise up at 40 dB per",
               "decade (AMOD-A's a6 is first order: 20 dB), so a sinc3 decimator gets more bits per clock.  INT1, INT2: high impedance."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ c2 --
def tile_c2():
    """A buck converter, an LDO after it and an electronic load, two cells.  Left: the TLV62568 (1.5 MHz, pulse-skipping at
    light load) from the switched 5 V with 2.2 uH, 10 uF in and out, its feedback 100 k / 20 k (3.6 V) and TRIM (a DAC)
    through 100 k into the feedback node, so the buck's output moves 2.2-5 V and the LDO can be pushed into dropout;
    BUCK~ is its output AC-coupled (1 uF, 49.9 ohm) for the ripple.  Right: the TPS7A2033 LDO (3.3 V) from the buck,
    LDO~ its output AC-coupled likewise; an OPA810 holds 10 ohm at LOAD's voltage through an AO3400A: 100 mA per volt from
    the LDO's output (LOAD terminated in 49.9 ohm), its loop closed slowly through 1 k and 1 nF so the FET's gate cannot
    make it ring.  The buck (SOT-23-5 at rot 0: EN, GND, SW down its left; VIN, FB up its right) in the left cell's
    top-right quarter, EN to VIN under its body, the inductor under SW, the feedback network stacked right of FB; its
    output along y 9.8 to BUCK~'s coupling in the gutter and on the back to the LDO in the right cell's top-right quarter
    (turned 0: IN, GND, EN down its left; OUT up its right), whose output goes right and down to LDO~'s coupling over its
    jack and left and down to the load in the right cell's bottom-left quarter."""
    t = Tile("c2", "regulators", [(1, 2), (2, 2)], supply="+5 V", subtitle="buck, LDO, load", sections=["Regulators"])
    t.jack("TL0", "TRIM", "TRIM", "in", "±2 V", silk="TRIM 100K")
    t.jack("BR0", "BUCK~", "BJ", "out", "", silk="BUCK~")
    t.jack("TL1", "LOAD", "LOAD", "in", "0-1 V", silk="LOAD 50R")
    t.jack("BR1", "LDO~", "LJ", "out", "", silk="LDO~")
    power_header(t)
    t.pwr_flags.append("VB")                                        # the buck's output feeds the LDO: no power-output pin drives it
    W = 0.25
    # ---- the buck
    bk = t.add("U", "TLV62568", "TLV62568", 14.6, 4.4, 0, {"1": "VS", "2": "GND", "3": "SW", "4": "VS", "5": "FB"}, hide_value=False, label=None)
    l1 = t.add("L", "L2016_2U2", "2.2u", 13.4625, 7.65, 90, {"1": "VB", "2": "SW"}, label=None)              # pad 2 up, under SW
    cbi = t.add("C", "C0805 10uF", "10u", 16.6, 7.85, 90, {"1": "GND", "2": "VS"}, label=None)               # pad 2 up, under VIN
    cbo = t.add("C", "C0805 10uF", "10u", 11.1, 8.2, 90, {"1": "VB", "2": "GND"}, label=None)                # pad 1 down
    rtr = t.add("R", "R0402 100k", "100k", 17.8, 2.35, 0, {"1": "FB", "2": "TRIM"}, label=None)
    rfb = t.add("R", "R0402 20k", "20k", 17.8, 3.45, 0, {"1": "FB", "2": "GND"}, label=None)
    rft = t.add("R", "R0402 100k", "100k", 17.8, 4.55, 0, {"1": "FB", "2": "VB"}, label=None)
    cac1 = t.add("C", "C0603 1uF", "1u", 19.8, 11.4, 270, {"1": "VB", "2": "BA"}, label=None)              # pad 1 up
    rac1 = t.add("R", "R0603 49.9R", "49.9", 19.8, 14.4, 270, {"1": "BA", "2": "BJ"}, label=None)          # pad 1 up
    t.wire("VS", [(bk, "1"), (14.6, 3.7), (14.6, 5.0), (bk, "4")], width=W, silk=False)       # EN to VIN under the body
    t.gnd_stub(bk, "2", (11.9, 4.4), sym=(0, 0))
    t.wire("SW", [(bk, "3"), (l1, "2")], width=0.4)
    t.wire("VS", [(bk, "4"), (cbi, "2")], width=0.4)
    t.wire("FB", [(bk, "5"), (16.9, 3.45), (rfb, "1")], width=W)
    t.wire("FB", [(16.9, 3.45), (16.9, 2.35), (rtr, "1")], width=W)
    t.wire("FB", [(16.9, 3.45), (16.9, 4.55), (rft, "1")], width=W)
    t.gnd_stub(rfb, "2", (19.3, 3.45), sym=(0, 0))
    # TRIM: right from its jack to a via, along the back over the top to a via by its 100 k
    t.wire("TRIM", [("J%d01" % t.idx, "1"), (8.9, 4.75)])
    t.wire("TRIM", [(8.9, 4.75), (8.9, 1.6), (19.3, 1.6), (19.3, 2.35)], layer="B.Cu", silk=False, width=W)
    t.wire("TRIM", [(19.3, 2.35), (rtr, "2")], width=W)
    # VB: the inductor's foot to its capacitor and along y 9.8 (up the gutter to the top of the divider) to BUCK~'s
    # capacitor and a via; on the back under the LOAD jack and up to the LDO
    t.wire("VB", [(cbo, "1"), (12.6, 9.15), (l1, "1")], width=0.5)
    t.wire("VB", [(l1, "1"), (13.4625, 9.8), (20.8, 9.8)], width=0.5)
    t.wire("VB", [(19.3, 9.8), (19.3, 4.55), (rft, "2")], width=W)
    t.wire("VB", [(19.8, 9.8), (cac1, "1")], width=0.5)
    t.wire("VB", [(20.8, 9.8), (20.8, 8.9), (31.2, 8.9), (31.2, 3.6), (32.0, 3.2)], layer="B.Cu", silk=False, width=0.5)
    t.gnd_stub(cbo, "2", (11.1, 6.2), sym=(0, 0))
    t.gnd_stub(cbi, "1", (17.9, 8.8), sym=(0, 0))
    t.wire("BA", [(cac1, "2"), (rac1, "1")], width=W)
    t.wire("BJ", [(rac1, "2"), (19.8, 15.25), ("J%d02" % t.idx, "1")])
    # ---- the LDO (SOT-23-5 at rot 0) in the right cell's top-right quarter: EN to IN under the body
    ld = t.add("U", "TPS7A2033", "TPS7A2033", 34.6, 4.4, 0, {"1": "VB", "2": "GND", "3": "VB", "5": "VL"}, hide_value=False, label=None)
    cli = t.add("C", "C0603 1uF", "1u", 31.0, 4.0, 90, {"1": "GND", "2": "VB"}, label=None)                # pad 2 up
    clo = t.add("C", "C0603 1uF", "1u", 37.6, 3.9, 90, {"1": "GND", "2": "VL"}, label=None)                # pad 2 up
    cac2 = t.add("C", "C0603 1uF", "1u", 37.6, 9.15, 0, {"1": "LA", "2": "VL"}, label=None)
    rac2 = t.add("R", "R0402 49.9R", "49.9", 36.75, 10.82, 270, {"1": "LA", "2": "LJ"}, label=None)         # pad 1 up, over the jack
    t.wire("VB", [(ld, "3"), (34.6, 5.35), (34.6, 3.45), (ld, "1")], width=W, silk=False)
    t.wire("VB", [(32.0, 3.2), (ld, "1")], width=0.4)
    t.wire("VB", [(32.0, 3.2), (cli, "2")], width=0.4)
    t.gnd_stub(ld, "2", (32.0, 4.4), sym=(0, 0))
    t.gnd_stub(cli, "1", (32.0, 4.4), sym=(0, 0))
    t.wire("VL", [(ld, "5"), (clo, "2")], width=0.4)
    t.gnd_stub(clo, "1", (37.6, 5.8), sym=(0, 0))
    t.wire("VL", [(clo, "2"), (38.6, 3.125), (38.6, 8.2), (32.6, 8.2), (32.6, 13.6)], width=0.5)
    t.wire("VL", [(38.6, 8.2), (38.6, 9.15), (cac2, "2")], width=W)
    t.wire("LA", [(cac2, "1"), (rac2, "1")], width=W)
    t.wire("LJ", [(rac2, "2"), ("J%d04" % t.idx, "1")])
    # ---- the load in the right cell's bottom-left quarter: the OPA810 (rot 270: +IN, V-, OUT along its top; -IN, V+ along
    # its bottom) with 1 nF under it from OUT to -IN, 1 k from the shunt to -IN on its left, the FET and its shunt right
    ua = t.add("U", "OPA810", "OPA810", 25.4, 13.0, 270, {"1": "OG", "2": "GND", "3": "LOAD", "4": "FBK", "5": "VS"}, hide_value=False, label=None)
    rtl = t.add("R", "R0402 49.9R", "49.9", 27.3, 9.5, 0, {"1": "LOAD", "2": "GND"}, label=None)
    cc = t.add("C", "C0603 1nF", "1n", 25.6, 16.4, 0, {"1": "FBK", "2": "OG"}, label=None)
    rc = t.add("R", "R0402 1k", "1k", 23.2, 15.8, 90, {"1": "SH", "2": "FBK"}, label=None)                  # pad 2 up
    rg = t.add("R", "R0402 100R", "100R", 28.2, 11.0, 0, {"1": "OG", "2": "GATE"}, label=None)
    q = t.add("Q", "NFET", "AO3400A", 29.8, 13.6, 0, {"1": "GATE", "2": "SH", "3": "VL"}, hide_value=True)
    rsh = t.add("R", "R0805 10R", "10R", 29.2, 17.0, 90, {"1": "GND", "2": "SH"}, label=None)               # pad 2 up
    coa = t.add("C", "C0402 100nF", "100n", 22.4, 12.6, 90, {"1": "GND", "2": "VS"}, label=None)            # pad 2 up
    t.wire("LOAD", [("J%d03" % t.idx, "1"), (26.25, 9.5), (24.45, 9.5), (ua, "3")])
    t.wire("LOAD", [(26.25, 9.5), (rtl, "1")])
    t.gnd_stub(rtl, "2", (28.6, 9.9), sym=(0, 0))
    t.gnd_stub(ua, "2", (25.4, 10.4), sym=(0, 0))
    t.wire("FBK", [(ua, "4"), (24.45, 16.4), (cc, "1")], width=W)
    t.wire("FBK", [(rc, "2"), (24.45, 15.29)], width=W)
    t.wire("OG", [(ua, "1"), (27.4, 11.8625), (27.4, 16.4), (cc, "2")], width=W)
    t.wire("OG", [(27.4, 11.8625), (27.4, 11.0), (rg, "1")], width=W)
    t.wire("GATE", [(rg, "2"), (28.71, 12.0), (q, "1")], width=W)
    t.wire("SH", [(q, "2"), (rsh, "2")], width=0.4)
    t.wire("SH", [(rsh, "2"), (27.9, 16.05), (27.9, 17.5), (23.2, 17.5), (rc, "1")], width=W)
    t.wire("VL", [(32.6, 13.6), (q, "3")], width=0.5)
    t.gnd_stub(rsh, "1", (29.2, 19.0), sym=(0, 0))
    t.via("VS", 26.35, 15.3)
    t.wire("VS", [(ua, "5"), (26.35, 15.3)], width=W)
    t.wire("VS", [(22.4, 11.0), (coa, "2")], width=W)
    t.gnd_stub(coa, "1", (22.4, 14.0), sym=(0, 0))
    # VS: the FET's drain to a via, along the back under the BUCK~ jack's legs to a via by the load's capacitor (a branch up
    # the gutter to the buck's input capacitor) and on to a via under the op amp's V+
    t.wire("VS", [HDR_VS, (8.54, 18.5), (10.6, 18.5)])
    t.wire("VS", [(10.6, 18.5), (10.6, 11.0), (22.4, 11.0)], layer="B.Cu", silk=False)
    t.wire("VS", [(17.9, 6.9), (18.6, 6.9), (18.6, 11.0), (22.4, 11.0)], layer="B.Cu", silk=False)
    t.wire("VS", [(17.9, 6.9), (cbi, "2")], width=0.4)
    t.wire("VS", [(22.4, 11.0), (23.4, 12.0), (26.35, 15.3)], layer="B.Cu", silk=False)
    t.text(6.0, 10.6, "c2", 1.5, 0.3, "center")
    t.titles.append("Regulators")
    t.result = "BUCK~ shows the buck's 1.5 MHz ripple (a few mV, pulse-skipping below about 150 mA); LDO~ the same after the LDO, 40 dB smaller; LOAD sets 100 mA per volt"
    t.notes = ["TLV62568: 3.6 V from 100 k / 20 k; TRIM through 100 k into the feedback node moves it (0 V: 4.2 V, +1 V: 3.2 V, open: 3.6 V).",
               "TPS7A2033: 3.3 V, about 92 dB of PSRR at 1 kHz and 40 dB at 1 MHz; below 3.5 V in it drops out (lower TRIM's voltage).",
               "The load: an OPA810 servos 10 ohm to LOAD's voltage through an AO3400A (1 k and 1 nF slow its loop): a square on LOAD",
               "is a load step.  Keep it under 100 mA for long (the shunt is 1/8 W), steps can be larger.  Both outputs are AC-coupled."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ c3 --
def tile_c3():
    """A charge pump the FPGA clocks: the ICL7660A from the switched 5 V, its OSC pin driven from Pmod IO6 through an
    SN74LV1T34 and 1 k (the pump runs at half the clock), 1 uF flying and 1 uF on the output, 1 k of load on the output;
    CAP shows the flying capacitor's top (0-5 V) and OUT the output (about -5 V), each through 47 k / 10 k (read at high
    impedance).  SOIC-8 at rot 0 (BOOST, CAP+, GND, CAP- down its left at 11.925; V+, OSC, LV, VOUT down its right at
    16.875) in the top-right quarter: the flying capacitor standing left of it with CAP's 47 k above, the output
    capacitor, V+'s capacitor and the load down the right edge, OSC under the body to the 1 k from the buffer below; CAP's
    10 k under its jack, OUT's divider over the OUT jack.  VS comes up the back to the buffer and V+; IO6 from the back."""
    t = Tile("c3", "charge pump", [(3, 2)], supply="+5 V", subtitle="ICL7660A", sections=["Regulators"])
    t.jack("TL", "CAP", "CJ", "out", "", silk="CAP /5.7")
    t.jack("BR", "OUT", "OJ", "out", "", silk="OUT /5.7")
    power_header(t)
    W = 0.25
    b = t.add("U", "LV1T34", "LV1T34", 12.0, 9.2, 0, {"2": "/PMOD6", "3": "GND", "4": "CK", "5": "VS"}, hide_value=True, label=None)
    u = t.add("U", "ICL7660A", "ICL7660A", 14.4, 4.95, 0, {"2": "CP", "3": "GND", "4": "CM", "5": "VO", "7": "OSC", "8": "VS"}, hide_value=False, label=None)
    cf = t.add("C", "C0603 1uF", "1u", 9.6, 5.585, 90, {"1": "CM", "2": "CP"}, label=None)                  # pad 2 up
    rc1 = t.add("R", "R0402 47k", "47k", 9.6, 3.0, 90, {"1": "CP", "2": "CJ"}, label=None)                 # pad 2 up
    rc2 = t.add("R", "R0402 10k", "10k", 4.75, 9.6, 270, {"1": "CJ", "2": "GND"}, label=None)              # pad 1 up, under the jack
    cv = t.add("C", "C0402 100nF", "100n", 18.85, 3.4, 90, {"1": "GND", "2": "VS"}, label=None)            # pad 2 up
    co = t.add("C", "C0603 1uF", "1u", 18.85, 6.6, 90, {"1": "VO", "2": "GND"}, label=None)                # pad 2 up
    rl = t.add("R", "R0603 1k", "1k", 18.85, 9.6, 90, {"1": "GND", "2": "VO"}, label=None)                 # pad 2 up
    rosc = t.add("R", "R0402 1k", "1k", 14.4, 9.6, 90, {"1": "CK", "2": "OSC"}, label=None)                # pad 2 up
    ro1 = t.add("R", "R0402 47k", "47k", 17.0, 8.15, 0, {"1": "OJ", "2": "VO"}, label=None)
    ro2 = t.add("R", "R0402 10k", "10k", 16.2, 10.1, 90, {"1": "GND", "2": "OJ"}, label=None)              # pad 2 up
    # the flying capacitor and CAP's divider: 47 k above it, the jack's pin, 10 k under the jack
    t.wire("CP", [(u, "2"), (10.3, 4.315), (cf, "2")], width=W)
    t.wire("CP", [(rc1, "1"), (cf, "2")], width=W)
    t.wire("CM", [(u, "4"), (10.3, 6.855), (cf, "1")], width=W)
    t.wire("CJ", [(rc1, "2"), (8.9, 2.49), (8.6, 4.75), ("J%d01" % t.idx, "1")])
    t.wire("CJ", [("J%d01" % t.idx, "1"), (rc2, "1")])
    t.gnd_stub(rc2, "2", (4.75, 10.9), sym=(0, 0))
    t.gnd_stub(u, "3", (13.5, 5.585), sym=(0, 0))
    # VOUT down the right edge: its capacitor, the load, the divider to the OUT jack
    t.wire("VO", [(u, "5"), (co, "1")], width=W)
    t.wire("VO", [(co, "1"), (rl, "2")], width=W)
    t.wire("VO", [(18.85, 8.15), (ro1, "2")], width=W)
    t.wire("OJ", [(ro1, "1"), (15.25, 8.15), ("J%d02" % t.idx, "1")])
    t.wire("OJ", [(ro1, "1"), (16.2, 8.15), (ro2, "2")], width=W)
    t.gnd_stub(rl, "1", (18.85, 11.0), sym=(0, 0))
    t.gnd_stub(ro2, "1", (17.0, 11.0), sym=(0, 0))
    t.gnd_stub(co, "2", (18.85, 4.75), sym=(0, 0))
    t.gnd_stub(cv, "1", (18.85, 4.75), sym=(0, 0))
    # OSC under the body to the 1 k, the buffer's output beside it; IO6 up from the back
    t.wire("OSC", [(u, "7"), (15.9, 4.315), (14.4, 4.8), (rosc, "2")], width=W, silk=False)
    t.wire("CK", [(b, "4"), (13.6, 9.85), (13.6, 10.11), (rosc, "1")], width=W)
    t.via("/PMOD6", 10.2, 9.2)
    t.wire("/PMOD6", [(10.2, 9.2), (b, "2")], width=W)
    t.gnd_stub(b, "3", (10.3, 10.4), sym=(0, 0))
    # VS: the FET's drain right to a via, up the back left of the OUT jack's legs to a via under the buffer's VCC, on
    # under the chip and up to a via by V+
    t.wire("VS", [HDR_VS, (8.54, 18.5), (11.4, 18.5), (11.4, 19.4)])
    t.wire("VS", [(11.4, 19.4), (11.0, 19.0), (11.0, 7.85), (17.9, 7.85), (17.9, 2.2)], layer="B.Cu", silk=False)
    t.via("VS", 12.84, 7.85)
    t.wire("VS", [(12.84, 7.85), (b, "5")], width=W)
    t.wire("VS", [(17.9, 2.2), (u, "8")], width=W)
    t.wire("VS", [(17.9, 2.2), (cv, "2")], width=W)
    t.text(2.4, 9.6, "c3", 1.2, 0.24, "center")
    t.titles.append("Charge pump")
    t.result = "about -5 V on the output, falling with load as 1 / (f C) + the switches: 2 k at 1 kHz, 80 ohm at 100 kHz (the pump at half IO6's clock)"
    t.notes = ["ICL7660A: switches charge the flying 1 uF across the supply and dump it, upside down, into the output's 1 uF.  IO6",
               "clocks it through an SN74LV1T34 and 1 k; with 1 k of load, sweep the clock and read OUT: Rout = 1 / (f C) + 60 ohm."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ c7 --
def tile_c7():
    """A track-and-hold: the LF398 on +-5 V (its minimum), 1 nF C0G as the hold capacitor, LOGIC from Pmod IO5 (high:
    track; TTL threshold 1.4 V, so 3.3 V drives it), LOGIC REF grounded; IN terminated in 49.9 ohm, OUT through 49.9 ohm.
    The SOIC-14 turned 90 low in the cell (IN, V-, OUT along its bottom at y 10.08; OFFSET, V+, LOGIC, LOGIC REF, CH along
    its top at 5.13), the hold capacitor, V+'s capacitor and the logic's via in the band above it; IN down the left to
    pin 1, its termination below; OUT round the right edge to its 49.9 ohm and in between the jack's right legs; V- to a
    via under the body and on the back to its capacitor in the strip left of the jack and the bottom margin; VS up the
    back on the left."""
    t = Tile("c7", "track and hold", [(3, 3)], supply="+-5 V", subtitle="LF398", sections=["Trading speed for bits"])
    t.jack("TL", "IN", "IN", "in", "±1 V", silk="IN 50R")
    t.jack("BR", "OUT", "OUT", "out", "")
    power_header(t)
    W = 0.25
    u = t.add("U", "LF398", "LF398", 13.8, 7.6, 90, {"1": "IN", "3": "-5V", "7": "OA", "8": "CH", "10": "GND", "11": "/PMOD5", "12": "VS"},
              hide_value=False, label=None)
    rt = t.add("R", "R0402 49.9R", "49.9", 8.6, 12.0, 270, {"1": "IN", "2": "GND"}, label=None)            # pad 1 up
    ch = t.add("C", "C0603 1nF", "1n", 17.6, 2.9, 0, {"1": "GND", "2": "CH"}, label=None)
    ro = t.add("R", "R0402 49.9R", "49.9", 19.55, 12.8, 90, {"1": "OUT", "2": "OA"}, label=None)           # pad 2 up, clear of the leg
    cvp = t.add("C", "C0402 100nF", "100n", 11.6, 2.75, 0, {"1": "VS", "2": "GND"}, label=None)
    cvn = t.add("C", "C0402 100nF", "100n", 10.3, 12.4, 90, {"1": "GND", "2": "-5V"}, label=None)          # pad 2 up
    t.wire("IN", [("J%d01" % t.idx, "1"), (8.8, 4.75), (8.8, 10.075), (u, "1")])
    t.wire("IN", [(8.8, 10.075), (8.8, 11.49), (rt, "1")])
    t.gnd_stub(rt, "2", (8.6, 13.4), sym=(0, 0))
    # the band above the chip: CH to the hold capacitor, LOGIC REF to ground, LOGIC to IO5's via, V+ to its capacitor
    t.wire("CH", [(u, "8"), (17.61, 4.0), (ch, "2")], width=W)
    t.gnd_stub(u, "10", [(15.07, 3.6), (15.6, 3.2)], sym=(0, 0))
    t.gnd_stub(ch, "1", (15.6, 3.2), sym=(0, 0))
    t.via("/PMOD5", 13.8, 3.2)
    t.wire("/PMOD5", [(13.8, 3.2), (u, "11")], width=W)
    t.wire("VS", [(cvp, "1"), (11.12, 3.6), (12.53, 3.9), (u, "12")], width=W)
    t.gnd_stub(cvp, "2", (12.9, 2.3), sym=(0, 0))
    # OUT round the right edge to the 49.9 ohm and into the jack between its right legs
    t.wire("OA", [(u, "7"), (19.55, 10.075), (ro, "2")], width=W)
    t.wire("OUT", [(ro, "1"), (19.55, 15.25), ("J%d02" % t.idx, "1")])
    # -5 V: a via under the body, on the back to a via by its capacitor and down to the bottom margin
    t.via("-5V", 12.53, 8.6)
    t.wire("-5V", [(u, "3"), (12.53, 8.6)], width=W, silk=False)
    t.wire("-5V", [(12.53, 8.6), (11.2, 9.9), (11.2, 11.7)], layer="B.Cu", silk=False, width=W)
    t.wire("-5V", [(11.2, 11.7), (cvn, "2")], width=W)
    rail(t, "-5V", (11.2, 11.7), "margin")
    t.gnd_stub(cvn, "1", (10.5, 13.9), sym=(0, 0))
    # VS: the FET's drain right to a via and up the back on the left to a via by V+'s capacitor
    t.wire("VS", [HDR_VS, (8.54, 18.5), (9.8, 18.5)])
    t.wire("VS", [(9.8, 18.5), (9.8, 3.0)], layer="B.Cu", silk=False)
    t.wire("VS", [(9.8, 3.0), (cvp, "1")], width=W)
    t.text(6.0, 10.6, "c7", 1.5, 0.3, "center")
    t.titles.append("Track/hold")
    t.result = "OUT follows IN while IO5 is high and holds when it falls: 4 us to acquire, about 30 mV/s of droop, a few mV of hold step"
    t.notes = ["LF398 on +-5 V (its minimum supply: inputs within +-1.5 V).  1 nF C0G: acquisition about 4 us, droop about 30 mV/s.",
               "Measure the acquisition time, the droop, the pedestal (the hold step) against IN, the feedthrough of a sine while",
               "holding, and the aperture delay against the FPGA's edge on IO5."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ----------------------------------------------------------------------------------------------------------- c10 --
def tile_c10():
    """Common emitter against cascode: Q1 (one half of a DMMT3904W matched pair) at about 1.4 mA with 100 ohm in its
    emitter and a 1 k collector load, biased by a chain from the switched 5 V (33 k / 20 k / 10 k: 2.4 V on the cascode's
    base, decoupled; 0.8 V on Q1's); IN terminated, AC-coupled and through 2.2 k, so the Miller capacitance shows; Q2 (the
    pair's other half) the cascode; a jumper on the 1 x 2 header shorts the cascode out (common emitter), parked on one
    pin it leaves it in; Q3 (MMBT3904) an emitter follower at about 6 mA into 1 uF and 51 ohm on OUT.  Gain about -8 at
    Q1's collector, -6 from IN (the 2.2 k against the stage's 6 k); the cascode lifts the bandwidth several times.  The pair (SOT-363 turned 180: E1, E2, C2 down its left; C1, B1, B2
    down its right) in the middle of the top-right quarter, Q2's emitter to Q1's collector under the body; Q1's base out
    to a via on the right and on the back to the input network's column left of the pair; the header at the right edge;
    Q3 under the pair, its output down the strip left of the OUT jack and in between the jack's left legs.  C2 reaches
    the header, Q3's base and its collector resistor on the back; VS comes up the back round the jack's legs."""
    t = Tile("c10", "cascode", [(0, 1)], supply="+5 V", subtitle="", sections=["Transistors"])
    t.jack("TL", "IN", "IN", "in", "±50 mV", silk="IN 50R")
    t.jack("BR", "OUT", "OUT", "out", "")
    power_header(t)
    W = 0.25
    WF = 0.2
    q12 = t.add("Q", "DMMT3904W", "DMMT3904W", 13.2, 5.0, 180, {"1": "CB", "2": "B1", "3": "C1", "4": "E1", "5": "C1", "6": "CN"}, hide_value=True)
    q3 = t.add("Q", "MMBT3904", "MMBT3904", 12.0, 9.8, 0, {"1": "CN", "2": "E3", "3": "VS"}, hide_value=True)
    jp = t.add("J", "HDR2", "CE", 18.0, 3.8, 0, {"1": "C1", "2": "CN"}, hide_value=True)
    rt = t.add("R", "R0402 51R", "51", 4.75, 9.6, 270, {"1": "IN", "2": "GND"}, label=None)                # pad 1 up, under the jack
    cin = t.add("C", "C0402 1uF", "1u", 9.4, 4.75, 0, {"1": "IN", "2": "BI"}, label=None)
    rs = t.add("R", "R0402 2.2k", "2.2k", 10.0, 5.75, 0, {"1": "BI", "2": "B1"}, label=None)
    rch3 = t.add("R", "R0402 10k", "10k", 10.0, 6.85, 0, {"1": "GND", "2": "B1"}, label=None)
    re = t.add("R", "R0402 100R", "100R", 10.3, 3.6, 0, {"1": "GND", "2": "E1"}, label=None)
    rch2 = t.add("R", "R0402 20k", "20k", 13.6, 7.1, 0, {"1": "B1", "2": "CB"}, label=None)
    rch1 = t.add("R", "R0402 33k", "33k", 15.1, 8.5, 270, {"1": "CB", "2": "VS"}, label=None)              # pad 1 up
    ccb = t.add("C", "C0402 100nF", "100n", 15.65, 6.45, 90, {"1": "GND", "2": "CB"}, label=None)          # pad 2 up
    rc = t.add("R", "R0402 1k", "1k", 14.45, 10.4, 90, {"1": "CN", "2": "VS"}, label=None)                 # pad 2 up
    re3 = t.add("R", "R0402 470R", "470R", 9.35, 12.6, 90, {"1": "GND", "2": "E3"}, label=None)            # pad 2 up
    co = t.add("C", "C0402 1uF", "1u", 10.6, 12.6, 270, {"1": "E3", "2": "OC"}, label=None)                # pad 1 up
    ro = t.add("R", "R0402 51R", "51", 10.6, 14.6, 270, {"1": "OC", "2": "OUT"}, label=None)               # pad 1 up
    # IN: right to the coupling capacitor, down to its termination
    t.wire("IN", [("J%d01" % t.idx, "1"), (cin, "1")])
    t.wire("IN", [("J%d01" % t.idx, "1"), (rt, "1")])
    t.gnd_stub(rt, "2", (4.75, 10.9), sym=(0, 0))
    t.wire("BI", [(cin, "2"), (rs, "1")], width=WF)
    # B1: from the base (right middle) to a via, on the back under the pair to a via at the column left of it, which comes
    # down to the 20 k under the pair past the 2.2 k and the 10 k
    t.wire("B1", [(q12, "2"), (15.1, 5.0)], width=WF)
    t.wire("B1", [(15.1, 5.0), (11.3, 5.0)], layer="B.Cu", silk=False, width=W)
    t.wire("B1", [(11.3, 5.0), (11.3, 7.1), (rch2, "1")], width=WF)
    t.wire("B1", [(11.3, 5.75), (rs, "2")], width=WF)
    t.wire("B1", [(11.3, 6.85), (rch3, "2")], width=WF)
    t.wire("E1", [(q12, "4"), (re, "2")], width=WF)
    # the cascode: E2 (left middle) to C1 (right top) under the body, C1 on to the header; its base (right bottom) down a
    # column on the right with its network
    t.wire("C1", [(q12, "3"), (13.2, 4.35), (13.2, 5.0), (q12, "5")], width=WF, silk=False)
    t.wire("C1", [(q12, "3"), (16.4, 4.35), (17.0, 3.8), (jp, "1")], width=W)
    t.wire("CB", [(q12, "1"), (14.9, 5.65), (14.9, 7.6), (rch1, "1")], width=WF)
    t.wire("CB", [(14.9, 5.97), (ccb, "2")], width=WF)
    t.wire("CB", [(14.9, 7.1), (rch2, "2")], width=WF)
    # C2 (CN): a via under the pair, on the back to the header's other pin and to a via under the collector resistor
    t.wire("CN", [(q12, "6"), (12.3, 6.5)], width=WF)
    t.wire("CN", [(12.3, 6.5), (16.4, 6.5), (jp, "2")], layer="B.Cu", silk=False, width=W)
    t.wire("CN", [(12.3, 6.5), (12.9, 7.1), (13.6, 9.3), (14.45, 11.8)], layer="B.Cu", silk=False, width=W)
    t.wire("CN", [(14.45, 11.8), (rc, "1")], width=WF)
    t.wire("CN", [(12.3, 6.5), (11.06, 7.9)], layer="B.Cu", silk=False, width=W)
    t.wire("CN", [(11.06, 7.9), (q3, "1")], width=WF)
    # the follower: VS along y 9.85 to its collector, the 33 k and the 1 k; E3 down the strip to the jack
    t.wire("VS", [(19.6, 9.85), (15.6, 9.85), (rch1, "2")], width=W)
    t.wire("VS", [(15.6, 9.85), (rc, "2")], width=W)
    t.wire("VS", [(rc, "2"), (13.6, 9.85), (q3, "3")], width=W)
    t.wire("E3", [(q3, "2"), (10.6, 11.4), (co, "1")], width=W)
    t.wire("E3", [(10.6, 11.4), (re3, "2")], width=W)
    t.wire("OC", [(co, "2"), (ro, "1")], width=W)
    t.wire("OUT", [(ro, "2"), (11.2, 15.25), ("J%d02" % t.idx, "1")])
    for ref_, pad, pt in ((re, "1", (9.4, 2.6)), (rch3, "1", (9.49, 7.8)), (ccb, "1", (16.3, 7.4)), (re3, "1", (9.35, 14.0))):
        t.gnd_stub(ref_, pad, pt, sym=(0, 0))
    # VS: the FET's drain right to a via, along the back under the jack's legs and up the right edge
    t.wire("VS", [HDR_VS, (8.54, 18.5), (11.4, 18.5), (11.4, 19.4)])
    t.wire("VS", [(11.4, 19.4), (19.6, 19.4), (19.6, 9.85)], layer="B.Cu", silk=False)
    t.text(2.6, 9.6, "c10", 1.2, 0.24, "center")
    t.titles.append("Cascode")
    t.result = "gain about -6 into a high impedance (-8 at Q1's collector), half that into 50 ohm; common emitter (jumper on) about 2 MHz wide, the cascode (jumper parked) several times wider"
    t.notes = ["Q1's collector-base capacitance, multiplied by the gain (Miller), meets the 2.2 k at its base; the cascode holds Q1's",
               "collector still, so only one Ccb counts.  The jumper on the header shorts the cascode out: compare the two sweeps."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ----------------------------------------------------------------------------------------------------------- c11 --
def tile_c11():
    """A 555 as a VCO: the TLC555 (CMOS) astable from the switched 5 V, 1 k and 10 k with 10 nF C0G (about 6.9 kHz); CV
    (a DAC, terminated) into the control pin through 2.2 k moves the thresholds and the frequency; OUT through 3.9 k /
    1 k (about 1 V, read at high impedance).  SOIC-8 at rot 0 (GND, TRIG, OUT, RESET down its left at 11.725; VDD,
    DISCH, THRES, CONT down its right at 16.675) in the top-right quarter; the timing chain (1 k, 10 k, 10 nF) standing
    down the right edge, TRIG to THRES under the body; RESET to a via under the body and on the back to VS, which comes
    up the right edge round the jack's legs; OUT down the left to its divider and along the middle to the jack; CV on the
    back from beside its jack to the 2.2 k standing under CONT."""
    t = Tile("c11", "555", [(3, 0)], supply="+5 V", subtitle="TLC555", sections=["Trading speed for bits"])
    t.jack("TL", "CV", "CV", "in", "±1 V", silk="CV 50R")
    t.jack("BR", "OUT", "OJ", "out", "", silk="OUT /4.9")
    power_header(t)
    W = 0.25
    u = t.add("U", "TLC555", "TLC555", 14.2, 5.2, 0, {"1": "GND", "2": "TT", "3": "O5", "4": "VS", "5": "CT", "6": "TT", "7": "DS", "8": "VS"},
              hide_value=False, label=None)
    rt = t.add("R", "R0402 51R", "51", 8.9, 5.5, 90, {"1": "GND", "2": "CV"}, label=None)                  # pad 2 up, on the line
    rcv = t.add("R", "R0402 2.2k", "2.2k", 16.7, 8.9, 90, {"1": "CV", "2": "CT"}, label=None)              # pad 2 up, under CONT
    ra = t.add("R", "R0402 1k", "1k", 18.75, 3.93, 90, {"1": "DS", "2": "VS"}, label=None)                 # pad 2 up
    rb = t.add("R", "R0402 10k", "10k", 18.75, 5.8, 90, {"1": "TT", "2": "DS"}, label=None)                # pad 2 up
    ct = t.add("C", "C0603 10nF", "10n", 18.75, 8.3, 270, {"1": "TT", "2": "GND"}, label=None)             # pad 1 up
    cv = t.add("C", "C0402 100nF", "100n", 18.85, 2.5, 0, {"1": "GND", "2": "VS"}, label=None)
    ro1 = t.add("R", "R0402 3.9k", "3.9k", 11.6, 9.2, 0, {"1": "O5", "2": "OJ"}, label=None)
    ro2 = t.add("R", "R0402 1k", "1k", 14.0, 10.1, 90, {"1": "GND", "2": "OJ"}, label=None)                # pad 2 up
    # CV: right from the jack to a via (the termination hanging from the line), on the back to the 2.2 k under CONT
    t.wire("CV", [("J%d01" % t.idx, "1"), (9.9, 4.75)])
    t.wire("CV", [(8.9, 4.75), (rt, "2")])
    t.gnd_stub(rt, "1", (8.9, 7.0), sym=(0, 0))
    t.wire("CV", [(9.9, 4.75), (9.6, 5.05), (9.6, 10.4), (16.7, 10.4)], layer="B.Cu", silk=False, width=W)
    t.wire("CV", [(16.7, 10.4), (rcv, "1")], width=W)
    t.wire("CT", [(rcv, "2"), (u, "5")], width=W)
    # the timing chain down the right edge; TRIG to THRES under the body
    t.wire("VS", [(u, "8"), (ra, "2")], width=W)
    t.wire("DS", [(u, "7"), (ra, "1")], width=W)
    t.wire("DS", [(ra, "1"), (rb, "2")], width=W)
    t.wire("TT", [(u, "6"), (rb, "1")], width=W)
    t.wire("TT", [(rb, "1"), (ct, "1")], width=W)
    t.wire("TT", [(u, "2"), (12.7, 4.565), (15.7, 5.835), (u, "6")], width=W, silk=False)
    t.gnd_stub(ct, "2", (18.75, 10.2), sym=(0, 0))
    # VS: the FET's drain to a via, along the back under the jack's legs and up the right edge to a via by VDD's capacitor;
    # RESET to a via under the body and on the back to that column
    t.wire("VS", [HDR_VS, (8.54, 18.5), (11.4, 18.5), (11.4, 19.4)])
    t.wire("VS", [(11.4, 19.4), (19.6, 19.4), (19.6, 3.5)], layer="B.Cu", silk=False)
    t.wire("VS", [(19.6, 3.5), (cv, "2")], width=W)
    t.wire("VS", [(19.6, 3.5), (ra, "2")], width=W)
    t.wire("VS", [(u, "4"), (13.3, 7.105)], width=W, silk=False)
    t.wire("VS", [(13.3, 7.105), (16.9, 3.5), (19.6, 3.5)], layer="B.Cu", silk=False, width=W)
    t.gnd_stub(cv, "1", (17.6, 2.3), sym=(0, 0))
    t.gnd_stub(u, "1", (10.2, 2.7), sym=(0, 0))
    # OUT down the left to the divider and along the middle to the jack
    t.wire("O5", [(u, "3"), (10.3, 5.835), (10.3, 9.2), (ro1, "1")], width=W)
    t.wire("OJ", [(ro1, "2"), (14.0, 9.2), (ro2, "2")], width=W)
    t.wire("OJ", [(14.0, 9.2), (15.25, 9.2), ("J%d02" % t.idx, "1")])
    t.gnd_stub(ro2, "1", (14.0, 11.6), sym=(0, 0))
    t.text(6.0, 10.6, "c11", 1.2, 0.24, "center")
    t.titles.append("555 VCO")
    t.result = "a square near 6.9 kHz on OUT (5 V divided to about 1 V); CV moves it: up as CV falls, down as it rises"
    t.notes = ["TLC555 astable: f = 1.44 / ((1 k + 2 x 10 k) x 10 nF), the capacitor between 1/3 and 2/3 of the supply.  CV pulls the",
               "upper threshold through 2.2 k: a voltage-to-frequency converter.  Count OUT's cycles in the FPGA and you have an ADC."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ----------------------------------------------------------------------------------------------------------- c12 --
def tile_c12():
    """A precision full-wave rectifier: an OPA2197's first half inverts IN through two Schottky diodes (BAT54S), so its
    second node X is -IN for positive inputs and 0 for negative ones; the second half sums -(IN + 2 X) = |IN|.  10 k /
    10 k / 20 k / 10 k / 20 k; IN terminated, OUT through 49.9 ohm.  The chip (VSSOP-8 on KiCad's MSOP-8 pattern at rot 0: OUT A, -IN A, +IN A, V-
    down its left at 12.29; V+, OUT B, -IN B, +IN B down its right at 16.51) in the top-right quarter; OUT A goes under
    its body to the diodes' common pin below it, -IN A out to a column on the left that comes down to the X-to-N 10 k
    standing beside the diodes and on to the first stage's 10 k from IN.  The second half's Rf and V+'s capacitor stand
    right of the chip, its inputs lie under it on a column from -IN B, OUT B goes down the right edge to the 49.9 ohm over
    the jack.  X and IN reach the second stage on the back (IN comes down from its jack to the first stage's resistor);
    VS comes up the back round the jack's legs; -5 V goes down the back on the left to the bottom margin."""
    t = Tile("c12", "rectifier", [(2, 3)], supply="+-5 V", subtitle="precision", sections=["Transistors"])
    t.jack("TL", "IN", "IN", "in", "±1 V", silk="IN 50R")
    t.jack("BR", "OUT", "OUT", "out", "", silk="|IN|")
    power_header(t)
    W = 0.25
    u = t.add("U", "OPA2197", "OPA2197", 14.4, 4.6, 0, {"1": "OA", "2": "N", "3": "GND", "4": "-5V", "5": "GND", "6": "M", "7": "OB", "8": "VS"},
              hide_value=False, label=None)
    d = t.add("D", "BAT54S", "BAT54S", 12.4, 9.4, 0, {"1": "X", "2": "N", "3": "OA"}, hide_value=True, label=None)
    rt = t.add("R", "R0402 51R", "51", 6.6, 10.9, 270, {"1": "GND", "2": "IN"}, label=None)                 # pad 1 up
    r1 = t.add("R", "R0402 10k", "10k", 8.8, 11.2, 270, {"1": "N", "2": "IN"}, label=None)                 # pad 1 up
    r2 = t.add("R", "R0402 10k", "10k", 9.8, 9.4, 90, {"1": "N", "2": "X"}, label=None)                    # pad 2 up
    r3 = t.add("R", "R0402 20k", "20k", 17.2, 8.7, 0, {"1": "IN", "2": "M"}, label=None)
    r4 = t.add("R", "R0402 10k", "10k", 17.2, 7.6, 0, {"1": "X", "2": "M"}, label=None)
    rf = t.add("R", "R0402 20k", "20k", 18.5, 4.95, 90, {"1": "M", "2": "OB"}, label=None)                 # pad 2 up
    ro = t.add("R", "R0402 49.9R", "49.9", 17.6, 10.4, 0, {"1": "OUT", "2": "OB"}, label=None)
    cvp = t.add("C", "C0402 100nF", "100n", 18.5, 2.9, 90, {"1": "VS", "2": "GND"}, label=None)            # pad 1 down
    cvn = t.add("C", "C0402 100nF", "100n", 12.2, 6.85, 0, {"1": "-5V", "2": "GND"}, label=None)
    # IN: down from the jack to the first stage's 10 k (the termination hanging from it), on the back to the second's
    t.wire("IN", [("J%d01" % t.idx, "1"), (4.75, 11.71), (r1, "2")])
    t.wire("IN", [(6.6, 11.71), (rt, "2")])
    t.gnd_stub(rt, "1", (6.6, 9.4), sym=(0, 0))
    t.wire("IN", [(r1, "2"), (9.6, 12.3)], width=W)
    t.wire("IN", [(9.6, 12.3), (10.7, 11.2), (15.1, 11.2), (15.7, 10.6), (15.7, 8.75)], layer="B.Cu", silk=False, width=W)
    t.wire("IN", [(15.7, 8.75), (r3, "1")], width=W)
    # the first stage: OUT A under the body and down to the diodes; -IN A out left, down to the X-to-N 10 k and on to IN's;
    # X on the back to the second stage
    t.wire("OA", [(u, "1"), (13.8, 3.625), (13.8, 9.4), (d, "3")], width=W)
    t.wire("N", [(u, "2"), (9.0, 4.275), (9.0, 9.91), (r2, "1")], width=W)
    t.wire("N", [(9.0, 9.91), (9.0, 10.4), (r1, "1")], width=W)
    t.wire("N", [(r2, "1"), (d, "2")], width=W)
    t.wire("X", [(r2, "2"), (d, "1")], width=W)
    t.wire("X", [(9.8, 7.9), (r2, "2")], width=W)
    t.wire("X", [(9.8, 7.9), (10.3, 8.4), (15.0, 8.4), (15.7, 7.6)], layer="B.Cu", silk=False, width=W)
    t.wire("X", [(15.7, 7.6), (r4, "1")], width=W)
    # the second stage: Rf beside the chip, its inputs on a column from -IN B, OUT B down the right edge to the 49.9 ohm
    t.wire("OB", [(u, "7"), (rf, "2")], width=W)
    t.wire("M", [(u, "6"), (17.9, 4.925), (rf, "1")], width=W)
    t.wire("M", [(rf, "1"), (18.5, 8.7), (r3, "2")], width=W)
    t.wire("M", [(18.5, 7.6), (r4, "2")], width=W)
    t.wire("OB", [(rf, "2"), (19.45, 4.44), (19.45, 10.4), (ro, "2")], width=W)
    t.wire("OUT", [(ro, "1"), (15.25, 10.4), ("J%d02" % t.idx, "1")])
    # grounds: +IN A out left to a via, +IN B to a via under the body
    t.gnd_stub(u, "3", [(10.9, 4.925), (10.6, 5.25)], sym=(0, 0))
    t.gnd_stub(u, "5", (15.0, 5.575), sym=(0, 0))
    # -5 V: V- down to its capacitor, a via, the back left and down to the bottom margin
    t.wire("-5V", [(u, "4"), (11.72, 5.575), (cvn, "1")], width=W)
    t.wire("-5V", [(cvn, "1"), (10.8, 6.85)], width=W)
    t.wire("-5V", [(10.8, 6.85), (8.9, 6.85), (8.9, 21.0)], layer="B.Cu", silk=False)
    t.via("-5V", 8.9, 21.0)
    t.gnd_stub(cvn, "2", (12.9, 7.7), sym=(0, 0))
    # VS: the FET's drain right to a via, along the back under the jack's legs and up the right edge to V+'s capacitor
    t.wire("VS", [HDR_VS, (8.54, 18.5), (11.4, 18.5), (11.4, 19.4)])
    t.wire("VS", [(11.4, 19.4), (19.6, 19.4), (19.6, 3.6), (19.55, 3.6)], layer="B.Cu", silk=False)
    t.wire("VS", [(19.55, 3.6), (cvp, "1")], width=W)
    t.wire("VS", [(u, "8"), (18.0, 3.625), (cvp, "1")], width=W)
    t.gnd_stub(cvp, "2", (19.4, 2.4), sym=(0, 0))
    t.text(2.6, 10.3, "c12", 1.2, 0.24, "center")
    t.titles.append("Rectifier")
    t.result = "OUT = |IN| from DC to about 100 kHz; above that the first stage's slew across the diodes leaves a glitch at each zero crossing"
    t.notes = ["Stage 1: inverting with BAT54S in its feedback, so its node X follows -IN for positive IN and stays at 0 for negative.",
               "Stage 2: OUT = -(IN + 2 X) = |IN|.  No dead zone from the diodes (the op amp's gain hides their drop) until the op amp",
               "must slew through two diode drops at each zero crossing: watch the glitch grow with frequency."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ c8 --
def tile_c8():
    """A comparator for a successive-approximation or tracking ADC whose DAC is the host's: a TLV3201 on +3.3 V (40 ns,
    1.2 mV of hysteresis: the TLV3501's 6 mV would be 12 LSB at 12 bits) compares IN with DAC, each averaged with the
    3.3 V rail through a matched pair of 0.1 % 10 k (so both sit at 1.15-2.15 V inside the comparator's range and the
    comparison is unchanged), its decision to Pmod IO2 and a loop.  The gateware runs the search: set the DAC, read the
    bit, halve the step."""
    t = Tile("c8", "comparator", [(0, 2)], supply="+3.3 V", subtitle="TLV3201", sections=["Trading speed for bits"])
    t.jack("TL", "IN", "IN", "in", "±1 V", silk="IN 20K")
    t.jack("BR", "DAC", "DAC", "in", "±1 V", silk="DAC 20K")
    power_header(t, rail="+3V3")
    # the comparator in the top-right quarter (SC-70-5 at rot 0: OUT, GND, IN+ down its left at x 14.25; IN- and VCC up
    # its right at 16.15); IN through 10 k straight along the IN line to IN+, the DAC line up from the BR jack and round
    # the right edge to its 10 k and on to IN-; each node's second 10 k to VS
    u = t.add("U", "TLV3201", "TLV3201", 15.2, 3.4, 0, {"1": "/PMOD2", "2": "GND", "3": "A", "4": "B", "5": "VS"}, hide_value=False, label=None)
    ra1 = t.add("R", "RP0603 10k", "10k", 10.4, 4.75, 0, {"1": "IN", "2": "A"}, label=None)
    ra2 = t.add("R", "RP0603 10k", "10k", 12.2, 7.0, 90, {"1": "VS", "2": "A"}, label=None)        # pad 1 down
    rb1 = t.add("R", "RP0603 10k", "10k", 18.5, 7.4, 90, {"1": "DAC", "2": "B"}, label=None)       # pad 1 down
    rb2 = t.add("R", "RP0603 10k", "10k", 16.4, 7.4, 90, {"1": "VS", "2": "B"}, label=None)        # pad 1 down
    cp = t.add("C", "C0603 100nF", "100n", 17.6, 3.4, 90, {"1": "GND", "2": "VS"}, label=None)    # pad 2 up, by VCC
    t.via("/PMOD2", 9.6, 10.6)                                    # the bit's way down the back to the plug
    t.wire("IN", [("J%d01" % t.idx, "1"), (ra1, "1")])
    t.wire("A", [(ra1, "2"), (13.3, 4.75), (13.3, 4.05), (u, "3")])
    t.wire("A", [(ra2, "2"), (12.2, 4.75)])
    t.wire("DAC", [("J%d02" % t.idx, "1"), (15.25, 11.0), (18.5, 11.0), (rb1, "1")])
    t.wire("B", [(rb1, "2"), (18.5, 5.4), (16.4, 5.4)])
    t.wire("B", [(rb2, "2"), (16.4, 5.4), (16.4, 4.05), (u, "4")])
    # VS: the FET's drain to a via, up the back left of the BR jack's legs to a via in the middle band
    t.wire("VS", [HDR_VS, (8.54, 18.5), (10.6, 18.5)])
    t.wire("VS", [(10.6, 18.5), (10.6, 9.0)], layer="B.Cu", silk=False)
    for net, a, b in (("/PMOD2", (u, "1"), (9.6, 10.6)), ("VS", (10.6, 9.0), (ra2, "1")), ("VS", (ra2, "1"), (rb2, "1")),
                      ("VS", (rb2, "1"), (u, "5"))):
        t.route(net, [a, b])
    t.gnd_stub(u, "2", (12.9, 3.4), sym=(0, 0))
    t.wire("VS", [(u, "5"), (cp, "2")], width=0.25)
    t.gnd_stub(cp, "1", (18.7, 4.2), sym=(0, 0))
    t.text(6.0, 10.6, "c8", 1.5, 0.3, "center")
    t.titles.append("Comparator")
    t.result = "BIT on Pmod IO2 is high while IN is above DAC; a SAR search in gateware gives 12 bits in 12 steps of the DAC"
    t.notes = ["TLV3201 (40 ns, 1.2 mV hysteresis) on the 3.3 V rail.  Each input is averaged with the rail through a matched pair",
               "of 0.1 % 10 k, so +-1 V lands at 1.15-2.15 V on both pins and the comparison is unchanged.  20 k input impedance:",
               "drive it from a 50 ohm source, read the bit on IO2.  A successive-approximation ADC: the gateware sets the host's",
               "DAC, reads the bit, halves the step; a tracking ADC: up when high, down when low; a slope ADC with a ramp on DAC."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ c9 --
def tile_c9():
    """A differential pair on a current mirror, two cells along the bottom: a matched NPN pair (DMMT3904W) with IN+ (DAC 1)
    and IN- (DAC 2) on the bases, each terminated in 49.9 ohm, their emitters on a 1 mA tail (an MMBT3904 with its base
    at -3.4 V from 6.8 k / 3.3 k and 1 k to -5 V); a matched PNP pair (BCM857BS) mirrors the left collector's current onto
    the right one, so the output node carries Ic1 - Ic2, which an OPA810 transimpedance stage (1 k) turns into OUT: tanh of
    the input difference over 2 VT, +-1 V at the tail's full 1 mA.  The mirror (SOT-363 turned 180: E2, B2, C1 down its
    left; C2, B1, E1 down its right) over the pair (turned 180: E1, E2, C2 down its left; C1, B1, B2 down its right) in the
    left cell's top-right quarter; IN- comes down the right to B2, IN+ down the left to a via, under the pair on the back
    to a via right of it and in to B1 (a SOT-363 leaves no room for a via under its body); the mirror's emitters joined
    under its body; the pair's joined on the left and down the middle under the body to the tail; the mirror's diode node in the channel between the two; the tail standing under
    the pair with its divider and emitter resistor below.  The output node reaches the TIA (rot 270 in the right cell's
    bottom-left quarter, its feedback lying under it) on the back.  The Pmod plug in the margin below the left cell."""
    t = Tile("c9", "differential pair", [(0, 3), (1, 3)], supply="+-5 V", subtitle="", sections=["Transistors"])
    t.jack("TL0", "IN+", "INP", "in", "±0.2 V", silk="IN+ 50R")
    t.jack("TL1", "IN-", "INN", "in", "±0.2 V", silk="IN- 50R")
    t.jack("BR1", "OUT", "OUT", "out", "")
    power_header(t)
    W = 0.25
    WF = 0.2
    qp = t.add("Q", "BCM857BS", "BCM857BS", 15.0, 4.3, 180, {"1": "VS", "2": "MD", "3": "MO", "4": "VS", "5": "MD", "6": "MD"}, hide_value=True, label=None)
    qn = t.add("Q", "DMMT3904W", "DMMT3904W", 15.0, 7.4, 180, {"1": "INN", "2": "INP", "3": "MD", "4": "EM", "5": "EM", "6": "MO"}, hide_value=True, label=None)
    qt = t.add("Q", "MMBT3904", "MMBT3904", 15.84, 10.5, 90, {"1": "TB", "2": "TE", "3": "EM"}, hide_value=True, label=None)
    rt1 = t.add("R", "R0402 49.9R", "49.9", 9.6, 5.5, 90, {"1": "GND", "2": "INP"}, label=None)            # pad 2 up, on the line
    rt2 = t.add("R", "R0402 49.9R", "49.9", 19.6, 5.5, 90, {"1": "GND", "2": "INN"}, label=None)
    rb1 = t.add("R", "R0402 6.8k", "6.8k", 13.2, 11.44, 0, {"1": "GND", "2": "TB"}, label=None)
    rb2 = t.add("R", "R0402 3.3k", "3.3k", 13.2, 12.6, 0, {"1": "-5V", "2": "TB"}, label=None)
    re = t.add("R", "R0402 1k", "1k", 16.79, 13.4, 90, {"1": "-5V", "2": "TE"}, label=None)               # pad 2 up
    cn1 = t.add("C", "C0402 100nF", "100n", 14.8, 15.6, 90, {"1": "GND", "2": "-5V"}, label=None)        # pad 2 up
    # the inputs, each terminated on the way: IN- down the right to B2 (bottom right); IN+ down the left to a via, on the
    # back under the pair to a via right of it and in to B1 (right middle): both bases are on the pair's right
    t.wire("INP", [("J%d01" % t.idx, "1"), (12.0, 4.75), (12.0, 7.4)])
    t.wire("INP", [(12.0, 7.4), (17.1, 7.4)], layer="B.Cu", silk=False, width=W)
    t.wire("INP", [(17.1, 7.4), (qn, "2")], width=WF)
    t.wire("INP", [(9.6, 4.75), (rt1, "2")])
    t.wire("INN", [("J%d02" % t.idx, "1"), (18.4, 4.75), (18.4, 8.05)])
    t.wire("INN", [(18.4, 8.05), (qn, "1")], width=WF)
    t.wire("INN", [(19.6, 4.75), (rt2, "2")])
    t.gnd_stub(rt1, "1", (9.6, 7.0), sym=(0, 0))
    t.gnd_stub(rt2, "1", (19.6, 7.0), sym=(0, 0))
    # the mirror: emitters joined under the body, VS from a via on the left; the diode node down the right and along the
    # channel to C1, the pair's C1 up into it
    t.wire("VS", [(qp, "4"), (15.0, 3.65), (15.0, 4.95), (qp, "1")], width=WF, silk=False)
    t.wire("VS", [(12.9, 3.65), (qp, "4")], width=W)
    t.wire("MD", [(qp, "5"), (13.4, 4.3), (13.4, 4.95), (qp, "6")], width=WF)
    t.wire("MD", [(qp, "2"), (16.9, 4.3), (16.9, 5.85), (14.1625, 5.85), (qp, "6")], width=WF)
    t.wire("MD", [(qn, "3"), (15.8375, 5.85)], width=WF)
    # the pair: emitters joined on the left, then under the body and out of its bottom to the tail's collector
    t.wire("EM", [(qn, "4"), (qn, "5")], width=WF, silk=False)
    t.wire("EM", [(qn, "5"), (15.0, 7.4), (15.0, 8.9), (qt, "3")], width=WF)
    # the output node: the mirror's C2 and the pair's C2 to vias, joined on the back and on to the TIA's -IN
    t.wire("MO", [(qp, "3"), (16.6, 3.65), (17.2, 3.3)], width=WF)
    t.wire("MO", [(qn, "6"), (13.0, 8.6)], width=WF)
    t.wire("MO", [(17.2, 3.3), (17.9, 4.0), (17.9, 9.0), (13.0, 9.0), (13.0, 8.6)], layer="B.Cu", silk=False, width=W)
    t.wire("MO", [(13.0, 8.6), (13.0, 9.0), (22.0, 9.0), (24.4, 11.4), (24.4, 13.6)], layer="B.Cu", silk=False, width=W)
    # the tail: its base divider and emitter resistor, -5 V along y 14.6 with its capacitor, a via to the margin
    t.wire("TB", [(qt, "1"), (14.1, 11.44), (rb1, "2")], width=W)
    t.wire("TB", [(14.1, 11.44), (14.1, 12.6), (rb2, "2")], width=W)
    t.wire("TE", [(qt, "2"), (re, "2")], width=W)
    t.wire("-5V", [(rb2, "1"), (12.69, 14.6), (16.79, 14.6), (re, "1")], width=W)
    t.wire("-5V", [(14.8, 14.6), (cn1, "2")], width=W)
    rail(t, "-5V", (13.6, 14.6), "margin")
    t.gnd_stub(rb1, "1", (12.69, 10.5), sym=(0, 0))
    t.gnd_stub(cn1, "1", (14.8, 17.0), sym=(0, 0))
    # the TIA (OPA810 at rot 270: +IN, V-, OUT along its top; -IN, V+ along its bottom), Rf and Cf under it
    u = t.add("U", "OPA810", "OPA810", 26.4, 13.6, 270, {"1": "OA", "2": "-5V", "3": "GND", "4": "MO", "5": "VS"}, hide_value=False, label=None)
    rf = t.add("R", "R0402 1k", "1k", 26.6, 16.8, 0, {"1": "MO", "2": "OA"}, label=None)
    cf = t.add("C", "C0402 4.7pF", "4.7p", 26.6, 18.0, 0, {"1": "MO", "2": "OA"}, label=None)
    ro = t.add("R", "R0402 49.9R", "49.9", 31.0, 10.6, 0, {"1": "OA", "2": "OUT"}, label=None)
    cn2 = t.add("C", "C0402 100nF", "100n", 26.8, 10.2, 0, {"1": "-5V", "2": "GND"}, label=None)
    cp2 = t.add("C", "C0402 100nF", "100n", 30.0, 16.2, 270, {"1": "GND", "2": "VS"}, label=None)         # pad 1 up
    t.wire("MO", [(24.4, 13.6), (24.4, 18.0), (cf, "1")], width=W)
    t.wire("MO", [(24.4, 14.7375), (u, "4")], width=W)
    t.wire("MO", [(24.4, 16.8), (rf, "1")], width=W)
    t.wire("OA", [(u, "1"), (28.4, 12.4625), (28.4, 18.0), (cf, "2")], width=W)
    t.wire("OA", [(28.4, 16.8), (rf, "2")], width=W)
    t.wire("OA", [(28.4, 12.4625), (28.4, 10.6), (ro, "1")], width=W)
    t.wire("OUT", [(ro, "2"), (36.75, 10.6), ("J%d03" % t.idx, "1")])
    t.gnd_stub(u, "3", (25.45, 11.2), sym=(0, 0))
    t.via("-5V", 26.4, 11.2)
    t.wire("-5V", [(u, "2"), (26.4, 11.2), (cn2, "1")], width=W)
    t.wire("-5V", [(26.4, 11.2), (31.8, 11.2), (31.8, 21.0)], layer="B.Cu", silk=False)
    t.via("-5V", 31.8, 21.0)
    t.gnd_stub(cn2, "2", (27.9, 9.4), sym=(0, 0))
    t.via("VS", 27.35, 15.95)
    t.wire("VS", [(u, "5"), (27.35, 15.95)], width=W)
    # VS: the FET's drain right along y 18.5 to a via under the tail (and one at 10.6 for the mirror, up the back on the
    # left), along the back to the TIA's capacitor and its V+
    t.wire("VS", [HDR_VS, (8.54, 18.5), (17.6, 18.5)])
    t.via("VS", 10.6, 18.5)
    t.wire("VS", [(10.6, 18.5), (10.6, 4.4), (12.9, 3.65)], layer="B.Cu", silk=False)
    t.wire("VS", [(17.6, 18.5), (30.0, 18.5), (30.0, 17.6), (27.35, 15.95)], layer="B.Cu", silk=False)
    t.via("VS", 30.0, 17.6)
    t.wire("VS", [(30.0, 17.6), (cp2, "2")], width=W)
    t.gnd_stub(cp2, "1", (30.9, 15.0), sym=(0, 0))
    # --- the Pmod plug, below the left cell in the bottom margin: JLCPCB's pad p is Pmod pin (13 - p) as check_pmod says
    pm = t.add("J", "PMOD", "Pmod", 2.97, 24.25, 0, {"1": "/PMOD_VCC", "2": "/PMOD_VCC", "3": "GND", "4": "GND", "5": "/PMOD8", "6": "/PMOD4",
                                                      "7": "/PMOD7", "8": "/PMOD3", "9": "/PMOD6", "10": "/PMOD2", "11": "/PMOD5", "12": "/PMOD1"}, hide_value=True)
    t.wire("/PMOD_VCC", [(pm, "1"), (pm, "2")], layer="B.Cu", silk=False)
    # the lower row's two inner signal pads on the front with 0.2 mm tracks along the channel between the rows (the upper
    # row's pads take their lines straight down on the back, pads 9 and 11 theirs along the bottom edge and from the right:
    # BACK_WIRES)
    t.via("/PMOD8", -5.35, 24.25)
    t.wire("/PMOD8", [(-5.35, 24.25), (1.25, 24.25), (pm, "5")], width=0.2, silk=False)
    t.via("/PMOD7", 11.25, 24.25)
    t.wire("/PMOD7", [(11.25, 24.25), (4.85, 24.25), (pm, "7")], width=0.2, silk=False)
    t.text(6.0, 10.6, "c9", 1.5, 0.3, "center")
    t.titles.append("Differential pair")
    t.result = "OUT = -1 k x (Ic1 - Ic2): +-1 V, tanh of (IN+ - IN-) / 2 VT, linear within about +-25 mV of balance"
    t.notes = ["A matched NPN pair (DMMT3904W: 2 mV of VBE, 2 % of hFE) on a 1 mA tail; a matched PNP pair as the mirror; an OPA810",
               "holds the output node at 0 V and turns the difference current into volts.  Sweep IN+ with IN- at 0 V: the tanh, its",
               "slope gm = Itail / (4 VT), about 10 mS here; a triangle in becomes a sine-like wave out when it is driven past balance."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


def tiles():
    return [tile_c4(), tile_c5(), tile_c11(), tile_c10(), tile_c6(), tile_c8(), tile_c2(), tile_c3(), tile_c9(), tile_c12(), tile_c7(), tile_c1()]


GND_LOOPS = [(97.0, 14.5), (97.0, 23.5)]             # both in the right margin by c11, below the fiducial: the left margin carries the Pmod lanes
HOLES = []
FEET = [(5.0, 5.0), (95.0, 5.0), (95.0, 95.0), (5.0, 85.0)]
SLOTS = []
# the rails on L3: +5 V under the whole board; -5 V in the gutter under row 0, down the left margin and along the bottom
# margin; +3.3 V in the gutters under rows 1 and 2, joined down the right margin below c1's USB-C
RAIL_POURS = [("+5V", 0.6, 0.6, 99.4, 99.4, 0),
              # -5 V in the gutter under row 0 (c5 below, c6 above, c1's inverter), down the left margin and along the bottom
              # margin (c7, c9, c12)
              ("-5V", [(1.0, 27.75), (93.6, 27.75), (93.6, 29.25), (6.5, 29.25), (6.5, 93.0), (93.0, 93.0), (93.0, 94.5), (1.0, 94.5)], 1),
              # +3.3 V in the gutter under row 1 from c6's left edge to c1 (its LDO), down the gutter between columns 0 and 1 and
              # along the gutter under row 2 to c8's header: +5 V keeps a way from row 1 to row 2 under c10 and round the right
              # margin, and from row 2 to row 3 right of column 0
              ("+3V3", [(27.75, 49.25), (92.75, 49.25), (92.75, 50.75), (29.25, 50.75), (29.25, 72.25), (7.0, 72.25), (7.0, 70.75),
                        (27.75, 70.75)], 1)]
# the Pmod's lines on the back, from the tiles' vias to the plug (c9's left cell, bottom margin), in lanes that never cross:
# c5's two phases and c4's clock up to the top margin and down the left margin, c8's bit across to it, the outer lane the
# lowest at the plug; c6's clock and bit down the gutter between columns 2 and 3, c7's and c3's down the right margin, and
# all four left along the bottom margin, the farther the lower.  Pads 5 and 7 (the lower row's inner pins) take the last
# millimetres on the front through the channel between the rows (c9's 0.2 mm tracks from the vias at x 2.4 and 19.0).
BACK_WIRES = [("/PMOD8", [(52.15, 10.5), (52.15, 2.4), (2.4, 2.4), (2.4, 96.5)]),
              ("/PMOD4", [(51.35, 11.65), (51.35, 3.2), (3.2, 3.2), (3.2, 93.6), (9.45, 93.6), (9.45, 95.23)]),
              ("/PMOD3", [(23.35, 10.05), (23.35, 4.0), (4.0, 4.0), (4.0, 92.9), (11.99, 92.9), (11.99, 95.23)]),
              ("/PMOD2", [(17.35, 61.35), (4.8, 61.35), (4.8, 92.2), (14.53, 92.2), (14.53, 95.23)]),
              ("/PMOD7", [(70.35, 31.15), (71.85, 31.15), (71.85, 96.5), (19.0, 96.5)]),
              ("/PMOD1", [(70.35, 32.35), (71.15, 32.35), (71.15, 95.23), (17.07, 95.23)]),
              ("/PMOD5", [(86.05, 75.45), (86.05, 74.4), (95.2, 74.4), (95.2, 97.77), (17.07, 97.77)]),
              ("/PMOD6", [(82.45, 59.95), (82.45, 50.55), (96.0, 50.55), (96.0, 99.3), (14.53, 99.3), (14.53, 97.77)])]
BACK_TEXT_X = 50.0
QR_AT = (46.0, 20.5)                            # in c5's left cell: no through-hole pad within reach
BACK_TEXT = ["AMOD-C: power and data conversion, switched",
             "capacitors and transistors.  USB-C 5 V on c1."]
FRONT_TEXT = []


PMOD_HOST = "the bottom margin under c9"
PMOD_NAMES = {"/PMOD1": "c6's clock (about 1 MHz, to the register)", "/PMOD2": "c8's BIT (high: IN above DAC)",
              "/PMOD3": "c4's clock (100 x the corner)", "/PMOD4": "c5's phi1 (IN onto the capacitor)",
              "/PMOD5": "c7's LOGIC (high: track, low: hold)", "/PMOD6": "c3's clock (the pump runs at half of it)",
              "/PMOD7": "c6's bit (the modulator's output)", "/PMOD8": "c5's phi2 (the capacitor into the summing node)"}
HANDBOOK_INTRO = [
    "Twelve tiles on sixteen 20 mm cells, four layers.  c1 takes 5 V from its USB-C and makes -5 V (40 mA) and 3.3 V, as",
    "AMOD-A's a1 does; every other tile has a slide switch along its left edge (slider up: on).  Seven tiles take a clock,",
    "a phase or a control from the FPGA, or hand it a bit, on the Pmod plug in the bottom margin under c9, so plug in both",
    "the USB-C and the host's Pmod.  A tile's input is its top-left jack and its output its bottom-right jack.  A port's",
    "name is in capitals on its tile's frame; an input that is not 50 ohm says its impedance (IN 10K, DAC 20K) and an",
    "output read through a divider its ratio (OUT /5.7): read those at high impedance.  The back of each tile says what",
    "to know while cabling it."]
HANDBOOK_SECTIONS = [
    ["## The tiles together", "",
     "1. **Power** (Regulators).  c2's buck makes 3.6 V at 1.5 MHz and its LDO 3.3 V from it; c2's own electronic load",
     "   draws 100 mA per volt on LOAD, so a DAC step is a load step.  TRIM moves the buck from 2.2 to 5 V and pushes the",
     "   LDO into dropout.  c3's charge pump makes -5 V the way c1's LM2664 does, but at the FPGA's clock.",
     "2. **Switched capacitors.**  One law three times: c5's capacitor is a resistor of 1 / (f C), c4's filter is a ladder",
     "   of such resistors whose corner follows the clock, and c3's output resistance is 1 / (f C) again.",
     "3. **Trading speed for bits.**  c7 samples, c8 compares against the host's DAC (a successive-approximation ADC in",
     "   gateware), c6 modulates (second order: its noise rises at 40 dB per decade against AMOD-A's a6's 20) and c11",
     "   turns a voltage into a frequency (count it and it is an ADC).",
     "4. **Transistors.**  c9's differential pair (tanh, and a triangle into a sine), c10's common emitter against its",
     "   cascode (the Miller effect, on a jumper), c12's precision rectifier (an op amp hiding two diode drops).",
     "",
     "The -5 V rail is c1's 40 mA: the five tiles on +-5 V (c5, c6, c7, c9, c12) draw about 25 mA together."]]

import math
import backplots as BP
# The back panels (gen_pcb.back_panels): under each tile, what a user must know while cabling it.
BACK = {
    "c1": ["USB-C 5 V only", "+5 V 1.5 A", "-5 V 40 mA", "+3.3 V 300 mA"],
    "c4": ["CLK on IO3", "fc = fCLK / 100", "to 15 kHz", "IN +-1 V"],
    "c5": ["phases IO4, IO8", "R = 1 / f C", "C = 1 nF", "IN +-1 V"],
    "c6": ["IN +-1.65 V", "CLK IO1, BIT IO7", "needs gateware", "INT1, INT2 / 4"],
    "c2": ["buck 3.6 V 1.5 MHz", "LDO 3.3 V", "LOAD 100 mA/V,", "1 V max", "TRIM +-2 V"],
    "c3": ["IO6 clocks it", "OUT about -5 V", "R = 1 / f C"],
    "c7": ["IO5 high: track", "IO5 low: hold", "IN +-1 V", "droop 30 mV/s"],
    "c10": ["jumper on: CE", "off: cascode", "IN +-50 mV"],
    "c11": ["OUT 6.9 kHz", "CV +-1 V", "moves it"],
    "c12": ["OUT = |IN|", "DC to 100 kHz", "IN +-1 V"],
    "c8": ["BIT on IO2", "high: IN > DAC", "SAR in gateware"],
    "c9": ["IN+, IN- +-0.2 V", "linear +-25 mV", "OUT +-1 V"],
}
BACK_PLOTS = {
    "c4": BP.butterworth(5, 10e3),
    "c9": BP.curve(lambda v: -math.tanh(v / 0.0517), -0.2, 0.2, (-1.0, 1.0), ("-0.2V", "+0.2V"), ("+1", "-1 V")),
}
