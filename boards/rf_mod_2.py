"""RF-MOD-2: a coherent I/Q transceiver and microwave physics, rev A.  The second-level RF board, for the ECP5-2ADC-2DAC
board: its two DACs drive the I/Q modulator, its two ADCs read the I/Q demodulator, and one synthesizer, split, is the LO of
both, so the transmitter and the receiver share one phase.  Around them a low-noise amplifier, a log detector, an absorptive
switch, a switched noise source, a GNSS front end and a loop for NV centres' magnetic resonance.

Four layers as RF-MOD: L1 the parts, the drawn wires and a ground pour 0.25 mm from every 50 ohm line; L2 ground; L3 the
rails (+5 V everywhere, -5 V in the gutter under row 1 and under X10, the synthesizer's 3.3 V island); L4 ground with the
back-side text.  Every jack sits at a cell's top-left or bottom-right corner (the checkerboard of rev A, Prompt 12).

Designed for Prompt 13 ("work on the 2nd version of each board, filling them with whatever would make the most interesting
RF (physics and communications) tutorials"; "the second-level boards will almost certainly only be used with the 2DAC+2ADC
board").  PLAN_LEVEL2.md section 4 has the reasons.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, HERE)
import tiles as T
from tiles import Tile, power_header, HDR_VS
import geometry as G
import rf_mod

STEM = "rf_mod_2"
LAYERS = 4
USB_X = 100.0 - 2.45           # the USB-C's centre, as on RF-MOD and AMOD-A


# ------------------------------------------------------------------------------------------------------------ X1 --
def tile_x1():
    """The ADL5375-05 I/Q modulator (LFCSP-24 at (20.0, 9.0), rot 90: the I pair down its left side, the Q pair down its
    right, RFOUT on top, the LO pins along the bottom).  Each baseband input is single-ended from a DAC (+-1 V into 50
    ohm): the jack sees 68 ohm across 150 ohm into a node that 510 ohm from 5 V and 91 ohm to ground hold at 0.50 V, so
    +-1 V at the jack is +-0.34 V at the pin (0.16-0.84 V, inside the 0-1 V the pins allow); the negative pin of each
    pair sits at 0.50 V on 510 / 56 ohm (both nodes 50 ohm Thevenin, so the 41 uA bias currents cancel).  LO in through
    100 pF to LOIP, LOIN to ground through 100 pF; RFOUT through 100 pF up to the RF OUT jack.  DSOP is grounded (always
    on).  The tile's switched 5 V (VS) is an island on L3 under the chip and both networks; every VS pin and resistor
    reaches it with a via."""
    t = Tile("X1", "I/Q modulator", [(0, 2), (1, 2)], supply="+5 V", subtitle="ADL5375", sections=[], kind="rf")
    t.top_pour = True
    t.fine = True
    F = 0.15
    jI = t.jack("TL0", "I IN", "JI", "in", "+-1 V into 50 ohm", silk="I IN")
    jLO = t.jack("BR0", "LO IN", "LOJ", "in", "0 dBm", silk="LO IN")
    jRF = t.jack("TL1", "RF OUT", "RFOUT", "out", "", silk="RF OUT")
    jQ = t.jack("BR1", "Q IN", "JQ", "in", "+-1 V into 50 ohm", silk="Q IN")
    power_header(t, rail="+5V")
    t.via("VS", 9.6, 18.1)
    t.wire("VS", [HDR_VS, (9.6, 18.1)])
    pins = {"18": "VS", "24": "VS", "16": "RFO", "21": "IP", "22": "IN", "10": "QP", "9": "QN", "3": "LOI", "4": "LON", "1": "GND",
            "2": "GND", "5": "GND", "8": "GND", "11": "GND", "12": "GND", "14": "GND", "17": "GND", "19": "GND", "20": "GND", "23": "GND", "25": "GND"}
    u = t.add("U", "ADL5375", "ADL5375", 20.0, 9.0, 90, pins, hide_value=False, label=None)
    for (vx, vy) in [(x, y) for x in (19.25, 20.0, 20.75) for y in (8.25, 9.0, 9.75)]:
        t.gnd_stub(u, "25", (vx, vy), sym=(0, 0), width=F, fine=True)
    for n, pt in (("19", (18.9, 7.9)), ("20", (18.9, 8.3)), ("23", (18.9, 9.75)), ("17", (19.25, 7.9)), ("14", (20.75, 7.9)), ("2", (19.25, 10.1)),
                  ("5", (20.75, 10.1)), ("12", (21.1, 7.9)), ("11", (21.1, 8.3)), ("8", (21.1, 9.75)), ("1", (18.9, 10.1))):
        t.wire("GND", [(u, n), pt], width=F)                                            # into the paddle
    # RF: 100 pF up from RFOUT, the line along y 4.75 into the RF OUT jack between its legs
    crf = t.add("C", "C0402 100pF", "100p", 19.75, 5.4, 90, {"1": "RFO", "2": "RFOUT"}, label=None)             # pad 1 down
    t.wire("RFO", [(u, "16"), (crf, "1")], width=0.2)
    t.rf("RFOUT", [(crf, "2"), (19.75, 4.75), (jRF, "1")])
    # VPS1 (top-left corner): 100 pF and 100 nF above-left, a via to the island; VPS2 (left column, bottom): 100 nF and a via
    ca = t.add("C", "C0402 100pF", "100p", 18.4, 5.4, 90, {"1": "VS", "2": "GND"}, label=None)
    cb = t.add("C", "C0402 100nF", "100n", 17.2, 5.4, 90, {"1": "VS", "2": "GND"}, label=None)
    t.wire("VS", [(u, "18"), (18.4, 6.3), (ca, "1")], width=F)
    t.wire("VS", [(ca, "1"), (18.4, 6.05), (17.2, 6.05), (cb, "1")], width=0.2)
    t.via("VS", 17.8, 6.7, fine=True)
    t.wire("VS", [(18.4, 6.3), (17.8, 6.7)], width=F)
    t.gnd_stub(ca, "2", (18.4, 4.0), sym=(0, 0), width=0.2, fine=True)
    t.gnd_stub(cb, "2", (17.2, 4.0), sym=(0, 0), width=0.2, fine=True)
    cc = t.add("C", "C0402 100nF", "100n", 16.83, 10.78, 90, {"1": "GND", "2": "VS"}, label=None)             # pad 1 down
    t.wire("VS", [(u, "24"), (17.2, 10.25), (16.83, 10.25), (cc, "2")], width=F)
    t.via("VS", 17.2, 9.75, fine=True)
    t.wire("VS", [(17.2, 10.25), (17.2, 9.75)], width=F)
    t.wire("GND", [(cc, "1"), (18.75, 11.26), (u, "1")], width=F)                       # its ground through DSOP's pad
    # LO: 100 pF from the jack's line into LOIP, LOIN to ground through 100 pF
    clo = t.add("C", "C0402 100pF", "100p", 19.75, 12.6, 90, {"1": "LOJ", "2": "LOI"}, label=None)
    cln = t.add("C", "C0402 100pF", "100p", 21.0, 12.6, 90, {"1": "GND", "2": "LON"}, label=None)
    t.wire("LOI", [(u, "3"), (clo, "2")], width=0.2)
    t.wire("LON", [(u, "4"), (20.25, 11.6), (21.0, 11.84), (cln, "2")], width=F)
    t.gnd_stub(cln, "1", (21.0, 14.0), sym=(0, 0), width=0.2, fine=True)
    t.rf("LOJ", [(jLO, "1"), (19.75, 15.25), (clo, "1")])
    # I (left): the P node's three resistors in a column, its spine at x 16.4; the N pair below; the jack's line along y 4.75
    r3i = t.add("R", "R0402 150R", "150", 14.9, 6.6, 0, {"1": "JI", "2": "IP"}, label=None)
    r1i = t.add("R", "R0402 510R", "510", 14.9, 7.7, 0, {"1": "VS", "2": "IP"}, label=None)
    r2i = t.add("R", "R0402 91R", "91", 14.9, 8.8, 0, {"1": "GND", "2": "IP"}, label=None)
    t.wire("IP", [(r3i, "2"), (16.4, 6.6), (16.4, 8.75), (u, "21")], width=F)
    t.wire("IP", [(r1i, "2"), (16.4, 7.7)], width=F)
    t.wire("IP", [(r2i, "2"), (16.4, 8.8)], width=F)
    t.via("VS", 13.5, 7.7, fine=True)
    t.wire("VS", [(r1i, "1"), (13.5, 7.7)], width=0.2)
    t.gnd_stub(r2i, "1", (13.5, 8.8), sym=(0, 0), width=0.2, fine=True)
    r1n = t.add("R", "R0402 510R", "510", 14.8, 10.15, 0, {"1": "VS", "2": "IN"}, label=None)
    r2n = t.add("R", "R0402 56R", "56", 14.8, 11.2, 0, {"1": "GND", "2": "IN"}, label=None)
    t.wire("IN", [(u, "22"), (15.9, 9.25), (15.9, 11.2), (r2n, "2")], width=F)
    t.wire("IN", [(r1n, "2"), (15.9, 10.15)], width=F)
    t.via("VS", 13.5, 10.15, fine=True)
    t.wire("VS", [(r1n, "1"), (13.5, 10.15)], width=0.2)
    t.gnd_stub(r2n, "1", (13.5, 11.2), sym=(0, 0), width=0.2, fine=True)
    rti = t.add("R", "R0402 68R", "68", 11.0, 5.75, 270, {"1": "JI", "2": "GND"}, label=None)                    # pad 1 up
    t.wire("JI", [(jI, "1"), (12.0, 4.75), (12.0, 6.6), (r3i, "1")], width=0.25)
    t.wire("JI", [(11.0, 4.75), (rti, "1")], width=0.25)
    t.gnd_stub(rti, "2", (11.0, 7.1), sym=(0, 0), width=0.25, fine=True)
    # Q (right): the P spine at x 24.1 with its resistors to the right, the N spine at x 23.4 down to theirs below; the jack's
    # line along y 11.7 and down x 31 into the Q IN jack
    r1qp = t.add("R", "R0402 510R", "510", 25.6, 9.5, 0, {"1": "QP", "2": "VS"}, label=None)
    r2qp = t.add("R", "R0402 91R", "91", 25.6, 10.6, 0, {"1": "QP", "2": "GND"}, label=None)
    r3qp = t.add("R", "R0402 150R", "150", 25.6, 11.7, 0, {"1": "QP", "2": "JQ"}, label=None)
    t.wire("QP", [(u, "10"), (24.1, 8.75), (24.1, 11.7), (r3qp, "1")], width=F)
    t.wire("QP", [(24.1, 9.5), (r1qp, "1")], width=F)
    t.wire("QP", [(24.1, 10.6), (r2qp, "1")], width=F)
    t.via("VS", 27.0, 9.5, fine=True)
    t.wire("VS", [(r1qp, "2"), (27.0, 9.5)], width=0.2)
    t.gnd_stub(r2qp, "2", (27.0, 10.6), sym=(0, 0), width=0.2, fine=True)
    r1qn = t.add("R", "R0402 510R", "510", 25.6, 13.2, 0, {"1": "QN", "2": "VS"}, label=None)
    r2qn = t.add("R", "R0402 56R", "56", 25.6, 14.3, 0, {"1": "QN", "2": "GND"}, label=None)
    t.wire("QN", [(u, "9"), (23.4, 9.25), (23.4, 13.2), (r1qn, "1")], width=F)
    t.wire("QN", [(24.4, 13.2), (24.4, 14.3), (r2qn, "1")], width=F)
    t.via("VS", 27.0, 13.2, fine=True)
    t.wire("VS", [(r1qn, "2"), (27.0, 13.2)], width=0.2)
    t.gnd_stub(r2qn, "2", (27.0, 14.3), sym=(0, 0), width=0.2, fine=True)
    rtq = t.add("R", "R0402 68R", "68", 28.5, 12.7, 270, {"1": "JQ", "2": "GND"}, label=None)                    # pad 1 up
    t.wire("JQ", [(r3qp, "2"), (31.0, 11.7), (31.0, 15.25), (jQ, "1")], width=0.25)
    t.wire("JQ", [(28.5, 11.7), (rtq, "1")], width=0.25)
    t.gnd_stub(rtq, "2", (28.5, 14.1), sym=(0, 0), width=0.25, fine=True)
    t.text(1.2, 9.4, "X1", 1.0, 0.18, "left")
    t.info(["I/Q MODULATOR", "ADL5375 0.4-6 GHz"], near=(1.2, 10.7))
    t.result = ("about 0 dBm of single-sideband RF at full scale (I and Q +-1 V at 1 V p-p differential equivalent), 0.4-6 GHz, sideband "
                "and carrier suppression near 40 dB untrimmed; baseband flat to 95 MHz, far past the DACs' 12 MHz")
    t.notes = ["ADI ADL5375-05: two Gilbert-cell mixers and a quadrature LO splitter, 0.4-6 GHz, baseband bias 0.5 V.  Each input is",
               "single-ended from a DAC: 68 ohm at the jack, 150 ohm into 510 / 91 ohm from 5 V (0.50 V, gain 0.34); the other pin of",
               "each pair sits at 0.50 V on 510 / 56 ohm.  LO in single-ended through 100 pF (0 dBm; -6 to +6 dBm works); RF out is",
               "50 ohm through 100 pF.  Trim the carrier with small DC offsets on I and Q, the sideband with the DACs' gain and phase."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ X2 --
def tile_x2():
    """The ADL5380 I/Q demodulator (LFCSP-24 at (21.6, 11.0), rot 0: RF on top, LO along the bottom, the I outputs down its
    left side, Q down its right) and two OPA810 difference amplifiers that turn each 2.5 V-common-mode pair into one output
    around 0 V for the ECP5 board's +-1 V ADCs: 499 ohm into each input, 1 k of feedback and 1 k to ground (gain 2), 49.9
    ohm out, so a 50 ohm ADC sees the pair's difference and a high-impedance one twice it.  RF in single-ended to RFIN
    through 100 pF (RFIP to ground through 100 pF), LO likewise; ADJ on 1.5 k to 5 V (the datasheet's value below 3 GHz);
    ENBL grounded.  The amplifiers run from the tile's 5 V and the board's -5 V; the 5 V is an island on L3."""
    t = Tile("X2", "I/Q demodulator", [(2, 2), (3, 2)], supply="+5 V", subtitle="ADL5380", sections=[], kind="rf")
    t.top_pour = True
    t.fine = True
    F = 0.15
    jI = t.jack("TL0", "I OUT", "JIO", "out", "+-1 V", silk="I OUT")
    jLO = t.jack("BR0", "LO IN", "LOJ", "in", "0 dBm", silk="LO IN")
    jRF = t.jack("TL1", "RF IN", "RFJ", "in", "-10 dBm", silk="RF IN")
    jQ = t.jack("BR1", "Q OUT", "JQO", "out", "+-1 V", silk="Q OUT")
    power_header(t, rail="+5V")
    t.via("VS", 9.6, 18.1)
    t.wire("VS", [HDR_VS, (9.6, 18.1)])
    pins = {"3": "IHI", "4": "ILO", "16": "QHI", "15": "QLO", "6": "VS", "13": "VS", "24": "VS", "7": "GND", "9": "LOI", "10": "LON",
            "19": "ADJ", "21": "RFI", "22": "RFP", "1": "GND", "2": "GND", "5": "GND", "8": "GND", "11": "GND", "14": "GND", "17": "GND",
            "18": "GND", "20": "GND", "23": "GND", "25": "GND"}
    u = t.add("U", "ADL5380", "ADL5380", 21.6, 11.0, 0, pins, hide_value=False, label=None)
    for (vx, vy) in [(x, y) for x in (20.85, 21.6, 22.35) for y in (10.25, 11.0, 11.75)]:
        t.gnd_stub(u, "25", (vx, vy), sym=(0, 0), width=F, fine=True)
    for n, pt in (("1", (20.5, 9.9)), ("2", (20.5, 10.25)), ("5", (20.5, 11.75)), ("18", (22.7, 9.9)), ("17", (22.7, 10.25)), ("14", (22.7, 11.75)),
                  ("23", (20.85, 9.9)), ("20", (22.35, 9.9)), ("8", (20.85, 12.1)), ("11", (22.35, 12.1)), ("7", (20.4, 12.1))):
        t.wire("GND", [(u, n), pt], width=F)                                             # into the paddle
    # RF: RFIN from the RF IN jack through 100 pF, RFIP to ground through 100 pF
    crf = t.add("C", "C0402 100pF", "100p", 21.85, 7.4, 90, {"1": "RFI", "2": "RFJ"}, label=None)               # pad 1 down
    crp = t.add("C", "C0402 100pF", "100p", 20.6, 7.4, 90, {"1": "RFP", "2": "GND"}, label=None)
    t.wire("RFI", [(u, "21"), (crf, "1")], width=0.2)
    t.rf("RFJ", [(jRF, "1"), (21.85, 4.75), (crf, "2")])
    t.wire("RFP", [(u, "22"), (21.35, 8.35), (20.85, 8.0), (crp, "1")], width=F)
    t.gnd_stub(crp, "2", (20.6, 6.0), sym=(0, 0), width=0.2, fine=True)
    # VCC (24, top-left): 100 pF and 100 nF up-left, a via to the island
    ca = t.add("C", "C0402 100pF", "100p", 19.4, 7.4, 90, {"1": "VS", "2": "GND"}, label=None)
    cb = t.add("C", "C0402 100nF", "100n", 18.2, 7.4, 90, {"1": "VS", "2": "GND"}, label=None)
    t.wire("VS", [(u, "24"), (20.35, 8.5), (19.9, 8.45), (19.4, 8.16), (ca, "1")], width=F)
    t.wire("VS", [(ca, "1"), (19.4, 8.25), (18.2, 8.25), (cb, "1")], width=0.2)
    t.via("VS", 17.5, 8.25, fine=True)
    t.wire("VS", [(18.2, 8.25), (17.5, 8.25)], width=F)
    t.gnd_stub(ca, "2", (19.4, 6.0), sym=(0, 0), width=0.2, fine=True)
    t.gnd_stub(cb, "2", (18.2, 6.0), sym=(0, 0), width=0.2, fine=True)
    # ADJ: 1.5 k to the island
    radj = t.add("R", "R0402 1.5k", "1.5k", 25.6, 9.2, 0, {"1": "ADJ", "2": "VS"}, label=None)
    t.wire("ADJ", [(u, "19"), (24.6, 9.05), (radj, "1")], width=F)
    t.via("VS", 26.08, 8.45, fine=True)
    t.wire("VS", [(radj, "2"), (26.08, 8.45)], width=0.2)
    # VCC (6 and 13, the bottom corners): a via to the island and 100 nF each
    t.via("VS", 19.7, 13.25, fine=True)
    t.wire("VS", [(u, "6"), (19.65, 12.6), (19.7, 13.25)], width=F)
    c6 = t.add("C", "C0402 100nF", "100n", 19.7, 14.6, 90, {"1": "GND", "2": "VS"}, label=None)              # pad 1 down
    t.wire("VS", [(19.7, 13.25), (c6, "2")], width=F)
    t.gnd_stub(c6, "1", (20.4, 15.5), sym=(0, 0), width=0.2, fine=True)
    t.via("VS", 23.5, 13.25, fine=True)
    t.wire("VS", [(u, "13"), (23.55, 12.6), (23.5, 13.25)], width=F)
    c13 = t.add("C", "C0402 100nF", "100n", 23.9, 14.6, 90, {"1": "GND", "2": "VS"}, label=None)
    t.wire("VS", [(23.5, 13.25), (23.9, 13.84), (c13, "2")], width=F)
    t.gnd_stub(c13, "1", (23.9, 16.0), sym=(0, 0), width=0.2, fine=True)
    # LO: from the LO IN jack under the bottom-right leg, through 100 pF into LOIP; LOIN to ground through 100 pF
    clo = t.add("C", "C0402 100pF", "100p", 21.35, 14.6, 90, {"1": "LOJ", "2": "LOI"}, label=None)
    cln = t.add("C", "C0402 100pF", "100p", 22.6, 14.6, 90, {"1": "GND", "2": "LON"}, label=None)
    t.wire("LOI", [(u, "9"), (clo, "2")], width=0.2)
    t.wire("LON", [(u, "10"), (21.85, 13.6), (22.6, 13.84), (cln, "2")], width=F)
    t.gnd_stub(cln, "1", (22.6, 16.0), sym=(0, 0), width=0.2, fine=True)
    t.rf("LOJ", [(jLO, "1"), (16.2, 16.2), (21.35, 16.2), (clo, "1")])
    # the I amplifier (OPA810 rot 90 at (13.5, 5.6): OUT, V-, +IN along the bottom, V+ and -IN along the top)
    ui = t.add("U", "OPA810", "OPA810", 13.5, 5.6, 90, {"1": "IOA", "2": "-5V", "3": "IAP", "4": "IAN", "5": "VS"}, hide_value=False, label=None)
    t.via("VS", 12.55, 5.6, fine=True)
    t.wire("VS", [(ui, "5"), (12.55, 5.6)], width=F)
    t.via("-5V", 13.5, 5.6, fine=True)
    t.wire("-5V", [(ui, "2"), (13.5, 5.6)], width=F)
    t.wire("-5V", [(13.5, 5.6), (13.5, -0.75)], width=0.2, layer="B.Cu", silk=False, fine=True)
    cni = t.add("C", "C0402 100nF", "100n", 13.9, 8.3, 0, {"1": "-5V", "2": "GND"}, label=None)
    t.wire("-5V", [(ui, "2"), (13.42, 8.3)], width=F)
    t.gnd_stub(cni, "2", (15.3, 8.3), sym=(0, 0), width=0.2, fine=True)
    rai = t.add("R", "R0402 499R", "499", 17.2, 10.35, 0, {"1": "IAP", "2": "IHI"}, label=None)
    rbi = t.add("R", "R0402 1k", "1k", 16.9, 9.2, 0, {"1": "IAP", "2": "GND"}, label=None)
    t.wire("IHI", [(u, "3"), (18.3, 10.75), (17.9, 10.35), (rai, "2")], width=F)
    t.wire("IAP", [(rai, "1"), (15.8, 10.35), (15.8, 7.6), (14.6, 7.25), (ui, "3")], width=F)
    t.wire("IAP", [(15.8, 9.2), (rbi, "1")], width=F)
    t.gnd_stub(rbi, "2", (17.9, 9.2), sym=(0, 0), width=0.2, fine=True)
    rci = t.add("R", "R0402 499R", "499", 16.6, 4.4, 270, {"1": "ILO", "2": "IAN"}, label=None)               # pad 1 up
    t.wire("ILO", [(u, "4"), (18.7, 11.25)], width=F)
    t.wire("ILO", [(18.7, 11.25), (18.7, 3.2), (16.6, 3.2)], width=F, layer="B.Cu", silk=False, fine=True)
    t.wire("ILO", [(16.6, 3.2), (rci, "1")], width=F, silk=False)
    t.wire("IAN", [(rci, "2"), (15.2, 4.6), (ui, "4")], width=F)
    rfi = t.add("R", "R0402 1k", "1k", 11.2, 5.9, 90, {"1": "IOA", "2": "IAN"}, label=None)                  # pad 1 down
    t.wire("IAN", [(ui, "4"), (14.45, 3.2), (11.2, 3.2), (rfi, "2")], width=F)
    roi = t.add("R", "R0402 49.9R", "49.9", 9.9, 6.2, 270, {"1": "JIO", "2": "IOA"}, label=None)               # pad 1 up
    t.wire("IOA", [(ui, "1"), (12.55, 7.8), (9.9, 7.8), (roi, "2")], width=0.2)
    t.wire("IOA", [(11.2, 7.8), (rfi, "1")], width=0.2)
    t.wire("JIO", [(roi, "1"), (9.9, 4.75), (jI, "1")], width=0.25)
    # the Q amplifier (OPA810 rot 270 at (29.0, 13.0): +IN, V-, OUT along the top, -IN and V+ along the bottom), its feedback
    # round the right side, 49.9 ohm up to a line along y 9 and down into the Q OUT jack between its legs
    uq = t.add("U", "OPA810", "OPA810", 29.0, 13.0, 270, {"1": "QOA", "2": "-5V", "3": "QAP", "4": "QAN", "5": "VS"}, hide_value=False, label=None)
    t.via("VS", 29.95, 13.0, fine=True)
    t.wire("VS", [(uq, "5"), (29.95, 13.0)], width=F)
    t.via("-5V", 29.0, 13.0, fine=True)
    t.wire("-5V", [(uq, "2"), (29.0, 13.0)], width=F)
    t.wire("-5V", [(29.0, 13.0), (29.0, 10.0), (30.6, 8.4), (30.6, -0.75)], width=0.2, layer="B.Cu", silk=False, fine=True)
    cnq = t.add("C", "C0402 100nF", "100n", 29.4, 10.2, 0, {"1": "-5V", "2": "GND"}, label=None)
    t.wire("-5V", [(uq, "2"), (28.92, 10.5), (cnq, "1")], width=F)
    t.gnd_stub(cnq, "2", (30.6, 9.6), sym=(0, 0), width=0.2, fine=True)
    raq = t.add("R", "R0402 499R", "499", 25.6, 10.75, 0, {"1": "QHI", "2": "QAP"}, label=None)
    rbq = t.add("R", "R0402 1k", "1k", 27.1, 9.6, 270, {"1": "GND", "2": "QAP"}, label=None)                  # pad 1 up
    t.wire("QHI", [(u, "16"), (raq, "1")], width=F)
    t.wire("QAP", [(raq, "2"), (27.1, 10.75), (27.6, 11.25), (28.05, 11.5), (uq, "3")], width=F)
    t.wire("QAP", [(27.1, 10.75), (rbq, "2")], width=F)
    t.gnd_stub(rbq, "1", (27.1, 8.4), sym=(0, 0), width=0.2, fine=True)
    rcq = t.add("R", "R0402 499R", "499", 25.6, 12.3, 0, {"1": "QLO", "2": "QAN"}, label=None)
    t.wire("QLO", [(u, "15"), (24.6, 11.25), (24.6, 12.3), (rcq, "1")], width=F)
    t.wire("QAN", [(rcq, "2"), (26.8, 12.3), (26.8, 14.14), (uq, "4")], width=F)
    rfq = t.add("R", "R0402 1k", "1k", 31.6, 13.0, 90, {"1": "QAN", "2": "QOA"}, label=None)                  # pad 1 down
    t.wire("QAN", [(uq, "4"), (28.05, 15.6), (31.6, 15.6), (rfq, "1")], width=F)
    roq = t.add("R", "R0402 49.9R", "49.9", 32.6, 10.4, 90, {"1": "QOA", "2": "JQO"}, label=None)              # pad 1 down
    t.wire("QOA", [(uq, "1"), (31.0, 11.86), (32.6, 11.86), (roq, "1")], width=0.2)
    t.wire("QOA", [(31.6, 11.86), (rfq, "2")], width=0.2)
    t.wire("JQO", [(roq, "2"), (32.6, 9.0), (36.75, 9.0), (jQ, "1")], width=0.25)
    t.text(1.2, 9.4, "X2", 1.0, 0.18, "left")
    t.info(["I/Q DEMODULATOR"], near=(1.2, 10.7))
    t.titles.append("ADL5380")
    t.result = ("I and Q of the RF input against the LO, 0.4-6 GHz: about 7 dB of conversion gain from the chip, x2 in the amplifiers, "
                "+-1 V at the ADC for about -4 dBm of RF; flat from DC to beyond the ADCs' 23 MHz")
    t.notes = ["ADI ADL5380: a quadrature demodulator, 0.4-6 GHz, 390 MHz of baseband, I and Q as differential pairs at 2.5 V.  Two OPA810",
               "difference amplifiers (499 ohm in, 1 k feedback and to ground: gain 2) make each pair one output about 0 V from +5 / -5 V;",
               "49.9 ohm out.  RF and LO single-ended through 100 pF, the other pin to ground through 100 pF (a balun would gain 1-3 dB",
               "and IP2).  ADJ 1.5 k to 5 V suits 0.4-3 GHz (open it above 5 GHz).  With X3 through X5 on both LOs: one coherent radio."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ X9 --
def tile_x9():
    """A loop for NV centres' magnetic resonance: the IN line (50 ohm CPW) runs to a one-turn loop 1.6 mm across at the cell's
    centre and on to the OUT jack, so the current that makes the field is the line's own and nothing resonates: any frequency
    from DC to 6 GHz, the 2.87 GHz of NV's zero-field splitting and every Zeeman line around it.  No copper on any layer within
    2 mm of the loop (a plane under it would carry the image current and cancel the field).  Terminate OUT in 50 ohm, or in a
    short to double the current (the source sees the reflection)."""
    import math
    t = Tile("X9", "ODMR loop", [(0, 0)], subtitle="", sections=[], kind="rf")
    t.top_pour = True
    jin = t.jack("TL", "IN", "LOOP", "in", "+30 dBm", silk="IN")
    jout = t.jack("BR", "OUT", "LOOP", "out", "", silk="OUT")
    cx, cy, r = 9.4, 9.4, 0.8
    arc = [(round(cx + r * math.cos(math.radians(a)), 3), round(cy + r * math.sin(math.radians(a)), 3)) for a in range(120, 421, 15)]
    xa, xb, ya = arc[0][0], arc[-1][0], arc[0][1]
    t.wire("LOOP", [(xa, 11.6)] + arc + [(xb, 11.0), (11.6, 11.0)], width=0.3, silk=False)       # inside the void: no fence, no pour
    t.rf("LOOP", [(jin, "1"), (4.75, 12.4), (xa, 12.4), (xa, 11.6)])
    t.rf("LOOP", [(11.6, 11.0), (14.0, 11.0), (15.25, 12.25), (jout, "1")])
    t.voids.append((cx, cy, 2.0, "all"))
    t.text(14.6, 2.4, "X9", 1.2, 0.2, "center")
    t.text(19.0, 4.3, "NV ODMR LOOP", 0.8, 0.15, "right")
    t.text(19.0, 5.6, "DC - 6 GHz", 0.8, 0.15, "right")
    t.text(1.2, 14.7, "DIAMOND ON", 0.8, 0.15, "left")
    t.text(1.2, 16.0, "THE LOOP", 0.8, 0.15, "left")
    t.text(1.2, 17.3, "50 uT AT", 0.8, 0.15, "left")
    t.text(1.2, 18.6, "+20 dBm", 0.8, 0.15, "left")
    t.result = ("a 50 ohm through line (the loop adds about 1.5 nH); at its centre about 50 uT (0.5 G) of microwave field for +20 dBm "
                "through it into 50 ohm, a Rabi frequency near 1 MHz for NV centres; twice that with OUT shorted")
    t.notes = ["A one-turn loop, 1.6 mm across (0.3 mm track), in series with a 50 ohm line between IN and OUT.  B at its centre is",
               "mu0 I / 2a: 63 mA peak (+20 dBm into 50 ohm) gives 50 uT.  No resonance, so no tuning: sweep 2.6-3.2 GHz for ODMR",
               "in any bias field.  Copper is cleared on every layer within 2 mm of the loop.  Lay the diamond on the loop, shine",
               "green on it from above and read the red with the ECP5 board's photodiode."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ X6 --
def tile_x6():
    """The AD8318 log detector (LFCSP-16 at (14.0, 6.5), rot 90: the input pins on its left, VOUT and VSET on its right, TADJ
    and VPSO along the top, VPSI along the bottom).  ADI's basic connections: 51 ohm across the input, 1 nF to INHI and from
    INLO to ground, 499 ohm on TADJ, VSET tied to VOUT (measurement mode, -25 mV/dB), CLPF open (10 ns).  VOUT (0.5-2.1 V)
    through 110 ohm into 91 ohm to ground: a 50 ohm source, 0.23-0.95 V open (inside the ADC's +-1 V), half that into 50 ohm."""
    t = Tile("X6", "log detector", [(1, 0)], supply="+5 V", subtitle="AD8318", sections=[], kind="rf")
    t.top_pour = True
    t.fine = True
    F = 0.15
    jin = t.jack("TL", "IN", "IN", "in", "0 dBm", silk="IN")
    jout = t.jack("BR", "OUT", "OUT", "out", "0.23-0.95 V open", silk="OUT")
    power_header(t, rail="+5V")
    u = t.add("U", "AD8318", "AD8318", 14.0, 6.5, 90, {"14": "HI", "15": "LO", "16": "VS", "3": "VS", "4": "VS", "9": "VS", "10": "TADJ",
                                                     "6": "VO", "7": "VO", "8": "GND", "1": "GND", "2": "GND", "11": "GND", "12": "GND", "17": "GND"},
              hide_value=False, label=None)
    for (vx, vy) in ((13.5, 6.0), (14.5, 6.0), (13.5, 7.0), (14.5, 7.0)):
        t.gnd_stub(u, "17", (vx, vy), sym=(0, 0), width=F, fine=True)
    for n, pt in (("1", (13.025, 7.5)), ("2", (13.675, 7.5)), ("11", (13.675, 5.5)), ("12", (13.025, 5.5)), ("8", (15.0, 5.525))):
        t.wire("GND", [(u, n), pt], width=F)                                          # into the paddle
    # the input: 51 ohm across the line, 1 nF into INHI, INLO to ground through 1 nF
    rt = t.add("R", "R0402 51R", "51R", 9.1, 3.7, 90, {"1": "IN", "2": "GND"}, label=None)                  # pad 1 down
    c1 = t.add("C", "C0402 1nF", "1n", 10.3, 5.6, 270, {"1": "IN", "2": "HI"}, label=None)                  # pad 1 up
    c2 = t.add("C", "C0402 1nF", "1n", 10.8, 7.9, 270, {"1": "LO", "2": "GND"}, label=None)
    t.rf("IN", [(jin, "1"), (10.3, 4.75), (c1, "1")])
    t.wire("IN", [(9.1, 4.75), (rt, "1")], width=0.25)
    t.gnd_stub(rt, "2", (9.1, 2.3), sym=(0, 0), width=0.25, fine=True)
    t.wire("HI", [(c1, "2"), (10.3, 6.175), (u, "14")], width=0.2)
    t.wire("LO", [(u, "15"), (10.8, 6.825), (c2, "1")], width=F)
    t.gnd_stub(c2, "2", (10.0, 8.38), sym=(0, 0), width=0.2, fine=True)
    # the supplies: VS up from the header's FET to a bus under the chip (VPSI, ENBL), on the back to the VPSO pair at the top
    t.wire("VS", [HDR_VS, (8.54, 9.6), (16.3, 9.6)], width=0.25)
    t.wire("VS", [(u, "16"), (11.75, 7.475), (11.75, 9.6)], width=F)
    t.wire("VS", [(u, "3"), (14.325, 9.6)], width=F)
    t.wire("VS", [(u, "4"), (14.975, 9.6)], width=F)
    cc = t.add("C", "C0402 100pF", "100p", 10.0, 10.6, 270, {"1": "VS", "2": "GND"}, label=None)
    cd = t.add("C", "C0402 100nF", "100n", 11.2, 10.6, 270, {"1": "VS", "2": "GND"}, label=None)
    t.wire("VS", [(10.0, 9.6), (cc, "1")], width=0.25)
    t.wire("VS", [(11.2, 9.6), (cd, "1")], width=0.25)
    t.gnd_stub(cc, "2", (10.0, 11.9), sym=(0, 0), width=0.25, fine=True)
    t.gnd_stub(cd, "2", (11.2, 11.9), sym=(0, 0), width=0.25, fine=True)
    c10 = t.add("C", "C0805 10uF", "10u", 10.7, 14.6, 270, {"1": "GND", "2": "VS"}, label=None)              # pad 1 up
    t.wire("VS", [(8.54, 15.55), (c10, "2")])
    t.gnd_stub(c10, "1", [(10.0, 13.65), (10.0, 13.0)], sym=(0, 0))
    ca = t.add("C", "C0402 100pF", "100p", 17.75, 3.6, 0, {"1": "VS", "2": "GND"}, label=None)
    cb = t.add("C", "C0402 100nF", "100n", 17.75, 2.5, 0, {"1": "VS", "2": "GND"}, label=None)
    t.wire("VS", [(u, "9"), (14.975, 3.6), (ca, "1")], width=F)
    t.wire("VS", [(ca, "1"), (cb, "1")], width=0.2)
    t.wire("VS", [(16.3, 9.6), (16.3, 2.5)], layer="B.Cu", silk=False, fine=True)
    t.wire("VS", [(16.3, 2.5), (cb, "1")], width=0.2, silk=False)
    t.gnd_stub(ca, "2", (19.2, 3.6), sym=(0, 0), width=0.2, fine=True)
    t.gnd_stub(cb, "2", (19.2, 2.5), sym=(0, 0), width=0.2, fine=True)
    rtadj = t.add("R", "R0402 499R", "499", 14.325, 2.85, 90, {"1": "TADJ", "2": "GND"}, label=None)         # pad 1 down
    t.wire("TADJ", [(u, "10"), (rtadj, "1")], width=F)
    t.gnd_stub(rtadj, "2", (14.325, 1.45), sym=(0, 0), width=0.2, fine=True)
    # the output: VSET tied to VOUT, 110 ohm into 91 ohm, down to the OUT jack between its legs
    rtop = t.add("R", "R0402 110R", "110", 17.2, 8.4, 270, {"1": "VO", "2": "OUT"}, label=None)              # pad 1 up
    rbot = t.add("R", "R0402 91R", "91", 18.5, 9.9, 0, {"1": "OUT", "2": "GND"}, label=None)
    t.wire("VO", [(u, "7"), (16.6, 6.175), (16.6, 6.825)], width=F)
    t.wire("VO", [(u, "6"), (17.2, 6.825), (rtop, "1")], width=0.2)
    t.wire("OUT", [(rtop, "2"), (17.2, 9.9), (rbot, "1")], width=0.25)
    t.gnd_stub(rbot, "2", (18.98, 10.9), sym=(0, 0), width=0.25, fine=True)
    t.wire("OUT", [(17.2, 9.9), (17.2, 10.6), (15.25, 12.55), (jout, "1")], width=0.25)
    t.text(1.2, 9.6, "X6", 1.0, 0.18, "left")
    t.text(1.2, 10.9, "AD8318", 0.8, 0.15, "left")
    t.titles.append("POWER METER")
    t.result = ("VOUT falls 25 mV per dB of input from -60 to 0 dBm, 1 MHz-8 GHz (2.1 V at -60 dBm, 0.6 V at 0 dBm at the chip); at the jack "
                "0.45 x that from 50 ohm: 0.27-0.95 V into the ADC's high impedance, half into 50 ohm; 10 ns response")
    t.notes = ["ADI AD8318: a nine-stage log amplifier with detectors, 60 dB of range to 8 GHz, temperature-compensated (499 ohm on TADJ",
               "suits 0.9-2.2 GHz).  VSET = VOUT: -25 mV/dB with an intercept near +20 dBm.  CLPF is open, so it follows a pulse in 10 ns:",
               "a radar's or a pulsed experiment's envelope at the ADC's 65 MS/s.  The 110 / 91 ohm divider keeps the 0.5-2.1 V inside",
               "the ADC's +-1 V and makes the output a 50 ohm source.  A power meter, a scalar network analyzer with X3, antenna patterns."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ X8 --
def tile_x8():
    """A GNSS front end for an active antenna: a bias-T on ANT (3.3 V through 10 ohm and 18 nH, for the antenna's own LNA), a
    100 pF block, Murata's 1561-1602 MHz SAW, Maxim's MAX2659 LNA (470 pF and 6.8 nH at its input, its own matched, blocked
    output), a second SAW, OUT.  A TPS7A2033 makes the 3.3 V from the tile's switched 5 V."""
    t = Tile("X8", "GNSS front end", [(3, 0)], supply="+5 V", subtitle="MAX2659", sections=[], kind="rf")
    t.top_pour = True
    t.fine = True
    F = 0.15
    jant = t.jack("TL", "ANT", "ANT", "in", "3.3 V on the centre", silk="ANT")
    jout = t.jack("BR", "OUT", "OUT", "out", "", silk="OUT")
    power_header(t, rail="+5V")
    # along y 4.75: the block, the first SAW, 470 pF and 6.8 nH, the MAX2659 (rot 180: RFIN top-left, RFOUT bottom-right)
    cdc = t.add("C", "C0402 100pF", "100p", 10.6, 4.75, 0, {"1": "ANT", "2": "S1"}, label=None)
    saw1 = t.add("FL", "SAW1G57", "SAW", 12.32, 4.75, 0, {"1": "S1", "4": "S1O", "2": "GND", "3": "GND", "5": "GND"}, hide_value=True, label=None)
    c470 = t.add("C", "C0402 470pF", "470p", 14.04, 4.5, 0, {"1": "S1O", "2": "M1"}, label=None)
    l68 = t.add("L", "L0402 6.8nH", "6.8n", 15.96, 4.5, 0, {"1": "M1", "2": "RFIN"}, label=None)
    u = t.add("U", "MAX2659", "MAX2659", 17.88, 5.0, 180, {"3": "RFIN", "1": "GND", "2": "GND", "4": "V33", "5": "V33", "6": "LNO"}, hide_value=False, label=None)
    t.rf("ANT", [(jant, "1"), (cdc, "1")])
    t.wire("S1", [(cdc, "2"), (saw1, "1")], width=0.2)
    t.wire("GND", [(saw1, "2"), (12.52, 5.4)], width=F)
    t.wire("GND", [(saw1, "3"), (12.52, 5.4)], width=F)
    t.gnd_stub(saw1, "3", [(12.52, 5.4), (12.52, 5.85)], sym=(0, 0), width=F, fine=True)
    t.gnd_stub(saw1, "5", (12.32, 3.65), sym=(0, 0), width=F, fine=True)
    t.wire("S1O", [(saw1, "4"), (c470, "1")], width=0.2)
    t.wire("M1", [(c470, "2"), (l68, "1")], width=0.25)
    t.wire("RFIN", [(l68, "2"), (16.9, 4.583), (u, "3")], width=0.2)
    t.wire("GND", [(u, "2"), (17.88, 3.9), (18.38, 3.9), (u, "1")], width=F)
    t.gnd_stub(u, "1", (18.38, 3.0), sym=(0, 0), width=F, fine=True)
    t.wire("V33", [(u, "4"), (u, "5")], width=F)
    c33 = t.add("C", "C0402 33nF", "33n", 17.38, 7.1, 270, {"1": "V33", "2": "GND"}, label=None)             # pad 1 up
    t.wire("V33", [(u, "4"), (c33, "1")], width=F)
    t.gnd_stub(c33, "2", (17.38, 8.5), sym=(0, 0), width=F, fine=True)
    # the second SAW below the LNA (rot 270: in at the top), OUT along y 10 and down between the jack's legs
    saw2 = t.add("FL", "SAW1G57", "SAW", 18.38, 9.1, 270, {"1": "LNO", "4": "OUT", "2": "GND", "3": "GND", "5": "GND"}, hide_value=True, label=None)
    t.wire("LNO", [(u, "6"), (saw2, "1")], width=0.2)
    t.wire("GND", [(saw2, "2"), (17.75, 9.3)], width=F)
    t.gnd_stub(saw2, "3", [(17.75, 9.3), (17.45, 9.3)], sym=(0, 0), width=F, fine=True)
    t.gnd_stub(saw2, "5", (19.3, 9.1), sym=(0, 0), width=F, fine=True)
    t.wire("OUT", [(saw2, "4"), (18.63, 10.0), (16.6, 10.0), (15.25, 11.35), (jout, "1")], width=0.28)
    # the bias-T under the ANT line: 18 nH down to VA, 10 ohm to 3.3 V, 100 pF at VA
    lbt = t.add("L", "L0402 18nH", "18n", 9.05, 6.0, 270, {"1": "ANT", "2": "VA"}, label=None)                # pad 1 up
    rva = t.add("R", "R0402 10R", "10R", 10.3, 7.5, 0, {"1": "VA", "2": "V33"}, label=None)
    cva = t.add("C", "C0402 100pF", "100p", 10.3, 8.6, 0, {"1": "VA", "2": "GND"}, label=None)
    t.wire("ANT", [(9.05, 4.75), (lbt, "1")], width=0.25)
    t.wire("VA", [(lbt, "2"), (9.05, 7.5), (rva, "1")], width=0.25)
    t.wire("VA", [(9.05, 7.5), (9.05, 8.6), (cva, "1")], width=0.25)
    t.gnd_stub(cva, "2", (10.78, 9.5), sym=(0, 0), width=0.2, fine=True)
    # 3.3 V: the LDO under the chain, its output along y 6.8 to the bias resistor, its own 1 uF and the LNA's 33 nF
    ldo = t.add("U", "TPS7A2033", "3.3V", 13.6, 9.0, 0, {"1": "VS", "2": "GND", "3": "VS", "5": "V33"}, hide_value=False, label=None)
    t.gnd_stub(ldo, "2", (13.6, 9.0), sym=(0, 0))
    t.wire("V33", [(rva, "2"), (11.2, 6.8), (14.7375, 6.8), (ldo, "5")], width=0.25)
    co = t.add("C", "C0402 1uF", "1u", 16.25, 8.3, 270, {"1": "V33", "2": "GND"}, label=None)                 # pad 1 up
    t.wire("V33", [(14.7375, 6.8), (16.25, 6.8), (co, "1")], width=0.25)
    t.wire("V33", [(16.25, 6.8), (17.0, 6.8), (c33, "1")], width=0.2)
    t.gnd_stub(co, "2", (15.55, 8.85), sym=(0, 0), width=0.2, fine=True)
    t.wire("VS", [(ldo, "1"), (11.4, 8.05), (11.4, 9.95), (ldo, "3")], width=0.25)
    ci = t.add("C", "C0402 1uF", "1u", 10.5, 11.1, 0, {"1": "GND", "2": "VS"}, label=None)
    t.wire("VS", [(11.4, 9.95), (11.4, 11.1), (ci, "2")], width=0.25)
    t.gnd_stub(ci, "1", (9.2, 11.1), sym=(0, 0))
    t.wire("VS", [HDR_VS, (8.54, 11.9), (10.98, 11.9), (ci, "2")], width=0.25)
    t.text(5.9, 13.4, "X8", 1.0, 0.18, "left")
    t.titles.append("GNSS PREAMP")
    t.info(["GPS L1"], near=(9.0, 2.0), reach=6.0)
    t.result = ("about 19 dB of gain from 1559 to 1606 MHz (GPS L1, Galileo E1, BeiDou B1, GLONASS L1), 1.5 dB noise figure with the first SAW, "
                "50 dB or more of rejection at 900 MHz and 2.4 GHz; 3.3 V for an active antenna on ANT")
    t.notes = ["SAW - LNA - SAW, the front end of every GNSS receiver.  Murata's SAFFB1G56 passes 1561, 1575 and 1602 MHz with 1.6 dB of",
               "loss; Maxim's MAX2659 gives 20.5 dB with a 0.8 dB noise figure at 4 mA, its output matched and DC-blocked inside, its",
               "input matched by 470 pF and 6.8 nH (the datasheet's values).  The bias-T feeds 3.3 V through 10 ohm and 18 nH to an",
               "active antenna's LNA (10-30 mA).  OUT to X2's RF IN with X3 at 1575.42 MHz: the satellites' codes at the ADCs."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ X7 --
def tile_x7():
    """A switched noise source: the base-emitter junction of an MMBT3904 in avalanche (the base at -5 V, the emitter fed from
    the switched rail VN through 680 ohm, about 8 V across it at 2-3 mA), its noise through 1 nF into an ADL5611 gain block
    (22 dB, the 43 nH choke from VN), then 1 nF and a 20 dB pi pad (62 / 240 / 62 ohm) to the OUT jack.  A TPS22917 load
    switch makes VN from the tile's 5 V when Pmod IO6 is high: off, nothing is biased and OUT is the pad's own 50 ohm at room
    temperature, the cold state of a Y-factor measurement; on, the hot state.  QOD and CT open: the ADL5611's 94 mA empties
    VN within microseconds anyway, and the fastest turn-on (about 100 us)."""
    t = Tile("X7", "noise source", [(2, 1)], supply="+5 V", subtitle="ADL5611", sections=[], kind="rf")
    t.top_pour = True
    t.fine = True
    F = 0.15
    jout = t.jack("BR", "OUT", "OUT", "out", "", silk="OUT")
    power_header(t, rail="+5V")
    # the switch: TPS22917 (rot 0: VIN 1, GND 2, ON 3 down the left; VOUT 6 top-right; CT and QOD open); ON is Pmod IO6
    sw = t.add("U", "TPS22917", "TPS22917", 3.2, 3.0, 0, {"1": "VS", "2": "GND", "3": "/PMOD6", "6": "VN"}, hide_value=False, label=None)
    t.gnd_stub(sw, "2", (3.2, 3.0), sym=(0, 0), width=0.25, fine=True)
    cvs = t.add("C", "C0402 1uF", "1u", 3.2, 0.6, 0, {"1": "VS", "2": "GND"}, label=None)
    t.wire("VS", [(sw, "1"), (2.0625, 1.3), (2.72, 0.6)], width=0.25)
    t.gnd_stub(cvs, "2", (4.6, 0.6), sym=(0, 0), width=0.25, fine=True)
    t.wire("VS", [HDR_VS, (8.54, 15.5)], width=0.25)
    t.wire("VS", [(8.54, 15.5), (8.54, 4.6), (5.9, 1.3), (1.2, 1.3)], width=0.25, layer="B.Cu", silk=False)
    t.wire("VS", [(1.2, 1.3), (2.0625, 1.3)], width=0.25, silk=False)
    # the noise junction: MMBT3904 (rot 0: B 1 top-left, E 2 bottom-left, C 3 right, open); the base on -5 V and its bypasses
    q = t.add("Q", "MMBT3904", "MMBT3904", 6.6, 7.6, 0, {"1": "-5V", "2": "NE"}, hide_value=False, label=None)
    cb1 = t.add("C", "C0402 100pF", "100p", 3.6, 6.65, 0, {"1": "GND", "2": "-5V"}, label=None)
    cb2 = t.add("C", "C0402 100nF", "100n", 3.6, 5.5, 0, {"1": "GND", "2": "-5V"}, label=None)
    t.wire("-5V", [(cb1, "2"), (q, "1")], width=0.25)
    t.wire("-5V", [(cb2, "2"), (4.08, 6.65)], width=0.25)
    t.via("-5V", 1.2, 7.8)
    t.wire("-5V", [(1.2, 7.8), (4.08, 7.8), (4.08, 6.65)], width=0.25)
    t.gnd_stub(cb1, "1", (2.2, 6.65), sym=(0, 0), width=0.25, fine=True)
    t.gnd_stub(cb2, "1", (2.2, 5.5), sym=(0, 0), width=0.25, fine=True)
    re_ = t.add("R", "R0402 680R", "680", 3.0, 10.45, 0, {"1": "VN", "2": "NE"}, label=None)
    cin = t.add("C", "C0402 1nF", "1n", 8.5, 10.45, 0, {"1": "NE", "2": "AIN"}, label=None)
    t.wire("NE", [(q, "2"), (5.662, 10.45), (cin, "1")], width=0.25)
    t.wire("NE", [(re_, "2"), (5.662, 10.45)], width=0.25)
    t.route("VN", [(re_, "1"), (sw, "6")])
    # the gain block (SOT-89, rot 90: IN left and OUT right on y 8.95, the tab up)
    u = t.add("U", "ADL5611", "ADL5611", 12.0, 7.0, 90, {"1": "AIN", "2": "GND", "3": "AOUT"}, hide_value=False, label=None)
    t.wire("AIN", [(cin, "2"), (10.5, 10.45), (u, "1")], width=0.25)
    t.gnd_stub(u, "2", (12.0, 5.6), sym=(0, 0))
    t.gnd_stub(u, "2", (12.0, 6.6), sym=(0, 0))
    l = t.add("L", "L0603 43nH", "43n", 15.5, 7.0, 270, {"1": "VN", "2": "AOUT"}, label=None)                 # pad 1 up
    cout = t.add("C", "C0402 1nF", "1n", 16.6, 9.05, 0, {"1": "AOUT", "2": "PA"}, label=None)
    t.wire("AOUT", [(u, "3"), (13.5, 9.05), (cout, "1")], width=0.25)
    t.wire("AOUT", [(15.5, 9.05), (l, "2")], width=0.25)
    cn1 = t.add("C", "C0402 100pF", "100p", 17.25, 6.213, 0, {"1": "VN", "2": "GND"}, label=None)
    cn2 = t.add("C", "C0402 1uF", "1u", 17.25, 5.1, 0, {"1": "VN", "2": "GND"}, label=None)
    t.wire("VN", [(l, "1"), (cn1, "1")], width=0.25)
    t.wire("VN", [(l, "1"), (15.5, 5.1), (cn2, "1")], width=0.25)
    t.wire("VN", [(sw, "6"), (15.5, 2.05), (15.5, 5.1)], width=0.25)
    t.gnd_stub(cn1, "2", (18.7, 6.213), sym=(0, 0), width=0.25, fine=True)
    t.gnd_stub(cn2, "2", (18.7, 5.1), sym=(0, 0), width=0.25, fine=True)
    # the 20 dB pad (62 / 240 / 62 ohm) and down between the jack's legs
    rs1 = t.add("R", "R0402 62R", "62", 18.6, 9.05, 0, {"1": "PA", "2": "GND"}, label=None)
    rse = t.add("R", "R0402 240R", "240", 17.08, 10.6, 270, {"1": "PA", "2": "OUT"}, label=None)              # pad 1 up
    rs2 = t.add("R", "R0402 62R", "62", 18.6, 11.08, 0, {"1": "OUT", "2": "GND"}, label=None)
    t.wire("PA", [(cout, "2"), (rs1, "1")], width=0.25)
    t.wire("PA", [(17.08, 9.05), (rse, "1")], width=0.25)
    t.wire("OUT", [(rse, "2"), (rs2, "1")], width=0.25)
    t.wire("GND", [(rs1, "2"), (19.3, 9.6)], width=0.25)
    t.gnd_stub(rs2, "2", [(19.3, 10.6), (19.3, 10.07)], sym=(0, 0), width=0.25, fine=True)
    t.wire("GND", [(19.3, 9.6), (19.3, 10.07)], width=0.25)
    t.wire("OUT", [(rse, "2"), (16.4, 11.08), (15.25, 12.23), (jout, "1")], width=0.25)
    t.text(6.2, 12.4, "X7", 1.0, 0.18, "left")
    t.titles.append("NOISE SOURCE")
    t.result = ("IO6 high: a flat noise spectrum from 50 MHz to 4 GHz, roughly 15-30 dB ENR at OUT (measure it); IO6 low: a 50 ohm load "
                "at room temperature; 20 dB of pad keeps OUT matched in both states")
    t.notes = ["Avalanche noise: the MMBT3904's base-emitter junction breaks down near 8 V (6 V minimum), its base on -5 V and its emitter",
               "fed from the switched 5 V through 680 ohm.  The ADL5611 (22 dB, 43 nH choke, ADI's values) lifts it; the 20 dB pad",
               "makes the output 50 ohm whether the amplifier is on or off, so the cold state is a room-temperature termination.",
               "Calibrate the ENR against a 50 ohm load in ice water and in boiling water (273 and 373 K) or in liquid nitrogen (77 K)."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ----------------------------------------------------------------------------------------------------------- X11 --
def tile_x11():
    """The SKY13370 absorptive SPDT (DFN-6 at (13.5, 8.0), rot 270: V1, RFC, V2 down its left side, RF1, GND, RF2 down its
    right).  RFC from the top-left jack, RF2 to the left cell's bottom-right jack, RF1 along y 7.5 to the right cell's.  100 pF
    blocks on every port (the switch wants them); V1 and V2 come from Pmod IO5 and IO8 on the back, 100 pF on each: drive one
    high and the other low.  The throw that is off is terminated in 50 ohm inside the chip."""
    t = Tile("X11", "switch", [(2, 3), (3, 3)], subtitle="SKY13370", sections=[], kind="rf")
    t.top_pour = True
    t.fine = True
    F = 0.15
    jc = t.jack("TL", "RFC", "RFC", "in", "+30 dBm", silk="RFC")
    j2 = t.jack("BR0", "RF2", "RF2", "out", "", silk="RF2")
    j1 = t.jack("BR1", "RF1", "RF1", "out", "", silk="RF1")
    u = t.add("U", "SKY13370", "SKY13370", 13.5, 8.0, 270, {"1": "/PMOD5", "2": "AC", "3": "/PMOD8", "4": "A2", "5": "GND", "6": "A1", "7": "GND"},
              hide_value=False, label=None)
    t.gnd_stub(u, "7", (13.5, 8.0), sym=(0, 0), width=F, fine=True)
    t.wire("GND", [(u, "5"), (13.75, 8.0)], width=F)
    cc = t.add("C", "C0402 100pF", "100p", 9.5, 6.4, 270, {"1": "RFC", "2": "AC"}, label=None)                  # pad 1 up
    t.rf("RFC", [(jc, "1"), (9.5, 4.75), (cc, "1")])
    t.wire("AC", [(cc, "2"), (9.5, 8.0), (u, "2")], width=0.2)
    c1 = t.add("C", "C0402 100pF", "100p", 16.0, 7.5, 0, {"1": "A1", "2": "RF1"}, label=None)
    t.wire("A1", [(u, "6"), (c1, "1")], width=0.2)
    t.rf("RF1", [(c1, "2"), (36.75, 7.5), (j1, "1")])
    c2 = t.add("C", "C0402 100pF", "100p", 15.25, 10.0, 270, {"1": "A2", "2": "RF2"}, label=None)               # pad 1 up
    t.wire("A2", [(u, "4"), (15.25, 8.5), (c2, "1")], width=0.2)
    t.rf("RF2", [(c2, "2"), (j2, "1")])
    # the controls: a fine via beside each pin, down the back to vias at the bottom-left (where the Pmod lines arrive), 100 pF each
    t.wire("/PMOD5", [(u, "1"), (12.35, 7.05)], width=F)
    t.wire("/PMOD8", [(u, "3"), (12.35, 8.95)], width=F)
    t.wire("/PMOD5", [(12.35, 7.05), (11.6, 6.3), (9.4, 6.3), (9.4, 17.4)], layer="B.Cu", silk=False, fine=True)
    t.wire("/PMOD8", [(12.35, 8.95), (10.8, 10.5), (10.8, 17.4)], layer="B.Cu", silk=False, fine=True)
    cv1 = t.add("C", "C0402 100pF", "100p", 8.1, 17.4, 0, {"1": "GND", "2": "/PMOD5"}, label=None)
    cv2 = t.add("C", "C0402 100pF", "100p", 10.8, 16.1, 270, {"1": "GND", "2": "/PMOD8"}, label=None)          # pad 1 up
    t.wire("/PMOD5", [(cv1, "2"), (9.4, 17.4)], width=0.2, silk=False)
    t.wire("/PMOD8", [(cv2, "2"), (10.8, 17.4)], width=0.2, silk=False)
    t.gnd_stub(cv1, "1", (6.8, 17.4), sym=(0, 0), width=0.2, fine=True)
    t.gnd_stub(cv2, "1", (10.1, 15.62), sym=(0, 0), width=0.2, fine=True)
    t.text(1.2, 13.3, "X11", 1.0, 0.18, "left")
    t.text(1.2, 14.6, "RF SWITCH, SPDT", 0.8, 0.15, "left")
    t.info(["SKY13370 0.5-6 GHz", "LOSS 0.7 dB, < +30 dBm"], near=(1.2, 15.9))
    t.text(22.0, 11.0, "IO5: RFC-RF1", 0.8, 0.15, "left")
    t.text(22.0, 12.3, "IO8: RFC-RF2", 0.8, 0.15, "left")
    t.result = "0.7 dB through, 31 dB of isolation at 2.5 GHz (0.5-6 GHz); the off throw is a 50 ohm load; switches in about 100 ns"
    t.notes = ["Skyworks SKY13370: an absorptive SPDT, both throws matched in every state, so a Dicke radiometer's reference (X7 off: a",
               "room-temperature load) and its antenna see the same receiver.  V1 high and V2 low connects RFC to RF1; the reverse to RF2.",
               "Pmod IO5 drives V1 and IO8 V2 from the FPGA, so the switching is synchronous with the ADC's samples.  A T/R switch for",
               "one antenna, an antenna switch for two, a Dicke switch, a pulse gate."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ X3 --
def tile_x3():
    """The synthesizer: RF-MOD's MAX2871 tile (R10) with its own REF IN, moved to the right cell's bottom corner so the
    modulator above can use all four of its corners.  It carries the Pmod plug; the switch's two lines (IO5, IO8), the noise
    source's (IO6) and the modulator's output disable (IO7) leave its other pads along the bottom margin."""
    t = rf_mod.synth_tile("X3", [(0, 3), (1, 3)], host=True, share_ref=False, ref_slot="BR1",
                          pmod_extra={"11": "/PMOD5", "9": "/PMOD6", "5": "/PMOD8"})
    t.result = ("any frequency from 23.5 MHz to 6 GHz on OUT A (-4 to +5 dBm), locked to the 25 MHz on REF IN (the ECP5 board's CLK OUT "
                "or RF-MOD's REF OUT); through X5 it is the LO of X1 and X2 at once")
    t.notes = t.notes[:-1] + ["tied high, LE has 100 k down.  REF IN is unterminated (3.3 V CMOS from the ECP5 board's CLK OUT or RF-MOD's REF OUT).",
                              "Split OUT A with X5 to drive X1's and X2's LO inputs (-1 dBm each at the top power setting)."]
    return t


# ------------------------------------------------------------------------------------------------------------ X4 --
def tile_x4():
    """RF-MOD's QPL9547 LNA tile, unchanged."""
    return rf_mod.qpl_tile("X4", (2, 0))


# ------------------------------------------------------------------------------------------------------------ X5 --
def tile_x5():
    """RF-MOD's resistive splitter with its jacks on the checkerboard: P1 top-left, P2 the left cell's bottom-right, P3 the
    right cell's bottom-right.  Three 18 ohm resistors to one node: 6 dB from any port to any other, DC to 6 GHz.  Its job
    here is X3's OUT A into the LO of X1 and of X2, one phase for both."""
    t = Tile("X5", "splitter", [(0, 1), (1, 1)], subtitle="3 x 18 ohm, 6 dB", sections=[], kind="rf")
    t.top_pour = True
    j1 = t.jack("TL", "P1", "P1", "in", "+20 dBm", silk="P1")
    j2 = t.jack("BR0", "P2", "P2", "out", "", silk="P2")
    j3 = t.jack("BR1", "P3", "P3", "out", "", silk="P3")
    r1 = t.add("R", "R0402 18R", "18R", 15.0, 9.0, 0, {"1": "P1", "2": "N"}, label=None)
    r2 = t.add("R", "R0402 18R", "18R", 17.0, 9.0, 0, {"1": "N", "2": "P3"}, label=None)
    r3 = t.add("R", "R0402 18R", "18R", 16.0, 10.6, 270, {"1": "N", "2": "P2"}, label=None)            # pad 1 up
    t.rf("P1", [(j1, "1"), (4.75, 9.0), (r1, "1")])
    t.rf("P3", [(r2, "2"), (36.75, 9.0), (j3, "1")])
    t.rf("P2", [(r3, "2"), (16.0, 14.5), (j2, "1")])
    t.wire("N", [(r1, "2"), (r2, "1")], width=0.25)
    t.wire("N", [(16.0, 9.0), (r3, "1")], width=0.25)
    t.text(1.2, 13.3, "X5", 1.0, 0.18, "left")
    t.text(1.2, 14.6, "SPLITTER", 0.8, 0.15, "left")
    t.text(1.2, 15.9, "3 x 18R", 0.8, 0.15, "left")
    t.text(1.2, 17.2, "-6 dB", 0.8, 0.15, "left")
    t.text(1.2, 18.5, "DC-6 GHz", 0.8, 0.15, "left")
    t.result = "6.2 dB from any port to either other port, every port within 2 ohm of 50, DC to 6 GHz"
    t.notes = ["RF-MOD's R1: three 18 ohm resistors to one node, 6 dB per path, no isolation between the outputs beyond those 6 dB.",
               "Here it splits X3's OUT A into X1's and X2's LO inputs, so the transmitter and the receiver share one oscillator:",
               "the radar's and the network analyzer's phase reference.  Any two tiles can share a source through it."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ----------------------------------------------------------------------------------------------------------- X10 --
def tile_x10():
    """Power: AMOD-A's A1 without its 3.3 V regulator and rails socket.  USB-C on the right edge (5.1 k CC pull-downs), a
    2 A PTC, a 5 V TVS, 2 x 10 uF; the LM2664 inverts +5 to -5 V (40 mA) for the demodulator's difference amplifiers and the
    noise source's junction.  +5 V leaves through a via into the pour that covers L3; -5 V through vias into the island
    under this tile's bottom half and the gutter strip below row 1.  A green LED on +5 V, a red one on -5 V."""
    t = Tile("X10", "power", [(3, 1)], subtitle="USB-C 5 V in: +5, -5 out", sections=[])
    t.pwr_flags = ["+5V"]
    ux = USB_X - t.x0
    j = t.add("J", "USBC", "USB-C", ux, 10.0, 90, {"A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS", "A5": "CC1", "B5": "CC2",
                                                   "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "SH": "GND"}, hide_value=True)
    t.wire("GND", [(j, "A1"), (ux - 3.13, 14.32)])
    t.wire("GND", [(j, "B1"), (ux - 3.13, 5.68)])
    rc1 = t.add("R", "R0805 5.1k", "5.1k", 17.6, 11.5, 0, {"1": "GND", "2": "CC1"}, label=None)
    rc2 = t.add("R", "R0805 5.1k", "5.1k", 17.6, 9.3, 0, {"1": "GND", "2": "CC2"}, label=None)
    t.wire("CC1", [(j, "A5"), (19.3, 11.25), (19.3, 11.5), (rc1, "2")], width=0.25)
    t.wire("CC2", [(j, "B5"), (19.3, 8.25), (19.3, 9.3), (rc2, "2")], width=0.25)
    t.gnd_stub(rc1, "1", (16.688, 10.4), sym=(0, 0))
    t.gnd_stub(rc2, "1", (15.9, 9.3), sym=(0, 0))
    t.wire("VBUS", [(j, "B9"), (19.9, 12.45)], width=0.25)
    t.wire("VBUS", [(j, "A9"), (19.9, 7.55)], width=0.25)
    t.wire("VBUS", [(19.9, 12.45), (19.9, 7.55)], layer="B.Cu")
    f = t.add("F", "PTC2A", "2A", 15.5, 6.2, 0, {"1": "+5V", "2": "VBUS"}, label=None)
    t.wire("VBUS", [(19.9, 7.55), (19.9, 6.2), (f, "2")])
    d = t.add("D", "TVS5V", "SMAJ5.0A", 10.6, 7.6, 270, {"1": "+5V", "2": "GND"}, label=None)
    c1 = t.add("C", "C0805 10uF", "10u", 7.0, 6.2, 180, {"1": "+5V", "2": "GND"}, label=None)
    c2 = t.add("C", "C0805 10uF", "10u", 7.0, 8.8, 180, {"1": "+5V", "2": "GND"}, label=None)
    t.wire("+5V", [(f, "1"), (c1, "1")])
    t.via("+5V", 9.1, 6.2)
    t.wire("+5V", [(c1, "1"), (c2, "1")])
    t.gnd_stub(d, "2", (10.6, 11.3), sym=(0, 0))
    t.gnd_stub(c1, "2", (6.05, 4.7), sym=(0, 0))
    t.gnd_stub(c2, "2", (5.0, 8.8), sym=(0, 0))
    # -5 V: the LM2664 with its flying and output capacitors; the output into the -5 V island under the tile's bottom half
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
    t.via("-5V", 1.1, 13.65)
    t.wire("-5V", [(co, "1"), (1.1, 13.65)])
    # the LEDs along the bottom: red on -5 V, green on +5 V, 1 k each to ground
    dr = t.add("LED", "LED_R", "-5V", 11.4, 15.4, 0, {"1": "-5V", "2": "LEDR"}, label=None)        # rot 0: K (pad 1) at -x
    rr = t.add("R", "R0805 1k", "1k", 15.0, 15.4, 0, {"1": "LEDR", "2": "GND"}, label=None)
    t.via("-5V", 9.3, 15.4)
    t.wire("-5V", [(dr, "1"), (9.3, 15.4)], silk=False)
    t.wire("LEDR", [(dr, "2"), (rr, "1")])
    t.gnd_stub(rr, "2", (16.9, 15.4), sym=(0, 0))
    dg = t.add("LED", "LED_G", "+5V", 24.6, 2.6, 90, {"1": "LEDG", "2": "+5V"}, label=None)          # rot 90: A (pad 2) at the top
    rg = t.add("R", "R0805 1k", "1k", 26.6, 2.6, 90, {"1": "LEDG", "2": "GND"}, label=None)
    t.via("+5V", 24.6, 0.6)
    t.wire("+5V", [(dg, "2"), (24.6, 0.6)], silk=False)
    t.wire("LEDG", [(dg, "1"), (rg, "1")])
    t.gnd_stub(rg, "2", (26.6, 0.6), sym=(0, 0))
    t.text(17.4, 1.9, "X10", 1.2, 0.2, "center")
    t.text(18.7, 18.6, "POWER", 0.9, 0.17, "right")
    t.result = "+5 V from the USB-C (up to 1.5 A), -5 V at 40 mA; the green LED says 5 V is in, the red one that -5 V is up"
    t.notes = ["USB-C power only: 5.1 k on each CC asks any source for 5 V.  A 2 A PTC, a 5 V TVS (clamps at 9.2 V) and 20 uF.",
               "The LM2664 charge pump makes -5 V for X2's difference amplifiers and X7's noise junction (40 mA available, 25 used).",
               "Every powered tile switches its own +5 V with a slide switch and a P-FET, and regulates its own 3.3 V where it needs one."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


def tiles():
    return [tile_x9(), tile_x6(), tile_x4(), tile_x8(), tile_x5(), tile_x7(), tile_x10(), tile_x1(), tile_x2(), tile_x3(), tile_x11()]


PMOD_HOST = "X3's bottom edge"
PMOD_NAMES = {"/PMOD1": "MUXOUT of X3", "/PMOD2": "SDATA to X3", "/PMOD3": "SCLK to X3", "/PMOD4": "LE of X3",
              "/PMOD5": "V1 of X11 (RF1 on)", "/PMOD6": "X7's noise on", "/PMOD8": "V2 of X11 (RF2 on)"}
HANDBOOK_INTRO = [
    "Eleven tiles on sixteen 20 mm cells, four layers, USB-C power on X10.  The board is built for the ECP5-2ADC-2DAC board: its two",
    "DACs drive X1's I and Q, its two ADCs read X2's I and Q, and X3 split by X5 is the LO of both, so transmitter and receiver share",
    "one phase.  Every 50 ohm line is coplanar waveguide with a via fence; every jack's centre pin has no plane under it."]
HANDBOOK_SECTIONS = [
    ["## The tiles together", "",
     "X3 (the MAX2871, locked to the 25 MHz on its REF IN: the ECP5 board's CLK OUT) split by X5 is the LO of both X1 and X2, so the",
     "transmitter and the receiver share one phase.  The ECP5 board's DACs are X1's I and Q, its ADCs read X2's I and Q: a complete",
     "coherent I/Q transceiver from 0.4 to 6 GHz whose baseband is the ECP5 board's 30 MHz.",
     "",
     "1. **A radio link, any modulation.**  DAC 1 and DAC 2 into X1's I IN and Q IN, X1's RF OUT on a cable (or an antenna) into X4",
     "   (the LNA) and X2's RF IN, X2's I OUT and Q OUT into the ADCs: QPSK, 16-QAM, OFDM, FSK, chirps, with the constellation",
     "   on the screen and the carrier, timing and equalisation in gateware.  X11 switches one antenna between transmit and receive.",
     "2. **A vector network analyzer.**  X1 makes a tone (a DC on I), the device under test sits between X1 and X2, and X2's I and",
     "   Q are its transmission, magnitude and phase, at every frequency X3 steps to: filters, cables, the board's own LNA.",
     "3. **Radar.**  X3 stepped (or X1 chirped), X1's RF OUT to one antenna, X2's RF IN on another: a stepped-frequency or FMCW",
     "   radar whose range bins are an FFT of X2's samples, and whose phase gives millimetre motion (breathing, a pendulum).",
     "4. **Diamond NV centres (ODMR).**  X3 near 2.87 GHz through X1 (the DACs make the sweep and the modulation) and an amplifier",
     "   into X9's loop under a diamond plate; green light from AMOD-2's Y10 (pulsed with IO5) and a photodiode on an ADC: the",
     "   resonance dip, its Zeeman splitting under a magnet (a magnetometer), Rabi oscillations, a Ramsey sequence.",
     "5. **GNSS.**  An active antenna on X8 (bias on its centre pin, the MAX2659 and two SAW filters), X2's LO at 1575.42 MHz minus",
     "   a few MHz, I and Q into the ADCs: GPS L1 C/A acquisition by correlation, Doppler and code phase, then a position fix.",
     "6. **Power and noise.**  X6 (the AD8318, 25 mV per dB) is a power meter from 1 MHz to 8 GHz on an ADC (antenna patterns, a",
     "   filter's sweep); X7 (IO6) is a switched noise source for the Y-factor noise figure of X4 or the whole receiver, and with X11",
     "   switching between an antenna and a load, a Dicke radiometer (the Sun at 2.4 GHz).",
     "",
     "Levels to remember: X3 gives -4 to +5 dBm and X5 loses 6 dB to each output; X1 wants 0 dBm of LO and gives about 0 dBm at",
     "full scale; X2's amplified I and Q reach the ADCs' full scale near -10 dBm of RF (measure it) and it wants -6 to +6 dBm of LO; X4 gives 19 dB (no more",
     "than +20 dBm in); X6 reads -60 to 0 dBm; X9 is a through line rated for 1 W from an external amplifier."],
]

GND_LOOPS = [(3.0, 30.0), (3.0, 70.0), (97.0, 70.0)]
HOLES = []
FEET = [(5.0, 5.0), (95.0, 5.0), (95.0, 95.0), (5.0, 85.0)]
SLOTS = []
_X3, _X10 = G.cell_origin(0, 3), G.cell_origin(3, 1)


def _island(c0):
    x0, y0 = G.cell_origin(c0, 3)
    return (x0 + 9.0, y0 + 2.0, x0 + 31.5, y0 + 18.4)


RAIL_POURS = [("+5V", 0.6, 0.6, 99.4, 99.4, 0),
              ("-5V", [(51.15, 29.25 + 7.0), (52.75, 29.25 + 7.0), (52.75, 49.35), (_X10[0] + 0.4, 49.35), (_X10[0] + 0.4, _X10[1] + 12.6),
                       (_X10[0] + 19.6, _X10[1] + 12.6), (_X10[0] + 19.6, 50.65), (51.0, 50.65), (51.0, 49.35), (51.15, 49.35)], 1),
              ("/X3_V33", *_island(0), 2),
              ("/X1_VS", G.cell_origin(0, 2)[0] + 9.0, G.cell_origin(0, 2)[1] + 1.0, G.cell_origin(0, 2)[0] + 33.0, G.cell_origin(0, 2)[1] + 19.0, 2),
              ("/X2_VS", G.cell_origin(2, 2)[0] + 9.0, G.cell_origin(2, 2)[1] + 1.0, G.cell_origin(2, 2)[0] + 33.0, G.cell_origin(2, 2)[1] + 19.0, 2)]
_X7, _X11 = G.cell_origin(2, 1), G.cell_origin(2, 3)
_PM = (_X3[0] + 2.97, _X3[1] + 24.25)                       # the Pmod plug's centre: pad columns at -6.35 .. 6.35, rows at +-1.27


def _pad(k):
    """Board position of the plug's pad k (odd pads on the row nearer the edge)."""
    col = (k - 1) // 2
    return (round(_PM[0] - 6.35 + 2.54 * col, 3), round(_PM[1] + (1.27 if k % 2 else -1.27), 3))


# IO6 (pad 9) up between pads 10 and 12, along the margin under X3 and up the gutter between columns 1 and 2 to X7's ON pin;
# IO5 (pad 11) up right of pad 12, along the margin to X11's via; IO8 (pad 5) on the back along the bottom edge to X11's other via
FRONT_WIRES = [("/PMOD6", [_pad(9), (_pad(9)[0] + 1.27, _PM[1]), (_pad(9)[0] + 1.27, 93.05), (50.0, 93.05), (50.0, _X7[1] + 3.95), (_X7[0] + 2.0625, _X7[1] + 3.95)]),
               ("/PMOD5", [_pad(11), (_pad(11)[0] + 1.28, _PM[1]), (_pad(11)[0] + 1.28, 93.55), (_X11[0] + 9.4, 93.55), (_X11[0] + 9.4, _X11[1] + 17.4)])]
BACK_WIRES = [("/PMOD8", [_pad(5), (_pad(5)[0], 99.15), (_X11[0] + 10.8, 99.15), (_X11[0] + 10.8, _X11[1] + 17.4)])]
FRONT_TEXT = []
BACK_TEXT_X = 50.0
QR_AT = (80.0, 33.5)
BACK_TEXT = ["RF-MOD-2: X1 and X2 put the ECP5 board's DACs and ADCs",
             "at RF; X3 split by X5 is the LO of both.  Jacks at each",
             "cell's top-left and bottom-right; powered tiles have a",
             "slide switch (up: on).  USB-C on X10.  See the handbook."]


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
