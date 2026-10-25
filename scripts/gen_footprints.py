#!/usr/bin/env python3
"""Generate the project's own footprints: the parts whose land pattern is JLCPCB's drawing of the
exact LCSC code (so the part fits by construction and the CPL rotation is predicted exactly), and
the few KiCad has no footprint for.  Every dimension is taken from the land pattern JLCPCB places
the part with (scripts/easyeda.py <code>, read 2026-10-25) or from the drawing named.  Helpers
from the op-amp board's gen_footprints.py.

    python3 scripts/gen_footprints.py        writes hardware/lib/amod.pretty/*.kicad_mod
"""
import os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import S, q, n, uid, effects, stroke, at

FP_VERSION = "20260206"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "hardware", "lib", "amod.pretty")
VENDORED = os.path.join(HERE, "vendored")
LIB = "amod"
SILK_W, FAB_W, CRT_W = 0.15, 0.10, 0.05
MM_SCALE = 1.0 / 2.54       # VRML unit is 2.54 mm; our models are drawn in mm


def model(f, name, scale=MM_SCALE, rot=(0, 0, 0), offset=(0, 0, 0)):
    m = S("model", q("${KIPRJMOD}/lib/%s.3dshapes/%s" % (LIB, name)))
    m.add(S("offset").add(S("xyz", n(offset[0]), n(offset[1]), n(offset[2]))),
          S("scale").add(S("xyz", n(scale), n(scale), n(scale))),
          S("rotate").add(S("xyz", n(rot[0]), n(rot[1]), n(rot[2]))))
    f.add(m)


def fp_header(name, descr, tags, attr, ref_y):
    f = S("footprint", q(name))
    f.add(S("version", FP_VERSION), S("generator", q("amod-gen")), S("generator_version", q("10.0")),
          S("layer", q("F.Cu")), S("descr", q(descr)), S("tags", q(tags)), S("attr", *attr.split()))
    for pname, val, layer, hide in (("Reference", "REF**", "F.SilkS", False), ("Value", name, "F.Fab", False),
                                    ("Datasheet", "", "F.Fab", True), ("Description", descr, "F.Fab", True)):
        y = ref_y if pname == "Reference" else -ref_y
        p = S("property", q(pname), q(val))
        p.add(at(0, y), S("unlocked", "yes"), S("layer", q(layer)))
        if hide:
            p.add(S("hide", "yes"))
        p.add(S("uuid", q(uid(f"{name}/prop/{pname}"))), effects(size=1.0, thickness=0.15))
        f.add(p)
    return f


def line(x1, y1, x2, y2, layer, width, key):
    return S("fp_line").add(S("start", n(x1), n(y1)), S("end", n(x2), n(y2)), stroke(width), S("layer", q(layer)),
                            S("uuid", q(uid(key))))


def rect_lines(f, x1, y1, x2, y2, layer, width, key):
    f.add(line(x1, y1, x2, y1, layer, width, key + "/t"), line(x2, y1, x2, y2, layer, width, key + "/r"),
          line(x2, y2, x1, y2, layer, width, key + "/b"), line(x1, y2, x1, y1, layer, width, key + "/l"))


def circle(cx, cy, r, layer, width, key, fill=False):
    return S("fp_circle").add(S("center", n(cx), n(cy)), S("end", n(cx + r), n(cy)), stroke(width),
                              S("fill", "yes" if fill else "no"), S("layer", q(layer)), S("uuid", q(uid(key))))


def tht_pad(num, x, y, drill, dia, key, shape="circle", end_layers_only=False):
    p = S("pad", q(num), "thru_hole", shape)
    p.add(at(x, y), S("size", n(dia), n(dia)), S("drill", n(drill)), S("layers", q("*.Cu"), q("*.Mask")))
    if end_layers_only:
        p.add(S("remove_unused_layers", "yes"), S("keep_end_layers", "yes"))
    else:
        p.add(S("remove_unused_layers", "no"))
    p.add(S("uuid", q(uid(key))))
    return p


def npth(x, y, w, h, key):
    p = S("pad", q(""), "np_thru_hole", "oval" if w != h else "circle")
    p.add(at(x, y), S("size", n(w), n(h)), S("drill", "oval", n(w), n(h)) if w != h else S("drill", n(w)),
          S("layers", q("*.Cu"), q("*.Mask")), S("uuid", q(uid(key))))
    return p


def smd_pad(num, x, y, w, h, key, shape="roundrect", rot=0, paste=True):
    p = S("pad", q(num), "smd", shape)
    layers = [q("F.Cu"), q("F.Mask")] + ([q("F.Paste")] if paste else [])
    p.add(at(x, y, rot) if rot else at(x, y), S("size", n(w), n(h)), S("layers", *layers))
    if shape == "roundrect":
        p.add(S("roundrect_rratio", "0.25"))
    p.add(S("uuid", q(uid(key))))
    return p


def text_fab(f, txt, x, y, key, size=0.8):
    f.add(S("fp_text", "user", q(txt)).add(at(x, y, 0), S("layer", q("F.Fab")), S("uuid", q(uid(key))),
                                           effects(size=size, thickness=0.12)))


# ------------------------------------------------------------- SMA, vertical --
def sma_vertical():
    """Bat Wireless BWSMA-KE-Z001 (LCSC C496549): a straight SMA jack standing on the board, 6.5 mm
    square, 13.5 mm tall, 0-6 GHz.  JLCPCB's land pattern (easyeda C496549, 2026-10-25): four legs
    2.20 mm pads on 1.50 drills at (+-2.55, +-2.55), the centre pin 2.00 on 1.35 at the origin; its
    silkscreen is the 6.5 mm square.  Pads renumbered for KiCad's Conn_Coaxial: 1 = centre, 2 = shield
    (JLCPCB numbers the legs 1-4 and the centre 5; the symbol has pin 1 = centre).  The centre pad is
    kept on the end layers only (CLAUDE_PCB.md section 14: no rings on inner layers at a launch)."""
    name = "SMA_BWSMA-KE-Z001_Vertical"
    f = fp_header(name, "SMA jack, straight, through-hole, 6.5 mm square: Bat Wireless BWSMA-KE-Z001 (LCSC C496549), 0-6 GHz, 500 cycles",
                  "SMA coaxial vertical straight 50ohm", "through_hole", 4.6)
    f.add(tht_pad("1", 0, 0, 1.35, 2.0, f"{name}/p1", end_layers_only=True))
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        f.add(tht_pad("2", sx * 2.55, sy * 2.55, 1.5, 2.2, f"{name}/p2/{i}"))
    h = 3.25
    rect_lines(f, -h, -h, h, h, "F.Fab", FAB_W, f"{name}/fab")
    f.add(circle(0, 0, 2.3, "F.Fab", FAB_W, f"{name}/fab/barrel"))
    # silkscreen: the body's square with the corners cut where the leg pads are
    for key, (x1, y1, x2, y2) in {"t": (-1.0, -h, 1.0, -h), "b": (-1.0, h, 1.0, h), "l": (-h, -1.0, -h, 1.0), "r": (h, -1.0, h, 1.0)}.items():
        f.add(line(x1, y1, x2, y2, "F.SilkS", SILK_W, f"{name}/silk/{key}"))
    rect_lines(f, -h - 0.25, -h - 0.25, h + 0.25, h + 0.25, "F.CrtYd", CRT_W, f"{name}/crt")
    text_fab(f, "SMA", 0, 0, f"{name}/fabtxt")
    model(f, "SMA_Vertical.wrl")
    return name, f


# ---------------------------------------------------------------- test loop --
def testloop():
    """RH-5019 SMT test loop (LCSC C5199800): JLCPCB's pattern is one 4.0 x 2.2 mm pad, the loop along x."""
    name = "TestPoint_Loop_RH-5019"
    f = fp_header(name, "SMT test loop, 3.8 x 2.0 mm, RH-5019 / Keystone 5019 (LCSC C5199800)", "test point loop probe", "smd", 2.6)
    f.add(smd_pad("1", 0, 0, 4.0, 2.2, f"{name}/p1"))
    rect_lines(f, -1.9, -1.0, 1.9, 1.0, "F.Fab", FAB_W, f"{name}/fab")
    rect_lines(f, -2.3, -1.4, 2.3, 1.4, "F.CrtYd", CRT_W, f"{name}/crt")
    model(f, "TestLoop_RH-5019.wrl")
    return name, f


# --------------------------------------------------------------- DIP switches --
def dip(nways):
    """DSHP0xTSGET half-pitch SMD DIP switches (C40735 / C40736 / C40737).  JLCPCB's land patterns (easyeda,
    2026-10-25): pads 0.76 x 1.52 at 1.27 mm along x in two rows 7.62 mm apart; the body 5.4 mm across the rows and
    1.27 N + 1.6 along them, 2.5 high, recessed sliders.  Numbered as KiCad's SW_DIP_x0N: way k is pads k and 2N+1-k,
    pads 1..N along the +y row left to right (pin 1 bottom-left, as JLCPCB draws the 2- and 4-way; the 6-way's drawing
    has pin 1 top-right, so its CPL rotation is 180).  ON is toward -y (the row of pads N+1..2N); the part is printed."""
    name = "SW_DIP_SPSTx%02d_Slide_1.27mm_DSHP%02d" % (nways, nways)
    codes = {2: "C40735", 4: "C40736", 6: "C40737"}
    f = fp_header(name, "%d-way SMD DIP switch, 1.27 mm pitch, DSHP%02dTSGET (LCSC %s), JLCPCB's land pattern" % (nways, nways, codes[nways]),
                  "DIP switch SPST x%d SMD 1.27mm half pitch" % nways, "smd", 5.6)
    row = 3.81
    pw, ph = 0.76, 1.52
    for k in range(1, nways + 1):
        x = (k - (nways + 1) / 2.0) * 1.27
        f.add(smd_pad(str(k), x, row, pw, ph, f"{name}/p{k}"))
        f.add(smd_pad(str(2 * nways + 1 - k), x, -row, pw, ph, f"{name}/p{2 * nways + 1 - k}"))
    hw, hl = nways * 0.635 + 0.8, 2.7
    rect_lines(f, -hw, -hl, hw, hl, "F.Fab", FAB_W, f"{name}/fab")
    rect_lines(f, -hw, -hl, hw, hl, "F.SilkS", SILK_W, f"{name}/silk")
    rect_lines(f, -hw - 0.25, -(row + ph / 2 + 0.25), hw + 0.25, row + ph / 2 + 0.25, "F.CrtYd", CRT_W, f"{name}/crt")
    text_fab(f, "ON", 0, -1.5, f"{name}/fabtxt", size=0.6)
    model(f, "SW_DIP_x%02d_DSHP.wrl" % nways)
    return name, f


# ------------------------------------------------------------ screw terminals --
def kf301(npins):
    """KEFA KF301-5.0-xP (C474881 / C474882): pins on 5.0 mm centres, 2.2 mm pads on 1.4 mm holes (JLCPCB's
    drawing); the body 7.6 deep, the wires enter from -y."""
    name = "TerminalBlock_KF301_1x%02d_P5.00mm" % npins
    f = fp_header(name, "%d-way 5.0 mm screw terminal block, KEFA KF301-5.0-%dP (LCSC %s); wires enter from -y" % (npins, npins, "C474881" if npins == 2 else "C474882"),
                  "screw terminal block KF301 5.0mm", "through_hole", 5.6)
    for i in range(npins):
        x = (i - (npins - 1) / 2.0) * 5.0
        f.add(tht_pad(str(i + 1), x, 0, 1.4, 2.2, f"{name}/p{i + 1}", shape="rect" if i == 0 else "circle"))
    w = npins * 5.0 + 0.4
    x0, x1, yf, yb = -w / 2, w / 2, -4.0, 3.6
    rect_lines(f, x0, yf, x1, yb, "F.Fab", FAB_W, f"{name}/fab")
    rect_lines(f, x0 - 0.1, yf - 0.1, x1 + 0.1, yb + 0.1, "F.SilkS", SILK_W, f"{name}/silk")
    for i in range(npins):
        x = (i - (npins - 1) / 2.0) * 5.0
        f.add(line(x - 1.5, yf - 0.1, x - 1.5, yf + 1.2, "F.SilkS", SILK_W, f"{name}/silk/w{i}a"),
              line(x + 1.5, yf - 0.1, x + 1.5, yf + 1.2, "F.SilkS", SILK_W, f"{name}/silk/w{i}b"),
              line(x - 1.5, yf + 1.2, x + 1.5, yf + 1.2, "F.SilkS", SILK_W, f"{name}/silk/w{i}c"))
    rect_lines(f, x0 - 0.35, yf - 0.35, x1 + 0.35, yb + 0.35, "F.CrtYd", CRT_W, f"{name}/crt")
    model(f, "TerminalBlock_KF301_1x%02d.wrl" % npins)
    return name, f


# ---------------------------------------------------------------- Pmod plug --
def pmod_plug():
    """PZ254R-12-12P (LCSC C492434), a 2 x 6 right-angle male header.  JLCPCB's land pattern (easyeda,
    2026-10-25): 12 pads 1.80 mm on 1.10 mm drills, columns at x = -6.35 .. 6.35 step 2.54, rows at
    y = +1.27 (odd pads) and -1.27 (even pads); the plastic body on the +y side (silk y 5.37 .. 11.31),
    so the pins leave the board toward +y.  Pad k (odd) is Pmod pin (k+1)/2 and pad k (even) is Pmod pin
    k/2 + 6 (the ECP5 board's lesson, CLAUDE_PCB.md): pin 1 is the +y-row pad at -x when the pins point
    +y."""
    name = "PinHeader_2x06_P2.54mm_Horizontal_PZ254R-12-12P"
    f = fp_header(name, "2x6 right-angle male header 2.54 mm, XFCN PZ254R-12-12P (LCSC C492434): the Pmod plug; pins leave toward +y",
                  "pin header 2x6 right angle Pmod", "through_hole", -3.0)
    for k in range(1, 13):
        col = (k - 1) // 2
        x = -6.35 + col * 2.54
        y = 1.27 if k % 2 else -1.27
        f.add(tht_pad(str(k), x, y, 1.10, 1.80, f"{name}/p{k}", shape="rect" if k == 1 else "circle"))
    # the body (6.0 mm deep from y 5.37 to 11.31 in JLCPCB's drawing, 15.2 wide) and the bent pins
    rect_lines(f, -7.62, 2.6, 7.62, 11.3, "F.Fab", FAB_W, f"{name}/fab")
    rect_lines(f, -7.62, 2.6, 7.62, 11.3, "F.SilkS", SILK_W, f"{name}/silk")
    for k in range(6):
        x = -6.35 + k * 2.54
        f.add(line(x, -1.27, x, 2.6, "F.Fab", FAB_W, f"{name}/fab/pin{k}"))
    rect_lines(f, -8.2, -2.5, 8.2, 17.5, "F.CrtYd", CRT_W, f"{name}/crt")      # the pins reach about 6 mm past the body
    text_fab(f, "Pmod 1", -6.35, 3.6, f"{name}/fabtxt", size=0.6)
    model(f, "PinHeader_2x06_RightAngle.wrl")
    return name, f


# --------------------------------------------------------- ceramic resonator --
def kcr455():
    """KCR455E 455 kHz ceramic resonator (LCSC C366989): two leads on 5.0 mm, body 7.0 x 3.5 (JLCPCB's FILTER-TH_2P-L7.0-W3.5-P5.00)."""
    name = "Resonator_Ceramic_2Pin_P5.00mm_KCR455E"
    f = fp_header(name, "455 kHz ceramic resonator, 2 leads on 5.0 mm, body 7.0 x 3.5 mm: Kecheng KCR455E (LCSC C366989)",
                  "ceramic resonator 455kHz", "through_hole", 3.2)
    f.add(tht_pad("1", -2.5, 0, 0.8, 1.6, f"{name}/p1"), tht_pad("2", 2.5, 0, 0.8, 1.6, f"{name}/p2"))
    rect_lines(f, -3.5, -1.75, 3.5, 1.75, "F.Fab", FAB_W, f"{name}/fab")
    rect_lines(f, -3.6, -1.85, 3.6, 1.85, "F.SilkS", SILK_W, f"{name}/silk")
    rect_lines(f, -3.85, -2.1, 3.85, 2.1, "F.CrtYd", CRT_W, f"{name}/crt")
    model(f, "Resonator_KCR455.wrl")
    return name, f


# -------------------------------------------------------- HC-49S SMD crystal --
def hc49s_smd():
    """X49SM4MSD2SC 4 MHz crystal in HC-49S-SMD (LCSC C13774): two 5.5 x 1.3 pads centred at +-4.553 (JLCPCB's drawing), body 11.4 x 4.5."""
    name = "Crystal_HC49-S_SMD"
    f = fp_header(name, "HC-49S SMD crystal, 11.4 x 4.5 mm body, two gull-wing leads: YXC X49SM4MSD2SC 4 MHz (LCSC C13774)", "crystal HC49 SMD", "smd", 3.4)
    f.add(smd_pad("1", -4.553, 0, 5.5, 1.3, f"{name}/p1"), smd_pad("2", 4.553, 0, 5.5, 1.3, f"{name}/p2"))
    rect_lines(f, -5.7, -2.25, 5.7, 2.25, "F.Fab", FAB_W, f"{name}/fab")
    f.add(line(-5.7, -2.4, 5.7, -2.4, "F.SilkS", SILK_W, f"{name}/silk/t"), line(-5.7, 2.4, 5.7, 2.4, "F.SilkS", SILK_W, f"{name}/silk/b"))
    rect_lines(f, -7.6, -2.6, 7.6, 2.6, "F.CrtYd", CRT_W, f"{name}/crt")
    model(f, "Crystal_HC49S_SMD.wrl")
    return name, f


# ----------------------------------------------------------- PD70-01C --
def pd70():
    """Everlight PD70-01C/TR7 photodiode (LCSC C131196): two 1.8 mm square pads at +-3.6 (JLCPCB), body 4.4 x 3.9.
    JLCPCB's pad 1 is the ANODE end in their drawing? Their symbol names the pins; CLAUDE_PCB.md: check the
    diode's anode against the datasheet and JLCPCB's drawing before the order (PLACEMENT_CHECKS)."""
    name = "Photodiode_PD70-01C"
    f = fp_header(name, "Everlight PD70-01C PIN photodiode, 4.4 x 3.9 mm, two pads at +-3.6 mm (LCSC C131196); pad 1 cathode as KiCad's Device:Photodiode",
                  "photodiode PIN", "smd", 3.0)
    f.add(smd_pad("1", -3.6, 0, 1.8, 1.8, f"{name}/p1"), smd_pad("2", 3.6, 0, 1.8, 1.8, f"{name}/p2"))
    rect_lines(f, -2.2, -1.95, 2.2, 1.95, "F.Fab", FAB_W, f"{name}/fab")
    rect_lines(f, -2.3, -2.05, 2.3, 2.05, "F.SilkS", SILK_W, f"{name}/silk")
    rect_lines(f, -4.75, -2.3, 4.75, 2.3, "F.CrtYd", CRT_W, f"{name}/crt")
    model(f, "Photodiode_PD70.wrl")
    return name, f


# --------------------------------------------------------- side-view LED --
def led_side():
    """E6C1204URAC1UDA red side-view LED 3.2 x 1.0 (LCSC C375479): JLCPCB's pads 1.3 x 0.9 at +-1.6 and a 1.0 x 0.8 centre pad.
    Light leaves along -y (the face away from the pads' side); pad 1 is the cathode by JLCPCB's drawing: to be read in the preview."""
    name = "LED_SideView_3.2x1.0mm_E6C1204"
    f = fp_header(name, "red side-view LED 3.2 x 1.0 mm, Everlight E6C1204URAC1UDA (LCSC C375479); shines toward -y", "LED side view red", "smd", 2.0)
    f.add(smd_pad("1", 1.6, -0.225, 1.3, 0.9, f"{name}/p1"), smd_pad("2", -1.6, -0.225, 1.3, 0.9, f"{name}/p2"),
          smd_pad("3", 0, 0.225, 1.0, 0.8, f"{name}/p3"))
    rect_lines(f, -1.6, -0.5, 1.6, 0.5, "F.Fab", FAB_W, f"{name}/fab")
    f.add(line(-1.6, 0.75, 1.6, 0.75, "F.SilkS", SILK_W, f"{name}/silk"))
    rect_lines(f, -2.5, -1.0, 2.5, 1.0, "F.CrtYd", CRT_W, f"{name}/crt")
    model(f, "LED_Side.wrl")
    return name, f


# ------------------------------------------------------------ 3.5 mm jack --
def pj320a():
    """XKB PJ-320A 3.5 mm 4-pole jack (LCSC C2884926), SMD pads 1.0 x 2.0 at (-4,-2.4), (-1,-2.4), (3,-2.4), (4,+2.4), two 1.2 mm posts;
    the barrel opens toward -x (JLCPCB's silk runs from x -9.2 to 5.2).  Pads numbered as JLCPCB's: 2 sleeve, 3 ring 2, 4 ring 1, 5 tip."""
    name = "Jack_3.5mm_PJ-320A"
    f = fp_header(name, "3.5 mm TRRS jack, SMD, XKB PJ-320A (LCSC C2884926); the plug enters from -x", "audio jack 3.5mm", "smd", 4.0)
    for num, (x, y) in {"2": (-4.0, -2.4), "3": (-1.0, -2.4), "4": (3.0, -2.4), "5": (4.0, 2.4)}.items():
        f.add(smd_pad(num, x, y, 1.0, 2.0, f"{name}/p{num}"))
    f.add(npth(-5.6, 0, 1.2, 1.2, f"{name}/h1"), npth(1.4, 0, 1.2, 1.2, f"{name}/h2"))
    rect_lines(f, -9.2, -3.05, 5.2, 3.05, "F.Fab", FAB_W, f"{name}/fab")
    rect_lines(f, -9.2, -3.2, 5.2, 3.2, "F.SilkS", SILK_W, f"{name}/silk")
    rect_lines(f, -9.5, -3.7, 5.5, 3.7, "F.CrtYd", CRT_W, f"{name}/crt")
    model(f, "Jack_PJ320A.wrl")
    return name, f


# ------------------------------------------------------------- RF filters --
def saw_1411():
    """B39921B2672P810 915 MHz SAW (LCSC C1518004), SMD 1.4 x 1.1, five 0.25 x 0.32 pads: 1 at (-0.5, 0), 2 (0, +0.287), 3 (+0.5, +0.287),
    4 (+0.5, -0.287), 5 (0, -0.287) (JLCPCB's drawing).  RF Microelectronics' pinout: 1 IN, 3 OUT, the rest ground."""
    name = "Filter_SAW_1411-5P_B39921"
    f = fp_header(name, "915 MHz SAW filter, 1.4 x 1.1 mm, 5 pads: RF360 B39921B2672P810 (LCSC C1518004)", "SAW filter", "smd", 1.5)
    for num, (x, y) in {"1": (-0.5, 0.0), "2": (0.0, 0.287), "3": (0.5, 0.287), "4": (0.5, -0.287), "5": (0.0, -0.287)}.items():
        f.add(smd_pad(num, x, y, 0.25, 0.32, f"{name}/p{num}"))
    rect_lines(f, -0.7, -0.55, 0.7, 0.55, "F.Fab", FAB_W, f"{name}/fab")
    rect_lines(f, -0.95, -0.8, 0.95, 0.8, "F.CrtYd", CRT_W, f"{name}/crt")
    f.add(circle(-0.9, 0.0, 0.08, "F.SilkS", SILK_W, f"{name}/silk/p1", fill=True))
    model(f, "Filter_1411.wrl")
    return name, f


def lfb212():
    """Murata LFB212G45SG8A127 2.45 GHz band-pass (LCSC C341536), 2.0 x 1.25: pads 1 and 3 are 1.6 x 0.35 along the long sides at y = -+0.574
    (ground), 2 and 4 are 0.35 x 0.30 at the ends x = +-0.9 (in and out), as JLCPCB draws it."""
    name = "Filter_LTCC_2012_LFB212"
    f = fp_header(name, "2.4-2.5 GHz LTCC band-pass filter, 2.0 x 1.25 mm, 4 pads: Murata LFB212G45SG8A127 (LCSC C341536)", "LTCC filter", "smd", 1.8)
    f.add(smd_pad("1", 0, -0.574, 1.6, 0.35, f"{name}/p1"), smd_pad("2", 0.9, 0, 0.35, 0.30, f"{name}/p2"),
          smd_pad("3", 0, 0.574, 1.6, 0.35, f"{name}/p3"), smd_pad("4", -0.9, 0, 0.35, 0.30, f"{name}/p4"))
    rect_lines(f, -1.0, -0.625, 1.0, 0.625, "F.Fab", FAB_W, f"{name}/fab")
    rect_lines(f, -1.3, -0.95, 1.3, 0.95, "F.CrtYd", CRT_W, f"{name}/crt")
    f.add(circle(-1.2, -0.85, 0.08, "F.SilkS", SILK_W, f"{name}/silk/p1", fill=True))
    model(f, "Filter_2012.wrl")
    return name, f


def slot():
    """A 1.2 x 3.4 mm plated-nothing slot, for a cable tie through the board (P13's ferrite rod)."""
    name = "Slot_CableTie_1.2x3.4mm"
    f = fp_header(name, "NPTH slot 1.2 x 3.4 mm for a cable tie", "slot cable tie", "exclude_from_pos_files exclude_from_bom", 2.6)
    f.add(npth(0, 0, 1.2, 3.4, f"{name}/slot"))
    rect_lines(f, -1.0, -2.1, 1.0, 2.1, "F.CrtYd", CRT_W, f"{name}/crt")
    return name, f


def slide_switch():
    """The MSK12C02 footprint the motor-pid board vendored: KiCad's SW_SPDT_Shouhan_MSK12C02 with the locating holes
    lengthened so JLCPCB's drawing of the posts (0.3 mm further out) fits too.  Copied, with its model pointed at our library."""
    text = open(os.path.join(VENDORED, "SW_SPDT_Shouhan_MSK12C02.kicad_mod"), encoding="utf-8").read()
    text = re.sub(r'\(model "[^"]*"', '(model "${KIPRJMOD}/lib/%s.3dshapes/SW_MSK12C02.wrl"' % LIB, text)
    return "SW_SPDT_Shouhan_MSK12C02", text


def led_0805():
    """KiCad's LED_0805_2012Metric (pads 0.975 x 1.4 at +-0.9375, courtyard +-1.68 x 0.95) with only a cathode bar on
    the silk: the library's bracket runs the part's whole length at y +-0.96, so two LEDs 2.0 mm apart overlap."""
    name = "LED_0805_2012Metric_Kbar"
    f = fp_header(name, "0805 LED, KiCad's land pattern, cathode bar only on the silk (pin 1 = K)", "LED 0805 cathode bar", "smd", 2.0)
    f.add(smd_pad("1", -0.9375, 0, 0.975, 1.4, f"{name}/p1"))
    f.add(smd_pad("2", 0.9375, 0, 0.975, 1.4, f"{name}/p2"))
    f.add(line(-1.685, -0.7, -1.685, 0.7, "F.SilkS", SILK_W, f"{name}/kbar"))
    rect_lines(f, -1.0, -0.625, 1.0, 0.625, "F.Fab", FAB_W, f"{name}/fab")
    f.add(line(-1.0, -0.625, -0.6, -0.625, "F.Fab", FAB_W * 3, f"{name}/fabk"))
    rect_lines(f, -1.68, -0.95, 1.68, 0.95, "F.CrtYd", CRT_W, f"{name}/crt")
    model(f, "LED_0805.wrl")
    return name, f


MAKERS = [sma_vertical, testloop, lambda: dip(2), lambda: dip(4), lambda: dip(6), lambda: kf301(2), lambda: kf301(3),
          pmod_plug, kcr455, hc49s_smd, pd70, led_side, led_0805, pj320a, saw_1411, lfb212, slot]


def main():
    os.makedirs(OUT, exist_ok=True)
    for maker in MAKERS:
        name, node = maker()
        with open(os.path.join(OUT, name + ".kicad_mod"), "w") as fh:
            fh.write(node.render() + "\n")
        print("  wrote %s" % os.path.relpath(os.path.join(OUT, name + ".kicad_mod")))
    name, text = slide_switch()
    with open(os.path.join(OUT, name + ".kicad_mod"), "w") as fh:
        fh.write(text)
    print("  wrote %s (vendored)" % name)


if __name__ == "__main__":
    main()
