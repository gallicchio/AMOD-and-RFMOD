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
    n = max(len(pins_left), len(pins_right))
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
        for i, (num, pname, ptype) in enumerate(pins):
            y = top - 2.54 * (i + 1)
            if side == "L":
                x, rot = -w / 2 - 2.54, 0
            else:
                x, rot = w / 2 + 2.54, 180
            out.append(f'      (pin {ptype} line (at {x:.2f} {y:.2f} {rot}) (length 2.54)')
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
         ("7", "NC", "no_connect"), ("9", "NC", "no_connect"), ("11", "NC", "no_connect"), ("13", "NC", "no_connect")],
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
    # TC32H4 25 MHz TCXO (Taitien, 3.2 x 2.5 mm, 4 pads): 1 EN/NC, 2 GND, 3 OUT, 4 VCC (the 3225 TCXO convention; CostasLink)
    box("TCXO_3225", "X", [("1", "EN", "input"), ("2", "GND", "power_in")], [("4", "VCC", "power_in"), ("3", "OUT", "output")],
        "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", "TCXO, LVCMOS out", width=10.16),
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
