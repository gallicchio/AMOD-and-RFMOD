# AMOD-M: what could make it dead on arrival, and what to check before paying

Rev A, 2026-10-28 (Prompt 19).  Every item is a fact the design assumed that a datasheet, JLCPCB's placement preview or
the first bench test must confirm.  The ones under **Order gate** must be confirmed before the order is placed.
`scripts/check_rotations.py` fits JLCPCB's own drawing of every part onto its footprint: on 2026-10-28 it agreed with
the rotation table on all 64 of AMOD-M's codes once the board's new codes and three origin offsets were added.
`scripts/check_pinouts.py` compares each symbol's pin names with EasyEDA's for the same code: on this board every
difference is a naming one (KiCad's op amps' "+" and "-" against EasyEDA's IN+ and IN-, the TCA0372's "InputsB-"),
and each was read against the maker's pin table.

## Order gate: pins, packages and polarity

1. **SOIC-8 and SOIC-16W at +270** (pins in rows on JLCPCB's drawings): the OPA2171 (m3), INA828 (m11), TPS28225 (m8)
   and the TCA0372 (m7, SOIC-16W).  A half turn on any of them puts a supply on a signal pin.  The DRV8251A's HSOP-8
   (m3, m4) fits at 0: JLCPCB draws it as KiCad does (rms 0.05 mm); in the preview its exposed pad sits under the body
   and pin 1 (IPROPI) at the corner the board's dot marks.
2. **SOT-23 family**: +180 for the AO3401A switches, the AO3400A pair (m8), the DRV5055A3 (m9), the TLV3501 (m5, m6,
   m8), the TPS7A2033 and LM2664; 0 for the OPA810 and, unlike the other SOT-23-6 parts, the INA181A1 (rms 0.01 mm).
3. **NCE6020AK (m6), TO-252**: CPL 0 with JLCPCB's origin 1.8 mm toward the leads (JLC_DATUM).  In the preview the tab
   lies to the right in m6's left cell, gate and source to the left.  Pin 2 (the tab) is the drain.
4. **The JST connectors**: the B4B-XH-A (m4's stepper, m11's load cell) and the B6B-PH-K (m3's motor) at +180 with
   JLCPCB's origin at the middle of the row (JLC_DATUM).  Through-hole: JLCPCB solders them.  m4's XH: 1 A+, 2 A-,
   3 B+, 4 B-, each driver's OUT2 on its coil's + pin; m11's: 1 E+ red, 2 E- black, 3 S- white, 4 S+ green; m3's PH:
   1 M1, 2 GND, 3 A, 4 B, 5 3.3 V, 6 M2.
5. **DC-005 barrel jack (m2)**: drawn from JLCPCB's land pattern (three slotted pads, 1.0 x 3.5 mm): check the slots
   in the drill file and that pin 1 is the centre pin (VEXT), 2 the sleeve and 3 the switch (both on ground).
6. **QRE1113GR (m10)** on KiCad's OnSemi_CASE100CY: +270.  Pin 1 the LED's anode, 2 its cathode (ground), 3 the
   collector, 4 the emitter (to -5 V through 100 ohm).  The sensor faces up.
7. **The Pmod plug (m3's margin)**: `check_pmod` maps every pad to the Pmod standard; IO1 m3's IN2, IO2-IO4 and IO8
   m4's inputs, IO5 and IO6 m3's encoder, IO7 m3's IN1.  Pins 6 and 12 (the host's 3.3 V) join only each other.
8. **TCA0372 (m7)**: 1 VCC, 2 OUT B, 7 -IN B, 8 +IN B, 9 +IN A, 10 -IN A, 16 OUT A, 4 5 12 13 VEE/GND (onsemi's case
   751G drawing), 3 6 11 14 15 NC.  The ground pins are the heat path: one copper strip under the body with three vias.
9. **TPS28225 (m8)**: 1 UGATE, 2 BOOT, 3 PWM, 4 GND, 5 LGATE, 6 VDD, 7 EN/PG, 8 PHASE (TI's Terminal Functions).  EN/PG
   through 100 k from the tile's switch (it is also an output that the chip pulls low in undervoltage).
10. **The jumper on m6's 1 x 3 header** is not on JLCPCB's list: the kit's jumper cap goes on by hand (no soldering).

## Bench, first power

11. USB-C alone: m1's LEDs; +5 V, -5 V, +3.3 V on its socket; m2's LED lit from the USB through its Schottky, VM about
    4.6 / 16 = 0.29 V.  The -5 V rail's load is about 15 mA (the OPA2171, three OPA810s, the INA828, m10's sensor).
12. The barrel jack at 12 V: VM 0.73 V; the SMBJ16A must not conduct below about 18 V.
13. m3 on USB alone: the DRV8251A's lockout is 4.15-4.45 V and VMOT is about 4.6 V less the motor's surge, so a stalled
    motor may trip it; the barrel jack ends that.  IPROPI: 0.98 V/A at I; V: (M1 - M2) / 13.
14. m4 at 1 A per coil (VREF 1.0 V): the drivers warm with both coils held; IA and IB read 0.98 V/A.
15. m5: a 1.5 ms pulse every 20 ms centres a servo; its stall current on I (1 V/A) stays under about 0.7 A from USB.
16. m6 with each flyback: the diode (slow decay, drain at VMOT + 0.4 V), the TVS (drain near 30 V), none (the FET's
    avalanche near 70 V).  Check the solenoid's energy, 1/2 L I^2, against the NCE6020AK's single-pulse avalanche rating
    before running the third.
17. m7: with IN at 0 both outputs sit at VMOT / 2 and the load sees a few tens of millivolts; at 12 V into 8 ohm the
    chip dissipates up to 4.5 W and stops on its thermal shutdown: use 30 ohm or more there.  I at 0 A reads within about
    10 mA of 0.
18. m8: a 200 kHz square wave on PWM (0 / +1 V), VMOT 12 V: VO = duty x 12 V; the inductor ripple about 0.3 A peak to
    peak on I; switch the tile off and the driver's EN goes low (both FETs off).
19. m9, m10, m11: OUT near 0 with nothing near the sensor, no load or no cell.

## What is new and untried on these boards

- The motor rail on the back, 1.6 mm, every motor tile tapping it by a via; the board's only fuse is the supply's limit.
- m6's flyback by jumper and its avalanche demonstration; m7's DC-coupled bridge from VMOT with its offset set by one
  chain of resistors; m8's discrete buck stage with a gate driver from a DAC's PWM.
