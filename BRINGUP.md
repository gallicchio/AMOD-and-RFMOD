# AMOD and RF-MOD rev A: the bring-up

Written 2026-11-15, before any board was powered, for a bring-up run over chat: Jason does everything physical (looks,
cables, flips switches), the session drives the instruments from the bench PC (`bell`), judges each result against the
design's own numbers, logs it, and says exactly what to do next.  The limiting resource is Jason's time at the bench, in
short windows between other things, so the plan is cut into **visits**: one visit is one set of cables, a minute or two
of hands, and then the session measures alone.

| what | where |
|---|---|
| this procedure | `BRINGUP.md` (this file) |
| **where we are right now, and the next thing to do** | [`bringup/STATUS.md`](bringup/STATUS.md), rewritten after every step (`python3 bringup/run.py status`) |
| every visit's cabling card, with a picture | [`bringup/VISITS.md`](bringup/VISITS.md), `bringup/cards/<visit>.png` |
| the tests, their models and limits | [`bringup/tiles.py`](bringup/tiles.py): one place; the cards, the tool and the rehearsal all read it |
| the tool | [`bringup/`](bringup/README.md): `run.py`, on `~/mudd/lab-instrument-control`'s drivers |
| results | `bringup/BRINGUP_LOG.md` (one row per number judged), raw data in `bringup/data/` (not in git) |
| what rev B should change | [`bringup/REVB.md`](bringup/REVB.md) |
| the gateware that drives the Pmod lines | [`gateware/pmodbench/`](gateware/pmodbench/README.md), for the ECP5-2ADC-2DAC board |

## How a visit goes

1. I post the visit's **card**: which named cable goes on which jack (tile, printed name, row and column), what to set
   on the board, and a picture.  It also says which cables move from the last visit and which stay.
2. You cable it and type `<visit> cabled` (for example `A.v2 cabled`).  Unless the card says "stay", you can leave.
3. I run it (`run.py go A.v2`), read every number against its limits, write the log, and post the result and the next
   card.  A failure gets one re-check of the cabling by you before it is believed (a loose SMA reads as a dead tile).
4. If you come back after a gap and have lost the thread: ask "where are we?".  The answer is always `STATUS.md`'s:
   the board on the bench, what is cabled now, what passed, and the next card.

Rules of the bench:
- **Nothing is powered or driven that the card does not name.**  Generators go off and the Pmod host releases its pins
  at the end of every visit; the supply stays on until `run.py off`.
- **Change cables with the generators off** (they are, between visits).  The supply may stay on for SMA cables; it goes
  **off** before anything is plugged into a socket, a terminal or the Pmod plug.
- **The tool only talks to instruments named in `bringup/bench.json`.**  Everything else on `bell` belongs to other work
  and is not touched (not even `*IDN?`).
- One board on the bench at a time; its unit number is written on its back with a pen and told to the tool
  (`run.py board amod_a 1`).

## What I need to know before we start

1. **Which boards arrived, and how many of each are assembled.**  The plan covers all nine; the tool skips what is not
   here.
2. **Which instruments are mine** (next section): their addresses or serial numbers go into `bringup/bench.json`.
3. Whether an **ECP5-2ADC-2DAC board that has passed its own stages 1-3** (power, JTAG, a bitstream running) is free
   to be the Pmod host.  About a third of the tiles need it; the rest do not.  **On 2026-11-16 rev A's USB PROG is
   dead** (the ECP5 board's `bringup/REVB.md` rows 12 and 13: the FT2232H's VPHY and VPLL on 1.8 V, its D+ and D-
   swapped), so there is no JTAG and no serial channel from the PC until its rework: one wire, and a USB cable with D+
   and D- crossed.  Until then every visit marked HOST waits; the tool lists it as waiting and moves on to the next
   visit it can run (a visit waits whenever `bench.json` leaves one of its instruments unassigned).

## The instruments, and how each is connected

Ask for these (all have drivers in `lab-instrument-control`).  Each board uses a subset; the board's section says which.

| name here | instrument | to the PC | fixed connection |
|---|---|---|---|
| **G1, G2** | Siglent **SDG1032X** generator, CH1 and CH2 | LAN or USB | two **BNC-to-SMA-male** cables, 0.5 m, labelled G1 and G2 with tape at both ends |
| **S1-S4** | Siglent **SDS2104X Plus** scope, CH1-CH4 (it has 50 ohm inputs, which the plan uses) | LAN or USB | four **SMA-male-to-BNC** cables, 0.5 m, labelled S1-S4 at both ends.  No x10 probes |
| **PWR** | Agilent **E3646A** (the second unit: both outputs work), **output 1** | RS-232 through an FTDI adapter | a **USB-C power lead**: a USB-C plug on two wires (red to +, black to -).  Check its polarity with a meter before the first board |
| **MOT** | the same supply's **output 2** (one output switch serves both: the tool keeps it at 0 V except during a test that uses it) | | a **5.5 x 2.1 mm barrel plug on two leads, centre +**, for AMOD-M's jack (its motor drivers are below their minimum supply on USB alone: `bringup/REVB.md` 1.5); two clip leads for PhMOD h4's VM terminal |
| **HOST** | an **ECP5-2ADC-2DAC rev A** board running `gateware/pmodbench/build/pmodbench.bit` | its USB PROG to the PC | the tile board's Pmod plug straight into the host's **Pmod A** socket (the lower one on its right edge).  **Rev A only**: the rev A plugs and rev A's sockets are both non-standard and mate only with each other (`bringup/REVB.md` 1.15); never a standard Pmod host, module or cable |
| **P1, P2** | HP **8720ES** network analyzer, ports 1 and 2 | GPIB 16 through the Prologix adapter | its two test cables, labelled P1 and P2, with a **full two-port calibration at their ends for 50 MHz to 6 GHz, 1601 points** (every analyzer visit uses that one sweep; the tool refuses to change it, because that would switch the calibration off) |
| **SA** | Rigol **DSA875** spectrum analyzer | USB | one SMA cable, labelled SA (the most it is given here is a synthesizer's +5 dBm) |
| (rails) | scope CH1-CH3 again, only in the power stage | | three **BNC-to-clip** leads (x1) and four male-male jumper wires for the rails socket |

Small parts: **three 50 ohm SMA terminators**, **three short SMA male-male cables** (15 cm), **two SMA female-female
barrels** (for the thru calibration), **one BNC tee**, two clip leads, one jumper cap, male-male jumper wires.  The kit parts (motors, a speaker, an HB100, a loopstick coil...) are
only for the last stage of each board and are listed there and in `docs/KIT.md`.

Levels: every generator number in this plan is **volts peak to peak into 50 ohm**, and the tool sets the generator's
load to 50 ohm so its display agrees.  A jack that is not terminated on the board sees twice that.  The cards say which
scope input (50 ohm or 1 Mohm) each cable uses; the tool sets it.

**Before the first board: the thru calibration, `CAL` (2 minutes, once).**  G1 straight into S1 and G2 straight into
S2 (each generator cable joined to its scope cable with an SMA barrel).  `run.py cal` sweeps 100 Hz to 30 MHz and keeps
the result; every later sweep is divided by it.  It also proves the eight cables and the scope's 50 ohm setting.

## The stages of a board

| stage | what | your time | needs |
|---|---|---|---|
| `X.inspect` | unpowered, with a loupe, against the short list on the card (from the board's DOA list); photograph both sides | 5 min | |
| `X.setup` | DIP switches and jumpers to the bring-up's defaults; every tile's slide switch DOWN | 1 min | |
| `X.plug` | (boards with a Pmod plug, before their first HOST visit) both boards unpowered, the plug in the host's Pmod A, an ohmmeter from an SMA shell of one board to an SMA shell of the other: under 1 ohm, or the plug is mirrored (`bringup/REVB.md` 1.15) | 1 min | a meter |
| `X.power` | (boards with a USB-C) 1 V, 3 V, 5 V from the supply with a low current limit; the rails on the scope where the board has a rails socket; then **the walk**: the supply's display shows a tile's name, you slide that tile's switch UP, the tool reads the step in current, the display moves to the next | 5 min, staying | PWR (S1-S3) |
| `X.v1 ...` | generator and scope: two tiles a visit, more when a tile needs no generator | 1-2 min each, then leave | G, S, PWR |
| `X.host1 ...` | the same with the Pmod plug in the host: clocks, SPI, bits | 1-2 min each | + HOST |
| `X.hands1 ...` | things that need a change between measurements (a DIP way, a jumper, a terminator) | 3-5 min each, staying | |
| `X.rf1 ...` | network analyzer, one pair of jacks a visit; done as one sitting, a cable move every half minute | 10-20 min a board, staying | P1, P2 |
| `X.sa1 ...` | spectrum analyzer: the synthesizers, the mixers, the noise source | 1-2 min each | SA, HOST |
| `X.kit1 ...` | with a part from outside the board: a motor, a speaker, a coil | when the part is on hand | |

Suggested order of boards: **AMOD-P** first (no power, nothing to damage: it proves the bench), **AMOD-A** (first
power, the op-amp tile every other board reuses), **AMOD-N** (generator-and-scope first; its analyzer sitting whenever
the 8720ES is here), **RF-MOD**, **AMOD-C**, **PhMOD**, **IQ-MOD**, **AMOD-M**, **AMOD-B**.  Any order works; the tool
keeps each board's place.

## Every visit, at a glance

`G1->a2 IN` means generator cable G1 on tile a2's jack printed IN; `S1(50)<-` is scope cable S1 with the scope's 50 ohm
input (no mark: 1 Mohm); `P1-`, `P2-` the analyzer's ports; `HOST` the Pmod plug in the host.  The full cards (rows,
columns, limits, pictures) are in [`bringup/VISITS.md`](bringup/VISITS.md).

<!-- visits:start -->
```
AMOD-P (passive blocks)
  P.inspect  look it over, unpowered
  P.setup    set the switches and jumpers
  P.v1       G1->p1 IN, S1(50)<-p1 OUT, G2->p2 IN, S2<-p2 OUT
  P.v2       G1->p3 IN, S1<-p3 OUT, G2->p4 IN, S2(50)<-p4 OUT
  P.v3       G1->p5 IN, S1(50)<-p5 OUT, G2->p6 IN, S2(50)<-p6 OUT
  P.v4       G1->p7 IN, S1(50)<-p7 OUT, G2->p8 IN, S2(50)<-p8 OUT
  P.v5       G1->p9 IN, S1(50)<-p9 OUT, G2->p10 IN, S2<-p10 OUT
  P.v6       G1->p11 IN, S1<-p11 100ns, S2<-p11 200ns, S3<-p11 300ns, S4(50)<-p11 OUT
  P.hands1   G1->p4 IN, S1(50)<-p4 OUT | 3 parts, a change between each
  P.hands2   G1->p12 IN, S1<-p12 IN | 4 parts, a change between each
  P.kit1     (no cable) p13.loopstick | 330 uH AM loopstick coil (KIT.md); a 5-turn loop of hookup wire on a BNC clip lead
AMOD-A (active blocks)
  A.inspect  look it over, unpowered
  A.setup    set the switches and jumpers
  A.power    first power: staircase, rails, the switch walk
  A.v1       G1->a2 IN 50R, S1<-a2 OUT, G2->a3 IN 50R, S2<-a3 OUT
  A.v2       G1->a4 IN 50R, S1<-a4 OUT, S2<-a5 OUT, G2->a7 IN 1K, S3<-a7 VCO OUT, S4<-a8 TEMP OUT
  A.v3       G1->a9 RF IN, G2->a9 LO IN, S1<-a9 IF OUT
  A.v4       G1->a10 DRIVE IN, S1(50)<-a10 S OUT, S2(50)<-a10 X OUT, S3<-a11 RX OUT, S4<-a12 MIC OUT
  A.plug     the Pmod plug's orientation, unpowered
  A.host1    G1->a6 IN 10K, S1<-a8 TEMP OUT, S2<-a11 RX OUT, HOST | first: a male-male jumper wire from a11's TX socket pin 1 to its RX socket pin 1 (the left pin of each, as printed TX and RX)
  A.hands1   G1->a10 DRIVE IN, S1(50)<-a10 S OUT, S2(50)<-a10 X OUT | first: a 50 ohm SMA terminator on a10's DUT jack
  A.kit1     (no cable) a5.HB100 | HB100 Doppler module, three jumper wires
  A.kit2     (no cable) a12.speaker and microphone | 4-8 ohm speaker, 2 W; electret capsule
AMOD-N (network analyzer pieces)
  N.inspect  look it over, unpowered
  N.setup    set the switches and jumpers
  N.v1       G1->n1 THRU (the top-left one), S1(50)<-n1 THRU (the bottom-right one), G2->n2 IN, S2(50)<-n2 OUT 1, S3(50)<-n2 OUT 2
  N.v2       G1->n3 SUM, S1(50)<-n3 PORT 1, S2(50)<-n3 PORT 2, G2->n5 IN, S3(50)<-n5 OUT
  N.v3       G1->n7 RF, S1(50)<-n7 RF+DC, G2->n10 IN, S2(50)<-n10 OUT
  N.v4       G1->n11 IN, S1<-n11 OUT, G2->n6 IN, S2<-n6 OUT
  N.plug     the Pmod plug's orientation, unpowered
  N.host1    G1->n8 IN, S1(50)<-n8 OUT, G2->n9 TUNE, S2(50)<-n9 OUT, HOST
  N.hands1   G1->n11 IN, S1<-n11 OUT | first: n11 DIP: way 2 (49.9 ohm) ON as well as way 1
  N.hands2   (no cable) n7.DC path | first: two clip leads from the supply's output 2 to the DC and GND test loops
  N.hands3   (no cable) n10.OUT floats
  N.hands4   G1->n8 IN, S1(50)<-n8 OUT, HOST | first: n8 DIP: way 1 (SPI) OFF, way 8 (16 dB) ON, ways 2-7 OFF
  N.rf1      P1-n1 THRU (the top-left one), P2-n1 THRU (the bottom-right one)
  N.rf2      P1-n1 LOAD
  N.rf3      P1-n1 25 OHM
  N.rf4      P1-n1 SHORT
  N.rf5      P1-n1 OPEN
  N.rf6      P1-n2 IN, P2-n2 OUT 1 | first: a 50 ohm terminator on n2 OUT 2
  N.rf7      P1-n2 IN, P2-n2 OUT 2 | first: a 50 ohm terminator on n2 OUT 1
  N.rf8      P1-n3 SUM, P2-n3 PORT 1 | first: a 50 ohm terminator on n3 PORT 2
  N.rf9      P1-n3 PORT 1, P2-n3 PORT 2 | first: a 50 ohm terminator on n3 SUM
  N.rf10     P1-n4 IN, P2-n4 OUT
  N.rf11     P1-n5 IN, P2-n5 OUT
  N.rf12     P1-n7 RF, P2-n7 RF+DC
  N.rf13     P1-n10 IN, P2-n10 OUT
  N.rf14     P1-n11 IN
  N.rf15     P1-n8 IN, P2-n8 OUT, HOST
RF-MOD (RF blocks)
  R.inspect  look it over, unpowered
  R.setup    set the switches and jumpers
  R.power    first power: staircase, rails, the switch walk
  R.v1       S1(50)<-r9 REF OUT, G1->r1 LO, G2->r1 RF, S2(50)<-r1 IF
  R.rf1      P1-r2 IN, P2-r2 OUT
  R.rf2      P1-r4 IN, P2-r4 OUT
  R.rf3      P1-r5 IN, P2-r5 OUT | first: r5's slide switch UP
  R.rf4      P1-r12 IN, P2-r12 OUT | first: r12's slide switch UP
  R.plug     the Pmod plug's orientation, unpowered
  R.sa1      SA<-r10 OUT A+, HOST | first: an SMA cable from r9 REF OUT to r10 REF IN; a 50 ohm terminator on r10's other output; r10's slide switch UP
  R.sa2      SA<-r10 OUT A-, HOST | first: an SMA cable from r9 REF OUT to r10 REF IN; a 50 ohm terminator on r10's other output; r10's slide switch UP
  R.sa3      G1->r7 IF, SA<-r7 RF, HOST | first: an SMA cable from r10 OUT A+ to r7 LO; an SMA cable from r9 REF OUT to r10 REF IN; a 50 ohm terminator on r10 OUT A-
  R.sa4      G1->r8 IF, SA<-r8 RF, HOST | first: an SMA cable from r10 OUT A+ to r8 LO; an SMA cable from r9 REF OUT to r10 REF IN; a 50 ohm terminator on r10 OUT A-
  R.sa5      G1->r13 I IN, SA<-r13 RF OUT, HOST | first: an SMA cable from r9 REF OUT to r10 REF IN (the back trace carries it on to r13); r13's slide switch UP; r10's slide switch UP too: with r10 off, r13's programming and the reference back-power it (REVB 1.13)
AMOD-C (conversion)
  C.inspect  look it over, unpowered
  C.setup    set the switches and jumpers
  C.power    first power: staircase, rails, the switch walk
  C.v1       G1->c2 LOAD 50R, S1<-c2 BUCK~, S2<-c2 LDO~, G2->c9 IN+ 50R, S3<-c9 OUT
  C.v2       G1->c10 IN 50R, S1<-c10 OUT, G2->c11 CV 50R, S2<-c11 OUT /4.9
  C.v3       G1->c12 IN 50R, S1<-c12 |IN|
  C.plug     the Pmod plug's orientation, unpowered
  C.host1    S1<-c3 OUT /5.7, S2<-c3 CAP /5.7, G1->c4 IN 50R, S3<-c4 OUT, G2->c5 IN 50R, S4<-c5 OUT, HOST
  C.host2    G1->c6 IN 10K, G2->c7 IN 50R, S1<-c7 OUT, HOST
  C.host3    G1->c8 IN 20K, G2->c8 DAC 20K, HOST
  C.hands1   G1->c10 IN 50R, S1<-c10 OUT | first: c10: jumper ON the CE header's two pins
PhMOD (physics)
  H.inspect  look it over, unpowered
  H.setup    set the switches and jumpers
  H.power    first power: staircase, rails, the switch walk
  H.v1       G1->h3 LINE, G2->h3 TX IN, S1<-h3 RX OUT, S2(50)<-h3 PROBE, S3<-h4 MON
  H.v2       G1->h5 IN A, G2->h5 IN B, S1<-h5 OUT A, S2<-h5 OUT B
  H.v3       G1->h6 LOOP, S1<-h6 OUT, G2->h7 DRIVE, S2(50)<-h7 INC, S3(50)<-h7 REFL
  H.v4       G1->h8 SIG, S1(50)<-h8 OUT 1, G2->h10 SET, S2<-h10 MON | first: a 50 ohm SMA terminator on h10's LD jack (never a laser for this test)
  H.plug     the Pmod plug's orientation, unpowered
  H.host1    G1->h2 IN, S1(50)<-h2 OUT, S2(50)<-h9 OUT, HOST | first: h2 OUT straight into the scope's 50 ohm input: never open, never a tee
  H.hands1   G1->h7 DRIVE, S1(50)<-h7 INC, S2(50)<-h7 REFL | first: a 50 ohm SMA terminator on h7's DUT jack
  H.hands2   (no cable) h8.coupled tanks
  H.kit1     (no cable) h4.coil driver | 22 ohm, 10 W resistor; two clip leads from supply output 2
IQ-MOD (quadrature)
  Q.inspect  look it over, unpowered
  Q.setup    set the switches and jumpers
  Q.power    first power: staircase, rails, the switch walk
  Q.v1       G1->q6 IN, S1<-q6 OUT
  Q.plug     the Pmod plug's orientation, unpowered
  Q.host1    G1->q3 REF IN, G2->q1 I IN, S1(50)<-q2 I OUT, S2(50)<-q2 Q OUT, HOST | first: SMA cables: q3 OUT A+ to q1 LO IN, q3 OUT A- to q2 LO IN, q1 RF OUT to q2 RF IN; q1's, q2's and q3's slide switches UP
  Q.rf1      P1-q4 IN, P2-q4 OUT | first: q4's slide switch UP
  Q.rf2      P1-q5 IN, P2-q5 OUT | first: 50 ohm terminators on q5 FWD and REFL
  Q.rf3      P1-q5 IN, P2-q5 FWD | first: 50 ohm terminators on q5 OUT and REFL
  Q.rf4      P1-q5 IN, P2-q5 REFL | first: 50 ohm terminators on q5 OUT and FWD
  Q.rf5      P1-q8 ANT, P2-q8 OUT | first: q8's slide switch UP; ANT carries 3.3 V DC: fine for the 8720ES's port, NOT for a NanoVNA without a DC block
  Q.rf6      P1-q9 IN, P2-q9 OUT
  Q.rf7      P1-q11 RFC, P2-q11 RF1, HOST | first: a 50 ohm terminator on q11 RF2
  Q.sa1      G1->q3 REF IN, SA<-q3 OUT A+, HOST | first: q3's slide switch UP; a 50 ohm terminator on q3's other output
  Q.sa2      G1->q3 REF IN, G2->q1 I IN, SA<-q1 RF OUT, HOST | first: an SMA cable from q3 OUT A+ to q1 LO IN; a 50 ohm terminator on q3 OUT A-; q1's and q3's slide switches UP
  Q.sa3      SA<-q4 OUT, HOST | first: an SMA cable from q7 OUT to q4 IN; q4's and q7's slide switches UP
AMOD-M (motors)
  M.inspect  look it over, unpowered
  M.setup    set the switches and jumpers
  M.power    first power: staircase, rails, the switch walk
  M.v1       S1<-m2 VM /16, S2<-m4 IA 10K, S3<-m4 IB 10K, S4<-m5 I 1V/A, MOT->m2's barrel jack "5-16V"
  M.v2       S1<-m6 I 1V/A, S2<-m6 VD /52, S3<-m7 I 1V/A, S4<-m9 OUT
  M.v3       S1<-m10 OUT, S2<-m11 OUT, G1->m8 PWM 50R, S3<-m8 VO /16, S4<-m8 I 1V/A
  M.plug     the Pmod plug's orientation, unpowered
  M.host1    S1<-m3 V /13, S2<-m3 I 1V/A, MOT->m2's barrel jack "5-16V", HOST
  M.hands1   (no cable) m9.hall
  M.hands2   (no cable) m10.optical
  M.kit1     (no cable) m3.motor and encoder | N20 gear motor with encoder, PH 6-way cable; 12 V on the barrel jack
  M.kit2     (no cable) m4.stepper | NEMA 17 stepper, XH 4-way cable; 12 V on the barrel jack
  M.kit3     (no cable) m5.servo | SG90 or MG90S servo
  M.kit4     (no cable) m6.solenoid and flyback | 5 V or 12 V solenoid; jumper cap; 12 V on the barrel jack
  M.kit5     (no cable) m7.bridge amplifier | 8 ohm, 5 W resistor or speaker
  M.kit6     (no cable) m11.load cell | 1 kg load cell, XH 4-way
AMOD-B (brushless)
  B.inspect  look it over, unpowered
  B.setup    set the switches and jumpers
  B.power    first power: staircase, rails, the switch walk
  B.v1       S1<-b2 VM /16, S2<-b3 IA .75V/A, S3<-b3 IB .75V/A, S4<-b8 VIB
  B.v2       S1<-b9 IDX, S2<-b10 HA, S3<-b10 HB, S4<-b11 IPA 1V/A
  B.v3       S1<-b12 I 1V/A, S2<-b7 ANG
  B.plug     the Pmod plug's orientation, unpowered
  B.host1    G1->b3 COAST 50R, S1<-b4 EA /14, S2<-b4 EB /14, HOST
  B.kit1     (no cable) b5.gimbal motor | GBM2804H-100T gimbal motor; 6 x 2.5 mm diametric magnet; M2 / M2.5 screws; 12 V on the barrel jack; a piezo disc for b8
```
<!-- visits:end -->

## What each stage retires from the dead-on-arrival lists

| DOA item (docs/DOA_*.md) | retired by | if it fails |
|---|---|---|
| SOT-23 family turned (every powered tile's P-FET, the op amps) | `X.power`'s walk: a turned P-FET shows no step or a short; then the tile's own test | compare with an unassembled board's footprint; one part to turn by hand |
| USB-C, PTC, TVS, the LM2664 and the 3.3 V LDO | `X.power`: staircase and rails | a reversed lead or TVS shows as constant-current at 1 V, with nothing hot |
| AMOD-A: OPA847 (a4), 4046 (a7), MC1496 (a9), PAM8302 on its MSOP-8 (a12), DRV8837 (a11) | A.v2, A.v3, A.host1, A.kit2 | each is one tile; the others do not depend on it |
| AMOD-C: the DMMT3904W pairs' pinout (c9, c10), LF398, MAX7410, ICL7660A, TMUX4053 | C.v1, C.v2, C.host1-3 | |
| AMOD-N: PE43711 and its DIP (n8), the transformers' dots (n3, n10, n11), the varactor (n9), SHORT/OPEN/LOAD (n1), the stub (n4) | N.v1-v4, N.host1, N.rf1-15 | n8 by the switches if the SPI fails; n10's float by a meter |
| RF-MOD: MAX2871 (r10), TRF3722 (r13), GALI-84+ and QPL9547 orientation (r12, r5), the SAW's pads (r4), the TCXO's turn (r9), ADL5350 (r7, r8), ADEX-10L+ (r1) | R.power (currents), R.v1, R.rf1-4, R.sa1-5 | the reference can come from the generator if the TCXO is dead |
| PhMOD: THS3491 (h2) and its +-15 V, the diode pairs (h3), LMH6629 pinout (h5, h9), the FETs of h10, DRV8876 (h4) | H.power, H.v1-v4, H.host1, H.kit1 | h2 is only ever run terminated in 50 ohm; h10 never sees a laser here |
| IQ-MOD: the three footprints from JLCPCB's drawings (q8, q11), the LFCSPs (q1, q2, q6), the couplers' direction (q5) | Q.power (currents), Q.v1, Q.host1, Q.rf1-7, Q.sa1-3 | |
| AMOD-M and AMOD-B: the drivers' pinouts, the level shifts, the SPI sharing | M.host1, B.host1 with no motor at all; then the kit stage | a motor only after the no-motor tests pass |
| The Pmod plug's mirror (fixed before the order) | the first `host` visit of each board: every line does what its tile expects | |
| The 50 ohm lines, launches and fences (never measured) | N.rf1 (THRU), R.rf1-2, Q.rf6 to 6 GHz | measured against the cable, as the DOA lists ask |

## The gateware, and what has been rehearsed

- `gateware/pmodbench/`: a bitstream for the ECP5-2ADC-2DAC board that puts both Pmod sockets under the PC's control
  over the board's serial channel (per-pin direction, four clock generators a port, an SPI engine, a bit-density
  counter that can close a delta-sigma loop, a frequency counter, a quadrature decoder, a logic capture), with drivers
  for the MAX2871, PE43711, TRF3722, MT6701 and LSM6DSO and a pin profile per board that refuses to drive a line the
  tile drives.  It needs only the host's power, JTAG, oscillator and UART, so it depends on stages 1-3 of the host's
  own bring-up (`~/OpticsPCBs/ECP5-2ADC-2DAC/BRINGUP.md`) and nothing later.
  - Simulated, not run on a board: `make sim` (77 checks of the RTL against models of the chips and tiles), `make test`
    (84 checks: the Python driver's own bytes through the RTL in iverilog), `make mutants` (18 planted bugs, 18 caught),
    sigrok's SPI decoder reading the captured waveforms back; the bitstream meets 25 MHz with 84 MHz to spare on paper.
  - `python3 -m pytest bringup/test_host_cosim.py`: every call the plan makes on the host, for each of the eight
    boards with a plug, through that driver into the simulated FPGA with the board's tile model in Pmod A.
  - Its models were written from the same data sheets as its driver (and two parts' sheets are missing: REVB.md 2a.12),
    so a pass shows the driver and the gateware agree, not that the silicon does.
- `bringup/`: `python3 -m pytest bringup/` runs every visit of every board against a simulated bench (the instruments'
  words, each tile's model, noise, an 8-bit scope that clips), shows that a good board passes all 144 measured tests
  and that boards broken on purpose (a dead tile, half the gain, a shifted resonance, swapped cables, a silent host)
  fail the right ones.  `run.py go <visit> --sim` rehearses any visit by hand.
- Not rehearsable: that the models are right.  They are worked from the netlists and the datasheets; where the first
  board disagrees, the number in `tiles.py` changes and the reason goes into `bringup/REVB.md`.
