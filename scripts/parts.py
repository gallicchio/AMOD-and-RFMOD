"""Single source of truth for every part on the three boards: value, footprint, symbol, LCSC code,
JLCPCB library type, stock and price on STOCK_DATE, and the notes.  The schematics, the BOMs, the
CPLs, the cost estimate and the silkscreen legends read this table; the fab check compares every
code's JLCPCB description with its value and package before a release (scripts/jlc_api.py
re-queries; the cache keeps each answer's time).

A board part is PARTS[key]; a passive is PASSIVES["<kind><package> <value>"] ("R0805 1k",
"C0603 390pF", "L1210 150uH"), whose footprint and symbol follow from the key.  `info(key)`
returns one merged record for either.
"""
import re

REV = "A"
DATE = "2026-10-25"
STOCK_DATE = "2026-10-25"
URL = "github.com/gallicchio/AMOD-and-RFMOD"
AUTHORS = "Jason Gallicchio and Claude"
LIB = "amod"

BOARDS = {
    "amod_p": dict(stem="amod_p", name="AMOD-P", title="AMOD-P: passive building blocks for the converters", layers=2,
                   subtitle="pads, RC and LC filters, resonators, a crystal, a clipper, a tapped delay line, LEDs, an AM loopstick"),
    "amod_a": dict(stem="amod_a", name="AMOD-A", title="AMOD-A: active building blocks on USB-C power", layers=4,
                   subtitle="gain blocks, an HF LNA, Johnson noise, a one-pin ADC, a 74HC4046 PLL, heat, a mixer, light, ultrasound, audio"),
    "rf_mod": dict(stem="rf_mod", name="RF-MOD", title="RF-MOD: 915 MHz, 2.4 GHz and a stretch to 5.8 GHz", layers=4,
                   subtitle="printed antennas, filters, an LNA, a 2.4 GHz front end, two mixers, two synthesizers, a gain block, a quadrature transmitter"),
}

# lcsc / jlc_type ("basic" | "preferred" | "extended") / process ("SMT" | "THT") / stock on STOCK_DATE / price (1-9) /
# footprint ("Lib:Name"; "amod:" is the project library) / symbol / desc / match (words JLCPCB's description must contain) / alt
PARTS = {
    "SMA": dict(value="SMA", mpn="BWSMA-KE-Z001", lcsc="C496549", jlc_type="extended", process="THT", stock=112911, price=0.4043,
                footprint="amod:SMA_BWSMA-KE-Z001_Vertical", symbol="Connector:Conn_Coaxial", match=["BWSMA-KE-Z001"],
                desc="straight SMA jack, 6.5 mm square, 13.5 mm tall, 0-6 GHz, 500 cycles: every tile's port"),
    "TP": dict(value="", mpn="RH-5019", lcsc="C5199800", jlc_type="extended", process="SMT", stock=245451, price=0.0966,
               footprint="amod:TestPoint_Loop_RH-5019", symbol="Connector:TestPoint", match=["RH-5019"],
               desc="SMT test loop, 3.8 x 2.0 mm, for a scope hook or a mini-grabber"),
    "DIP2": dict(value="SW_DIP_x02", mpn="DSHP02TSGET", lcsc="C40735", jlc_type="extended", process="SMT", stock=13697, price=0.6039,
                 footprint="amod:SW_DIP_SPSTx02_Slide_1.27mm_DSHP02", symbol="Switch:SW_DIP_x02", match=["DSHP02TSGET"],
                 desc="2-way SMD DIP switch, 1.27 mm half pitch, recessed sliders (a pen tip flips them)"),
    "DIP4": dict(value="SW_DIP_x04", mpn="DSHP04TSGET", lcsc="C40736", jlc_type="extended", process="SMT", stock=30841, price=0.5450,
                 footprint="amod:SW_DIP_SPSTx04_Slide_1.27mm_DSHP04", symbol="Switch:SW_DIP_x04", match=["DSHP04TSGET"],
                 desc="4-way SMD DIP switch, 1.27 mm half pitch"),
    "DIP6": dict(value="SW_DIP_x06", mpn="DSHP06TSGET", lcsc="C40737", jlc_type="extended", process="SMT", stock=5016, price=0.6350,
                 footprint="amod:SW_DIP_SPSTx06_Slide_1.27mm_DSHP06", symbol="Switch:SW_DIP_x06", match=["DSHP06TSGET"],
                 desc="6-way SMD DIP switch, 1.27 mm half pitch"),
    "TERM2": dict(value="Screw_Terminal_01x02", mpn="KF301-5.0-2P", lcsc="C474881", jlc_type="extended", process="THT", stock=84342, price=0.1017,
                  footprint="amod:TerminalBlock_KF301_1x02_P5.00mm", symbol="Connector:Screw_Terminal_01x02", match=["KF301-5.0-2P"],
                  desc="2-way 5.0 mm screw terminal, blue"),
    "TERM3": dict(value="Screw_Terminal_01x03", mpn="KF301-5.0-3P", lcsc="C474882", jlc_type="extended", process="THT", stock=27437, price=0.1396,
                  footprint="amod:TerminalBlock_KF301_1x03_P5.00mm", symbol="Connector:Screw_Terminal_01x03", match=["KF301-5.0-3P"],
                  desc="3-way 5.0 mm screw terminal, blue"),
    "XTAL4M": dict(value="4 MHz", mpn="X49SM4MSD2SC", lcsc="C13774", jlc_type="extended", process="SMT", stock=33932, price=0.1095,
                   footprint="amod:Crystal_HC49-S_SMD", symbol="Device:Crystal", match=["4MHz", "HC-49S"],
                   desc="4.000 MHz quartz crystal, HC-49S SMD, 20 pF load, 120 ohm ESR max (YXC)"),
    "RES455": dict(value="455 kHz", mpn="KCR455E", lcsc="C366989", jlc_type="extended", process="THT", stock=504, price=0.1051,
                   footprint="amod:Resonator_Ceramic_2Pin_P5.00mm_KCR455E", symbol="Device:Crystal", match=["455kHz"],
                   desc="455 kHz two-terminal ceramic resonator, 5 mm leads (Kecheng KCR455E); alternates on the same footprint: HCTB1-455 C19181337"),
    "D1N4148": dict(value="1N4148W", mpn="1N4148W", lcsc="C81598", jlc_type="basic", process="SMT", stock=4120462, price=0.0124,
                    footprint="Diode_SMD:D_SOD-123", symbol="Diode:1N4148W", match=["1N4148W"], desc="small-signal silicon diode, SOD-123 (Basic)"),
    "LED_R": dict(value="red 630 nm", mpn="NCD0805R1", lcsc="C84256", jlc_type="basic", process="SMT", stock=3079163, price=0.0135,
                  footprint="amod:LED_0805_2012Metric_Kbar", symbol="Device:LED", match=["NCD0805R1"], desc="red 0805 LED, 630 nm, 1.6-2.6 V (Basic; JLCPCB rotation 0 read on GPiBridge)"),
    "LED_Y": dict(value="yellow 596 nm", mpn="KT-0805Y", lcsc="C2296", jlc_type="basic", process="SMT", stock=693960, price=0.0146,
                  footprint="amod:LED_0805_2012Metric_Kbar", symbol="Device:LED", match=["KT-0805Y"], desc="yellow 0805 LED, 584-594 nm, 1.8-2.4 V (Basic)"),
    "LED_G": dict(value="green 525 nm", mpn="KT-0805G", lcsc="C2297", jlc_type="basic", process="SMT", stock=2415050, price=0.0164,
                  footprint="amod:LED_0805_2012Metric_Kbar", symbol="Device:LED", match=["KT-0805G"], desc="green 0805 LED, 513-528 nm InGaN, 2.6-3.1 V (Basic; rotation 0 read on GPiBridge)"),
    "LED_B": dict(value="blue 469 nm", mpn="KT-0805B", lcsc="C2293", jlc_type="extended", process="SMT", stock=92857, price=0.0124,
                  footprint="amod:LED_0805_2012Metric_Kbar", symbol="Device:LED", match=["KT-0805B"], desc="blue 0805 LED, 460-475 nm, 3.1 V"),
    "MH": dict(value="", process="THT", in_bom=False, footprint="MountingHole:MountingHole_3.2mm_M3", symbol="Mechanical:MountingHole",
               desc="M3 mounting hole, one per corner"),
    "SLOT": dict(value="", process="THT", in_bom=False, footprint="amod:Slot_CableTie_1.2x3.4mm", symbol="Mechanical:MountingHole",
                 desc="a 1.2 x 3.4 mm slot for a cable tie (holds the ferrite rod)"),
}

# Passives: key "<kind><package> <value>".  Footprint and symbol follow from the key.  C0G/NP0 wherever the value sets
# a frequency; X7R only for decoupling.  Resistors from Uniroyal's 0805W8F (Basic) wherever the value exists there.
PASSIVES = {
    # --- 0805 resistors ---
    "R0805 49.9R": dict(lcsc="C17720", mpn="0805W8F499JT5E", jlc_type="basic", stock=569614, price=0.0049),
    "R0805 61.9R": dict(lcsc="C17779", mpn="0805W8F619JT5E", jlc_type="extended", stock=4584, price=0.0038),
    "R0805 100R": dict(lcsc="C17408", mpn="0805W8F1000T5E", jlc_type="basic", stock=8117449, price=0.0042),
    "R0805 249R": dict(lcsc="C32281", mpn="0805W8F2490T5E", jlc_type="extended", stock=123619, price=0.0032),
    "R0805 470R": dict(lcsc="C17710", mpn="0805W8F4700T5E", jlc_type="basic", stock=2348951, price=0.0048),
    "R0805 1k": dict(lcsc="C17513", mpn="0805W8F1001T5E", jlc_type="basic", stock=43091809, price=0.0035),
    "R0805 2.2k": dict(lcsc="C17520", mpn="0805W8F2201T5E", jlc_type="basic", stock=3549595, price=0.0049),
    "R0805 4.7k": dict(lcsc="C17673", mpn="0805W8F4701T5E", jlc_type="basic", stock=4743467, price=0.0051),
    "R0805 10k": dict(lcsc="C17414", mpn="0805W8F1002T5E", jlc_type="basic", stock=54229128, price=0.0034),
    "R0805 100k": dict(lcsc="C149504", mpn="0805W8F1003T5E", jlc_type="basic", stock=3366438, price=0.0059),
    # --- 0805 capacitors, C0G ---
    "C0805 10pF": dict(lcsc="C157608", mpn="0805CG100J500NT", jlc_type="extended", stock=45432, price=0.0104, note="C0G"),
    "C0805 22pF": dict(lcsc="C1804", mpn="CL21C220JBANNNC", jlc_type="basic", stock=624282, price=0.0122, note="C0G"),
    "C0805 33pF": dict(lcsc="C157687", mpn="0805CG330J500NT", jlc_type="extended", stock=26516, price=0.0065, note="C0G"),
    "C0805 47pF": dict(lcsc="C14857", mpn="CL21C470JBANNNC", jlc_type="basic", stock=99872, price=0.0082, note="C0G"),
    "C0805 100pF": dict(lcsc="C1790", mpn="CL21C101JBANNNC", jlc_type="basic", stock=663030, price=0.0101, note="C0G"),
    "C0805 220pF": dict(lcsc="C1805", mpn="0805CG221J500NT", jlc_type="extended", stock=6568, price=0.0111, note="C0G"),
    "C0805 270pF": dict(lcsc="C501860", mpn="0805CG271J500NT", jlc_type="extended", stock=3542, price=0.0187, note="C0G"),
    "C0805 330pF": dict(lcsc="C1815", mpn="0805CG331J500NT", jlc_type="extended", stock=20190, price=0.0132, note="C0G"),
    "C0805 470pF": dict(lcsc="C1822", mpn="0805CG471J500NT", jlc_type="extended", stock=34110, price=0.0189, note="C0G"),
    "C0805 680pF": dict(lcsc="C1835", mpn="0805CG681J500NT", jlc_type="extended", stock=7745, price=0.0138, note="C0G"),
    "C0805 1nF": dict(lcsc="C29925", mpn="0805CG102J500NT", jlc_type="extended", stock=127017, price=0.0138, note="C0G"),
    "C0805 2.2nF": dict(lcsc="C51795", mpn="0805CG222J500NT", jlc_type="extended", stock=3380, price=0.0424, note="C0G"),
    "C0805 10nF": dict(lcsc="C2971995", mpn="0805CG103J500NT", jlc_type="extended", stock=154680, price=0.0421, note="C0G"),
    # --- 0805 capacitors, X7R / X5R (decoupling only) ---
    "C0805 100nF": dict(lcsc="C49678", mpn="CC0805KRX7R9BB104", jlc_type="basic", stock=22490642, price=0.0205, note="X7R 50 V"),
    "C0805 1uF": dict(lcsc="C28323", mpn="CL21B105KBFNNNE", jlc_type="basic", stock=1906196, price=0.0341, note="X7R 50 V"),
    "C0805 10uF": dict(lcsc="C15850", mpn="CL21A106KAYNNNE", jlc_type="basic", stock=9131839, price=0.0426, note="X5R 25 V"),
    # --- 0603 (the delay line and the RF board) ---
    "C0402 390pF": dict(lcsc="C282239", mpn="CC0402JRNPO9BN391", jlc_type="extended", stock=92071, price=0.0051, note="NP0, the delay line"),
    "C0603 47pF": dict(lcsc="C1671", mpn="CL10C470JB8NNNC", jlc_type="basic", stock=891649, price=0.0074, note="C0G"),
    "C0603 100pF": dict(lcsc="C14858", mpn="CL10C101JB8NNNC", jlc_type="basic", stock=4843924, price=0.0087, note="C0G"),
    "C0603 390pF": dict(lcsc="C1667", mpn="0603CG391J500NT", jlc_type="extended", stock=8288, price=0.0113, note="C0G"),
    "C0603 470pF": dict(lcsc="C36252", mpn="0603CG471J500NT", jlc_type="extended", stock=83282, price=0.0098, note="C0G"),
    "C0603 100nF": dict(lcsc="C14663", mpn="CC0603KRX7R9BB104", jlc_type="basic", stock=44086756, price=0.0084, note="X7R 50 V"),
    "R0603 100R": dict(lcsc="C22775", mpn="0603WAF1000T5E", jlc_type="basic", stock=10639094, price=0.0023),
    "R0603 1k": dict(lcsc="C21190", mpn="0603WAF1001T5E", jlc_type="basic", stock=35103609, price=0.0017),
    "R0603 10k": dict(lcsc="C25804", mpn="0603WAF1002T5E", jlc_type="basic", stock=40711984, price=0.0022),
    "C0603 270pF": dict(lcsc="C501846", mpn="0603CG271J500NT", jlc_type="extended", stock=842, price=0.0131, note="C0G"),
    "C0603 2.2nF": dict(lcsc="C2991172", mpn="0603CG222J500NT", jlc_type="extended", stock=74606, price=0.0142, note="C0G"),
    "L0603 2.7uH": dict(lcsc="C29946", mpn="SDFL1608Q2R7KTF", jlc_type="extended", stock=3814, price=0.0091, note="multilayer, Q 35 at 10 MHz, SRF 45 MHz, 15 mA"),
    "L0603 330nH": dict(lcsc="C142165", mpn="CS0603-R33J-S", jlc_type="extended", stock=3760, price=0.0634, note="Q 25 at 100 MHz, SRF 900 MHz, 100 mA"),
    "L0603 1uH": dict(lcsc="C22037", mpn="SDFL1608Q1R0KTF", jlc_type="extended", stock=71621, price=0.0269, note="multilayer, Q 35 at 10 MHz, SRF 75 MHz, 25 mA"),
    # --- inductors ---
    "L0805 330nH": dict(lcsc="C98210", mpn="SDWL2012CR33JSTF", jlc_type="extended", stock=9910, price=0.0851, note="wire-wound, Q 40 at 100 MHz, SRF 600 MHz"),
    "L0805 1.5uH": dict(lcsc="C316402", mpn="SDFL2012Q1R5KTF", jlc_type="extended", stock=3868, price=0.0500, note="multilayer, Q 45 at 10 MHz, SRF 60 MHz, 50 mA"),
    "L0805 2.7uH": dict(lcsc="C74318", mpn="SDFL2012Q2R7KTF", jlc_type="extended", stock=2719, price=0.0477, note="multilayer, Q 45 at 10 MHz, SRF 45 MHz, 30 mA"),
    "L1210 100uH": dict(lcsc="C76836", mpn="NLV32T-101J-PF", jlc_type="extended", stock=66282, price=0.0555, note="TDK, 10 ohm, 40 mA, shielded"),
    "L1210 150uH": dict(lcsc="C250237", mpn="NLCV32T-151K-EF", jlc_type="extended", stock=10151, price=0.0482, note="TDK, 6.1 ohm, 100 mA, shielded"),
}

FOOTPRINT_OF = {"R0805": "Resistor_SMD:R_0805_2012Metric", "R0603": "Resistor_SMD:R_0603_1608Metric", "R1206": "Resistor_SMD:R_1206_3216Metric",
                "R2512": "Resistor_SMD:R_2512_6332Metric", "C0805": "Capacitor_SMD:C_0805_2012Metric", "C0603": "Capacitor_SMD:C_0603_1608Metric", "C0402": "Capacitor_SMD:C_0402_1005Metric",
                "C1206": "Capacitor_SMD:C_1206_3216Metric", "L0805": "Inductor_SMD:L_0805_2012Metric", "L0603": "Inductor_SMD:L_0603_1608Metric",
                "L1210": "Inductor_SMD:L_1210_3225Metric"}
SYMBOL_OF = {"R": "Device:R_US", "C": "Device:C", "L": "Device:L"}


def passive_value(key):
    """'C0805 220pF' -> 220e-12; 'R0805 61.9R' -> 61.9; 'L1210 150uH' -> 150e-6."""
    v = key.split(" ", 1)[1]
    m = re.match(r"([\d.]+)\s*([pnumkMR]?)", v)
    return float(m.group(1)) * {"p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3, "": 1.0, "R": 1.0, "k": 1e3, "M": 1e6}[m.group(2)]


def passive_key(kind, pkg, value):
    """('C', '0805', 220e-12) -> 'C0805 220pF', the key as the table spells it."""
    for k in PASSIVES:
        if k.startswith(kind + pkg + " ") and abs(passive_value(k) - value) <= 1e-3 * abs(value):
            return k
    raise KeyError("no %s%s of %g in parts.PASSIVES" % (kind, pkg, value))


def info(key):
    """One record for a PARTS key or a PASSIVES key: footprint, symbol, value, lcsc, mpn, jlc_type, stock, price, desc, match."""
    if key in PARTS:
        d = dict(PARTS[key])
        d.setdefault("match", [])
        return d
    if key in PASSIVES:
        d = dict(PASSIVES[key])
        kind, pkg = key[0], key[1:5]
        d["footprint"] = FOOTPRINT_OF[key[:5]]
        d["symbol"] = SYMBOL_OF[kind]
        val = key.split(" ", 1)[1]
        d["value"] = val
        d["process"] = "SMT"
        d.setdefault("desc", "%s %s" % (val, pkg))
        vtxt = val.replace("R", "Ω") if kind == "R" else val
        if kind == "R":
            vtxt = val[:-1] + "Ω" if val.endswith("R") else val + "Ω"
        d["match"] = [vtxt, pkg]
        return d
    raise KeyError(key)


def all_keys():
    return list(PARTS) + list(PASSIVES)


# JLCPCB places from its own drawing of each part, and some drawings are turned from KiCad's footprint.
# Degrees counter-clockwise to ADD to the KiCad rotation in the upload CPL.  "read": seen in a JLCPCB
# "Confirm Parts Placement" preview on a real order; "predicted": from the land pattern (JLCPCB's own, so
# exact) or a family lesson; every predicted one is listed in PLACEMENT_CHECKS.txt for the order day.
JLC_ROTATION = {
    "C496549": (0, "predicted", "BWSMA-KE-Z001: the footprint IS JLCPCB's drawing (pads renumbered); a square pattern with a centre pin, any quarter turn fits"),
    "C5199800": (0, "predicted", "RH-5019: one pad, the loop along x as JLCPCB draws it"),
    "C40735": (0, "predicted", "DSHP02: JLCPCB's drawing has pin 1 bottom-left as ours (easyeda 2026-10-25)"),
    "C40736": (0, "predicted", "DSHP04: as the DSHP02"),
    "C40737": (180, "predicted", "DSHP06: JLCPCB's drawing has pin 1 top-right, ours bottom-left"),
    "C474881": (0, "predicted", "KF301-2P: pins along x as JLCPCB's drawing"),
    "C474882": (0, "predicted", "KF301-3P: pins along x as JLCPCB's drawing"),
    "C13774": (0, "predicted", "HC-49S SMD crystal: two pads along x as JLCPCB's drawing; symmetric"),
    "C366989": (0, "predicted", "KCR455E: two leads along x; symmetric"),
    "C81598": (0, "predicted", "1N4148W SOD-123: JLCPCB's pad 1 at -x as KiCad's; cathode end to be seen in the preview"),
    "C84256": (0, "read", "NCD0805R1 on KiCad's LED_0805: GPiBridge rev A preview, cathode at pad 1"),
    "C2297": (0, "read", "KT-0805G on KiCad's LED_0805: GPiBridge rev A preview"),
    "C2296": (0, "predicted", "KT-0805Y: the same family drawing as the KT-0805G"),
    "C2293": (0, "predicted", "KT-0805B: the same family drawing as the KT-0805G"),
}


if __name__ == "__main__":
    print("%d parts, %d passives" % (len(PARTS), len(PASSIVES)))
    for k in ("SMA", "R0805 61.9R", "C0805 220pF", "L1210 150uH"):
        print(k, info(k)["footprint"], info(k).get("lcsc"), info(k)["match"])
    print(passive_key("C", "0805", 220e-12))
