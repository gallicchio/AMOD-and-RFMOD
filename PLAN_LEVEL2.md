# The second level: AMOD-2 and RF-MOD-2, and the first level checked again

Prompt 13 (2026-10-25): check that the first AMOD and RF-MOD boards hold the right things to build first, then fill
the second-level boards with the most interesting RF physics and communications experiments.  Prompt 13's
follow-ups: the second-level boards will be used only with the ECP5-2ADC-2DAC board; a part with 14 or 21 in stock
is acceptable.  This file is the plan and the decision record for both; `PLAN.md` stays the first level's.

## 1. What the host gives, and what that changes

The ECP5-2ADC-2DAC board (tutorial Appendix D) has two DC-coupled 12-bit ADC channels at 65 MS/s from one AD9238,
two 14-bit DAC channels at 125 MS/s from one AD9767, CLK IN (a GPSDO's 10 MHz) and CLK OUT, gigabit Ethernet, two
Pmods, and on the board itself a Johnson-noise source switched into ADC A, a photodiode with a 10 kOhm / 9 MHz
transimpedance amplifier switched into ADC B, and a 0-50 mA LED current source from DAC 1.  Three consequences:

- **Two coherent channels in and out are the point.**  The second-level tiles are chosen so that both ADCs (I and Q;
  incident and reflected; two loops; signal and reference) and both DACs (I and Q; pump and signal) have a job.
- **Everything can share one clock.**  RF-MOD-2's synthesizer takes CLK OUT as its reference, so the converters, the
  local oscillators and the DAC's waveforms are phase-locked: a phase measured means something.
- **The host's own noise source, photodiode and LED driver make AMOD-A's A5 (Johnson noise) and A10 (LED and
  photodiode) duplicates** (section 2).

## 2. The first level, checked again (rev A, not yet ordered)

| board | change | why |
|---|---|---|
| RF-MOD | **R5 becomes a QPL9547 low-noise amplifier** (QPL9547TR7, C5367093, 5,070 in stock, $6.70); R12 stays the GALI-84+ | Appendix D's choice.  Rev A's search found only the untaped QPL9547 (0 in stock) and used a second GALI-84+ (NF about 4 dB).  0.3 dB at 1.9 GHz is 3-4 dB more sensitivity for every receiver, the hydrogen line and GPS included |
| RF-MOD | **R11 becomes a TRF3722 quadrature transmitter** (C1850395, 2,218 in stock, $8.63): PLL, VCO and I/Q modulator, 400-4200 MHz, its baseband from the host's two DACs, its LO output on a jack | Jason asked for it ("Yes. Add that tile.") and rev A left it out.  It removes the transmitter's image, its own PLL replaces the second MAX2871, and its LO output (the same VCO) drives a receive mixer coherently with the transmitter: a homodyne radar whose phase noise cancels |
| AMOD-A | **A5 (Johnson noise) becomes A5 "Doppler": a socket for an HB100 10.525 GHz radar module and a x100 audio amplifier** | the host has the noise source and a x100 input.  The HB100 ($3-5, 5.08's speed gun) is the only route above 6 GHz: walking speed, a fan's blades, a speaker cone, breathing |
| AMOD-A | **A10 (LED and photodiode) becomes A10 "impedance": a driven reference resistor and two buffered outputs, V across the part and I through it, for the host's two ADCs** | the host has the LED driver and a faster photodiode amplifier.  Two channels make an impedance analyzer (DC-5 MHz, 47 Ohm-47 kOhm ranges) and an I-V curve tracer (LEDs and Planck with P12, diodes, the crystal's motional arm): what the ADALM2000's impedance adapter does |

AMOD-P is unchanged: every tile serves a tutorial page and nothing on the host duplicates it.  AMOD-A's A2 and A3
stay although the host has x10 and x100 inputs: they are 50 Ohm drivers with more bandwidth, and the op-amp tiles the
tutorial measures.

## 3. AMOD-2: HF, magnetic resonance and the reflectometer (as built, rev A)

DC to 30 MHz is where the host's converters sample directly, and where most of the RF physics a student can touch
lives: nuclear and electron spin resonance, the ionosphere (VLF transmitters, sferics, WWV, the HF bands), coupled
and parametric resonators, impedance and transmission lines, noise.  Plus the one optical tile that serves RF
physics: a laser driver whose bias-T puts gigahertz on the current (the rubidium CPT clock, NV-centre ODMR, PDH
sidebands).  The piezo driver, the bimorph and the TEC of Appendix D's first AMOD-2 go to a future optics board
(section 6).  ERC 0, DRC 0, all fabrication checks; 234 placements, 76 BOM lines, $78.19 of parts a board.

| # | cells | tile | jacks | as built | chips (JLCPCB 2026-10-25) |
|---|---|---|---|---|---|
| Y1 | (2,1)-(3,1) | power | | USB-C 5 V (5.1 k CC), 2 A PTC, 5 V TVS; an LM2664 for -5 V (40 mA) into L3's strip under row 0; a TPS65131 for +-15 V (1 M / 88.7 k, 1.3 M / 105 k, 1.25 MHz, power-save off) carried to Y2 on two tracks on the back | TPS65131RGER C87663, LM2664 |
| Y2 | (2,0) | pulse amplifier | IN, OUT | THS3491 (RGT) at gain 10.3 from +-15 V: +-1 V into 50 ohm becomes +-10 V, 1 W; PD from IO1 through 4.7 k, 10 k holding it off | THS3491IRGTR C2058688 (237) |
| Y3 | (0,0)-(1,0) | duplexer and preamplifier | TX IN, PROBE, LINE, RX OUT | two pairs of crossed 1N4148W from TX IN to PROBE (the pulse passes, the transmitter's noise between pulses does not); LINE, from the probe through a quarter-wave cable (or a short cable and a 6 dB pad), clamped by crossed diodes and terminated in 49.9 ohm, into an OPA847 at x12: the classic passive duplexer | OPA847IDBVR C160422 |
| Y4 | (3,3) | coil driver | MON | DRV8876 in PH/EN mode (IO6 enable and PWM, IO7 direction), VM the higher of USB's 5 V and 12-18 V on a terminal (two B5819W), IPROPI into 1.5 k (a 1.3 A limit with VREF at 2 V) buffered by an OPA810 to MON; the coil on a second terminal | DRV8876PWPR C575551 |
| Y5 | (0,3)-(1,3) | two-channel HF receiver | IN A, OUT A, IN B, OUT B | two LMH6629 at x9.9, 50 ohm in and out, 5 kHz-100 MHz; carries the Pmod plug | LMH6629MFX C2059678 |
| Y6 | (2,3) | VLF loop amplifier | LOOP, OUT | one OPA810 at x101, 1.6-160 kHz (100 pF across 10 k keeps the AM band out), the loop on an SMA lead | OPA810 |
| Y7 | (0,1)-(1,1) | reflection bridge | DRIVE, DUT, INC, REFL | a 49.9 ohm bridge; OPA810 at x2 on B (INC) and an OPA810 difference amplifier, 2 A - 2 B (REFL): REFL / INC = Gamma | OPA810 x2 |
| Y8 | (0,2)-(1,2) | coupled and parametric resonators | SIG, OUT 1, TUNE/PUMP, OUT 2 | two passive 10 MHz tanks (10 uH, 4.7 / 6.8 pF, two BB133 back to back at 2.5 V); 2.2 pF ports in and out (-43 dB into the host's 50 ohm); TUNE/PUMP into tank 2's cathodes through 100 k and 1 nF; a DIP4 for 1 and 2.2 pF of coupling and 2 k across either tank | BB133 x4, NLV32T-100J x2 |
| Y9 | (3,0) | noise source | OUT | an MMBT3904's emitter-base junction in avalanche between -5 V and the switched 5 V (680 ohm), an LMH6629 at x9.9; a TPS22917 switches it from IO8 | MMBT3904, LMH6629, TPS22917 |
| Y10 | (2,2)-(3,2) | laser driver with an RF bias-T | SET, MON, RF IN, LD | REF = VS - SET (OPA810 and a 2N7002), an OPA810 holding an AO3401's source at REF over 10 ohm: 100 mA per volt; 330 nH + 27 nH to the diode, 100 pF + 47 ohm from RF IN (20 MHz-3 GHz); an AO3400 shunt from IO5 for pulses; a B5819W against reverse current; MON is the diode's voltage through 10 k | OPA810 x2, AO3401A, AO3400A, 2N7002 |

**Changes from the plan, and why.**  Y1 lost the PCA9555, the MCP4728 and the +-5 V LDOs: with the attenuators gone
(Y5) and Y10 set by a DAC, five Pmod lines do every slow job, and the LM2664 already gives -5 V.  Y2 moved to one cell
(the RGT package fits).  Y3 uses crossed diodes, not the PIN switch and the ADG901: no control line, no +-15 V bias,
and the textbook duplexer.  Y4's current monitor is the DRV8876's own IPROPI, not an INA240.  Y5's attenuators,
bias-T and low-pass did not fit beside two LMH6629 channels and the Pmod plug; an external 30 MHz low-pass does the
anti-aliasing.  Y6 is one channel, not two: two transimpedance channels with their loop terminals needed four nets
across one cell's free quarter; Y5's IN A is the second loop for crossed-loop bearings.  Y7 uses two OPA810, not a
fully differential amplifier: REFL's difference is formed from INC's output.  Y8 lost its buffers: capacitive ports
read the tanks without loading them and need no power.  Y9's junction runs between -5 and +5 V rather than from +15 V.
Y10 has one range (100 mA per volt from 0; start a VCSEL at a few millivolts) and monitors the diode's voltage.

Pmod (the plug on Y5's bottom edge): IO1 Y2's PD, IO5 Y10's shunt, IO6 and IO7 Y4's EN and PH, IO8 Y9's switch;
IO2-IO4 spare.  IO1 and IO5 run on the front up the gutter at x 50.0 and 50.4, IO6 and IO7 on the back along the
bottom edge and across the top of Y6, IO8 round the left and top margins.

**What it opens, with the host:** see `docs/HANDBOOK_amod_2.md`, "The tiles together": pulsed NMR and one-dimensional
MRI, Earth's-field NMR, ESR of DPPH, the ionosphere at HF and VLF, the Smith chart and time-domain reflectometry,
normal modes, EIT and parametric gain, noise figure and transfer functions from noise, CPT and ODMR with a laser.

## 4. RF-MOD-2: quadrature, a coherent transceiver and microwave physics (as built, rev A)

One MAX2871, split, drives both an I/Q modulator and an I/Q demodulator, referenced to the host's CLK OUT: a coherent
zero-IF transceiver from 400 MHz to 6 GHz whose four baseband ports are the host's four converter channels.  Around
it the receiver's LNA, a log detector, an absorptive switch, a switched noise source, a GNSS front end and a loop for
NV centres' resonance.  ERC 0, DRC 0, all fabrication checks; $98.61 of parts a board.

| # | cells | tile | jacks | as built | chips |
|---|---|---|---|---|---|
| X1 | (0,2)-(1,2) | I/Q modulator | I IN, LO IN, RF OUT, Q IN | ADL5375-05, 0.4-6 GHz; the host's DACs through resistor networks to the chip's 0.5 V bias; DSOP grounded (always on) | ADL5375-05ACPZ C579150 (652) |
| X2 | (2,2)-(3,2) | I/Q demodulator | I OUT, LO IN, RF IN, Q OUT | ADL5380; each differential output to single-ended about 0 V by an OPA810 difference amplifier on +-5 V | ADL5380ACPZ C579152 (14: accepted), OPA810 x2 |
| X3 | (0,3)-(1,3) | synthesizer | OUT A, REF IN | RF-MOD's MAX2871 tile with REF IN (the host's CLK OUT) at the right cell's bottom corner; carries the Pmod plug | MAX2871 |
| X4 | (2,0) | low-noise amplifier | IN, OUT | RF-MOD's QPL9547 tile | QPL9547TR7 C5367093 |
| X5 | (0,1)-(1,1) | splitter | P1, P2, P3 | RF-MOD's 3 x 18 ohm splitter: X3's OUT A into both LOs | |
| X6 | (1,0) | log detector | IN, OUT | AD8318, 1 MHz-8 GHz, scaled to the host's input | AD8318ACPZ C578694 (152) |
| X7 | (2,1) | noise source | OUT | MMBT3904 in avalanche, an ADL5611, a 20 dB pad; a TPS22917 switches it from IO6 | ADL5611ARKZ C208262 |
| X8 | (3,0) | GNSS front end | ANT, OUT | a bias-T for an active antenna, a 1575 MHz SAW, a MAX2659, a second SAW | MAX2659ELT C28043, SAFFB1G56KB0F0AR1X C91647 |
| X9 | (0,0) | ODMR loop | IN, OUT | a one-turn 1.6 mm loop in a 50 ohm through line, nothing resonant: DC-6 GHz, 2.87 GHz and every Zeeman line; no copper within 2 mm | copper |
| X10 | (3,1) | power | | USB-C, PTC, TVS, an LM2664 for -5 V | LM2664 |
| X11 | (2,3)-(3,3) | absorptive SPDT | RFC, RF2, RF1 | SKY13370, 0.5-6 GHz, V1 and V2 from IO5 and IO8 | SKY13370-374LF C105628 |

**Changes from the plan, and why.**  X3 has one output on a jack and X5 splits it: one VCO either way, and RF-MOD's
proven tile.  The SPDT moved to X11 as the SKY13370 (in stock in the package the footprint wanted) and X5 became the
splitter the shared LO needs.  X11's printed coupler and X9's split-ring resonator were dropped for the same reason
as RF-MOD's printed antennas: both depend on a stack and a field solver the night did not have, and a resonator
needs tuning on the bench.  X9's through-line loop works at any frequency with no tuning.

Pmod (the plug under X3): IO1 MUXOUT, IO2 SDATA, IO3 SCLK, IO4 LE (X3), IO5 and IO8 X11's V1 and V2, IO6 X7's
noise; IO7 spare.

**What it opens, with the host:** see `docs/HANDBOOK_rf_mod_2.md`, "The tiles together": a radio link in any
modulation, a vector network analyzer, stepped-frequency and FMCW radar, NV-centre ODMR, GPS acquisition, power
metering, noise figure and a Dicke radiometer.

## 5. Rules and constraints carried over

The tile grid, the checkerboard jacks, the slide switch and P-FET per powered tile, USB-C on the right edge, the
Pmod plug at the left end of the bottom edge, four layers on JLC04161H-7628 with CPWG lines and CostasLink's launch,
the fine net class for 0.5 mm pitch parts, JLCPCB's shelf with the stock read on the day.  ADL5380 is the one part
below 100 in stock; Jason accepted it (and 21) on 2026-10-25, and `check_outputs` records the exception per part.

## 6. What moved to a future optics board

Appendix D's first AMOD-2 carried the experiments of an optics lab: the OPA462 piezo driver with its 60 and 150 V
ranges, the bimorph cantilever with its shadow sensor (the Thorlabs PB4NB2W and PiezoDrive BA4010 recorded there),
the TEC driver, the fast photodiode amplifier and the varactor-pulled crystal.  None is RF, and the second level is
now RF; they are kept, with Jason's answers, as an optics board for later.  AMOD-2's coil driver also drives a TEC,
and Y10 is the laser driver they would have shared.
