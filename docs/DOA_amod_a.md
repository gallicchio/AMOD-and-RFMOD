# AMOD-A: what could make it dead on arrival, and what to check before paying

Rev A, 2026-10-25.  Every item is a fact the design assumed that a datasheet, JLCPCB's placement preview or the
first bench test must confirm.  The ones marked **order gate** must be confirmed before the order is placed.

## Order gate: pin and polarity assumptions

1. **PD70-01C photodiode (A10, D1001).** The footprint puts the cathode on pad 1 at x = -3.6 (KiCad's convention);
   the tile wires pad 1 to VS and pad 2 to the amplifier's -IN.  JLCPCB's drawing and the datasheet's marking must
   agree.  Reversed, the diode conducts and PD OUT sits at the rail: not fatal, but the tile does nothing.
2. **E6C1204 side-view LED (A10, LED1001).** Pad 1 is taken as the cathode (Device:LED pin 1 = K) and the light
   leaves along the footprint's -y, which rot 270 points at the board's right edge.  Check the orientation in the
   placement preview and the cathode mark in JLCPCB's drawing.  Reversed, no light.
3. **LT6230 (A5, U501).** TSOT-23-6, taken as OUT 1, V- 2, +IN 3, -IN 4, V+ 5, SHDN-bar 6 with SHDN-bar tied to V+.
   Confirm the pin order on the datasheet's package drawing; a swap of 5 and 6 would still run (both are at V+),
   a different order would not.
4. **TLV3501 (A6, U601).** SOT-23-6, taken as -IN 1, V- 2, +IN 3, V+ 4, OUT 5, SHDN 6 with SHDN grounded (active
   high).  Confirm.
5. **PAM8302A (A12, U1201).** SOIC-8, taken as SD 1, BYP 2, IN+ 3, IN- 4, VO+ 5, VDD 6, GND 7, VO- 8 (the board's
   own box symbol).  SD is tied to VS (on when the tile is on).  Confirm SD's polarity (active low shutdown).
6. **DRV8837 (A11, U1101).** WSON-8 with the thermal pad on ground; pins taken as VM 1, OUT1 2, OUT2 3, GND 4,
   IN2 5, IN1 6, nSLEEP 7, VCC 8, nSLEEP tied to VS.  Confirm against the DSG package drawing (pin 1 at the dot).
7. **MC1496 (A9, U901).** SOIC-14 as the datasheet's "pin connections": SIG+ 1, GAIN 2 and 3, SIG- 4, BIAS 5,
   OUT+ 6, CAR+ 8, CAR- 10, OUT- 12, VEE 14; pins 7, 9, 11, 13 no connection.  Pin 7 carries the output wire past
   the chip: that is only safe if pin 7 is truly unconnected inside the package (the datasheet says so).
8. **OPA847 (A4, U401).** Pin 1 carries the feedback node; the datasheet lists pins 1 and 5 as NC.  Confirm the
   DIS pin's sense (8, pulled to +VS here: enabled).
9. **CD74HC4046A (A7, U701).** The order code was changed on the day to CD74HC4046AM96 (C6542, 959 in stock); the
   same die and pinout as the AM part.  Pin 15 is PC3out on the HC part (unused).
10. **The MSK12C02 slide switch** (every powered tile): pad 1 is taken as the contact made with the slider UP
    (toward the jacks), pad 2 the common, pad 3 the other end.  The tile grounds pad 1 (on) and puts the rail on
    pad 3 (off); if the switch is mirrored the labels are wrong but nothing is damaged (the FET is either on or
    off).  Check the "ON" marking in the preview.
11. **The HRO TYPE-C-31-M-12 footprint** (A1): both CC pins have 5.1 k; the SMD ground pads A1/B1 reach the shell
    holes with a short wire each (the plane carries them).  Check the connector's overhang (1.2 mm past the edge)
    in the preview.

## Order gate: the rails

12. The -5 V rail is one polygon on L3 (In2) through the gutters under rows 0 and 2 and down the left margin; its
    end in the right margin stops at x 93.6 so the +5 V pour keeps a path down that margin.  Every tile's -5 V via
    lands in a gutter strip; `check_outputs` found the net connected, and KiCad's DRC found no island.
13. The +3.3 V rail is the strip in the gutter under row 1; only A6 draws from it, through the header via at the
    tile's bottom edge.
14. A1's LM2664 gives 40 mA of -5 V.  The op-amp tiles draw about 4 mA each at rest (OPA810), the LT6230 3.5 mA,
    the MC1496 2 mA, the class-D nothing from -5 V: all twelve tiles on at once stay under 40 mA.  The USB-C
    source must give 1.5 A for the heater (170 mA), the LED drive (45 mA) and the class-D at full volume.

## Bench, first power

15. With every tile off, the green LED lights and the socket shows +5, -5 and 3.3 V.  Then one tile at a time.
16. A10's current source: with 1 V on DRIVE IN the LED carries 45 mA; above about 1.1 V the op amp runs out of
    headroom.  Never put the DAC's +4 V open-circuit swing on DRIVE IN without a series resistor.
17. A8's heater is 170 mA when Pmod 3 is high; the 2512 pair runs warm (0.83 W).  Nothing else on the board is near it.
18. A9's IF OUT is a 1.5 k source: read it with a high-impedance scope input or the ADC's high-impedance setting.

## What was dropped from the plan (not faults: scope)

A4's loop; A7's loop-filter and VCO-capacitor DIPs and its two loops (probe pins 9 and 13); A8's NTC divider and
loop; A10's laser terminal and its DIP (solder a module's leads to the LED's pads); A12's 3.5 mm jack; A9's
carrier-null trimmer and output follower; A5's 4-way DIP (10 k, 1 k and a socket instead); A11's TX IN jack and
comparator (the bridge is driven from the Pmod); A2's and A3's two-stage variants.
