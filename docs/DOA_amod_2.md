# AMOD-2: what could make it dead on arrival, and what to check before paying

Rev A, 2026-10-25.  Every item is a fact the design assumed that a datasheet, JLCPCB's placement preview or the first
bench test must confirm.  The ones marked **order gate** must be confirmed before the order is placed.

## Order gate: pins, packages and polarity

1. **THS3491 (Y2, U201).** VQFN-16 3 x 3 (RGT) on KiCad's footprint, CPL rotation 0 (TI's "-TL" drawing, predicted).
   Pins as the board's own symbol: 1 FB, 3 -IN, 4 +IN, 5 GND, 6 TJ (open), 7/8 -VS, 10/11 VOUT, 13/14 +VS, 16 PD,
   2, 9, 12, 15 no connection, the pad on ground through four vias.  Confirm against TI's RGT pin table, PD's polarity
   (high runs it; 10 k holds it off) and that the thermal pad may sit at ground rather than -VS.
2. **TPS65131 (Y1).** VQFN-24 4 x 4 (RGE), rotation 0 (predicted).  +15 V = 1.213 V x (1 + 1 M / 88.7 k) and -15 V =
   -1.213 V x 1.3 M / 105 k: confirm the feedback references (VREF and FBN) in TI's table.  The inverter's B5819W must
   point from SWN to -15 V as drawn; reversed, -15 V never comes up and the yellow LED (+15 V) still lights.
3. **DRV8876 (Y4).** HTSSOP-16 (PWP), rotation 270 (predicted).  PMODE and IMODE are grounded (PH/EN mode,
   cycle-by-cycle chopping), nSLEEP on the switched 5 V, nFAULT open.  Confirm the current mirror's gain (A_IPROPI)
   in the datasheet: it sets both MON's volts per amp and the chopping current with VREF at 2 V and 1.5 k on IPROPI.
4. **The OPA810s and LMH6629s (Y3's preamp uses an OPA847; Y4, Y6, Y7, Y10 the OPA810; Y5, Y9 the LMH6629).**
   SOT-23-5 as 1 OUT, 2 V-, 3 +IN, 4 -IN, 5 V+ (`amod:OPA_SOT23-5`), the same as AMOD-A's.  Confirm the LMH6629MF's
   pinout matches (its WSON version has a COMP pin; the SOT-23 does not).
5. **BB133 varactors (Y8, four).** SOD-323, pad 1 the cathode.  Each tank's pair stands cathode to cathode on the bias
   node; a reversed diode conducts and pins its tank's node to a diode drop: the tank still rings, at a different
   frequency and Q.  Check the bands in the preview.
6. **MMBT3904 (Y9).** Pin 1 base (on -5 V), pin 2 emitter (the noise node), collector open.  Reversed (collector for
   emitter) the junction that breaks down is the collector's at 60 V: no noise.
7. **The SOT-23 FETs in Y10.** AO3401 (the current source), AO3400 (the shunt), 2N7002 (the reference): 1 G, 2 S, 3 D.
   A swapped source and drain on the AO3401 conducts through its body diode: the laser sees VS through 10 ohm.  Do not
   connect a laser before the bench check below.
8. **B5819W (Y4 twice, Y10) and 1N4148W (Y3, four pairs).** The cathode bar must face VM in Y4 and ID in Y10.  Each of
   Y3's pairs must be antiparallel (one bar each way); two bars the same way pass only one polarity of the pulse.
9. **The terminals (Y4) and the DIP4 (Y8)** are through-hole and must be selected for assembly.  The terminals' wire
   entries face the right edge (rot 270); check in the preview that they do not overhang the edge.

10. **The Pmod plug (on Y5).**  `check_pmod` maps every pad to its standard pin.  IO1 Y2's PD, IO5 Y10's shunt, IO6 and
    IO7 Y4's EN and PH, IO8 Y9's switch; IO2-IO4 spare.  A floating line leaves each tile safe: Y2 off, Y10's shunt
    off (100 k), Y4 off (100 k on both), Y9 off (the TPS22917's own pull-down).
11. **No mounting holes**: four stick-on rubber feet, circled on the back; one moved to (95.8, 71) off Y10's LD jack.
12. **Fiducials** at (3.5, 50), (96.5, 10) and (88, 97): the third moved off Y4's coil terminal (`FIDUCIALS` in
    `boards/amod_2.py`).

## Order gate: the rails

13. +5 V covers L3.  -5 V is a polygon on L3 in the gutter under row 0 with a finger up Y9's left side; Y3's OPA847, Y7's
    two OPA810 and Y9's junction draw about 30 mA of the LM2664's 40.
14. +-15 V go from Y1 to Y2 only, on two tracks on the back (0.5 mm), not on a plane.  The TPS65131 gives a few hundred mA
    on each from 5 V (check TI's curves for 15 V); Y2 at full output into 50 ohm draws more in its peaks, from its 3 x 10 uF.  Pulse it:
    a duty cycle under 10 %, and never into an open or a short for long.
15. Y4's VM is the higher of USB's 5 V (less a Schottky: 4.6 V, just above the DRV8876's 4.5 V minimum) and the
    terminal's supply.  The 10 uF on VM is rated 25 V: keep the external supply at 18 V or less.

## Bench, first power

16. Every tile off: the green LED (5 V), the red (-5 V) and the yellow (+15 V) light.  Then one tile at a time.
17. Y2 with IO1 low into a 50 ohm load rated 2 W: OUT sits at 0 V.  IO1 high and a 10 MHz burst of 0.1 V from DAC 1:
    1 V at OUT.  Then full scale, in bursts.
18. Y10 with no laser and a 10 ohm resistor on LD: SET at 0.1 V gives 10 mA (0.1 V across the resistor), MON reads
    the resistor's voltage / 200; IO5 high takes it to 0.  Only then a laser, starting at a few millivolts of SET; a
    VCSEL (about 1.5 mA) gets 30 dB of SMA attenuation on SET, so the DAC's full scale is about 3 mA.
19. Y8: DAC 1 swept 5-15 MHz into SIG, OUT 1 into an ADC: tank 1's resonance near 10 MHz; TUNE/PUMP's DC moves tank 2's.
20. Y4 on USB power with a 10 ohm, 5 W resistor as the coil: IO6 high gives 0.46 A; MON reads it.

## What changed from the plan (scope, not faults)

`PLAN_LEVEL2.md` section 3 lists them: Y1 without the I/O expander, the DAC and the LDOs; Y3's crossed diodes instead of
a PIN switch; Y5 without attenuators; Y6 with one channel; Y8 without buffers; Y10 with one range.
