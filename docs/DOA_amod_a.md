# AMOD-A: what could make it dead on arrival, and what to check before paying

Rev A, 2026-10-25.  Every item is a fact the design assumed that a datasheet, JLCPCB's placement preview or the
first bench test must confirm.  The ones marked **order gate** must be confirmed before the order is placed.

## Order gate: pin and polarity assumptions

1. **The HB100's header (A5, J501).**  A 1 x 3 socket wired +5 V (the tile's switched rail), IF, ground.  HB100
   modules differ in their pin order (some print "+5V GND IF", some "IF GND +5V"): the module goes on three jumper
   wires, so read the module's own print and wire it to match.  +5 V on the IF pin does no harm through 1 uF; on the
   ground pin it shorts the tile's rail through the P-FET (the PTC on A1 limits it).
2. **A10's DIP4 (SW1001).**  One reference resistor at a time (47, 470, 4.7 k, 47 k from S to X); two closed give
   their parallel value, which the analysis must use.  The DUT jack's part sees up to +-4 V and 40 mA (47 ohm).
3. (Rev A's LT6230 item: A5 no longer carries an LT6230.)
4. **TLV3501 (A6, U601).** SOT-23-6, taken as -IN 1, V- 2, +IN 3, V+ 4, OUT 5, SHDN 6 with SHDN grounded (active
   high).  Confirm.
5. **PAM8302A (A12, U1201).** SOIC-8, taken as SD 1, BYP 2, IN+ 3, IN- 4, VO+ 5, VDD 6, GND 7, VO- 8 (the board's
   own box symbol).  SD is tied to VS (on when the tile is on).  Confirm SD's polarity (active low shutdown).
6. **DRV8837 (A11, U1101).** WSON-8 with the thermal pad on ground; pins taken as VM 1, OUT1 2, OUT2 3, GND 4,
   IN2 5, IN1 6, nSLEEP 7, VCC 8, nSLEEP tied to VS.  Confirm against the DSG package drawing (pin 1 at the dot).
7. **MC1496 (A9, U901).** SOIC-14 as the datasheet's "pin connections": SIG+ 1, GAIN 2 and 3, SIG- 4, BIAS 5,
   OUT+ 6, CAR+ 8, CAR- 10, OUT- 12, VEE 14; pins 7, 9, 11, 13 no connection.  Pin 7 carries the output wire past
   the chip: that is only safe if pin 7 is truly unconnected inside the package (the datasheet says so).
8. **OPA847 (A4, U401).** Now the SOT-23-6 (OPA847IDBVR, C160422; the SOIC-8 did not fit between the checkerboard
   jacks), taken as TI's DBV pinout: OUT 1, -VS 2, +IN 3, -IN 4, DIS 5, +VS 6, with DIS tied to +VS (enabled; low
   disables).  Confirm against the DBV package drawing and the pin-1 mark in JLCPCB's preview.
9. **74HC4046A (A7, U701).** Now Nexperia's 74HC4046APW-Q100J in TSSOP-16 (C546981, 234 in stock on 2026-10-25):
   TI's SOIC-16 (C6542) was too long for the cell between the checkerboard jacks.  Nexperia's pin table is the same
   as TI's (pin 15 is PC3out, unused).  Check two things: the stock on the order day (TI's CD74HC4046APWR, C6543,
   is the same footprint but had only 21), and the VCO range with R1 10 k and C1 1 nF against Nexperia's Fig. 29,
   since its curves differ a little from TI's.
10. **The MSK12C02 slide switch** (every powered tile): pad 1 is taken as the contact made with the slider UP
    (toward the jacks), pad 2 the common, pad 3 the other end.  The tile grounds pad 1 (on) and puts the rail on
    pad 3 (off); if the switch is mirrored the labels are wrong but nothing is damaged (the FET is either on or
    off).  Check the "ON" marking in the preview.
11. **The HRO TYPE-C-31-M-12 footprint** (A1): both CC pins have 5.1 k; the SMD ground pads A1/B1 reach the shell
    holes with a short wire each (the plane carries them).  Check the connector's overhang (1.2 mm past the edge)
    in the preview.

12a. **The Pmod plug (J1104).**  Fixed 2026-10-25: the first layout mirrored every line (see PLAN.md section 2).  The
     plug now sits two columns left with ground on pads 3-4 and 3.3 V on pads 1-2 in JLCPCB's numbering, which is
     Pmod pins 5/11 and 6/12; `check_pmod` confirms every pad.  Confirm in the placement preview that the plug's body
     hangs off the bottom edge and pad 1's square is at the left end of the row nearest the edge.  The lines are now
     IO8/IO7 (A6), IO6 (A8), IO4/IO3 (A11), IO2 (A12); IO1 and IO5 are spare (A10 and A5 no longer use a line).
12b. **No mounting holes.**  Four stick-on rubber feet (8 mm, circled on the back) replace them; buy them with the order.

## Order gate: the rails

12. The -5 V rail is one polygon on L3 (In2) through the gutters under rows 0 and 2 and down the left margin; its
    end in the right margin stops at x 93.6 so the +5 V pour keeps a path down that margin.  Every tile's -5 V via
    lands in a gutter strip; `check_outputs` found the net connected, and KiCad's DRC found no island.
13. The +3.3 V rail is the strip in the gutter under row 1; only A6 draws from it, through the header via at the
    tile's bottom edge.
14. A1's LM2664 gives 40 mA of -5 V.  The op-amp tiles draw about 4 mA each at rest (OPA810), the MC1496 2 mA, the
    class-D nothing from -5 V: all twelve tiles on at once stay under 40 mA.  The USB-C source must give 1.5 A for
    the heater (170 mA), the HB100 (about 40 mA), A10's DUT drive (40 mA at most) and the class-D at full volume.

## Bench, first power

15. With every tile off, the green LED lights and the socket shows +5, -5 and 3.3 V.  Then one tile at a time.
16. A10: with the DUT jack open, S OUT and X OUT read the same (half of S each into 50 ohm); shorted, X OUT reads 0.
    Calibrate open and short at every range before measuring.  A5: wave a hand a metre in front of the HB100 and the
    IF shows tens of hertz at x101.
17. A8's heater is 170 mA when Pmod IO6 is high; the 2512 pair runs warm (0.83 W).  It now sits in A8's top-left,
    about 2 mm below A4's slide switch and FET across the gutter, which tolerate the rise; no precise part is near it.
18. A9's IF OUT is a 1.5 k source: read it with a high-impedance scope input or the ADC's high-impedance setting.

## What was dropped from the plan (not faults: scope)

A4's loop; A7's loop-filter and VCO-capacitor DIPs and its two loops (probe pins 9 and 13); A8's NTC divider and
loop; rev A's first A10 (an LED driver and a photodiode amplifier, now on the host) and A5 (Johnson noise, now on the
host); A12's 3.5 mm jack; A9's
carrier-null trimmer and output follower; A5's 4-way DIP (10 k, 1 k and a socket instead); A11's TX IN jack and
comparator (the bridge is driven from the Pmod); A2's and A3's two-stage variants.
