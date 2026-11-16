# Rev B: what to change, and what is still open

Started 2026-11-15, while the bring-up plan was written and before any rev A board was powered.  This is the one list:
anything the bench, the gateware or the documents show that a rev B should change, each with what showed it.  Rows
found on paper say so; the bench confirms or strikes them, and the row then says which visit and which number.

State words: **predicted** (worked out from the netlist or a datasheet, not yet seen), **measured** (a visit's number
is quoted), **struck** (the bench showed it is not a problem; kept, crossed out, so it is not found twice).

## 1. Faults in a tile

**Since 2026-11-16 these are faults on built boards** (Jason: "Some of the AMOD and RF-MOD boards were ordered and came
in.  I haven't tested them.").  Each row's *change* is a rework of rev A where one is worth it, and rev B's fix; each is
measured at the bring-up visit its *state* names before it is believed.

| # | board, tile | what | evidence | state | change |
|---|---|---|---|---|---|
| 1.1 | AMOD-C c11 (555) | The CV jack is DC-coupled to the 555's control pin through 2.2 k, with 51 ohm from the jack to ground.  With nothing on CV that is 2.25 k from pin 5 to ground, across the chip's own divider, so the thresholds sit far below 2/3 and 1/3 of the supply and the tile does not run at the 6.9 kHz the silk and the handbook print.  Worked from the netlist: about 11 kHz if the divider is 5 k a leg, about 14 kHz in narrow pulses if it is 100 k a leg (a CMOS 555's). | `out/amod_c_tiles.json`: `51(0,CV) 2.2k(CV,CT)`, CT = pin 5; the arithmetic is in `bringup/tiles.py` beside the test | predicted; C.v2 reads the frequency and the duty | Couple CV through a capacitor, or sum it into pin 5 through 22 k or more with no DC path to ground, or drop the 51 ohm and say "high-impedance source"; then correct the silk |
| 1.2 | AMOD-N n9 (oscillator) | "10.5 MHz with TUNE at 0 V" is true only with a source holding TUNE at 0 V.  With the jack open the varactor's cathode is at 3.3 V (100 k to the rail and nothing to ground), not (3.3 V + TUNE) / 2, so the tile runs at the top of its range. | netlist: `100k(TUNE,T) 100k(VS,T)`, no resistor from TUNE to ground | predicted; N.host1 drives TUNE at 0, -2 and +2 V | 100 k from TUNE to ground (then the open jack is the 0 V case), or say it on the back panel |
| 1.3 | AMOD-A a2, a3 (and every "x10" or "x100" figure that quotes them) | The silk and the handbook give the bandwidths as 140 MHz divided by the gain: 14 MHz for a2, 1.4 MHz for a3.  140 MHz is the OPA810's bandwidth at gain 1; its gain-bandwidth product is 70 MHz, so the corners should measure about 6.9 MHz and 0.69 MHz. | TI's data sheet (`datasheets/OPA2810IDR_C1849413.pdf`: GBWP 70 MHz); `boards/amod_a.py`'s notes | predicted; A.v1 reads both corners | Correct the silk ("7 MHz", "0.7 MHz"), the handbook and the back panel's plots; a tile that needs 14 MHz at x10 wants the OPA847 or two stages |
| 1.4 | AMOD-A a9 (mixer) | **HIGH.**  The MC1496's bias resistor R904 (3.9 k) returns BIAS (pin 5) to -5V, which is also VEE (pin 14), instead of to ground.  So the tail current is zero, the mixer does not mix, and IF OUT sits at VS.  The generator's "1 mA" is the figure for a return to ground.  Even with R904 fixed, +-5 V misses two of the MC1496's bias rules (carrier - signal >= 2.7 V, collector - carrier >= 2 V): low headroom. | Pin audit 2026-11-16, `../PIN_AUDIT.md` section 1: R904.2 = -5V = U901.14; MC1496DR2G_C7295.txt:208-212 "R5 is the resistor between Pin 5 and ground", :225-227; `boards/amod_a.py:601, 616` | predicted (pin audit; checked here against the MC1496 data sheet, "R5 is the resistor between Pin 5 and ground"); A.v3's a9 test reads it | R904 pin 2 to GND (I5 = (5 - 0.75) / 4.4 k = 0.97 mA); measure the headroom at bring-up, or raise the collector supply |
| 1.5 | AMOD-M m3, m4 (DRV8251A x3: U301, U401, U402) | **HIGH.**  VMOT is +5V through the SS34 D203: 4.10-4.9 V on USB alone.  That is below the DRV8251A's 4.5 V minimum and inside its 4.15-4.45 V lockout band.  The drivers may not start, or may drop out under load.  They are fine from the 5-16 V jack. | `../PIN_AUDIT.md` section 1; fetched_drv8251a.txt:217 "VVM 4.5 48 V", :290-294; other_SS34_C8678.txt:74 | predicted (pin audit) | "Motors need the jack" on the silk and in the handbook, or an ideal-diode or P-FET OR instead of D203 |
| 1.6 | PhMOD h4 (DRV8876, its MON op amp) | **HIGH.**  VM = h4_VS through the B5819W D401, 4.04-4.65 V on USB alone, against the DRV8876's 4.5 V minimum (UVLO rising 4.3-4.6 V).  The OPA810 MON buffer U402 is also on VM, against its 4.75 V minimum.  At the 1.3 A chopping limit VM falls to about 4.0-4.3 V.  This settles 2a.11 on paper. | `../PIN_AUDIT.md` section 1; DRV8876PWPR_C575551.txt:268, :386-389; fetched_opa810.txt:211 | predicted (pin audit); H.kit1 will show | "12-18 V" on the silk; power U402 from h4_VS, not VM; or a lower-drop OR |
| 1.7 | AMOD-C c5 (TMUX4053) | **HIGH.**  The analog switch's VDD (c5_VS, 4.64-5.25 V) is below its 5 V minimum.  It will probably switch, with more on-resistance, but the data sheet promises nothing below 5 V. | `../PIN_AUDIT.md` section 1; fetched_tmux4053.txt "VDD ... 5 24 V" | predicted (pin audit) | Accept and document; or a switch rated from 1.8-2.7 V (TMUX1xxx, 74LVC1G3157 class); or VDD from a higher rail |
| 1.8 | AMOD-C c7 (LF398) | **HIGH.**  The sample-and-hold runs below its +-5 V minimum on both rails (about 4.6-4.9 V each).  The guaranteed input range shrinks to about -0.8..+1.2 V, which excludes the handbook's IN = -1 V. | `../PIN_AUDIT.md` section 1; LF398MX_NOPB_C2864267.txt:253 | predicted (pin audit) | Limit IN to -0.7..+1 V in the handbook and silk, or give c7 +-6 V or more |
| 1.9 | AMOD-A (AMOD-B close) | MEDIUM.  The -5V load with every op amp tile on is 47 mA typical and 54 mA maximum (32-39 mA on AMOD-B), against the LM2664's 40 mA.  -5V sags to about -4.4 V typical and as low as -3.2 V worst case, which makes 1.4 and 1.8 worse. | `../PIN_AUDIT.md` section 1 | predicted (pin audit) | Budget the tiles that are on; a larger inverter |
| 1.10 | AMOD-C c2; PhMOD h6, h10 | MEDIUM.  Four OPA810s run single-supply on a 5 V tile rail (4.64-5.25 V), against their 4.75 V minimum: in spec at a 5.0 V source, out at USB's 4.75 V. | `../PIN_AUDIT.md` section 1; fetched_opa810.txt:211 | predicted (pin audit) | Return V- to -5V where the board has it, or an op amp specified from 2.7 V |
| 1.11 | IQ-MOD q1, q2, q7 | MEDIUM.  The ADL5375, ADL5380 and ADL5611 need 4.75-5.25 V; their switched rails reach 4.62-4.64 V at USB's minimum and the board's ~0.9 A. | `../PIN_AUDIT.md` section 1 | predicted (pin audit) | The kit's 5.1 V / 3 A supply on the silk, or a lower-drop input path |
| 1.12 | PhMOD h1 (TPS65131) | MEDIUM.  The set points sit at the edges of the adjustable range: -15V is -15.02 V nominal, -15.80..-14.25 V worst case, against VNEG -15..-2 V; +15V is 14.89 V nominal, 14.33..15.46 V worst case, against <= 15 V. | `../PIN_AUDIT.md` section 1; TPS65131RGER_C87663.txt:240-241 | predicted (pin audit) | R102 to 1.27 M (about -14.7 V), and trim the positive divider likewise |
| 1.13 | RF-MOD r10, r13 | MEDIUM.  With r10 switched off, programming r13 (shared SDATA/SCLK), LE, and REF when it is cabled drive the unpowered MAX2871 past VCC + 0.3 V and back-power r10's 3.3 V.  This confirms 2a.9 from the data sheet and extends it to REF. | `../PIN_AUDIT.md` section 1; MAX2871.txt:82 | predicted (pin audit) | Keep r10 on while r13 or REF is in use; 1 k in series on the shared lines, or one switch for both |
| 1.14 | AMOD-B b3 (DRV8311H) | MEDIUM, *uncertain*.  SOA and SOB are pulled below their -0.3 V absolute maximum (about -0.6 V, 0.33 mA each) while the DRV8311 sleeps, which is the default with SW301 off. | `../PIN_AUDIT.md` section 1; fetched_drv8311.txt:412, :2858 | predicted (pin audit); settle by measuring SOA with b3 off | A Schottky clamp to GND, or move the offset network behind a buffer |
| 1.15 | every plug board, and `icepi_adapter/` | HIGH, *uncertain*: **the Pmod plug's orientation**.  The plugs were drawn to mate with ECP5-2ADC-2DAC rev A's J303/J304 and the Icepi adapter's J3 (IO1 at the end where KiCad's horizontal socket puts its pad 1).  Those sockets appear to be mirrored end to end against the Pmod spec's figure 5 (`~/OpticsPCBs/ECP5-2ADC-2DAC/bringup/REVB.md` row 14).  If so, a bought Pmod host gives these plugs +3V3 on IO1 and puts their VCC and GND on host I/O.  On 2026-11-16 the original Icepi adapter (`~/OpticsPCBs/IcepiZeroADCDAC/adapters/`, board `adda12p`) is being redrawn to the spec, so the plugs and this repo's copy of the adapter must change with it before ordering.  On the ECP5 rev A board, spec plugs then go in upside down (IO1-4 and IO5-8 swap; the `.lpf` or profile swaps them back). | `../PIN_AUDIT.md` section 1 (INFO, the plug footprint) and its connector section (check 3, being added 2026-11-16); spec `~/OpticsPCBs/IcepiZeroADCDAC/datasheets/pmod-interface-specification-1_3_1.pdf` figures 2 and 5 | **accepted** (Jason, 2026-11-16): rev B to the standard; the rev A boards are marked non-standard and used only with ECP5-2ADC-2DAC rev A, whose J303/J304 are non-standard the same way.  Each board's `X.plug` step (an unpowered ground-to-ground check through the plug) confirms the pair before its first host visit | Rev B: the plug's pads to the Pmod specification's figure 2 (a module's plug), with ECP5 rev B and the redrawn Icepi adapter; `icepi_adapter/` replaced by the redrawn files when they are ready.  A rev A board in a standard host fits only upside down, with IO1-4 and IO5-8 swapped in the host's pin file.  The handbooks, KIT.md and the README say "rev A: ECP5-2ADC-2DAC rev A only" wherever they say to plug in |

The pin audit's LOW and INFO rows (lock-detect LED current, R801's rating, REF OUT's swing, X901's pad 1, the c5
integrator's sign in the handbook, the plug footprint's stale docstring, and others) are in `../PIN_AUDIT.md`
section 1, with their changes.

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
