"""Every tile's bring-up tests, for the nine boards.  The words are engine.py's.

Each board has: its facts (BOARDS), what to set on it once (its DIP switches and jumpers as the bring-up
wants them), what each tile should draw when its slide switch goes on (the power walk), and its tests.
The models are worked from the tiles' netlists (out/<board>_tiles.json), so a number here is the
design's prediction for the parts on the board; where the first board says otherwise, change the
number here and write the reason in bringup/REVB.md.

A jack is named by its key in the tile table (IN, OUT, ...); the cards print the name on the silkscreen.
"""
import math

import numpy as np

from engine import (P, Lin, Time, ladder, amp, flat, table, zload, bode, wave, listen, dc, s21, spec, manual, seq,
                    G, Gabs, Corner, PeakF, PeakFabs, PeakG, NotchF, W, Wm, Delay, Num, SpecPeak, SpecPeakF, Check, TWO_PI)

R, L, C, ser, par = P.R, P.L, P.C, P.series_arm, P.parallel_arm


def H(method, *args, key=None, **kwargs):
    """A call on the Pmod host (gateware/pmodbench/host/pmodbench.py); key names its result in the test's values."""
    return (key, method, args, kwargs)


def dbm_vpp(dbm):
    """Peak-to-peak volts into 50 ohm for a sine of `dbm`."""
    return 2 * math.sqrt(2) * math.sqrt(50 * 1e-3 * 10 ** (dbm / 10.0))


def const(v):
    return Time(lambda t, emf, ctx: np.full(np.shape(t), float(v)))


def butter(n, fc, gain=1.0):
    return Lin(lambda f, load: gain / np.sqrt(1 + (f / fc) ** (2 * n)) + 0j)


QUIET = [W("mean", -0.3, 0.3), W("rms", 0, 0.15)]

BOARDS = {}
TESTS = {}


def board(stem, **kw):
    BOARDS[stem] = dict(stem=stem, **kw)
    TESTS[stem] = []
    return TESTS[stem]


# =====================================================================================================
# AMOD-P: thirteen passive tiles, two layers, no power
# =====================================================================================================
T = board("amod_p", letter="p", name="AMOD-P", title="passive blocks", power=None, pmod=None,
          setup=["p4 DIP (2 ways): both OFF", "p12 DIP (4 ways): all OFF", "p13 DIP (4 ways): all OFF"],
          inspect=["The four DIP switches' ON marks are toward the top edge (p4, p12, p13).",
                   "p8's crystal and p9's resonator stand at 45 degrees, flat on the board, both leads soldered.",
                   "p11: twenty 0603 inductors in two rows, no tombstones (a lifted end opens the whole line).",
                   "p12: four LEDs, their cathode marks all the same way.",
                   "p13: the two screw terminals' wire openings face the bottom edge."])

T += [bode("p1", "IN", "OUT", (1e3, 3e7, 13), 2.0, ladder([("p", R(61.9)), ("s", R(249)), ("p", R(61.9))]),
           [G(1e4, 0.7), G(1e6, 0.7), G(1e7, 1.0), G(3e7, 2.0)], load="50", why="61.9 / 249 / 61.9 ohm: -20.0 dB")]
T += [bode("p2", "IN", "OUT", (1e3, 5e6, 21), 1.0, ladder([("s", R(1e3)), ("p", C(1e-9))]),
           [G(1e3, 0.7), Corner(0.12)], why="1 k and 1 nF with the cable's capacitance across it")]
T += [bode("p3", "IN", "OUT", (1e3, 5e6, 21), 1.0, ladder([("s", C(1e-9)), ("p", R(1e3))]),
           [G(2e6, 1.0), Corner(0.12, side="lo", ref="hf")])]


def _p4(cadd):
    return ladder([("s", ser(L(100e-6, 10.0), C(220e-12 + cadd)))])


T += [bode("p4", "IN", "OUT", (3e5, 3e6, 41), 0.5, _p4(0), [PeakF(0.06), PeakG(2.5)], load="50", refine=1,
           why="100 uH and 220 pF: 1.07 MHz, Q about 6")]
for ways, cadd, txt in (("1", 47e-12, "way 1 ON, way 2 OFF"), ("2", 100e-12, "way 1 OFF, way 2 ON"), ("1+2", 147e-12, "both ON")):
    T += [bode("p4", "IN", "OUT", (3e5, 3e6, 41), 0.5, _p4(cadd), [PeakF(0.06)], load="50", refine=1, name="DIP " + ways,
               pre=("p4 DIP: " + txt,), hands=True)]
T += [bode("p5", "IN", "OUT", (1e5, 3e7, 31), 1.0,
           ladder([("p", C(220e-12)), ("s", L(1.5e-6)), ("p", C(680e-12)), ("s", L(1.5e-6)), ("p", C(220e-12))]),
           [G(1e6, 1.0), Corner(0.12), Gabs(1.8e7, -70, -22)], load="50", why="5th-order Butterworth, 8.9 MHz")]
T += [bode("p6", "IN", "OUT", (1e3, 2e6, 31), 1.0, ladder([("p", C(20e-9)), ("s", L(150e-6, 2.0)), ("p", C(20e-9))]),
           [G(1e4, 1.0), Corner(0.15), Gabs(1e6, -95, -25)], load="50", why="2 x 10 nF, 150 uH, 2 x 10 nF")]
T += [bode("p7", "IN", "OUT", (1e6, 3e7, 45), 1.0,
           ladder([("s", ser(L(2.7e-6), C(270e-12))), ("p", par(L(330e-9), C(2.2e-9))), ("s", ser(L(2.7e-6), C(270e-12)))]),
           [G(6.0e6, 1.5), Corner(0.10, side="hi", ref="max"), Corner(0.10, side="lo", ref="max"), Gabs(2e7, -70, -15)], load="50")]
_SPLIT = Check("notch above the peak", lambda r: r.notch()[0] - r.peak()[0], "Hz", lo=1.5e3, hi=1.5e4)
T += [bode("p8", "IN", "OUT", list(np.linspace(3.994e6, 4.012e6, 73)), 0.2, ladder([("s", P.crystal(3.9992e6, 15e-15, 50000, 4e-12))]),
           [PeakFabs(3.9970e6, 4.0006e6), Check("peak gain", lambda r: r.peak()[1], "dB", lo=-12, hi=-1), _SPLIT], load="50", refine=2,
           why="series resonance a little under 4.000 MHz, the parallel one a few kHz above")]
T += [bode("p9", "IN", "OUT", list(np.linspace(430e3, 480e3, 51)), 0.2, ladder([("s", P.crystal(452e3, 7e-12, 400, 250e-12))]),
           [PeakFabs(440e3, 462e3), Check("peak gain", lambda r: r.peak()[1], "dB", lo=-10, hi=-0.3),
            Check("notch above the peak", lambda r: r.notch()[0] - r.peak()[0], "Hz", lo=2e3, hi=2.5e4)], load="50", refine=1)]


def _clip(t, emf, ctx):
    v = np.clip(emf, -0.6, 0.6)
    for _ in range(40):                                   # (emf - v) / 1050 = Is (exp(v / nVt) - exp(-v / nVt))
        fv = (emf - v) / 1050.0 - 2 * 2.5e-9 * np.sinh(v / 0.0494)
        dv = -1 / 1050.0 - 2 * 2.5e-9 / 0.0494 * np.cosh(v / 0.0494)
        v = v - np.clip(fv / dv, -0.05, 0.05)
    return v


T += [wave("p10", "IN", "sine", 1e3, 3.0, "OUT", Time(_clip), [W("vmax", 0.45, 0.80), W("vmin", -0.80, -0.45)], name="clipping",
           why="+-3 V in, a diode drop out"),
      wave("p10", "IN", "sine", 1e3, 0.1, "OUT", Time(_clip), [W("vpp", 0.17, 0.21)], name="small signal")]
_LINE = [e for _ in range(20) for e in (("s", L(1.0e-6, 0.15)), ("p", C(390e-12)))]
_TAPS = {"t100": ("100ns", "1M"), "t200": ("200ns", "1M"), "t300": ("300ns", "1M"), "out": ("OUT", "50")}
_TAPM = {"t100": ladder(_LINE, tap=10, tap_r=470), "t200": ladder(_LINE, tap=20, tap_r=470), "t300": ladder(_LINE, tap=30, tap_r=470),
         "out": ladder(_LINE)}
T += [wave("p11", "IN", "square", 250e3, 1.0, _TAPS, _TAPM,
           [Delay("t100", "t200", 12e-9), Delay("t200", "t300", 12e-9), Delay("t100", "out", 20e-9), Wm("vpp", "out", frac=0.25),
            Wm("vpp", "t100", frac=0.3)], name="delays", cycles=3, why="20 ns a section: 99 ns between taps"),
      bode("p11", "IN", {"out": ("OUT", "50")}, (1e5, 2.5e7, 31), 1.0, {"out": ladder(_LINE)}, [G(1e6, 1.0, "out"), Corner(0.15, role="out")],
           name="through", why="flat to the 16 MHz cut-off")]


def _led(vk, rd=8.0):
    def fn(t, emf, ctx):
        i = np.maximum(0.0, (emf - vk) / (150.0 + rd))
        return emf - 50.0 * i
    return Time(fn)


def _led_derive(v):
    vin = v["vin@2.5"]; i = (5.0 - vin) / 50.0
    return {"mA at 5 V": 1e3 * i, "LED volts": vin - 100.0 * i}


for way, colour, vk, lo, hi in ((1, "red", 1.85, 1.6, 2.3), (2, "yellow", 1.95, 1.7, 2.4), (3, "green", 2.7, 2.3, 3.5), (4, "blue", 2.8, 2.4, 3.6)):
    T += [dc("p12", "IN", [0.5, 1.5, 2.5], {"vin": ("IN", "1M")}, {"vin": _led(vk)},
             [Num("LED volts", lo, hi, "V"), Num("mA at 5 V", 8, 25, "mA")], name="way %d (%s)" % (way, colour), derive=_led_derive, hands=True,
             pre=("a BNC tee on the scope's CH1 input: generator CH1 to one side of the tee with a BNC cable, cable S1 from the other side to p12 IN "
                  "(the two hookup lines above share that one cable; G1 itself is not used)",
                  "p12 DIP: only way %d ON; tell me which colour lights" % way))]
T += [manual("p13", "loopstick", "With a 330 uH ferrite-rod coil on the COIL terminal (HOT, TAP, GND as printed) and a 5-turn wire loop "
             "on the generator held near the rod, I sweep 0.3-2 MHz and read OUT: one peak per DIP way (1.28, 0.88, 0.59, 0.40 MHz).",
             kit=("330 uH AM loopstick coil (KIT.md)", "a 5-turn loop of hookup wire on a BNC clip lead"))]

# =====================================================================================================
# AMOD-A: twelve active tiles on USB-C power
# =====================================================================================================
T = board("amod_a", letter="a", name="AMOD-A", title="active blocks", power="a1", socket=True, pmod="a11", quiescent=(0.004, 0.030),
          setup=["a10 DIP (4 ways): only way 2 (470 ohm) ON", "every tile's slide switch DOWN (off)"],
          walk=[("a2", 5, 14), ("a3", 5, 14), ("a4", 25, 50), ("a5", 5, 14), ("a6", 2, 8), ("a7", 0.2, 6), ("a8", 0, 1.5),
                ("a9", 4, 14), ("a10", 10, 28), ("a11", 5, 16), ("a12", 8, 28)],
          inspect=["a1: USB-C shell soldered on all four posts; the 5.1 k CC resistors present; D101 (SMAJ5.0A) by the fuse.",
                   "Every SOT-23 P-FET beside a slide switch has its single pin toward the tile's inside (pin 1 at the dot).",
                   "a4: U401 (OPA847, SOT-23-6) pin 1 dot at the silkscreen dot.",
                   "a7: U701 (TSSOP-16) pin 1; a9: U901 (SOIC-14) pin 1; a11: U1101 (WSON-8) pin 1.",
                   "a12: U1201 is an MSOP-8 sitting squarely on its pads (rev A's first order had a SOIC-8 footprint here).",
                   "a8: the two 2512 heater resistors, flat.  a12: the screw terminal's openings face the right edge.",
                   "The Pmod plug hangs off the bottom edge under a11; its pins straight."])
# The OPA810's gain-bandwidth product is 70 MHz (its 140 MHz is the bandwidth at gain 1), so these two corners are half the silk's (REVB.md 1.3).
_GBW810 = 70e6
T += [bode("a2", "IN", "OUT", (1e3, 3e7, 21), 0.1, amp(1 + 10e3 / 1.1e3, _GBW810 / 10.09), [G(1e4, 0.6), G(1e6, 0.8), Corner(0.4)],
           why="1 + 10 k / 1.1 k = 10.1; corner 70 MHz / 10.1 = 6.9 MHz (the silk says 14 MHz)"),
      bode("a3", "IN", "OUT", (1e3, 1e7, 21), 0.01, amp(101, _GBW810 / 101), [G(1e4, 0.8), Corner(0.4)],
           why="1 + 10 k / 100 = 101; corner 70 MHz / 101 = 0.69 MHz (the silk says 1.4 MHz)"),
      bode("a4", "IN", "OUT", (1e4, 3e7, 21), 0.01, amp(101, 39e6), [G(1e5, 1.0), G(1e7, 2.0), Gabs(3e7, 34, 42)], why="OPA847, 1 k / 10 ohm"),
      listen("a5", "OUT", const(0.02), QUIET, why="x101 of the op amp's offset with no HB100"),
      manual("a5", "HB100", "With an HB100 on the +5 / G / IF socket (read the module's own print: its pin order varies) I record OUT "
             "while you wave a hand a metre in front of it: tens of hertz, tens of millivolts.", kit=("HB100 Doppler module, three jumper wires",))]
for f0 in (80e3, 100e3, 130e3):
    T += [wave("a7", "IN", "square", f0, 1.0, "OUT",
               Time(lambda t, emf, ctx, f0=f0: 2.5 + 2.5 * np.sign(np.sin(TWO_PI * f0 * t - 1.0))),
               [Wm("freq", frac=0.004, unit="Hz"), W("vpp", 3.5, 5.6)], name="lock at %g kHz" % (f0 / 1e3), cycles=40,
               why="the VCO follows the input: 74HC4046A, R1 10 k, C1 1 nF")]
T += [listen("a8", "OUT", const(0.74), [W("mean", 0.69, 0.80)], name="temperature at rest", why="TMP235: 500 mV + 10 mV per degree C")]


def _mix(t, emf, ctx):
    rf, lo = emf["rf"] / 2.0, emf["lo"] / 2.0
    return 0.42 * rf * np.tanh(lo / 0.052) + 0.01 * lo


T += [wave("a9", {"rf": "RF", "lo": "LO"}, None, None, None, {"if": ("IF", "1M")}, {"if": Time(_mix)},
           [W("tone", 0.012, 0.09, arg=100e3), W("tone", 0.0, 0.05, arg=1.1e6)], name="product", span=1e-4,
           stim={"rf": ("sine", 1.0e6, 0.2, 0.0), "lo": ("sine", 1.1e6, 0.4, 0.0)},
           why="1.0 MHz x 1.1 MHz: the difference at 100 kHz, and the LO's leak at 1.1 MHz")]
_A10 = amp(2.0, 35e6)
T += [bode("a10", "DRIVE", {"s": ("S", "50"), "x": ("X", "50")}, (1e3, 1e7, 13), 0.5, {"s": _A10, "x": _A10},
           [G(1e4, 0.6, "s"), G(1e4, 0.6, "x"), Check("X - S at 10 kHz", lambda r: r.gain(1e4, "x") - r.gain(1e4, "s"), "dB", lo=-0.3, hi=0.3)],
           name="DUT open", why="no current in R: X = S"),
      bode("a10", "DRIVE", {"s": ("S", "50"), "x": ("X", "50")}, (1e3, 1e6, 7), 0.5, {"s": _A10, "x": amp(2.0 * 50 / 520.0, 35e6)},
           [Check("X - S at 10 kHz", lambda r: r.gain(1e4, "x") - r.gain(1e4, "s"), "dB", lo=-21.3, hi=-19.3)], name="DUT 50 ohm", hands=True,
           pre=("a 50 ohm SMA terminator on a10's DUT jack",), why="50 / (470 + 50)"),
      listen("a11", "OUT", const(0.02), QUIET), listen("a12", "OUT", const(0.02), [W("mean", -0.5, 0.5), W("rms", 0, 0.3)])]
T += [seq("a6", "ones density against IN", [dict(host=[H("use", "amod_a"), H("dsm_loop", 1e6)])] +
          [dict(gen={"in": ("dc", 0, 0, v)}, wait=0.3, read={"density@%g" % (2 * v): ("host", "density", "IO7")}) for v in (0.25, 0.825, 1.4)] +
          [dict(host=[H("safe")])],
          lambda ctx: {"density@0.5": 0.5 / 3.3, "density@1.65": 0.5, "density@2.8": 2.8 / 3.3},
          [Num("density@0.5", tol=0.05), Num("density@1.65", tol=0.05), Num("density@2.8", tol=0.05)], gens={"in": "IN"},
          why="first-order delta-sigma closed through the FPGA: density = IN / 3.3 V"),
      seq("a8", "heater", [dict(host=[H("use", "amod_a"), H("out", "IO6", 0)], wait=1, read={"i0": "psu", "t0": ("scope", "out", "mean")}),
                            dict(host=[H("out", "IO6", 1)], wait=20, read={"i1": "psu", "t1": ("scope", "out", "mean")}),
                            dict(host=[H("out", "IO6", 0), H("safe")])],
          lambda ctx: {"i0": 0.06, "i1": 0.23, "t0": 0.74, "t1": 0.80}, [Num("heater current", 0.12, 0.21, "A"), Num("temperature rise", 0.008, 0.6, "V")],
          scopes={"out": ("OUT", "1M")}, derive=lambda v: {"heater current": v["i1"] - v["i0"], "temperature rise": v["t1"] - v["t0"]}, psu=True,
          why="30 ohm on the switched 5 V: 170 mA, 0.83 W; 10 mV per kelvin"),
      seq("a11", "bridge into the receiver", [dict(host=[H("use", "amod_a"), H("antiphase", "IO4", "IO3", 40e3)],
                                               wait=0.2, read={"freq": ("scope", "out", "freq"), "vpp": ("scope", "out", "vpp")}),
                                          dict(host=[H("safe")])],
          lambda ctx: {"freq": 40e3, "vpp": 7.5}, [Num("freq", 39.5e3, 40.5e3, "Hz"), Num("vpp", 2.0, 9.5, "V")], scopes={"out": ("OUT", "1M")},
          pre=("a male-male jumper wire from a11's TX socket pin 1 to its RX socket pin 1 (the left pin of each, as printed TX and RX)",),
          why="5 V squares through 10 nF into x100: RX OUT clips at the rails at 40 kHz"),
      manual("a12", "speaker and microphone", "Speaker on SPK, electret in MIC (its + pin to pin 1): I play 1 kHz into SPEAKER IN (you hear it), then a "
             "one-bit tone from IO2, then record MIC OUT while you clap.", kit=("4-8 ohm speaker, 2 W", "electret capsule"))]

# =====================================================================================================
# AMOD-C: conversion (regulators, switched capacitors, converters, transistor blocks)
# =====================================================================================================
T = board("amod_c", letter="c", name="AMOD-C", title="conversion", power="c1", socket=True, pmod="c9", quiescent=(0.004, 0.030),
          setup=["c10: no jumper on the CE header (parked on one pin, or off)", "every tile's slide switch DOWN (off)"],
          walk=[("c2", 1, 12), ("c3", 0.1, 5), ("c4", 1, 8), ("c5", 5, 14), ("c6", 8, 30), ("c7", 3, 16), ("c8", 0.02, 3), ("c9", 6, 18),
                ("c10", 2, 12), ("c11", 0.2, 8), ("c12", 2, 10)],
          inspect=["c9 Q903 and c10 Q1002 (DMMT3904W, SOT-363): the pin-1 mark at the BOTTOM-RIGHT corner as the board reads (they are turned 180).",
                   "c7: U701 (LF398, SOIC-14) pin 1; c4: U401 (MAX7410, MSOP-8) pin 1; c5: U501 (TSSOP-16) pin 1.",
                   "c2: the 2.2 uH inductor and the three SOT-23-5 parts; c3: U302 (ICL7660A, SOIC-8) pin 1.",
                   "c10: the 1 x 2 header; the Pmod plug hangs off the bottom edge under c9."])


def _c2_ripple(k):
    return Time(lambda t, emf, ctx: k * np.sign(np.sin(TWO_PI * 1e3 * t)) * np.exp(-((t * 1e3) % 0.5) / 0.05))


T += [dc("c2", "LOAD", [0.0, 0.5], None, {"psu": lambda v, ctx: 0.012 + 0.082 * v}, [Num("input current for 50 mA of load", 0.026, 0.058, "A")],
         name="electronic load", derive=lambda v: {"input current for 50 mA of load": v["psu@0.5"] - v["psu@0"]}, psu=True,
         why="LOAD 0.5 V: 50 mA from the LDO: 50 mA x 3.6 V / (5 V x 0.88)"),
      wave("c2", "LOAD", "square", 1e3, 0.5, {"buck": ("BUCK~", "1M"), "ldo": ("LDO~", "1M")}, {"buck": _c2_ripple(0.02), "ldo": _c2_ripple(0.004)},
           [W("vpp", 0.002, 0.4, "buck"), Check("LDO~ / BUCK~", lambda r: r.vpp("ldo") / r.vpp("buck"), "", lo=0, hi=0.9)], name="load step",
           offset=0.25, why="a 0 to 50 mA step: the buck's transient, and the LDO's smaller one")]
_C9 = Time(lambda t, emf, ctx: -0.98 * np.tanh(emf / 2.0 / 0.052))
T += [dc("c9", "IN+", [-0.1, -0.01, 0.0, 0.01, 0.1], "OUT", _C9,
         [Num("OUT@0.1", tol=0.13), Num("OUT@-0.1", tol=0.13), Num("OUT@0.01", tol=0.07), Num("OUT@-0.01", tol=0.07), Num("OUT@0", -0.15, 0.15, "V")],
         why="-1 k x 0.98 mA x tanh(Vd / 52 mV); IN- rests at 0 V on its own 49.9 ohm")]
T += [bode("c10", "IN", "OUT", (1e4, 3e7, 25), 0.05, amp(6.0, 12e6, rout=51.0),
           [Gabs(1e5, 11.5, 19.0), Check("-3 dB corner", lambda r: r.corner(-3, "hi", "lf"), "Hz", lo=3.5e6, hi=6e7)], name="cascode",
           why="no jumper: Q1's collector held still"),
      bode("c10", "IN", "OUT", (1e4, 3e7, 25), 0.05, amp(6.0, 2e6, rout=51.0),
           [Check("-3 dB corner", lambda r: r.corner(-3, "hi", "lf"), "Hz", lo=0.7e6, hi=4e6)], name="common emitter", hands=True,
           pre=("c10: jumper ON the CE header's two pins",), why="the Miller capacitance back: about 2 MHz")]
# The 555: the CV jack's 51 ohm to ground pulls the control pin down through 2.2 k (REVB.md), so the frequency is not the silk's 6.9 kHz.
_C11 = Time(lambda t, emf, ctx: 0.5 + 0.5 * np.sign(np.sin(TWO_PI * 12e3 * t)))
T += [listen("c11", "OUT", _C11, [W("freq", 5.5e3, 17e3, unit="Hz"), W("vpp", 0.6, 1.3)], name="free running", span=2e-3,
             why="silk says 6.9 kHz; the netlist predicts 11-14 kHz with CV unconnected: record which"),
      seq("c11", "CV moves it", [dict(gen={"cv": ("dc", 0, 0, 0.0)}, wait=0.2, read={"f0": ("scope", "out", "freq")}),
                                 dict(gen={"cv": ("dc", 0, 0, 0.5)}, wait=0.2, read={"f+": ("scope", "out", "freq")})],
          lambda ctx: {"f0": 12e3, "f+": 11e3}, [Num("f(+1 V) / f(0 V)", 0.4, 0.985)], gens={"cv": "CV"}, scopes={"out": ("OUT", "1M")},
          derive=lambda v: {"f(+1 V) / f(0 V)": v["f+"] / v["f0"]}, why="a higher control voltage: a longer charge, a lower frequency")]
T += [wave("c12", "IN", "sine", 1e3, 1.0, "OUT", Time(lambda t, emf, ctx: np.abs(emf / 2.0)),
           [W("vmax", 0.43, 0.56), W("vmin", -0.03, 0.06), W("freq", 1.9e3, 2.1e3, unit="Hz")], why="OUT = |IN|: twice the frequency")]
_USE_C = H("use", "amod_c")
T += [seq("c3", "pump against its clock",
          [dict(host=[_USE_C, H("clock", "IO6", 100e3)], wait=1.0, read={"out 100 kHz": ("scope", "out", "mean"), "cap vpp": ("scope", "cap", "vpp")}),
           dict(host=[H("clock", "IO6", 2e3)], wait=1.5, read={"out 2 kHz": ("scope", "out", "mean")}), dict(host=[H("safe")])],
          lambda ctx: {"out 100 kHz": -0.807, "out 2 kHz": -0.42, "cap vpp": 0.85},
          [Num("out 100 kHz", -0.92, -0.68, "V"), Num("out 2 kHz", -0.60, -0.25, "V"), Num("cap vpp", 0.3, 1.2, "V")],
          scopes={"out": ("OUT", "1M"), "cap": ("CAP", "1M")}, why="Rout = 1 / (f C) + 60 ohm into 1 k: -4.6 V at 100 kHz, -2.4 V at 2 kHz, each / 5.7")]
for fclk in (1e6, 500e3):
    T += [bode("c4", "IN", "OUT", (1e3, 4e4, 25), 0.5, butter(5, fclk / 100),
               [G(1.5e3, 1.0), Corner(0.08), Check("gain two corners up", lambda r, f=fclk: r.gain(2 * f / 100), "dB", lo=-50, hi=-22)],
               name="clock %g kHz" % (fclk / 1e3), host=(_USE_C, H("clock", "IO3", fclk)), why="corner = clock / 100")]
T += [bode("c5", "IN", "OUT", (2e2, 5e3, 11), 0.1, Lin(lambda f, load: -100.0 / (1 + 1j * f / 15.9)), [G(1e3, 1.5), G(3e3, 1.5)],
           host=(_USE_C, H("two_phase", "IO4", "IO8", 100e3)), why="R = 1 / (100 kHz x 1 nF) = 10 k into 10 nF: 1592 / f")]
T += [seq("c6", "ones density against IN", [dict(host=[_USE_C, H("clock", "IO1", 1e6)])] +
          [dict(gen={"in": ("dc", 0, 0, v)}, wait=0.3, read={"density@%g" % (2 * v): ("host", "density", "IO7")}) for v in (-0.5, 0.0, 0.5)] +
          [dict(host=[H("safe")])],
          lambda ctx: {"density@-1": 0.5 - 1 / 3.3, "density@0": 0.5, "density@1": 0.5 + 1 / 3.3},
          [Num("density@-1", tol=0.05), Num("density@0", tol=0.04), Num("density@1", tol=0.05)], gens={"in": "IN"},
          why="second order: density = 0.5 + IN / 3.3 V")]
T += [wave("c7", "IN", "sine", 1e3, 1.0, "OUT", amp(1.0, 1e6), [W("tone", 0.44, 0.53, arg=1e3)], name="track", host=(_USE_C, H("out", "IO5", 1)),
           why="IO5 high: OUT follows IN"),
      wave("c7", "IN", "sine", 1e3, 1.0, "OUT", const(0.2), [W("vpp", 0, 0.06)], name="hold", host=(_USE_C, H("out", "IO5", 0)),
           why="IO5 low: OUT stands still (30 mV/s of droop)")]
T += [seq("c8", "the bit against the DAC",
          [dict(host=[_USE_C], gen={"in": ("dc", 0, 0, 0.25), "dac": ("dc", 0, 0, -0.1)}, wait=0.2, read={"bit, DAC below IN": ("host", "inp", "IO2")}),
           dict(gen={"dac": ("dc", 0, 0, 0.6)}, wait=0.2, read={"bit, DAC above IN": ("host", "inp", "IO2")}), dict(host=[H("safe")])],
          lambda ctx: {"bit, DAC below IN": 1, "bit, DAC above IN": 0}, [Num("bit, DAC below IN", 1, 1), Num("bit, DAC above IN", 0, 0)],
          gens={"in": "IN", "dac": "DAC"}, why="IN +0.5 V; DAC at -0.2 V, then +1.2 V")]

# =====================================================================================================
# AMOD-N: the pieces of a network analyzer (no USB; n8 and n9 run from the Pmod's 3.3 V)
# =====================================================================================================
T = board("amod_n", letter="n", name="AMOD-N", title="network analyzer pieces", power=None, pmod="n8",
          setup=["n8 DIP (8 ways): way 1 (SPI) ON, ways 2-8 OFF", "n11 DIP (2 ways): way 1 (200 ohm) ON, way 2 OFF", "n9's slide switch UP (on)"],
          inspect=["n8: U801 (PE43711, QFN-24) pin-1 dot at the chip's top-left as the board reads; the 8-way DIP's ON toward the top edge.",
                   "n3 (ADP-2-1+), n10 (TC1-1TG2+), n11 (TC4-1W+): each transformer's dot as the silkscreen draws it.",
                   "n6: D601 (SOT-23); n9: Q902 and the BB133 varactor (its cathode band toward the 10 uH inductor).",
                   "n1 SHORT: the centre pin soldered into copper all round (no clearance ring).  n4: the stub is copper, 17.3 mm long.",
                   "n10's OUT jack: no copper bridge from its legs to the ground pour (it floats)."])
T += [bode("n1", "THRU A", {"b": ("THRU B", "50")}, (1e4, 3e7, 9), 1.0, {"b": flat(0)}, [G(1e6, 0.5, "b"), G(3e7, 1.0, "b")], load="50", name="THRU",
           why="19.8 mm of 50 ohm line"),
      bode("n2", "IN", {"o1": ("OUT 1", "50"), "o2": ("OUT 2", "50")}, (1e4, 3e7, 9), 1.0, {"o1": flat(-6.02), "o2": flat(-6.02)},
           [G(1e6, 0.5, "o1"), G(1e6, 0.5, "o2"), G(3e7, 1.0, "o1")], why="three 16.9 ohm: half the voltage to each"),
      bode("n3", "SUM", {"p1": ("PORT 1", "50"), "p2": ("PORT 2", "50")}, (3e5, 3e7, 11), 1.0, {"p1": flat(-3.3), "p2": flat(-3.3)},
           [G(3e6, 0.8, "p1"), G(3e6, 0.8, "p2"), G(3e7, 1.0, "p1")], why="ADP-2-1+: 3.0 dB of split and 0.3 dB of loss"),
      bode("n5", "IN", "OUT", (1e5, 3e7, 7), 1.0, flat(-0.2), [G(1e7, 0.6)], load="50", name="passband", why="LFCN-1000+ far below its corner"),
      bode("n7", "RF", "RF+DC", (1e5, 3e7, 17), 1.0,
           ladder([("s", C(100e-9)), ("p", ser(L(27e-9), L(330e-9), L(10e-6), C(100e-9)))]), [G(1e7, 0.8), G(3e7, 1.0)], load="50", name="RF path",
           why="100 nF in series; 10 uH to the DC loop's 100 nF"),
      bode("n10", "IN", "OUT", (1e6, 3e7, 7), 1.0, flat(-0.4), [G(1e7, 0.8)], load="50", why="TC1-1TG2+, 0.3 dB at 10 MHz"),
      bode("n11", "IN", "OUT", (3e6, 3e7, 7), 0.5, flat(6.0 - 0.8), [G(1e7, 1.2)], name="1:4, 200 ohm on", why="matched: twice the voltage, 0.8 dB of loss"),
      bode("n11", "IN", "OUT", (3e6, 3e7, 7), 0.5, flat(20 * math.log10(2 * 2 * 9.98 / (9.98 + 50)) - 0.8), [G(1e7, 1.5)], name="1:4, 200 and 49.9 ohm on",
           hands=True, pre=("n11 DIP: way 2 (49.9 ohm) ON as well as way 1",), why="40 ohm across OUT is 10 ohm at IN")]
for dbm, lo, hi in ((-10, 0.035, 0.22), (0, 0.14, 0.75)):
    T += [wave("n6", "IN", "sine", 20e6, dbm_vpp(dbm), "OUT", const(0.1 if dbm < 0 else 0.4), [W("mean", lo, hi)], name="%+d dBm at 20 MHz" % dbm,
               cycles=400, why="a doubler of two zero-bias diodes: about 0.1 V at -10 dBm; positive")]
T += [manual("n7", "DC path", "Bench supply output 2 at 5.0 V, 20 mA limit, clipped to n7's DC and GND loops; the scope on RF+DC reads 5 V and on RF 0 V.",
             pre=("two clip leads from the supply's output 2 to the DC and GND test loops",)),
      manual("n10", "OUT floats", "A meter between n10's OUT jack shell and any other jack's shell reads open (over 1 Mohm), and the same from OUT's centre pin.")]
_USE_N = H("use", "amod_n")
_ATT = [0, 0.25, 0.5, 1, 2, 4, 8, 16, 31.75]
T += [seq("n8", "every bit, by the FPGA", [dict(host=[_USE_N], gen={"in": ("sine", 10e6, 0.2, 0.0)})] +
          [dict(host=[H("pe43711_set", a)], wait=0.1, read={"%g dB" % a: ("scope", "out", "tone", 10e6)}) for a in _ATT] + [dict(host=[H("safe")])],
          lambda ctx: {"%g dB" % a: 0.1 * 10 ** (-(a + 1.6) / 20.0) for a in _ATT},
          [Num("loss at 0 dB", 0.8, 3.2, "dB")] + [Num("step to %g dB" % a, a - 0.35 - 0.03 * a, a + 0.35 + 0.03 * a, "dB") for a in _ATT[1:]],
          gens={"in": "IN"}, scopes={"out": ("OUT", "50")},
          derive=lambda v: dict({"loss at 0 dB": -20 * math.log10(v["0 dB"] / 0.1)},
                                **{"step to %g dB" % a: 20 * math.log10(v["0 dB"] / v["%g dB" % a]) for a in _ATT[1:]}),
          why="PE43711 over the Pmod: each of the seven bits alone, then all of them"),
      seq("n8", "by the switches", [dict(gen={"in": ("sine", 10e6, 0.2, 0.0)}, read={"v": ("scope", "out", "tone", 10e6)})],
          lambda ctx: {"v": 0.1 * 10 ** (-17.6 / 20)}, [Num("loss", 16.3, 19.5, "dB")], gens={"in": "IN"}, scopes={"out": ("OUT", "50")},
          derive=lambda v: {"loss": -20 * math.log10(v["v"] / 0.1)}, hands=True, host=(H("ident"),),
          pre=("n8 DIP: way 1 (SPI) OFF, way 8 (16 dB) ON, ways 2-7 OFF",), why="direct parallel mode: 16 dB by hand"),
      seq("n9", "oscillator and its tuning", [dict(host=[H("ident")], gen={"tune": ("dc", 0, 0, v)}, wait=0.3,
                                                   read={"f@%g" % (2 * v): ("scope", "out", "freq"), "vpp@%g" % (2 * v): ("scope", "out", "vpp")})
                                              for v in (0.0, -1.0, 1.0)],
          lambda ctx: {"f@0": 10.5e6, "f@-2": 9.6e6, "f@2": 11.5e6, "vpp@0": 0.05, "vpp@-2": 0.05, "vpp@2": 0.05},
          [Num("f@0", 9.3e6, 11.7e6, "Hz"), Num("f(-2 V) / f(0)", 0.85, 0.975), Num("f(+2 V) / f(0)", 1.025, 1.16), Num("vpp@0", 0.015, 0.2, "V")],
          gens={"tune": "TUNE"}, scopes={"out": ("OUT", "50")},
          derive=lambda v: {"f(-2 V) / f(0)": v["f@-2"] / v["f@0"], "f(+2 V) / f(0)": v["f@2"] / v["f@0"]},
          why="Clapp: 10 uH and the BB133 between 220 pF and 220 pF; TUNE through 100 k")]
_RFF = (50e6, 6e9, 1601)          # one sweep for every analyzer test: the 8720ES's calibration holds only for the sweep it was made at
T += [s21("n1", "THRU A", "THRU B", _RFF, flat(-0.3), [Gabs(1e9, -1.0, 0.2), Gabs(3e9, -1.8, 0.2), Gabs(6e9, -4.0, 0.3)], name="THRU, S21"),
      s21("n1", "LOAD", None, _RFF, flat(-30), [Gabs(1e9, -80, -17), Gabs(3e9, -80, -12)], name="LOAD, S11", param="S11"),
      s21("n1", "25 OHM", None, _RFF, flat(-9.54), [Gabs(5e8, -11.0, -8.2), Gabs(2e9, -12.5, -7.0)], name="25 OHM, S11", param="S11"),
      s21("n1", "SHORT", None, _RFF, flat(-0.1), [Gabs(1e9, -1.5, 0.3)], name="SHORT, S11", param="S11"),
      s21("n1", "OPEN", None, _RFF, flat(-0.1), [Gabs(1e9, -1.5, 0.3)], name="OPEN, S11", param="S11"),
      s21("n2", "IN", "OUT 1", _RFF, flat(-6.1), [Gabs(1e9, -7.0, -5.3), Gabs(3e9, -8.0, -5.0)], pre=("a 50 ohm terminator on n2 OUT 2",)),
      s21("n2", "IN", "OUT 2", _RFF, flat(-6.1), [Gabs(1e9, -7.0, -5.3), Gabs(3e9, -8.0, -5.0)], pre=("a 50 ohm terminator on n2 OUT 1",)),
      s21("n3", "SUM", "PORT 1", _RFF, flat(-3.3), [Gabs(1e8, -4.2, -2.8), Gabs(4e8, -5.0, -2.8)], pre=("a 50 ohm terminator on n3 PORT 2",)),
      s21("n3", "PORT 1", "PORT 2", _RFF, flat(-28), [Gabs(1e8, -80, -18)], name="isolation, PORT 1 to PORT 2",
          pre=("a 50 ohm terminator on n3 SUM",)),
      s21("n4", "IN", "OUT", _RFF, Lin(lambda f, load: 1.0 / (1 + 0.5j * np.tan(0.5 * math.pi * f / 2.45e9) + 0.02)),
          [NotchF(0.08, lo=1.5e9, hi=3.5e9), Gabs(3e8, -1.5, 0.2), Check("notch depth", lambda r: r.notch(None, 1.5e9, 3.5e9)[1], "dB", hi=-15)]),
      s21("n5", "IN", "OUT", _RFF, table([(5e7, -0.2), (5e8, -0.3), (1e9, -0.8), (1.3e9, -3), (1.5e9, -26), (1.9e9, -32), (6e9, -32)]),
          [Gabs(5e8, -1.5, 0.1), Gabs(1e9, -2.5, 0.0), Gabs(2.5e9, -80, -20)]),
      s21("n7", "RF", "RF+DC", _RFF, flat(-0.4), [Gabs(1e8, -1.5, 0.2), Gabs(2.4e9, -2.5, 0.2)]),
      s21("n10", "IN", "OUT", _RFF, flat(-0.6), [Gabs(1e8, -1.5, 0.1), Gabs(5e8, -3.5, 0.1)]),
      s21("n11", "IN", None, _RFF, flat(-20), [Gabs(1e8, -80, -11), Gabs(5e8, -80, -8)], name="IN matched by 200 ohm, S11", param="S11"),
      s21("n8", "IN", "OUT", _RFF, flat(-2.0), [Gabs(1e9, -3.2, -1.0), Gabs(3e9, -4.5, -1.0)], name="S21 at 0 dB", host=(_USE_N, H("pe43711_set", 0))),
      s21("n8", "IN", "OUT", _RFF, flat(-18.0), [Gabs(1e9, -19.8, -16.6)], name="S21 at 16 dB", host=(_USE_N, H("pe43711_set", 16)))]

# =====================================================================================================
# AMOD-M: motors (most of it wants a motor: the kit stage)
# =====================================================================================================
T = board("amod_m", letter="m", name="AMOD-M", title="motors", power="m1", socket=True, pmod="m3", quiescent=(0.008, 0.045),
          setup=["m6: no jumper on the D / Z header", "every tile's slide switch DOWN (off)", "nothing on the barrel jack yet"],
          walk=[("m3", 3, 16), ("m4", 0.5, 12), ("m5", 1, 9), ("m6", 1, 9), ("m8", 1, 12), ("m9", 6, 22), ("m10", 18, 36)],
          inspect=["m6: Q602 (NCE6020AK, TO-252) tab to the right; m7: U701 (TCA0372, SOIC-16W) pin 1; m8: U802 (TPS28225) pin 1.",
                   "m3, m4: the DRV8251A's exposed pad under the body, pin 1 at the dot.",
                   "The JST connectors (m3 PH 6-way, m4 and m11 XH 4-way) and the barrel jack soldered through.",
                   "m2: the 220 uF electrolytic's stripe (negative) as the silkscreen marks it; D (SMBJ16A) and the two SS34.",
                   "The Pmod plug hangs off the bottom edge under m3."])
T += [listen("m2", "VM", const(0.29), [W("mean", 0.24, 0.33)], name="VMOT on USB power", why="(5 V less a Schottky) / 16"),
      listen("m4", {"ia": ("IA", "1M"), "ib": ("IB", "1M")}, {"ia": const(0.0), "ib": const(0.0)}, [W("mean", -0.05, 0.05, "ia"), W("mean", -0.05, 0.05, "ib")]),
      listen("m5", "I", const(0.0), [W("mean", -0.06, 0.06)]),
      listen("m6", {"i": ("I", "1M"), "vd": ("VD", "1M")}, {"i": const(0.0), "vd": const(0.0)}, [W("mean", -0.06, 0.06, "i"), W("mean", -0.05, 0.12, "vd")]),
      listen("m7", "I", const(0.0), [W("mean", -0.04, 0.04)], why="no load: within 10 mA of zero, at 1 V/A"),
      listen("m9", "OUT", const(0.0), [W("mean", -0.12, 0.12)], why="no magnet: the DRV5055's half-supply subtracted away"),
      listen("m10", "OUT", const(0.02), [W("mean", -0.05, 0.2)], why="nothing over the sensor"),
      listen("m11", "OUT", const(0.0), [W("mean", -5.5, 5.5)], name="no cell (recorded only)")]
for duty, name in ((50, "half"), (25, "quarter")):
    T += [wave("m8", "PWM", "square", 200e3, 1.0, {"vo": ("VO", "1M"), "i": ("I", "1M")}, {"vo": const(4.6 * duty / 100 / 16), "i": const(0.0)},
               [Wm("mean", "vo", frac=0.18)], name="%s duty, no load" % name, offset=0.5, duty=duty, cycles=20,
               why="a synchronous stage with no load: VO = duty x VMOT; the jack is VO / 16")]
_USE_M = H("use", "amod_m")
T += [seq("m3", "bridge with no motor", [dict(host=[_USE_M, H("out", "IO7", 1), H("out", "IO1", 0)], wait=0.2, read={"forward": ("scope", "v", "mean")}),
                                         dict(host=[H("out", "IO7", 0), H("out", "IO1", 1)], wait=0.2, read={"reverse": ("scope", "v", "mean")}),
                                         dict(host=[H("out", "IO7", 1), H("out", "IO1", 1)], wait=0.2, read={"brake": ("scope", "v", "mean"), "current": ("scope", "i", "mean")}),
                                         dict(host=[H("safe")])],
          lambda ctx: {"forward": 4.6 / 13, "reverse": -4.6 / 13, "brake": 0.0, "current": 0.0},
          [Num("forward", 0.29, 0.41, "V"), Num("reverse", -0.41, -0.29, "V"), Num("brake", -0.04, 0.04, "V"), Num("current", -0.04, 0.04, "V")],
          scopes={"v": ("V", "1M"), "i": ("I", "1M")}, why="IN1 on IO7, IN2 on IO1: (M1 - M2) / 13 = +-VMOT / 13"),
      manual("m3", "motor and encoder", "A 6 V gear motor with an encoder on the PH connector (M1 G A B 3V3 M2): I run it both ways at three duties and "
             "read its current, its back-EMF in coast and the encoder's count.", kit=("N20 gear motor with encoder, PH 6-way cable", "12 V on the barrel jack")),
      manual("m4", "stepper", "A NEMA 17 on the XH connector: I step it 200 full steps each way and read IA and IB (0.98 V/A, 1 A limit).",
             kit=("NEMA 17 stepper, XH 4-way cable", "12 V on the barrel jack")),
      manual("m5", "servo", "A hobby servo on the S + - header: I send 1.0, 1.5 and 2.0 ms pulses on CMD and read I.", kit=("SG90 or MG90S servo",)),
      manual("m6", "solenoid and flyback", "A solenoid (or a 12 ohm, 5 W resistor) on the coil terminal, 12 V on the barrel jack: I pulse CMD and "
             "read I and VD with the jumper on 1-2 (diode), then 2-3 (TVS).  The no-jumper (avalanche) case only after the coil's energy is checked.",
             kit=("5 V or 12 V solenoid", "jumper cap", "12 V on the barrel jack")),
      manual("m7", "bridge amplifier", "An 8 ohm resistor or speaker on the load terminal: IN at 0.2 V gives 0.8 V across it and 0.1 V on I.",
             kit=("8 ohm, 5 W resistor or speaker",)),
      manual("m9", "hall", "Bring a magnet's pole to the small part at the tile's top left: OUT swings one way, the other pole the other way."),
      manual("m10", "optical", "White paper 1 mm over the sensor (top left of the tile): OUT rises to 0.1-0.9 V."),
      manual("m11", "load cell", "A 1 kg bar load cell on the XH connector (red E+, black E-, white S-, green S+): OUT moves with a finger's push.",
             kit=("1 kg load cell, XH 4-way",))]

# =====================================================================================================
# AMOD-B: a brushless gimbal motor and its sensors
# =====================================================================================================
T = board("amod_b", letter="b", name="AMOD-B", title="brushless", power="b1", socket=True, pmod="b3", quiescent=(0.03, 0.12),
          setup=["b3's slide switch DOWN (off)", "nothing on the barrel jack, no motor yet"], walk=[("b3", 3, 30)],
          inspect=["b3: U301 (DRV8311H, WQFN-24, 0.4 mm pitch) pin 1 at the dot; look for bridges along all four sides.",
                   "b5: U501 (MT6701, SOP-8) at the centre of the four slots, pin 1; the two DRV5055 and the QRE1113 between the slots.",
                   "b6: U601 (LSM6DSO, LGA-14) pin-1 dot; U602 (SOT-23-5).",
                   "b11: U1101 (INA240, SOIC-8) pin 1 and the 0.05 ohm shunt; b12: the 0.1 ohm shunt.",
                   "b2: the 220 uF electrolytic's stripe; the barrel jack; b3 and b8: the screw terminals' openings toward the top edge.",
                   "The four motor slots are clean ovals; the Pmod plug hangs off the bottom edge under b3."])
T += [listen("b2", "VM", const(0.29), [W("mean", 0.24, 0.33)], name="VMOT on USB power"),
      listen("b3", {"ia": ("IA", "1M"), "ib": ("IB", "1M")}, {"ia": const(0.0), "ib": const(0.0)}, [W("mean", -0.08, 0.08, "ia"), W("mean", -0.08, 0.08, "ib")],
             why="no current: SOA and SOB shifted to 0 V by 3.3 k / 10 k"),
      listen("b8", "VIB", const(0.0), [W("mean", -0.2, 0.2)]), listen("b9", "IDX", const(0.01), [W("mean", -0.1, 0.4)]),
      listen("b10", {"ha": ("HA", "1M"), "hb": ("HB", "1M")}, {"ha": const(0.0), "hb": const(0.0)}, [W("mean", -0.12, 0.12, "ha"), W("mean", -0.12, 0.12, "hb")]),
      listen("b11", "IPA", const(0.0), [W("mean", -0.08, 0.08)]), listen("b12", "I", const(0.0), [W("mean", -0.08, 0.08)]),
      listen("b7", "ANG", const(0.0), [W("mean", -1.0, 1.0)], name="no magnet (recorded only)")]
_USE_B = H("use", "amod_b")


def _phases(a, b, c):
    return [H("out", "IO5", a), H("out", "IO1", b), H("out", "IO2", c)]


_EHI, _ELO = (4.6 - 4.6 / 3) / 14, (0 - 4.6 / 3) / 14
T += [seq("b4", "each phase high in turn, no motor",
          [dict(host=[_USE_B] + _phases(1, 0, 0), gen={"coast": ("dc", 0, 0, 0.0)}, wait=0.2, read={"EA, A high": ("scope", "ea", "mean"), "EB, A high": ("scope", "eb", "mean")}),
           dict(host=_phases(0, 1, 0), wait=0.2, read={"EA, B high": ("scope", "ea", "mean"), "EB, B high": ("scope", "eb", "mean")}),
           dict(host=_phases(0, 0, 1), wait=0.2, read={"EA, C high": ("scope", "ea", "mean"), "EB, C high": ("scope", "eb", "mean")}),
           dict(host=_phases(0, 0, 0) + [H("safe")])],
          lambda ctx: {"EA, A high": _EHI, "EB, A high": _ELO, "EA, B high": _ELO, "EB, B high": _EHI, "EA, C high": _ELO, "EB, C high": _ELO},
          [Num("EA, A high", tol=0.05), Num("EB, A high", tol=0.04), Num("EA, B high", tol=0.04), Num("EB, B high", tol=0.05),
           Num("EA, C high", tol=0.04), Num("EB, C high", tol=0.04)],
          gens={"coast": ("b3", "COAST")}, scopes={"ea": ("EA", "1M"), "eb": ("EB", "1M")},
          why="INHA IO5, INHB IO1, INHC IO2: a phase at VMOT reads (VMOT - VMOT / 3) / 14, the others -(VMOT / 3) / 14"),
      seq("b6", "IMU and encoder answer", [dict(host=[_USE_B], read={"WHO_AM_I": ("host", "lsm6dso_whoami"), "encoder CRC ok": ("host", "mt6701_read.crc_ok", False)}),
                                           dict(host=[H("safe")])],
          lambda ctx: {"WHO_AM_I": 0x6C, "encoder CRC ok": 1}, [Num("WHO_AM_I", 0x6C, 0x6C), Num("encoder CRC ok", 1, 1)],
          why="LSM6DSO on CS IMU (IO8), MT6701 on CS ENC (IO6) through the buffer: one MISO"),
      manual("b5", "gimbal motor", "GBM2804H-100T on the four slots with a 6 x 2.5 mm diametric magnet on its shaft, 1 mm over the MT6701; its three "
             "wires in b3's terminal (C B A).  I turn it open loop, then read the angle, the halls, the index, the currents and the back-EMF.",
             kit=("GBM2804H-100T gimbal motor", "6 x 2.5 mm diametric magnet", "M2 / M2.5 screws", "12 V on the barrel jack", "a piezo disc for b8"))]

# =====================================================================================================
# RF-MOD: one radio link on one reference
# =====================================================================================================
T = board("rf_mod", letter="r", name="RF-MOD", title="RF blocks", power="r9", socket=False, pmod="r10", quiescent=(0.01, 0.06), limit=1.3,
          setup=["every tile's slide switch DOWN (off)", "a 50 ohm terminator ready for r10's unused output"],
          walk=[("r5", 50, 85), ("r7", 12, 35), ("r8", 12, 35), ("r10", 15, 140), ("r12", 130, 220), ("r13", 20, 220)],
          inspect=["r10: U1002 (MAX2871, QFN-32) pin-1 dot; r13: U1301 (TRF3722, VQFN-48) pin-1 dot; solder bridges on both.",
                   "r12: U1201 (GALI-84+, SOT-89): its tab toward the top edge.  r5: U501 (QPL9547, DFN 2 x 2) pin-1 dot.",
                   "r9: X901 (the TCXO) pad 1 mark; U901 (MT3608) and the SS34's cathode bar toward the output capacitor.",
                   "r7, r8: U702 / U802 (ADL5350, 8-lead) pad 1.  r1: the ADEX-10L+'s dot.  r2 (LTCC) and r4 (SAW): lying along their lines.",
                   "The Pmod plug hangs off the bottom edge under r10 and does not cover the OUT A- line above its pins."])
T += [listen("r9", "REF OUT", Time(lambda t, emf, ctx: 0.8 * np.sign(np.sin(TWO_PI * 25e6 * t))), [W("freq", 24.97e6, 25.03e6, unit="Hz"), W("vpp", 1.0, 2.2)],
             load="50", span=4e-7, name="25 MHz reference", why="TC32H4 through a 74LVC1G17 and 51 ohm: 1.6 V p-p into 50 ohm")]
T += [wave("r1", {"lo": "LO", "rf": "RF"}, None, None, None, {"if": ("IF", "50")},
           {"if": Time(lambda t, emf, ctx: 10 ** (-7.2 / 20) * (emf["rf"] / 2.0) * np.sign(emf["lo"]) * 4 / math.pi / 2 * 2)},
           [W("tone", 0.006, 0.024, arg=1e6)], name="20 MHz LO, 21 MHz RF", span=2e-5,
           stim={"lo": ("sine", 20e6, dbm_vpp(4), 0.0), "rf": ("sine", 21e6, dbm_vpp(-20), 0.0)},
           why="+4 dBm of LO, -20 dBm of RF: -27 dBm at 1 MHz (7 dB of loss)")]
_USE_R = H("use", "rf_mod")
_REFJ = ("an SMA cable from r9 REF OUT to r10 REF IN", "a 50 ohm terminator on r10's other output", "r10's slide switch UP")


def _synth(f, lvl=3.0):
    return lambda ctx: ([(f, lvl)], -75.0)


for f0 in (915e6, 2440e6, 100e6, 5800e6):
    T += [spec("r10", "OUT A+", (f0 - 5e6, f0 + 5e6), _synth(f0), [SpecPeakF(f0, 4e6, 60e3), SpecPeak(f0, 4e6, -6 if f0 < 3e9 else -12, 9)],
               name="OUT A+ at %g MHz" % (f0 / 1e6), host=(_USE_R, H("max2871_set", f0, 3, key="locked")), pre=_REFJ,
               why="MAX2871 at its top power step (+5 dBm), locked to the TCXO")]
T += [spec("r10", "OUT A-", (910e6, 920e6), _synth(915e6), [SpecPeak(915e6, 4e6, -6, 9)], name="OUT A- at 915 MHz",
           host=(_USE_R, H("max2871_set", 915e6, 3, key="locked")), pre=_REFJ, why="the complementary output: the same power within a dB or two")]
for tile, word in (("r7", "TX"), ("r8", "RX")):
    T += [spec(tile, "RF", (900e6, 930e6), lambda ctx: ([(915e6 - 6.25e6, -9.0), (915e6 + 6.25e6, -9.0), (915e6, -20.0)], -75.0),
               [SpecPeak(921.25e6, 1.5e6, -18, -3), SpecPeak(908.75e6, 1.5e6, -18, -3)], name="up-conversion at 915 MHz", gens={"if": "IF"},
               stim={"if": ("sine", 6.25e6, dbm_vpp(0), 0.0)}, host=(_USE_R, H("max2871_set", 915e6, 3)),
               pre=("an SMA cable from r10 OUT A+ to %s LO" % tile, "an SMA cable from r9 REF OUT to r10 REF IN", "a 50 ohm terminator on r10 OUT A-"),
               why="0 dBm at 6.25 MHz on IF: both sidebands about 8 dB down")]
T += [spec("r13", "RF OUT", (910e6, 920e6), _synth(915e6, -6.0), [SpecPeak(915e6, 4e6, -20, 3)], name="carrier at 915 MHz", gens={"i": "I IN"},
           stim={"i": ("dc", 0, 0, 0.5)}, host=(_USE_R, H("trf3722_set", 915e6, key="locked")),
           pre=("an SMA cable from r9 REF OUT to r10 REF IN (the back trace carries it on to r13)", "r13's slide switch UP"),
           why="DC on I alone is a CW carrier; about -3 dBm at full scale")]
_F3 = _RFF
T += [s21("r2", "IN", "OUT", _F3, table([(5e7, -45), (2.0e9, -32), (2.3e9, -6), (2.4e9, -1.8), (2.5e9, -1.8), (2.6e9, -6), (3.0e9, -30), (6e9, -30)]),
          [Gabs(2.45e9, -3.8, -0.8), Gabs(1.9e9, -90, -18), Gabs(3.1e9, -90, -15)]),
      s21("r4", "IN", "OUT", _RFF, table([(7e8, -50), (8.8e8, -45), (9.0e8, -4), (9.02e8, -1.3), (9.28e8, -1.3), (9.3e8, -4), (9.5e8, -45), (1.1e9, -50)]),
          [Gabs(915e6, -3.6, -0.5), Gabs(860e6, -95, -25), Gabs(970e6, -95, -25)], power=-10.0),
      s21("r5", "IN", "OUT", _F3, table([(5e7, 22), (5e8, 21), (1e9, 19.5), (2.4e9, 16), (6e9, 9)]), [Gabs(1e9, 15, 23.5), Gabs(2.4e9, 11, 21)],
          power=-30.0, pre=("r5's slide switch UP",), why="QPL9547: never more than -20 dBm in"),
      s21("r12", "IN", "OUT", _F3, table([(5e7, 23), (1e9, 21.9), (2.5e9, 18), (6e9, 10)]), [Gabs(1e9, 17, 24.5), Gabs(2.4e9, 13, 22)],
          power=-25.0, pre=("r12's slide switch UP",), why="GALI-84+ from 7.8 V through 22 ohm")]

# =====================================================================================================
# PhMOD: magnetic resonance, the ionosphere and light
# =====================================================================================================
T = board("phmod", letter="h", name="PhMOD", title="physics", power="h1", socket=False, pmod="h5", quiescent=(0.03, 0.14),
          setup=["h8 DIP (4 ways): all OFF", "every tile's slide switch DOWN (off)", "nothing on h4's terminals, no laser anywhere near h10"],
          walk=[("h3", 14, 40), ("h4", 2, 16), ("h5", 22, 60), ("h6", 3, 12), ("h7", 10, 28), ("h8", 0.02, 3), ("h9", 10, 34), ("h10", 4, 20)],
          inspect=["h1: U101 (TPS65131, VQFN-24) pin 1; the inverter's B5819W points from the inductor's node to -15 V as drawn.",
                   "h2: U201 (THS3491, VQFN-16 3 x 3) pin-1 dot.  h4: U401 (DRV8876, HTSSOP-16) pin 1; both B5819W bars toward VM.",
                   "h3: four pairs of 1N4148W, each pair with one bar each way.  h8: four BB133, in pairs cathode to cathode.",
                   "h10: the three SOT-23 FETs; the B5819W's bar toward the inductors.  h9: Q902 (MMBT3904).",
                   "h4: both screw terminals' openings toward the right edge, not overhanging it.  The Pmod plug under h5."])
T += [bode("h3", "LINE", "RX OUT", (1e5, 3e7, 13), 0.02, amp(12.0, 200e6), [G(1e6, 1.0), G(1e7, 1.5)], name="preamplifier",
           why="OPA847 at 1 + 1.1 k / 100 = 12 behind the clamp"),
      wave("h3", "TX IN", "sine", 1e6, 4.0, {"probe": ("PROBE", "50")}, {"probe": Time(lambda t, emf, ctx: np.sign(emf) * np.maximum(0, np.abs(emf) - 1.25) / 2.0)},
           [W("vpp", 2.0, 3.5, "probe")], name="large pulse passes", why="two crossed pairs in series: 8 V p-p of drive less 2.5 V, halved into 50 ohm"),
      wave("h3", "TX IN", "sine", 1e6, 0.2, {"probe": ("PROBE", "50")}, {"probe": const(0.0)}, [W("vpp", 0, 0.03, "probe")], name="small signal blocked",
           why="0.4 V p-p never turns the diodes on: the transmitter's noise stays out"),
      listen("h4", "MON", const(0.0), [W("mean", -0.05, 0.08)], name="no coil"),
      bode("h5", "IN A", "OUT A", (1e4, 3e7, 15), 0.05, amp(1 + 240 / 27.0, 300e6, hp=5e3), [G(1e6, 0.8), G(1e7, 1.0), Gabs(3e7, 17, 21.5)], name="channel A"),
      bode("h5", "IN B", "OUT B", (1e4, 3e7, 15), 0.05, amp(1 + 240 / 27.0, 300e6, hp=5e3), [G(1e6, 0.8), G(1e7, 1.0), Gabs(3e7, 17, 21.5)], name="channel B"),
      bode("h6", "LOOP", "OUT", (3e2, 1e6, 25), 0.005, amp(101, 160e3, rin=5e4, hp=1.6e3), [G(2e4, 1.3), Corner(0.3, ref="max", side="hi"), Corner(0.3, ref="max", side="lo")],
           why="x101, 1.6 kHz to 160 kHz; the input is 50 k, so it sees the generator's open-circuit voltage")]
_H7 = amp(2.0 * 0.5, 35e6, rin=99.8)
T += [bode("h7", "DRIVE", {"inc": ("INC", "50"), "refl": ("REFL", "50")}, (1e4, 3e7, 15), 0.5, {"inc": _H7, "refl": _H7},
           [G(1e5, 0.8, "inc"), G(1e5, 0.8, "refl"), Check("REFL - INC at 1 MHz", lambda r: r.gain(1e6, "refl") - r.gain(1e6, "inc"), "dB", lo=-0.6, hi=0.6),
            Check("REFL - INC at 10 MHz", lambda r: r.gain(1e7, "refl") - r.gain(1e7, "inc"), "dB", lo=-1.5, hi=1.5)], name="DUT open",
           why="an open reflects everything: REFL / INC = +1"),
      bode("h7", "DRIVE", {"inc": ("INC", "50"), "refl": ("REFL", "50")}, (1e4, 1e7, 7), 0.5, {"inc": amp(1.0, 35e6, rin=74.9), "refl": amp(0.01, 35e6, rin=74.9)},
           [Check("REFL - INC at 1 MHz", lambda r: r.gain(1e6, "refl") - r.gain(1e6, "inc"), "dB", hi=-25)], name="DUT 50 ohm", hands=True,
           pre=("a 50 ohm SMA terminator on h7's DUT jack",), why="a match reflects nothing")]
_TANK = Lin(lambda f, load: 0.0071 * 30 / (1 + 1j * 30 * (f / 10.0e6 - 10.0e6 / f)) / 30)
T += [bode("h8", "SIG", {"o1": ("OUT 1", "50")}, list(np.linspace(7e6, 14e6, 71)), 2.0, {"o1": _TANK},
           [Check("tank 1 resonance", lambda r: r.peak("o1")[0], "Hz", lo=8.3e6, hi=11.7e6, fmt="%.4g"),
            Check("level at resonance", lambda r: r.peak("o1")[1], "dB", lo=-62, hi=-28)], name="tank 1 alone", refine=1,
           why="10 uH and about 25 pF: near 10 MHz, Q about 30, -43 dB into 50 ohm through 2.2 pF"),
      seq("h10", "current into 50 ohm", [dict(gen={"set": ("dc", 0, 0, v)}, wait=0.3, read={"mon@%g" % v: ("scope", "mon", "mean"), "psu@%g" % v: "psu"}) for v in (0.0, 0.05, 0.1)],
          lambda ctx: {"mon@0": 0.0, "mon@0.05": 0.25, "mon@0.1": 0.5, "psu@0": 0.05, "psu@0.05": 0.055, "psu@0.1": 0.06},
          [Num("mon@0", -0.03, 0.03, "V"), Num("mon@0.05", tol=0.05), Num("mon@0.1", tol=0.08), Num("supply step", 0.007, 0.014, "A")],
          gens={"set": "SET"}, scopes={"mon": ("MON", "1M")}, psu=True, derive=lambda v: {"supply step": v["psu@0.1"] - v["psu@0"]},
          pre=("a 50 ohm SMA terminator on h10's LD jack (never a laser for this test)",), why="100 mA per volt of SET: 10 mA makes 0.5 V across 50 ohm")]
_USE_H = H("use", "phmod")
T += [bode("h2", "IN", "OUT", (1e5, 3e7, 9), 0.1, amp(1 + 698 / 75.0, 400e6, rout=0.2), [G(1e6, 0.8), G(1e7, 1.2), G(3e7, 2.0)], load="50", name="enabled",
           host=(_USE_H, H("out", "IO1", 1)), pre=("h2 OUT straight into the scope's 50 ohm input: never open, never a tee",),
           why="THS3491 at 1 + 698 / 75 = 10.3; 0.1 V p-p in, 1 V p-p out: small enough to run continuously"),
      bode("h2", "IN", "OUT", [1e6, 1e7], 0.1, flat(-60), [Gabs(1e6, -120, -15)], load="50", name="powered down", host=(_USE_H, H("out", "IO1", 0)),
           why="IO1 low: PD holds it off"),
      seq("h9", "noise on and off", [dict(host=[_USE_H, H("out", "IO8", 0)], wait=0.3, read={"off": ("scope", "out", "rms")}),
                                     dict(host=[H("out", "IO8", 1)], wait=0.3, read={"on": ("scope", "out", "rms")}), dict(host=[H("out", "IO8", 0), H("safe")])],
          lambda ctx: {"off": 0.00015, "on": 0.0009}, [Num("on / off", 1.5, 1e4)], scopes={"out": ("OUT", "50")}, derive=lambda v: {"on / off": v["on"] / v["off"]},
          why="the avalanche junction's noise times 9.9, against the amplifier's own"),
      manual("h4", "coil driver", "A 10 ohm, 5 W resistor on the COIL terminal: IO6 high gives 0.46 A from USB's 4.6 V and 0.69 V on MON; IO7 reverses it.",
             kit=("10 ohm, 5 W resistor",)),
      manual("h8", "coupled tanks", "With DIP way 1 or 2 ON (1 pF, 2.2 pF between the tanks) the single peak splits in two; TUNE / PUMP's DC moves tank 2.")]

# =====================================================================================================
# IQ-MOD: a coherent I/Q transceiver and microwave physics
# =====================================================================================================
T = board("iq_mod", letter="q", name="IQ-MOD", title="quadrature", power="q10", socket=False, pmod="q3", quiescent=(0.004, 0.03), limit=1.6,
          setup=["every tile's slide switch DOWN (off)", "two 50 ohm terminators ready (q5's unused ports, q3's unused output)"],
          walk=[("q1", 120, 240), ("q2", 180, 330), ("q3", 15, 140), ("q4", 50, 85), ("q6", 45, 90), ("q7", 0.02, 6), ("q8", 3, 14)],
          inspect=["q1 (ADL5375), q2 (ADL5380), q6 (AD8318): LFCSP pin-1 dots; q3: the MAX2871's.",
                   "q8: the MAX2659 (1.5 x 1.0 mm) and the two 1.1 x 0.9 mm SAW filters sit square on their pads (three footprints made from JLCPCB's drawings).",
                   "q11: U1101 (SKY13370, 1.5 mm DFN).  q5: the two TDK couplers, their marks at opposite ends.",
                   "q7: U702 (ADL5611, SOT-89) tab; q4: the QPL9547's dot.  q9: a clean one-turn loop, nothing near it.",
                   "The Pmod plug hangs off the bottom edge under q3."])
_Q6 = {-40: 0.72, -20: 0.495, 0: 0.27}
T += [seq("q6", "volts against power at 20 MHz", [dict(gen={"in": ("sine", 20e6, dbm_vpp(p), 0.0)}, wait=0.2, read={"%d dBm" % p: ("scope", "out", "mean")}) for p in (-40, -20, 0)],
          lambda ctx: {"%d dBm" % p: v for p, v in _Q6.items()},
          [Num("slope", 8.5, 14.0, "mV/dB"), Num("0 dBm", 0.19, 0.37, "V")], gens={"in": "IN"}, scopes={"out": ("OUT", "1M")},
          derive=lambda v: {"slope": 1e3 * (v["-40 dBm"] - v["0 dBm"]) / 40.0}, why="AD8318: -25 mV/dB at the chip, 0.45 of it at the jack")]
_USE_Q = H("use", "iq_mod")
_REFG = {"ref": ("square", 25e6, 1.5, 0.75)}
_QPRE = ("q3's slide switch UP", "a 50 ohm terminator on q3's other output")
for f0 in (915e6, 2440e6):
    T += [spec("q3", "OUT A+", (f0 - 5e6, f0 + 5e6), _synth(f0), [SpecPeakF(f0, 4e6, 60e3), SpecPeak(f0, 4e6, -6, 9)], name="OUT A+ at %g MHz" % (f0 / 1e6),
               gens={"ref": "REF IN"}, stim=_REFG, host=(_USE_Q, H("max2871_set", f0, 3, key="locked")), pre=_QPRE,
               why="the generator's 25 MHz square (0 to 3 V at the unterminated jack) is the reference")]
T += [spec("q1", "RF OUT", (910e6, 920e6), _synth(915e6, -6.0), [SpecPeak(915e6, 4e6, -18, 4)], name="carrier from DC on I", gens={"ref": ("q3", "REF IN"), "i": "I IN"},
           stim=dict(_REFG, i=("dc", 0, 0, 0.5)), host=(_USE_Q, H("max2871_set", 915e6, 1)),
           pre=("an SMA cable from q3 OUT A+ to q1 LO IN", "a 50 ohm terminator on q3 OUT A-", "q1's and q3's slide switches UP"),
           why="0.5 V on I: a carrier a few dB under the 0 dBm full scale"),
      seq("q2", "the loop: q3, q1, q2", [dict(host=[_USE_Q, H("max2871_set", 915e6, 1)], gen={"ref": ("square", 25e6, 1.5, 0.75), "i": ("sine", 1e6, 0.2, 0.0)}, wait=0.5,
                                              read={"I": ("scope", "i", "tone", 1e6), "Q": ("scope", "q", "tone", 1e6)})],
          lambda ctx: {"I": 0.05, "Q": 0.03}, [Num("root sum square of I and Q", 0.006, 2.0, "V")], gens={"ref": ("q3", "REF IN"), "i": ("q1", "I IN")},
          scopes={"i": ("I OUT", "50"), "q": ("Q OUT", "50")}, derive=lambda v: {"root sum square of I and Q": math.hypot(v["I"], v["Q"])},
          pre=("SMA cables: q3 OUT A+ to q1 LO IN, q3 OUT A- to q2 LO IN, q1 RF OUT to q2 RF IN", "q1's, q2's and q3's slide switches UP"),
          why="a 1 MHz tone on I goes up to 915 MHz and comes back down on the same LO: one coherent radio"),
      seq("q7", "noise through the LNA", [dict(host=[_USE_Q, H("out", "IO6", 0)], wait=0.3, read={"off": ("sa", 1.0e9, 1.1e9)}),
                                          dict(host=[H("out", "IO6", 1)], wait=0.3, read={"on": ("sa", 1.0e9, 1.1e9)}), dict(host=[H("out", "IO6", 0), H("safe")])],
          lambda ctx: {"off": -92.0, "on": -78.0}, [Num("rise", 5.0, 50.0, "dB")], ports={"SA": ("q4", "OUT")}, derive=lambda v: {"rise": v["on"] - v["off"]},
          pre=("an SMA cable from q7 OUT to q4 IN", "q4's and q7's slide switches UP"), why="15-30 dB of excess noise, lifted 19.5 dB by q4 over the analyzer's floor")]
T += [s21("q4", "IN", "OUT", _F3, table([(5e7, 22), (5e8, 21), (1e9, 19.5), (2.4e9, 16), (6e9, 9)]), [Gabs(1e9, 15, 23.5), Gabs(2.4e9, 11, 21)], power=-30.0,
          pre=("q4's slide switch UP",)),
      s21("q5", "IN", "OUT", _F3, flat(-0.4), [Gabs(1e9, -1.5, 0.1), Gabs(2.4e9, -2.5, 0.1)], name="through", pre=("50 ohm terminators on q5 FWD and REFL",)),
      s21("q5", "IN", "FWD", _F3, flat(-25), [Gabs(1e9, -29, -21), Gabs(2.4e9, -29, -20)], name="forward coupling",
          pre=("50 ohm terminators on q5 OUT and REFL",)),
      s21("q5", "IN", "REFL", _F3, flat(-45), [Gabs(1e9, -90, -36)], name="directivity", pre=("50 ohm terminators on q5 OUT and FWD",)),
      s21("q8", "ANT", "OUT", _RFF, table([(1.0e9, -40), (1.5e9, -20), (1.56e9, 17), (1.575e9, 19), (1.606e9, 17), (1.66e9, -20), (2.6e9, -40)]),
          [Gabs(1.575e9, 13, 23.5), Gabs(1.1e9, -95, -15), Gabs(2.4e9, -95, -15)], power=-40.0,
          pre=("q8's slide switch UP", "ANT carries 3.3 V DC: fine for the 8720ES's port, NOT for a NanoVNA without a DC block"),
          why="SAW, MAX2659, SAW"),
      s21("q9", "IN", "OUT", _F3, flat(-0.5), [Gabs(1e9, -1.5, 0.2), Gabs(3e9, -2.5, 0.2)]),
      s21("q11", "RFC", "RF1", _F3, flat(-0.8), [Gabs(2.5e9, -2.5, -0.2)], name="RFC to RF1, on", host=(_USE_Q, H("rf_switch", 1)),
          pre=("a 50 ohm terminator on q11 RF2",)),
      s21("q11", "RFC", "RF1", _F3, flat(-31), [Gabs(2.5e9, -90, -20)], name="RFC to RF1, off", host=(_USE_Q, H("rf_switch", 2)),
          pre=("a 50 ohm terminator on q11 RF2",))]

ORDER = ["amod_p", "amod_a", "amod_n", "rf_mod", "amod_c", "phmod", "iq_mod", "amod_m", "amod_b"]
