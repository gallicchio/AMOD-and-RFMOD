# AMOD-N: what could make it dead on arrival, and what to check before paying

Rev A, 2026-10-28 (Prompt 17; n8's switch, Prompt 18).  Every item is a fact the design assumed that a datasheet, JLCPCB's placement preview or
the first bench test must confirm.  The ones marked **order gate** must be confirmed before the order is placed.
`scripts/check_rotations.py amod_n` fits JLCPCB's own drawing of every part onto its footprint; on 2026-10-28 it
agreed with the rotation table on all 32 codes (Prompt 18, after n8's switch went in and P15
came out).

## Order gate: pins, packages and polarity

1. **PE43711 (n8, U801).**  KiCad's QFN-24 4 x 4 (EP 2.7), on the board at 0, CPL +270 (JLCPCB's drawing has pin 1
   bottom-left; CostasLink rev A read +270 for this same part in its preview).  Pins as pSemi's Table 9: 5 RF1 (IN
   through 100 nF), 14 RF2 (OUT through 100 nF), 2 VDD on the Pmod's 3.3 V, 3 P/S on switch way 1 (100 k down), 16 LE
   on Pmod IO4 (100 k up), 17 CLK on IO3, 18 SI on IO2; the seven parallel pins (1, 24-19 for 0.25-16 dB) on ways 2-8,
   each 100 k down; every ground pin into the exposed pad.  In the preview the pin-1 dot sits at the chip's top-left
   corner as the board shows it.
1a. **The 8-way DIP switch (n8, SW801), DSHP08TSGET C40738.**  JLCPCB's drawing fits ours at 0 (unlike the 6-way
   DSHP06, which is 180).  Pins 1-8 are the ways' chip side (P/S, then the bits), 9-16 the 3.3 V side.  Turned half
   round it still works, but way 1 would be the 16 dB bit, way 8 SPI, and "up: on" upside down: check pin 1 in the
   preview against the silk's "1: SPI".
2. **ADP-2-1+ (n3, U301), case CD636, 41 in stock.**  The footprint is JLCPCB's drawing (pin 1 bottom-left), turned 270
   on the board so SUM (pin 1) faces the top jack.  Pins 1 SUM, 3 port 1, 4 port 2, 6 ground; 2 and 5 joined by a
   track under the body and **not** grounded (Mini-Circuits: "externally connect together & isolate").
3. **TC1-1TG2+ (n10) and TC4-1W+ (n11), case AT224.**  JLCPCB's drawing: 1, 2, 3 along the top (secondary dot, centre
   tap, secondary), 6 and 4 along the bottom (primary dot, primary).  Both turned 180 so the primary faces the IN line.
   A reversed transformer still passes signal (the windings swap), but n10's OUT would no longer float and n11's 1:4
   would become 4:1: check the dot in the preview.
4. **SMS7630-006LF (n6), a reverse series pair: pin 2 anode, pin 3 the joint, pin 1 cathode.**  CPL +180 (JLCPCB's
   SOT-23 drawings are KiCad's turned 180).  Reversed, the doubler's output goes negative: it still detects.  83 in stock.
5. **MMBT3904 (n9) and the AO3401A of n9's switch: +180, as every SOT-23 on all six boards since Prompt 17.**  The
   BB133's pad 1 (cathode) goes to the tank node, which sits at +0.6 to +2.6 V; reversed, the diode conducts and the
   oscillator does not tune (it may not start).
6. **LFCN-1000+ (n5)** is symmetric (1 and 3 interchangeable); a half turn is harmless.
7. **The Pmod plug (on n8).**  `check_pmod` maps every pad to its standard pin: IO2 SDATA, IO3 SCLK, IO4 LE, pins 6
   and 12 the host's 3.3 V (an L3 pour under the whole board), 5 and 11 ground.  IO1 and IO5-IO8 unused.
8. **n10's floating OUT.**  In the Gerber viewer: no copper of any layer within 5.6 mm of OUT's centre except its own
   pin, its legs (net /n10_ISO, joined by a U of track on the front) and the two tracks from the transformer.
9. **n1's SHORT** is the centre pin joined to the top pour all round (no launch void); the OPEN is the bare pin with
   its void.  If the preview or the Gerbers show a ring of clearance round SHORT's pin, the short is open.
10. **n4's stub** is copper graphics on the net, not tracks (so DRC does not call its open end dangling): confirm it is
    in the front copper Gerber.
11. **Feet, no holes**: four stick-on feet as RF-MOD (the board is held by its plug when it is on a host).

## Bench, first power

12. Unplugged, every passive tile works: n2 IN to OUT 1 is -6 dB on a VNA or the host, n3 SUM to PORT 1 -3.2 dB, n5
    flat to 1 GHz, n11 with its 200 ohm switched on reads about 50 ohm at IN from 3 to 800 MHz.
13. Plugged into the host's Pmod: 3.3 V across n8's 100 nF.  By hand (way 1 off): every bit off and IN to OUT reads
    1.5-2.8 dB of loss; way 8 (16 dB) on and it reads 16 dB more.  By the FPGA (ways 2-8 off, way 1 on): it powers up
    at 31.75 dB; write 0x00 (0 dB) and it reads the same 1.5-2.8 dB; write 0x40 (16 dB) and 16 dB more.
14. n9's switch up: OUT about -22 dBm near 10.5 MHz on the ADC's x10 input; TUNE from a DAC at -2 V and +2 V moves it
    to about 9.6 and 11.5 MHz.  Then a tone near its frequency on TUNE: it locks.
15. n6: -10 dBm at 915 MHz into IN gives about 0.1 V on the ADC at high impedance; 20 dB less, about 1 mV.
16. n7 with 5 V on its DC loop: 5 V on RF+DC, none on RF; RF to RF+DC within 1 dB from 2 MHz up.
17. n1: calibrate a NanoVNA on SHORT, OPEN, LOAD and THRU through a short cable, then read the 25 OHM standard:
    |S11| = 0.33 (9.5 dB of return loss) and a phase that turns with frequency (its 4.75 mm of line).

## What it is not

AMOD-N has no USB and no power of its own: n8 and n9 are dark unless the board is on a Pmod (n8 even when set
by hand: the PE43711 is an active switch array).  Its RF tiles are on
RF-MOD's stack-up and launch, so their 50 ohm lines are only as good as RF-MOD's (CostasLink's design); none has been
measured.
