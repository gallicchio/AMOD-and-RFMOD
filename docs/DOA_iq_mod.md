# IQ-MOD: what could make it dead on arrival, and what to check before paying

Rev A, 2026-10-25.  Every item is a fact the design assumed that a datasheet, JLCPCB's placement preview or the first
bench test must confirm.  The ones marked **order gate** must be confirmed before the order is placed.

**Placements (Prompt 17).**  `scripts/check_rotations.py` found rev A's table placing every SOT-23, SOT-23-5 and
SOT-23-6 as KiCad draws them, while JLCPCB's drawings are turned 180 ("-BR") or 90 ("-BL"); the upload CPL now turns
them, and moves the USB-C, SOT-89s, slide switches and headers to JLCPCB's origins (`parts.JLC_DATUM`).  In the preview,
check that each SOT-23's pin 1 sits at its silkscreen dot and the USB-C's shell sits on its pads: an **order gate**.

## Order gate: pins, packages and polarity

1. **ADL5375-05 (q1), ADL5380 (q2), AD8318 (q6).** ADI LFCSPs on KiCad's footprints, CPL rotation 270 (ADI's "-BL"
   drawings, predicted).  Confirm each pin-1 dot in the preview; a quarter turn puts the supply on an RF pin.
2. **The three footprints made from JLCPCB's drawings:** MAX2659 (q8, UDFN-6 1.5 x 1.0), SAFFB1G56 (q8, twice,
   1.1 x 0.9 five-pad SAW) and SKY13370 (q11, DFN-6 1.5 x 1.5).  `scripts/gen_footprints.py` has each one's source
   dimensions.  Compare the pads with the datasheets' recommended land patterns before ordering.
3. **ADL5611 (q7).** SOT-89, rotation 180 (JLCPCB's drawing has pins 1 and 3 opposite KiCad's, as the GALI-84+).
   Reversed, its bias lands on the input.
4. **MAX2871 (q3)** and **QPL9547 (q4)**: RF-MOD's tiles (see `DOA_rf_mod.md` items 1 and 7a).  q3's REF IN is at its right
   cell's top-left (its line on the back) and its OUT A- (RFOUTA-) at the bottom-right, its line in the margin as r10's.
4a. **HHM22137A1 (q5, twice).** TDK's 1.6 x 0.8 mm coupler on JLCPCB's land pattern for C415328, the pads drawn 0.29 mm wide
   where JLCPCB draws 0.35 (TDK's terminals are 0.25; 0.25 mm between pads is the RF class's clearance).  Rotation 0
   (predicted), the first coupler placed at 180 degrees and the second at 0 on purpose: they face opposite ways.  Pin 3 is
   the input, 1 the output, 4 the coupled port, 6 the isolated port (51 ohm), 2 and 5 ground.  Confirm TDK's direction
   mark sits at the input end of each (the first one's toward IN, the second one's toward OUT): a turned coupler swaps
   FWD and REFL with its terminated port, and that jack reads nothing.
5. **MMBT3904 and TPS22917 (q7).** As PhMOD's h9: the base on -5 V, the emitter the noise node; the load switch's ON
   from IO6.
6. **The stack.**  The 50 ohm lines assume JLC04161H-7628, as RF-MOD.  Choose that stack in the order.
7. **q9's loop** has no copper on any layer within 2 mm (rule areas): check the inner-layer gerbers show the hole.

8. **The Pmod plug (on q3).**  IO1 MUXOUT, IO2 SDATA, IO3 SCLK, IO4 LE (q3), IO5 and IO8 q11's V1 and V2 (drive one
   high and the other low), IO6 q7's noise; IO7 spare (q1's DSOP is grounded: always on).
9. **ADL5380 stock**: 14 on 2026-10-25, accepted by Jason ("14 and 21 in stock isn't great, but I would not consider
   that level too low to proceed"); `check_outputs` records the exception.  Read it again on the order day.

## Order gate: the rails

10. +5 V covers L3; -5 V (the LM2664, 40 mA) is a polygon in the gutter under row 1 and under q10, for q2's two
    difference amplifiers and q7's junction.  q1's, q2's and q3's 5 V / 3.3 V are islands on L3 under their chips.

## The RF layout survey (2026-10-29)

CLAUDE_PCB.md's gates 24-32 (CostasLink rev A's receive chain, which lost 30 dB at 5.8 GHz with every line right), measured
on the written board by `scripts/rf_extract.py` and `scripts/rf_survey.py iq_mod 6` before the order:

- **Lines (gate 32):** every 50 ohm line 0.29 mm wide, 0.25 mm from the top pour, ground under all of it outside the jacks'
  launch voids.  The lines short of that are meant: q3's reference input (1 mm), the LNA's 5 V feed and q9's loop, the ODMR antenna, which has no ground by design.
- **Parts on the lines (gates 26-28):** the RF chips are internally matched, so no matching part hangs on a branch (the
  fault that cost CostasLink its 30 dB).  The shunt parts on RF lines are bias chokes and pull-ups 0.5-2 mm off the line,
  under 10 degrees at 2.4 GHz; their cold ends reach a capacitor in 1.2-4.4 mm, not the 1 mm the gate asks.
- **Detours (gate 24):** none but q9's loop, which is the antenna; `check_layout.py` now fails one in every build.
- **Stitching (gates 30, 32):** the fences carry 0.2-1.7 (median 0.4) vias per mm (the gate: 1.5), and the top pour near the lines is
  a median 2.0 mm and at most 9.4 mm from a ground via.  Fine at 2.4 GHz (lambda/20 is 3 mm in FR4); short of the gate for the 5.8-6 GHz stretch, where a via-free
  patch of the pour can resonate.  Measure the stretch band against a cable before believing it.
- **Not done:** the as-laid circuit simulation of gate 25.  The reason is the second bullet: with internally matched blocks
  and no external match, the reference circuit and the as-laid one are the same chips joined by 50 ohm lines.

## Bench, first power

11. Every tile off: the green and red LEDs light.  q3 on, 25 MHz on REF IN, program it: OUT A+ and OUT A- at -4 to +5 dBm.
12. q3's OUT A+ into q1's LO IN and OUT A- into q2's (set -1 dBm); a DC on q1's I IN: a carrier at RF OUT; I and Q of a
    tone on q2's RF IN appear at I OUT and Q OUT.
13. q7 with IO6 high into a spectrum analyzer: a flat floor from 50 MHz to 4 GHz; IO6 low: the analyzer's own floor.
14. q8 with an active GNSS antenna (it gets 3.3 V on the centre pin): its output into q2 or a spectrum analyzer shows
    the noise hump of the L1 band.  A passive antenna sees the 3.3 V through 10 ohm and 18 nH: use a DC block.
15. q5: q1's tone at 1 GHz into IN, a 50 ohm terminator on OUT: FWD 25 dB below the tone, REFL about 45 dB below (the
    directivity and the terminator's match); OUT open or shorted: REFL comes up to about 25 dB below, with opposite phases
    in q2's I and Q.  Calibrated on AMOD-N's n1 (SHORT, OPEN, LOAD, THRU), its 25 OHM standard reads |S11| = 1/3.

## What changed from the plan (scope, not faults)

`PLAN_LEVEL2.md` section 4: q3's two outputs (OUT A+ and OUT A-, Prompt 15) where one output was split by q5; q5 a dual
directional coupler of two TDK parts (Prompt 15) where the plan had a printed one; the switch as q11 (SKY13370); the
split-ring resonator dropped for q9's broadband loop.
