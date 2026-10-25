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

## 3. AMOD-2: HF, magnetic resonance and the reflectometer

DC to 30 MHz is where the host's converters sample directly, and where most of the RF physics a student can touch
lives: nuclear and electron spin resonance, the ionosphere (VLF transmitters, sferics, WWV, the HF bands), coupled
and parametric resonators, impedance and transmission lines, noise.  Plus the one optical tile that serves RF
physics: a laser driver whose bias-T puts gigahertz on the current (the rubidium CPT clock, NV-centre ODMR, PDH
sidebands).  The piezo driver, the bimorph and the TEC of Appendix D's first AMOD-2 go to a future optics board
(section 6).

| # | cells | tile | jacks | what it does | chips (JLCPCB 2026-10-25) |
|---|---|---|---|---|---|
| Y1 | (2,1)-(3,1) | power and slow I/O | | USB-C 5 V (3 A asked), PTC, TVS; +-15 V from a TPS65131; +-5 V LDOs from it; 3.3 V; a PCA9555 for the slow lines (attenuators, enables) and an MCP4728 for the slow setpoints, on I2C from the Pmod | TPS65131RGER C87663 (2,301), TPS7A4901 C16430 (9,505), TPS7A3001 C33835 (8,365), PCA9555PW C128392 (11,190), MCP4728 C478093 (18,443) |
| Y2 | (0,0) | RF power amplifier | IN, OUT | THS3491 at x11 from +-15 V: a DAC's +-1 V to 12 V peak into 50 Ohm (1.5 W), 1-30 MHz; gated by a Pmod pin so it is silent between pulses | THS3491IRGTR C2058688 (237) |
| Y3 | (1,0)-(2,0) | T/R switch and preamplifier | TX IN, PROBE, RX OUT | crossed diodes from the transmitter to the probe; a PIN-diode switch (series and shunt BAP64-03, biased +-15 V from a Pmod pin) and an absorptive blanking switch to an OPA847 preamplifier (x12): NMR's duplexer, broadband instead of a quarter-wave line | BAP64-03 C475615 (30,093), ADG901 C206802 (115), OPA847IDBVR C160422 (724) |
| Y4 | (3,3) | coil driver | MON | DRV8876 H-bridge from two Pmod pins on a 12-24 V barrel jack (or USB's 5 V), INA240 current monitor; the coil on a screw terminal: a Helmholtz pair for ESR, a gradient coil, an Earth's-field prepolarizer, a TEC | DRV8876PWPR C575551 (39,081), INA240A1DR C2060769 (6,440) |
| Y5 | (0,3)-(1,3) | two-channel HF receiver | IN A, OUT A, IN B, OUT B | per channel: a bias-T for an active antenna, a 30 MHz 5th-order low-pass, a PE43711 step attenuator (0-31.75 dB, 9 kHz up), an LMH6629 amplifier (0.69 nV/rtHz, x10): the host becomes a coherent two-channel direct-sampling receiver from 10 kHz to 30 MHz | PE43711B-Z C470929 (1,673), LMH6629MFX C2059678 (2,648) |
| Y6 | (2,3) | VLF loop amplifiers | OUT A, OUT B | two current-mode (transimpedance) loop amplifiers, 300 Hz-100 kHz, the loops on a 4-way terminal: sferics and their bearing from crossed loops, the US Navy's MSK transmitters near 24 kHz and sudden ionospheric disturbances (solar flares), WWVB's 60 kHz time code | OPA1612AIDR C94590 (26,280) |
| Y7 | (0,1)-(1,1) | reflection bridge | DRIVE, DUT, INC, REFL | a 50 Ohm resistive bridge with a buffered incident sample and a differential reflected sample for the two ADCs: complex S11 from 10 kHz to 30 MHz after an open-short-load calibration.  NMR probe matching, antennas, cables (time-domain reflectometry), crystals, the Smith chart | THS4521IDGKR C170157 (22,444) or LMH6551 (3,349) |
| Y8 | (0,2)-(1,2) | coupled and parametric resonators | SIG, OUT, PUMP, TUNE | two 4 MHz LC resonators tuned by back-to-back varactors, coupled by a capacitor on a DIP switch; the pump (DAC 2 at 2f) on the varactors: normal-mode splitting and the avoided crossing (the classical vacuum Rabi splitting), an EIT analogue, phase-sensitive parametric gain and de-amplification (squeezing's classical cousin), parametric oscillation | BB133 C5334579 (8,576), OPA810 (on AMOD-A) |
| Y9 | (3,0) | noise source | OUT | an avalanching base-emitter junction from +15 V, switched from a Pmod pin, amplified and padded to 50 Ohm: Y-factor noise figure, a noise stimulus whose cross-spectrum with the second ADC gives a transfer function, a calibrated radiometer | MMBT3904 C20526, LMH6629 |
| Y10 | (2,2)-(3,2) | laser driver with an RF bias-T | SET, RF IN, MON, LD | a high-side current source (0-30 or 0-300 mA by DIP, slow start, a clamp), set by a DAC or the MCP4728; a broadband bias-T (about 20 MHz-3.5 GHz) onto the diode's lead; a shunt switch from a Pmod pin for pulsed ODMR; an INA240 monitor.  The diode in its own mount on an SMA cable | OPA2388IDR C1517414 (6,421), AO3401A, INA240A1DR, 74LVC1G17 |

Pmod (one, the plug in Y5's bottom-left): IO1 the PA's gate, IO2 T/R and blanking, IO3 and IO4 the coil bridge,
IO5 the laser's shunt, IO6 and IO7 I2C (SDA, SCL), IO8 the noise source.  Everything slow (the attenuators, enables,
setpoints) is behind the PCA9555 and the MCP4728.

**What it opens, with the host:**

| experiment | tiles | beyond the board |
|---|---|---|
| pulsed NMR in a permanent magnet, 5-21 MHz: FID, spin echo, CPMG, T1, T2 | Y2, Y3, the host's DAC (the pulse at the Larmor frequency, shaped) and ADC (the echo, quadrature in gateware), Y7 to match the probe | 32 N52 cubes in a printed former, a coil, a vial |
| one-dimensional MRI | the same with Y4 on a gradient coil | a printed gradient coil |
| Earth's-field NMR at 2 kHz | Y4 prepolarizes, Y5 (or the host's x100) records | a 1000-turn coil round a bottle, outdoors |
| ESR of DPPH at 10-100 MHz (g = 2, 28 GHz/T) | Y2 at low power into a loop, Y4 on a Helmholtz pair, Y5 | coils, DPPH |
| the ionosphere: WWV's carrier Doppler (HamSCI), ionosonde chirps, WSPR and FT8 propagation, Jupiter at 20 MHz | Y5's two channels (two antennas: phase between them is direction) | an active antenna or a dipole; CLK IN on a GPSDO |
| lightning bearings and solar flares | Y6's crossed loops on both ADCs; NAA's MSK (6.04's modulation, on the air) | two 1 m wire loops |
| WWVB's time code | Y6 | a loop or a ferrite rod |
| the Smith chart, return loss, TDR, a crystal's motional arm | Y7 on both ADCs | a NanoVNA calibration kit |
| strong coupling, EIT, parametric amplification | Y8, both DACs and both ADCs | nothing |
| noise figure, radiometry, transfer functions from noise | Y9 with Y5 or AMOD-A's A4 | nothing |
| a rubidium CPT clock, NV ODMR, PDH sidebands | Y10 (with RF-MOD's or RF-MOD-2's synthesizer on its RF port), the host's photodiode | a VCSEL or a laser diode in a mount, a cell, optics |

## 4. RF-MOD-2: quadrature, a coherent transceiver and microwave physics

One MAX2871 drives both an I/Q modulator and an I/Q demodulator from its two outputs, referenced to the host's CLK
OUT: a coherent zero-IF transceiver from 400 MHz to 6 GHz whose four baseband ports are the host's four converter
channels.  Around it, the receiver's front end, a detector, a switch, a noise source, a printed coupler for
reflection, GPS, and the NV centre's resonator.

| # | cells | tile | jacks | what it does | chips (JLCPCB 2026-10-25) |
|---|---|---|---|---|---|
| X1 | (0,2)-(1,2) | I/Q modulator | I IN, Q IN, LO IN, RF OUT | ADL5375-05, 0.4-6 GHz: the host's DACs (+-1 V into 50 Ohm) through resistor networks to the chip's 0.5 V bias, 1 V p-p differential at full scale; about 0 dBm out.  Image-free Chapter 6 at 2.4 and 5.8 GHz; pulsed ODMR's gate in 8 ns steps; 120 MHz chirps for 1.25 m radar cells | ADL5375-05ACPZ C579150 (652) |
| X2 | (2,2)-(3,2) | I/Q demodulator | RF IN, LO IN, I OUT, Q OUT | ADL5380, 0.4-6 GHz, 390 MHz of baseband; I and Q differential to single-ended and re-centred to 0 V for the host's +-1 V inputs by two difference amplifiers | ADL5380ACPZ C579152 (14: accepted), THS4521 or an op amp |
| X3 | (0,3)-(1,3) | synthesizer | OUT A, OUT B, REF IN | MAX2871 (R10's circuit) with both outputs on jacks: A to X1, B to X2, one VCO, so transmitter and receiver are coherent; REF IN from the host's CLK OUT.  Carries the Pmod plug | MAX2871 (on RF-MOD) |
| X4 | (2,0) | low-noise amplifier | IN, OUT | QPL9547 (the new R5's circuit) | QPL9547TR7 C5367093 (5,070) |
| X5 | (0,1)-(1,1) | SPDT switch | COM, A, B | SKY13351, 20 MHz-6 GHz, 100 ns, from a Pmod pin: one antenna for a half-duplex link, a Dicke radiometer (antenna against X7), antenna switching | SKY13351-378LF C129189 (9,676) |
| X6 | (1,0) | log detector | IN, OUT | AD8318, 1 MHz-8 GHz, 60 dB; its 0.5-2.1 V scaled to the host's +-1 V: a power meter, a scalar network analyzer with X3, antenna patterns without a coherent receiver, total-power radiometry | AD8318ACPZ C578694 (152) |
| X7 | (2,1) | noise source | OUT | an avalanching junction and an ADL5611 gain block, switched from a Pmod pin, padded to 50 Ohm: Y-factor noise figure of X4 and RF-MOD's LNA, the Dicke reference | ADL5611ARKZ C208262 (1,597) |
| X8 | (3,0) | GPS L1 front end | ANT, OUT | a bias-T for an active antenna, the Murata 1575 MHz SAW, a MAX2659 LNA, a second SAW: real GPS for 6.06's acquisition, the satellites' codes, Doppler and delays | MAX2659ELT C28043 (17,969), SAFFB1G56KB0F0AR1X C91647 (10,050) |
| X9 | (0,0) | 2.87 GHz split-ring resonator | IN | a printed split ring over a cleared ground, fed by a tapped line, with pads for a trim capacitor: NV centres' ODMR (the diamond in the gap), DPPH's ESR at 102 mT | copper |
| X10 | (3,1) | power | | USB-C 5 V (1.5 A), PTC, TVS, bulk capacitors; every tile switches and regulates its own | |
| X11 | (2,3)-(3,3) | directional coupler | IN, OUT, CPL | a printed coupled-line coupler, about -20 dB at 2.45 GHz: the reflected wave from an antenna to X2, so X1-X3 measure S11 as a vector network analyzer does | copper |

Pmod (the plug under X3): IO1 MUXOUT, IO2 SDATA, IO3 SCLK, IO4 LE (X3), IO5 the switch's control, IO6 the noise
source, IO7 and IO8 spare.

**What it opens, with the host:**

| experiment | tiles |
|---|---|
| Chapter 6's QPSK, QAM and OFDM on the air at 2.4 and 5.8 GHz, image-free | X1 and X2 on two boards (or X1 here and RF-MOD's TRF3722) |
| a homodyne I/Q radar: Doppler with its sign, breathing and heartbeats, FMCW from DAC chirps, range-Doppler | X3 to X1 and X2, two antennas (cans, patches) |
| a vector network analyzer at 0.4-6 GHz, S21 and (with X11) S11 | X1, X2, X3, X11 |
| CW and pulsed ODMR of NV centres; Rabi, Ramsey, Hahn echo | X3 and X1 (the gate), RF-MOD's R12, X9; AMOD-2's Y10 and the host's photodiode |
| a Dicke radiometer: the Sun, a hand, the sky | X5, X7, X4, X6 |
| noise figure by Y-factor | X7, X6 |
| GPS from the satellites | X8, RF-MOD's mixer and synthesizer, the host's ADC |
| a microwave power meter, antenna patterns, Friis | X6 |

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
