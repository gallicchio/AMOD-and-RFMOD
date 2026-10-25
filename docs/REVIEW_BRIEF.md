# Design-review brief: AMOD-P, AMOD-A, RF-MOD and the Icepi Pmod adapter, rev A (2026-10-25)

For a reviewer (a person or another model) who has not seen the night's work.  Read in this order, then answer the
questions at the end with evidence (a datasheet page, a rule, a measurement), not opinion.

## What the boards are

Two 100 x 100 mm boards of analog "tiles" for an FPGA-plus-ADC/DAC teaching module (the ECP5-2ADC-2DAC board,
tutorial at `~/mudd/133electronics/icepi-zero-dac-adc/tutorial/`, Appendix D is the brief).  Each tile is a 20 mm
cell between two vertical SMA jacks (IN top-left, OUT top-right), the circuit drawn on the silkscreen as it is
wired.  AMOD-P (two layers) is thirteen passive tiles: attenuators, RC and LC filters, resonators, a delay line, a
clipper, an AM loopstick.  AMOD-A (four layers) is twelve active tiles on USB-C power with a slide switch and P-FET
per tile: two gain blocks, an OPA847 LNA, a Johnson-noise amplifier, a delta-sigma comparator, a 4046 PLL, a
heater with a TMP235, an MC1496 mixer, an LED current source with a photodiode receiver, a 40 kHz ultrasound pair,
a class-D speaker amplifier with an electret preamplifier; a 2 x 6 Pmod plug carries the FPGA's lines.

RF-MOD (four layers) is ten RF tiles on 50 ohm coplanar waveguide: a resistive splitter, 2.45 GHz LTCC and 915 MHz
SAW filters, two GALI-84+ gain blocks, power with a 7.8 V boost and a 25 MHz TCXO reference, two ADL5350 mixers and
two MAX2871 synthesizers on a Pmod (one complete link on one reference; `PLAN.md` section 6).  Its tiles take IN at
the top-left jack and OUT at the bottom-right.  The fourth board, `icepi_adapter/`, is the tutorial's 2x12 Icepi Zero
adapter grown to 80 x 30 mm with a Pmod socket on In2-routed lines.

## Where everything is

- `PLAN.md`: the decisions with their reasons, the tile tables as built, the parts and the stock on the day.
- `boards/amod_p.py`, `boards/amod_a.py`, `boards/rf_mod.py`: each tile's netlist, placement and wires in one place (the source of
  truth; the schematic and the board are generated from it and checked against it).
- `scripts/parts.py`: every part with its LCSC code, checked against JLCPCB's API (`scripts/jlc_cache.json`
  keeps the answers and their times).
- `hardware/*.kicad_sch`, `hardware/*.kicad_pcb`: the KiCad 10 files; `out/<stem>/`: gerbers, BOM, placement
  files, assembly notes, renders; `docs/images/`: the renders; `docs/HANDBOOK_*.md`: what each tile does and what
  to expect; `docs/DOA_amod_a.md`, `docs/DOA_rf_mod.md`: the assumptions to confirm.
- `~/OpticsPCBs/CLAUDE_PCB.md`: the rule book the boards were designed to (section 17 is this project's lessons).
- `CLAUDE_CODE_CHAT.md`: the night's record, with the reasons for every deviation from the plan.

## The checks already run (every build)

ERC 0; the schematic's connectivity equal to the declared netlist; every board wire ending on a pad of its net;
DRC 0 at 0.2 mm clearance, 0.3 mm hole clearance, 0.15 mm silk clearance; the gerbers parsed; 3D models resolved;
BOM and placement files complete with order codes; every LCSC code's description matched to value and package;
stock above 100 for every part on the day.

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
7. **Every Pmod pin, on both mating halves** (the plugs on AMOD-A and RF-MOD, the ECP5 board's and the adapter's
   sockets), by pad position against the body, not by pad number: rev A's first layout got this wrong once.

Answer as a numbered list of findings, each with the file and line (or the tile and part), the evidence, and the
fix.  "Looks fine" without evidence is not a finding.
