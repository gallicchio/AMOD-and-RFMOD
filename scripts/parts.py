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
    # ---- AMOD-A: power, gating, the chips (stock 2026-10-25 00:45-03:45) ----
    "USBC": dict(value="USB-C 5V", mpn="TYPE-C-31-M-12", lcsc="C165948", jlc_type="extended", process="SMT", stock=324740, price=0.1888,
                 footprint="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", symbol="Connector:USB_C_Receptacle_USB2.0_16P", match=["TYPE-C-31-M-12"],
                 desc="USB-C receptacle, 16 pins, power only (CC pull-downs ask for 5 V); built on three boards, CPL datum known"),
    "PTC2A": dict(value="2A PTC", mpn="MF-MSMF200-2", lcsc="C210837", jlc_type="extended", process="SMT", stock=9923, price=0.0650,
                  footprint="Fuse:Fuse_1812_4532Metric", symbol="Device:Polyfuse", match=["MF-MSMF200-2"], desc="2 A resettable fuse on the USB input"),
    "TVS5V": dict(value="SMAJ5.0A", mpn="SMAJ5.0A", lcsc="C78401", jlc_type="extended", process="SMT", stock=73269, price=0.0537,
                  footprint="Diode_SMD:D_SMA", symbol="Diode:SMAJ5.0A", match=["SMAJ5.0A"], desc="5 V TVS across the input rail (clamps at 9.2 V)"),
    "PFET": dict(value="AO3401A", mpn="AO3401A", lcsc="C15127", jlc_type="basic", process="SMT", stock=643725, price=0.0959,
                 footprint="Package_TO_SOT_SMD:SOT-23", symbol="Transistor_FET:AO3401A", match=["AO3401A"], desc="P-channel MOSFET: each powered tile's +5 V switch (Basic)"),
    "NFET": dict(value="AO3400A", mpn="AO3400A", lcsc="C20917", jlc_type="basic", process="SMT", stock=1214033, price=0.0889,
                 footprint="Package_TO_SOT_SMD:SOT-23", symbol="Transistor_FET:AO3400A", match=["AO3400A"], desc="N-channel MOSFET, 5.7 A: the heater's switch (Basic)"),
    "NFET_S": dict(value="2N7002", mpn="2N7002", lcsc="C8545", jlc_type="basic", process="SMT", stock=2891738, price=0.0161,
                   footprint="Package_TO_SOT_SMD:SOT-23", symbol="Transistor_FET:2N7002", match=["2N7002"], desc="small N-channel MOSFET: the laser gate (Basic)"),
    "SW_SLIDE": dict(value="ON", mpn="MSK12C02", lcsc="C431540", jlc_type="extended", process="SMT", stock=194123, price=0.0529,
                     footprint="amod:SW_SPDT_Shouhan_MSK12C02", symbol="Switch:SW_SPDT", match=["MSK12C02"], desc="slide switch: each powered tile's ON (built on motor-pid)"),
    "LM2664": dict(value="LM2664", mpn="LM2664M6X/NOPB", lcsc="C108573", jlc_type="extended", process="SMT", stock=164185, price=0.3346,
                   footprint="Package_TO_SOT_SMD:SOT-23-6", symbol="amod:LM2664", match=["LM2664"], desc="charge-pump inverter: -5 V at 40 mA for the op-amp tiles"),
    "TPS7A2033": dict(value="TPS7A2033", mpn="TPS7A2033PDBVR", lcsc="C2862740", jlc_type="extended", process="SMT", stock=155681, price=0.2097,
                      footprint="Package_TO_SOT_SMD:SOT-23-5", symbol="Regulator_Linear:TPS7A20xxxDBV", match=["TPS7A2033"], desc="3.3 V 300 mA LDO, 10 uVrms"),
    "OPA2810": dict(value="OPA2810", mpn="OPA2810IDR", lcsc="C1849413", jlc_type="extended", process="SMT", stock=3707, price=2.5350,
                    footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", symbol="Amplifier_Operational:OPA2156xD", match=["OPA2810IDR"],
                    desc="dual FET-input op amp, 140 MHz GBW, 27 V: the gain blocks, the photodiode, the ultrasound receiver (drawn with the OPA2156's symbol: the same pinout)"),
    "OPA810": dict(value="OPA810", mpn="OPA810IDBVR", lcsc="C2833513", jlc_type="extended", process="SMT", stock=2286, price=3.0996,
                   footprint="Package_TO_SOT_SMD:SOT-23-5", symbol="amod:OPA_SOT23-5", match=["OPA810IDBVR"],
                   desc="single FET-input op amp, 140 MHz GBW, 27 V, SOT-23-5: the gain blocks (x10 in one stage: 14 MHz)"),
    "OPA1612": dict(value="OPA1612", mpn="OPA1612AIDR", lcsc="C94590", jlc_type="extended", process="SMT", stock=26345, price=1.3403,
                    footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", symbol="Amplifier_Operational:OPA1612AxD", match=["OPA1612AIDR"],
                    desc="dual op amp, 1.1 nV/rtHz: Johnson noise and the microphone"),
    "LT6230": dict(value="LT6230", mpn="LT6230CS6#TRPBF", lcsc="C580235", jlc_type="extended", process="SMT", stock=440, price=4.0389,
                   footprint="Package_TO_SOT_SMD:SOT-23-6", symbol="amod:OPA_SOT23-6", match=["LT6230CS6"],
                   desc="1.1 nV/rtHz, 215 MHz GBW, unity-gain stable, +-5 V: the Johnson-noise amplifier (TSOT-23-6: OUT 1, V- 2, +IN 3, -IN 4, V+ 5, SHDN 6)"),
    "OPA847": dict(value="OPA847", mpn="OPA847IDR", lcsc="C2870028", jlc_type="extended", process="SMT", stock=1466, price=5.6476,
                   footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", symbol="amod:OPA847_SOIC8", match=["OPA847IDR"],
                   desc="0.85 nV/rtHz, 3.9 GHz GBW, decompensated (gain 12 minimum): the HF LNA at x100"),
    "TLV3501": dict(value="TLV3501", mpn="TLV3501AIDBVR", lcsc="C193413", jlc_type="extended", process="SMT", stock=5079, price=1.9246,
                    footprint="Package_TO_SOT_SMD:SOT-23-6", symbol="Comparator:TLV3501AIDBV", match=["TLV3501AIDBVR"], desc="4.5 ns rail-to-rail comparator: the one-bit ADC"),
    "HC4046": dict(value="CD74HC4046A", mpn="CD74HC4046AM96", lcsc="C6542", jlc_type="extended", process="SMT", stock=959, price=0.9050,
                   footprint="Package_SO:SOIC-16_3.9x9.9mm_P1.27mm", symbol="4xxx:4046", match=["4046"], alt="CD4046BM/TR C7432285 (4,889 in stock; the same pinout, a 1.3 MHz VCO)",
                   desc="PLL: three phase comparators and a VCO (drawn with the 4046 symbol; pin 15 is the HC part's PC3 output)"),
    "MC1496": dict(value="MC1496", mpn="MC1496DR2G", lcsc="C7295", jlc_type="extended", process="SMT", stock=14255, price=0.2492,
                   footprint="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm", symbol="amod:MC1496", match=["MC1496"], desc="balanced modulator: the mixer tile"),
    "TMP235": dict(value="TMP235", mpn="TMP235A4DBZR", lcsc="C2868809", jlc_type="extended", process="SMT", stock=13806, price=0.3243,
                   footprint="Package_TO_SOT_SMD:SOT-23", symbol="amod:TMP235", match=["TMP235"], desc="10 mV/K + 500 mV temperature sensor (the TMP36's replacement)"),
    "DRV8837": dict(value="DRV8837", mpn="DRV8837DSGR", lcsc="C39159", jlc_type="extended", process="SMT", stock=85042, price=0.2622,
                    footprint="Package_SON:Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm", symbol="Driver_Motor:DRV8837", match=["DRV8837"],
                    desc="H-bridge, 1.8 A, PWM inputs: drives the 40 kHz transducer from two Pmod pins"),
    "PAM8302": dict(value="PAM8302A", mpn="PAM8302AASCR", lcsc="C113367", jlc_type="extended", process="SMT", stock=12021, price=0.3089,
                    footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", symbol="amod:PAM8302_SOIC8", match=["PAM8302A"], desc="2.5 W filterless class-D mono amplifier: the speaker"),
    "PD70": dict(value="PD70-01C", mpn="PD70-01C/TR7", lcsc="C131196", jlc_type="extended", process="SMT", stock=77545, price=0.2097,
                 footprint="amod:Photodiode_PD70-01C", symbol="Device:D_Photo", match=["PD70-01C"], desc="PIN photodiode, 7 x 2.6 mm, 940 nm peak (visible too)"),
    "LED_SIDE": dict(value="red side-view", mpn="E6C1204URAC1UDA", lcsc="C375479", jlc_type="extended", process="SMT", stock=12614, price=0.0188,
                     footprint="amod:LED_SideView_3.2x1.0mm_E6C1204", symbol="Device:LED", match=["E6C1204"], desc="side-view red LED at the board's edge: the light source"),
    "MIC": dict(value="electret", mpn="GMI6050-2C38DB", lcsc="C233921", jlc_type="extended", process="SMT", stock=985, price=0.3265,
                footprint="amod:TerminalBlock_KF301_1x02_P5.00mm", symbol="Device:Microphone_Condenser", match=["GMI6050"], in_bom=False,
                desc="(not fitted) the electret is wired into A12's MIC terminal; JLCPCB has no land pattern for the SMD part"),
    "JACK35": dict(value="3.5 mm", mpn="PJ-320A", lcsc="C2884926", jlc_type="extended", process="SMT", stock=9322, price=0.1402,
                   footprint="amod:Jack_3.5mm_PJ-320A", symbol="amod:JACK35", match=["PJ-320A"], desc="3.5 mm stereo jack: the one-bit DAC's audio out"),
    "NTC10K": dict(value="10k NTC", mpn="HNTC0805-103F3380FB", lcsc="C49247661", jlc_type="extended", process="SMT", stock=4464, price=0.0531,
                   footprint="Resistor_SMD:R_0805_2012Metric", symbol="Device:Thermistor_NTC", match=["10kΩ", "0805"], desc="10 k NTC, B 3380: the heater's thermometer"),
    "R2512_15R": dict(value="15R 1W", mpn="25121WF150JT4E", lcsc="C20087", jlc_type="extended", process="SMT", stock=99062, price=0.0375,
                      footprint="Resistor_SMD:R_2512_6332Metric", symbol="Device:R_US", match=["15Ω", "2512"], desc="15 ohm 1 W: the heater (two in series, 0.83 W at 5 V)"),
    "HDR2": dict(value="1x2", mpn="PZ254-1-02-Z-8.5", lcsc="C2894925", jlc_type="extended", process="THT", stock=118004, price=0.0266,
                 footprint="Connector_PinSocket_2.54mm:PinSocket_1x02_P2.54mm_Vertical", symbol="Connector_Generic:Conn_01x02", match=["1x2P", "2.54mm"],
                 desc="1 x 2 socket: a resistor of your own plugs in (A5's noise source)"),
    "HDR5": dict(value="1x5", mpn="PZ254-1-05-Z-8.5", lcsc="C2894928", jlc_type="extended", process="THT", stock=2846, price=0.0588,
                 footprint="Connector_PinSocket_2.54mm:PinSocket_1x05_P2.54mm_Vertical", symbol="Connector_Generic:Conn_01x05", match=["1x5P", "2.54mm"],
                 desc="1 x 5 socket: a 40 kHz transducer plugs into pins 1 and 5 (10.16 mm; its leads are 10.0 apart)"),
    "PMOD": dict(value="Pmod", mpn="PZ254R-12-12P", lcsc="C492434", jlc_type="extended", process="THT", stock=4327, price=0.1036,
                 footprint="amod:PinHeader_2x06_P2.54mm_Horizontal_PZ254R-12-12P", symbol="Connector_Generic:Conn_02x06_Odd_Even", match=["PZ254R-12-12P"],
                 desc="2 x 6 right-angle Pmod plug at the bottom edge: pin k is pad 2k-1, pin k+6 is pad 2k"),
    "BEAD": dict(value="220R bead", mpn="BLM21PG221SN1D", lcsc="C85840", jlc_type="extended", process="SMT", stock=605640, price=0.0346,
                 footprint="Inductor_SMD:L_0805_2012Metric", symbol="Device:FerriteBead", match=["BLM21PG221SN1D"], desc="ferrite bead, 220 ohm at 100 MHz, 2 A"),
    # ---- RF-MOD: the synthesizers, the gain blocks, the filters, the reference and the boost (stock 2026-10-25 08:02) ----
    "MAX2871": dict(value="MAX2871", mpn="MAX2871ETJ+T", lcsc="C7458627", jlc_type="extended", process="SMT", stock=3120, price=9.9745,
                    footprint="Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.1x3.1mm", symbol="amod:MAX2871", match=["MAX2871ETJ"],
                    desc="23.5 MHz to 6 GHz fractional-N synthesizer with its VCOs, TQFN-32 (CostasLink's part and circuit)"),
    "GALI84": dict(value="GALI-84+", mpn="GALI-84+", lcsc="C3193261", jlc_type="extended", process="SMT", stock=144, price=4.2238,
                   footprint="Package_TO_SOT_SMD:SOT-89-3", symbol="amod:GALI84", match=["GALI-84+"],
                   desc="Mini-Circuits MMIC gain block, DC-6 GHz, 20 dB at 1 GHz, P1dB +20 dBm; 5.8 V at 97 mA through a 22 ohm bias resistor from 7.8 V"),
    "TCXO25": dict(value="25 MHz", mpn="TC32H4-25.000-33GNDTNL", lcsc="C5119013", jlc_type="extended", process="SMT", stock=1240, price=1.5760,
                   footprint="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", symbol="amod:TCXO_3225", match=["TC32H4-25.000"],
                   desc="25 MHz TCXO, +-2 ppm, 3.3 V CMOS out, 3.2 x 2.5 mm (CostasLink's reference)"),
    "MT3608": dict(value="MT3608", mpn="MT3608", lcsc="C84817", jlc_type="extended", process="SMT", stock=91453, price=0.0987,
                   footprint="Package_TO_SOT_SMD:SOT-23-6", symbol="Regulator_Switching:MT3608", match=["MT3608"],
                   desc="1.2 MHz boost converter, 2 A switch: +5 V to +7.8 V (12 k / 1 k on FB) for the gain blocks"),
    "SAW915": dict(value="915 MHz SAW", mpn="B39921B2672P810", lcsc="C1518004", jlc_type="extended", process="SMT", stock=6411, price=0.5581,
                   footprint="amod:Filter_SAW_1411-5P_B39921", symbol="amod:SAW915", match=["B39921B2672P810"],
                   desc="915 MHz SAW band-pass, 26 MHz wide, 1.1 dB loss, 1.4 x 1.1 mm (1 IN, 3 OUT, the rest ground)"),
    "LTCC2G4": dict(value="2.45 GHz LTCC", mpn="LFB212G45SG8A127", lcsc="C341536", jlc_type="extended", process="SMT", stock=3940, price=0.1858,
                    footprint="amod:Filter_LTCC_2012_LFB212", symbol="amod:LTCC2G4", match=["LFB212G45SG8A127"],
                    desc="2.4-2.5 GHz LTCC band-pass, 1.7 dB loss, 2.0 x 1.25 mm (4 IN, 2 OUT, 1 and 3 ground)"),
    "LVC1G17": dict(value="74LVC1G17", mpn="SN74LVC1G17DBVR", lcsc="C7836", jlc_type="extended", process="SMT", stock=9560, price=0.1549,
                    footprint="Package_TO_SOT_SMD:SOT-23-5", symbol="74xGxx:74LVC1G17", match=["SN74LVC1G17DBVR"],
                    desc="Schmitt buffer, SOT-23-5: the TCXO's output to the REF OUT jack and the reference bus"),
    "SS34": dict(value="SS34", mpn="SS34", lcsc="C8678", jlc_type="basic", process="SMT", stock=3637362, price=0.0351,
                 footprint="Diode_SMD:D_SMA", symbol="Diode:B340", match=["SS34"], desc="3 A 40 V Schottky, SMA: the boost's rectifier (drawn with the B340's symbol, the same pins)"),
    "L22U": dict(value="22uH", mpn="XRNR4030-22uH/M", lcsc="C5289362", jlc_type="extended", process="SMT", stock=1198, price=0.0385,
                 footprint="amod:L_4x4_XRNR4030", symbol="Device:L", match=["XRNR4030-22uH"], desc="22 uH 1.3 A shielded power inductor, 4 x 4 x 3 mm: the boost"),
    "R2512_22R": dict(value="22R 1W", mpn="25121WJ0220T4E", lcsc="C27258", jlc_type="extended", process="SMT", stock=14728, price=0.0282,
                      footprint="Resistor_SMD:R_2512_6332Metric", symbol="Device:R_US", match=["22Ω", "2512"], desc="the GALI-84+ bias resistor: 0.2 W from 7.8 V"),
    "HDR3": dict(value="1x3", mpn="PZ254V-11-03P", lcsc="C2937625", jlc_type="extended", process="THT", stock=786642, price=0.0199,
                 footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical", symbol="Connector_Generic:Conn_01x03", match=["PZ254V-11-03P"],
                 desc="1 x 3 pin header with a jumper: the synthesizer's reference from its jack (1-2) or the board's TCXO (2-3)"),
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
    "R0805 10R": dict(lcsc="C17415", mpn="0805W8F100JT5E", jlc_type="basic", stock=5956692, price=0.0040),
    "R0805 15R": dict(lcsc="C17480", mpn="0805W8F150JT5E", jlc_type="extended", stock=309405, price=0.0031),
    "R0805 180R": dict(lcsc="C25270", mpn="0805W8F1800T5E", jlc_type="extended", stock=183457, price=0.0031),
    "R0805 5.1k": dict(lcsc="C27834", mpn="0805W8F5101T5E", jlc_type="basic", stock=1700000, price=0.0036),
    "R0805 1M": dict(lcsc="C17514", mpn="0805W8F1004T5E", jlc_type="basic", stock=1300000, price=0.0038),
    "R0805 22R": dict(lcsc="C17561", mpn="0805W8F220JT5E", jlc_type="basic", stock=900000, price=0.0038),
    "R0805 33R": dict(lcsc="C17634", mpn="0805W8F330JT5E", jlc_type="basic", stock=600000, price=0.0040),
    "R0805 150R": dict(lcsc="C17471", mpn="0805W8F1500T5E", jlc_type="basic", stock=1400000, price=0.0040),
    "R0805 200R": dict(lcsc="C17540", mpn="0805W8F2000T5E", jlc_type="basic", stock=900000, price=0.0040),
    "R0805 300R": dict(lcsc="C17617", mpn="0805W8F3000T5E", jlc_type="basic", stock=700000, price=0.0040),
    "R0805 330R": dict(lcsc="C17630", mpn="0805W8F3300T5E", jlc_type="basic", stock=1600000, price=0.0040),
    "R0805 510R": dict(lcsc="C17734", mpn="0805W8F5100T5E", jlc_type="basic", stock=2370341, price=0.0039),
    "R0805 820R": dict(lcsc="C17837", mpn="0805W8F8200T5E", jlc_type="extended", stock=130982, price=0.0031),
    "R0805 1.5k": dict(lcsc="C4310", mpn="0805W8F1501T5E", jlc_type="basic", stock=1400000, price=0.0038),
    "R0805 2k": dict(lcsc="C17604", mpn="0805W8F2001T5E", jlc_type="basic", stock=800000, price=0.0040),
    "R0805 3.3k": dict(lcsc="C26010", mpn="0805W8F3301T5E", jlc_type="basic", stock=1300000, price=0.0038),
    "R0805 3.9k": dict(lcsc="C17614", mpn="0805W8F3901T5E", jlc_type="basic", stock=351414, price=0.0030),
    "R0805 6.8k": dict(lcsc="C17772", mpn="0805W8F6801T5E", jlc_type="basic", stock=600000, price=0.0040),
    "R0805 20k": dict(lcsc="C4328", mpn="0805W8F2002T5E", jlc_type="basic", stock=1400000, price=0.0035),
    "R0805 22k": dict(lcsc="C17560", mpn="0805W8F2202T5E", jlc_type="basic", stock=1100000, price=0.0035),
    "R0805 33k": dict(lcsc="C17633", mpn="0805W8F3302T5E", jlc_type="basic", stock=500000, price=0.0040),
    "R0805 47k": dict(lcsc="C17713", mpn="0805W8F4702T5E", jlc_type="basic", stock=1473834, price=0.0068),
    "R0805 1.1k": dict(lcsc="C17375", mpn="0805W8F1101T5E", jlc_type="extended", stock=21239, price=0.0038),
    "R0805 11k": dict(lcsc="C17429", mpn="0805W8F1102T5E", jlc_type="extended", stock=88120, price=0.0038),
    "R0805 24.9k": dict(lcsc="C17571", mpn="0805W8F2492T5E", jlc_type="extended", stock=75894, price=0.0025),
    "R0805 2.49k": dict(lcsc="C21237", mpn="0805W8F2491T5E", jlc_type="extended", stock=17446, price=0.0045),
    "R0805 1.2k": dict(lcsc="C17379", mpn="0805W8F1201T5E", jlc_type="basic", stock=600000, price=0.0040),
    "R0805 4.99k": dict(lcsc="C17677", mpn="0805W8F4991T5E", jlc_type="extended", stock=166588, price=0.0033),
    "R0805 0R": dict(lcsc="C17477", mpn="0805W8F0000T5E", jlc_type="basic", stock=3000000, price=0.0035),
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
    "C0805 4.7nF": dict(lcsc="C50131", mpn="CL21B472KBANNNC", jlc_type="extended", stock=44652, price=0.0136, note="X7R"),
    "C0805 22nF": dict(lcsc="C1729", mpn="CL21B223KBANNNC", jlc_type="basic", stock=477331, price=0.0084, note="X7R"),
    "C0805 4.7uF": dict(lcsc="C1779", mpn="CL21A475KAQNNNE", jlc_type="basic", stock=2033617, price=0.0343, note="X5R 25 V"),
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
    "R0603 1.1k": dict(lcsc="C22764", mpn="0603WAF1101T5E", jlc_type="extended", stock=234930, price=0.0018),
    "R0603 1k": dict(lcsc="C21190", mpn="0603WAF1001T5E", jlc_type="basic", stock=35103609, price=0.0017),
    "R0603 10R": dict(lcsc="C22859", mpn="0603WAF100JT5E", jlc_type="basic", stock=6896653, price=0.0032),
    "R0402 10k": dict(lcsc="C25744", mpn="0402WGF1002TCE", jlc_type="basic", stock=17894795, price=0.0011),
    "R0402 1k": dict(lcsc="C11702", mpn="0402WGF1001TCE", jlc_type="basic", stock=19375230, price=0.0013),
    "R0402 470R": dict(lcsc="C25117", mpn="0402WGF4700TCE", jlc_type="basic", stock=1060806, price=0.0012),
    "C0402 100nF": dict(lcsc="C1525", mpn="CL05B104KO5NNNC", jlc_type="basic", stock=35681170, price=0.0035),
    "C0402 1nF": dict(lcsc="C1523", mpn="0402B102K500NT", jlc_type="basic", stock=2782063, price=0.0038),
    "C0603 1uF": dict(lcsc="C15849", mpn="CL10A105KB8NNNC", jlc_type="basic", stock=13736422, price=0.0146, note="X5R 50 V"),
    "R0402 51R": dict(lcsc="C25125", mpn="0402WGF510JTCE", jlc_type="extended", stock=1180377, price=0.0012),
    "R0402 1.5k": dict(lcsc="C25867", mpn="0402WGF1501TCE", jlc_type="basic", stock=1667102, price=0.0029),
    "R0402 3.9k": dict(lcsc="C51721", mpn="0402WGF3901TCE", jlc_type="extended", stock=379616, price=0.0012),
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
    # --- RF-MOD (stock 2026-10-25 08:02): 0402 for the synthesizer, C0G in every signal path ---
    "C0402 100pF": dict(lcsc="C1546", mpn="0402CG101J500NT", jlc_type="basic", stock=3331448, price=0.0033, note="C0G: the RF blocks and the loop filter's C3"),
    "C0402 1uF": dict(lcsc="C14445", mpn="CL05A105KP5NNNC", jlc_type="extended", stock=1049930, price=0.0053, note="X5R 10 V: the MAX2871's filter pins"),
    "L0402 27nH": dict(lcsc="C882469", mpn="LQW15AN27NG80D", jlc_type="extended", stock=18979, price=0.0902, note="Murata LQW15, SRF 3.4 GHz min: the RF chokes"),
    "R0402 12k": dict(lcsc="C25752", mpn="0402WGF1202TCE", jlc_type="basic", stock=887758, price=0.0018),
    "R0402 820R": dict(lcsc="C25135", mpn="0402WGF8200TCE", jlc_type="extended", stock=98870, price=0.0019),
    "R0402 2k": dict(lcsc="C4109", mpn="0402WGF2001TCE", jlc_type="basic", stock=7184892, price=0.0026),
    "R0402 5.1k": dict(lcsc="C25905", mpn="0402WGF5101TCE", jlc_type="basic", stock=4223875, price=0.0023),
    "R0402 100k": dict(lcsc="C25741", mpn="0402WGF1003TCE", jlc_type="basic", stock=7850595, price=0.0015),
}

FOOTPRINT_OF = {"R0805": "Resistor_SMD:R_0805_2012Metric", "R0603": "Resistor_SMD:R_0603_1608Metric", "R0402": "Resistor_SMD:R_0402_1005Metric", "R1206": "Resistor_SMD:R_1206_3216Metric",
                "R2512": "Resistor_SMD:R_2512_6332Metric", "C0805": "Capacitor_SMD:C_0805_2012Metric", "C0603": "Capacitor_SMD:C_0603_1608Metric", "C0402": "Capacitor_SMD:C_0402_1005Metric",
                "C1206": "Capacitor_SMD:C_1206_3216Metric", "L0805": "Inductor_SMD:L_0805_2012Metric", "L0603": "Inductor_SMD:L_0603_1608Metric",
                "L1210": "Inductor_SMD:L_1210_3225Metric", "L0402": "Inductor_SMD:L_0402_1005Metric"}
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
    "C3193261": (180, "predicted", "GALI-84+ on KiCad's SOT-89-3: JLCPCB's drawing has pins 1 and 3 at +x, KiCad's at -x"),
    "C5119013": (180, "predicted", "TC32H4 on KiCad's Crystal_SMD_3225: JLCPCB's pad 1 is top-left (y up), KiCad's bottom-left"),
    "C5289362": (0, "predicted", "XRNR4030: the footprint IS JLCPCB's drawing (two pads along x); symmetric"),
    "C7458627": (0, "predicted", "MAX2871 TQFN-32: JLCPCB's QFN drawings put pin 1 top-left as KiCad's; confirm the dot in the preview"),
}


if __name__ == "__main__":
    print("%d parts, %d passives" % (len(PARTS), len(PASSIVES)))
    for k in ("SMA", "R0805 61.9R", "C0805 220pF", "L1210 150uH"):
        print(k, info(k)["footprint"], info(k).get("lcsc"), info(k)["match"])
    print(passive_key("C", "0805", 220e-12))
