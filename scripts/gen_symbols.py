#!/usr/bin/env python3
"""The project symbol library, hardware/lib/amod.kicad_sym: box symbols for the chips KiCad's libraries lack.

Each symbol is a rectangle with its pins on the left and right at 2.54 mm, named from the datasheet (the pin
tables are quoted in the comments with the datasheet's page).  gen_sch registers the library as "amod:" so a
part's symbol can be "amod:MC1496".
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "hardware", "lib", "amod.kicad_sym")


def _esc(s):
    return s.replace('"', '\\"')


def box(name, ref, pins_left, pins_right, footprint="", desc="", width=None):
    """pins_left / pins_right: [(number, name, type)] top to bottom; type: input, output, power_in, power_out,
    passive, bidirectional, open_collector, no_connect."""
    n = max(sum(1 for p in pins_left if len(p) < 4), sum(1 for p in pins_right if len(p) < 4))
    h = (n + 1) * 2.54
    w = width or 12.7
    top = h / 2
    out = []
    out.append(f'  (symbol "{name}" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)')
    out.append(f'    (property "Reference" "{ref}" (at {-w/2:.2f} {top + 1.27:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))')
    out.append(f'    (property "Value" "{name}" (at {-w/2:.2f} {-top - 1.27:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))')
    out.append(f'    (property "Footprint" "{_esc(footprint)}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    out.append(f'    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    out.append(f'    (property "Description" "{_esc(desc)}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    out.append(f'    (symbol "{name}_0_1"')
    out.append(f'      (rectangle (start {-w/2:.2f} {top:.2f}) (end {w/2:.2f} {-top:.2f}) (stroke (width 0.254) (type default)) (fill (type background)))')
    out.append('    )')
    out.append(f'    (symbol "{name}_1_1"')
    for side, pins in (("L", pins_left), ("R", pins_right)):
        i = 0
        for pin in pins:
            num, pname, ptype = pin[:3]
            stacked = len(pin) > 3 and pin[3] == "stack"          # on the previous pin of this side, hidden (one net)
            if not stacked:
                i += 1
            y = top - 2.54 * i
            if side == "L":
                x, rot = -w / 2 - 2.54, 0
            else:
                x, rot = w / 2 + 2.54, 180
            out.append(f'      (pin {ptype} line (at {x:.2f} {y:.2f} {rot}) (length 2.54)' + (' (hide yes)' if stacked else ''))
            out.append(f'        (name "{_esc(pname)}" (effects (font (size 1.27 1.27))))')
            out.append(f'        (number "{num}" (effects (font (size 1.27 1.27)))))')
    out.append('    )')
    out.append('  )')
    return "\n".join(out)


SYMBOLS = [
    # MC1496 (onsemi MC1496DR2G, SOIC-14; datasheet page 1 "pin connections"): 1 SIG+, 2 GAIN, 3 GAIN, 4 SIG-, 5 BIAS, 6 OUT+,
    # 8 CARRIER-IN, 10 CARRIER+IN, 12 OUT-, 14 VEE; 7, 9, 11, 13 NC
    box("MC1496", "U", [("1", "SIG+", "input"), ("4", "SIG-", "input"), ("8", "CAR+", "input"), ("10", "CAR-", "input"),
                        ("2", "GAIN", "passive"), ("3", "GAIN", "passive"), ("5", "BIAS", "passive")],
        [("6", "OUT+", "output"), ("12", "OUT-", "output"), ("14", "VEE", "power_in"),
         ("7", "NC", "passive"), ("9", "NC", "passive"), ("11", "NC", "passive"), ("13", "NC", "passive")],
        "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm", "balanced modulator / demodulator (Gilbert cell)"),
    # TMP235 (TI TMP235A4DBZR, SOT-23-3; datasheet pin functions): 1 VDD, 2 VOUT, 3 GND
    box("TMP235", "U", [("1", "VDD", "power_in"), ("3", "GND", "power_in")], [("2", "VOUT", "output")],
        "Package_TO_SOT_SMD:SOT-23", "analog temperature sensor, 10 mV/K + 500 mV", width=10.16),
    # LM2664 (TI LM2664M6X, SOT-23-6; datasheet section 5): 1 GND, 2 OUT, 3 CAP-, 4 SD, 5 V+, 6 CAP+
    box("LM2664", "U", [("5", "V+", "power_in"), ("4", "SD", "input"), ("6", "CAP+", "passive"), ("3", "CAP-", "passive")],
        [("2", "OUT", "power_out"), ("1", "GND", "power_in")],
        "Package_TO_SOT_SMD:SOT-23-6", "switched-capacitor voltage inverter, 40 mA"),
    # OPA810IDBVR (TI, SOT-23-5; the standard single op amp pinout): 1 OUT, 2 V-, 3 +IN, 4 -IN, 5 V+
    box("OPA_SOT23-5", "U", [("3", "+IN", "input"), ("4", "-IN", "input"), ("2", "V-", "power_in")], [("5", "V+", "power_in"), ("1", "OUT", "output")],
        "Package_TO_SOT_SMD:SOT-23-5", "single op amp, SOT-23-5 (OUT 1, V- 2, +IN 3, -IN 4, V+ 5)", width=10.16),
    # OPA847IDR (TI, SOIC-8): 1 NC, 2 -IN, 3 +IN, 4 -VS, 5 NC, 6 OUT, 7 +VS, 8 DIS (open = enabled); the two NC pins are
    # drawn as passive pins so a board may run a track through them (A4 carries its feedback node through pin 1)
    box("OPA847_SOIC8", "U", [("1", "NC", "passive"), ("2", "-IN", "input"), ("3", "+IN", "input"), ("4", "-VS", "power_in")],
        [("8", "DIS", "input"), ("7", "+VS", "power_in"), ("6", "OUT", "output"), ("5", "NC", "passive")],
        "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "OPA847 wideband low-noise op amp, SOIC-8", width=10.16),
    # OPA847IDBVR (TI, SOT-23-6, the DBV pin configuration): 1 OUT, 2 -VS, 3 +IN, 4 -IN, 5 DIS (high or open: enabled), 6 +VS
    box("OPA847_SOT23-6", "U", [("3", "+IN", "input"), ("4", "-IN", "input"), ("2", "-VS", "power_in")],
        [("6", "+VS", "power_in"), ("5", "DIS", "input"), ("1", "OUT", "output")],
        "Package_TO_SOT_SMD:SOT-23-6", "OPA847 wideband low-noise op amp, SOT-23-6 (OUT 1, -VS 2, +IN 3, -IN 4, DIS 5, +VS 6)", width=10.16),
    # LT6230CS6 (ADI, TSOT-23-6): the SOT-23-5 op amp pinout plus SHDN-bar on pin 6 (tie to V+ to run)
    box("OPA_SOT23-6", "U", [("3", "+IN", "input"), ("4", "-IN", "input"), ("2", "V-", "power_in")],
        [("5", "V+", "power_in"), ("6", "~{SHDN}", "input"), ("1", "OUT", "output")],
        "Package_TO_SOT_SMD:SOT-23-6", "single op amp with shutdown, SOT-23-6 (OUT 1, V- 2, +IN 3, -IN 4, V+ 5, SHDN 6)", width=10.16),
    # PJ-320A 3.5 mm jack as JLCPCB numbers its pads: 2 sleeve, 3 ring 2, 4 ring 1, 5 tip
    box("JACK35", "J", [("2", "S", "passive"), ("3", "R2", "passive")], [("5", "T", "passive"), ("4", "R1", "passive")],
        "amod:Jack_3.5mm_PJ-320A", "3.5 mm 4-pole jack, PJ-320A", width=7.62),
    # PAM8302AASCR (Diodes, SOIC-8; datasheet pin descriptions): 1 SD, 2 BYP, 3 IN+, 4 IN-, 5 VO+, 6 VDD, 7 GND, 8 VO-
    box("PAM8302_SOIC8", "U", [("3", "IN+", "input"), ("4", "IN-", "input"), ("1", "SD", "input"), ("2", "BYP", "passive"), ("7", "GND", "power_in")],
        [("6", "VDD", "power_in"), ("5", "VO+", "output"), ("8", "VO-", "output")],
        "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "PAM8302A 2.5 W filterless class-D amplifier, SOIC-8", width=10.16),
    # TC32H4 25 MHz TCXO (Taitien, 3.2 x 2.5 mm, 4 pads): 1 EN/NC, 2 GND, 3 OUT, 4 VCC (the 3225 TCXO convention; CostasLink)
    box("TCXO_3225", "X", [("1", "EN", "input"), ("2", "GND", "power_in")], [("4", "VCC", "power_in"), ("3", "OUT", "output")],
        "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", "TCXO, LVCMOS out", width=10.16),
    # MAX2871 (ADI, TQFN-32 5 x 5; datasheet "Pin Description", the table CostasLink's gen/symbols.py quotes): the reference,
    # the SPI and the loop filter on the left; the supplies, the four open-collector RF outputs and the grounds on the right
    box("MAX2871", "U", [("29", "REF_IN", "input"), ("1", "CLK", "input"), ("2", "DATA", "input"), ("3", "LE", "input"), ("4", "CE", "input"),
                         ("26", "RFOUT_EN", "input"), ("30", "MUX", "output"), ("25", "LD", "output"), ("7", "CP_OUT", "output"), ("20", "TUNE", "input"),
                         ("22", "RSET", "passive"), ("5", "SW", "passive"), ("19", "NOISE_FILT", "passive"), ("23", "BIAS_FILT", "passive"), ("24", "REG", "passive")],
        [("6", "VCC_CP", "power_in"), ("10", "VCC_PLL", "power_in"), ("28", "VCC_DIG", "power_in"), ("32", "VCC_SD", "power_in"), ("17", "VCC_VCO", "power_in"),
         ("16", "VCC_RF", "power_in"), ("12", "RFOUTA+", "output"), ("13", "RFOUTA-", "output"), ("14", "RFOUTB+", "output"), ("15", "RFOUTB-", "output"),
         ("8", "GND", "power_in"), ("9", "GND", "power_in"), ("27", "GND", "power_in"), ("31", "GND", "power_in"), ("21", "GND", "power_in"),
         ("18", "GND", "power_in"), ("11", "GND", "power_in"), ("33", "EP", "power_in")],
        "Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.1x3.1mm", "MAX2871 23.5 MHz to 6 GHz fractional-N synthesizer with VCOs, TQFN-32", width=17.78),
    # GALI-84+ (Mini-Circuits, SOT-89): 1 RF IN, 2 GND (the tab), 3 RF OUT and DC in
    box("GALI84", "U", [("1", "IN", "input")], [("3", "OUT", "output"), ("2", "GND", "power_in")],
        "Package_TO_SOT_SMD:SOT-89-3", "Mini-Circuits GALI-84+ MMIC amplifier, SOT-89 (1 IN, 2 GND, 3 OUT + DC)", width=10.16),
    # B39921B2672P810 915 MHz SAW (RF360, 1.4 x 1.1, 5 pads): 1 IN, 3 OUT, 2 / 4 / 5 ground
    box("SAW915", "FL", [("1", "IN", "passive"), ("2", "GND", "power_in"), ("5", "GND", "power_in")], [("3", "OUT", "passive"), ("4", "GND", "power_in")],
        "amod:Filter_SAW_1411-5P_B39921", "915 MHz SAW band-pass filter, 1.4 x 1.1 mm", width=10.16),
    # ADL5350 (ADI, LFCSP-8 2 x 3; datasheet Table 6): 1 and 8 RF/IF (tied inside), 2 and 5 GND, 3 LOIN, 4 and 7 NC (ground them), paddle 9
    box("ADL5350", "U", [("1", "RF/IF", "passive"), ("8", "RF/IF", "passive"), ("3", "LOIN", "input")],
        [("6", "VPOS", "power_in"), ("2", "GND", "power_in"), ("5", "GND", "power_in"), ("4", "NC", "passive"), ("7", "NC", "passive"), ("9", "EP", "power_in")],
        "amod:LFCSP-8_2x3mm_P0.5mm_ADL5350", "ADL5350 LF to 4 GHz passive mixer with LO buffer, LFCSP-8", width=10.16),
    # QPL9547 (Qorvo, DFN-8 2 x 2; datasheet pad table): 1 Vbias, 2 RF In, 6 Shut Down (low = on), 7 RF Out and VDD, 3 4 5 8 NC, 9 paddle
    box("QPL9547", "U", [("2", "RF_IN", "input"), ("1", "VBIAS", "passive"), ("6", "SD", "input")],
        [("7", "RF_OUT", "output"), ("3", "NC", "passive"), ("4", "NC", "passive"), ("5", "NC", "passive"), ("8", "NC", "passive"), ("9", "GND", "power_in")],
        "Package_DFN_QFN:DFN-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm", "QPL9547 0.1-6 GHz LNA, DFN-8 2 x 2", width=10.16),
    # TRF3722 (TI, VQFN-48 7 x 7; datasheet section 5 "Pin Functions"): baseband, reference, serial port and loop on the left;
    # the supplies, the outputs and the grounds on the right
    box("TRF3722", "U", [("27", "BBI_P", "input"), ("29", "BBI_N", "input"), ("10", "BBQ_P", "input"), ("8", "BBQ_N", "input"), ("44", "REFIN", "input"),
                         ("48", "CLK", "input"), ("47", "DATA", "input"), ("46", "LE", "input"), ("1", "PD", "input"), ("31", "EXT_VCO", "passive"),
                         ("41", "CP_OUT", "output"), ("34", "VTUNE", "input"), ("2", "RDBK", "output"), ("3", "LD", "output"),
                         ("18", "RFOUT", "output"), ("39", "LO_OUTP", "output"), ("38", "LO_OUTN", "output")],
        [("4", "VCC_DIG", "power_in"), ("6", "VCC_LO1", "power_in"), ("14", "VCC_MOD1", "power_in"), ("16", "VCC_MOD2", "power_in"),
         ("21", "VCC_MOD3", "power_in"), ("23", "VCC_MOD4", "power_in"), ("42", "VCC_PLL", "power_in"), ("33", "VCC_VCO", "power_in"),
         ("35", "VCC_LO2", "power_in"), ("32", "VCC_TK", "power_in"), ("5", "GND", "power_in")]
        + [(n, "GND", "power_in", "stack") for n in ("7", "11", "15", "17", "19", "20", "22", "26", "30", "37", "40", "43", "45", "49")]
        + [("9", "NC", "passive"), ("12", "NC", "passive"), ("13", "NC", "passive"), ("24", "NC", "passive"), ("25", "NC", "passive"),
           ("28", "NC", "passive")] + [("36", "NC", "passive")],
        "Package_DFN_QFN:Texas_RGZ0048A_VQFN-48-1EP_7x7mm_P0.5mm_EP5.15x5.15mm", "TRF3722 I/Q modulator with PLL and VCO, 400-4200 MHz, VQFN-48", width=17.78),
    # LFB212G45SG8A127 2.45 GHz LTCC (Murata, 2.0 x 1.25, 4 pads): 4 IN, 2 OUT, 1 / 3 ground (JLCPCB's numbering)
    box("LTCC2G4", "FL", [("4", "IN", "passive"), ("1", "GND", "power_in")], [("2", "OUT", "passive"), ("3", "GND", "power_in")],
        "amod:Filter_LTCC_2012_LFB212", "2.4-2.5 GHz LTCC band-pass filter, 2.0 x 1.25 mm", width=10.16),
]

def main():
    text = ['(kicad_symbol_lib (version 20241209) (generator "amod_gen_symbols") (generator_version "10.0")']
    for s in SYMBOLS:
        text.append(s)
    text.append(")")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        fh.write("\n".join(text) + "\n")
    print("  wrote %s (%d symbols)" % (os.path.relpath(OUT), len(SYMBOLS)))


if __name__ == "__main__":
    main()
