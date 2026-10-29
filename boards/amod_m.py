"""AMOD-M: motors, rev A (Prompt 19).  Sixteen cells, four layers, USB-C power on m1 as AMOD-A's a1 and a motor supply
of 5-16 V on m2 (a barrel jack), with the USB's 5 V joining it through a Schottky.  A brushed DC motor with its
encoder (DRV8251A, the FPGA's PWM, the current and the back-EMF on jacks), a stepper (two DRV8251A), and
the actuators whose command comes from a DAC (a servo, a solenoid with its flyback chosen by a jumper, a DC-coupled
power amplifier for a voice coil or an electromagnet, a buck stage the FPGA closes the loop on); the sensors those loops
need (a linear hall sensor, a reflective optical sensor, a load cell's amplifier).  PLAN.md section 14 has the
decisions; the parts research of 2026-10-28 the choices.

Jason, Prompt 19: "motor drivers and mechanical servo-type feedback.  DC motor, stepper motor, 3-pole BLDC motor ...
along with encoders or magnetic back reaction or some other fast mechanical feedback."  The brushless half is AMOD-B.

L1 the parts and the drawn wires, L2 ground, L3 the rails (+5 V under the board; -5 V in the gutters under rows 0 and 2
and down the left margin; +3.3 V in the gutter under row 1), L4 ground with the motor rail VMOT (a 1.6 mm track along the
top margin and down the gutter between columns 1 and 2, which every motor tile taps), the Pmod lines and the back-side text.  Every tile
with a +5 V load has the standard header (tiles.power_header): a slide switch and a P-FET; VMOT itself is not switched.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, HERE)
import tiles as T
from tiles import Tile, power_header, HDR_VS
import geometry as G
from amod_a import power_tile

STEM = "amod_m"
LAYERS = 4
BUS_X = 50.0                    # board x of the VMOT track on the back, the gutter between columns 1 and 2
BUS_TOP = 6.75                  # board y of its run along the top margin from m2
BUS_END = 87.0                  # board y of its last tap (m3's), where it ends
W = 0.25
WP = 1.0                        # VMOT on the front inside a tile
VM = "/VMOT"                    # the motor rail, a board-wide net


def rail(t, net, pt, gutter):
    """A rail from a point in the tile to its strip on L3: a via at the point, the back to a via in the gutter at the same
    x (gutter: "below" 20.5, "above" -0.75)."""
    y = {"below": 20.5, "above": -0.75}[gutter]
    t.wire(net, [pt, (pt[0], y)], layer="B.Cu", silk=False)
    t.via(net, pt[0], y)


def vmot_tap(t, y, x_to, n=2):
    """VMOT from the bus on the back: n vias on the bus at board x BUS_X (local x bx), 0.9 mm apart from y, and a 1.5 mm
    track on the back from them to vias at local x x_to, where the tile's front VMOT starts.  Returns the local bus x."""
    bx = BUS_X - t.x0
    for k in range(n):
        yy = y + 0.9 * k
        t.via(VM, bx, yy)
        t.via(VM, x_to, yy)
        t.wire(VM, [(bx, yy), (x_to, yy)], width=1.0, layer="B.Cu", silk=False)
    return bx


# ------------------------------------------------------------------------------------------------------------ m1 --
def tile_m1():
    return power_tile("m1", sections=["Motors"])


# ------------------------------------------------------------------------------------------------------------ m2 --
def tile_m2():
    """The motor supply, one cell at the right edge: a 5.5 / 2.1 mm barrel jack (its face at the edge, in the cell's
    bottom-right quarter; no screw terminal, whose place the board's rubber foot takes: bare leads want a barrel-to-
    terminal adapter) through an SS34 into VMOT, the USB's +5 V through another; an SMBJ16A (26 V clamp: under the buck's 30 V FETs and the TPS28225's
    27 V) and 220 uF on VMOT, which also soak up a motor's braking energy (the Schottkys stop it reaching the supply); a
    green LED; VMOT / 16 (15 k / 1 k) through 49.9 ohm on the VM jack (top-left).  VMOT leaves on the back down the
    gutter on the tile's left and along the gutter under row 0 to the bus at x 50, which every motor tile taps.  The
    electrolytic lies in the top-right quarter, the TVS stands down the left edge, the two Schottkys (cathodes left) in
    the middle, the divider under the jack."""
    t = Tile("m2", "motor supply", [(3, 0)], supply=None, subtitle="5-16 V in", sections=["Motors"])
    t.jack("TL", "VM", "VMJ", "out", "", silk="VM /16")
    t.pwr_flags = [VM, "VEXT"]
    jdc = t.add("J", "DC005", "5-16V", 17.15, 13.35, 180, {"1": "VEXT", "2": "GND", "3": "GND"}, hide_value=True)
    ce = t.add("C", "ELCO220U", "220u", 13.0, 4.9, 0, {"1": VM, "2": "GND"}, label=None)                 # pad 1 (+) left
    dz = t.add("D", "SMBJ16A", "SMBJ16A", 2.6, 14.0, 270, {"1": VM, "2": "GND"}, label=None)              # K up
    dx = t.add("D", "SS34", "SS34", 8.7, 11.3, 0, {"1": VM, "2": "VEXT"}, label=None)                     # K left
    du = t.add("D", "SS34", "SS34", 8.7, 15.0, 0, {"1": VM, "2": "+5V"}, label=None)
    ro = t.add("R", "R0402 49.9R", "49.9", 0.6, 6.4, 90, {"1": "VD", "2": "VMJ"}, label=None)              # pad 1 down
    rd2 = t.add("R", "R0402 1k", "1k", 0.6, 9.0, 270, {"1": "VD", "2": "GND"}, label=None)                 # pad 1 up
    rd1 = t.add("R", "R0402 15k", "15k", 2.6, 9.3, 180, {"1": VM, "2": "VD"}, label=None)                 # pad 1 right
    led = t.add("LED", "LED_G", "VM", 4.0, 18.9, 0, {"1": "GND", "2": "LA"}, label=None)                  # K left
    rl = t.add("R", "R0402 4.7k", "4.7k", 7.3, 18.9, 0, {"1": "LA", "2": VM}, label=None)
    # VEXT: the jack's centre pin up x 13 to the upper Schottky's anode
    t.wire("VEXT", [(jdc, "1"), (13.0, 15.7), (13.0, 11.3), (dx, "2")], width=WP)
    # VMOT: the cathodes and the TVS joined along x 6.7 and y 11.3, up x 6.7 and along y 8.9 to the electrolytic
    t.wire(VM, [(du, "1"), (6.7, 11.3), (dx, "1")], width=WP)
    t.wire(VM, [(6.7, 11.3), (dz, "1")], width=WP)
    t.wire(VM, [(6.7, 11.3), (6.7, 9.5), (10.3, 9.5), (ce, "1")], width=WP)
    t.wire(VM, [(du, "1"), (6.7, 17.4), (rl, "2")], width=W)
    t.wire(VM, [(6.7, 9.5), (rd1, "1")], width=W)
    # the bus: two vias between the Schottkys, the back right to x 9.6 (clear of the jack's legs), up into the top margin
    # and along it at board y 6.75 (under the back's title, over no hole) to the gutter between columns 1 and 2 at x 50,
    # and down that gutter to the last tap (m8's, at BUS_END); every motor tile's tap is a via on it
    bx = BUS_X - t.x0
    for xv in (5.9, 7.5):
        t.via(VM, xv, 13.15)
    t.wire(VM, [(5.9, 13.15), (7.5, 13.15)], width=WP)
    t.wire(VM, [(5.9, 13.15), (9.6, 13.15), (9.6, BUS_TOP - t.y0), (bx, BUS_TOP - t.y0), (bx, BUS_END - t.y0)], width=1.6, layer="B.Cu", silk=False)
    # +5 V: the lower Schottky's anode from the pour
    t.via("+5V", 10.7, 16.75)
    t.wire("+5V", [(du, "2"), (10.7, 16.75)], width=WP)
    # VM / 16: up the left edge to the jack between its left legs
    t.wire("VD", [(rd1, "2"), (rd2, "1")], width=W)
    t.wire("VD", [(rd2, "1"), (ro, "1")], width=W)
    t.wire("VMJ", [(ro, "2"), (0.6, 4.75), ("J%d01" % t.idx, "1")])
    for ref_, pad, pt in ((rd2, "2", (0.6, 10.6)), (led, "1", (2.6, 18.3)), (dz, "2", (2.6, 18.3)), (ce, "2", (17.9, 6.6)),
                          (jdc, "2", (20.15, 19.0)), (jdc, "3", (19.8, 9.3))):
        t.gnd_stub(ref_, pad, pt, sym=(0, 0))
    t.wire("LA", [(led, "2"), (rl, "1")], width=W)
    t.titles.append("Motor supply")
    t.result = "VMOT = the larger of the barrel jack or terminal (5-16 V) and USB 5 V, each less a Schottky's 0.3-0.5 V; VM jack VMOT / 16"
    t.notes = ["Barrel jack (centre +) or terminal, 5-16 V: each through an SS34 into VMOT, as is USB's 5 V, so VMOT is about 4.6 V",
               "with no supply.  SMBJ16A and 220 uF on VMOT take the braking energy a motor returns.  VM: VMOT / 16 at high impedance."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ m3 --
def tile_m3():
    """A brushed DC motor with its encoder, two cells along the bottom, the Pmod plug in the margin under the left cell.
    A DRV8251A (4.1 A, its undervoltage lockout at 4.45 V at most, so USB's 5 V through m2's Schottky runs it) from VMOT:
    IN1 on Pmod IO7 and IN2 on IO1 (pulled down in the chip: the motor coasts with no FPGA, and sleeps after 1 ms), drive
    / brake (IPROPI continuous) or drive / coast (the back-EMF shows in the off time) as the gateware chooses; VREF 2.0 V
    (1.5 k / 1 k from the switched 5 V) with 620 ohm on IPROPI: a 2 A limit, 0.98 V/A, and the tile's switch takes the
    limit to zero.  An OPA2171 on +-5 V: one half buffers IPROPI onto I through 49.9 ohm, the other takes the terminal
    voltage, (M1 - M2) / 13 (13 k / 1 k), onto V.  The motor and its hall encoder on a 6-way JST PH (2.0 mm) in the
    bottom margin: 1 M1, 2 GND, 3 A, 4 B, 5 3.3 V (a TPS7A2033 of its own, so A and B are 3.3 V logic), 6 M2 (an N20
    with a ZH plug needs a ZH-to-PH lead); A on IO5, B on IO6 (the encoder's pull-ups, or the FPGA's).  The driver
    turned 270 in the left cell (its logic up, VM out to the left, OUT1 and OUT2 down and right to the PH); the op amp in
    the right cell's top-right quarter beside I, its two 13 k at the PH, its inputs up the cell's right edge; V on the
    left jack, reached along the top."""
    t = Tile("m3", "DC motor", [(0, 3), (1, 3)], supply="+-5 V, VMOT", subtitle="DRV8251A", sections=["Motors"])
    t.jack("TL0", "V", "VJ", "out", "", silk="V /13")
    t.jack("TL1", "I", "IJ", "out", "", silk="I 1V/A")
    power_header(t)
    WS = 0.2
    WM = 0.8                                                  # the motor's current
    bx = BUS_X - t.x0
    # ---- the driver, turned 270 in the left cell
    D = drv8251(t, "M", 14.0, 11.6, "/PMOD7", "/PMOD1", "IP", "VR", "M1", "M2", rtop=("R0402 1.5k", "1.5k"))
    t.route("VS", [HDR_VS, (D["rv1"], "1")], width=0.3)
    # VMOT: from a via on the bus (10 uF beside it) along the back at y 14.2 to the driver's VM via
    cb = t.add("C", "C0805 10uF", "10u", 40.6, 13.0, 90, {"1": VM, "2": "GND"}, label=None)              # pad 1 down
    t.via(VM, bx, BUS_END - t.y0)
    t.wire(VM, [(bx, BUS_END - t.y0), (cb, "1")], width=WM)
    t.gnd_stub(cb, "2", (40.6, 10.9), sym=(0, 0))
    t.wire(VM, [(bx, BUS_END - t.y0), (41.25, 14.2), D["vm"]], width=WM, layer="B.Cu", silk=False)
    # the motor: OUT2 along y 16.4 and down to the PH's pin 6, OUT1 along y 17.6 and down to its pin 1
    ph = t.add("J", "PH6V", "motor", 23.5, 24.4, 0, {"1": "M1", "2": "GND", "3": "/PMOD5", "4": "/PMOD6", "5": "E3V3", "6": "M2"}, hide_value=True)
    t.wire("M2", [D["out2"], (D["out2"][0], 16.4), (33.5, 16.4), (ph, "6")], width=WM)
    t.wire("M1", [D["out1"], (D["out1"][0], 17.6), (23.5, 17.6), (ph, "1")], width=WM)
    t.gnd_stub(ph, "2", (25.5, 22.6), sym=(0, 0))
    # ---- the op amp: A buffers IPROPI onto I beside it, B the difference of M1 and M2 onto V
    ua = t.add("U", "OPA2171", "OPA2171", 36.4, 5.0, 0, {"1": "AO", "2": "AO", "3": "IP", "4": "-5V", "5": "BP", "6": "BN", "7": "BO", "8": "+5V"},
               hide_value=False, label=None)
    roa = t.add("R", "R0402 49.9R", "49.9", 31.2, 4.75, 0, {"1": "IJ", "2": "AO"}, label=None)
    t.wire("AO", [(ua, "1"), (32.5, 3.095), (32.5, 4.365), (ua, "2")], width=W)
    t.wire("AO", [(roa, "2"), (32.5, 4.75), (32.5, 4.365)], width=W)
    t.wire("IJ", [(roa, "1"), ("J%d02" % t.idx, "1")])
    rf = t.add("R", "R0402 1k", "1k", 40.9, 5.0, 270, {"1": "BO", "2": "BN"}, label=None)                   # pad 1 up
    rob = t.add("R", "R0402 49.9R", "49.9", 40.9, 2.4, 270, {"1": "VJ", "2": "BO"}, label=None)
    rb2 = t.add("R", "R0402 1k", "1k", 37.4, 20.7, 0, {"1": "GND", "2": "BP"}, label=None)
    t.wire("BO", [(ua, "7"), (40.2, 4.365), (40.2, 4.49), (rf, "1")], width=W)
    t.wire("BO", [(rf, "1"), (rob, "2")], width=W)
    t.wire("BP", [(rb2, "2"), (37.91, 21.9)], width=WS)
    t.gnd_stub(rb2, "1", (35.9, 20.7), sym=(0, 0))
    t.wire("VJ", [(rob, "1"), (40.9, -0.35), (9.4, -0.35), (9.4, 4.75), ("J%d01" % t.idx, "1")], width=W, silk=False)
    cvp = t.add("C", "C0402 100nF", "100n", 37.2, 1.75, 0, {"1": "GND", "2": "+5V"}, label=None)
    t.wire("+5V", [(ua, "8"), (38.875, 1.75), (cvp, "2")], width=W)
    t.via("+5V", 39.8, 1.75)
    t.wire("+5V", [(38.875, 1.75), (39.8, 1.75)], width=W)
    t.gnd_stub(cvp, "1", (36.0, 1.75), sym=(0, 0))
    cvn = t.add("C", "C0402 100nF", "100n", 33.4, 8.9, 0, {"1": "-5V", "2": "GND"}, label=None)
    t.wire("-5V", [(ua, "4"), (32.92, 6.905), (cvn, "1")], width=W)
    t.gnd_stub(cvn, "2", (34.6, 8.9), sym=(0, 0))
    t.via("-5V", 32.0, 8.9)
    t.wire("-5V", [(cvn, "1"), (32.0, 8.9)], width=W)
    t.wire("-5V", [(32.0, 8.9), (32.0, -1.1)], layer="B.Cu", silk=False)
    t.via("-5V", 32.0, -1.1)
    t.route("IP", [(D["rip"], "1"), (ua, "3")], width=WS)
    # the difference amp's two 13 k beside the PH in the margin: M2 straight from pin 6, M1 from pin 1 on the back; their
    # outputs up the cell's right edge (BP at x 38.6, BN at x 39.4) to the op amp
    rb1 = t.add("R", "R0402 13k", "13k", 37.4, 21.9, 0, {"1": "M1", "2": "BP"}, label=None)
    rb3 = t.add("R", "R0402 13k", "13k", 37.4, 23.4, 0, {"1": "M2", "2": "BN"}, label=None)
    t.wire("M2", [(ph, "6"), (34.6, 24.4), (35.6, 23.4), (rb3, "1")], width=WS)
    t.via("M1", 36.0, 21.7)
    t.wire("M1", [(ph, "1"), (23.5, 21.7), (36.0, 21.7)], width=WS, layer="B.Cu", silk=False)
    t.wire("M1", [(36.0, 21.7), (rb1, "1")], width=WS)
    t.wire("BP", [(rb1, "2"), (38.6, 21.9), (38.6, 7.6), (ua, "5")], width=WS)
    t.wire("BN", [(rb3, "2"), (39.4, 23.4), (39.4, 8.0), (40.3, 8.0), (40.3, 5.635), (ua, "6")], width=WS)
    t.wire("BN", [(40.3, 5.635), (rf, "2")], width=WS)
    # the encoder's 3.3 V: a TPS7A2033 from +5 V in the margin right of the PH, turned 180 (OUT and NC to the left; IN,
    # GND and EN to the right, IN and EN joined round the ground's via between them), out on the back to the PH's pin 5
    ul = t.add("U", "TPS7A2033", "3.3V", 43.0, 24.9, 180, {"1": "+5V", "2": "GND", "3": "+5V", "5": "E3V3"}, hide_value=False, label=None)
    cli = t.add("C", "C0603 1uF", "1u", 47.1, 24.9, 90, {"1": "GND", "2": "+5V"}, label=None)             # pad 2 up
    clo = t.add("C", "C0603 1uF", "1u", 39.7, 25.0, 90, {"1": "GND", "2": "E3V3"}, label=None)            # pad 2 up
    t.gnd_stub(ul, "2", (45.3, 24.9), sym=(0, 0))
    t.wire("+5V", [(ul, "1"), (46.1, 25.85), (46.1, 23.95), (ul, "3")], width=W)
    t.wire("+5V", [(46.1, 23.95), (47.1, 23.95), (cli, "2")], width=W)
    t.via("+5V", 47.1, 22.9)
    t.wire("+5V", [(cli, "2"), (47.1, 22.9)], width=W)
    t.gnd_stub(cli, "1", (48.3, 25.675), sym=(0, 0))
    t.via("E3V3", 40.85, 23.0)
    t.wire("E3V3", [(ul, "5"), (40.85, 25.85), (40.85, 23.0)], width=W)
    t.wire("E3V3", [(clo, "2"), (40.85, 24.225)], width=W)
    t.gnd_stub(clo, "1", (38.5, 25.775), sym=(0, 0))
    t.wire("E3V3", [(40.85, 23.0), (31.5, 23.0), (ph, "5")], width=0.3, layer="B.Cu", silk=False)
    # ---- the Pmod plug (as AMOD-C's c9): JLCPCB's pad p is Pmod pin (13 - p)
    pm = t.add("J", "PMOD", "Pmod", 2.97, 24.25, 0, {"1": "/PMOD_VCC", "2": "/PMOD_VCC", "3": "GND", "4": "GND", "5": "/PMOD8", "6": "/PMOD4",
                                                      "7": "/PMOD7", "8": "/PMOD3", "9": "/PMOD6", "10": "/PMOD2", "11": "/PMOD5", "12": "/PMOD1"}, hide_value=True)
    t.wire("/PMOD_VCC", [(pm, "1"), (pm, "2")], layer="B.Cu", silk=False)
    # encoder A, B on the back along the bottom edge into the plug's lower row (pads 11 and 9)
    t.wire("/PMOD5", [(ph, "3"), (27.5, 26.05), (10.4, 26.05), (9.32, 25.52), (pm, "11")], layer="B.Cu", silk=False, width=WS)
    t.wire("/PMOD6", [(ph, "4"), (29.5, 27.1), (6.78, 27.1), (pm, "9")], layer="B.Cu", silk=False, width=WS)
    # IO8 (m4's coil B IN2) from the margin lane's via along the channel between the rows into pad 5
    t.via("/PMOD8", -5.35, 24.25)
    t.wire("/PMOD8", [(-5.35, 24.25), (1.25, 24.25), (pm, "5")], width=0.2, silk=False)
    # IN2 (IO1) and IN1 (IO7) from the driver's vias on the back, down between the jack and the driver: IN2 up, over
    # IN1's via and down the outer lane (x 8.8) into pad 12 from above; IN1 down the inner lane (x 9.4) to the channel
    t.wire("/PMOD1", [D["in2"], (D["in2"][0], 6.3), (8.8, 6.3), (8.8, 21.0), (9.32, 21.4), (pm, "12")], width=WS, layer="B.Cu", silk=False)
    t.via("/PMOD7", 11.6, 24.25)
    t.wire("/PMOD7", [D["in1"], (9.4, D["in1"][1]), (9.4, 20.0), (11.6, 20.0), (11.6, 24.25)], width=WS, layer="B.Cu", silk=False)
    t.wire("/PMOD7", [(11.6, 24.25), (4.85, 24.25), (pm, "7")], width=0.2, silk=False)
    t.titles.append("DC motor")
    t.result = "the motor at the duty and direction IO7 (IN1) and IO1 (IN2) set; I = its current, 0.98 V/A; V = its terminal voltage / 13 (back-EMF in coast)"
    t.notes = ["DRV8251A from VMOT: IN1 (IO7) and IN2 (IO1) choose forward, reverse, brake (both high) or coast (both low: then sleep).",
               "IPROPI (620 ohm, 0.98 V/A, 2 A limit) buffered onto I; (M1 - M2) / 13 onto V.  Encoder A on IO5, B on IO6, its own 3.3 V."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


def drv8251(t, name, x, y, in1, in2, ip, vref, out1, out2, ws=0.2, rtop=("R0402 3.9k", "3.9k")):
    """A DRV8251A turned 270 at (x, y): its logic pins along the top (4 VREF, 3 IN1, 2 IN2, 1 IPROPI at x - 1.905 ... +
    1.905, y - 2.65), its power pins along the bottom (5 VM, 6 OUT1, 7 GND, 8 OUT2, y + 2.65), the thermal pad between.
    IN1 and IN2 to vias 2.0 mm above the pins (for the Pmod lines on the back), VREF up to a divider from VS (rtop / 1 k;
    3.9 k: 1.0 V, a 1 A limit), IPROPI up to 620 ohm to ground (0.98 V/A); VM out of the left side to a via (VMOT arrives on the back)
    with 100 nF; GND into the pad, the pad's vias.  Returns the points the tile wires on from."""
    u = t.add("U", "DRV8251A", "DRV8251A", x, y, 270, {"1": ip, "2": in2, "3": in1, "4": vref, "5": VM, "6": out1, "7": "GND",
                                                       "8": out2, "9": "GND"}, hide_value=False, label=None)
    for (dx, dy) in ((-0.8, -0.6), (0.8, -0.6), (-0.8, 0.6), (0.8, 0.6)):
        t.gnd_stub(u, "9", (x + dx, y + dy), sym=(0, 0), width=0.3)
    t.wire("GND", [(u, "7"), (x + 0.635, y + 1.2)], width=0.3, silk=False)
    top = y - 3.45
    t.via(in1, x - 0.635, top - 1.1)
    t.wire(in1, [(u, "3"), (x - 0.635, top - 1.1)], width=ws)
    t.via(in2, x + 0.635, top - 1.1)
    t.wire(in2, [(u, "2"), (x + 0.635, top - 1.1)], width=ws)
    rv2 = t.add("R", "R0402 1k", "1k", x - 1.905, top - 1.25, 90, {"1": vref, "2": "GND"}, label=None)       # pad 1 down
    rv1 = t.add("R", rtop[0], rtop[1], x - 3.4, top - 0.74, 0, {"1": "VS", "2": vref}, label=None)
    t.wire(vref, [(u, "4"), (rv2, "1")], width=ws)
    t.wire(vref, [(rv1, "2"), (rv2, "1")], width=ws)
    t.gnd_stub(rv2, "2", (x - 1.905, top - 2.6), sym=(0, 0))
    rip = t.add("R", "R0402 620R", "620", x + 1.905, top - 1.25, 90, {"1": ip, "2": "GND"}, label=None)       # pad 1 down
    t.wire(ip, [(u, "1"), (rip, "1")], width=ws)
    t.gnd_stub(rip, "2", (x + 1.905, top - 2.6), sym=(0, 0))
    t.via(VM, x - 3.2, y + 2.6)
    t.wire(VM, [(u, "5"), (x - 3.2, y + 2.6)], width=0.5)
    cvm = t.add("C", "C0402 100nF", "100n", x - 3.2, y + 1.2, 90, {"1": VM, "2": "GND"}, label=None)          # pad 1 down
    t.wire(VM, [(x - 3.2, y + 2.6), (cvm, "1")], width=0.4)
    t.gnd_stub(cvm, "2", (x - 3.2, y - 0.2), sym=(0, 0))
    return dict(u=u, rip=rip, rv1=rv1, vm=(x - 3.2, y + 2.6), in1=(x - 0.635, top - 1.1), in2=(x + 0.635, top - 1.1),
                out1=(x - 0.635, y + 3.45), out2=(x + 1.905, y + 3.45), ip=(x + 1.905, top - 0.74))


# ------------------------------------------------------------------------------------------------------------ m4 --
def tile_m4():
    """A bipolar stepper, two cells above m3: two DRV8251A (4.1 A, IN1 / IN2: the gateware makes EN / PH or microsteps
    from them) from VMOT, coil A's IN1 on Pmod IO2 and IN2 on IO3, coil B's IN1 on IO4 and IN2 on IO8 (each pulled down
    in the chip; the assignment is the one whose lanes to the plug never cross).  VREF 1.0 V from the switched 5 V with
    620 ohm on each IPROPI: 1 A per coil, and the tile's switch takes the limit to zero; each IPROPI through 10 k onto IA,
    IB (0.98 V/A, read at high impedance; the 10 k keeps a 50 ohm input from upsetting the regulation).  The motor on a
    4-way JST XH (A+, A-, B+, B-) between the drivers at the bottom, each OUT2 on its coil's + pin; VMOT from the bus on the back to each driver's VM.
    Each driver turned 270, A's in the left cell, B's in the right; the Pmod lines go up from vias above each driver to
    the gutter over the tile, along it to the left margin and down it to the plug under m3 (BACK_WIRES)."""
    t = Tile("m4", "stepper", [(0, 2), (1, 2)], supply="+5 V, VMOT", subtitle="2 x DRV8251A", sections=["Motors"])
    t.jack("TL0", "IA", "IAJ", "out", "", silk="IA 10K")
    t.jack("TL1", "IB", "IBJ", "out", "", silk="IB 10K")
    power_header(t)
    WM = 0.6
    bx = BUS_X - t.x0
    A = drv8251(t, "A", 13.0, 11.8, "/PMOD2", "/PMOD3", "IPA", "VRA", "A1", "A2")
    B = drv8251(t, "B", 35.0, 11.8, "/PMOD4", "/PMOD8", "IPB", "VRB", "B1", "B2")
    # VMOT: from a via on the bus (a 10 uF beside it on the front) along the back at y 14.4 to each driver's VM via
    cb = t.add("C", "C0805 10uF", "10u", 40.3, 16.4, 0, {"1": "GND", "2": VM}, label=None)
    t.via(VM, bx, 14.4)
    t.wire(VM, [(bx, 14.4), (41.25, 15.2), (cb, "2")], width=WM)
    t.gnd_stub(cb, "1", (39.35, 18.0), sym=(0, 0))
    t.wire(VM, [(bx, 14.4), B["vm"], A["vm"]], width=WM, layer="B.Cu", silk=False)
    # the motor: the XH between the drivers, its body clear of m3's frame; each coil's OUT2 to its + pin and OUT1 to its
    # - pin (both coils turned round: a stepper only starts its sequence half a turn of the field on), so the leads nest
    # from below, the nearer output to the nearer pin
    xh = t.add("J", "XH4V", "stepper", 20.5, 16.5, 0, {"1": "A2", "2": "A1", "3": "B2", "4": "B1"}, hide_value=True)
    t.wire("A2", [A["out2"], (A["out2"][0], 18.3), (20.5, 18.3), (xh, "1")], width=WM)
    t.wire("A1", [A["out1"], (A["out1"][0], 19.3), (23.0, 19.3), (xh, "2")], width=WM)
    t.wire("B1", [B["out1"], (B["out1"][0], 18.3), (28.0, 18.3), (xh, "4")], width=WM)
    t.wire("B2", [B["out2"], (B["out2"][0], 19.3), (25.5, 19.3), (xh, "3")], width=WM)
    # IA, IB: each IPROPI through 10 k to its jack
    ria = t.add("R", "R0402 10k", "10k", 16.6, 6.4, 90, {"1": "IPA", "2": "IAJ"}, label=None)             # pad 1 down
    rib = t.add("R", "R0402 10k", "10k", 38.6, 6.4, 90, {"1": "IPB", "2": "IBJ"}, label=None)
    t.route("IPA", [(A["rip"], "1"), (ria, "1")], width=0.2)
    t.route("IPB", [(B["rip"], "1"), (rib, "1")], width=0.2)
    t.wire("IAJ", [(ria, "2"), (16.6, 3.0), (9.0, 3.0), (9.0, 4.75), ("J%d01" % t.idx, "1")], width=0.25)
    t.wire("IBJ", [(rib, "2"), (38.6, 3.0), (31.0, 3.0), (31.0, 4.75), ("J%d02" % t.idx, "1")], width=0.25)
    # VS: the drain to the two VREF dividers
    t.route("VS", [HDR_VS, (A["rv1"], "1")], width=0.3)
    t.route("VS", [(A["rv1"], "1"), (B["rv1"], "1")], width=0.3)
    t.titles.append("Stepper")
    t.result = "full, half or PWM microsteps at the rate the FPGA sets (IN1, IN2 per coil); IA, IB = the coil currents' size, 0.98 V/A, 1 A limit"
    t.notes = ["Two DRV8251A from VMOT: coil A IN1 on IO2, IN2 on IO3; coil B IN1 on IO4, IN2 on IO8 (both low: coast, then sleep).",
               "VREF 1.0 V and 620 ohm on IPROPI: 1 A limit, 0.98 V/A through 10 k onto IA and IB.  Stepper on the XH: A+, A-, B+, B-."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ m5 --
def tile_m5():
    """An RC servo, one cell: CMD (a DAC's pulse of 0 / +1 V, terminated in 49.9 ohm) through 10 k into a TLV3501 on the
    switched 5 V whose threshold is 0.49 V (47 k / 5.1 k), its 5 V output on a 3-pin header (S, +, -) that powers the servo
    from the same switched 5 V (10 uF beside it); the servo's ground returns through 0.05 ohm, read by an INA181A1 (x20:
    1 V/A) onto I through 49.9 ohm.  A 1-2 ms pulse every 20 ms from the DAC sets the angle; the current shows the load.
    The comparator and the INA181 stand in the top-right quarter, the header at its right edge, the shunt in the middle."""
    t = Tile("m5", "servo", [(2, 0)], supply="+5 V", subtitle="", sections=["Motors"])
    t.jack("TL", "CMD", "CMD", "in", "0/+1 V", silk="CMD 50R")
    t.jack("BR", "I", "IJ", "out", "", silk="I 1V/A")
    power_header(t)
    rt = t.add("R", "R0402 49.9R", "49.9", 4.75, 9.6, 270, {"1": "CMD", "2": "GND"}, label=None)       # pad 1 up, under the jack
    rin = t.add("R", "R0402 10k", "10k", 9.4, 4.75, 0, {"1": "CMD", "2": "CP"}, label=None)
    rr1 = t.add("R", "R0402 47k", "47k", 9.6, 2.6, 0, {"1": "VS", "2": "TH"}, label=None)
    rr2 = t.add("R", "R0402 5.1k", "5.1k", 11.9, 2.6, 0, {"1": "TH", "2": "GND"}, label=None)
    u = t.add("U", "TLV3501", "TLV3501", 13.0, 5.4, 0, {"1": "TH", "2": "GND", "3": "CP", "4": "VS", "5": "SIG", "6": "GND"}, hide_value=False, label=None)
    hdr = t.add("J", "HDR3", "servo", 17.6, 2.7, 0, {"1": "SIG", "2": "VS", "3": "SG"}, hide_value=True)
    cvs = t.add("C", "C0402 100nF", "100n", 9.6, 7.2, 0, {"1": "VS", "2": "GND"}, label=None)
    ina = t.add("U", "INA181A1", "INA181", 13.0, 9.6, 0, {"1": "IO", "2": "GND", "3": "SG", "4": "GND", "5": "GND", "6": "VS"}, hide_value=False, label=None)
    rs = t.add("R", "R1206 0.05R", "0.05", 8.3, 11.0, 0, {"1": "GND", "2": "SG"}, label=None)
    cb = t.add("C", "C0805 10uF", "10u", 8.0, 13.5, 0, {"1": "VS", "2": "GND"}, label=None)
    ro = t.add("R", "R0402 49.9R", "49.9", 10.6, 15.25, 0, {"1": "IO", "2": "IJ"}, label=None)
    t.wire("CMD", [("J%d01" % t.idx, "1"), (rin, "1")])
    t.wire("CMD", [("J%d01" % t.idx, "1"), (rt, "1")])
    t.gnd_stub(rt, "2", (4.75, 10.95), sym=(0, 0))
    t.wire("CP", [(rin, "2"), (10.4, 4.75), (10.4, 6.35), (u, "3")], width=W)
    t.wire("TH", [(rr1, "2"), (rr2, "1")], width=W)
    t.wire("TH", [(rr2, "1"), (11.39, 4.45), (u, "1")], width=W)
    t.gnd_stub(rr2, "2", (13.3, 2.6), sym=(0, 0))
    t.wire("GND", [(u, "2"), (13.0, 5.4), (13.0, 4.45), (u, "6")], width=W, silk=False)
    t.gnd_stub(u, "6", (15.2, 3.7), sym=(0, 0))
    t.wire("SIG", [(u, "5"), (15.4, 5.4), (16.3, 4.5), (16.3, 2.7), (hdr, "1")], width=W)
    t.wire("GND", [(ina, "4"), (ina, "5")], width=W, silk=False)
    t.gnd_stub(ina, "5", (15.5, 10.6), sym=(0, 0))
    t.gnd_stub(ina, "2", (10.5, 9.0), sym=(0, 0))
    t.wire("SG", [(rs, "2"), (11.0, 11.0), (ina, "3")], width=W)
    t.route("SG", [(rs, "2"), (hdr, "3")], width=0.4)
    t.gnd_stub(rs, "1", (5.8, 12.2), sym=(0, 0))
    t.gnd_stub(cvs, "2", (10.6, 8.1), sym=(0, 0))
    t.gnd_stub(cb, "2", (9.9, 12.6), sym=(0, 0))
    t.route("IO", [(ina, "1"), (ro, "1")], width=W)
    t.wire("IJ", [(ro, "2"), ("J%d02" % t.idx, "1")])
    # VS: the drain up to the bulk capacitor, the header, the comparator, the INA181 and the divider
    t.route("VS", [HDR_VS, (cb, "1")], width=0.4)
    t.route("VS", [(cb, "1"), (hdr, "2")], width=0.4)
    t.route("VS", [(hdr, "2"), (u, "4")], width=W)
    t.route("VS", [(u, "4"), (ina, "6")], width=W)
    t.route("VS", [(cvs, "1"), (rr1, "1")], width=W)
    t.route("VS", [(cvs, "1"), (cb, "1")], width=W)
    t.titles.append("Servo")
    t.result = "a servo at the angle a 1-2 ms pulse every 20 ms sets (CMD 0 / +1 V); I = the servo's current, 1 V/A"
    t.notes = ["CMD (0 / +1 V from a DAC) through 10 k into a TLV3501 (threshold 0.49 V) makes the 5 V pulse a servo wants; the servo's",
               "ground returns through 0.05 ohm and an INA181A1 (x20) puts 1 V/A on I.  Slew the angle and watch the current."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ m6 --
def tile_m6():
    """A solenoid's low-side switch, two cells at the top left: CMD (a DAC's pulse of 0 / +1 V, terminated in 49.9 ohm)
    through 10 k into a TLV3501 on the switched 5 V (threshold 0.49 V, as m5), its output through 49.9 ohm to an NCE6020AK's
    gate (60 V, 20 A, 40 mohm at 4.5 V; 100 k holds it off), the FET lying in the left cell with its tab (the drain) to
    the right.  The coil on a 2-way screw terminal at the top of the right cell (wires in from the top margin): VMOT on
    pin 2 from the bus beside it (10 uF), the drain on pin 1.  The flyback by jumper on a 1 x 3 header: 1-2 a B5819W from
    the drain to VMOT (slow decay: the current circulates at the diode's 0.4 V), 2-3 an SMAJ24A from the drain to ground
    (fast decay: the drain clamps near 30 V), no jumper the FET's own avalanche near 70 V.  The source returns through
    0.05 ohm, read by an INA181A1 (x20, on +5 V) onto I through 49.9 ohm (1 V/A); the drain through 5.1 k / 100 ohm onto
    VD through 49.9 ohm (the drain / 52).  The comparator above the FET as in m5, the shunt and the INA181 under it, the
    header, the clamps and the divider in the right cell's left half; the drain reaches the terminal on the back."""
    t = Tile("m6", "solenoid", [(0, 0), (1, 0)], supply="+5 V, VMOT", subtitle="NCE6020AK", sections=["Motors"])
    t.jack("TL0", "CMD", "CMD", "in", "0/+1 V", silk="CMD 50R")
    t.jack("TL1", "VD", "VDJ", "out", "", silk="VD /52")
    t.jack("BR1", "I", "IJ", "out", "", silk="I 1V/A")
    power_header(t)
    WD = 1.0                                                  # the coil's current
    bx = BUS_X - t.x0
    # ---- the comparator (as m5's) and the gate
    rt = t.add("R", "R0402 49.9R", "49.9", 4.75, 9.6, 270, {"1": "CMD", "2": "GND"}, label=None)       # pad 1 up, under the jack
    rin = t.add("R", "R0402 10k", "10k", 9.4, 4.75, 0, {"1": "CMD", "2": "CP"}, label=None)
    rr1 = t.add("R", "R0402 47k", "47k", 9.6, 2.6, 0, {"1": "VS", "2": "TH"}, label=None)
    rr2 = t.add("R", "R0402 5.1k", "5.1k", 11.9, 2.6, 0, {"1": "TH", "2": "GND"}, label=None)
    u = t.add("U", "TLV3501", "TLV3501", 13.0, 5.4, 0, {"1": "TH", "2": "GND", "3": "CP", "4": "VS", "5": "SIG", "6": "GND"}, hide_value=False, label=None)
    cvs = t.add("C", "C0402 100nF", "100n", 9.6, 7.2, 0, {"1": "VS", "2": "GND"}, label=None)
    rg = t.add("R", "R0402 49.9R", "49.9", 13.6, 8.2, 180, {"1": "SIG", "2": "GATE"}, label=None)              # pad 1 right
    rpd = t.add("R", "R0402 100k", "100k", 11.6, 8.2, 0, {"1": "GND", "2": "GATE"}, label=None)
    t.wire("CMD", [("J%d01" % t.idx, "1"), (rin, "1")])
    t.wire("CMD", [("J%d01" % t.idx, "1"), (rt, "1")])
    t.gnd_stub(rt, "2", (4.75, 10.95), sym=(0, 0))
    t.wire("CP", [(rin, "2"), (10.4, 4.75), (10.4, 6.35), (u, "3")], width=W)
    t.wire("TH", [(rr1, "2"), (rr2, "1")], width=W)
    t.wire("TH", [(rr2, "1"), (11.39, 4.45), (u, "1")], width=W)
    t.gnd_stub(rr2, "2", (13.3, 2.6), sym=(0, 0))
    t.wire("GND", [(u, "2"), (13.0, 5.4), (13.0, 4.45), (u, "6")], width=W, silk=False)
    t.gnd_stub(u, "6", (15.2, 3.7), sym=(0, 0))
    t.wire("SIG", [(u, "5"), (15.3, 5.4), (15.3, 8.2), (rg, "1")], width=W)
    t.wire("GATE", [(rg, "2"), (rpd, "2")], width=W)
    t.gnd_stub(cvs, "2", (10.6, 8.1), sym=(0, 0))
    t.wire("GND", [(rpd, "1"), (10.6, 8.1)], width=W, silk=False)
    # ---- the FET, its tab (the drain) to the right
    q = t.add("Q", "NCE6020AK", "NCE6020AK", 16.0, 12.8, 0, {"1": "GATE", "2": "DRN", "3": "SRC"}, hide_value=False, label=None)
    t.wire("GATE", [(rpd, "2"), (11.5, 9.0), (q, "1")], width=W)
    # ---- the source's shunt and the INA181 under the FET; the INA181's inputs Kelvin-connected (IN- along the bottom)
    rs = t.add("R", "R1206 0.05R", "0.05", 13.0, 18.4, 0, {"1": "GND", "2": "SRC"}, label=None)
    ina = t.add("U", "INA181A1", "INA181", 18.3, 18.4, 0, {"1": "IO", "2": "GND", "3": "SRC", "4": "GND", "5": "GND", "6": "+5V"}, hide_value=False, label=None)
    cvi = t.add("C", "C0402 100nF", "100n", 21.0, 18.6, 90, {"1": "GND", "2": "+5V"}, label=None)          # pad 2 up
    t.wire("SRC", [(q, "3"), (12.4, 16.5), (14.462, 16.9), (rs, "2")], width=0.8)
    t.wire("SRC", [(rs, "2"), (15.4, 19.35), (ina, "3")], width=W)
    t.gnd_stub(rs, "1", (10.2, 18.4), sym=(0, 0), width=0.6)
    t.wire("GND", [(rs, "1"), (11.538, 20.0), (19.437, 20.0), (ina, "4")], width=W, silk=False)
    t.wire("GND", [(ina, "4"), (ina, "5")], width=W, silk=False)
    t.gnd_stub(ina, "2", (15.9, 17.95), sym=(0, 0))
    t.wire("+5V", [(ina, "6"), (20.4, 17.45), (21.0, 17.6), (cvi, "2")], width=W)
    t.via("+5V", 21.0, 16.9)
    t.wire("+5V", [(cvi, "2"), (21.0, 16.9)], width=W)
    t.wire("GND", [(cvi, "1"), (22.0, 18.5)], width=W, silk=False)          # to the TVS's ground via
    # I: the INA181's output on the back along the bottom to 49.9 ohm by the jack
    ro = t.add("R", "R0402 49.9R", "49.9", 30.8, 19.0, 0, {"1": "IO", "2": "IJ"}, label=None)
    t.via("IO", 17.4, 16.6)
    t.wire("IO", [(ina, "1"), (17.4, 16.6)], width=W)
    t.wire("IO", [(17.4, 16.6), (18.1, 19.3), (29.4, 19.3)], width=W, layer="B.Cu", silk=False)
    t.wire("IO", [(29.4, 19.3), (ro, "1")], width=W)
    t.wire("IJ", [(ro, "2"), (32.4, 19.0), (32.4, 15.25), ("J%d03" % t.idx, "1")])
    # ---- the coil's terminal (VMOT on pin 2 beside the bus, the drain on pin 1), 10 uF on VMOT at the bus
    tc = t.add("J", "TERM2", "coil", 35.9, 4.35, 0, {"1": "DRN", "2": VM}, hide_value=True)
    cvm = t.add("C", "C0805 10uF", "10u", bx, 10.2, 90, {"1": "GND", "2": VM}, label=None)                # pad 2 up
    t.via(VM, bx, 4.35)
    t.wire(VM, [(bx, 4.35), (tc, "2")], width=WD)
    t.wire(VM, [(bx, 4.35), (tc, "2")], width=WD, layer="B.Cu", silk=False)
    t.wire(VM, [(bx, 4.35), (cvm, "2")], width=0.6)
    t.gnd_stub(cvm, "1", (40.9, 11.4), sym=(0, 0))
    # the drain: the tab to the header's middle pin along y 13.14; to the terminal's pin 1 on the back along y 9.0
    sel = t.add("J", "HDR3", "D Z", 31.0, 10.6, 0, {"1": "DA", "2": "DRN", "3": "ZK"}, hide_value=True)
    t.wire("DRN", [(20.4, 13.14), (sel, "2")], width=WD)
    for yv in (10.3, 11.3):
        t.via("DRN", 20.95, yv)
        t.wire("DRN", [(20.1, yv), (20.95, yv)], width=0.6)
    t.wire("DRN", [(20.95, 11.3), (20.95, 10.3), (21.75, 9.15), (33.4, 9.15), (tc, "1")], width=0.8, layer="B.Cu", silk=False)
    # the clamps: 1-2 the Schottky to VMOT (pin 2's pad), 2-3 the TVS to ground
    dd = t.add("D", "B5819W", "B5819W", 36.4, 10.0, 180, {"1": VM, "2": "DA"}, label=None)                # K right
    dz = t.add("D", "SMAJ24A", "SMAJ24A", 25.4, 16.6, 180, {"1": "ZK", "2": "GND"}, label=None)           # K right
    t.wire("DA", [(dd, "2"), (31.85, 10.6), (sel, "1")], width=0.6)
    t.wire(VM, [(dd, "1"), (38.4, 9.0), (tc, "2")], width=0.6)
    t.wire("ZK", [(dz, "1"), (30.2, 15.68), (sel, "3")], width=0.6)
    t.gnd_stub(dz, "2", (22.0, 18.5), sym=(0, 0), width=0.6)
    # VD: 5.1 k from the drain, 100 ohm to ground, 49.9 ohm up between the jack's lower legs
    rv1 = t.add("R", "R0805 5.1k", "5.1k", 23.6, 11.2, 90, {"1": "DRN", "2": "VDV"}, label=None)          # pad 1 down, on the drain
    rv2 = t.add("R", "R0402 100R", "100", 25.1, 11.3, 270, {"1": "VDV", "2": "GND"}, label=None)          # pad 1 up
    rvo = t.add("R", "R0402 49.9R", "49.9", 26.25, 9.7, 90, {"1": "VDV", "2": "VDJ"}, label=None)          # pad 1 down
    t.wire("DRN", [(rv1, "1"), (23.6, 13.14)], width=0.6)
    t.wire("VDV", [(rv1, "2"), (25.1, 10.29), (rv2, "1")], width=W)
    t.wire("VDV", [(25.1, 10.29), (25.6, 10.21), (rvo, "1")], width=W)
    t.gnd_stub(rv2, "2", (25.9, 12.0), sym=(0, 0))
    t.wire("VDJ", [(rvo, "2"), ("J%d02" % t.idx, "1")])
    # VS: the switched 5 V to the comparator
    t.route("VS", [HDR_VS, (cvs, "1")], width=0.3)
    t.route("VS", [(cvs, "1"), (rr1, "1")], width=W)
    t.route("VS", [(cvs, "1"), (u, "4")], width=W)
    t.titles.append("Solenoid")
    t.result = "the coil on while CMD is high; I = its current, 1 V/A (up to 2 A); VD = the drain / 52: the flyback's spike, by the jumper"
    t.notes = ["CMD (0 / +1 V) through 10 k into a TLV3501 drives an NCE6020AK (60 V) that switches the coil to ground; VMOT on the coil.",
               "Jumper 1-2: a Schottky to VMOT (slow decay); 2-3: a 24 V TVS (fast decay); none: the FET avalanches.  I 1 V/A, VD drain / 52."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ m7 --
def tile_m7():
    """A DC-coupled bridge amplifier, two cells in row 2 on the right, for a voice coil, a speaker as an actuator or a
    maglev's electromagnet: a TCA0372 (two 1 A power op amps, 40 V) from VMOT.  Side A inverts IN (terminated in 49.9
    ohm) with a gain of 2 about VMOT / 2 (10 k in, 20 k back, its + input at VMOT / 6), side B inverts side A about VMOT /
    2 (10 k, 10 k): the load between them sees 4 x IN, +-4 V for +-1 V, both ends at VMOT / 2 with IN at 0.  One chain
    (2 x 15 k, 20 k, 10 k: 3 : 2 : 1) sets both + inputs, so their ratio holds whatever VMOT is.  The load on a 2-way
    screw terminal in the right margin; its current through 0.1 ohm (in series, on side A's lead) read by an INA181A1 (x20
    about 2.5 V from 1 k / 1 k) and an OPA810 on +-5 V that takes away the 2.5 V and halves it: I = 1 V/A, through 49.9
    ohm.  No switch: the amplifier runs from VMOT, which no switch takes away, and sits at 0 V across the load with IN at
    0.  The TCA0372 dissipates up to VMOT^2 / (4 R): about 1 W is its limit (thermal shutdown beyond), so 8 ohm at 5-6
    V, or 30 ohm and more at 12 V.  The TCA0372 turned 270 at the right end of the right cell (its inputs to the left,
    its outputs to the terminal), the chain to its left, the shunt and the INA181 under the terminal, the difference
    amplifier in the left cell's lower-left corner; side A's output reaches side B's input on the back."""
    t = Tile("m7", "linear amp", [(2, 2), (3, 2)], supply="VMOT, +-5 V", subtitle="TCA0372", sections=["Motors"])
    t.jack("BR0", "IN", "IN", "in", "+-1 V", silk="IN 50R")
    t.jack("TL0", "I", "IJ", "out", "", silk="I 1V/A")
    WL = 0.8                                                  # the load's current
    bx = BUS_X - t.x0
    # ---- VMOT: a tap on the bus at the gutters' crossing (10 uF there), on the back along the gutter above the tile
    ct = t.add("C", "C0805 10uF", "10u", bx, 1.9, 90, {"1": "GND", "2": VM}, label=None)                  # pad 2 up
    t.via(VM, bx, -0.75)
    t.wire(VM, [(bx, -0.75), (ct, "2")], width=0.6)
    t.gnd_stub(ct, "1", (0.6, 3.8), sym=(0, 0))
    t.wire(VM, [(bx, -0.75), (39.6, -0.75), (39.6, 3.6)], width=WL, layer="B.Cu", silk=False)
    t.wire(VM, [(bx, -0.75), (27.0, -0.75), (27.0, 1.2)], width=0.4, layer="B.Cu", silk=False)
    # ---- the TCA0372, its ground pins joined under the body and to the planes
    u = t.add("U", "TCA0372", "TCA0372", 34.3, 10.6, 270, {"1": VM, "2": "OB", "4": "GND", "5": "GND", "7": "NB", "8": "TB", "9": "TA",
                                                          "10": "NA", "12": "GND", "13": "GND", "16": "OA"}, hide_value=False, label=None)
    t.wire("GND", [(34.3, 5.95), (34.3, 15.25)], width=2.2, silk=False)
    for yv in (8.2, 10.6, 13.0):
        t.gnd_stub(u, "5", (34.3, yv), sym=(0, 0), width=1.0)
    t.via(VM, 39.6, 3.6)
    t.wire(VM, [(39.6, 3.6), (38.745, 4.4), (u, "1")], width=0.6)
    cvc = t.add("C", "C0402 100nF", "100n", 40.45, 6.0, 90, {"1": "GND", "2": VM}, label=None)             # pad 2 up
    t.wire(VM, [(u, "1"), (38.745, 5.52), (cvc, "2")], width=0.4)
    t.gnd_stub(cvc, "1", (40.45, 7.4), sym=(0, 0))
    # ---- the chain from VMOT: 15 k + 15 k to TB (VMOT / 2), 20 k to TA (VMOT / 6), 10 k to ground; 100 nF on each tap
    rt1 = t.add("R", "R0402 15k", "15k", 27.0, 2.6, 90, {"1": "CT", "2": VM}, label=None)                  # pad 2 up
    rt2 = t.add("R", "R0402 15k", "15k", 27.0, 4.6, 90, {"1": "TB", "2": "CT"}, label=None)
    rc2 = t.add("R", "R0402 20k", "20k", 27.0, 9.6, 90, {"1": "TA", "2": "TB"}, label=None)
    rc3 = t.add("R", "R0402 10k", "10k", 27.0, 14.6, 90, {"1": "GND", "2": "TA"}, label=None)
    ctb = t.add("C", "C0402 100nF", "100n", 28.2, 7.0, 90, {"1": "GND", "2": "TB"}, label=None)
    cta = t.add("C", "C0402 100nF", "100n", 28.2, 12.4, 90, {"1": "TA", "2": "GND"}, label=None)
    t.wire(VM, [(27.0, 1.2), (rt1, "2")], width=W)
    t.wire("CT", [(rt1, "1"), (rt2, "2")], width=W)
    t.wire("TB", [(rt2, "1"), (27.0, 5.7), (29.855, 5.7), (u, "8")], width=W)
    t.wire("TB", [(27.0, 5.7), (rc2, "2")], width=W)
    t.wire("TB", [(28.2, 5.7), (ctb, "2")], width=W)
    t.gnd_stub(ctb, "1", (28.2, 8.4), sym=(0, 0))
    t.wire("TA", [(rc2, "1"), (rc3, "2")], width=W)
    t.wire("TA", [(27.0, 13.4), (29.855, 13.4), (u, "9")], width=W)
    t.wire("TA", [(28.2, 13.4), (cta, "1")], width=W)
    t.gnd_stub(cta, "2", (28.2, 11.0), sym=(0, 0))
    t.gnd_stub(rc3, "1", (27.0, 16.2), sym=(0, 0))
    # ---- side A: IN through 10 k (from under the jack) and 20 k back from OA, both into -IN A from below
    rti = t.add("R", "R0402 49.9R", "49.9", 20.4, 13.6, 90, {"1": "IN", "2": "GND"}, label=None)           # pad 1 down
    ria = t.add("R", "R0402 10k", "10k", 31.125, 18.3, 90, {"1": "IN", "2": "NA"}, label=None)            # pad 2 up
    rfa = t.add("R", "R0402 20k", "20k", 35.0, 17.4, 0, {"1": "NA", "2": "OA"}, label=None)
    t.wire("IN", [("J%d01" % t.idx, "1"), (20.4, 15.25), (20.4, 18.81), (ria, "1")])
    t.wire("IN", [(20.4, 15.25), (rti, "1")])
    t.gnd_stub(rti, "2", (20.4, 12.2), sym=(0, 0))
    t.wire("NA", [(ria, "2"), (u, "10")], width=W)
    t.wire("NA", [(rfa, "1"), (31.125, 17.4)], width=W)
    t.wire("OA", [(u, "16"), (38.745, 17.4), (rfa, "2")], width=W)
    # ---- side B: OA through 10 k (on the back from beside OA) and 10 k back from OB, both into -IN B from above
    rib = t.add("R", "R0402 10k", "10k", 31.125, 3.2, 90, {"1": "NB", "2": "OA"}, label=None)             # pad 2 up
    rfb = t.add("R", "R0402 10k", "10k", 34.3, 3.6, 0, {"1": "NB", "2": "OB"}, label=None)
    t.wire("NB", [(rib, "1"), (u, "7")], width=W)
    t.wire("NB", [(rfb, "1"), (31.125, 3.6)], width=W)
    t.wire("OB", [(37.475, 3.6), (rfb, "2")], width=W)
    t.via("OA", 37.4, 18.4)
    t.via("OA", 31.125, 1.7)
    t.wire("OA", [(38.745, 18.35), (37.4, 18.4)], width=W)
    t.wire("OA", [(37.4, 18.4), (37.0, 18.0), (37.0, 1.7), (31.125, 1.7)], width=W, layer="B.Cu", silk=False)
    t.wire("OA", [(31.125, 1.7), (rib, "2")], width=W)
    # ---- the load: OB straight to the terminal's pin 1, OA through the shunt to pin 2
    tl = t.add("J", "TERM2", "load", 44.9, 8.0, 270, {"1": "OB", "2": "LA"}, hide_value=True)
    rsh = t.add("R", "R1206 0.1R", "0.1", 42.6, 18.35, 0, {"1": "OA", "2": "LA"}, label=None)
    t.wire("OB", [(u, "2"), (37.475, 2.2), (43.8, 2.2), (44.9, 3.3), (tl, "1")], width=WL)
    t.wire("OA", [(u, "16"), (38.745, 18.35), (rsh, "1")], width=WL)
    t.wire("LA", [(rsh, "2"), (48.0, 18.35), (48.0, 12.0), (46.5, 10.5), (tl, "2")], width=WL)
    # ---- the INA181 over the shunt (2.5 V on REF from 1 k / 1 k: no capacitor, so the reference and the difference
    # amplifier's both follow +5 V and its noise cancels), its output on the back down beside it and along the bottom
    ina = t.add("U", "INA181A1", "INA181", 42.6, 15.45, 0, {"1": "IO", "2": "GND", "3": "OA", "4": "LA", "5": "RFN", "6": "+5V"},
                hide_value=False, label=None)
    t.wire("OA", [(41.138, 17.475), (ina, "3")], width=W)
    t.wire("LA", [(44.062, 17.475), (ina, "4")], width=W)
    t.gnd_stub(ina, "2", (39.9, 15.45), sym=(0, 0))
    cvi = t.add("C", "C0402 100nF", "100n", 46.1, 14.05, 0, {"1": "+5V", "2": "GND"}, label=None)
    rr1 = t.add("R", "R0402 1k", "1k", 45.5, 15.6, 90, {"1": "RFN", "2": "+5V"}, label=None)              # pad 2 up
    rr2 = t.add("R", "R0402 1k", "1k", 46.7, 15.6, 90, {"1": "RFN", "2": "GND"}, label=None)
    t.via("+5V", 44.6, 13.0)
    t.wire("+5V", [(44.6, 13.0), (44.6, 14.05), (cvi, "1")], width=W)
    t.wire("+5V", [(ina, "6"), (44.6, 14.5)], width=W)
    t.wire("+5V", [(44.6, 14.05), (44.6, 14.5)], width=W)
    t.wire("+5V", [(cvi, "1"), (45.5, 14.6), (rr1, "2")], width=W)
    t.wire("GND", [(cvi, "2"), (rr2, "2")], width=W, silk=False)
    t.gnd_stub(rr2, "2", (47.1, 14.3), sym=(0, 0))
    t.wire("RFN", [(ina, "5"), (44.75, 15.45), (44.75, 16.7), (46.7, 16.7), (rr2, "1")], width=W)
    t.wire("RFN", [(45.5, 16.7), (rr1, "1")], width=W)
    t.via("IO", 41.463, 13.2)
    t.wire("IO", [(ina, "1"), (41.463, 13.2)], width=W)
    t.wire("IO", [(41.463, 13.2), (40.6, 13.8), (40.6, 19.5), (19.4, 19.5), (19.4, 9.8)], width=W, layer="B.Cu", silk=False)
    # ---- the difference amplifier in the left cell's middle: I = 0.833 V x 1.5 - IO / 2 = (2.5 V - IO) / 2 (the
    # INA181's output falls as the current, OB to the load, rises); out through 49.9 ohm between the jack's right legs
    ud = t.add("U", "OPA810", "OPA810", 14.6, 6.4, 0, {"1": "DO", "2": "-5V", "3": "DP", "4": "DN", "5": "+5V"}, hide_value=False, label=None)
    r1 = t.add("R", "R0402 20k", "20k", 18.4, 8.8, 0, {"1": "DN", "2": "IO"}, label=None)
    r2 = t.add("R", "R0402 10k", "10k", 15.0, 2.6, 0, {"1": "DO", "2": "DN"}, label=None)
    r3 = t.add("R", "R0402 10k", "10k", 9.6, 9.2, 90, {"1": "+5V", "2": "DP"}, label=None)                 # pad 2 up
    r4 = t.add("R", "R0402 2k", "2k", 10.8, 9.2, 90, {"1": "GND", "2": "DP"}, label=None)
    ro = t.add("R", "R0402 49.9R", "49.9", 11.0, 2.6, 0, {"1": "IJ", "2": "DO"}, label=None)
    cdn = t.add("C", "C0402 100nF", "100n", 11.2, 5.0, 90, {"1": "-5V", "2": "GND"}, label=None)           # pad 2 up
    cdv = t.add("C", "C0402 100nF", "100n", 18.6, 5.0, 90, {"1": "GND", "2": "+5V"}, label=None)
    t.via("IO", 19.4, 9.8)
    t.wire("IO", [(19.4, 9.8), (19.4, 8.8), (r1, "2")], width=W)
    t.wire("DN", [(r1, "1"), (17.2, 8.8), (17.2, 2.6), (r2, "2")], width=W)
    t.wire("DN", [(17.2, 7.35), (ud, "4")], width=W)
    t.wire("DO", [(ud, "1"), (13.463, 2.6), (r2, "1")], width=W)
    t.wire("DO", [(13.463, 2.6), (ro, "2")], width=W)
    t.wire("IJ", [(ro, "1"), (9.0, 2.6), (8.6, 3.2), (8.6, 4.75), ("J%d02" % t.idx, "1")])
    t.via("+5V", 16.0, 4.5)
    t.wire("+5V", [(ud, "5"), (16.0, 4.5)], width=W)
    t.via("+5V", 18.6, 3.9)
    t.wire("+5V", [(cdv, "2"), (18.6, 3.9)], width=W)
    t.gnd_stub(cdv, "1", (18.6, 6.1), sym=(0, 0))
    t.wire("DP", [(ud, "3"), (12.0, 7.35), (12.0, 8.2), (9.6, 8.2), (r3, "2")], width=W)
    t.wire("DP", [(10.8, 8.2), (r4, "2")], width=W)
    t.via("+5V", 9.6, 10.6)
    t.wire("+5V", [(r3, "1"), (9.6, 10.6)], width=W)
    t.gnd_stub(r4, "1", (10.8, 10.6), sym=(0, 0))
    t.via("-5V", 11.2, 6.4)
    t.wire("-5V", [(ud, "2"), (11.2, 6.4)], width=W)
    t.wire("-5V", [(11.2, 6.4), (cdn, "1")], width=W)
    t.wire("-5V", [(11.2, 6.4), (8.6, 9.0), (8.6, 20.5)], width=W, layer="B.Cu", silk=False)
    t.via("-5V", 8.6, 20.5)
    t.gnd_stub(cdn, "2", (10.2, 4.3), sym=(0, 0))
    t.titles.append("Linear amp")
    t.result = "the load at 4 x IN (+-4 V for +-1 V), about VMOT / 2 at each end; I = the load's current, 1 V/A (+-1 A)"
    t.notes = ["A TCA0372 bridge from VMOT: side A = VMOT/2 - 2 IN, side B = VMOT/2 + 2 IN, so the load sees 4 x IN.  Up to 1 A and about 1 W",
               "in the chip: 8 ohm at 5-6 V, 30 ohm or more at 12 V.  0.1 ohm + INA181 + OPA810: I = 1 V/A.  A voice coil, a maglev magnet."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ m8 --
def tile_m8():
    """A synchronous buck power stage the FPGA closes the loop on, two cells at the bottom right: PWM (a DAC's square
    wave, 0 / +1 V, terminated in 49.9 ohm) through 10 k into a TLV3501 on +5 V (threshold 0.49 V, as m5) that drives a
    TPS28225 (5 V gate driver, 14 ns adaptive dead time, its own bootstrap diode; 220 nF of bootstrap; its EN from the
    tile's switch through 100 k, so the switch stops it) and two AO3400A (30 V, 32 mohm at 4.5 V) from VMOT (22 uF beside
    them); 47 uH (SWPA6045, 1.2 A) into 2 x 22 uF, the output on a 2-way screw terminal in the right margin.  At 200 kHz
    from 12 V to 5 V the ripple is about 0.3 A peak to peak.  The inductor's current through 0.05 ohm (between it and the
    output) read by an INA181A1 (x20) onto I through 49.9 ohm: 1 V/A, as m5's and m6's, one way only (at light load the
    synchronous stage's current dips below zero and I sits at 0 there); VO / 16 (15 k / 1 k) through 49.9 ohm.  The
    half-bridge, its input capacitor and the inductor along the right cell's top, the driver under the FETs, the shunt
    and the INA181 under the inductor; the comparator, the switch and VO's divider in the left cell."""
    t = Tile("m8", "buck stage", [(2, 3), (3, 3)], supply="+5 V, VMOT", subtitle="TPS28225", sections=["Motors"])
    t.jack("TL0", "PWM", "PWMJ", "in", "0/+1 V", silk="PWM 50R")
    t.jack("BR0", "VO", "VOJ", "out", "", silk="VO /16")
    t.jack("BR1", "I", "IJ", "out", "", silk="I 1V/A")
    power_header(t)
    WP2 = 0.8                                                 # the power stage's currents
    bx = BUS_X - t.x0
    # ---- VMOT: a tap on the bus (10 uF there), on the back along the tile's top edge to the input capacitor
    ctap = t.add("C", "C0805 10uF", "10u", -0.55, 2.4, 90, {"1": "GND", "2": VM}, label=None)             # pad 2 up
    t.via(VM, bx, 0.4)
    t.wire(VM, [(bx, 0.4), (-0.55, 0.9), (ctap, "2")], width=0.6)
    t.gnd_stub(ctap, "1", (0.8, 4.4), sym=(0, 0))
    t.via(VM, 24.9, 0.4)
    t.wire(VM, [(bx, 0.4), (24.9, 0.4)], width=WP2, layer="B.Cu", silk=False)
    # ---- the comparator (as m5's), on +5 V
    rt = t.add("R", "R0402 49.9R", "49.9", 4.75, 9.6, 270, {"1": "PWMJ", "2": "GND"}, label=None)
    rin = t.add("R", "R0402 10k", "10k", 9.4, 4.75, 0, {"1": "PWMJ", "2": "CP"}, label=None)
    rr1c = t.add("R", "R0402 47k", "47k", 9.6, 2.6, 0, {"1": "+5V", "2": "TH"}, label=None)
    rr2c = t.add("R", "R0402 5.1k", "5.1k", 11.9, 2.6, 0, {"1": "TH", "2": "GND"}, label=None)
    u = t.add("U", "TLV3501", "TLV3501", 13.0, 5.4, 0, {"1": "TH", "2": "GND", "3": "CP", "4": "+5V", "5": "PWM", "6": "GND"}, hide_value=False, label=None)
    cvs = t.add("C", "C0402 100nF", "100n", 9.6, 7.2, 0, {"1": "+5V", "2": "GND"}, label=None)
    t.wire("PWMJ", [("J%d01" % t.idx, "1"), (rin, "1")])
    t.wire("PWMJ", [("J%d01" % t.idx, "1"), (rt, "1")])
    t.gnd_stub(rt, "2", (4.75, 10.95), sym=(0, 0))
    t.wire("CP", [(rin, "2"), (10.4, 4.75), (10.4, 6.35), (u, "3")], width=W)
    t.wire("TH", [(rr1c, "2"), (rr2c, "1")], width=W)
    t.wire("TH", [(rr2c, "1"), (11.39, 4.45), (u, "1")], width=W)
    t.gnd_stub(rr2c, "2", (13.3, 2.6), sym=(0, 0))
    t.wire("GND", [(u, "2"), (13.0, 5.4), (13.0, 4.45), (u, "6")], width=W, silk=False)
    t.gnd_stub(u, "6", (15.2, 3.7), sym=(0, 0))
    t.gnd_stub(cvs, "2", (10.6, 8.1), sym=(0, 0))
    t.via("+5V", 9.1, 8.4)
    t.wire("+5V", [(cvs, "1"), (9.1, 8.4)], width=W)
    t.route("+5V", [(cvs, "1"), (rr1c, "1")], width=W)
    t.route("+5V", [(cvs, "1"), (u, "4")], width=W)
    # ---- the half-bridge: VMOT's 22 uF, the high-side FET's drain beside it, its source and the low side's drain to the
    # inductor's left pad along x 31
    cin = t.add("C", "C1206 22uF", "22u", 24.9, 3.8, 90, {"1": "GND", "2": VM}, label=None)               # pad 2 up
    hs = t.add("Q", "NFET", "AO3400A", 28.6, 2.95, 180, {"1": "UG", "2": "PH", "3": VM}, hide_value=True, label=None)
    ls = t.add("Q", "NFET", "AO3400A", 28.6, 6.6, 0, {"1": "LG", "2": "GND", "3": "PH"}, hide_value=True, label=None)
    lo = t.add("L", "L47U_6045", "47u", 35.6, 3.4, 0, {"1": "PH", "2": "LX"}, label=None)
    t.wire(VM, [(24.9, 0.4), (cin, "2")], width=WP2)
    t.wire(VM, [(cin, "2"), (hs, "3")], width=WP2)
    t.wire("GND", [(cin, "1"), (24.9, 7.55), (ls, "2")], width=WP2, silk=False)
    t.gnd_stub(cin, "1", (23.6, 6.6), sym=(0, 0), width=0.6)
    t.gnd_stub(ls, "2", (26.2, 7.55), sym=(0, 0), width=0.6)
    t.wire("PH", [(hs, "2"), (31.0, 2.0), (31.0, 6.6), (ls, "3")], width=0.6)
    t.wire("PH", [(31.0, 3.4), (lo, "1")], width=WP2)
    # ---- the driver under the FETs; its gates, bootstrap and PWM found by the router
    drv = t.add("U", "TPS28225", "TPS28225", 27.0, 13.9, 90, {"1": "UG", "2": "BOOT", "3": "PWM", "4": "GND", "5": "LG", "6": "+5V", "7": "EN", "8": "PH"},
                hide_value=False, label=None)
    cb = t.add("C", "C0402 220nF", "220n", 23.2, 13.9, 90, {"1": "BOOT", "2": "PH"}, label=None)          # pad 2 up
    cvd = t.add("C", "C0603 1uF", "1u", 27.8, 9.25, 0, {"1": "+5V", "2": "GND"}, label=None)
    ren = t.add("R", "R0402 100k", "100k", 24.0, 9.6, 0, {"1": "VS", "2": "EN"}, label=None)
    t.gnd_stub(drv, "4", (28.905, 18.7), sym=(0, 0))
    t.gnd_stub(cvd, "2", (29.9, 9.25), sym=(0, 0))
    t.via("+5V", 26.4, 8.5)
    t.wire("+5V", [(cvd, "1"), (26.4, 8.5)], width=W)
    t.wire("+5V", [(cvd, "1"), (27.635, 10.45)], width=0.3)
    t.route("UG", [(drv, "1"), (hs, "1")], width=0.3)
    t.route("LG", [(drv, "5"), (ls, "1")], width=0.3)
    t.route("BOOT", [(drv, "2"), (cb, "1")], width=0.3)
    t.route("PH", [(drv, "8"), (cb, "2")], width=0.3)
    t.route("PH", [(cb, "2"), (ls, "3")], width=0.3)
    t.route("EN", [(drv, "7"), (ren, "2")], width=W)
    # ---- the output: the inductor's right pad through the shunt (standing under it) to the terminal and 2 x 22 uF
    rsh = t.add("R", "R1206 0.05R", "0.05", 38.6, 9.0, 90, {"1": "VO", "2": "LX"}, label=None)              # pad 2 up
    tc = t.add("J", "TERM2", "out", 44.9, 6.0, 270, {"1": "VO", "2": "GND"}, hide_value=True)
    co1 = t.add("C", "C1206 22uF", "22u", 44.0, 14.0, 0, {"1": "VO", "2": "GND"}, label=None)
    co2 = t.add("C", "C1206 22uF", "22u", 44.0, 16.6, 0, {"1": "VO", "2": "GND"}, label=None)
    t.wire("LX", [(lo, "2"), (38.6, 6.7), (rsh, "2")], width=WP2)
    t.wire("VO", [(rsh, "1"), (40.4, 10.462), (40.4, 1.0), (43.8, 1.0), (tc, "1")], width=WP2)
    t.wire("VO", [(40.4, 10.462), (41.9, 11.4), (41.9, 16.6), (co2, "1")], width=WP2)
    t.wire("VO", [(41.9, 14.0), (co1, "1")], width=WP2)
    t.gnd_stub(co1, "2", (46.8, 14.0), sym=(0, 0), width=0.6)
    t.gnd_stub(co2, "2", (46.8, 16.6), sym=(0, 0), width=0.6)
    t.gnd_stub(tc, "2", (46.9, 10.4), sym=(0, 0), width=0.6)
    # ---- the INA181 beside the shunt (REF on ground), its inputs from the shunt's own pads; I through 49.9 ohm between
    # the jack's left legs
    ina = t.add("U", "INA181A1", "INA181", 35.75, 9.0, 90, {"1": "IO", "2": "GND", "3": "LX", "4": "VO", "5": "GND", "6": "+5V"},
                hide_value=False, label=None)
    cvi = t.add("C", "C0402 100nF", "100n", 33.2, 7.9, 90, {"1": "GND", "2": "+5V"}, label=None)          # pad 2 up
    ro = t.add("R", "R0402 49.9R", "49.9", 32.2, 15.25, 0, {"1": "IO", "2": "IJ"}, label=None)
    t.route("VO", [(rsh, "1"), (ina, "4")], width=W)
    t.route("LX", [(rsh, "2"), (ina, "3")], width=W)
    t.wire("GND", [(ina, "2"), (ina, "5")], width=W, silk=False)
    t.gnd_stub(ina, "2", (35.75, 12.0), sym=(0, 0))
    t.wire("+5V", [(ina, "6"), (34.8, 7.0), (33.2, 7.0), (cvi, "2")], width=W)
    t.via("+5V", 32.2, 7.42)
    t.wire("+5V", [(cvi, "2"), (32.2, 7.42)], width=W)
    t.gnd_stub(cvi, "1", (32.2, 8.9), sym=(0, 0))
    t.route("IO", [(ina, "1"), (ro, "1")], width=W)
    t.wire("IJ", [(ro, "2"), ("J%d03" % t.idx, "1")])
    # ---- VO / 16 beside its jack: 15 k from VO (found by the router), 1 k, 49.9 ohm between the jack's right legs
    rd1 = t.add("R", "R0402 15k", "15k", 21.2, 12.8, 90, {"1": "VD", "2": "VO"}, label=None)               # pad 2 up
    rd2 = t.add("R", "R0402 1k", "1k", 21.2, 17.4, 90, {"1": "GND", "2": "VD"}, label=None)
    rdo = t.add("R", "R0402 49.9R", "49.9", 20.2, 15.25, 0, {"1": "VOJ", "2": "VD"}, label=None)
    t.wire("VD", [(rd1, "1"), (21.2, 15.25), (rd2, "2")], width=W)
    t.wire("VD", [(21.2, 15.25), (rdo, "2")], width=W)
    t.wire("VOJ", [(rdo, "1"), ("J%d02" % t.idx, "1")])
    t.gnd_stub(rd2, "1", (21.2, 18.7), sym=(0, 0))
    t.via("VO", 37.2, 11.6)
    t.via("VO", 22.6, 12.0)
    t.wire("VO", [(rsh, "1"), (37.2, 11.6)], width=W)
    t.wire("VO", [(37.2, 11.6), (36.6, 11.0), (22.6, 11.0), (22.6, 12.0)], width=W, layer="B.Cu", silk=False)
    t.wire("VO", [(22.6, 12.0), (rd1, "2")], width=W)
    # ---- the switch's 5 V to the driver's EN; PWM from the comparator to the driver
    t.route("PWM", [(u, "5"), (drv, "3")], width=W)
    t.wire("VS", [HDR_VS, (9.4, 17.3), (9.4, 11.2), (22.0, 11.2), (22.0, 10.2), (ren, "1")], width=0.3)
    t.titles.append("Buck stage")
    t.result = "VO = the duty cycle x VMOT at the PWM's frequency (100-500 kHz); I = the inductor's current, 1 V/A (0 when it dips below zero); VO jack VO / 16"
    t.notes = ["PWM (0 / +1 V) squared by a TLV3501 into a TPS28225 driving two AO3400A from VMOT; 47 uH into 2 x 22 uF.  Close the loop",
               "in the FPGA from VO (VO / 16) and I (1 V/A); a load on the terminal, up to 1 A.  The switch holds the driver's EN low."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ m9 --
def tile_m9():
    """A linear hall sensor, one cell: a DRV5055A3 (25 mV/mT at 5 V, +-85 mT, ratiometric about half its supply) in the
    top-left quarter where a magnet can come close, on the switched 5 V; an OPA810 on +-5 V subtracts half the supply
    (two 20 k from VS and ground on its -IN, the same ratio as the sensor's) and scales by 0.39 (10 k / 3.9 k): OUT is
    9.75 mV/mT, +-0.83 V at +-85 mT, through 49.9 ohm.  The maglev and the position loops' sensor."""
    t = Tile("m9", "hall", [(0, 1)], supply="+-5 V", subtitle="DRV5055A3", sections=["Motors"])
    t.jack("BR", "OUT", "OUT", "out", "")
    power_header(t)
    hs = t.add("U", "DRV5055A3", "DRV5055", 4.0, 4.2, 0, {"1": "VS", "2": "OH", "3": "GND"}, hide_value=False, label=None)
    chs = t.add("C", "C0402 100nF", "100n", 1.6, 4.2, 90, {"1": "GND", "2": "VS"}, label=None)          # pad 2 up
    u = t.add("U", "OPA810", "OPA810", 12.6, 5.0, 0, {"1": "OA", "2": "-5V", "3": "IP", "4": "IN", "5": "VS"}, hide_value=False, label=None)
    r1 = t.add("R", "R0402 10k", "10k", 8.0, 5.95, 0, {"1": "OH", "2": "IP"}, label=None)
    r2 = t.add("R", "R0402 3.9k", "3.9k", 9.6, 7.8, 270, {"1": "IP", "2": "GND"}, label=None)           # pad 1 up
    r3 = t.add("R", "R0402 20k", "20k", 16.6, 6.4, 0, {"1": "VS", "2": "IN"}, label=None)
    r4 = t.add("R", "R0402 20k", "20k", 16.6, 7.6, 0, {"1": "GND", "2": "IN"}, label=None)
    rf = t.add("R", "R0402 3.9k", "3.9k", 12.6, 8.4, 0, {"1": "IN", "2": "OA"}, label=None)
    ro = t.add("R", "R0402 49.9R", "49.9", 10.6, 15.25, 0, {"1": "OA", "2": "OUT"}, label=None)
    cvp = t.add("C", "C0402 100nF", "100n", 15.8, 3.2, 0, {"1": "VS", "2": "GND"}, label=None)
    cvn = t.add("C", "C0402 100nF", "100n", 9.4, 3.2, 0, {"1": "GND", "2": "-5V"}, label=None)
    t.route("OH", [(hs, "2"), (r1, "1")], width=W)
    t.wire("IP", [(r1, "2"), (9.6, 5.95), (u, "3")], width=W)
    t.wire("IP", [(9.6, 5.95), (r2, "1")], width=W)
    t.gnd_stub(r2, "2", (9.6, 9.0), sym=(0, 0))
    t.route("IN", [(u, "4"), (r3, "2")], width=W)
    t.wire("IN", [(r3, "2"), (r4, "2")], width=W)
    t.route("IN", [(r4, "2"), (rf, "1")], width=W)
    t.route("OA", [(u, "1"), (rf, "2")], width=W)
    t.route("OA", [(rf, "2"), (ro, "1")], width=W)
    t.wire("OUT", [(ro, "2"), ("J%d01" % t.idx, "1")])
    t.gnd_stub(r4, "1", (15.2, 8.6), sym=(0, 0))
    t.gnd_stub(hs, "3", (6.0, 4.2), sym=(0, 0))
    t.gnd_stub(chs, "1", (1.6, 5.9), sym=(0, 0))
    t.gnd_stub(cvp, "2", (17.2, 3.2), sym=(0, 0))
    t.gnd_stub(cvn, "1", (8.92, 4.4), sym=(0, 0))
    t.wire("-5V", [(u, "2"), (10.2, 5.0), (10.2, 3.2), (cvn, "2")], width=W)
    rail(t, "-5V", (10.2, 2.2), "above")
    t.wire("-5V", [(10.2, 3.2), (10.2, 2.2)], width=W)
    t.route("VS", [HDR_VS, (r3, "1")], width=0.3)
    t.route("VS", [(r3, "1"), (cvp, "1")], width=0.3)
    t.route("VS", [(cvp, "1"), (u, "5")], width=W)
    t.route("VS", [(cvp, "1"), (hs, "1")], width=0.3)
    t.wire("VS", [(hs, "1"), (1.6, 3.05), (chs, "2")], width=W)
    t.titles.append("Hall")
    t.result = "OUT = 9.75 mV per mT at the sensor (+-0.83 V at +-85 mT), 0 V with no field; about 20 kHz wide"
    t.notes = ["DRV5055A3: 25 mV/mT about half its 5 V supply, ratiometric.  The OPA810 subtracts the same half (20 k / 20 k) and scales",
               "by 0.39: OUT 9.75 mV/mT.  A magnet's distance, a maglev's gap, a gear tooth; the sensor is the small part top left."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ----------------------------------------------------------------------------------------------------------- m10 --
def tile_m10():
    """A reflective optical sensor, one cell: a QRE1113GR (IR LED and phototransistor in one 2.9 x 3.6 mm package, best
    at 1 mm, useful to a few) in the top-left quarter facing up; the LED at 21 mA through 180 ohm (0805) from the switched
    5 V; the phototransistor's collector held at 0 V by an OPA810 (its emitter on -5 V through 100 ohm), so OUT = 1 k x the collector
    current (0.1-0.9 mA: 0.1-0.9 V), with 100 pF across 1 k, through 49.9 ohm.  Distance, a reflective mark on a wheel
    (a tachometer), an edge."""
    t = Tile("m10", "optical", [(1, 1)], supply="+-5 V", subtitle="QRE1113", sections=["Motors"])
    t.jack("BR", "OUT", "OUT", "out", "")
    power_header(t)
    q = t.add("U", "QRE1113GR", "QRE1113", 4.0, 4.5, 0, {"1": "LA", "2": "GND", "3": "COL", "4": "EM"}, hide_value=False, label=None)
    re = t.add("R", "R0402 100R", "100", 7.0, 2.6, 0, {"1": "EM", "2": "-5V"}, label=None)               # the emitter to -5 V
    rl = t.add("R", "R0805 180R", "180", 4.0, 9.2, 0, {"1": "VS", "2": "LA"}, label=None)
    u = t.add("U", "OPA810", "OPA810", 12.6, 5.0, 0, {"1": "OA", "2": "-5V", "3": "GND", "4": "COL", "5": "VS"}, hide_value=False, label=None)
    rf = t.add("R", "R0402 1k", "1k", 12.6, 8.0, 0, {"1": "COL", "2": "OA"}, label=None)
    cf = t.add("C", "C0402 100pF", "100p", 12.6, 9.2, 0, {"1": "COL", "2": "OA"}, label=None)
    ro = t.add("R", "R0402 49.9R", "49.9", 10.6, 15.25, 0, {"1": "OA", "2": "OUT"}, label=None)
    cvp = t.add("C", "C0402 100nF", "100n", 15.8, 3.2, 0, {"1": "VS", "2": "GND"}, label=None)
    cvn = t.add("C", "C0402 100nF", "100n", 9.4, 3.2, 0, {"1": "GND", "2": "-5V"}, label=None)
    t.route("LA", [(q, "1"), (rl, "2")], width=W)
    t.gnd_stub(q, "2", (1.8, 6.5), sym=(0, 0))
    t.route("COL", [(q, "3"), (u, "4")], width=W)
    t.route("COL", [(u, "4"), (rf, "1")], width=W)
    t.wire("COL", [(rf, "1"), (11.7, 8.0), (11.7, 9.2), (cf, "1")], width=W)
    t.route("OA", [(u, "1"), (rf, "2")], width=W)
    t.wire("OA", [(rf, "2"), (13.5, 8.0), (13.5, 9.2), (cf, "2")], width=W)
    t.route("OA", [(cf, "2"), (ro, "1")], width=W)
    t.wire("OUT", [(ro, "2"), ("J%d01" % t.idx, "1")])
    t.gnd_stub(u, "3", (10.0, 6.4), sym=(0, 0))
    t.gnd_stub(cvp, "2", (17.2, 3.2), sym=(0, 0))
    t.gnd_stub(cvn, "1", (8.92, 4.4), sym=(0, 0))
    t.wire("-5V", [(u, "2"), (10.2, 5.0), (10.2, 3.2), (cvn, "2")], width=W)
    t.wire("-5V", [(10.2, 3.2), (10.2, 2.2)], width=W)
    rail(t, "-5V", (10.2, 2.2), "above")
    t.route("EM", [(q, "4"), (re, "1")], width=W)
    t.route("-5V", [(re, "2"), (10.2, 2.2)], width=W)
    t.route("VS", [HDR_VS, (rl, "1")], width=0.4)
    t.route("VS", [(rl, "1"), (cvp, "1")], width=0.3)
    t.route("VS", [(cvp, "1"), (u, "5")], width=W)
    t.titles.append("Optical")
    t.result = "OUT = 1 k x the phototransistor's current: about 0.1-0.9 V with white paper 1 mm above the sensor, near 0 V with nothing"
    t.notes = ["QRE1113GR: an IR LED (21 mA through 180 ohm) and a phototransistor side by side.  The OPA810 holds the collector at 0 V",
               "(emitter on -5 V through 100 ohm): OUT = 1 k x Ic.  Distance in the first millimetres, a mark on a wheel, a line."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ----------------------------------------------------------------------------------------------------------- m11 --
def tile_m11():
    """A load cell's amplifier, one cell, always on (no switch: the bridge draws 5 mA): a 4-way JST XH standing down the
    left edge (1 E+ red, 2 E- black, 3 S- white, 4 S+ green) excites the bridge from +5 V; an INA828 on +-5 V at gain 201
    (249 ohm, lying above it between pins 1 and 8) reads it, REF on ground, its output through 49.9 ohm onto OUT (the
    INA828's own 10 kHz at this gain is the filter).  A 1 mV/V cell at 5 V gives 5 mV at full load: about 1 V out."""
    t = Tile("m11", "load cell", [(2, 1)], supply="+-5 V", subtitle="INA828", sections=["Motors"])
    t.jack("BR", "OUT", "OUT", "out", "")
    xh = t.add("J", "XH4V", "cell", 3.5, 4.0, 270, {"1": "+5V", "2": "GND", "3": "SN", "4": "SP"}, hide_value=True)
    u = t.add("U", "INA828", "INA828", 14.5, 5.6, 0, {"1": "RG1", "2": "SN", "3": "SP", "4": "-5V", "5": "GND", "6": "OI", "7": "+5V", "8": "RG8"},
              hide_value=False, label=None)
    rg = t.add("R", "R0402 249R", "249", 14.5, 2.3, 0, {"1": "RG1", "2": "RG8"}, label=None)
    ro = t.add("R", "R0402 49.9R", "49.9", 18.4, 9.8, 270, {"1": "OI", "2": "OUT"}, label=None)            # pad 1 up
    cvp = t.add("C", "C0402 100nF", "100n", 19.3, 3.6, 90, {"1": "GND", "2": "+5V"}, label=None)          # pad 2 up
    cvn = t.add("C", "C0402 100nF", "100n", 12.0, 9.6, 0, {"1": "-5V", "2": "GND"}, label=None)
    t.wire("RG1", [(rg, "1"), (12.6, 2.3), (u, "1")], width=W)
    t.wire("RG8", [(rg, "2"), (16.4, 2.3), (u, "8")], width=W)
    t.wire("SN", [(xh, "3"), (8.0, 9.0), (8.0, 4.965), (u, "2")], width=W)
    t.wire("SP", [(xh, "4"), (10.0, 11.5), (10.0, 6.235), (u, "3")], width=W)
    t.wire("OI", [(u, "6"), (18.4, 6.235), (ro, "1")], width=W)
    t.wire("OUT", [(ro, "2"), (18.4, 11.0), (15.25, 11.0), ("J%d01" % t.idx, "1")])
    t.wire("+5V", [(u, "7"), (18.5, 4.965), (18.5, 3.12), (cvp, "2")], width=W)
    t.via("+5V", 19.3, 2.2)
    t.wire("+5V", [(cvp, "2"), (19.3, 2.2)], width=W)
    t.gnd_stub(cvp, "1", (19.6, 5.2), sym=(0, 0))
    t.gnd_stub(u, "5", (17.0, 8.6), sym=(0, 0))
    t.via("+5V", 6.0, 4.0)
    t.wire("+5V", [(xh, "1"), (6.0, 4.0)], width=0.4)
    t.gnd_stub(xh, "2", (6.0, 6.5), sym=(0, 0))
    t.wire("-5V", [(u, "4"), (11.0, 7.505), (11.0, 9.6), (cvn, "1")], width=W)
    t.gnd_stub(cvn, "2", (13.3, 9.6), sym=(0, 0))
    rail(t, "-5V", (11.0, 8.4), "above")
    t.titles.append("Load cell")
    t.result = "OUT = 201 x the bridge's output: about 1 V at full load for a 1 mV/V cell; about 10 kHz wide"
    t.notes = ["INA828 at G = 1 + 50 k / 249 = 201 on +-5 V, REF on ground; the bridge excited from +5 V.  Weigh, feel a force, close a",
               "force loop with the servo or the linear amplifier.  Cable: 1 red E+, 2 black E-, 3 white S-, 4 green S+."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


def tiles():
    return [tile_m6(), tile_m5(), tile_m2(), tile_m9(), tile_m10(), tile_m11(), tile_m4(), tile_m7(), tile_m8(), tile_m3(), tile_m1()]


GND_LOOPS = [(80.0, 95.8), (88.0, 95.8)]                 # the bottom margin under m8's right cell, clear of the back's text
FIDUCIALS = [(3.5, 50.0), (96.5, 50.0), (60.0, 96.8)]    # off m2's jack and terminal in the right margin
HOLES = []
FEET = [(5.0, 5.0), (95.0, 5.0), (95.0, 95.0), (5.0, 85.0)]
SLOTS = []
# the rails on L3: +5 V under the board; -5 V in the gutters under rows 0 and 2, joined down the left margin; +3.3 V in
# the gutter under row 1.  +5 V keeps a way between the rows round the right margin.
RAIL_POURS = [("+5V", 0.6, 0.6, 99.4, 99.4, 0),
              ("-5V", [(1.0, 27.75), (93.6, 27.75), (93.6, 29.25), (6.5, 29.25), (6.5, 70.75), (93.0, 70.75), (93.0, 72.25), (6.5, 72.25),
                       (6.5, 94.5), (1.0, 94.5)], 1),
              ("+3V3", 7.0, 49.25, 93.0, 50.75, 1)]
# m4's four Pmod lines on the back down the left margin to the plug under m3, in lanes that never cross: B's (from vias
# beside its driver) above A's and outermost, the farther the lower at the plug; IO8 ends on the via m3 takes along the
# channel between the rows into pad 5
# m4's four Pmod lines on the back: up from the vias above its drivers to the gutter over m4 (and the frame band under
# it), left along it to the left margin, down the margin to the plug under m3 -- B's above and outside A's, the outermost
# lane the lowest at the plug (IO8 ends on the via m3 takes along the channel between the rows into pad 5)
_M4 = (7.75, 50.75)
def _m4(x, y):
    return (_M4[0] + x, _M4[1] + y)
_A_IN1, _A_IN2 = (13.0 - 0.635, 11.8 - 3.45 - 1.1), (13.0 + 0.635, 11.8 - 3.45 - 1.1)
_B_IN1, _B_IN2 = (35.0 - 0.635, 11.8 - 3.45 - 1.1), (35.0 + 0.635, 11.8 - 3.45 - 1.1)
BACK_WIRES = [("/PMOD8", [_m4(*_B_IN2), _m4(_B_IN2[0], -1.3), (2.4, _M4[1] - 1.3), (2.4, 96.5)]),
              ("/PMOD4", [_m4(*_B_IN1), _m4(_B_IN1[0], -0.75), (3.15, _M4[1] - 0.75), (3.15, 93.85), (9.45, 93.85), (9.45, 95.23)]),
              ("/PMOD3", [_m4(*_A_IN2), _m4(_A_IN2[0], -0.2), (3.85, _M4[1] - 0.2), (3.85, 93.15), (11.99, 93.15), (11.99, 95.23)]),
              ("/PMOD2", [_m4(*_A_IN1), _m4(_A_IN1[0], 0.35), (4.55, _M4[1] + 0.35), (4.55, 92.45), (14.53, 92.45), (14.53, 95.23)])]
BACK_TEXT_X = 66.5                      # in the bottom margin between m3's regulator and the ground loops
QR_AT = (78.0, 58.9)                    # under m7's right cell (the TCA0372 and its chain are all SMD): 17 mm with no hole
BACK_TEXT = ["AMOD-M: motors.  Motor supply",
             "5-16 V on m2; USB-C 5 V on m1."]
FRONT_TEXT = []


PMOD_HOST = "the bottom margin under m3"
PMOD_NAMES = {"/PMOD1": "m3's IN2 (the DC motor's second input)", "/PMOD2": "m4's coil A IN1",
              "/PMOD3": "m4's coil A IN2", "/PMOD4": "m4's coil B IN1",
              "/PMOD5": "m3's encoder A (3.3 V logic)", "/PMOD6": "m3's encoder B (3.3 V logic)",
              "/PMOD7": "m3's IN1 (the DC motor's first input)", "/PMOD8": "m4's coil B IN2"}
HANDBOOK_INTRO = [
    "Eleven tiles on sixteen 20 mm cells, four layers.  m1 takes 5 V from its USB-C and makes -5 V (40 mA) and 3.3 V, as",
    "AMOD-A's a1 does; m2 takes the motor supply, 5-16 V on a 5.5 / 2.1 mm barrel jack (centre positive), and joins the",
    "USB's 5 V to it through Schottky diodes, so small motors run with no supply at about 4.6 V.  That rail, VMOT, runs",
    "on a wide track down the back and is not switched.  The DC motor and the stepper take their commands from the FPGA",
    "on the Pmod plug in the bottom margin under m3; everything else takes its command from a DAC and answers to an ADC",
    "over SMA, as on the other boards.  A powered tile has a slide switch along its left edge (slider up: on); the motor",
    "drivers' current limits and the buck's driver hang off it.  A port's name is in capitals on its tile's frame, a",
    "terminated input says so (CMD 50R) and an output read through a divider says its ratio (VM /16).  The back of each",
    "tile says what to know while cabling it."]
HANDBOOK_SECTIONS = [
    ["## The tiles together", "",
     "1. **Drives.**  m3 runs a brushed motor with its encoder (drive, brake or coast from two FPGA lines; its current",
     "   and its terminal voltage on jacks, so the back-EMF shows in the coast intervals); m4 runs a bipolar stepper from",
     "   four lines (full, half or PWM microsteps in gateware); m5 squares a DAC's pulse for a hobby servo; m6 switches",
     "   a solenoid and shows its flyback three ways.",
     "2. **Power stages the FPGA closes the loop on.**  m7 is a DC-coupled bridge amplifier (the load sees 4 x the DAC,",
     "   both ways) for a voice coil, a speaker used as an actuator or a maglev's electromagnet; m8 is a synchronous",
     "   buck's power stage, its PWM from a DAC and its inductor current and output on jacks.",
     "3. **Sensors for those loops.**  m9 a linear hall sensor (a magnet's distance, a maglev's gap), m10 a reflective",
     "   optical sensor (distance in the first millimetres, marks on a wheel), m11 a load cell's amplifier (force).",
     "",
     "A position servo: m3's encoder into the gateware, its PWM back out.  A maglev: m7 drives the electromagnet, m9",
     "under it reads the gap, the gateware closes the loop at tens of kilohertz.  Every motor tile's supply is VMOT: a",
     "bench supply's current limit, or the USB's, is the board's only fuse."]]

# The back panels (gen_pcb.back_panels): under each tile, what a user must know while cabling it.
BACK = {
    "m1": ["USB-C 5 V only", "+5 V 1.5 A", "-5 V 40 mA", "+3.3 V 300 mA"],
    "m2": ["5-16 V, centre +", "or USB 5 V alone", "VMOT = in - 0.4 V", "not switched"],
    "m3": ["IN1 IO7, IN2 IO1", "2 A limit", "I 0.98 V/A", "V = motor / 13", "PH: M1 G A B 3V3 M2"],
    "m4": ["A: IN1 IO2, IN2 IO3", "B: IN1 IO4, IN2 IO8", "1 A per coil", "XH: A+ A- B+ B-"],
    "m5": ["CMD 1-2 ms / 20 ms", "header: S + -", "I 1 V/A"],
    "m6": ["CMD high: coil on", "jumper 1-2: diode", "2-3: 24 V TVS", "none: avalanche", "VD = drain / 52"],
    "m7": ["load = 4 x IN", "IN +-1 V", "1 W in the chip:", "8 ohm at 5-6 V", "I 1 V/A both ways"],
    "m8": ["PWM 100-500 kHz", "VO = duty x VMOT", "load up to 1 A", "I 1 V/A, VO /16"],
    "m9": ["9.75 mV/mT", "+-85 mT", "sensor top left"],
    "m10": ["target 1 mm up", "OUT 0.1-0.9 V", "sensor top left"],
    "m11": ["1 red E+  2 black E-", "3 white S-", "4 green S+", "gain 201"],
}
BACK_PLOTS = {}                         # m7's clipping plot found no room beside the QR code over its right cell
