"""AMOD-B: brushless, rev A (Prompt 19).  Sixteen cells, four layers, USB-C power on b1 as AMOD-A's a1 and a motor supply
of 5-12 V on b2 (a barrel jack), with the USB's 5 V joining it through a Schottky.  A gimbal motor (a GBM2804H-100T
class, 12N14P) on four radial slots over an MT6701 magnetic angle sensor and two linear hall sensors in the middle of
the board, on a 2 x 2 tile; a DRV8311H three-phase driver under it from three FPGA PWM lines, its low-side current
amplifiers on jacks and a DAC's COAST that lets every phase float; the bus current and one phase's current in line, the
phase voltages against a virtual neutral (the back-EMF), the encoder's analog angle, the halls, an index sensor under
the rotor's rim, a vibration pickup and an IMU on SPI.  PLAN.md section 14 has the decisions; the parts research of
2026-10-28 the choices.

Jason, Prompt 19: "3-pole BLDC motor (like for a drone or even better a gimbal), along with encoders or magnetic back
reaction or some other fast mechanical feedback."  The brushed motors and the slow actuators are AMOD-M.

L1 the parts and the drawn wires, L2 ground, L3 the rails (+5 V under the board; -5 V in the gutters under rows 0 and 2,
along the bottom margin and down the left margin; +3.3 V in the gutter under row 1, which runs under the gimbal's middle,
with a band over the gimbal's side slots, which cut the strip, so the middle under the encoder joins the rest), L4
ground with the motor rail (VMOT from b2 down the gutter between columns 2 and 3 to b12's shunt, VMB from it on to the
driver), the lines between tiles (the Pmod's SPI lines up the gutter between columns 0 and 1 to b6, the encoder's,
the halls' and the index's from b5; BACK_WIRES) and the back-side text.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
sys.path.insert(0, HERE)
import tiles as T
from tiles import Tile, power_header, HDR_VS
import geometry as G
from amod_a import power_tile

STEM = "amod_b"
LAYERS = 4
BUS_X = 71.5                    # board x of VMOT and VMB on the back: the gutter between columns 2 and 3
BUS_END = 54.0                  # board y where VMOT ends at b12's shunt
VMB_START, VMB_END = 56.35, 82.85   # board y of VMB's run down the same gutter, from b12 to the driver's tap
W = 0.25
WP = 1.0                        # VMOT on the front inside a tile
VM = "/VMOT"                    # the motor supply, a board-wide net
VMB = "/VMB"                    # the same after b12's shunt: the driver's supply


def rail(t, net, pt, gutter):
    """A rail from a point in the tile to its strip on L3: a via at the point, the back to a via in the gutter at the same
    x (gutter: "below" 20.5, "above" -0.75)."""
    y = {"below": t.h + 0.5, "above": -0.75}[gutter]
    t.wire(net, [pt, (pt[0], y)], layer="B.Cu", silk=False)
    t.via(net, pt[0], y)


def diff_amp(t, x, y, io, out_net, jack_pin, ref="RFN"):
    """The current monitors' second stage (as AMOD-M's m7): an OPA810 on +-5 V at (x, y) turned 0 that gives (2.5 V - IO)
    / 2 (20 k in, 10 k back, its + input at 5 V x 2 k / 12 k = 0.833 V: no capacitor, so +5 V's noise cancels against
    the INA181's 1 k / 1 k reference).  Returns the parts; the tile wires IO in and DO out."""
    ud = t.add("U", "OPA810", "OPA810", x, y, 0, {"1": "DO", "2": "-5V", "3": "DP", "4": "DN", "5": "+5V"}, hide_value=False, label=None)
    r1 = t.add("R", "R0402 20k", "20k", x, y + 2.8, 0, {"1": io, "2": "DN"}, label=None)
    r2 = t.add("R", "R0402 10k", "10k", x + 0.3, y - 3.0, 0, {"1": "DO", "2": "DN"}, label=None)
    r3 = t.add("R", "R0402 10k", "10k", x - 3.8, y + 1.6, 90, {"1": "+5V", "2": "DP"}, label=None)       # pad 2 up
    r4 = t.add("R", "R0402 2k", "2k", x - 2.6, y + 1.6, 90, {"1": "GND", "2": "DP"}, label=None)
    # feedback over the top: DO up, r2, down the right to -IN; +5 V's via inside the loop
    t.wire("DO", [(ud, "1"), (x - 1.137, y - 3.0), (r2, "1")], width=W)
    t.wire("DN", [(r2, "2"), (x + 2.6, y - 3.0), (x + 2.6, y + 0.95), (ud, "4")], width=W)
    t.wire("DN", [(x + 2.6, y + 0.95), (x + 2.6, y + 2.8), (r1, "2")], width=W)
    t.via("+5V", x + 1.55, y - 1.9)
    t.wire("+5V", [(ud, "5"), (x + 1.55, y - 1.9)], width=W)
    t.wire("DP", [(ud, "3"), (x - 2.6, y + 0.95), (r4, "2")], width=W)
    t.wire("DP", [(x - 2.6, y + 0.95), (x - 3.8, y + 0.95), (r3, "2")], width=W)
    t.via("+5V", x - 3.8, y + 3.0)
    t.wire("+5V", [(r3, "1"), (x - 3.8, y + 3.0)], width=W)
    t.gnd_stub(r4, "1", (x - 2.6, y + 3.0), sym=(0, 0), width=W)
    return dict(ud=ud, r1=r1, r2=r2)


# ------------------------------------------------------------------------------------------------------------ b1 --
def tile_b1():
    return power_tile("b1", sections=["Motors"])


# ------------------------------------------------------------------------------------------------------------ b2 --
def tile_b2():
    """The motor supply, one cell at the right edge (AMOD-M's m2 with a 12 V clamp): a 5.5 / 2.1 mm barrel jack (its face
    at the edge) through an SS34 into VMOT, the USB's +5 V through another; an SMBJ12A (20 V clamp, under the DRV8311's
    24 V absolute maximum) and 220 uF on VMOT, which take a motor's braking energy; a green LED; VMOT / 16 (15 k / 1 k)
    through 49.9 ohm on the VM jack.  VMOT leaves on the back left to the gutter beside the tile and down it to b12."""
    t = Tile("b2", "motor supply", [(3, 0)], supply=None, subtitle="5-12 V in", sections=["Motors"])
    t.jack("TL", "VM", "VMJ", "out", "", silk="VM /16")
    t.pwr_flags = [VM, "VEXT"]
    jdc = t.add("J", "DC005", "5-12V", 17.15, 13.35, 180, {"1": "VEXT", "2": "GND", "3": "GND"}, hide_value=True)
    ce = t.add("C", "ELCO220U", "220u", 13.0, 4.9, 0, {"1": VM, "2": "GND"}, label=None)                 # pad 1 (+) left
    dz = t.add("D", "SMBJ12A", "SMBJ12A", 2.6, 14.0, 270, {"1": VM, "2": "GND"}, label=None)              # K up
    dx = t.add("D", "SS34", "SS34", 8.7, 11.3, 0, {"1": VM, "2": "VEXT"}, label=None)                     # K left
    du = t.add("D", "SS34", "SS34", 8.7, 15.0, 0, {"1": VM, "2": "+5V"}, label=None)
    ro = t.add("R", "R0402 49.9R", "49.9", 0.6, 6.4, 90, {"1": "VD", "2": "VMJ"}, label=None)
    rd2 = t.add("R", "R0402 1k", "1k", 0.6, 9.0, 270, {"1": "VD", "2": "GND"}, label=None)
    rd1 = t.add("R", "R0402 15k", "15k", 2.6, 9.3, 180, {"1": VM, "2": "VD"}, label=None)
    led = t.add("LED", "LED_G", "VM", 4.0, 18.9, 0, {"1": "GND", "2": "LA"}, label=None)
    rl = t.add("R", "R0402 4.7k", "4.7k", 7.3, 18.9, 0, {"1": "LA", "2": VM}, label=None)
    t.wire("VEXT", [(jdc, "1"), (13.0, 15.7), (13.0, 11.3), (dx, "2")], width=WP)
    t.wire(VM, [(du, "1"), (6.7, 11.3), (dx, "1")], width=WP)
    t.wire(VM, [(6.7, 11.3), (dz, "1")], width=WP)
    t.wire(VM, [(6.7, 11.3), (6.7, 9.5), (10.3, 9.5), (ce, "1")], width=WP)
    t.wire(VM, [(du, "1"), (6.7, 17.4), (rl, "2")], width=W)
    t.wire(VM, [(6.7, 9.5), (rd1, "1")], width=W)
    # the bus: two vias between the Schottkys, the back left to the gutter beside the tile and down it to b12
    bx = BUS_X - t.x0
    for xv in (5.9, 7.5):
        t.via(VM, xv, 13.15)
    t.wire(VM, [(5.9, 13.15), (7.5, 13.15)], width=WP)
    t.wire(VM, [(7.5, 13.15), (5.9, 13.15), (bx, 13.15), (bx, BUS_END - t.y0)], width=1.6, layer="B.Cu", silk=False)
    t.via("+5V", 10.7, 16.75)
    t.wire("+5V", [(du, "2"), (10.7, 16.75)], width=WP)
    t.wire("VD", [(rd1, "2"), (rd2, "1")], width=W)
    t.wire("VD", [(rd2, "1"), (ro, "1")], width=W)
    t.wire("VMJ", [(ro, "2"), (0.6, 4.75), ("J%d01" % t.idx, "1")])
    for ref_, pad, pt in ((rd2, "2", (0.6, 10.6)), (led, "1", (2.6, 18.3)), (dz, "2", (2.6, 18.3)), (ce, "2", (17.9, 6.6)),
                          (jdc, "2", (20.15, 19.0)), (jdc, "3", (19.8, 9.3))):
        t.gnd_stub(ref_, pad, pt, sym=(0, 0), width=W)
    t.wire("LA", [(led, "2"), (rl, "1")], width=W)
    t.titles.append("Motor supply")
    t.result = "VMOT = the larger of the barrel jack (5-12 V) and USB 5 V, each less a Schottky's 0.3-0.5 V; VM jack VMOT / 16"
    t.notes = ["Barrel jack (centre +), 5-12 V, through an SS34 into VMOT, as is USB's 5 V, so VMOT is about 4.6 V with no supply.",
               "SMBJ12A and 220 uF on VMOT take the braking energy a motor returns.  VM: VMOT / 16 at high impedance."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ----------------------------------------------------------------------------------------------------------- b12 --
def tile_b12():
    """The bus current, one cell beside the gimbal: VMOT from b2 through 0.1 ohm (VMB on to the driver), read by an
    INA181A1 about 2.5 V and an OPA810 as AMOD-M's m7: I = the driver's supply current, 1 V/A both ways (negative while
    the motor brakes and gives its energy back), through 49.9 ohm.  With VM it is the electrical power in; against the
    phase currents it is the driver's losses.  The shunt and the INA181 in the top-left corner beside the bus, the
    difference amplifier right of them, I bottom right."""
    t = Tile("b12", "bus current", [(3, 2)], supply="+-5 V", subtitle="INA181", sections=["Motors"])
    t.pwr_flags = [VMB]
    t.jack("BR", "I", "IJ", "out", "", silk="I 1V/A")
    bx = BUS_X - t.x0
    rsh = t.add("R", "R1206 0.1R", "0.1", 3.0, 3.25, 0, {"1": VM, "2": VMB}, label=None)
    t.via(VM, bx, BUS_END - t.y0)
    t.wire(VM, [(bx, BUS_END - t.y0), (rsh, "1")], width=WP)
    # VMB: a via beside the shunt, the back left to the gutter and down it to the driver
    t.via(VMB, 5.9, 3.25)
    t.wire(VMB, [(rsh, "2"), (5.9, 3.25)], width=WP)
    t.wire(VMB, [(5.9, 3.25), (5.9, VMB_START - t.y0), (bx, VMB_START - t.y0), (bx, VMB_END - t.y0)], width=1.2, layer="B.Cu", silk=False)
    # the INA181 turned 180 under the shunt: IN- up to the VMOT end, IN+ to the VMB end (so IO falls as the current rises)
    ina = t.add("U", "INA181A1", "INA181", 3.0, 8.6, 180, {"1": "IO", "2": "GND", "3": VMB, "4": VM, "5": "RFN", "6": "+5V"},
                hide_value=False, label=None)
    t.wire(VM, [(1.6, 4.1), (1.6, 6.9), (ina, "4")], width=W)
    t.wire(VMB, [(4.4, 4.1), (4.4, 6.9), (ina, "3")], width=W)
    t.gnd_stub(ina, "2", (5.6, 8.6), sym=(0, 0), width=W)
    rr1 = t.add("R", "R0402 1k", "1k", 1.0, 13.4, 90, {"1": "+5V", "2": "RFN"}, label=None)              # pad 2 up
    rr2 = t.add("R", "R0402 1k", "1k", 2.2, 13.4, 90, {"1": "GND", "2": "RFN"}, label=None)
    cvi = t.add("C", "C0402 100nF", "100n", 4.6, 12.0, 0, {"1": "+5V", "2": "GND"}, label=None)
    t.wire("RFN", [(rr1, "2"), (rr2, "2")], width=W)
    t.route("RFN", [(ina, "5"), (rr1, "2")], width=W)
    t.route("+5V", [(ina, "6"), (cvi, "1")], width=W)
    t.via("+5V", 1.0, 15.0)
    t.wire("+5V", [(rr1, "1"), (1.0, 15.0)], width=W)
    t.via("+5V", 4.12, 13.2)
    t.wire("+5V", [(cvi, "1"), (4.12, 13.2)], width=W)
    t.gnd_stub(cvi, "2", (5.2, 13.2), sym=(0, 0), width=W)
    t.gnd_stub(rr2, "1", (2.2, 15.0), sym=(0, 0), width=W)
    # the difference amplifier; its -5 V from a via beside it, on the back down to the gutter under the tile
    D = diff_amp(t, 11.0, 6.8, "IO", "DO", None)
    t.route("IO", [(ina, "1"), (D["r1"], "1")], width=W)
    cdn = t.add("C", "C0402 100nF", "100n", 7.6, 5.4, 90, {"1": "-5V", "2": "GND"}, label=None)           # pad 2 up
    t.via("-5V", 8.6, 6.8)
    t.wire("-5V", [(D["ud"], "2"), (8.6, 6.8)], width=W)
    t.wire("-5V", [(8.6, 6.8), (7.6, 6.3), (cdn, "1")], width=W)
    t.wire("-5V", [(8.6, 6.8), (9.5, 7.7), (9.5, t.h + 0.5)], width=W, layer="B.Cu", silk=False)
    t.via("-5V", 9.5, t.h + 0.5)
    t.gnd_stub(cdn, "2", (7.6, 4.0), sym=(0, 0), width=W)
    ro = t.add("R", "R0402 49.9R", "49.9", 15.25, 10.6, 90, {"1": "IJ", "2": "DO"}, label=None)             # pad 2 up
    t.wire("DO", [(9.863, 3.8), (9.863, 2.2), (15.25, 2.2), (ro, "2")], width=W)
    t.wire("IJ", [(ro, "1"), ("J%d01" % t.idx, "1")])
    t.titles.append("Bus current")
    t.result = "I = the driver's supply current, 1 V/A (+-1.2 A), negative while the motor brakes"
    t.notes = ["VMOT through 0.1 ohm to the driver; an INA181A1 (2.5 V on REF) and an OPA810 give I = 1 V/A both ways.  With VM: the",
               "electrical power in; against the phase currents: the driver's losses; negative while the motor's energy comes back."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ b5 --
GIMBAL_R_HALL = 14.5            # the halls under the rotor's magnets (a 2804's bell is 35 mm across)
GIMBAL_R_INDEX = 16.5           # the index sensor under the bell's rim
# the vias the board's back wires join (tile mm): b6's SPI lanes' ends and the encoder's line's starts, b7's, b9's and b10's
B6_VIA = {"/PMOD8": (12.45, 15.5), "/PMOD4": (13.35, 15.0), "/PMOD7": (12.45, 14.5), "/PMOD3": (14.4, 13.5), "/PMOD6": (18.6, 12.4),
          "SCK_ENC": (13.35, 10.6), "/ENC_DO": (18.9, 9.4)}
B7_VIA = {"/ANG": (5.1, 8.92), "+3V3": (14.3, 4.6)}
B9_VIA = {"/IDX_E": (4.5, 16.4), "/IDX_C": (10.7, 14.4)}
B10_VIA = {"/HALLA": (9.4, 6.12), "/HALLB": (0.5, 15.52)}
# the encoder's vias under its body (b5 mm): the SSI lines' on the left, OUT's and VDD's on the right
ENC_VIA = {"/ENC_DO": (19.95, 20.115), "/PMOD4": (19.95, 21.385), "/PMOD6": (19.95, 22.655), "/ANG": (20.85, 20.115), "+3V3": (21.6, 20.75)}


def tile_b5():
    """The gimbal motor, four cells in the middle of the board: its stator on four radial slots (3.4 mm wide, 6-10 mm
    from the centre: M2-M3 screws on any of the patterns reported for a 2804, the motor turned to suit) over an MT6701
    (14-bit, SSI: CLK on SCK, CSN on CS ENC, DO to b6's buffer, which puts it on MISO only while CS ENC is low; its
    analog angle and its 3.3 V to b7) at the centre, where a 6 x 2.5 mm diametric magnet on the shaft's end
    sits 0.5-2 mm above it (the motor on spacers); two DRV5055A3 linear halls under the rotor's magnets 14.5 mm out,
    17.1 degrees apart (120 electrical degrees for 7 pole pairs), to b10; a QRE1113 under the bell's rim 16.5 mm out
    toward b9 reads a white mark once a turn.  The motor's leads go to b3's terminal; no jacks here (the bell would
    cover them).  The motor's outline and its stator's are drawn on the silk."""
    t = Tile("b5", "gimbal", [(1, 1), (2, 1), (1, 2), (2, 2)], supply="+3.3 V, +5 V", subtitle="MT6701", sections=["Motors"])
    cx = cy = t.w / 2
    for k, (dx, dy, rot) in enumerate(((8.0, 0.0, 90), (-8.0, 0.0, 90), (0.0, -8.0, 0), (0.0, 8.0, 0))):
        t.add("H", "SLOT_MOTOR", "", cx + dx, cy + dy, rot, {}, hide_value=True, label=None)
    t.draw_arc(cx, cy, 17.5, -45, 330)                # the bell, open over the index sensor at -60 degrees
    t.draw_arc(cx, cy, 12.5, 0, 360)                  # the stator's base, outside the slots
    # the MT6701 at the centre, turned 180: DO, SCK, CS ENC on the left to vias under its body, whose lines run on the back
    # between the slots down to the left (to b6); OUT and VDD on the right to vias under it, their lines up between the
    # slots to the left (to b7).  VDD's via is on the +3.3 V strip (the gutter between rows 1 and 2 runs under the middle)
    enc = t.add("U", "MT6701", "MT6701", cx, cy, 180, {"1": "+3V3", "3": "/ANG", "4": "GND", "6": "/ENC_DO", "7": "/PMOD4", "8": "/PMOD6"},
                hide_value=True, label=None)
    for net, pin, y in (("/ENC_DO", "6", cy - 0.635), ("/PMOD4", "7", cy + 0.635), ("/PMOD6", "8", cy + 1.905)):
        t.via(net, *ENC_VIA[net], fine=True)
        t.wire(net, [(enc, pin), ENC_VIA[net]], width=0.2)
    t.via("/ANG", *ENC_VIA["/ANG"], fine=True)
    t.wire("/ANG", [(enc, "3"), ENC_VIA["/ANG"]], width=0.2)
    t.via("+3V3", *ENC_VIA["+3V3"], fine=True)
    t.wire("+3V3", [(enc, "1"), (ENC_VIA["+3V3"][0], cy + 1.905), ENC_VIA["+3V3"]], width=0.2)
    cenc = t.add("C", "C0402 100nF", "100n", cx + 3.85, cy + 3.35, 0, {"1": "+3V3", "2": "GND"}, label=None)
    t.wire("+3V3", [(enc, "1"), (cx + 3.37, cy + 1.905), (cenc, "1")], width=0.2)
    t.gnd_stub(cenc, "2", (cx + 5.25, cy + 3.85), sym=(0, 0), width=W)
    t.gnd_stub(enc, "4", (cx + 3.95, cy - 3.15), sym=(0, 0), width=W)
    # the halls 14.5 mm out on the left, 17.1 degrees apart, each with its 100 nF; their outputs on vias for b10
    for k, sgn in enumerate((-1, 1)):
        a = math.radians(180 + sgn * 120.0 / 7 / 2)
        hx, hy = cx + GIMBAL_R_HALL * math.cos(a), cy + GIMBAL_R_HALL * math.sin(a)
        net = "/HALL%s" % "BA"[k]                     # A the upper one, whose line goes up b10 to its upper stage
        h = t.add("U", "DRV5055A3", "DRV5055", hx, hy, 0, {"1": "+5V", "2": net, "3": "GND"}, hide_value=True, label=None)
        outer = hy > cy
        cy_c = hy + 3.0 if outer else hy - 3.0
        ch = t.add("C", "C0402 100nF", "100n", hx, cy_c, 0, {"1": "+5V", "2": "GND"}, label=None)
        if outer:                                     # the lower: VDD to a via of its own, the capacitor below on another
            t.via("+5V", hx - 2.0, hy - 0.95)
            t.wire("+5V", [(h, "1"), (hx - 2.0, hy - 0.95)], width=W)
        else:
            t.wire("+5V", [(h, "1"), (hx - 0.938, cy_c), (ch, "1")], width=W)
        t.via("+5V", hx - 2.0, cy_c)
        t.wire("+5V", [(ch, "1"), (hx - 2.0, cy_c)], width=W)
        t.gnd_stub(h, "3", (hx + 2.0, hy), sym=(0, 0), width=W)
        t.gnd_stub(ch, "2", (hx + 1.6, cy_c), sym=(0, 0), width=W)
        t.via(net, hx - 2.4, hy + 0.95)
        t.wire(net, [(h, "2"), (hx - 2.4, hy + 0.95)], width=W)
    # the index sensor under the rim toward b9: its LED from +5 V through 180 ohm; collector and emitter on vias for b9
    a = math.radians(-60.0)
    qx, qy = cx + GIMBAL_R_INDEX * math.cos(a), cy + GIMBAL_R_INDEX * math.sin(a)
    q = t.add("U", "QRE1113GR", "QRE1113", qx, qy, 0, {"1": "QLA", "2": "GND", "3": "/IDX_C", "4": "/IDX_E"}, hide_value=True, label=None)
    rq = t.add("R", "R0805 180R", "180", qx - 0.9, qy - 4.86, 0, {"1": "+5V", "2": "QLA"}, label=None)
    t.wire("QLA", [(rq, "2"), (qx, qy - 3.6), (qx - 0.9, qy - 2.83), (q, "1")], width=W)
    t.via("+5V", qx - 3.0, qy - 4.86)
    t.wire("+5V", [(rq, "1"), (qx - 3.0, qy - 4.86)], width=W)
    t.gnd_stub(q, "2", (qx - 2.6, qy + 2.0), sym=(0, 0), width=W)
    t.via("/IDX_E", qx + 2.4, qy - 2.0)
    t.wire("/IDX_E", [(q, "4"), (qx + 2.4, qy - 2.0)], width=W)
    t.via("/IDX_C", qx + 3.2, qy + 2.0)
    t.wire("/IDX_C", [(q, "3"), (qx + 3.2, qy + 2.0)], width=W)
    t.titles.append("Gimbal")
    t.result = "the MT6701's angle on SSI (14 bits a turn) and as a sawtooth to b7; two hall signals 120 electrical degrees apart to b10; an index pulse to b9"
    t.notes = ["A GBM2804H-100T class gimbal motor on four slots over an MT6701 (SSI on the Pmod; DO through b6's buffer onto MISO);",
               "a 6 x 2.5 mm diametric magnet on the shaft 0.5-2 mm above it.  Two DRV5055A3 under the magnets, a QRE1113 under the rim."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ b3 --
def tile_b3():
    """The three-phase driver, two cells along the bottom, the Pmod plug in the margin under the left cell: a DRV8311H
    (3-20 V, 5 A peak, 210 mohm) from VMB in 3x PWM mode: INHA on Pmod IO5, INHB on IO1, INHC on IO2 set each phase
    high or low; the three INL pins together are EN, from COAST (a DAC's 0 / +1 V, terminated in 49.9 ohm) through a
    TLV3501 on the driver's own 3.3 V (AVDD): COAST high floats every phase, so the back-EMF shows on b4.  The strap pins
    left open: MODE 3x PWM with a 9 A trip, SLEW 180 V/us, GAIN 1 V/A.  nSLEEP from the tile's switch (10 k, 100 k
    down); nFAULT left open.  Its low-side current amplifiers SOA and SOB (CSAREF = AVDD: 1.65 V + 1 V/A) each shifted
    to 0 by 3.3 k from SOx and 10 k to -5 V (1.65 x 10 = 5 x 3.3): IA, IB = phase A's and B's currents while the low
    side conducts, 0.75 V/A from 2.5 k (no amplifier: an ADC's or a scope's high-impedance input reads them).  The motor on a 3-way screw terminal at the top of
    the right cell (wires in from the gimbal above), its phases C, B, A from the left; phase A out to b11's shunt and
    back.  The driver turned 90 in the middle (VM and the outputs to the right, INH up to vias for the Pmod lanes on the
    back, the current amplifiers down), COAST's comparator by its jack."""
    t = Tile("b3", "BLDC driver", [(1, 3), (2, 3)], supply="+5 V, VMOT, +-5 V", subtitle="DRV8311H", sections=["Motors"])
    t.fine = True
    t.jack("TL0", "COAST", "COASTJ", "in", "0/+1 V", silk="COAST 50R")
    t.jack("BR0", "IB", "IBJ", "out", "", silk="IB .75V/A")
    t.jack("BR1", "IA", "IAJ", "out", "", silk="IA .75V/A")
    power_header(t)
    X, Y = 21.0, 9.0
    drv = t.add("U", "DRV8311H", "DRV8311H", X, Y, 90, {"2": "AVDD", "4": "SOB", "5": "SOA", "6": "CP", "7": VMB, "8": VMB,
                                                        "9": "GND", "10": "/PHA", "11": "/PHB", "12": "/PHC", "13": "/PMOD2", "14": "/PMOD1",
                                                        "15": "/PMOD5", "16": "GND", "17": "AVDD", "18": "EN", "19": "EN", "20": "EN",
                                                        "24": "NSLP", "25": "GND"}, hide_value=False, label=None)
    F = 0.15                                                  # the fan-out at the 0.4 mm pitch
    for (dx, dy) in ((-0.475, -0.475), (0.475, -0.475), (-0.475, 0.475), (0.475, 0.475)):
        t.gnd_stub(drv, "25", (X + dx, Y + dy), sym=(0, 0), width=0.3, fine=True)
    t.wire("GND", [(drv, "9"), (X + 1.0, Y + 0.27)], width=0.2, silk=False)                  # PGND into the pad
    t.wire("GND", [(drv, "16"), (X, Y - 1.0)], width=0.2, silk=False)                        # AGND into the pad
    t.wire(VMB, [(drv, "7"), (X + 1.45, Y + 1.05), (drv, "8")], width=F)                     # VIN_AVDD round the corner to VM
    # ---- the phases: C, B, A fan out right at 0.2 mm, turn up in order to the terminal's pins 1, 2 (C, B); A on to b11
    tc = t.add("J", "TERM3", "motor", 33.2, 4.35, 0, {"1": "/PHC", "2": "/PHB", "3": "/PHAM"}, hide_value=True)
    t.wire("/PHC", [(drv, "12"), (23.6, Y - 0.93), (23.6, 6.3)], width=0.2)
    t.wire("/PHC", [(23.6, 6.3), (28.2, 6.3), (tc, "1")], width=0.6)
    t.wire("/PHB", [(drv, "11"), (24.6, Y - 0.53), (24.6, 7.3)], width=0.2)
    t.wire("/PHB", [(24.6, 7.3), (33.2, 7.3), (tc, "2")], width=0.6)
    t.wire("/PHA", [(drv, "10"), (25.6, Y - 0.13)], width=0.2)
    t.wire("/PHA", [(25.6, Y - 0.13), (43.0, Y - 0.13)], width=0.6)
    # the phases' taps for b4: up to the gutter over the tile, left along it and down to b4's dividers (no silk: the frame's
    # names sit over them); B's and A's hop the lanes above them on the back
    for ph, x, yl, xd in (("/PHC", 24.5, -0.35, -2.7), ("/PHB", 25.3, -0.75, -3.9), ("/PHA", 26.1, -1.15, -5.1)):
        ylane = {"/PHC": 6.3, "/PHB": 7.3, "/PHA": Y - 0.13}[ph]
        if ph == "/PHC":
            t.wire(ph, [(x, ylane), (x, yl), (xd, yl), (xd, 1.6)], width=0.2, silk=False)
        else:
            t.wire(ph, [(x, ylane), (x, 5.6)], width=0.2, layer="B.Cu", silk=False, fine=True)
            t.wire(ph, [(x, 5.6), (x, yl), (xd, yl), (xd, 1.6)], width=0.2, silk=False)
    # ---- VMB: from the bus on the back to a via in the gutter, the front along y 10.6 to VM; 100 nF and 10 uF on it
    bx = BUS_X - t.x0
    t.via(VMB, bx, 10.6)
    t.wire(VMB, [(drv, "8"), (23.2, Y + 0.67), (23.8, 10.27), (23.8, 10.6)], width=0.25)
    t.wire(VMB, [(23.8, 10.6), (bx, 10.6)], width=1.0)
    cvm = t.add("C", "C0402 100nF", "100n", 25.2, 12.0, 90, {"1": "GND", "2": VMB}, label=None)            # pad 2 up
    t.wire(VMB, [(cvm, "2"), (25.2, 10.9)], width=0.4)
    t.gnd_stub(cvm, "1", (26.2, 12.8), sym=(0, 0), width=W)
    cbk = t.add("C", "C0805 10uF", "10u", 28.4, 13.0, 0, {"1": "GND", "2": VMB}, label=None)
    t.wire(VMB, [(cbk, "2"), (29.35, 10.9)], width=0.6)
    t.gnd_stub(cbk, "1", (27.45, 14.4), sym=(0, 0), width=W)
    ccp = t.add("C", "C0402 100nF", "100n", 23.0, 11.9, 0, {"1": "CP", "2": VMB}, label=None)
    t.wire("CP", [(drv, "6"), (X + 0.8, 11.2), (ccp, "1")], width=F)
    t.wire(VMB, [(ccp, "2"), (23.8, 11.3), (23.8, 10.6)], width=0.25)
    # ---- EN: the three INL pins joined over the driver's top-left corner, from the comparator
    t.wire("EN", [(drv, "19"), (X - 1.2, 6.6)], width=F)
    t.wire("EN", [(drv, "18"), (X - 0.8, 6.6)], width=F)
    t.wire("EN", [(drv, "20"), (19.0, Y - 0.93), (19.0, 6.6), (X - 0.8, 6.6)], width=F)
    # ---- AVDD: up to a via; on the back to CSAREF's via under the driver and to the comparator's via; 1 uF there
    t.via("AVDD", X - 0.4, 6.1, fine=True)
    t.wire("AVDD", [(drv, "17"), (X - 0.4, 6.1)], width=F)
    t.via("AVDD", 19.6, 11.2, fine=True)
    t.wire("AVDD", [(drv, "2"), (X - 0.8, 10.8), (19.6, 11.2)], width=F)
    t.via("AVDD", 16.0, 6.1)
    t.wire("AVDD", [(X - 0.4, 6.1), (16.0, 6.1)], width=0.25, layer="B.Cu", silk=False)
    t.wire("AVDD", [(X - 0.4, 6.1), (19.6, 6.1), (19.6, 11.2)], width=0.25, layer="B.Cu", silk=False)
    cav = t.add("C", "C0603 1uF", "1u", 16.0, 7.6, 90, {"1": "GND", "2": "AVDD"}, label=None)              # pad 2 up
    t.wire("AVDD", [(16.0, 6.1), (cav, "2")], width=0.25)
    t.gnd_stub(cav, "1", (16.0, 9.0), sym=(0, 0), width=W)
    ccs = t.add("C", "C0402 100nF", "100n", 19.4, 12.4, 90, {"1": "GND", "2": "AVDD"}, label=None)       # CSAREF's, under its via
    t.wire("AVDD", [(19.6, 11.2), (19.4, 11.6), (ccs, "2")], width=0.2)
    t.wire("GND", [(ccs, "1"), (17.79, 12.71)], width=0.25, silk=False)                                  # to IB's jack's leg
    # ---- INH up to vias over the driver; on the back left above everything and down outside I's jack to the plug
    t.via("/PMOD5", 21.2, 4.6, fine=True)
    t.wire("/PMOD5", [(drv, "15"), (21.4, 5.0), (21.2, 4.6)], width=F)
    t.via("/PMOD1", 22.0, 4.0, fine=True)
    t.wire("/PMOD1", [(drv, "14"), (21.8, 6.6), (22.0, 6.4), (22.0, 4.0)], width=F)
    t.via("/PMOD2", 22.8, 3.4, fine=True)
    t.wire("/PMOD2", [(drv, "13"), (22.2, 6.6), (22.8, 6.0), (22.8, 3.4)], width=F)
    # ---- the Pmod plug in the margin under the left cell: INHB IO1, INHC IO2, INHA IO5 (the lanes nest so); SPI on the left
    pm = t.add("J", "PMOD", "Pmod", 2.97, 24.25, 0, {"1": "/PMOD_VCC", "2": "/PMOD_VCC", "3": "GND", "4": "GND", "5": "/PMOD8", "6": "/PMOD4",
                                                      "7": "/PMOD7", "8": "/PMOD3", "9": "/PMOD6", "10": "/PMOD2", "11": "/PMOD5", "12": "/PMOD1"}, hide_value=True)
    t.wire("/PMOD_VCC", [(pm, "1"), (pm, "2")], layer="B.Cu", silk=False)
    t.wire("GND", [(pm, "3"), (pm, "4")], width=0.5, layer="B.Cu", silk=False)
    t.wire("/PMOD2", [(22.8, 3.4), (9.8, 3.4), (9.8, 21.2), (6.78, 21.2), (pm, "10")], width=0.2, layer="B.Cu", silk=False)
    t.wire("/PMOD1", [(22.0, 4.0), (10.4, 4.0), (10.4, 21.6), (9.32, 22.0), (pm, "12")], width=0.2, layer="B.Cu", silk=False)
    t.wire("/PMOD5", [(21.2, 4.6), (11.0, 4.6), (11.0, 23.6), (10.59, 24.25), (9.9, 24.9), (pm, "11")], width=0.2, layer="B.Cu", silk=False)
    # ---- COAST: the comparator by its jack (as m5's, inputs swapped: COAST above the threshold pulls EN low)
    rt = t.add("R", "R0402 49.9R", "49.9", 4.75, 9.6, 270, {"1": "COASTJ", "2": "GND"}, label=None)
    rin = t.add("R", "R0402 10k", "10k", 9.4, 4.75, 0, {"1": "COASTJ", "2": "CN"}, label=None)
    rr2 = t.add("R", "R0402 10k", "10k", 10.4, 8.2, 0, {"1": "GND", "2": "TH"}, label=None)
    rr1 = t.add("R", "R0402 47k", "47k", 12.45, 8.2, 0, {"1": "TH", "2": "AVDD"}, label=None)
    u = t.add("U", "TLV3501", "TLV3501", 13.0, 5.4, 0, {"1": "CN", "2": "GND", "3": "TH", "4": "AVDD", "5": "EN", "6": "GND"}, hide_value=False, label=None)
    t.wire("COASTJ", [("J%d01" % t.idx, "1"), (rin, "1")])
    t.wire("COASTJ", [("J%d01" % t.idx, "1"), (rt, "1")])
    t.gnd_stub(rt, "2", (4.75, 10.95), sym=(0, 0), width=W)
    t.wire("CN", [(rin, "2"), (11.0, 4.75), (11.0, 4.45), (u, "1")], width=W)
    t.wire("TH", [(u, "3"), (11.3, 6.35), (11.3, 8.2)], width=W)
    t.wire("TH", [(rr2, "2"), (rr1, "1")], width=W)
    t.wire("AVDD", [(rr1, "2"), (14.0, 8.2), (14.8, 7.4), (15.2, 7.4), (15.2, 6.35), (u, "4")], width=W)
    t.wire("AVDD", [(15.2, 6.35), (15.2, 6.1), (16.0, 6.1)], width=W)
    t.gnd_stub(rr2, "1", (9.2, 8.2), sym=(0, 0), width=W)
    t.wire("GND", [(u, "2"), (13.0, 5.4), (13.0, 4.45), (u, "6")], width=W, silk=False)
    t.gnd_stub(u, "2", (13.0, 5.4), sym=(0, 0), width=W, fine=True)
    t.wire("EN", [(u, "5"), (15.6, 5.4), (15.6, 4.0), (19.0, 4.0), (19.0, 6.6)], width=W)
    # ---- nSLEEP from the switch through 10 k, 100 k down
    rns = t.add("R", "R0402 10k", "10k", 17.2, 10.4, 0, {"1": "VS", "2": "NSLP"}, label=None)
    rnp = t.add("R", "R0402 100k", "100k", 17.75, 9.3, 0, {"1": "GND", "2": "NSLP"}, label=None)
    t.wire("NSLP", [(drv, "24"), (18.6, Y + 0.67), (18.6, 10.4), (rns, "2")], width=F)
    t.wire("NSLP", [(18.6, 9.67), (rnp, "2")], width=F)
    t.wire("GND", [(rnp, "1"), (16.0, 9.0)], width=W, silk=False)
    t.wire("VS", [HDR_VS, (9.2, 17.4), (9.2, 10.4), (rns, "1")], width=0.3)
    # ---- the current amplifiers' level shift, passive: 3.3 k from SOx and 10 k to -5 V put the node at 0 V for 1.65 V
    # (1.65 x 10 = 5 x 3.3): 0.75 V/A from 2.5 k.  IB (SOB) to the left jack, IA (SOA, on the back) to the right one
    r1b = t.add("R", "R0402 3.3k", "3.3k", 20.6, 12.6, 90, {"1": "IBJ", "2": "SOB"}, label=None)          # pad 2 up
    r2b = t.add("R", "R0402 10k", "10k", 20.6, 16.4, 90, {"1": "-5V", "2": "IBJ"}, label=None)
    t.wire("SOB", [(drv, "4"), (X, 11.2), (20.6, 11.6), (r1b, "2")], width=F)
    t.wire("IBJ", [(r1b, "1"), (r2b, "2")], width=W)
    t.wire("IBJ", [(20.6, 13.6), (19.4, 13.6), (19.4, 15.25), ("J%d02" % t.idx, "1")], width=W)
    t.via("-5V", 20.6, t.h + 0.8)
    t.wire("-5V", [(r2b, "1"), (20.6, t.h + 0.8)], width=W)
    t.via("SOA", 21.6, 12.0, fine=True)
    t.wire("SOA", [(drv, "5"), (X + 0.4, 11.5), (21.6, 12.0)], width=F)
    t.via("SOA", 32.2, 12.2)
    t.wire("SOA", [(21.6, 12.0), (24.0, 12.0), (24.4, 12.2), (32.2, 12.2)], width=0.2, layer="B.Cu", silk=False)
    r1a = t.add("R", "R0402 3.3k", "3.3k", 32.2, 13.6, 90, {"1": "IAJ", "2": "SOA"}, label=None)
    r2a = t.add("R", "R0402 10k", "10k", 31.0, 16.6, 90, {"1": "-5V", "2": "IAJ"}, label=None)
    t.wire("SOA", [(32.2, 12.2), (r1a, "2")], width=W)
    t.wire("IAJ", [(r1a, "1"), (32.2, 15.25), ("J%d03" % t.idx, "1")], width=W)
    t.wire("IAJ", [(32.2, 15.25), (31.0, 15.25), (r2a, "2")], width=W)
    t.via("-5V", 31.0, t.h + 0.8)
    t.wire("-5V", [(r2a, "1"), (31.0, t.h + 0.8)], width=W)
    t.titles.append("BLDC driver")
    t.result = "the motor's phases at the duty cycles of IO5, IO1, IO2 (A, B, C); IA, IB = phase A's and B's currents (low side), 0.75 V/A; COAST high floats them"
    t.notes = ["DRV8311H in 3x PWM from VMB: INHA IO5, INHB IO1, INHC IO2; EN from COAST through a TLV3501 (high: every phase floats).",
               "IA, IB = SOA, SOB shifted to 0 by 3.3 k / 10 k to -5 V: 0.75 V/A from 2.5 k while each low side conducts.  The motor on the terminal: C, B, A from the left."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ b4 --
def tile_b4():
    """The back-EMF, one cell left of the driver: each phase through 13 k / 1 k (/14: 12 V reads 0.86 V); with every
    phase floating (b3's COAST) the three dividers are the motor's ground, so A and B read each phase against the
    neutral: its back-EMF, the sinusoid a spun motor makes.  A and B followed by an OPA2171 on +-5 V, through 49.9 ohm;
    C's divider keeps the star balanced.  The phases arrive on the front along the gutter over the tile from b3."""
    t = Tile("b4", "back-EMF", [(0, 3)], supply="+-5 V", subtitle="OPA2171", sections=["Motors"])
    t.jack("TL", "EA", "EAJ", "out", "", silk="EA /14")
    t.jack("BR", "EB", "EBJ", "out", "", silk="EB /14")
    divs = {}
    for ph, x in (("/PHA", 16.4), ("/PHB", 17.6), ("/PHC", 18.8)):
        net = "D" + ph[-1]
        r1 = t.add("R", "R0402 13k", "13k", x, 3.2, 90, {"1": net, "2": ph}, label=None)                  # pad 2 up
        r2 = t.add("R", "R0402 1k", "1k", x, 5.4, 90, {"1": "GND", "2": net}, label=None)
        t.wire(net, [(r1, "1"), (r2, "2")], width=W)
        t.wire(ph, [(x, 1.6), (r1, "2")], width=W)                         # b3's tap ends at (x, 1.6)
        t.gnd_stub(r2, "1", (x, 6.8), sym=(0, 0), width=W)
        divs[net] = (r1, r2)
    # the followers in the bottom-left quarter (the jacks hold two others): A's output up to EA, B's right to EB
    ua = t.add("U", "OPA2171", "OPA2171", 5.0, 14.0, 0, {"1": "EAO", "2": "EAO", "3": "DA", "4": "-5V", "5": "DB", "6": "EBO", "7": "EBO", "8": "+5V"},
               hide_value=False, label=None)
    t.route("DA", [(divs["DA"][1], "2"), (ua, "3")], width=W)
    t.route("DB", [(divs["DB"][1], "2"), (ua, "5")], width=W)
    t.wire("EAO", [(ua, "1"), (ua, "2")], width=W)
    t.wire("EBO", [(ua, "7"), (ua, "6")], width=W)
    roa = t.add("R", "R0402 49.9R", "49.9", 4.75, 10.2, 90, {"1": "EAO", "2": "EAJ"}, label=None)             # pad 2 up
    rob = t.add("R", "R0402 49.9R", "49.9", 9.9, 15.25, 0, {"1": "EBO", "2": "EBJ"}, label=None)
    t.wire("EAO", [(ua, "1"), (2.525, 11.3), (3.9, 11.3), (roa, "1")], width=W)
    t.wire("EAJ", [(roa, "2"), ("J%d01" % t.idx, "1")])
    t.wire("EBO", [(ua, "6"), (8.8, 14.635), (rob, "1")], width=W)
    t.wire("EBJ", [(rob, "2"), ("J%d02" % t.idx, "1")])
    cvp = t.add("C", "C0402 100nF", "100n", 10.0, 12.095, 0, {"1": "+5V", "2": "GND"}, label=None)
    t.wire("+5V", [(ua, "8"), (cvp, "1")], width=W)
    t.via("+5V", 9.52, 11.0)
    t.wire("+5V", [(cvp, "1"), (9.52, 11.0)], width=W)
    t.gnd_stub(cvp, "2", (10.6, 11.0), sym=(0, 0), width=W)
    cvn = t.add("C", "C0402 100nF", "100n", 2.525, 17.9, 90, {"1": "GND", "2": "-5V"}, label=None)          # pad 2 up
    t.wire("-5V", [(ua, "4"), (cvn, "2")], width=W)
    t.via("-5V", 1.2, 17.42)
    t.wire("-5V", [(cvn, "2"), (1.2, 17.42)], width=W)
    t.wire("-5V", [(1.2, 17.42), (-2.0, 17.42)], width=W, layer="B.Cu", silk=False)                     # to the left margin's -5 V
    t.gnd_stub(cvn, "1", (2.525, 19.4), sym=(0, 0), width=W)
    t.titles.append("Back-EMF")
    t.result = "EA, EB = phase A's and B's voltage / 14 against the neutral: with COAST high and the motor spun, its back-EMF"
    t.notes = ["Each phase through 13 k / 1 k; with every phase floating the three dividers are the motor's ground, so EA and EB read the",
               "back-EMF against the neutral (14 x EA in volts).  Followed by an OPA2171.  A spun gimbal motor makes a few volts."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ----------------------------------------------------------------------------------------------------------- b11 --
def tile_b11():
    """Phase A's current in line, one cell right of the driver: phase A from b3 through 0.05 ohm and back to the motor's
    terminal, read by an INA240A1 (common mode -4 to 80 V and its PWM rejection: the phase swings the whole supply at
    every edge) about half its 5 V (REF1 on 5 V, REF2 on ground) and an OPA810 that takes the 2.5 V away: IPA = the
    phase's whole current, both ways and through every PWM state, 1 V/A, through 49.9 ohm.  Set beside b3's IA (the
    low side only, sampled) it shows what a low-side amplifier misses."""
    t = Tile("b11", "phase current", [(3, 3)], supply="+-5 V", subtitle="INA240", sections=["Motors"])
    t.jack("BR", "IPA", "IJ", "out", "", silk="IPA 1V/A")
    rsh = t.add("R", "R1206 0.05R", "0.05", 3.6, 8.87, 0, {"1": "/PHA", "2": "/PHAM"}, label=None)
    t.wire("/PHA", [(-0.75, 8.87), (rsh, "1")], width=0.6)
    # the return to the terminal's pin 3, up and left along y 4.35
    t.wire("/PHAM", [(rsh, "2"), (5.6, 7.6), (5.6, 4.35), (-4.8, 4.35)], width=0.6)
    ina = t.add("U", "INA240A1", "INA240", 4.0, 13.4, 0, {"1": "/PHA", "2": "GND", "3": "GND", "4": "GND", "5": "IO", "6": "+5V", "7": "+5V", "8": "/PHAM"},
                hide_value=False, label=None)
    t.wire("/PHA", [(rsh, "1"), (2.1, 10.3), (1.525, 10.9), (ina, "1")], width=W, silk=False)
    t.route("/PHAM", [(rsh, "2"), (ina, "8")], width=W)
    cvi = t.add("C", "C0402 100nF", "100n", 8.6, 15.6, 90, {"1": "GND", "2": "+5V"}, label=None)
    t.route("+5V", [(ina, "6"), (ina, "7")], width=W)
    t.route("+5V", [(ina, "6"), (cvi, "2")], width=W)
    t.via("+5V", 8.6, 13.8)
    t.wire("+5V", [(cvi, "2"), (8.6, 13.8)], width=W)
    t.gnd_stub(cvi, "1", (8.6, 17.2), sym=(0, 0), width=W)
    t.route("GND", [(ina, "2"), (ina, "3")], width=W)
    t.route("GND", [(ina, "3"), (ina, "4")], width=W)
    t.gnd_stub(ina, "4", (0.8, 17.0), sym=(0, 0), width=W)
    # OUT = 2.5 V - IO, gain 1: IO through 10 k into -IN, 10 k back; +IN at 1.25 V from 20 k / 20 k of +5 V and 10 k down
    ud = t.add("U", "OPA810", "OPA810", 12.0, 7.0, 0, {"1": "DO", "2": "-5V", "3": "DP", "4": "DN", "5": "+5V"}, hide_value=False, label=None)
    r1 = t.add("R", "R0402 10k", "10k", 10.4, 10.6, 0, {"1": "IO", "2": "DN"}, label=None)
    r2 = t.add("R", "R0402 10k", "10k", 12.3, 3.8, 0, {"1": "DO", "2": "DN"}, label=None)
    r3 = t.add("R", "R0402 20k", "20k", 8.4, 5.2, 90, {"1": "DP", "2": "+5V"}, label=None)
    r4 = t.add("R", "R0402 20k", "20k", 8.0, 8.6, 90, {"1": "GND", "2": "DP"}, label=None)
    r5 = t.add("R", "R0402 10k", "10k", 9.2, 8.6, 90, {"1": "GND", "2": "DP"}, label=None)
    ro = t.add("R", "R0402 49.9R", "49.9", 15.25, 10.6, 90, {"1": "IJ", "2": "DO"}, label=None)
    t.wire("DO", [(r2, "1"), (11.82, 4.6), (10.863, 5.5), (ud, "1")], width=0.2)
    for (net, a, b) in (("IO", (ina, "5"), (r1, "1")), ("DN", (r1, "2"), (ud, "4")), ("DN", (r2, "2"), (ud, "4")),
                        ("DP", (r3, "1"), (ud, "3")), ("DP", (r4, "2"), (ud, "3")), ("DP", (r5, "2"), (r4, "2")), ("DO", (ud, "1"), (ro, "2"))):
        t.route(net, [a, b], width=0.2)
    t.wire("IJ", [(ro, "1"), ("J%d01" % t.idx, "1")])
    t.via("+5V", 8.4, 3.6)
    t.wire("+5V", [(r3, "2"), (8.4, 3.6)], width=W)
    t.gnd_stub(r4, "1", (8.0, 10.2), sym=(0, 0), width=W)
    t.wire("GND", [(r5, "1"), (r4, "1")], width=W, silk=False)
    t.via("+5V", 14.2, 5.4)
    t.route("+5V", [(ud, "5"), (14.2, 5.4)], width=W)
    cvn = t.add("C", "C0402 100nF", "100n", 10.2, 2.4, 0, {"1": "GND", "2": "-5V"}, label=None)
    t.via("-5V", 10.68, -1.0)
    t.route("-5V", [(ud, "2"), (cvn, "2")], width=W)
    t.wire("-5V", [(cvn, "2"), (10.68, -1.0)], width=W, silk=False)
    t.gnd_stub(cvn, "1", (9.0, 2.4), sym=(0, 0), width=W)
    t.titles.append("Phase current")
    t.result = "IPA = phase A's whole current, 1 V/A both ways, through every PWM state (compare b3's IA: the low side only)"
    t.notes = ["Phase A through 0.05 ohm between the driver and the motor; an INA240A1 (PWM rejection, common mode to 80 V) about 2.5 V",
               "and an OPA810 that takes the 2.5 V away: IPA = 1 V/A, the whole current.  b3's IA sees only the low side's share."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ b6 --
def tile_b6():
    """The IMU and the SPI lines' junction, one cell left of the gimbal's lower half: an LSM6DSO (gyro to 2000 dps,
    accelerometer to 16 g, both to 6.66 kHz) on SPI (mode 3, 10 MHz) and the 74LVC1G125 that puts the encoder's DO on
    MISO only while CS ENC is low (the MT6701's DO never lets go), so the two share the Pmod's MISO.  The five lines come
    up the gutter on the back from the plug under b3 (BACK_WIRES); SCK, CS ENC and DO go on to the encoder on b5; the
    +3.3 V from the strip in the gutter over the tile.  Stand the board on edge with the motor's axis horizontal and the
    accelerometer sees the roll about it: a one-axis gimbal's level reference.  No jacks: its data comes over the Pmod."""
    t = Tile("b6", "IMU", [(0, 2)], supply="+3.3 V", subtitle="LSM6DSO", sections=["Motors"])
    t.fine = True
    F = 0.15
    imu = t.add("U", "LSM6DSO", "LSM6DSO", 10.5, 15.0, 270, {"1": "/PMOD3", "2": "GND", "3": "GND", "5": "+3V3", "6": "GND", "7": "GND", "8": "+3V3",
                                                             "12": "/PMOD8", "13": "/PMOD4", "14": "/PMOD7"}, hide_value=False, label=None)
    # SPI: the right side's three to vias staggered so the lanes on the back pass between them; MISO's from the top
    for net, pad, mid, via in (("/PMOD7", "14", [], (12.45, 14.5)), ("/PMOD8", "12", [], B6_VIA["/PMOD8"]), ("/PMOD4", "13", [], B6_VIA["/PMOD4"]),
                               ("/PMOD3", "1", [(11.25, 13.5)], (12.45, 13.5))):
        t.via(net, via[0], via[1], fine=True)
        t.wire(net, [(imu, pad)] + mid + [via], width=F)
    t.wire("/PMOD3", [(12.45, 13.5), B6_VIA["/PMOD3"]], width=F, layer="B.Cu", silk=False, fine=True)
    # SCK on up over the MISO and MOSI lanes to the encoder's line
    t.via("/PMOD4", *B6_VIA["SCK_ENC"], fine=True)
    t.wire("/PMOD4", [B6_VIA["/PMOD4"], B6_VIA["SCK_ENC"]], width=F)
    # the buffer: A from the encoder's DO, /OE from CS ENC, Y onto MISO
    buf = t.add("U", "LVC1G125", "74LVC1G125", 16.5, 9.4, 180, {"1": "/PMOD6", "2": "/ENC_DO", "3": "GND", "4": "/PMOD3", "5": "+3V3"},
                hide_value=True, label=None)
    t.via("/ENC_DO", *B6_VIA["/ENC_DO"], fine=True)
    t.wire("/ENC_DO", [(buf, "2"), B6_VIA["/ENC_DO"]], width=F)
    t.via("/PMOD6", *B6_VIA["/PMOD6"], fine=True)
    t.wire("/PMOD6", [(buf, "1"), (18.2, 10.35), (18.6, 10.75), B6_VIA["/PMOD6"]], width=F)
    t.via("/PMOD3", *B6_VIA["/PMOD3"], fine=True)
    t.wire("/PMOD3", [(buf, "4"), (14.4, 8.45), B6_VIA["/PMOD3"]], width=F)
    t.gnd_stub(buf, "3", (18.75, 7.75), sym=(0, 0), width=0.2, fine=True)
    cb = t.add("C", "C0402 100nF", "100n", 16.6, 11.9, 0, {"1": "+3V3", "2": "GND"}, label=None)
    t.via("+3V3", 15.363, 11.5, fine=True)
    t.wire("+3V3", [(buf, "5"), (15.363, 11.5), (15.76, 11.9), (cb, "1")], width=0.2)
    t.gnd_stub(cb, "2", (17.08, 12.95), sym=(0, 0), width=0.2, fine=True)
    # +3.3 V: from the strip over the tile down the back to the IMU's capacitors, on to the buffer's
    t.via("+3V3", 8.0, -0.6)
    t.wire("+3V3", [(8.0, -0.6), (8.0, 11.5)], width=0.25, layer="B.Cu", silk=False, fine=True)
    t.wire("+3V3", [(8.0, 11.5), (15.363, 11.5)], width=0.2, layer="B.Cu", silk=False, fine=True)
    t.wire("+3V3", [(8.0, 11.5), (8.0, 17.52)], width=0.2, layer="B.Cu", silk=False, fine=True)
    cio = t.add("C", "C0402 100nF", "100n", 8.0, 13.2, 90, {"1": "GND", "2": "+3V3"}, label=None)        # pad 2 up
    cdd = t.add("C", "C0402 100nF", "100n", 9.75, 18.0, 90, {"1": "GND", "2": "+3V3"}, label=None)
    t.wire("+3V3", [(8.0, 11.5), (cio, "2")], width=0.2)
    t.wire("+3V3", [(imu, "5"), (8.7, 14.5), (8.7, 12.72), (cio, "2")], width=0.2)
    t.wire("+3V3", [(8.0, 17.52), (cdd, "2"), (imu, "8")], width=0.2)
    t.gnd_stub(cio, "1", (6.9, 13.68), sym=(0, 0), width=0.2)
    t.gnd_stub(cdd, "1", (9.75, 19.4), sym=(0, 0), width=0.2)
    # ground: the top's two pads to a via over them, the left's two to a via beside them
    t.wire("GND", [(imu, "3"), (10.25, 13.4), (10.75, 13.4), (imu, "2")], width=F, silk=False)
    t.gnd_stub(imu, "2", (10.5, 12.85), sym=(0, 0), width=F, fine=True)
    t.gnd_stub(imu, "6", [(9.15, 15.0), (8.7, 15.25)], sym=(0, 0), width=F, fine=True)
    t.gnd_stub(imu, "7", [(9.15, 15.5), (8.7, 15.25)], sym=(0, 0), width=F, fine=True)
    t.titles.append("IMU")
    t.result = "six axes on SPI (the tutorial's gateware reads them): with the board on edge, the roll about the motor's axis"
    t.notes = ["LSM6DSO on SPI (mode 3): CS IMU on IO8, SCK IO4, MOSI IO7, MISO IO3, shared with the encoder through a 74LVC1G125",
               "(CS ENC on IO6).  Gyro to 2000 dps, accelerometer to 16 g, to 6.66 kHz.  On edge: a one-axis gimbal's level reference."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


def amp_stage(t, x, y, inp, neg5, rin, rgnd, rtop, rbot, rf, ref_net, ro_at, ro_rot, tag, route_ro=True):
    """An OPA810 difference stage on +-5 V at (x, y) turned 0: OUT = (rf / rtop||rbot ...) -- the tile's own values: inp
    through rin to +IN with rgnd down, -IN from ref_net through rtop with rbot down, rf back.  Returns (ud, ro)."""
    ud = t.add("U", "OPA810", "OPA810", x, y, 0, {"1": tag + "O", "2": "-5V", "3": tag + "P", "4": tag + "N", "5": "+5V"}, hide_value=False, label=None)
    p = lambda key, val, xx, yy, rot, pins: t.add("R", key, val, xx, yy, rot, pins, label=None)
    a = p(*rin, x - 4.0, y + 1.4, 90, {"1": tag + "P", "2": inp})
    b = p(*rgnd, x - 2.8, y + 1.4, 90, {"1": "GND", "2": tag + "P"})
    c = p(*rtop, x + 3.4, y - 1.6, 90, {"1": tag + "N", "2": ref_net})
    d = p(*rbot, x + 3.4, y + 1.6, 90, {"1": "GND", "2": tag + "N"})
    f = p(*rf, x, y - 2.8, 0, {"1": tag + "O", "2": tag + "N"})
    ro = p("R0402 49.9R", "49.9", ro_at[0], ro_at[1], ro_rot, {"1": tag + "O", "2": tag + "J"})
    for (net, aa, bb) in ((tag + "P", (a, "1"), (ud, "3")), (tag + "P", (b, "2"), (ud, "3")), (tag + "N", (c, "1"), (ud, "4")),
                          (tag + "N", (d, "2"), (ud, "4")), (tag + "N", (f, "2"), (ud, "4")), (tag + "O", (f, "1"), (ud, "1"))) + \
            (((tag + "O", (ro, "1"), (ud, "1")),) if route_ro else ()):
        t.route(net, [aa, bb], width=0.2)
    t.gnd_stub(b, "1", (x - 2.8, y + 3.0), sym=(0, 0), width=W)
    t.gnd_stub(d, "1", (x + 3.4, y + 3.2), sym=(0, 0), width=W)
    t.via("+5V", x + 1.9, y - 1.4)
    t.route("+5V", [(ud, "5"), (x + 1.9, y - 1.4)], width=0.2)
    if ref_net == "+5V":
        t.wire("+5V", [(c, "2"), (x + 2.6, y - 2.08), (x + 1.9, y - 1.4)], width=0.2)
    t.via("-5V", neg5[0], neg5[1])
    t.route("-5V", [(ud, "2"), neg5], width=0.2)
    return ud, a, c, ro


# ------------------------------------------------------------------------------------------------------------ b7 --
def tile_b7():
    """The encoder's analog angle, one cell at the top left: the MT6701's OUT (0 to its 3.3 V over a turn, a sawtooth)
    from b5 into an OPA810: ANG = 0.51 x (OUT - 1.65 V), +-0.84 V over the turn, through 49.9 ohm (the 1.65 V from 20 k /
    20 k of the same 3.3 V, so it tracks: the MT6701's own, which comes with the angle up the gutter on the back).  The
    angle without the SSI: a scope's or an ADC's view of the shaft."""
    t = Tile("b7", "angle", [(0, 0)], supply="+-5 V", subtitle="MT6701", sections=["Motors"])
    t.jack("BR", "ANG", "AJ", "out", "")
    ud, a, c, ro = amp_stage(t, 10.0, 8.0, "/ANG", (4.0, 20.5), ("R0402 10k", "10k"), ("R0402 5.1k", "5.1k"), ("R0402 20k", "20k"),
                             ("R0402 20k", "20k"), ("R0402 5.1k", "5.1k"), "+3V3", (15.25, 10.6), 270, "A", route_ro=False)
    t.wire("AO", [(9.52, 5.2), (9.52, 3.4), (16.4, 3.4), (16.4, 9.6), (ro, "1")], width=W)            # from the feedback resistor
    t.wire("AJ", [(ro, "2"), ("J%d01" % t.idx, "1")])
    # the angle and the 3.3 V from b5 arrive on the back (BACK_WIRES) at vias by the input and by the reference's divider
    t.via("/ANG", *B7_VIA["/ANG"])
    t.wire("/ANG", [B7_VIA["/ANG"], (a, "2")], width=W)
    t.via("+3V3", *B7_VIA["+3V3"])
    t.wire("+3V3", [B7_VIA["+3V3"], (13.4, 5.5), (c, "2")], width=W)
    t.titles.append("Angle")
    t.result = "ANG = a sawtooth, -0.84 V to +0.84 V, once a turn of the shaft (0 at half a turn from the MT6701's zero)"
    t.notes = ["The MT6701's analog output (0-3.3 V a turn) less 1.65 V, times 0.51, by an OPA810: the shaft's angle without SSI.",
               "Its zero is the MT6701's (set by its registers over the SSI, or where the magnet sits)."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ b8 --
def tile_b8():
    """A vibration pickup, one cell at the top: a piezo disc on a 2-way screw terminal (wires in from the top margin)
    into an OPA810 charge amplifier (1 nF with 1 M across: OUT = -Q / 1 nF above 160 Hz), through 49.9 ohm.  Stick the
    disc to the motor's mount: the cogging and the commutation's ripple, the bearing's noise, the frame's resonances."""
    t = Tile("b8", "vibration", [(1, 0)], supply="+-5 V", subtitle="OPA810", sections=["Motors"])
    t.jack("BR", "VIB", "VJ", "out", "")
    tp = t.add("J", "TERM2", "piezo", 6.4, 5.6, 0, {"1": "PZ", "2": "GND"}, hide_value=True)
    ud = t.add("U", "OPA810", "OPA810", 6.4, 14.6, 0, {"1": "VO", "2": "-5V", "3": "GND", "4": "VN", "5": "+5V"}, hide_value=False, label=None)
    rs = t.add("R", "R0402 1k", "1k", 2.4, 12.4, 90, {"1": "VN", "2": "PZ"}, label=None)                  # pad 2 up
    cf = t.add("C", "C0402 1nF", "1n", 6.4, 11.4, 0, {"1": "VN", "2": "VO"}, label=None)
    rf = t.add("R", "R0805 1M", "1M", 6.4, 18.0, 0, {"1": "VN", "2": "VO"}, label=None)
    ro = t.add("R", "R0402 49.9R", "49.9", 15.25, 10.6, 90, {"1": "VJ", "2": "VO"}, label=None)
    t.route("PZ", [(tp, "1"), (rs, "2")], width=W)
    t.gnd_stub(tp, "2", (8.9, 9.8), sym=(0, 0), width=W)
    for (net, a, b) in (("VN", (rs, "1"), (ud, "4")), ("VN", (cf, "1"), (ud, "4")), ("VN", (rf, "1"), (ud, "4")), ("VO", (cf, "2"), (ud, "1")),
                        ("VO", (rf, "2"), (ud, "1")), ("VO", (ro, "2"), (ud, "1"))):
        t.route(net, [a, b], width=0.2)
    t.wire("VJ", [(ro, "1"), ("J%d01" % t.idx, "1")])
    t.gnd_stub(ud, "3", (4.0, 16.4), sym=(0, 0), width=W)
    t.via("+5V", 9.0, 13.2)
    t.route("+5V", [(ud, "5"), (9.0, 13.2)], width=0.2)
    t.via("-5V", 1.2, t.h + 0.5)
    t.route("-5V", [(ud, "2"), (1.2, t.h + 0.5)], width=0.2)
    t.titles.append("Vibration")
    t.result = "VIB = -the piezo's charge / 1 nF above 160 Hz: the motor's cogging, its commutation ripple, the bearing"
    t.notes = ["A piezo disc on the terminal into an OPA810 charge amplifier (1 nF, 1 M: from 160 Hz).  Stick the disc to the motor's",
               "mount: the cogging at 12 a turn, the commutation's ripple, the bearing, the frame's resonances."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ------------------------------------------------------------------------------------------------------------ b9 --
def tile_b9():
    """The index, one cell at the top over the gimbal: the QRE1113 under the bell's rim (on b5) held at 0 V on its
    collector by an OPA810 (its emitter on -5 V through 100 ohm): IDX = 4.7 k x the collector current, 100 pF across,
    through 49.9 ohm.  A white mark on the bell's rim gives a pulse once a turn: an index for the encoder, a tachometer."""
    t = Tile("b9", "index", [(2, 0)], supply="+-5 V", subtitle="QRE1113", sections=["Motors"])
    t.jack("BR", "IDX", "XJ", "out", "")
    ud = t.add("U", "OPA810", "OPA810", 10.6, 9.0, 0, {"1": "XO", "2": "-5V", "3": "GND", "4": "/IDX_C", "5": "+5V"}, hide_value=False, label=None)
    rf = t.add("R", "R0402 4.7k", "4.7k", 10.6, 12.0, 0, {"1": "/IDX_C", "2": "XO"}, label=None)
    cf = t.add("C", "C0402 100pF", "100p", 10.6, 13.2, 0, {"1": "/IDX_C", "2": "XO"}, label=None)
    re = t.add("R", "R0402 100R", "100", 6.0, 16.4, 0, {"1": "/IDX_E", "2": "-5V"}, label=None)
    ro = t.add("R", "R0402 49.9R", "49.9", 15.25, 10.6, 90, {"1": "XJ", "2": "XO"}, label=None)
    for (net, a, b) in (("/IDX_C", (rf, "1"), (ud, "4")), ("/IDX_C", (cf, "1"), (rf, "1")), ("XO", (rf, "2"), (ud, "1")), ("XO", (cf, "2"), (rf, "2")),
                        ("XO", (ro, "2"), (ud, "1"))):
        t.route(net, [a, b], width=0.2)
    t.wire("XJ", [(ro, "1"), ("J%d01" % t.idx, "1")])
    t.gnd_stub(ud, "3", (8.4, 10.2), sym=(0, 0), width=W)
    t.via("+5V", 12.6, 7.0)
    t.route("+5V", [(ud, "5"), (12.6, 7.0)], width=0.2)
    t.via("-5V", 8.0, t.h + 0.5)
    t.route("-5V", [(ud, "2"), (8.0, t.h + 0.5)], width=0.2)
    t.route("-5V", [(re, "2"), (8.0, t.h + 0.5)], width=0.2)
    t.via("/IDX_E", *B9_VIA["/IDX_E"])
    t.wire("/IDX_E", [B9_VIA["/IDX_E"], (re, "1")], width=W)
    t.via("/IDX_C", *B9_VIA["/IDX_C"])
    t.wire("/IDX_C", [B9_VIA["/IDX_C"], (10.12, 13.82), (cf, "1")], width=W)
    t.titles.append("Index")
    t.result = "IDX = 4.7 k x the sensor's current: a pulse once a turn as a white mark on the bell's rim passes"
    t.notes = ["The QRE1113 under the gimbal's rim (on b5), its collector held at 0 V by an OPA810: IDX = 4.7 k x Ic.  Put a white mark",
               "(tape, paint) on the bell's lower rim: an index pulse a turn, a tachometer with no encoder."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


# ----------------------------------------------------------------------------------------------------------- b10 --
def tile_b10():
    """The halls, one cell left of the gimbal: the two DRV5055A3 under the rotor's magnets (on b5, 120 electrical
    degrees apart) each less half its 5 V (20 k / 20 k) times 0.39 (10 k / 3.9 k), as AMOD-M's m9: HA, HB = 9.75 mV/mT
    through 49.9 ohm.  Two sinusoids in quadrature-ish: an analog encoder of the rotor's electrical angle, the
    commutation a hall-sensored motor uses, and the rotor's field to compare with the back-EMF."""
    t = Tile("b10", "halls", [(0, 1)], supply="+-5 V", subtitle="DRV5055A3", sections=["Motors"])
    t.jack("TL", "HA", "HAJ", "out", "")
    t.jack("BR", "HB", "HBJ", "out", "")
    uA, aA, cA, roA = amp_stage(t, 14.4, 5.2, "/HALLA", (13.0, -0.75), ("R0402 10k", "10k"), ("R0402 3.9k", "3.9k"), ("R0402 20k", "20k"),
                                ("R0402 20k", "20k"), ("R0402 3.9k", "3.9k"), "+5V", (9.6, 2.0), 0, "HA")
    uB, aB, cB, roB = amp_stage(t, 5.7, 14.6, "/HALLB", (-2.4, 14.6), ("R0402 10k", "10k"), ("R0402 3.9k", "3.9k"), ("R0402 20k", "20k"),
                                ("R0402 20k", "20k"), ("R0402 3.9k", "3.9k"), "+5V", (10.7, 15.25), 0, "HB")
    t.wire("HAJ", [(roA, "2"), (10.6, 2.0), (10.6, 3.4), (8.6, 4.75), ("J%d01" % t.idx, "1")])
    t.wire("HBJ", [(roB, "2"), ("J%d02" % t.idx, "1")])
    for net, ra in (("/HALLA", aA), ("/HALLB", aB)):
        t.via(net, *B10_VIA[net])
        t.wire(net, [B10_VIA[net], (ra, "2")], width=W, silk=False)
    t.titles.append("Halls")
    t.result = "HA, HB = 9.75 mV/mT from the two halls under the rotor: two sinusoids 120 electrical degrees apart as it turns"
    t.notes = ["Two DRV5055A3 under the gimbal's magnets (b5), 17.1 degrees apart (120 electrical for 7 pole pairs); each less half its",
               "5 V, times 0.39 (as AMOD-M's m9).  The rotor's electrical angle without the encoder; hall-sensored commutation."]
    t.sch_draw = lambda ctx, tt: ctx.netlist_block(tt)
    return t


def tiles():
    return [tile_b7(), tile_b8(), tile_b9(), tile_b2(), tile_b10(), tile_b5(), tile_b1(), tile_b6(), tile_b12(), tile_b4(), tile_b3(), tile_b11()]


GND_LOOPS = [(80.0, 95.8), (88.0, 95.8)]
FIDUCIALS = [(3.5, 50.0), (96.5, 50.0), (60.0, 96.8)]
HOLES = []
FEET = [(5.0, 5.0), (95.0, 5.0), (95.0, 95.0), (5.0, 85.0)]
SLOTS = []
RAIL_POURS = [("+5V", 0.6, 0.6, 99.4, 99.4, 0),
              ("-5V", [(1.0, 27.75), (93.6, 27.75), (93.6, 29.25), (6.5, 29.25), (6.5, 70.75), (93.0, 70.75), (93.0, 72.25), (6.5, 72.25),
                       (6.5, 92.6), (62.0, 92.6), (62.0, 93.6), (6.5, 93.6), (6.5, 94.5), (1.0, 94.5)], 1),
              ("+3V3", [(7.0, 49.25), (37.0, 49.25), (37.0, 46.3), (63.0, 46.3), (63.0, 49.25), (93.0, 49.25), (93.0, 50.75), (7.0, 50.75)], 1)]

def _at(c, r):
    x0, y0 = G.cell_origin(c, r)
    return lambda x, y: (round(x0 + x, 3), round(y0 + y, 3))


_B3, _B5, _B6, _B7, _B9, _B10 = _at(1, 3), _at(1, 1), _at(0, 2), _at(0, 0), _at(2, 0), _at(0, 1)


def _pad(n):
    """The Pmod plug's pad n (JLCPCB's numbering) in board mm: b3's margin, the upper row even."""
    return _B3((-3.38, -0.84, 1.70, 4.24, 6.78, 9.32)[(n - 1) // 2], 22.98 if n % 2 == 0 else 25.52)


def _diag(via, y, sense=1):
    """The point at height y (board mm) on the 45-degree line through a b5 via (board mm): down-left (sense 1, x + y kept)
    or up-left (sense -1, x - y kept)."""
    return (round(via[0] + via[1] - y, 3), y) if sense == 1 else (round(via[0] - via[1] + y, 3), y)


def _back_wires():
    """The board's lines on the back: the plug's five SPI lines up the gutter between columns 0 and 1 to b6 (each lane to
    the right of the last, each turning in above the last, so none crosses: the plug's pin order is chosen for it), CS ENC
    on to the encoder; SCK and DO between b6 and the encoder; the angle and the encoder's 3.3 V up between the slots to
    b7; the halls to b10 (the upper one up the tile, the lower one along the gutter under it); the index to b9."""
    gx = {"/PMOD8": 27.40, "/PMOD4": 27.85, "/PMOD7": 28.30, "/PMOD3": 28.75, "/PMOD6": 29.20}       # the lanes in the gutter
    hy = {"/PMOD8": 93.30, "/PMOD4": 92.95, "/PMOD7": 92.60, "/PMOD3": 92.25, "/PMOD6": 91.90}       # their runs over the plug
    # (CS IMU's 1 mm over the upper row, so the back's ground reaches the plug's pad 4 past it; 0.35 mm apart, the fine
    # nets' pitch, so CS ENC's stays clear of the tile switch's +5 V via)
    wires = []
    for net, n in (("/PMOD8", 5), ("/PMOD4", 6), ("/PMOD7", 7), ("/PMOD3", 8), ("/PMOD6", 9)):
        p = _pad(n)
        out = [p] if n % 2 == 0 else [p, (round(p[0] - 1.27, 3), round(p[1] - 1.27, 3))]          # the lower row out between the upper's pads
        end = _B6(*B6_VIA[net])
        wires.append((net, out + [(out[-1][0], hy[net]), (gx[net], hy[net]), (gx[net], end[1]), end]))
    enc = {n: _B5(*v) for n, v in ENC_VIA.items()}
    ty = _B6(0, 11.6)[1]                                                                           # CS ENC's turn to b5
    wires.append(("/PMOD6", [(gx["/PMOD6"], _B6(*B6_VIA["/PMOD6"])[1]), (gx["/PMOD6"], ty), _diag(enc["/PMOD6"], ty), enc["/PMOD6"]]))
    for net, frm in (("/PMOD4", "SCK_ENC"), ("/ENC_DO", "/ENC_DO")):
        a = _B6(*B6_VIA[frm])
        wires.append((net, [a, _diag(enc[net], a[1]), enc[net]]))
    # the angle and the 3.3 V: up-left from the encoder's vias, left over b5's top-left corner, up the gutter, into b7
    a7, p7 = _B7(*B7_VIA["/ANG"]), _B7(*B7_VIA["+3V3"])
    ya, yp = _B5(0, 1.77)[1], _B5(0, 1.3)[1]
    wires.append(("/ANG", [enc["/ANG"], _diag(enc["/ANG"], ya, -1), (28.2, ya), (28.2, _B7(0, 10.0)[1]), (a7[0], _B7(0, 10.0)[1]), a7]))
    v3 = (enc["+3V3"][0], round(enc["+3V3"][1] - 0.85, 3))
    wires.append(("+3V3", [enc["+3V3"], v3, _diag(v3, yp, -1), (28.8, yp), (28.8, p7[1]), p7]))
    # the halls: A (the upper) straight left and up b10 to its upper stage; B left, up the gutter to the one under b10, along it
    cx = cy = 20.75
    hall = {}
    for k, sgn in enumerate((-1, 1)):
        a = math.radians(180 + sgn * 120.0 / 7 / 2)
        hx, hy_ = cx + GIMBAL_R_HALL * math.cos(a), cy + GIMBAL_R_HALL * math.sin(a)
        hall["/HALL%s" % "BA"[k]] = _B5(hx - 2.4, hy_ + 0.95)
    ha, hb = _B10(*B10_VIA["/HALLA"]), _B10(*B10_VIA["/HALLB"])
    wires.append(("/HALLA", [hall["/HALLA"], (_B10(10.5, 0)[0], hall["/HALLA"][1]), _B10(10.5, 8.4), _B10(ha[0] - 7.75, 7.3), ha]))
    wires.append(("/HALLB", [hall["/HALLB"], (28.4, hall["/HALLB"][1]), (28.4, 49.5), (hb[0], 49.5), hb]))
    # the index: straight up into b9, the emitter's line left under its resistor
    q = math.radians(-60.0)
    qx, qy = cx + GIMBAL_R_INDEX * math.cos(q), cy + GIMBAL_R_INDEX * math.sin(q)
    e5, c5 = _B5(qx + 2.4, qy - 2.0), _B5(qx + 3.2, qy + 2.0)
    e9, c9 = _B9(*B9_VIA["/IDX_E"]), _B9(*B9_VIA["/IDX_C"])
    wires.append(("/IDX_E", [e5, (e5[0], _B9(0, 17.6)[1]), (e9[0], _B9(0, 17.6)[1]), e9]))
    wires.append(("/IDX_C", [c5, c9]))                                                         # b9's via is straight over b5's
    return wires


BACK_WIRES = _back_wires()
BACK_TEXT_X = 60.0                      # in the bottom margin between the plug and the ground loops
QR_AT = (61.5, 61.5)                    # under the gimbal's bottom-right quarter: SMD only, clear of its slots
BACK_TEXT = ["AMOD-B: brushless.  Motor supply",
             "5-12 V on b2; USB-C 5 V on b1."]
FRONT_TEXT = []


PMOD_HOST = "the bottom margin under b3's left cell"
HANDBOOK_INTRO = [
    "Twelve tiles on sixteen 20 mm cells (the gimbal takes four), four layers.  b1 takes 5 V from its USB-C and makes -5 V",
    "(40 mA) and 3.3 V, as AMOD-A's a1 does; b2 takes the motor supply, 5-12 V on a 5.5 / 2.1 mm barrel jack (centre",
    "positive), and joins the USB's 5 V to it through Schottky diodes, so the gimbal motor turns, weakly, with no supply.",
    "That rail, VMOT, runs down the back to b12's shunt and on from it (as VMB) to the driver; it is not switched.  The",
    "driver's three phases and the two SPI sensors take their commands from the FPGA on the Pmod plug in the bottom margin",
    "under b3; COAST comes from a DAC and everything else answers to an ADC over SMA, as on the other boards.  A powered",
    "tile has a slide switch along its left edge (slider up: on).  A port's name is in capitals on its tile's frame, a",
    "terminated input says so (COAST 50R) and an output read through a divider says its ratio (EA /14).  The back of each",
    "tile says what to know while cabling it."]
HANDBOOK_SECTIONS = [
    ["## The tiles together", "",
     "1. **The motor.**  b5 holds a GBM2804H-100T class gimbal motor (12 slots, 14 poles, 10 ohm) on four slots over its",
     "   sensors: an MT6701 magnetic encoder under the shaft (a magnet glued to its end), two linear halls under the",
     "   rotor's magnets, a reflective sensor under the bell's rim.  Its three leads go to b3's terminal.",
     "2. **The drive.**  b3's DRV8311H sets each phase high or low from INHA, INHB, INHC (Pmod IO5, IO1, IO2) at the",
     "   gateware's PWM: six-step commutation from the halls or the encoder, or sinusoidal and field-oriented control from",
     "   the encoder's angle.  COAST from a DAC floats all three phases.  IA and IB are two phases' low-side currents (the",
     "   driver's own amplifiers); b11 reads phase A's whole current in line, b12 the current from the supply.",
     "3. **The feedback.**  The encoder's angle over SPI (14 bits; b6's buffer shares MISO with the IMU) and as a",
     "   sawtooth on b7; the halls' sinusoids on b10; the back-EMF on b4 (coast and spin the motor); an index on b9; the",
     "   IMU on b6; the motor's vibration on b8.",
     "",
     "A one-axis gimbal: stand the board on edge with the motor's shaft horizontal and a load on the bell; the IMU's",
     "accelerometer gives the board's roll, the encoder the motor's angle, and the gateware turns the motor against the",
     "roll.  Every motor tile's supply is VMOT: a bench supply's current limit, or the USB's, is the board's only fuse."]]
PMOD_NAMES = {"/PMOD1": "b3's INHB (phase B high or low)", "/PMOD2": "b3's INHC (phase C)",
              "/PMOD3": "MISO (b6's IMU and, through b6's buffer, b5's encoder)", "/PMOD4": "SCK (the IMU and the encoder)",
              "/PMOD5": "b3's INHA (phase A)", "/PMOD6": "CS ENC (the encoder's select, low to read it)",
              "/PMOD7": "MOSI (the IMU)", "/PMOD8": "CS IMU (the IMU's select, low to talk to it)"}

# The back panels (gen_pcb.back_panels): under each tile, what a user must know while cabling it.
BACK = {
    "b1": ["USB-C 5 V only", "+5 V 1.5 A", "-5 V 40 mA", "+3.3 V 300 mA"],
    "b2": ["5-12 V, centre +", "or USB 5 V alone", "VMOT = in - 0.4 V", "not switched"],
    "b3": ["INHA IO5, INHB IO1", "INHC IO2", "COAST high: all float", "IA, IB 0.75 V/A", "terminal: C B A"],
    "b4": ["phase / 14 vs neutral", "COAST high, spin it"],
    "b5": ["magnet 6 x 2.5 mm,", "diametric, 1 mm over", "the MT6701", "M2-M3 in the slots"],
    "b6": ["SPI mode 3", "CS IMU IO8, SCK IO4", "MOSI IO7, MISO IO3", "CS ENC IO6"],
    "b7": ["ANG +-0.84 V", "a sawtooth a turn"],
    "b8": ["piezo on the terminal", "VIB = -Q / 1 nF"],
    "b9": ["white mark on the rim", "IDX = 4.7 k x Ic"],
    "b10": ["9.75 mV/mT", "A, B 120 deg apart", "(electrical)"],
    "b11": ["IPA 1 V/A", "both ways, all PWM"],
    "b12": ["I 1 V/A both ways", "VMB on to b3"],
}
BACK_PLOTS = {}
