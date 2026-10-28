# Analog Devices' university labs against the six boards

Prompt 18, 2026-10-28.  Jason: "Look at these sets of labs from Analog Devices:
https://wiki.analog.com/university/courses/electronics/labs ... I think that there is value in building most of these
things on a breadboard with individual ICs, but if there are some labs here that fit in the spirit of these boards (along
with the ECP5 2DAC 2ADC board), if we are missing something, let's see if we can add it.  Whole areas that we are missing
include power regulation and other component-level circuits, but something like a switched capacitor filter or details of
their Delta - Sigma Modulator, if there is room, might be worth it."

A survey by a Claude subagent: every lab page's objective and parts list, and JLCPCB's stock of the parts a tile would
need.  The six boards are full, so the candidates below are the tiles of a possible seventh board (`PLAN.md` section 12).

**Scope.** I read the objective and parts list of every page the ADI index links to (109 pages, index revision of Nov 2021). Two of them, the Wien-bridge oscillator and Efficiency/Power Loss, returned HTTP 403, so I judged them by title.

## 1. ADI labs by topic
C = already covered, B = breadboard-only, T = candidate tile

| Topic | Labs | Status |
|---|---|---|
| Background | Breadboards, breadboard parasitics, resistor and capacitor notes, real sources | B: these are about the breadboard and the instrument |
| Passive | Ohm, RC and RL transients, low/high-pass, band-pass, band-stop, RLC resonance, cascaded RC | C on AMOD-P. Band-stop and cascaded RC are B (they need swappable parts) |
| Op amps | Basics, comparator, settling time, loop gain by injection | C on AMOD-A. Settling time and loop gain are T (C8, C3) |
| Junctions | Diode I/V, junction capacitance, ΔT sensor, zener | C on AMOD-A's I/V and heater tiles and PhMOD's varactors |
| Devices | BJT/MOS as a diode, I/V curves | T: a three-terminal curve tracer (AMOD-A's I/V tile has two terminals) |
| Stages | CE, CS, frequency response, CE loop gain, followers, class B/AB | Frequency response is T (C9). The rest is B |
| Bias | Mirrors, zero-gain amplifier, stabilized and ΔVBE current sources, reference, shunt regulator | The mirror is T (C9). The others are B: they need pots, and the hand-wiring is the lesson |
| Differential pair | BJT/MOS pair, transresistance input, triangle-to-sine, full amplifier | T (C9). The full amplifier is B |
| CMOS analog | Inverter amplifier with chopper, analog switches, switched-capacitor circuits | Switches and switched-capacitor circuits are T (C4, C6). The inverter amplifier is B |
| Conversion | Flash/VFC/SAR/dual-slope ADCs, R-2R DAC, first-order ΔΣ | First-order ΔΣ is C on AMOD-A. The rest is T (C5, C7, C11) |
| Oscillators | CMOS LC, Hartley, Colpitts, Clapp, Peltz, pulsed, Wien, LDR, multivibrators | C on AMOD-P and AMOD-P2. Wien is a weaker T. LDR and multivibrators are B |
| Misc devices | Optocoupler isolation amplifier, SCR, ideal-diode rectifier | The isolation amplifier is a weaker T. SCR is B |
| Logic | TTL, CD4007 gates, XOR, latch, level shifting, LFSR | B: wiring the gates is the lesson, and the LFSR belongs in the FPGA |
| Comms | PLL, diode ring, active mixer, envelope and FM detectors, PWM, VGA, tuned amplifiers, self-resonance, transformers, transmission lines | C on AMOD-A, RF-MOD, AMOD-P2, AMOD-P and PhMOD. VGA is B |
| Filters | Sallen-Key/MFB active filters, RC polyphase | Weaker T |
| Sensors | LED sensor, PV cell, speaker, heartbeat, TMP01, magnetic, tilt, IC temperature, electret, piezo | Mostly C. The rest is B: they need a body, a magnet, light or motion |
| **Power** | Switched-capacitor supplies (LT1054), buck basics, efficiency, open-loop buck/boost (LTC6992 + LTC7001), closed-loop buck and boost, negative reference, DC-DC I and II | **The real gap**: T (C1 to C3) |

## 2. Candidate tiles
JLCPCB stock on 2026-10-28, given as LCSC code, units in stock, unit price. Parts are Extended unless marked Basic.

**C1. LDO vs buck, with an electronic load (2 cells, USB 5 V).**
- Parts: TLV62568DBVR buck, 5 V→3.6 V (C163219, 79.6k, $0.07), feeding an LP5907-3.3 LDO (C80670, 35k, $0.17) or the poor-PSRR XC6206P332 (C5446, Basic, 535k). The load is OPA2810 + AO3400A (C20917, Basic) + 10 Ω, giving I = V_DAC/10 Ω; a Pmod line switches a separate step load.
- Jacks: LOAD, I-LOAD, SW÷5, BUCK~ and LDO~ (AC-coupled, for ×10/×100 gain), VOUT÷4.
- Measurements:
  - MHz ripple before and after the LDO
  - load steps
  - Zout(f): DAC sine on the load, the two ADCs read I and V
  - dropout
  - pulse-skipping at light load

**C2. Charge pump (1 cell, Pmod 3.3 V).**
- Parts: ICL7660AIBAZA-T (C7881, 22k, $0.95), with its OSC pin clocked from a Pmod line. LM2664 (C108573, 163k, $0.33, fixed 80 kHz) is the modern contrast.
- Jacks: VOUT÷4, VOUT~, the flying-capacitor node, LOAD.
- Measurements: Rout ≈ 1/(fC) + switch resistance while the FPGA sweeps the pump clock; ripple vs load. Check the OSC drive levels.

**C3. FPGA-driven power stage (1–2 cells, 5 V).**
- Parts: DRV8837DSGR H-bridge (C39159, 70k, $0.26) used as two half-bridges into two inductors, giving a two-phase buck. Its PWM limit is about 250 kHz; verify that.
- The FPGA replaces ADI's LTC6992/LTC7001 and the compensator.
- Measurements:
  - output vs duty cycle
  - inductor ripple, computed as ∫(SW−VOUT)dt
  - ripple cancellation from interleaving
  - a digital loop whose Bode plot comes from injecting into the duty word

**C4. Switched-capacitor filter (2 cells, 5 V).**
- Parts, cell 1: MAX291ESA+T, 8th-order Butterworth with fclk/fc = 100 (C596390, 46, $11.58), or LTC1069-6IS8, elliptic (C674326, 61, $14.86). MAX7400 is in stock only as PDIP (46). The FPGA clock needs a TTL-threshold 5 V buffer (not checked).
- Measurements, cell 1: the corner frequency tracks the clock; aliases at fclk ± fin; clock feedthrough; the staircase output.
- Cell 2 is a discrete switched-capacitor resistor/integrator, as in ADI lab 19: 2× SN74LVC1G3157 (C10426, 212k, $0.09) and OPA2810, with non-overlapping clocks from the FPGA.
- Measurements, cell 2: R = 1/(fC), charge-injection steps, the error from clock overlap.

**C5. Second-order ΔΣ with its internals visible (2 cells, ±5 V).**
- Parts: OPA2810 integrators (C1849413, 3.5k, $2.54), TLV3501AIDBVR comparator (C193413, 4.2k, $1.93), and SN74LVC1G79 flip-flop (C42878, 12.6k, $0.18). The flip-flop drives a 1G3157 switch that selects ±REF3033 (C36658, 30.7k, $0.46), so the one-bit DAC is clean rather than an FPGA pin.
- Jacks: IN, INT1, INT2, FB. Bitstream and clock go over the Pmod.
- Measurements: integrator swing and overload; 40 dB/decade shaping vs AMOD-A's 20; idle tones; ENOB after sinc3 decimation.
- Optional black-box comparison: AD7401A (C194166, 274, $4.91, external clock) with a B0505S-1W isolated supply (C234073, 848). Too little stock: AD7403 (6), ADuM7703 (0), AMC1306M05 (0).

**C6. Track-and-hold (1 cell, ±5 V).**
- Parts: LF398MX/NOPB (C2864267, 2.6k, $1.76; ±5 V is its minimum supply) with an external hold capacitor and the hold command from the Pmod. The discrete alternative is OPA2810 + TMUX1134 (C2866620, 6.2k, $3.15).
- Measurements: acquisition time, droop, pedestal vs input, feedthrough, aperture delay.

**C7. R-2R DAC + comparator, so the FPGA can run SAR, tracking and dual-slope conversions (1–2 cells, 3.3 V).**
- Parts: 0.1 % resistors (not checked). The stocked 4816P-R2R network (C1731693, 36) is only ±2 %. The comparator is TLV3501.
- Measurements: DNL/INL read by the 12-bit ADC, the major-carry glitch, a trace of the SAR's decisions.

**C8. Voltage-feedback vs current-feedback amplifier (1 cell, ±5 V).**
- Parts: OPA690IDBVR (C524799, 6.7k, $3.24) vs OPA695IDBVR (C138301, 3.5k, $2.73) or LMH6702 (C2059900, 4.5k, $1.95). OPA691 has only 8 in stock. Rg is switched by TS5A3157 (C353034, 9k).
- Measurements: bandwidth vs gain (the CFB part may exceed the 23 MHz ADC unless Rf is raised), slew, settling.

**C9. Transistor blocks (2 cells, ±5 V).**
- Parts: DMMT3904W matched NPN pair (C155305, 4.6k, $0.16), BCV62 PNP mirror (C139953, 1.2k, $0.36).
- Cell A: differential pair with mirror load. Measurements: tanh transfer from the two DACs, gm vs tail current, triangle-to-sine THD, mirror Rout.
- Cell B: common-emitter vs cascode. Measurement: Miller-limited bandwidth, which breadboard parasitics would swamp.

**C10. Precision rectifier + multiplier (2 cells, ±5 V).**
- Rectifier: OPA2810 + BAT54S (C8592, 260k). Measurements: dead zone, and the zero-crossing glitch vs frequency.
- Multiplier: AD835ARZ (C26332, 156, $25.81). AD633 and MPY634 are out of stock. It takes the ±1 V DACs directly. Measurements: four-quadrant DC accuracy, doubling, phase detection, RMS, division.

**C11. 555 / VCO (1 cell, 5 V).**
- Parts: TLC555CDR (C6986, 96.8k, $0.23).
- Jacks: CAP÷4, CV from the DAC, OUT to the Pmod, where the FPGA counts frequency.
- Measurements: thresholds, f vs V, a VFC used as an ADC.

**Weaker candidates:** Wien bridge with MMBF4391 JFET amplitude control (C153770, 18.5k), and an HCNR201 opto isolation amplifier (C9066, 8.3k, $1.98).

**Not checked:** adjustable LDOs, a 5 V clock buffer, 0.1 % resistors, a current-sense amplifier, and whether the passives fit each cell.
