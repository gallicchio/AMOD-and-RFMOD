# RF-MOD: what could make it dead on arrival, and what to check before paying

Rev A, 2026-10-25.  Each item is an assumption the design made that a datasheet, JLCPCB's placement preview or the first
bench test must confirm.  The ones marked **order gate** must be confirmed before the order is placed.

## Order gate: pins, packages and polarity

1. **MAX2871 (R10, R11).** The pin table is CostasLink's, which passed two review rounds; the footprint is KiCad's
   QFN-32 5 x 5 with EP 3.1.  Check pin 1's dot in the placement preview (the CPL adds no rotation).  RFOUTB (14, 15)
   and SW (5) are left open: the gateware must keep RFOUTB disabled (register 4, bit 8 = 0).
2. **GALI-84+ (R5, R12).** SOT-89, pin 1 in, 2 the tab (ground), 3 out and DC.  JLCPCB's drawing has pins 1 and 3 on
   the opposite side to KiCad's, so the CPL turns it 180 degrees (`JLC_ROTATION`, predicted).  Reversed, DC lands on
   the input's 100 pF and the part does nothing.  Confirm the tab faces the board's top edge in the preview.
3. **TC32H4 TCXO (R9).** The CPL turns it 180 degrees (JLCPCB's pad 1 is top-left, KiCad's bottom-left); pad 1 (enable
   or no connection on Taitien's drawing) floats.  A wrong turn puts 3.3 V on the output and ground on VCC.
4. **ADL5350 (R7, R8).** The footprint is JLCPCB's own land pattern for C206667 (pads 1-4 along one long side, 5-8
   along the other, the 1.74 x 0.45 paddle as pad 9).  Check that pad 1 is RF/IF as the datasheet's Figure 2 says.
5. **B39921B2672P810 SAW (R4).** Pad 1 in, 3 out, the others ground (JLCPCB's drawing).  The part is symmetric in
   function, so a swap of in and out is harmless; a quarter turn would short the signal to ground.
6. **LFB212G45SG8A127 LTCC (R2).** Pads 4 in, 2 out at the ends, 1 and 3 ground along the long sides.  A quarter turn
   grounds the signal.
7. **MT3608 boost (R9).** SOT-23-6: 1 SW, 2 GND, 3 FB, 4 EN, 5 IN, 6 NC.  FB 0.6 V with 12 k / 1 k: 7.8 V.  The SS34's
   cathode bar must face the output capacitor.

## Order gate: rules and fab

8. **The fine rules.**  The synthesizers' and mixers' nets use 0.127 mm clearance, 0.15 mm tracks and 0.45 / 0.25 mm
   vias (JLCPCB's standard four-layer limits are 0.09 / 0.09 and 0.25 / 0.15, so these cost nothing extra).  The rest
   of the board keeps 0.2 mm.
9. **The stack.**  The 50 ohm lines assume JLC04161H-7628 (0.21 mm of 7628 prepreg between L1 and L2).  Choose that
   stack in the order; another one moves the impedance by 10-20 ohm.
10. **Stock.**  The GALI-84+ had 144 on the day: enough for 72 boards' pairs but thin; alternates (stock not checked) are the GALI-S66+
    or a PGA-103+ on the same footprint with a different bias resistor.

## Bench, first power

11. With every tile off: the green LED (5 V in) and the yellow one (7.8 V) light; REF OUT shows 25 MHz.
12. R5 or R12 on: 97 mA from 7.8 V each; the 2512 runs warm (0.2 W).  The pin 3 voltage should read 5.4-6.2 V.
13. R10 or R11 on: 3.3 V on the LDO's output; program the chip (the gateware's `max2871` module); the red LED lights
    on lock.  Unprogrammed, the part may output anything from nothing to full power.
14. R7 or R8: the LO at +4 dBm or more; a 6.25 MHz IF at 0 dBm gives about -8 dBm at RF on both sides of the LO.

## What changed from the plan (scope, not faults)

The QPL9547 LNA (no stock), the LTC5510 mixers (35 in stock), the RFX2401C front end and the TRF3722 quadrature
transmitter are not on rev A; the GALI-84+ (twice) and the ADL5350 (twice) take their places.  The printed antennas
are replaced by SMA whips; R1's cell holds a resistive splitter that the reference and the LO distribution need.
