# Rev B: what to change, and what is still open

Started 2026-11-15, while the bring-up plan was written and before any rev A board was powered.  This is the one list:
anything the bench, the gateware or the documents show that a rev B should change, each with what showed it.  Rows
found on paper say so; the bench confirms or strikes them, and the row then says which visit and which number.

State words: **predicted** (worked out from the netlist or a datasheet, not yet seen), **measured** (a visit's number
is quoted), **struck** (the bench showed it is not a problem; kept, crossed out, so it is not found twice).

## 1. Faults in a tile

| # | board, tile | what | evidence | state | change |
|---|---|---|---|---|---|
| 1.1 | AMOD-C c11 (555) | The CV jack is DC-coupled to the 555's control pin through 2.2 k, with 51 ohm from the jack to ground.  With nothing on CV that is 2.25 k from pin 5 to ground, across the chip's own divider, so the thresholds sit far below 2/3 and 1/3 of the supply and the tile does not run at the 6.9 kHz the silk and the handbook print.  Worked from the netlist: about 11 kHz if the divider is 5 k a leg, about 14 kHz in narrow pulses if it is 100 k a leg (a CMOS 555's). | `out/amod_c_tiles.json`: `51(0,CV) 2.2k(CV,CT)`, CT = pin 5; the arithmetic is in `bringup/tiles.py` beside the test | predicted; C.v2 reads the frequency and the duty | Couple CV through a capacitor, or sum it into pin 5 through 22 k or more with no DC path to ground, or drop the 51 ohm and say "high-impedance source"; then correct the silk |
| 1.2 | AMOD-N n9 (oscillator) | "10.5 MHz with TUNE at 0 V" is true only with a source holding TUNE at 0 V.  With the jack open the varactor's cathode is at 3.3 V (100 k to the rail and nothing to ground), not (3.3 V + TUNE) / 2, so the tile runs at the top of its range. | netlist: `100k(TUNE,T) 100k(VS,T)`, no resistor from TUNE to ground | predicted; N.host1 drives TUNE at 0, -2 and +2 V | 100 k from TUNE to ground (then the open jack is the 0 V case), or say it on the back panel |
| 1.3 | AMOD-A a2, a3 (and every "x10" or "x100" figure that quotes them) | The silk and the handbook give the bandwidths as 140 MHz divided by the gain: 14 MHz for a2, 1.4 MHz for a3.  140 MHz is the OPA810's bandwidth at gain 1; its gain-bandwidth product is 70 MHz, so the corners should measure about 6.9 MHz and 0.69 MHz. | TI's data sheet (`datasheets/OPA2810IDR_C1849413.pdf`: GBWP 70 MHz); `boards/amod_a.py`'s notes | predicted; A.v1 reads both corners | Correct the silk ("7 MHz", "0.7 MHz"), the handbook and the back panel's plots; a tile that needs 14 MHz at x10 wants the OPA847 or two stages |

## 2. Things the bring-up could not reach without hands

The rule since 2026-10-29 (CLAUDE_PCB.md section 9, "remote first") is newer than these boards.  What it would have
bought here, counted from the plan (`BRINGUP.md`):

| # | what | cost in this bring-up | change |
|---|---|---|---|
| 2.1 | **No bench power entry and no way to read a tile's current.**  Power is USB-C only; the supply's one number is the whole board. | A hand-made USB-C lead; the "walk" (one switch at a time, 5 minutes a board, a person present) is the only per-tile current reading | A 2-pin bench header beside the USB-C that bypasses nothing but the cable; where a tile's current is a DOA item (the gain blocks, the LNAs, the modulators), a 0.1 ohm shunt with Kelvin pads or an INA on the rail |
| 2.2 | **RF-MOD, PhMOD and IQ-MOD have no rail access at all**: no rails socket, no test point; their rails are judged by an LED and by whether the tiles work. | PhMOD's +-15 V and RF-MOD's 7.8 V cannot be measured without a probe on a capacitor | The rails socket on every powered board (AMOD-A's, with the extra rails), or a jack per rail (CLAUDE_PCB.md section 9: every test point a jack) |
| 2.3 | **Every tile's power is a slide switch.** Right for a student; for the bench it is one sitting per board, and no test can power a tile down to read its neighbour. | the walk; "slide switch UP" in thirty cards | Keep the switch; add one host line (or a jumper) that turns every tile on, wired-OR with the switches |
| 2.4 | **Outputs that end on a terminal or a socket and nowhere else**: a12's speaker drive, a11's transmit bridge, m4's, m5's, m6's and m7's outputs, b3's phases (b4 reads two of three). | Each needs a part from the kit or a jumper wire before it can be judged; a11 is tested with a wire from its TX socket to its RX socket | A divided monitor jack on each driven output, as m3's V and m8's VO already are |
| 2.5 | **A Pmod line's level cannot be seen from the tile board**, and nothing loops a host output back to a host input. | A wrong line is found only by its tile not working; the host's own capture memory is the one witness | One spare line looped (IOx to IOy through 1 k) on each board, and a row of test pads, in plug order, by the plug |
| 2.6 | **DIP switches and jumpers that a test must change** (p4, p12, p13, a10, n8, n11, c10, h8, m6) | nine "hands" sittings | Unavoidable on the passive boards; on the powered ones an analog switch on a host line where the choice is part of an experiment worth automating (a10's range, h8's coupling) |
| 2.7 | p12 (LEDs) has one jack, so its I-V curve needs a tee; a10 does the same job with two outputs | one hands sitting with a tee | none: p12 is the passive board's version by design |

## 2a. The Pmod lines when no host holds them

Found while the host driver's pin profiles were written (`gateware/pmodbench/README.md`): what each line does when the
FPGA's pin is high-impedance, which is the state of every board on USB power alone, of a host before it is configured,
and of the driver's `safe()`.  Rows marked *checked* were read against the netlist and the part's data sheet; the
others come from a reviewer's reading and are to be checked before they are believed.

| # | board, tile | what | state | change |
|---|---|---|---|---|
| 2a.1 | AMOD-B b5, b6 | CS ENC (IO6, also the buffer's enable) and CS IMU (IO8) have no pull-ups: with the host absent both float, and the buffer and the IMU can drive MISO against each other. | checked on the netlist; predicted on the bench | 100 k to 3.3 V on each |
| 2a.2 | PhMOD h10 | IO5 high shunts the laser's current; 100 k holds it low.  So an absent host, an unconfigured FPGA and `safe()` all mean "laser on at whatever SET says".  The driver's `use('phmod')` drives IO5 high for that reason. | checked | Turn the line round (low or floating = blanked), or pull it up: a laser's idle state should be off |
| 2a.3 | RF-MOD r13 | The TRF3722's LE (IO6) has no pull, r10's has 100 k down, and the two chips share SCLK and SDATA: a floating LE on r13 while r10 is written.  The driver holds the other chip's LE low. | checked | 100 k down on r13's LE |
| 2a.4 | AMOD-N n8 | LE has its 100 k up; SI and CLK have none and float when released. | checked | 100 k down on each |
| 2a.5 | AMOD-C c3, c4, c6, c7 | The clock buffers' inputs (IO6, IO3), the flip-flop's clock (IO1) and the LF398's LOGIC pin (IO5) float with no host: the charge pump and the filter may be clocked by noise, and the track-and-hold's state is undefined.  It also makes those tiles' supply currents in the power walk unreliable. | the buffers checked on the netlist (no pull on IO6 or IO3); the rest a reviewer's reading | 100 k down on every host line that reaches a CMOS input |
| 2a.6 | PhMOD h9, IQ-MOD q7 | The TPS22917's "smart" pull-down lets go once ON has been high, so a line that is released after being driven high may stay on.  `safe()` drives these low before it releases them. | checked against TI's data sheet | 100 k down beside the chip |
| 2a.7 | AMOD-A a11 | The Pmod lines reach the DRV8837 crossed against the handbook's names: IO4 is its IN2, IO3 its IN1.  Harmless for antiphase bursts (the test's use); it matters when one side is held. | checked | Correct the handbook, or swap the lines |
| 2a.8 | AMOD-A a12 | IO2 is DC-coupled through 10 k into the PAM8302's input node: a line held high or low puts DC into the amplifier's input.  The profile leaves IO2 high-impedance until it is used. | a reviewer's reading | A series capacitor on the one-bit path |
| 2a.9 | RF-MOD r10, r13 | Programming one synthesizer with the other tile's slide switch off drives an unpowered chip's pins through the host's 33 ohm. | a reviewer's reading | Series 1 k on the shared lines, or one switch for both |
| 2a.10 | AMOD-M m3 | The encoder's A and B lines have no pull-ups and no series resistors. | a reviewer's reading | 10 k up, 1 k in series |
| 2a.11 | PhMOD h4 | The DRV8876's undervoltage lockout (to 4.6 V) against USB's 5 V less a Schottky: on USB alone it may not start. | a reviewer's reading; H.kit1 will show | Say "12 V" on the silk, or a lower-drop diode |
| 2a.12 | every board | `datasheets/` lacks the MT6701, LSM6DSO, DRV8311H, DRV8251A, SN74LVC1G79 and AO3400A: the driver's encoder and IMU helpers were written from the handbook's description, and nobody could check what the two motor drivers do with floating inputs. | checked (the folder) | Fetch them (`scripts/jlc_datasheet.py`) before the first host visit of AMOD-B and AMOD-M |

## 3. Documents and silkscreen

| # | where | what | change |
|---|---|---|---|
| 3.1 | every board's back panel | The inputs' terminations are not all the same and the silk says so only on some jacks ("IN 50R", "IN 1K", "IN 10K"): a generator set for 50 ohm puts twice its setting on a6's, c6's, c8's, h6's and n9's jacks.  The plan's numbers allow for it; a student's will not. | Print the input resistance beside every input jack, as AMOD-A and AMOD-C mostly do |
| 3.2 | PhMOD h7 | DRIVE's own input resistance depends on the DUT (100 ohm open, 75 ohm matched, 50 ohm shorted): the generator's level moves with the DUT.  REFL / INC is right all the same, because INC moves with it. | A line in the handbook |
| 3.3 | IQ-MOD q8 | ANT carries 3.3 V DC by design (an active antenna's supply).  Safe for the 8720ES's port; a NanoVNA or a generator needs a DC block. | Already on the back; print "3.3 V DC" beside the jack on the front as well |

## 4. Open questions for the bench (not faults until measured)

- The supply currents in `tiles.py`'s walk tables are estimates from datasheet typicals.  After the first board of each
  kind, replace them with what it read and tighten the windows.
- The cable's capacitance (`cable_pf` in `bench.json`, 75 pF by default) moves every corner measured into the scope's
  1 Mohm input (p2, p3, a9's IF OUT).  Measure it once in `CAL` and set it.
- Whether the SDS2104X Plus's forced acquisition is quick enough for a 45-point sweep in under 30 s over the LAN.
- The 50 ohm lines above 3 GHz (the DOA lists' stitching note): N.rf1's THRU, R.rf1 and Q.rf6 against the cable.

## Inbox

Lines added from the bench by `run.py revb "..."`, to be sorted into the tables above.
