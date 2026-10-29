# RF-MOD: what could make it dead on arrival, and what to check before paying

Rev A, 2026-10-25.  Each item is an assumption the design made that a datasheet, JLCPCB's placement preview or the first
bench test must confirm.  The ones marked **order gate** must be confirmed before the order is placed.

**Placements (Prompt 17).**  `scripts/check_rotations.py` found rev A's table placing every SOT-23, SOT-23-5 and
SOT-23-6 as KiCad draws them, while JLCPCB's drawings are turned 180 ("-BR") or 90 ("-BL"); the upload CPL now turns
them, and moves the USB-C, SOT-89s, slide switches and headers to JLCPCB's origins (`parts.JLC_DATUM`).  In the preview,
check that each SOT-23's pin 1 sits at its silkscreen dot and the USB-C's shell sits on its pads: an **order gate**.

## Order gate: pins, packages and polarity

1. **MAX2871 (r10).** The pin table is CostasLink's, which passed two review rounds; the footprint is KiCad's
   QFN-32 5 x 5 with EP 3.1.  Check pin 1's dot in the placement preview (the CPL adds no rotation).  RFOUTB (14, 15)
   and SW (5) are left open: the gateware must keep RFOUTB disabled (register 4, bit 8 = 0).
2. **GALI-84+ (r12).** SOT-89, pin 1 in, 2 the tab (ground), 3 out and DC.  JLCPCB's drawing has pins 1 and 3 on
   the opposite side to KiCad's, so the CPL turns it 180 degrees (`JLC_ROTATION`, predicted).  Reversed, DC lands on
   the input's 100 pF and the part does nothing.  Confirm the tab faces the board's top edge in the preview.
3. **TC32H4 TCXO (r9).** The CPL turns it 180 degrees (JLCPCB's pad 1 is top-left, KiCad's bottom-left); pad 1 (enable
   or no connection on Taitien's drawing) floats.  A wrong turn puts 3.3 V on the output and ground on VCC.
4. **ADL5350 (r7, r8).** The footprint is JLCPCB's own land pattern for C206667 (pads 1-4 along one long side, 5-8
   along the other, the 1.74 x 0.45 paddle as pad 9).  Check that pad 1 is RF/IF as the datasheet's Figure 2 says.
5. **B39921B2672P810 SAW (r4).** Pad 1 in, 4 out, 2, 3 and 5 ground (RF360's section 4; JLCPCB's drawing numbers the
   pads as RF360 does, its bottom view turned over).  The first build took the output from pad 3, a ground pad, and
   grounded pad 4: found by `scripts/check_pinouts.py` (Prompt 19) and fixed.  The part is symmetric in function, so a
   swap of in and out is harmless; a quarter turn would short the signal to ground.
6. **LFB212G45SG8A127 LTCC (r2).** Pads 4 in, 2 out at the ends, 1 and 3 ground along the long sides.  A quarter turn
   grounds the signal.
7. **MT3608 boost (r9).** SOT-23-6: 1 SW, 2 GND, 3 FB, 4 EN, 5 IN, 6 NC.  FB 0.6 V with 12 k / 1 k: 7.8 V.  The SS34's
   cathode bar must face the output capacitor.
7a. **QPL9547 (r5).** DFN-8 2 x 2 mm on KiCad's footprint, CPL rotation 0 (predicted: JLCPCB's DFN drawings put pin 1
   top-left as KiCad's).  Confirm pin 1's dot in the preview; a half turn swaps input and output and puts the bias on
   the input.  It runs from 5 V (not r12's 7.8 V).
7b. **TRF3722 (r13) and its TLV75733.** VQFN-48 7 x 7 and WSON-6 2 x 2, both rotation 0 (predicted).  Confirm both
   pin-1 dots.  The TRF3722's I and Q come from the host's DACs through the tile's bias networks; its LO output is the
   jack beside its RF output.
7c. **ADEX-10L+ (r1).** Mini-Circuits case CD542 on JLCPCB's own land pattern for C118997 (pads 1-3 along the bottom from
   the left, 4-6 along the top from the right), rotation 0 (predicted).  Mini-Circuits' pinout: 6 LO, 3 RF, 2 IF, 1 4 5
   ground.  Confirm the pin-1 mark in the preview against Mini-Circuits' outline: a half turn puts LO on ground pin 1 and
   RF on ground pin 4, and the tile does nothing (nothing burns: it is passive).
7d. **r10's OUT A- line** runs 1.25 mm below the tile, in the bottom margin above the Pmod plug's pins, with the top
   ground pour following it (`Tile.pour_below`).  Check in the preview that the plug's body does not cover it.

8a. **The Pmod plug (J1003, on r10).**  JLCPCB's numbering: pads 1-2 3.3 V, 3-4 ground (Pmod pins 6/12 and 5/11), the
    lines on pads 5-12; `check_pmod` maps every pad to its standard pin.  IO1 MUXOUT of r10, IO2 SDATA and IO3 SCLK
    (r10 and r13), IO4 LE of r10, IO5 the TRF3722's readback, IO6 LE of r13.  Confirm the body hangs off the bottom edge
    in the placement preview.
8b. **No mounting holes**: four stick-on rubber feet, circled on the back.

## Order gate: rules and fab

9. **The fine rules.**  The synthesizers' and mixers' nets use 0.127 mm clearance, 0.15 mm tracks and 0.45 / 0.25 mm
   vias (JLCPCB's standard four-layer limits are 0.09 / 0.09 and 0.25 / 0.15, so these cost nothing extra).  The rest
   of the board keeps 0.2 mm.
10. **The stack.**  The 50 ohm lines assume JLC04161H-7628 (0.21 mm of 7628 prepreg between L1 and L2).  Choose that
   stack in the order; another one moves the impedance by 10-20 ohm.
11. **Stock.**  The GALI-84+ (r12 only now) had 144 on the day: thin; alternates (stock not checked) are the GALI-S66+
    or a PGA-103+ on the same footprint with a different bias resistor.

## Bench, first power

11. With every tile off: the green LED (5 V in) and the yellow one (7.8 V) light; REF OUT shows 25 MHz.
12. r12 on: 97 mA from 7.8 V; the 2512 runs warm (0.2 W).  The pin 3 voltage should read 5.4-6.2 V.  r5 on: the
    QPL9547's current from 5 V should match its datasheet's (tens of mA); far more means a turned part.
13. r10 or r13 on: 3.3 V on the LDO's output; program the chip (the gateware's `max2871` module, or the TRF3722's
    registers over the same SDATA and SCLK); the red LED lights on lock.  Unprogrammed, a synthesizer may output
    anything from nothing to full power.
14. r7 or r8: the LO at +4 dBm or more; a 6.25 MHz IF at 0 dBm gives about -8 dBm at RF on both sides of the LO.
15. r10: OUT A+ and OUT A- at the same power within a dB (OUT A- has 30 mm more line: 0.2-0.4 dB at 2.4 GHz), 180
    degrees apart on two channels of a fast scope at a low frequency.  A 50 ohm terminator on whichever is unused.
16. r1: r10's OUT A+ at +5 dBm on LO, a -20 dBm tone 10 MHz away on RF: about -27 dBm at 10 MHz on IF (7 dB of loss);
    the LO leaks to IF at about -25 dBm at 1 GHz (the datasheet's L-I isolation).

## What changed from the plan (scope, not faults)

After Prompt 13 the QPL9547 LNA (r5, now in stock as the taped QPL9547TR7) and the TRF3722 quadrature transmitter (r13)
are on rev A.  The LTC5510 mixers (35 in stock) and the RFX2401C front end are not; the ADL5350 (twice) takes the
mixers' place.  The printed antennas are replaced by SMA whips.  After Prompt 15 r1's cell holds a diode-ring mixer
(ADEX-10L+) where a resistive splitter was: the reference reaches r13 by a back trace, and r10's second output (OUT A-,
the MAX2871's RFOUTA-, which was terminated) is the second LO.
