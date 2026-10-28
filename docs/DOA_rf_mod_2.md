# RF-MOD-2: what could make it dead on arrival, and what to check before paying

Rev A, 2026-10-25.  Every item is a fact the design assumed that a datasheet, JLCPCB's placement preview or the first
bench test must confirm.  The ones marked **order gate** must be confirmed before the order is placed.

## Order gate: pins, packages and polarity

1. **ADL5375-05 (X1), ADL5380 (X2), AD8318 (X6).** ADI LFCSPs on KiCad's footprints, CPL rotation 270 (ADI's "-BL"
   drawings, predicted).  Confirm each pin-1 dot in the preview; a quarter turn puts the supply on an RF pin.
2. **The three footprints made from JLCPCB's drawings:** MAX2659 (X8, UDFN-6 1.5 x 1.0), SAFFB1G56 (X8, twice,
   1.1 x 0.9 five-pad SAW) and SKY13370 (X11, DFN-6 1.5 x 1.5).  `scripts/gen_footprints.py` has each one's source
   dimensions.  Compare the pads with the datasheets' recommended land patterns before ordering.
3. **ADL5611 (X7).** SOT-89, rotation 180 (JLCPCB's drawing has pins 1 and 3 opposite KiCad's, as the GALI-84+).
   Reversed, its bias lands on the input.
4. **MAX2871 (X3)** and **QPL9547 (X4)**: RF-MOD's tiles (see `DOA_rf_mod.md` items 1 and 7a).  X3's REF IN is at its right
   cell's top-left (its line on the back) and its OUT A- (RFOUTA-) at the bottom-right, its line in the margin as R10's.
4a. **HHM22137A1 (X5, twice).** TDK's 1.6 x 0.8 mm coupler on JLCPCB's land pattern for C415328, the pads drawn 0.29 mm wide
   where JLCPCB draws 0.35 (TDK's terminals are 0.25; 0.25 mm between pads is the RF class's clearance).  Rotation 0
   (predicted), the first coupler placed at 180 degrees and the second at 0 on purpose: they face opposite ways.  Pin 3 is
   the input, 1 the output, 4 the coupled port, 6 the isolated port (51 ohm), 2 and 5 ground.  Confirm TDK's direction
   mark sits at the input end of each (the first one's toward IN, the second one's toward OUT): a turned coupler swaps
   FWD and REFL with its terminated port, and that jack reads nothing.
5. **MMBT3904 and TPS22917 (X7).** As AMOD-2's Y9: the base on -5 V, the emitter the noise node; the load switch's ON
   from IO6.
6. **The stack.**  The 50 ohm lines assume JLC04161H-7628, as RF-MOD.  Choose that stack in the order.
7. **X9's loop** has no copper on any layer within 2 mm (rule areas): check the inner-layer gerbers show the hole.

8. **The Pmod plug (on X3).**  IO1 MUXOUT, IO2 SDATA, IO3 SCLK, IO4 LE (X3), IO5 and IO8 X11's V1 and V2 (drive one
   high and the other low), IO6 X7's noise; IO7 spare (X1's DSOP is grounded: always on).
9. **ADL5380 stock**: 14 on 2026-10-25, accepted by Jason ("14 and 21 in stock isn't great, but I would not consider
   that level too low to proceed"); `check_outputs` records the exception.  Read it again on the order day.

## Order gate: the rails

10. +5 V covers L3; -5 V (the LM2664, 40 mA) is a polygon in the gutter under row 1 and under X10, for X2's two
    difference amplifiers and X7's junction.  X1's, X2's and X3's 5 V / 3.3 V are islands on L3 under their chips.

## Bench, first power

11. Every tile off: the green and red LEDs light.  X3 on, 25 MHz on REF IN, program it: OUT A+ and OUT A- at -4 to +5 dBm.
12. X3's OUT A+ into X1's LO IN and OUT A- into X2's (set -1 dBm); a DC on X1's I IN: a carrier at RF OUT; I and Q of a
    tone on X2's RF IN appear at I OUT and Q OUT.
13. X7 with IO6 high into a spectrum analyzer: a flat floor from 50 MHz to 4 GHz; IO6 low: the analyzer's own floor.
14. X8 with an active GNSS antenna (it gets 3.3 V on the centre pin): its output into X2 or a spectrum analyzer shows
    the noise hump of the L1 band.  A passive antenna sees the 3.3 V through 10 ohm and 18 nH: use a DC block.
15. X5: X1's tone at 1 GHz into IN, a 50 ohm terminator on OUT: FWD 25 dB below the tone, REFL about 45 dB below (the
    directivity and the terminator's match); OUT open or shorted: REFL comes up to about 25 dB below, with opposite phases
    in X2's I and Q.

## What changed from the plan (scope, not faults)

`PLAN_LEVEL2.md` section 4: X3's two outputs (OUT A+ and OUT A-, Prompt 15) where one output was split by X5; X5 a dual
directional coupler of two TDK parts (Prompt 15) where the plan had a printed one; the switch as X11 (SKY13370); the
split-ring resonator dropped for X9's broadband loop.
