# Design-review brief: AMOD-P, AMOD-N, AMOD-A, AMOD-C, AMOD-M, AMOD-B, RF-MOD, PhMOD (was AMOD-2), IQ-MOD and the Icepi Pmod adapter, rev A (2026-10-25; AMOD-N, AMOD-C, AMOD-M and AMOD-B 2026-10-28)

For a reviewer (a person or another model) who has not seen the night's work.  Read in this order, then answer the
questions at the end with evidence (a datasheet page, a rule, a measurement), not opinion.

## What the boards are

Nine 100 x 100 mm boards of analog and RF "tiles" for an FPGA-plus-ADC/DAC teaching module (the ECP5-2ADC-2DAC board,
tutorial at `~/mudd/133electronics/icepi-zero-dac-adc/tutorial/`, Appendix D is the brief).  Each tile is a 20 mm
cell between two vertical SMA jacks (IN top-left, OUT bottom-right, so every jack is 14.85 mm or more from every
other on the board), the circuit drawn on the silkscreen as it is
wired.  AMOD-P (two layers) is thirteen passive tiles: attenuators, RC and LC filters, resonators, a delay line, a
clipper, an AM loopstick.  AMOD-N (four layers, `PLAN.md` sections 11 and 12) is eleven tiles, nine passive: calibration
standards at the jacks' pins, a resistive and a transformer splitter, a quarter-wave stub, an
LTCC low-pass, a zero-bias diode detector, a bias-T, a 1:1 balun with a floating output and a 1:4 transformer; and two on
the Pmod's 3.3 V with no USB: a PE43711 step attenuator set by an 8-way switch or the Pmod's SPI lines, and a
one-transistor Clapp oscillator.  Every tile has a panel on the back (its limits, its loads, its supply) and most a plot
of the response to expect (`PLAN.md` section 12).
AMOD-A (four layers) is twelve active tiles on USB-C power with a slide switch and P-FET
per tile: two gain blocks, an OPA847 LNA, a socket and amplifier for an HB100 Doppler module, a delta-sigma comparator, a 4046 PLL, a
heater with a TMP235, an MC1496 mixer, an impedance and I-V tile (V and I for the host's two ADCs), a 40 kHz ultrasound pair,
a class-D speaker amplifier with an electret preamplifier; a 2 x 6 Pmod plug carries the FPGA's lines.

AMOD-C (four layers, twelve tiles, `PLAN.md` section 15) is conversion: a buck and an LDO with an electronic load, a
charge pump, a switched-capacitor filter and integrator, a second-order delta-sigma modulator, an LF398 track-and-hold,
a SAR comparator, a differential pair, a cascode, a 555 V-to-F and a precision rectifier.  AMOD-M (four layers, eleven
tiles, `PLAN.md` section 14) is motors on a 5-16 V supply: a DRV8251A for a DC motor with its encoder and two for a
stepper on the Pmod; a servo, a solenoid with a jumper-chosen flyback, a TCA0372 bridge amplifier and a TPS28225 buck
stage from DACs; a hall, an optical and a load-cell amplifier for their loops.  AMOD-B (four layers, twelve tiles,
`PLAN.md` section 14) is a brushless gimbal motor on a 5-12 V supply: a DRV8311H in 3x PWM from three Pmod lines with
COAST from a DAC, the motor on four slots over an MT6701 encoder, two halls and an index sensor; its back-EMF, phase
and bus currents (an INA240 in line), its vibration, and an LSM6DSO sharing the SPI with the encoder through a buffer.

RF-MOD (four layers) is ten RF tiles on 50 ohm coplanar waveguide: a diode-ring mixer (ADEX-10L+), 2.45 GHz LTCC and 915 MHz
SAW filters, a QPL9547 LNA and a GALI-84+ gain block, power with a 7.8 V boost and a 25 MHz TCXO reference, two
ADL5350 mixers, a MAX2871 synthesizer with both of its complementary outputs on jacks and a TRF3722 quadrature transmitter on a Pmod (one complete link on one
reference; `PLAN.md` section 6, `PLAN_LEVEL2.md` section 2).

The second level is built for the ECP5-2ADC-2DAC board's two DACs and two ADCs (`PLAN_LEVEL2.md`).  PhMOD (AMOD-2 until Prompt 17; four
layers, ten tiles, DC-30 MHz): a THS3491 1 W pulse amplifier on +-15 V from a TPS65131, NMR's passive duplexer with an
OPA847 preamplifier, a DRV8876 coil driver, two LMH6629 receive channels, an OPA810 VLF loop amplifier, a 50 ohm
reflection bridge, two passive coupled LC tanks with BB133 varactors, an avalanche-noise source and a laser driver with
an RF bias-T.  IQ-MOD (four layers, eleven tiles, 0.4-6 GHz): an ADL5375 modulator and an ADL5380 demodulator sharing
one MAX2871's two complementary outputs, a dual directional coupler (two HHM22137A1), a QPL9547 LNA, an AD8318 log
detector, an ADL5611 noise source, a MAX2659 GNSS front end, a SKY13370 switch and a broadband ODMR loop.  Its tiles take IN at
the top-left jack and OUT at the bottom-right too.  The fourth board, `icepi_adapter/`, is the tutorial's 2x12 Icepi Zero
adapter grown to 80 x 30 mm with a Pmod socket on In2-routed lines.

## Where everything is

- `PLAN.md`: the decisions with their reasons, the tile tables as built, the parts and the stock on the day.
- `PLAN_LEVEL2.md`: the same for PhMOD and IQ-MOD, with every change from their plan and its reason.
- `boards/amod_p.py`, `boards/amod_n.py`, `boards/amod_a.py`, `boards/amod_c.py`, `boards/amod_m.py`, `boards/amod_b.py`,
  `boards/rf_mod.py`, `boards/phmod.py`, `boards/iq_mod.py`: each tile's netlist, placement and wires in one place (the source of
  truth; the schematic and the board are generated from it and checked against it).
- `scripts/parts.py`: every part with its LCSC code, checked against JLCPCB's API (`scripts/jlc_cache.json`
  keeps the answers and their times).
- `hardware/*.kicad_sch`, `hardware/*.kicad_pcb`: the KiCad 10 files; `out/<stem>/`: gerbers, BOM, placement
  files, assembly notes, renders; `docs/images/`: the renders; `docs/HANDBOOK_*.md`: what each tile does and what
  to expect; `docs/DOA_*.md` (one per board): the assumptions to confirm.
- `~/OpticsPCBs/CLAUDE_PCB.md`: the rule book the boards were designed to (sections 17-26 are this project's lessons).
- `CLAUDE_CODE_CHAT.md`: the night's record, with the reasons for every deviation from the plan.

## The checks already run (every build)

ERC 0; the schematic's connectivity equal to the declared netlist; every board wire ending on a pad of its net;
DRC 0 at 0.2 mm clearance, 0.3 mm hole clearance, 0.15 mm silk clearance; the gerbers parsed; 3D models resolved;
BOM and placement files complete with order codes; every LCSC code's description matched to value and package;
stock above 100 for every part on the day, except the ADL5380 (14), which Jason accepted (`stock_exception`).

## What to review, with evidence

1. **Circuit function per tile** against the handbook's "expect" line: is the gain, bandwidth, bias and level
   right for the part chosen?  (The MC1496 bias on +-5 V, the 4046's VCO range with R1 10 k / C1 1 nF, the
   TLV3501's reference and integrator, the current source's headroom, the PAM8302's input network.)
2. **Pin assignments** listed in `docs/DOA_amod_a.md` items 1-11, each against the datasheet's package drawing.
3. **Rails**: the -5 V polygon on L3 and the +3.3 V strip; the LM2664's 40 mA against the sum of the tiles.
4. **The Pmod plug's feeds** in the bottom margin: 0.2 mm tracks through 0.74 mm gaps, 0.3 mm from the edge.
5. **Anything the silkscreen says that the copper does not do.**
6. **RF-MOD's RF:** the CPWG geometry against the JLC04161H-7628 stack, the launch voids, the MAX2871 loop filter
   (`PLAN.md` section 6: 80-120 kHz, 61 degrees, from CostasLink's `sim/budget.py` method), the ADL5350's crossover
   in place of the datasheet's tuned tanks, the GALI-84+ bias (22 ohm from 7.8 V).
7. **The two parts placed at 45 degrees on AMOD-P** (p8's HC-49S crystal, p9's ceramic resonator): their placement
   rotation in `out/amod_p/` against JLCPCB's preview.
8. **Every Pmod pin, on both mating halves** (the plugs on AMOD-A, RF-MOD, PhMOD and IQ-MOD, the ECP5 board's and the adapter's
   sockets), by pad position against the body, not by pad number: rev A's first layout got this wrong once.
9. **PhMOD's power and pulse path:** the TPS65131's dividers and inductor choice, the THS3491's RGT pin table and
   thermal pad (on ground), the +-15 V back tracks' width for h2's peaks, h3's crossed diodes against a 1 W pulse.
10. **PhMOD's analog tiles:** h7's REFL = 2A - 2B with the OPA810 (bandwidth at 30 MHz), h8's tank frequencies with the
    BB133's C-V curve (`docs/DOA_phmod.md` 5), h10's loop stability (1 k / 10 nF integrator, 100 ohm into the AO3401's
    gate) and its 100 mA/V scale, h4's DRV8876 mode pins and IPROPI gain.
11. **IQ-MOD's front ends:** the ADL5375 baseband networks (0.5 V common mode, +-0.34 V swing), the ADL5380's output
    difference amplifiers, the three footprints drawn from JLCPCB's drawings (MAX2659, the 1109 SAW, SKY13370),
    and q9's loop and its keep-out.
12. **The back panels** (each board module's `BACK` and `BACK_PLOTS`, drawn by `gen_pcb.back_panels`; the bottom-side
    renders in `docs/images/`): is every number the tile's own limit (input level, load, supply, duty), is anything a
    user could damage a tile with missing, and does each plot's shape match the handbook's "expect" line?
13. **n8's hand mode:** the PE43711's direct parallel mode with P/S and the seven bits on the DIP switch (100 k
    pull-downs) and LE pulled up by 100 k, against pSemi's Table 9 and its power-up rules.
14. **AMOD-C's converters:** c6's two integrators and their swing against the 3.3 V comparator, c7's LF398 hold
    capacitor and droop, c2's electronic load's loop and the buck's TRIM, c3's ICL7660A clocked from Pmod IO6 through
    a 5 V buffer (`docs/DOA_amod_c.md`).
15. **AMOD-M's power stages:** the DRV8251A's VREF and IPROPI scaling (m3, m4), m7's TCA0372 dissipation and its
    references from one chain off VMOT, m8's TPS28225 dead time and bootstrap from a DAC's PWM, m6's avalanche
    demonstration against the NCE6020AK's single-pulse rating (`docs/DOA_amod_m.md`).
16. **AMOD-B's drive:** the DRV8311H's strap pins left open (3x PWM, 9 A trip, 1 V/A), COAST's comparator on AVDD, the
    passive 3.3 k / 10 k level shift of SOA and SOB to -5 V, the MT6701's MODE on its pull-up, the LSM6DSO's unused pins,
    and the five SPI lanes and the encoder's lines on the back between the gimbal's slots (`docs/DOA_amod_b.md`).

Answer as a numbered list of findings, each with the file and line (or the tile and part), the evidence, and the
fix.  "Looks fine" without evidence is not a finding.
