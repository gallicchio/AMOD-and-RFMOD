# AMOD and RF-MOD: the plan

Three boards of 20 x 20 mm tiles, one circuit to a tile with its own SMA jacks, its schematic and
its expected response printed beside it, for the FPGA tutorial's converters
(github.com/gallicchio/icepi-zero-dac-adc, Appendix D).  This file is the design's plan and its
decision record; `CLAUDE_CODE_CHAT.md` is the conversation; the generators under `scripts/` and
`boards/` are the design.  Numbers quoted here from the build are checked by `scripts/gen_docs.py`.

| board | what | layers | cells | jacks |
|---|---|---|---|---|
| **AMOD-P** | passive blocks: pads, RC and LC filters, resonators, a crystal, a clipper, a tapped delay line, LEDs, an AM loopstick | 2 | 16 | 27 |
| **AMOD-A** | active blocks on USB-C power: gain blocks, an HF LNA, Johnson noise, a one-pin delta-sigma ADC, a 74HC4046 PLL, a heater, a mixer, light, 40 kHz ultrasound, audio | 4 | 16 | 21 |
| **RF-MOD** | 915 MHz, 2.4 GHz and a stretch to 5.8 GHz: printed antennas, filters, an LNA, a 2.4 GHz front end, two mixers, two synthesizers, a gain block, a TRF3722 quadrature transmitter | 4 | 16 | 26 |

Status (2026-10-25 01:05): decided, planned, parts stock-checked; the generators being written,
AMOD-P first.  See section 10.

## 1. The idea in one paragraph

The NanoVNA's RF demo kit is a 10 x 10 cm board of eighteen numbered circuits, each soldered in with
its own connectors and its expected plot printed beside it.  Nothing like it exists for DC to
30 MHz, audio, ultrasound and light, where the tutorial's converters live, nor cheaply for the ISM
bands above.  So: a 100 x 100 mm board (the cheapest fabrication tier) of sixteen 20 x 20 mm
cells, each cell one circuit, every port an SMA jack that a short cable takes to the
ECP5-2ADC-2DAC board's DAC OUT or ADC IN (or the Icepi Zero's module), and the board itself says
what each tile is, how it is wired and what to expect.  A student points at a square, cables it,
measures it, and checks the answer on the board.

## 2. What was decided, and what changed from Appendix D (with the reasons)

Appendix D's "Decided here, not to be reopened without a reason" list stands except where a
reason is given below.

- **Vertical SMA jacks (BWSMA-KE-Z001, LCSC C496549), not the right-angle BWSMA-KWE-Z001.**
  A right-angle jack's barrel at an interior tile has nowhere to go: 10 mm of barrel over the
  neighbouring tile, its nut over the neighbour's parts.  The alternative, a ring of tiles round the
  edge with every barrel pointing out, holds twelve single cells and none of the double ones the
  boards need (AMOD-A alone wants 16 cells).  The vertical jack (6.5 mm square, 13.5 mm tall,
  0 to 6 GHz, 500 cycles, $0.40, 113 k in stock on 2026-10-25) sits in any corner of any cell,
  cables rise from the board, and the same 5-pin land pattern family and ENIG launch rules apply.
  "SMA, not U.FL" stands; the part number changes.
- **A 4 x 4 grid of 20 mm cells with 1.5 mm gutters, 7.75 mm margins** (the geometry of the Appendix
  D sketches): cell (c, r) at x = 7.75 + 21.5 c, y = 7.75 + 21.5 r, y down from the top-left.  The
  margins hold the M3 holes (4 mm in from the corners), the identity text along the top, the Pmod
  plug at the left end of the bottom edge, and the USB-C on the right edge.
- **Jack slots.** A jack sits 4.75 mm in from a cell's edges at any of its four corners; a
  two-cell tile also has a slot at the middle of its top and bottom edges.  That makes every pair
  of jacks on the board at least 11.0 mm apart (a cable's nut and two fingers) whatever the
  neighbours do, with no case analysis: adjacent corners of one cell are 10.5 + 0.5, facing corners
  across a gutter 2 x 4.75 + 1.5 = 11.0.  The jack's 6.5 mm body stays inside its cell.
- **Every two-port tile has IN at its top-left slot and OUT at its top-right slot**, the signal
  flowing left to right along a line under the jacks, shunts hanging down from it, the plot and the
  legend in the bottom band.  One relation for every tile ("labels in a row stand alike"), all the
  jacks of a row of tiles in one line, and the whole lower half of each cell free for the circuit.
  Tiles with three jacks are 40 x 20 mm (slots TL, TM, TR); the delay line (five) uses TL, TM, TR,
  BL, BR.
- **The silkscreen is the schematic**, as on the op-amp board: each wire of a tile is laid as
  copper and drawn on the silkscreen, clipped round pads and bodies, so the picture cannot
  disagree with the netlist.  Passive tiles are outlined with a thin line; powered tiles with a
  thick frame whose title says the supply, a slide switch that powers the tile (a P-FET on the
  +5 V rail; the 3.3 V tiles of RF-MOD through their own LDO's enable), and a green LED that says it
  is alive.  A switch rated 50 mA cannot carry a synthesizer's 144 mA, so it only drives the gate.
- **Layers.** AMOD-P is two layers (parts and the drawn wires on top, one unbroken ground plane on
  the back).  AMOD-A and RF-MOD are four layers on JLCPCB's JLC04161H-7628 stack-up (L1 parts and
  signals, L2 solid ground, L3 the rails as pours, L4 ground fill with the Pmod and SPI lines and the
  back-side text), because the 40 dB HF amplifier, the Johnson-noise amplifier and the RF lines
  want a ground plane one prepreg under them and the rails off the signal layer.
- **Three op amps on AMOD-A, not one:** the OPA2810 (140 MHz GBW, 27 V, FET input: the gain blocks,
  the transimpedance amplifier, the ultrasound receiver), the OPA1612 (1.1 nV/rtHz: Johnson noise
  and the microphone), and the OPA847 (0.85 nV/rtHz, 3.9 GHz GBW, decompensated: the one HF LNA that
  does 40 dB from 1 to 30 MHz with a 3 dB noise figure in a single stage).  One of each costs
  $2.70 of feeder loading; an OPA2810 at x100 would be a 1.4 MHz amplifier and an OPA1612 x100 a
  400 kHz one.
- **The mixers.** The LTC5510 (R7, R8) had 35 in stock on 2026-10-25 and its fallback, the AD8342,
  36.  Two boards need four; the shelf covers the order with a thin margin, so the LTC5510 stays
  with a Digi-Key consignment fallback (ADI's own stock is deep) applied only if the shelf is short
  on the day, as CostasLink's release does.  The two chips have different footprints (QFN-16 4 x 4
  and 3 x 3), so the AD8342 is not a drop-in: it is named here as the design alternative, not drawn.
- **R2 and R4 (the 2.45 GHz LTCC and the 915 MHz SAW filters) share one cell** with four jacks at
  its four corners; the parts are 2 x 1.2 mm and 1.4 x 1.1 mm.  **R6 (RFX2401C) is one cell** with
  three jacks (TL, TR, BR).  That frees the two cells the **TRF3722 tile (R13)** needs: a PLL, VCO
  and I/Q modulator to 4.2 GHz with I, Q and RF OUT jacks and its own 25 MHz from R9.
- **The 74HC4046.** The CD74HC4046AM (C1519916) had 91 in stock; the CD4046BM (C7432285, 4,889)
  has the same SOIC-16 pinout and a 1.3 MHz VCO.  The tile is drawn for the HC part, with the
  CD4046 as the order-day alternate on the same footprint.
- **The TMP36 is out of stock; the TMP235A4 (C2868809, SOT-23, 10 mV/K + 500 mV, the same transfer
  function) takes its place** on A8.
- **P9 is a 455 kHz ceramic resonator (two-terminal), not a three-terminal IF filter**: JLCPCB
  stocks no 455 kHz filter and several resonators.  In series between the jacks it passes at its
  series resonance and blocks at its parallel one a few kHz above: the Q measurement of 4.02 and
  4.03 on a part with a Q of a few hundred, between the LC (P4) and the quartz (P8).
- **P4's trimmer capacitor becomes switched capacitors** (JLCPCB's only SMD trimmers are 0.6 mm
  parts with no stock): 220 pF fixed with 47 pF and 100 pF on a 2-way DIP switch, so the
  resonance steps between about 0.85 and 1.0 MHz.
- **Hand-fitted parts plug in; nothing is soldered by hand.**  P13's ferrite-rod coil goes in a
  3-way screw terminal (coil ends and tap) with its tuning capacitors on a 4-way DIP switch and
  two slots for a cable tie to hold the rod; A11's 40 kHz transducers plug into 1 x 5 pin sockets
  (pins 1 and 5 are 10.16 mm apart, the transducers' 10.0 mm leads flex the rest); A12's 20 mm
  speaker and A10's external laser module go in 2-way screw terminals, the electret microphone in a
  2-way socket.  JLCPCB stocks none of these transducers; the lab has them.
- **The Pmod plug is the PZ254R-12-12P (C492434), a 2 x 6 right-angle male header** at the left
  end of the bottom edge, its pins past the edge, so the host's second socket 0.9 inch to the
  right stays free.  Pin k is pad 2k-1 and pin k+6 is pad 2k in KiCad's numbering (the ECP5
  board's lesson): IO1-4 on Pmod 1-4, IO5-8 on 7-10, ground 5 and 11, 3.3 V 6 and 12.  Nothing on
  these boards is powered from the Pmod's 3.3 V except the 3.3 V logic references that need
  exactly the host's level.
- **An Icepi Zero adapter with a Pmod is feasible and is a fourth, small board** (section 9): the
  existing adapter uses 18 of the header's 28 GPIO lines; the ten free ones (header pins 3, 5, 8,
  10, 22, 27, 28, 36, 38, 40) are more than a Pmod's eight.  It is last in the order of work.

## 3. The tile grid and the jack rule

```
  x: 0      7.75   27.75 29.25  50.75 52.25  72.25 73.75  92.25  100
  y: 7.75   +------+-----+------+-----+------+-----+------+   row 0
            | (0,0)|     | (1,0)|     | (2,0)|     | (3,0)|
     27.75  +------+     +------+     +------+     +------+
     29.25  +------+     +------+     +------+     +------+   row 1
      ...
  jack slots in a cell (local mm):  TL (4.75, 4.75)  TR (15.25, 4.75)  BL (4.75, 15.25)  BR (15.25, 15.25)
  in a two-cell tile also:          TM (20.75, 4.75)  BM (20.75, 15.25)
  M3 holes at (4, 4), (96, 4), (4, 96), (96, 96); identity text in the top margin;
  Pmod plug body at x = 3.3 .. 18.5 in the bottom margin, pins past y = 100; USB-C on the right edge.
```

Every jack slot is 11.0 mm or more from every other slot on the board; `scripts/geometry.py`
asserts it for each board's tile list.

## 4. AMOD-P: the passive board

| cell | # | tile | jacks | the circuit (50 ohm unless said) | expected |
|---|---|---|---|---|---|
| (0,0) | P1 | pi attenuator, -20 dB | IN, OUT | 61.9 / 249 / 61.9 ohm | flat -20 dB |
| (1,0) | P2 | RC low-pass | IN, OUT (hi-Z) | 1 k series, 1 nF shunt: 159 kHz | -3 dB at 159 kHz, -20 dB/decade |
| (2,0) | P3 | RC high-pass | IN, OUT (hi-Z) | 1 nF series, 1 k shunt: 159 kHz | the mirror image |
| (3,0) | P4 | series RLC | IN, OUT | 100 uH, 220 pF + 47 / 100 pF on a 2-way DIP: 1.07 / 0.97 / 0.90 / 0.83 MHz, Q about 6 between 50 ohm ports | a peak you can move |
| (0,1) | P5 | LC low-pass 9 MHz | IN, OUT | 5th-order Butterworth pi: 220 pF, 1.5 uH, 680 pF, 1.5 uH, 220 pF | -3 dB at 9 MHz, -30 dB at 18 |
| (1,1) | P6 | LC low-pass 100 kHz | IN, OUT | 5th-order pi: 22 nF, 120 uH, 3 x 22 nF, 120 uH, 22 nF (C0G 1206) | -3 dB at 100 kHz |
| (2,1) | P7 | LC band-pass 4.7-7.8 MHz | IN, OUT | 3rd-order Butterworth: series 2.7 uH + 270 pF, shunt 2.2 nF + 330 nH, series 2.7 uH + 270 pF | Chapter 6's band |
| (3,1) | P8 | 4 MHz crystal | IN, OUT | the crystal in series, with 33 pF in series shorted by DIP 1 and 10 pF across it by DIP 2 | a spike at 4.000 MHz that moves 1 kHz |
| (0,2) | P9 | 455 kHz ceramic resonator | IN, OUT | the resonator in series | pass at 455, block a few kHz up |
| (1,2) | P10 | diode clipper | IN, OUT (hi-Z) | 1 k series, 1N4148W pairs to ground; DIP 1 shorts the second diode of each leg (0.7 V) else 1.4 V | flat tops |
| (2,2)-(3,2) | P11 | delay line, 400 ns | IN, 100 ns, 200 ns, 300 ns, OUT | 20 sections of 1.0 uH and 390 pF (Z0 50 ohm, 20 ns each, cut-off 16 MHz); taps through 470 ohm | an echo every 100 ns; dispersion near 16 MHz |
| (0,3) | P12 | LEDs, four colours | IN | 100 ohm, then red 630 / yellow 596 / green 525 / blue 469 nm on a 4-way DIP | V_f against wavelength: Planck |
| (1,3)-(3,3) | P13 | AM loopstick | OUT | 3-way terminal for the rod's coil and tap, 47 / 100 / 220 / 470 pF on a 4-way DIP across the coil, the jack on the tap; cable-tie slots | a station, with A4 |

Every jack carries a test loop (RH-5019) on its node beside it, and four ground loops stand in the
margins.  27 SMA jacks, 5 DIP switches, one terminal block.  Section 7 has the parts.

## 5. AMOD-A: the active board

Rails: +5 V from USB-C (5.1 k CC pull-downs: 1.5 A; a 2 A PTC, an SMAJ5.0A TVS, a 100 uF polymer),
-5 V from an LM2664 charge pump (40 mA; the op-amp tiles draw 10 mA each), +3.3 V from a TPS7A2033
(the comparator and anything that meets the FPGA).  Every powered tile has its own slide switch,
P-FET and green LED; the -5 V rail is not switched (an op amp with V+ open draws nothing).

| cell | # | tile | supply | jacks | Pmod | the circuit as built (rev A, 2026-10-25) |
|---|---|---|---|---|---|---|
| (0,0) | A2 | gain x10, 14 MHz | +-5 | IN (50 ohm), OUT | | one OPA810 non-inverting, 1.1 k / 10 k, 49.9 ohm out: x10 into a high impedance, x5 into 50 ohm (the plan's two-stage x3.16 did not fit a cell beside the switch) |
| (1,0) | A3 | gain x100, 1.4 MHz | +-5 | IN (50 ohm), OUT | | the same stage with 100 ohm / 10 k |
| (2,0) | A4 | HF LNA, 30 MHz | +-5 | IN (50 ohm), OUT | | OPA847 at x101 (1 k / 10 ohm), the feedback node carried through the NC pin 1; no loop |
| (3,0) | A5 | Johnson noise x100 | +-5 | OUT | | LT6230 (1.1 nV/rtHz, SOT-23-6) at x100 in the A2 geometry; 10 k or 1 k by a 2-way DIP, or your own resistor in a 1 x 2 socket (the OPA1612 two-stage x1000 and a 4-way DIP did not fit) |
| (0,1) | A6 | delta-sigma ADC | +3.3 | IN (10 k) | 1, 2 | TLV3501 against a 1.65 V reference; 10 k / 10 k / 10 nF integrator; the FPGA's bit in on Pmod 1, the comparator's bit out on Pmod 2 and a loop |
| (1,1) | A7 | PLL 4046 | +5 | IN (1 k), VCO OUT | | CD74HC4046A: 100 n / 1 k into SIGin, R1 10 k, C1 1 nF (about 100 kHz), PC2 through 10 k / 100 n into VCOin, VCO OUT through 470 ohm (fixed values, no DIP; no loops: probe pins 9 and 13) |
| (2,1) | A8 | heat | +5 | TEMP OUT | 3 | two 15 ohm 2512 in series (0.83 W) switched by an AO3400 from Pmod 3 (10 k pull-down); a TMP235 (10 mV/K + 500 mV) to the jack (the NTC divider did not fit) |
| (3,1) | A1 | power | | | | USB-C on the right edge, 5.1 k CC pull-downs, 2 A PTC, SMAJ5.0A, 2 x 10 uF, LM2664 for -5 V, TPS7A2033 for +3.3 V, green +5 V and red -5 V LEDs in the margin, a 1 x 5 socket along the top edge (+5, G, -5, G, 3.3) |
| (0,2)-(1,2) | A9 | mixer MC1496 | +-5 | RF IN, LO IN, IF OUT | | the Gilbert cell on +-5 V: 51 ohm inputs, carrier pair at 2.5 V, 1 mA per side, 1.5 k loads, IF single-ended through 100 n (1.5 k source: a high-impedance input); no null trimmer |
| (2,2)-(3,2) | A10 | light | +-5 | PD OUT, DRIVE IN | 4 | OPA810 voltage-to-current source (22 ohm: 45 mA per volt) into a side-view red LED at the board's right edge, a 2N7002 from Pmod 4 blanks it; PD70-01C (5 V reverse) into an OPA810 transimpedance stage, 10 k / 10 pF, 49.9 ohm out (the laser terminal and its DIP did not fit) |
| (0,3)-(1,3) | A11 | 40 kHz ultrasound | +-5 | RX OUT | 5, 6 | DRV8837 H-bridge from Pmod 5 and 6 into a transducer in pins 1 and 5 of a 1 x 5 socket; the second transducer through 10 n / 3.9 k into the A2 geometry at x100; the Pmod plug hangs off this tile's bottom edge |
| (2,3)-(3,3) | A12 | audio | +-5 | AUDIO IN, MIC OUT | 7 | PAM8302A into a speaker on a screw terminal, fed by AUDIO IN through 1 u and by the one-bit stream on Pmod 7 through 10 k / 10 n; an electret in a 1 x 2 socket (2.2 k bias) through 1 u into the A2 geometry at x100 (no 3.5 mm jack) |

The Pmod lines: A6 two (1, 2), A8 one (3), A10 one (4), A11 two (5, 6), A12 one (7); 8 is unused.
The switched rail of every tile comes from its own slide switch and P-FET; -5 V (40 mA from the
LM2664) is shared and unswitched.

## 6. RF-MOD: 915 MHz, 2.4 GHz, a stretch to 5.8 GHz

| cell | # | tile | supply | jacks | the circuit |
|---|---|---|---|---|---|
| (0,0)-(1,0) | R1 | 915 MHz antenna | | ANT | TI DN023 inverted-F along the top edge, bare board on every layer under it, a pi matching network (0 ohm fitted) to the jack |
| (2,0) | R2 + R4 | the two filters | | IN, OUT (2.45 GHz, top); IN, OUT (915 MHz, bottom) | Murata LFB212G45SG8A127 between TL and TR; B39921B2672P810 SAW between BL and BR |
| (3,0) | R3 | 2.4 GHz antenna | | ANT | TI AN043 meandered inverted-F in the corner, bare board |
| (0,1) | R5 | LNA | +5 | IN, OUT | QPL9547, 0.1-6 GHz, 19.5 dB, its datasheet's bias network |
| (1,1) | R6 | 2.4 GHz front end | +3.3 | TX IN, ANT, RX OUT | RFX2401C; TXEN and RXEN from the Pmod (or a DIP) |
| (2,1) | R12 | gain block | +8 | IN, OUT | GALI-84+, 7 V through its bias resistor from the 8 V boost |
| (3,1) | R9 | power and reference | | REF IN/OUT | USB-C on the right edge, PTC, TVS, polymer; +5 V RF through a bead; 3.3 V LDO for the TCXO; MT3608 boost to 8 V; TC32H4 25 MHz TCXO buffered to the three synthesizers and the jack; a jumper picks the TCXO or the jack as the reference |
| (0,2)-(1,2) | R7 | TX mixer | +5 | IF IN, LO IN, RF OUT | LTC5510 up-converting: its wideband upmixer circuit |
| (2,2)-(3,2) | R8 | RX mixer | +5 | RF IN, LO IN, IF OUT | LTC5510 down-converting to an IF of a few MHz: its output network chosen for 1-30 MHz |
| (0,3) | R10 | TX synthesizer | +3.3 | OUT A, OUT B | MAX2871, CostasLink's circuit: the loop filter for 25 MHz / fPFD, both outputs through 27 nH and DC blocks |
| (1,3) | R11 | RX synthesizer | +3.3 | OUT A, OUT B | the same |
| (2,3)-(3,3) | R13 | quadrature transmitter | +3.3 / +5 | I IN, Q IN, RF OUT | TRF3722: PLL + VCO + I/Q modulator to 4.2 GHz; I and Q from the DACs through the datasheet's bias network |

Pmod: SCLK, SDATA, LE_TX (R10), LE_RX (R11), LE_IQ (R13), MUXOUT (R10, R11 and R13's lock
detects wire-ORed through diodes), TXEN and RXEN (R6).  Eight.

## 7. Parts and sourcing

JLCPCB's shelf for everything machine-placed, queried through `scripts/jlc_api.py` on
2026-10-25 00:45-01:00 PDT (the cache keeps each answer's time).  `scripts/parts.py` is the one
table; the schematics, the BOMs, the cost estimate and the silkscreen legends read it, and the
fab check compares every code's JLCPCB description with the value and package before a release.
The chips, with stock that day:

| part | code | $ (1-9) | stock | used on |
|---|---|---|---|---|
| BWSMA-KE-Z001 vertical SMA | C496549 | 0.40 | 112,911 | every jack |
| RH-5019 test loop | C5199800 | 0.10 | 245,451 | every node worth a hook |
| KingTek DSIC02 / 04 / 06 DIP switches | C54949 / C54950 / C54952 | 0.39 / 0.49 / 0.57 | 12,716 / 2,973 / 2,562 | the variants |
| MSK12C02 slide switch | C431540 | 0.05 | 194,123 | each powered tile's switch |
| AO3401A (P, Basic) / AO3400A (N, Basic) / 2N7002 (Basic) | C15127 / C20917 / C8545 | 0.10 / 0.09 / 0.02 | plenty | power gating, the heater, the laser gate |
| OPA2810IDR | C1849413 | 2.54 | 3,707 | A2, A3, A10, A11 |
| OPA1612AIDR | C94590 | 1.34 | 26,345 | A5, A12 |
| OPA847IDR | C2870028 | 5.65 | 1,466 | A4 |
| TLV3501AIDBVR | C193413 | 1.92 | 5,079 | A6 (and A11's TX comparator) |
| CD74HC4046AM (alt. CD4046BM/TR C7432285, 4,889) | C1519916 | 1.37 | 91 | A7 |
| MC1496DR2G | C7295 | 0.25 | 14,255 | A9 |
| TMP235A4DBZR | C2868809 | 0.32 | 13,806 | A8 |
| DRV8837DSGR | C39159 | 0.26 | 85,042 | A11 |
| PAM8302AASCR | C113367 | 0.31 | 12,021 | A12 |
| PD70-01C/TR7 | C131196 | 0.21 | 77,545 | A10 |
| LM2664M6X/NOPB | C108573 | 0.33 | 164,185 | A1 (-5 V) |
| TPS7A2033PDBVR | C2862740 | 0.21 | 155,681 | A1, R9, R10, R11, R13 |
| LP5907MFX-3.3 | C23380874 | 0.14 | 12,279 | R9 (the TCXO) |
| MT3608 | C84817 | 0.10 | 91,494 | R9 (8 V for the GALI-84+) |
| TYPE-C-31-M-12 USB-C | C165948 | 0.19 | 324,740 | A1, R9 |
| MF-MSMF200-2 PTC, SMAJ5.0A TVS | C210837, C113952 | 0.07, - | 9,923 | A1, R9 |
| PZ254R-12-12P Pmod plug | C492434 | 0.10 | 4,327 | AMOD-A, RF-MOD |
| KF301-5.0-2P / -3P terminals | C474881 / C474882 | 0.10 / 0.14 | 84,342 / 27,437 | P13, A10, A12 |
| PZ254V-11-05P 1 x 5 header (the transducer sockets are the female of it: see section 10) | C492404 | 0.03 | 168,994 | A11 |
| MAX2871ETJ+T | C7458627 | 9.97 | 3,120 | R10, R11 |
| QPL9547TR7 | C5367093 | 6.70 | 5,070 | R5 |
| LTC5510IUF#TRPBF (fallback: Digi-Key; design alternative AD8342 C182567, 36) | C688646 | 14.98 | 35 | R7, R8 |
| RFX2401C | C19213 | 0.97 | 58,226 | R6 |
| GALI-84+ | C3193261 | 4.22 | 144 | R12 |
| TRF3722IRGZR | C1850395 | 8.63 | 2,218 | R13 |
| B39921B2672P810 SAW 915 MHz | C1518004 | 0.56 | 6,411 | R4 |
| LFB212G45SG8A127 2.45 GHz | C341536 | 0.19 | 3,940 | R2 |
| TC32H4-25.000-33GNDTNL TCXO | C5119013 | 1.58 | 1,240 | R9 |
| X49SM4MSD2SC 4 MHz crystal | C13774 | 0.11 | 33,932 | P8 |
| KCR455E 455 kHz resonator | C366989 | 0.11 | 504 | P9 |
| 1N4148W (Basic) | C81598 | 0.01 | 4.1 M | P10, clamps |
| LEDs 0805: NCD0805R1 red (Basic), KT-0805Y yellow (Basic), KT-0805G green (Basic), KT-0805B blue | C84256, C2296, C2297, C2293 | 0.01-0.02 | plenty | P12, the rail and tile LEDs |
| E6C1204URAC1UDA side-view red LED | C375479 | 0.02 | 12,614 | A10 |
| GMI6050-2C38DB electret (SMD, 6 mm) | C233921 | 0.33 | 985 | A12 (fitted; the socket is the alternative) |
| PJ-320A 3.5 mm jack | C2884926 | 0.14 | 9,322 | A12 |
| HNTC0805-103F3380FB 10 k NTC | C49247661 | 0.05 | 4,464 | A8 |
| 2512 15 ohm 1 W | (see parts.py) | 0.03 | | A8 |

Passives: 0805 on AMOD-P and AMOD-A (a student can probe and rework them), 0603 on the delay line
(forty parts in two cells) and on RF-MOD, 0402 only where an RF chip's land pattern asks.  C0G
wherever a value sets a frequency.  Resistors from the Uniroyal 0805W8F series (Basic) wherever
the value exists there.

Not stocked at JLCPCB, so plugged in by the lab: the 40 kHz transducers (TCT40-16T/R), a 20 mm
8 ohm speaker, a 650 nm laser module, the ferrite rod and its coil.

## 8. Build system

`./make.py [--board amod_p|amod_a|rf_mod|all] [--stage ...]` builds one board or all: the project
library (footprints drawn or vendored, 3D models), the simulations (the expected plots the silk
prints, `sim/`), the schematic (`boards/<board>.py` describes the tiles; `scripts/gen_sch.py`
draws one sheet per board with a block per tile), ERC and the netlist, the circuit checks
(`scripts/check_circuit.py`: every tile's design equation against the netlist's values), the
board (`scripts/gen_pcb.py`: the grid, the jacks, the drawn wires as copper and silk, the planes,
the frames, the legends, the QR code), DRC with parity, the fab package (`scripts/gen_outputs.py`,
`scripts/check_outputs.py`) and the documents (`scripts/gen_docs.py`).  `--clean` removes what it
makes.  Everything a reviewer needs is committed, so nothing has to be built to read the design.

```
make.py                   one command, all three boards or one
scripts/geometry.py       the cell grid, the jack slots and the 11 mm rule
scripts/parts.py          every part: value, footprint, LCSC code, stock, JLCPCB rotation
scripts/tiles.py          the Tile class: parts, nets, the drawn wires, the legend, the plot
boards/amod_p.py ...      each board's tiles and where they sit
scripts/gen_*.py          footprints, models, project, schematic, pcb, outputs, docs
scripts/check_*.py        the circuit, the schematic sheet, the fab package
sim/                      the tiles' responses (numpy / ngspice), which the silkscreen plots
out/<board>/              gerbers, BOM, CPL (native and JLCPCB), prints, PLACEMENT_CHECKS
docs/                     MANUFACTURING, HANDBOOK, DESIGN_NOTES, images, history
```

## 9. The Icepi Zero adapter with a Pmod (the fourth board)

The adapter in the tutorial repository (`adapter_board/`) takes 18 of the Icepi Zero's 28 header
GPIO lines (pins 7, 11-13, 15, 16, 18, 19, 21, 23, 24, 26, 29, 31-33, 35, 37).  The ten it leaves
(3, 5, 8, 10, 22, 27, 28, 36, 38, 40) give a Pmod its eight with two spare, if the Icepi Zero
routes all of them to FPGA balls (to be read off its schematic; the LiteX platform file lists
them).  The board: the existing 65 x 30 mm adapter plus a 2 x 6 right-angle Pmod socket on its
edge with 33 ohm series resistors and the 3.3 V from the header, and the pin table generated into
the tutorial's `.lpf`.  Last in the order of work; it is a day's board, not a night's.

## 10. Order of work and status

1. Plan, decisions, stock (this file): done 2026-10-25 01:05.
2. The framework: geometry, parts, the Tile class, the schematic and board generators: done 02:00
   (the grid router and the back-wire machinery came with AMOD-A).
3. AMOD-P end to end: done 03:40 (ERC 0, DRC 0, the fab package through every check, $16.97 of parts).
4. AMOD-A: done 08:30 (twelve tiles, four layers, ERC 0, DRC 0, the fab package through every check,
   $45.97 of parts; the handbook and manufacturing notes generated).  The plan's tiles were trimmed to
   fit 20 mm cells beside a switch and a FET: section 5's table says what was built, the handbook's
   DOA list what was dropped.
5. RF-MOD: the RF rules (CPWG lines on JLC04161H-7628, CostasLink's launch, via fences, the
   antennas' keep-outs), the synthesizers' circuit from CostasLink.
6. The Icepi adapter.
7. The design-review brief, the author's own review, then the rounds.

Open items that are not Jason's to answer are decided in this file as they come up and logged in
the chat; the ones that are his go in `QUESTIONS.md`.
