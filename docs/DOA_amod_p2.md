# AMOD-P2: what could make it dead on arrival, and what to check before paying

Rev A, 2026-10-28 (Prompt 17).  Every item is a fact the design assumed that a datasheet, JLCPCB's placement preview or
the first bench test must confirm.  The ones marked **order gate** must be confirmed before the order is placed.
`scripts/check_rotations.py amod_p2` fits JLCPCB's own drawing of every part onto its footprint; on 2026-10-28 it
agreed with the rotation table on all 33 codes.

## Order gate: pins, packages and polarity

1. **PE43711 (P22, U2201).** KiCad's QFN-24 4 x 4 (EP 2.7), CPL +270 (JLCPCB's drawing has pin 1 bottom-left; CostasLink
   rev A read +270 for this same part in its preview).  Pins as pSemi's Table 9: 5 RF1 (IN through 100 nF), 14 RF2 (OUT
   through 100 nF), 2 VDD and 3 P/S on the Pmod's 3.3 V (serial mode), 16 LE, 17 CLK, 18 SI on Pmod IO4, IO3 and IO2;
   the seven parallel pins (1, 19-24) and every ground pin into the exposed pad.  In the preview the pin-1 dot sits at
   the chip's top-right corner as the board shows it.
2. **ADP-2-1+ (P17, U1701), case CD636, 41 in stock.**  The footprint is JLCPCB's drawing (pin 1 bottom-left), turned 270
   on the board so SUM (pin 1) faces the top jack.  Pins 1 SUM, 3 port 1, 4 port 2, 6 ground; 2 and 5 joined by a
   track under the body and **not** grounded (Mini-Circuits: "externally connect together & isolate").
3. **TC1-1TG2+ (P24) and TC4-1W+ (P25), case AT224.**  JLCPCB's drawing: 1, 2, 3 along the top (secondary dot, centre
   tap, secondary), 6 and 4 along the bottom (primary dot, primary).  Both turned 180 so the primary faces the IN line.
   A reversed transformer still passes signal (the windings swap), but P24's OUT would no longer float and P25's 1:4
   would become 4:1: check the dot in the preview.
4. **SMS7630-006LF (P20), a reverse series pair: pin 2 anode, pin 3 the joint, pin 1 cathode.**  CPL +180 (JLCPCB's
   SOT-23 drawings are KiCad's turned 180).  Reversed, the doubler's output goes negative: it still detects.  83 in stock.
5. **MMBT3904 (P23) and the AO3401A of P23's switch: +180, as every SOT-23 on all six boards since Prompt 17.**  The
   BB133's pad 1 (cathode) goes to the tank node, which sits at +0.6 to +2.6 V; reversed, the diode conducts and the
   oscillator does not tune (it may not start).
6. **LFCN-1000+ (P19)** is symmetric (1 and 3 interchangeable); a half turn is harmless.
7. **The Pmod plug (on P22).**  `check_pmod` maps every pad to its standard pin: IO2 SDATA, IO3 SCLK, IO4 LE, pins 6
   and 12 the host's 3.3 V (an L3 pour under the whole board), 5 and 11 ground.  IO1 and IO5-IO8 unused.
8. **P24's floating OUT.**  In the Gerber viewer: no copper of any layer within 5.6 mm of OUT's centre except its own
   pin, its legs (net /P24_ISO, joined by a U of track on the front) and the two tracks from the transformer.
9. **P14's SHORT** is the centre pin joined to the top pour all round (no launch void); the OPEN is the bare pin with
   its void.  If the preview or the Gerbers show a ring of clearance round SHORT's pin, the short is open.
10. **P18's stub** is copper graphics on the net, not tracks (so DRC does not call its open end dangling): confirm it is
    in the front copper Gerber.
11. **Feet, no holes**: four stick-on feet as RF-MOD (the board is held by its plug when it is on a host).

## Bench, first power

12. Unplugged, every passive tile works: P16 IN to OUT 1 is -6 dB on a VNA or the host, P17 SUM to PORT 1 -3.2 dB, P19
    flat to 1 GHz, P15's MATCHED reads 50 ohm at 9.2 MHz.
13. Plugged into the host's Pmod: 3.3 V across P22's 100 nF.  P22 powers up at 31.75 dB; write 0x00 (0 dB) and IN to OUT
    reads 1.5-2.8 dB of loss; write 0x40 (16 dB) and it reads 16 dB more.
14. P23's switch up: OUT about -22 dBm near 10.5 MHz on the ADC's x10 input; TUNE from a DAC at -2 V and +2 V moves it
    to about 9.6 and 11.5 MHz.  Then a tone near its frequency on TUNE: it locks.
15. P20: -10 dBm at 915 MHz into IN gives about 0.1 V on the ADC at high impedance; 20 dB less, about 1 mV.
16. P21 with 5 V on its DC loop: 5 V on RF+DC, none on RF; RF to RF+DC within 1 dB from 2 MHz up.
17. P14: calibrate a NanoVNA on SHORT, OPEN, LOAD and THRU through a short cable, then read the 25 OHM standard:
    |S11| = 0.33 (9.5 dB of return loss) and a phase that turns with frequency (its 4.75 mm of line).

## What it is not

AMOD-P2 has no USB and no power of its own: P22 and P23 are dark unless the board is on a Pmod.  Its RF tiles are on
RF-MOD's stack-up and launch, so their 50 ohm lines are only as good as RF-MOD's (CostasLink's design); none has been
measured.
