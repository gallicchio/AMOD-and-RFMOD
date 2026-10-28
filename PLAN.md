# AMOD and RF-MOD: the plan

Three boards of 20 x 20 mm tiles, one circuit to a tile with its own SMA jacks, its schematic and
its expected response printed beside it, for the FPGA tutorial's converters
(github.com/gallicchio/icepi-zero-dac-adc, Appendix D).  This file is the design's plan and its
decision record; `CLAUDE_CODE_CHAT.md` is the conversation; the generators under `scripts/` and
`boards/` are the design.  Numbers quoted here from the build are checked by `scripts/gen_docs.py`.

| board | what | layers | cells | jacks |
|---|---|---|---|---|
| **AMOD-P** | passive blocks: pads, RC and LC filters, resonators, a crystal, a clipper, a tapped delay line, LEDs, an AM loopstick | 2 | 16 | 27 |
| **AMOD-N** | the second passive board (section 11, Prompt 17): calibration standards, two splitters, a stub, a low-pass, a detector, a bias-T, a balun and a 1:4 transformer; a step attenuator (by hand or the FPGA) and an oscillator on the Pmod's 3.3 V | 4 | 16 | 28 |
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
  plug at the left end of the bottom edge, and the USB-C on the right edge.  **Changed 2026-10-25
  (Prompts 2 and 5):** AMOD-A and RF-MOD have no mounting holes.  The corrected Pmod plug fills the
  bottom-left corner, a board plugged into a host is held by its plug, and four stick-on rubber feet
  (8 mm, circled on the back) stand where the holes were.  AMOD-P keeps its M3 holes.
- **Jack slots.** A jack sits 4.75 mm in from a cell's edges at any of its four corners; a
  two-cell tile also has a slot at the middle of its top and bottom edges.  That makes every pair
  of jacks on the board at least 11.0 mm apart (a cable's nut and two fingers) whatever the
  neighbours do, with no case analysis: adjacent corners of one cell are 10.5 + 0.5, facing corners
  across a gutter 2 x 4.75 + 1.5 = 11.0.  The jack's 6.5 mm body stays inside its cell.
- **Every jack on every board stands in a checkerboard** (Prompt 2 for RF-MOD, Prompt 12 for AMOD-P and AMOD-A:
  "spread the jacks out away from each other, even away from jacks on other tiles").  Each cell uses only its
  top-left and bottom-right slots: IN top-left, OUT bottom-right, a two-cell tile's third jack at its right cell's
  top-left.  Two jacks in one cell are then 14.85 mm apart and two across a gutter 15.2 mm, against 10.5 and 11.0
  for adjacent slots.  `scripts/geometry.py` asserts 14.3 mm for every pair on each board.  The signal runs on the
  cell's anti-diagonal: the parts fill the top-right and bottom-left quarters the jacks leave, with the power
  header in the bottom-left.  Two parts changed so that they fit: a4's OPA847 went from the SOIC-8 to the
  SOT-23-6, and a7's 4046 from TI's SOIC-16 to Nexperia's TSSOP-16.  p8's crystal and p9's resonator stand at 45
  degrees between their jacks, and p8's jacks sit 0.5 mm further out (slots TLo, BRo).
- **Rev A's first layout (until Prompt 12) had IN at the top-left slot and OUT at the top-right slot**, the signal
  flowing left to right along a line under the jacks.  It kept every row's jacks in one line but put them 10.5 mm
  apart, too close for two cables and fingers.
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
- **The mixers.** The LTC5510 (r7, r8) had 35 in stock on 2026-10-25 and its fallback, the AD8342,
  36.  **As built: the ADL5350** (C206667, 2,036 in stock, $5.64), a passive GaAs mixer with its own LO
  buffer, LF to 4 GHz, 6.8 dB of loss, +25 dBm IIP3, 3 V at 19 mA.  Its RF and IF pins are one node; a
  200 MHz crossover (15 pF / 47 nH each way) splits them, so one tile serves 915 MHz and 2.4 GHz with
  any IF the ADC reaches, in either direction.
- **r2 and r4 (the 2.45 GHz LTCC and the 915 MHz SAW filters) share one cell** with four jacks at
  its four corners; the parts are 2 x 1.2 mm and 1.4 x 1.1 mm.  **R6 (RFX2401C) is one cell** with
  three jacks (TL, TR, BR).  That frees the two cells the **TRF3722 tile (r13)** needs: a PLL, VCO
  and I/Q modulator to 4.2 GHz with I, Q and RF OUT jacks and its own 25 MHz from r9.  **As built
  (section 6):** r2 and r4 have a cell each (IN top-left, OUT bottom-right); R6, r13, the QPL9547
  LNA and the printed antennas are not on rev A.  Prompt 4 asked for the board to be filled with
  tiles that work together, so the cells went to a second gain block, two mixers, two synthesizers
  and a splitter: one complete link, transmitter and receiver, on one reference.  (Prompt 15 made the splitter a diode-ring
  mixer and brought the synthesizer's second output, RFOUTA-, to a jack.)
- **The 74HC4046.** The CD74HC4046AM (C1519916) had 91 in stock; the CD4046BM (C7432285, 4,889)
  has the same SOIC-16 pinout and a 1.3 MHz VCO.  The tile is drawn for the HC part, with the
  CD4046 as the order-day alternate on the same footprint.
- **The TMP36 is out of stock; the TMP235A4 (C2868809, SOT-23, 10 mV/K + 500 mV, the same transfer
  function) takes its place** on a8.
- **p9 is a 455 kHz ceramic resonator (two-terminal), not a three-terminal IF filter**: JLCPCB
  stocks no 455 kHz filter and several resonators.  In series between the jacks it passes at its
  series resonance and blocks at its parallel one a few kHz above: the tutorial's Q measurement
  on a part with a Q of a few hundred, between the LC (p4) and the quartz (p8).
- **p4's trimmer capacitor becomes switched capacitors** (JLCPCB's only SMD trimmers are 0.6 mm
  parts with no stock): 220 pF fixed with 47 pF and 100 pF on a 2-way DIP switch, so the
  resonance steps between about 0.85 and 1.0 MHz.
- **Hand-fitted parts plug in; nothing is soldered by hand.**  p13's ferrite-rod coil goes in a
  3-way screw terminal (coil ends and tap) with its tuning capacitors on a 4-way DIP switch and
  two slots for a cable tie to hold the rod; a11's 40 kHz transducers plug into 1 x 5 pin sockets
  (pins 1 and 5 are 10.16 mm apart, the transducers' 10.0 mm leads flex the rest); a12's 20 mm
  speaker and a10's external laser module go in 2-way screw terminals, the electret microphone in a
  2-way socket.  JLCPCB stocks none of these transducers; the lab has them.
- **The Pmod plug is the PZ254R-12-12P (C492434), a 2 x 6 right-angle male header** at the left
  end of the bottom edge, its pins past the edge, so the host's second socket 0.9 inch to the
  right stays free.  Pin k is pad 2k-1 and pin k+6 is pad 2k in KiCad's numbering (the ECP5
  board's lesson): IO1-4 on Pmod 1-4, IO5-8 on 7-10, ground 5 and 11, 3.3 V 6 and 12.  **Caught
  2026-10-25:** the plug's footprint is JLCPCB's drawing, whose pad 1 sits at the other end of the
  row nearest the body (its pad p is KiCad's 13 - p).  The first layout applied KiCad's rule to it,
  which mirrored every line onto the host's ground and 3.3 V.  The plug moved two columns left (into
  the corner where a mounting hole was), the nets were renamed to the standard IO numbers, and
  `check_outputs.check_pmod` now maps every plug pad to its pin by position.  Nothing on
  these boards is powered from the Pmod's 3.3 V except the 3.3 V logic references that need
  exactly the host's level.
- **An Icepi Zero adapter with a Pmod is feasible and is a fourth, small board** (section 9): the
  existing adapter uses 18 of the header's 28 GPIO lines; the ten free ones (header pins 3, 5, 8,
  10, 22, 27, 28, 36, 38, 40) are more than a Pmod's eight.  Built: `icepi_adapter/`, 80 x 30 mm,
  four layers.

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
  in a tile of several cells:       TLk, BRk = cell k's TL and BR (TL1 = (26.25, 4.75), BR1 = (36.75, 15.25))
  p8 only:                          TLo (4.25, 4.25), BRo (15.75, 15.75): 0.5 mm further out, for the 45-degree crystal
  M3 holes at (4, 4), (96, 4), (4, 96), (96, 96) on AMOD-P; rubber feet at (5, 5), (95, 5), (95, 95),
  (5, 85) on AMOD-A and RF-MOD; identity text in the top margin; Pmod plug pads at x = 4.4 .. 17.1
  in the bottom margin (its body past y = 100); USB-C on the right edge.
```

As built, nearly every jack is at a cell's TL or BR (TLk or BRk in a tile of several cells).  The exceptions: p8's
TLo and BRo; TM on a9 (LO), R1 (P2), r10 and R11 (REF IN); TR on a5, a10 and a12, whose neighbours already leave
those jacks 14.3 mm or more from every other.  `scripts/geometry.py` asserts 14.3 mm between every pair of jacks on
each board; the closest pair on each board is 14.85 mm, the diagonal of one cell.

## 4. AMOD-P: the passive board

| cell | # | tile | jacks | the circuit (50 ohm unless said) | expected |
|---|---|---|---|---|---|
| (0,0) | p1 | pi attenuator, -20 dB | IN, OUT | 61.9 / 249 / 61.9 ohm | flat -20 dB |
| (1,0) | p2 | RC low-pass | IN, OUT (hi-Z) | 1 k series, 1 nF shunt: 159 kHz | -3 dB at 159 kHz, -20 dB/decade |
| (2,0) | p3 | RC high-pass | IN, OUT (hi-Z) | 1 nF series, 1 k shunt: 159 kHz | the mirror image |
| (3,0) | p4 | series RLC | IN, OUT | 100 uH, 220 pF + 47 / 100 pF on a 2-way DIP: 1.07 / 0.97 / 0.90 / 0.83 MHz, Q about 6 between 50 ohm ports | a peak you can move |
| (0,1) | p5 | LC low-pass 9 MHz | IN, OUT | 5th-order Butterworth pi: 220 pF, 1.5 uH, 680 pF, 1.5 uH, 220 pF | -3 dB at 9 MHz, -30 dB at 18 |
| (1,1) | p6 | LC low-pass 100 kHz | IN, OUT | 5th-order pi: 22 nF, 120 uH, 3 x 22 nF, 120 uH, 22 nF (C0G 1206) | -3 dB at 100 kHz |
| (2,1) | p7 | LC band-pass 4.7-7.8 MHz | IN, OUT | 3rd-order Butterworth: series 2.7 uH + 270 pF, shunt 2.2 nF + 330 nH, series 2.7 uH + 270 pF | Chapter 6's band |
| (3,1) | p8 | 4 MHz crystal | IN, OUT | the crystal in series, with 33 pF in series shorted by DIP 1 and 10 pF across it by DIP 2 | a spike at 4.000 MHz that moves 1 kHz |
| (0,2) | p9 | 455 kHz ceramic resonator | IN, OUT | the resonator in series | pass at 455, block a few kHz up |
| (1,2) | p10 | diode clipper | IN, OUT (hi-Z) | 1 k series, 1N4148W pairs to ground; DIP 1 shorts the second diode of each leg (0.7 V) else 1.4 V | flat tops |
| (2,2)-(3,2) | p11 | delay line, 400 ns | IN, 100 ns, 200 ns, 300 ns, OUT | 20 sections of 1.0 uH and 390 pF (Z0 50 ohm, 20 ns each, cut-off 16 MHz); taps through 470 ohm | an echo every 100 ns; dispersion near 16 MHz |
| (0,3) | p12 | LEDs, four colours | IN | 100 ohm, then red 630 / yellow 596 / green 525 / blue 469 nm on a 4-way DIP | V_f against wavelength: Planck |
| (1,3)-(3,3) | p13 | AM loopstick | OUT | 3-way terminal for the rod's coil and tap, 47 / 100 / 220 / 470 pF on a 4-way DIP across the coil, the jack on the tap; cable-tie slots | a station, with a4 |

Every jack carries a test loop (RH-5019) on its node beside it, and four ground loops stand in the
margins.  27 SMA jacks, 5 DIP switches, one terminal block.  Section 7 has the parts.

## 5. AMOD-A: the active board

Rails: +5 V from USB-C (5.1 k CC pull-downs: 1.5 A; a 2 A PTC, an SMAJ5.0A TVS, a 100 uF polymer),
-5 V from an LM2664 charge pump (40 mA; the op-amp tiles draw 10 mA each), +3.3 V from a TPS7A2033
(the comparator and anything that meets the FPGA).  Every powered tile has its own slide switch,
P-FET and green LED; the -5 V rail is not switched (an op amp with V+ open draws nothing).

| cell | # | tile | supply | jacks | Pmod | the circuit as built (rev A, 2026-10-25) |
|---|---|---|---|---|---|---|
| (0,0) | a2 | gain x10, 14 MHz | +-5 | IN (50 ohm), OUT | | one OPA810 non-inverting, 1.1 k / 10 k, 49.9 ohm out: x10 into a high impedance, x5 into 50 ohm (the plan's two-stage x3.16 did not fit a cell beside the switch) |
| (1,0) | a3 | gain x100, 1.4 MHz | +-5 | IN (50 ohm), OUT | | the same stage with 100 ohm / 10 k |
| (2,0) | a4 | HF LNA, 30 MHz | +-5 | IN (50 ohm), OUT | | OPA847 (SOT-23-6, DIS tied to +VS) at x101 (1 k / 10 ohm) in the a2 geometry; no loop |
| (3,0) | a5 | Doppler | +-5 | OUT | | a 1 x 3 socket (+5 V, IF, ground) for an HB100 10.525 GHz module on jumper wires; the IF through 1 uF (100 k to ground) into the a2 geometry at x101, 49.9 ohm out: 70 Hz per m/s (Prompt 13: the host has the Johnson-noise source this tile was) |
| (0,1) | a6 | delta-sigma ADC | +3.3 | IN (10 k) | IO8, IO7 | TLV3501 against a 1.65 V reference; 10 k / 10 k / 10 nF integrator; the FPGA's bit in on IO8, the comparator's bit out on IO7 and a loop |
| (1,1) | a7 | PLL 4046 | +5 | IN (1 k), VCO OUT | | 74HC4046A (Nexperia, TSSOP-16): 100 n / 1 k into SIGin, R1 10 k, C1 1 nF (about 100 kHz), PC2 through 10 k / 100 n into VCOin, VCO OUT through 470 ohm (fixed values, no DIP; no loops: probe pins 9 and 13) |
| (2,1) | a8 | heat | +5 | TEMP OUT | IO6 | two 15 ohm 2512 in series (0.83 W) in the top-left, switched by an AO3400 from IO6 (10 k pull-down); a TMP235 (10 mV/K + 500 mV) straight above the jack (the NTC divider did not fit) |
| (3,1) | a1 | power | | | | USB-C on the right edge, 5.1 k CC pull-downs, 2 A PTC, SMAJ5.0A, 2 x 10 uF, LM2664 for -5 V, TPS7A2033 for +3.3 V, green +5 V and red -5 V LEDs in the margin, a 1 x 5 socket along the top edge (+5, G, -5, G, 3.3) |
| (0,2)-(1,2) | a9 | mixer MC1496 | +-5 | RF IN, LO IN, IF OUT | | the Gilbert cell on +-5 V: 51 ohm inputs, carrier pair at 2.5 V, 1 mA per side, 1.5 k loads, IF single-ended through 100 n (1.5 k source: a high-impedance input); no null trimmer |
| (2,2)-(3,2) | a10 | impedance and I-V | +-5 | DRIVE IN, S OUT, DUT, X OUT | | DRIVE IN into the a2 geometry at x2: the driven node S (also out through 49.9 ohm on S OUT); a 4-way DIP picks 47, 470, 4.7 k or 47 k from S to X, the part under test from X to ground on DUT, an OPA810 follower to X OUT: Z = R X / (S - X), DC to a few MHz, and I-V curves to +-4 V and 40 mA (Prompt 13: the host has the LED driver and photodiode amplifier this tile was) |
| (0,3)-(1,3) | a11 | 40 kHz ultrasound | +-5 | RX OUT | IO4, IO3 | DRV8837 H-bridge from IO4 and IO3 into a transducer in pins 1 and 5 of a 1 x 5 socket; the second transducer through 10 n / 3.9 k into the a2 geometry at x100; the Pmod plug hangs off this tile's bottom edge |
| (2,3)-(3,3) | a12 | audio | +-5 | SPEAKER IN, MIC OUT | IO2 | PAM8302A into a speaker on a screw terminal, fed by SPEAKER IN through 1 u and by the one-bit stream on IO2 through 10 k / 10 n; an electret in a 1 x 2 socket (2.2 k bias) through 1 u into the a2 geometry at x100 (no 3.5 mm jack) |

The Pmod lines (the standard's IO numbers: IO1-4 on pins 1-4, IO5-8 on pins 7-10): a6 IO8 and IO7, a8 IO6,
a11 IO4 and IO3, a12 IO2; IO1 and IO5 are unused (a10 needs no line since Prompt 13).  (Renumbered 2026-10-25 when the plug's mirrored pinout was fixed.)
The switched rail of every tile comes from its own slide switch and P-FET; -5 V (40 mA from the
LM2664) is shared and unswitched.

## 6. RF-MOD: 915 MHz, 2.4 GHz, a stretch to 5.8 GHz

As built (rev A, 2026-10-25): ten tiles on sixteen cells, four layers, every tile's IN top-left and OUT bottom-right
(a third jack at the top middle on r1, r10 and R11, at the right cell's top-left on the mixers), CPWG lines (0.29 mm, 0.25 mm gaps over 0.21 mm of 7628) with via fences, a launch
void under every jack's centre pin, a top-side ground pour on every RF tile.  ERC 0, DRC 0, the fab checks pass,
$57.19 of parts per board (after Prompt 13's QPL9547 and TRF3722).

| cells | # | tile | supply | jacks | Pmod | the circuit as built |
|---|---|---|---|---|---|---|
| (0,0)-(1,0) | r1 | diode mixer | | LO, RF, IF | | ADEX-10L+ double-balanced diode-ring mixer (10-1000 MHz, LO +4 dBm, 7 dB loss), its baluns and ring drawn on the silk; in the splitter's place after Prompt 15 ("Do the diode-ring mixer instead of the least useful passive splitter.  I have passive splitters.") |
| (2,0) | r2 | 2.45 GHz filter | | IN, OUT | | Murata LFB212G45SG8A127 LTCC, 1.7 dB, 2.4-2.5 GHz |
| (3,0) | r4 | 915 MHz filter | | IN, OUT | | RF360 B39921B2672P810 SAW, 1.1 dB, 902-928 MHz |
| (0,1) | r5 | LNA | +5 | IN, OUT | | QPL9547 (Prompt 13; the taped QPL9547TR7 was in stock): Qorvo's 18 nH choke feeding 5 V into the output pin, 3.3 k to Vbias for 65 mA; 19.5 dB, 0.3-0.5 dB NF from 0.5 to 3 GHz, 22 dBm absolute maximum at the input |
| (1,1) | r12 | gain block | +7.8 | IN, OUT | | GALI-84+: 100 pF in and out, 27 nH and 22 ohm (2512) from the switched 7.8 V; 20 dB, +20 dBm P1dB |
| (2,1)-(3,1) | r9 | power and reference | | REF OUT | | USB-C (5.1 k CC, 2 A PTC, SMAJ5.0A, 2 x 10 uF); MT3608 boost to 7.8 V (22 uH, SS34, 12 k / 1 k) on the L3 strip under row 1; TPS7A2033 3.3 V for a TC32H4 25 MHz TCXO and a 74LVC1G17 driving REF OUT through 51 ohm; green (5 V) and yellow (7.8 V) LEDs |
| (0,2)-(1,2) | r7 | TX mixer | +5 (3.3 V LDO) | RF, LO, IF | | ADL5350 with a 200 MHz crossover on its RF/IF node, 0 ohm + 100 pF LO input, 10 nH LO-buffer choke; its own TPS7A2033 behind the switch |
| (2,2)-(3,2) | r8 | RX mixer | +5 (3.3 V LDO) | RF, LO, IF | | the same |
| (0,3)-(1,3) | r10 | synthesizer | +5 (3.3 V LDO) | OUT A+, REF IN, OUT A- | IO1-4 | MAX2871, CostasLink's circuit: RFOUTA+ and RFOUTA- each through 27 nH / 100 pF to a jack (RFOUTA- was in 51 ohm until Prompt 15), RFOUTB open; loop filter C1 470 p, R2 820 + C2 6.8 n, R3 470, C3 100 p (80-120 kHz, 61 degrees for 915 MHz at VCO/4 and 2.4 GHz at VCO/2, ICP 2.56 mA); LD on a red LED; carries the Pmod plug |
| (2,3)-(3,3) | r13 | I/Q transmitter | +5 (3.3 V LDO) | I IN, Q IN, RF OUT | IO2, IO3, IO5, IO6 | TRF3722 (PLL, VCO, I/Q modulator, 0.4-4.2 GHz; Prompt 13, replacing rev A's second MAX2871) on SPI shared with r10 (LE IO6, readback IO5), referenced from r10's REF IN; each DAC through 56 ohm at the jack and 270 ohm to a node at 0.25 V; about -3 dBm, image-free (-42 dBc untrimmed); a TLV75733 for its 3.3 V |

Pmod (the standard's IO numbers): IO1 MUXOUT of r10, IO2 SDATA, IO3 SCLK, IO4 LE of r10, IO5 the TRF3722's readback,
IO6 LE of r13; IO7 and IO8 unused.  The synthesizers' and mixers' nets use a "Fine" class (0.127 mm, 0.15 mm tracks, 0.45 / 0.25
vias) for the QFN fan-out; everything else keeps 0.2 mm.

Not on rev A, with the reason: the RFX2401C front end (its cells went to a complete second chain), the LTC5510 mixers
(35 in stock: the ADL5350 instead), and the printed antennas (TI's dimensions are for another stack and need a bench to
tune; SMA whips instead, see the handbook).  The QPL9547 and the TRF3722, missing from the first layout, came back in
Prompt 13 (`PLAN_LEVEL2.md` section 2).

## 7. Parts and sourcing

The table below is the plan's list (2026-10-25 01:00).  The boards as built use what `scripts/parts.py` lists; the
differences: OPA810 (not OPA2810) on AMOD-A's gain tiles, OPA847IDBVR (C160422, SOT-23-6) for a4, 74HC4046APW-Q100J
(C546981, TSSOP-16, 234 in stock on 2026-10-25) for a7, no LT6230, NTC or 3.5 mm jack, and on RF-MOD one GALI-84+, the
QPL9547TR7, the TRF3722, the ADL5350 twice and no LTC5510 or RFX2401C.

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
| OPA2810IDR | C1849413 | 2.54 | 3,707 | a2, a3, a10, a11 |
| OPA1612AIDR | C94590 | 1.34 | 26,345 | a5, a12 |
| OPA847IDR | C2870028 | 5.65 | 1,466 | a4 |
| TLV3501AIDBVR | C193413 | 1.92 | 5,079 | a6 (and a11's TX comparator) |
| CD74HC4046AM (alt. CD4046BM/TR C7432285, 4,889) | C1519916 | 1.37 | 91 | a7 |
| MC1496DR2G | C7295 | 0.25 | 14,255 | a9 |
| TMP235A4DBZR | C2868809 | 0.32 | 13,806 | a8 |
| DRV8837DSGR | C39159 | 0.26 | 85,042 | a11 |
| PAM8302AASCR | C113367 | 0.31 | 12,021 | a12 |
| PD70-01C/TR7 | C131196 | 0.21 | 77,545 | a10 |
| LM2664M6X/NOPB | C108573 | 0.33 | 164,185 | a1 (-5 V) |
| TPS7A2033PDBVR | C2862740 | 0.21 | 155,681 | a1, r9, r10, R11, r13 |
| LP5907MFX-3.3 | C23380874 | 0.14 | 12,279 | r9 (the TCXO) |
| MT3608 | C84817 | 0.10 | 91,494 | r9 (8 V for the GALI-84+) |
| TYPE-C-31-M-12 USB-C | C165948 | 0.19 | 324,740 | a1, r9 |
| MF-MSMF200-2 PTC, SMAJ5.0A TVS | C210837, C113952 | 0.07, - | 9,923 | a1, r9 |
| PZ254R-12-12P Pmod plug | C492434 | 0.10 | 4,327 | AMOD-A, RF-MOD |
| KF301-5.0-2P / -3P terminals | C474881 / C474882 | 0.10 / 0.14 | 84,342 / 27,437 | p13, a10, a12 |
| PZ254V-11-05P 1 x 5 header (the transducer sockets are the female of it: see section 10) | C492404 | 0.03 | 168,994 | a11 |
| MAX2871ETJ+T | C7458627 | 9.97 | 3,120 | r10, R11 |
| QPL9547TR7 | C5367093 | 6.70 | 5,070 | r5 |
| LTC5510IUF#TRPBF (fallback: Digi-Key; design alternative AD8342 C182567, 36) | C688646 | 14.98 | 35 | r7, r8 |
| RFX2401C | C19213 | 0.97 | 58,226 | R6 |
| GALI-84+ | C3193261 | 4.22 | 144 | r12 |
| TRF3722IRGZR | C1850395 | 8.63 | 2,218 | r13 |
| B39921B2672P810 SAW 915 MHz | C1518004 | 0.56 | 6,411 | r4 |
| LFB212G45SG8A127 2.45 GHz | C341536 | 0.19 | 3,940 | r2 |
| TC32H4-25.000-33GNDTNL TCXO | C5119013 | 1.58 | 1,240 | r9 |
| X49SM4MSD2SC 4 MHz crystal | C13774 | 0.11 | 33,932 | p8 |
| KCR455E 455 kHz resonator | C366989 | 0.11 | 504 | p9 |
| 1N4148W (Basic) | C81598 | 0.01 | 4.1 M | p10, clamps |
| LEDs 0805: NCD0805R1 red (Basic), KT-0805Y yellow (Basic), KT-0805G green (Basic), KT-0805B blue | C84256, C2296, C2297, C2293 | 0.01-0.02 | plenty | p12, the rail and tile LEDs |
| E6C1204URAC1UDA side-view red LED | C375479 | 0.02 | 12,614 | a10 |
| GMI6050-2C38DB electret (SMD, 6 mm) | C233921 | 0.33 | 985 | a12 (fitted; the socket is the alternative) |
| PJ-320A 3.5 mm jack | C2884926 | 0.14 | 9,322 | a12 |
| HNTC0805-103F3380FB 10 k NTC | C49247661 | 0.05 | 4,464 | a8 |
| 2512 15 ohm 1 W | (see parts.py) | 0.03 | | a8 |

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

Built 2026-10-25 as board `adda12p` of the generator that drew every Icepi adapter
(`~/OpticsPCBs/IcepiZeroADCDAC/adapters/make_boards.py`); the outputs are copied to `icepi_adapter/` with a README.
The 2x12 adapter unchanged, plus a 2 x 6 right-angle Pmod socket.  The socket's housing does not fit on the 65 x 30 mm
board between the header's legends and a mounting hole, so the board is 80 x 30 mm, the extra 15 mm past the Icepi
Zero's right-hand end with the socket on it (the module above ends at x 62).  Four layers: the outer two keep the
converter's fan-out as it was, the eight Pmod lines run on In2 between through-hole pads with no via and no crossing,
In1 is solid ground.  Eight of the ten free header pins (8, 10, 22, 27, 28, 36, 38, 40) are the Pmod's IO1-8, header pin
1 its 3.3 V, pins 3 and 5 spare.  DRC 0, no unconnected pads; the `.lpf` names the lines `pmod[0..7]` with DRIVE=4 and
SLEWRATE=SLOW, so no series resistors.  Hand-soldered like the original (three through-hole connectors).

## 10. Order of work and status

1. Plan, decisions, stock (this file): done 2026-10-25 01:05.
2. The framework: geometry, parts, the Tile class, the schematic and board generators: done 02:00
   (the grid router and the back-wire machinery came with AMOD-A).
3. AMOD-P end to end: done 03:40 (ERC 0, DRC 0, the fab package through every check, $16.97 of parts).
4. AMOD-A: done 08:30 (twelve tiles, four layers, ERC 0, DRC 0, the fab package through every check,
   $45.97 of parts; the handbook and manufacturing notes generated).  The plan's tiles were trimmed to
   fit 20 mm cells beside a switch and a FET: section 5's table says what was built, the handbook's
   DOA list what was dropped.  Pmod pinout corrected and holes replaced by feet: 10:05.
5. RF-MOD: done 09:55 (ten tiles, ERC 0, DRC 0, the fab checks, $55.78 of parts): section 6.
6. The Icepi adapter: done 10:20 (section 9).
7. The design-review brief (`docs/REVIEW_BRIEF.md`), the DOA lists (`docs/DOA_*.md`); the review rounds are next.
8. The jacks spread into the checkerboard on every board (Prompt 12): done 12:40.  AMOD-P's thirteen tiles and
   AMOD-A's a2-a4, a7, a8, a9 and a11 re-laid, RF-MOD's mixers' LO moved to the right cell's top-left; every pair of
   jacks 14.85 mm or more apart.  a4 now uses the OPA847's SOT-23-6 and a7 Nexperia's TSSOP-16 4046, so AMOD-A's
   parts are $50.90 a board.  All three boards: ERC 0, DRC 0, every fab check passed.

Open items that are not Jason's to answer are decided in this file as they come up and logged in
the chat; the ones that are his go in `QUESTIONS.md`.

## 11. AMOD-N: the second passive board (Prompt 17, 2026-10-28)

Jason: "It seems like there is enough pressure that I should make another analog board.  We should really call this the
2nd board because it's so much simpler than even the active board.  The board with the laser stuff and NV center stuff
should maybe be renamed OMOD for optics or PhMOD for physics.  All of the things that you suggested along with some of
the things that we've dropped should go on this new analog board ... SLOT for VNA-type calibration, passive splitters ...
If it make sense to move the diode mixer onto this new analog passive board, do that to free up space there."  Mid-turn:
"If something can run on 3.3V, it could still be plugged into the PMOD port but wouldn't require an external USB 5V
input", and "To distinguish whole-tile labels from SMA or port labels, use different cases (upper, lower, mixed)."

**Decided.**

- **The name is AMOD-N, and it is the second board in every list** (after AMOD-P, before AMOD-A).  The name AMOD-2 is
  not reused: the commits, Appendix D and the chat log mean the physics board by it.  The tiles continue AMOD-P's
  numbers, n1-n11.
- **AMOD-2 is PhMOD** (physics: magnetic resonance, the ionosphere and light), not OMOD: one of its ten tiles is optical.
  The optics board of PLAN_LEVEL2 section 6 keeps the name OMOD for later.  Its tiles keep h1-h10.
- **Passive, with two tiles on the Pmod's 3.3 V and no USB.**  The step attenuator (150 uA) and the oscillator (about
  2 mA) run from the host's 3.3 V through AMOD-N's own plug, carried by n8 at the bottom-left as on every other board.
  Everything else works unplugged.  The plug's IO2-IO4 are RF-MOD's SDATA, SCLK and LE, so one SPI peripheral in the
  gateware drives every SPI tile on every board.
- **Four layers, RF-MOD's stack (JLC04161H-7628) and launch,** because half the tiles are GHz parts: L2 ground, L3 the
  Pmod's 3.3 V, L4 ground.  Feet, no holes (the board sits on a Pmod).
- **The diode-ring mixer stays on RF-MOD.**  The tiles asked for, suggested in Prompt 16 and dropped before filled the
  sixteen cells exactly once the two powered tiles came onto this board (Jason's mid-turn message), and moving r1 would
  have left two cells on RF-MOD with nothing waiting for them; r1 also wants r10's LO beside it.
- **Silk case.**  Ports in capitals, a tile's label in mixed case (its first letter capitalised, the rest as written:
  `tiles.label_case`), notes and ranges in lower case except units, acronyms and part numbers.  Applied to all six
  boards.  Titles that no longer fit a cell's frame were shortened (Attenuator, Balun, Transformer; RF-MOD's and
  IQ-MOD's LNA tiles are "Preamp").

**As built** (ERC 0, DRC 0, all fab checks; $43.91 of parts a board; 30 jacks):

| # | cells | tile | jacks | as built | chips (JLCPCB 2026-10-28) |
|---|---|---|---|---|---|
| n1 | (0,0)-(2,0) | calibration | SHORT, OPEN, LOAD, 25 OHM, THRU, THRU | SHORT: the pin poured to ground (no launch void); OPEN: the bare pin; LOAD: 2 x 100 ohm after 4 mm of line; 25 ohm: 2 x 49.9 ohm (VSWR 2); THRU: 19.8 mm, about 115 ps | resistors |
| n2 | (0,1)-(1,1) | resistive splitter | IN, OUT 1, OUT 2 | 3 x 16.9 ohm star, DC-6 GHz, -6 dB | 0402WGF169JTCE C82287 |
| n3 | (2,1)-(3,1) | transformer splitter | SUM, PORT 1, PORT 2 | ADP-2-1+ turned 270, pins 2 and 5 joined off ground | ADP-2-1+ C2683460 (41: accepted under Prompt 13's rule) |
| n4 | (0,2) | quarter-wave stub | IN, OUT | a 17.3 mm open stub (copper graphics, not a track) on the line: a notch near 2.45 GHz | copper |
| n5 | (1,2) | low-pass | IN, OUT | LFCN-1000+, DC-1 GHz | LFCN-1000+ C879868 |
| n6 | (2,2) | detector | IN, OUT | 51 ohm, 10 nF, a zero-bias SMS7630 pair as a doubler, 100 pF / 100 k | SMS7630-006LF C6489012 (83: accepted) |
| n7 | (3,2) | bias-T | RF, RF+DC | 100 nF; 27 nH + 330 nH + 10 uH; DC and GND test loops | (the board's passives) |
| n8 | (0,3)-(1,3) | step attenuator | IN, OUT | PE43711; an 8-way DIP switch (way 1 SPI, ways 2-8 the bits, 100 k pull-downs, LE pulled high): by hand in direct parallel mode, or serial on IO2-IO4; 100 nF blocks; carries the Pmod plug | PE43711B-Z C470929 (1,673); DSHP08TSGET C40738 (4,520) |
| n9 | (3,0) | oscillator | TUNE, OUT | Clapp on an MMBT3904, 10 uH + BB133, 220 / 220 pF, 9.6-11.5 MHz; switch and FET | MMBT3904, BB133 |
| n10 | (2,3) | 1:1 balun | IN, OUT | TC1-1TG2+ in the top-right quarter; OUT's legs an island 5.6 mm clear of every plane | TC1-1TG2+ C3305009 (85: accepted) |
| n11 | (3,3) | 1:4 transformer | IN, OUT | TC4-1W+, the secondary grounded at one end; DIP: 200 or 49.9 ohm on OUT | TC4-1W+ C879855 (2,227) |

**Left out, and why.**  The oscillator's crystal and DIP switch (a VCXO, which Appendix D's first AMOD-2 had): no room
in one cell beside the switch and the jacks.  A 30 MHz anti-alias low-pass: the host's front end has its own filters.
A crystal ladder filter: with 50 ohm ends it needs matching transformers, and its crystals' motional parameters are not
published.  A 10.7 MHz ceramic filter: none in stock.  A quadrature hybrid: the I/Q chips on RF-MOD and IQ-MOD make
their own quadrature.  Printed antennas, a printed coupler, a split-ring resonator: as before, they need a field solver
and tuning.

**Found on the way: JLCPCB's placements.**  `scripts/check_rotations.py` fits JLCPCB's drawing of every part onto the
footprint on our board.  Rev A's table had every SOT-23, SOT-23-5 and SOT-23-6 at 0 ("the standard drawing"); JLCPCB's
"-BR" drawings are KiCad's turned 180 (the AO3401A in every powered tile, the MMBT3904s, LMH6629s and the rest) and its
"-BL" ones KiCad's turned +90 (OPA847, LT6230, MT3608).  The SOICs, the TSSOP and the 2.54 mm headers needed +270, and the
3225 TCXO 0 rather than 180.  `parts.JLC_DATUM` now moves the USB-C (1.572 mm), the SOT-89s, the slide switch and the
headers to JLCPCB's origin in the upload CPL.  CLAUDE_PCB.md's readings from earlier orders agree with every one.

## 12. Prompt 18: the back of every board, n8 by hand, and what is still missing (2026-10-28)

Jason, Prompt 18: "Can the P22 Attenuator (PE43711) also still be controlled with switches?  Does this part need the
3.3V power? ... I hope that the silkscreen (including on the back) is appropriately used to document anything that a
user definitely needs to know to use the tiles successfully and without damaging anything.  If there is additional room
on the back, putting plots of expected responses or other relevant parameters would be great.  When someone is screwing
things into the board, it's far easier to read the silkscreen in front of them than it is to look up stuff on github."

**Done.**

- **A panel under every tile, on the back** (`gen_pcb.back_panels`): its number and title, then the lines in its board
  module's `BACK` dict: input limits, loads, supplies, the switch and the one thing that breaks it.  Mirrored, so they
  read from the back; 0.8 mm text on a 1.5 mm pitch.  A panel goes as one block or in two to four parts, each below the
  one before so it reads in order, clear of the back's tracks and vias where there is room (over a track otherwise: the
  ink sits on the mask).  Lines are 13 characters or fewer on a one-cell tile, about 22 on a wider one: the free space
  on a cell's back is the 10 mm between its two diagonal jacks.
- **A plot of the expected response** where there is room: the ladder tiles of AMOD-P their own simulation; the others
  from `scripts/backplots.py` (amplifiers' gain against frequency, datasheet tables, n4's open stub, n9's frequency
  against TUNE, p10's OUT against IN).  The axis drawn mirrored so it reads left to right from the back; its range in
  the line above it, its ends below.  All plots placed on all six boards.
- **The front** carries the few that must be seen while cabling: h2 PULSES ONLY, h10 "start at mV", r5 and q4 "IN -20
  dBm", n8's switch rule.
- **n8 by hand.**  The PE43711 has a direct parallel mode (P/S low, LE high) that pSemi calls "ideal for manual
  control": an 8-way DIP switch, way 1 SPI (on: serial, P/S high), ways 2-8 the seven bits, 100 k pull-downs, LE pulled
  up by 100 k so a floating FPGA pin leaves the switches in charge.  In SPI mode the bits must be off.  The chip needs
  the Pmod's 3.3 V either way: it is an active switch array (its digital inputs are 3.6 V absolute maximum).  It took a
  second cell; P15 (two Smith-chart loads) gave it up, n9 moved to (3,0).  n1's 25 ohm standard and n11's 200 and
  49.9 ohm loads still put points on a Smith chart.

**Swaps considered, not made.**  q4 (IQ-MOD's preamp) is r5 again; it stays so IQ-MOD receives on its own, but it
is the first cell to give up.  r1 (the passive diode mixer) would suit AMOD-N but wants r10's LO beside it, and AMOD-N
is full.  a6 (one-bit ADC) and a7 (4046 PLL) would run on the Pmod's 3.3 V, but AMOD-A needs USB for its other tiles
anyway, so moving them saves nothing.

**Still missing: Analog Devices' labs** (`docs/ADI_LABS_SURVEY.md`).  Power regulation is the one whole area none of
the boards covers; switched-capacitor circuits, the inside of a delta-sigma modulator, sample-and-hold, SAR conversion
and transistor-level stages are the others that fit.  The six boards are full, so these would be a seventh board,
**AMOD-A2** (the second active board, USB-C power and the Pmod), proposed and not started:

| tile | cells | what | parts (JLCPCB stock 2026-10-28) |
|---|---|---|---|
| power | 1 | USB-C 5 V, +-5 V for the op amps | as AMOD-A's a1 |
| LDO and buck | 2 | a buck then an LDO, an electronic load from a DAC: ripple before and after, load steps, Zout(f), dropout, pulse-skipping | TLV62568 C163219, LP5907-3.3 C80670 or XC6206 C5446, OPA2810, AO3400A |
| charge pump | 1 | the FPGA clocks it: Rout = 1/(fC) + switches, ripple against load | ICL7660A C7881; LM2664 C108573 |
| FPGA buck | 2 | two half-bridges into two inductors, the duty from the FPGA: two-phase ripple cancellation, a digital loop's Bode plot | DRV8837 C39159 (about 250 kHz) |
| switched-capacitor filter | 1 | an 8th-order filter whose corner follows the FPGA's clock; aliases at fclk +- fin | MAX291 C596390 (46) or LTC1069-6 C674326 (61) |
| switched-capacitor resistor | 1 | R = 1/(fC) and an integrator from two switches and a capacitor, non-overlapping clocks from the FPGA | 2 x SN74LVC1G3157 C10426, OPA2810 |
| second-order delta-sigma | 2 | both integrators, the comparator and the one-bit DAC on jacks: 40 dB/decade against AMOD-A's 20, idle tones | OPA2810, TLV3501 C193413, 74LVC1G79 C42878, REF3033 C36658 |
| track-and-hold | 1 | acquisition, droop, pedestal, feedthrough | LF398 C2864267 |
| R-2R and comparator | 2 | the FPGA runs SAR, tracking and dual-slope conversions; DNL and INL | 0.1 % resistors (to find), TLV3501 |
| transistor blocks | 2 | a differential pair with a mirror load (tanh, triangle to sine); common emitter against cascode (Miller) | DMMT3904W C155305, BCV62 C139953 |
| 555 | 1 | thresholds, f against V, a VFC as an ADC | TLC555 C6986 |

Sixteen cells.  Not checked yet: a 5 V clock buffer for the filter chip, 0.1 % resistors in stock, whether each fits its
cell.  Jason to decide.

## 13. Prompt 19: one letter per board, tiles in lower case (2026-10-28)

Jason, Prompt 19: "We need a better naming system for the boards and tiles ... If we can have a nice, well justified
single-letter designator for each board, it would make everything much more clear", and mid-turn: "Maybe you want to
make the tiles lower case, because D11, Q11, C11, etc look like a reference designators for diodes, transistors, and
capacitors.  d11, q11, and c11 don't look like obvious electronics or PCB things."

**The rule.**  Every board has one letter, the initial of what it is about.  A tile is that letter in lower case and a
number (`n8`, `q3`), numbered from 1 on each board.  Board names keep their capitals (AMOD-N), ports are capitals (IN,
OUT), a tile's title is mixed case (Step attenuator), everything else lower case: Prompt 17's convention, extended.

| letter | board (stem) | the letter says | tiles | was |
|---|---|---|---|---|
| p | AMOD-P (`amod_p`) | passive | p1-p13 | P1-P13 |
| n | AMOD-N (`amod_n`) | networks: the pieces of a network analyzer (standards, splitters, a detector, an attenuator, a source) and the networks it measures | n1-n11 | AMOD-P2's P14, P16-P25 |
| a | AMOD-A (`amod_a`) | active | a1-a12 | A1-A12 |
| c | AMOD-C (`amod_c`) | conversion: power (linear, switched, charge pump) and data (delta-sigma, sample-and-hold, SAR), and the switched capacitors both use | c1-... | new (section 12's AMOD-A2) |
| m | AMOD-M (`amod_m`) | motors: brushed DC, stepper, servo, solenoid, voice coil, and their sensors | m1-... | new |
| b | AMOD-B (`amod_b`) | brushless: a gimbal motor on its magnetic encoder, the drone's sensorless six-step, an IMU | b1-... | new |
| r | RF-MOD (`rf_mod`) | radio | r1, r2, r4, r5, r7-r10, r12, r13 | R1-R13 |
| h | PhMOD (`phmod`) | the h of Ph (p is the passive board's), and HF, where all its tiles work | h1-h10 | Y1-Y10 |
| q | IQ-MOD (`iq_mod`) | quadrature: its I/Q modulator and demodulator share one LO | q1-q11 | RF-MOD-2's X1-X11 |

**Why these and not others.**

- *A letter never moves to another board, and a retired name is never reused.*  Then a reference missed in an update
  points at nothing instead of at the wrong tile.  That is why the passive board keeps p and the active board a (Jason
  offered a for the passive board and b or c for the active one: every existing "a4", the LNA, would have become a
  different tile), and why RF-MOD keeps r3, r6 and r11 unused (dropped in planning; renumbering would have moved r4-r13
  onto other tiles).  P14-P25, X1-X11 and Y1-Y10 are retired.
- *Not s for the second RF board* (Jason asked about S11 and T11): s11 is the reflection coefficient that IQ-MOD's coupler
  and AMOD-N's standards exist to measure.  t says nothing about the board.  Not c for comms either: the radio boards are
  r and q, and c went to conversion.
- *Not i, l or o*: they read as 1 and 0.  Lower case also stops q, c and r reading as a transistor, a capacitor and a
  resistor; the boards' part references stay upper case (U801, R501) and never print on the silk.
- *Board names follow their letter where they did not*: AMOD-P2 became AMOD-N (a "P" in its name promised p tiles) and
  RF-MOD-2 became IQ-MOD (an "RF-MOD" in its name promised r tiles).  PhMOD keeps Jason's name; its h is the h in it.
- *Motors take two boards, not one with two Pmods* (Jason: "If it makes more sense to do 2 boards rather than one board
  with two Pmods, stick with an extra board").  A DC motor with its encoder needs 4 FPGA lines, a stepper 4, a
  three-phase bridge 3 and its encoder and IMU 5 more: AMOD-M (brushed, stepper and the slow actuators, 8 lines) and AMOD-B
  (brushless, 8 lines).  Neither fits the conversion board, whose sixteen cells and eight lines are full.

`scripts/tiles.dump` refuses a tile whose name is not its board's letter and a number, a number used twice, and a `BACK`
or `BACK_PLOTS` entry for a tile that does not exist.
