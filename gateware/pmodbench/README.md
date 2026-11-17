# pmodbench: the ECP5-2ADC-2DAC board's two Pmod sockets from the PC

A small bitstream for the ECP5-2ADC-2DAC rev A board (LFE5U-25F, CABGA256, speed 6) and a Python driver, so a
tile board of this repository (AMOD-A/B/C/M/N, RF-MOD, IQ-MOD, PHMOD) plugged into a Pmod can be driven and read
over the FT2232H's serial channel with nobody at the bench.  It uses as little of the host board as it can: the
25 MHz TCXO (no PLL), the UART, the LEDs and the sixteen Pmod pins.  The converters' static pins and the PHY's
reset are held where the host's own `blink.v` holds them, and CLK OUT carries the TCXO as it does there (RF-MOD's
r10 and IQ-MOD's q3 take their 25 MHz reference from it).

**Written and simulated on 2026-11-15; nothing here has run on a board.**  See "What is verified" at the end.

| file | what |
|---|---|
| `rtl/pmodbench.v` | The top level: UART, register bus, the global registers, two `pmod_port`s, the capture, LEDs. |
| `rtl/pmod_port.v` | One socket: per pin an output bit, an enable, a lock, a synchronised input and a 4-bit source select; four clock generators; an SPI engine; a one-bit sampler; a frequency counter; a quadrature decoder. |
| `rtl/capture.v` | The logic analyser: 16 pins, 16384 samples, a sample every (div + 1) x 40 ns, optional trigger. |
| `rtl/vendor/uart.v`, `regbus.v` | The host board's UART and register bus, copied unmodified (each file's header says from where). |
| `constraints/vendor/ecp5_2adc_2dac.lpf` | The host board's pin constraints, copied unmodified.  `constraints/pmodbench.lpf` adds only the Pmod pins' settings: **no internal pull** (a released pin is high-Z and the tile's own resistors decide), 8 mA, slow edges. |
| `sim/models.v`, `sim/tiles.v` | Models of the tiles' chips and a "socket" that wires them to the eight lines as each tile does, with its pull resistors and checkers. |
| `sim/tb_pmodbench.v` | The self-checking testbench (`make sim`, 77 checks). |
| `sim/tb_cosim.v`, `host/simlink.py`, `host/test_sim.py` | The co-simulation (`make test`, 84 checks): the driver's own bytes through the simulated UART, live. |
| `host/test_mutants.py` | 18 planted bugs, each in a temporary copy, each caught (`make mutants`). |
| `host/pmodbench.py` | The driver and its command line.  `host/max2871.py`, `host/trf3722.py`: the two synthesizers' register arithmetic.  `host/vendor/max2871_regs.py`: CostasLink's proven MAX2871 arithmetic, copied unmodified. |
| `build.sh`, `Makefile` | `make sim`, `make test`, `make mutants`, `make bit`.  Tools: the oss-cad-suite (`OSS_CAD_SUITE`). |
| `build/pmodbench.bit` | The bitstream (240 kB), kept in git; everything else in `build/` is ignored. |

## Loading (a person at the board; no script here does it)

```sh
openFPGALoader -c ft2232 build/pmodbench.bit        # into the FPGA: until the next power cycle
openFPGALoader -c ft2232 -f build/pmodbench.bit     # into the flash: it boots by itself from then on
python3 host/pmodbench.py ident                     # {'id': 0x504D4231, 'version': '20261115', 'gate_s': 1.0}
```

**On ECP5 board A, never `-f`**: its flash holds the ECP5 bring-up's own design (`bringup.bit`, ID 0xEC5BA2D2),
so the board boots into that, and pmodbench goes into the FPGA at every sitting and after every power cycle.  The
driver names that design when it finds it.  Rev A's USB PROG works only after its FT2232H rework and through the labelled
USB-A-to-C cable with D+ and D- crossed (the ECP5 board's `bringup/REVB.md` rows 12 and 13).

LED0 blinks at 1.5 Hz when the bitstream is alive.  At power-up **every Pmod pin is high-Z** and stays so until
the driver is told which board is in the socket.  The serial channel is the FT2232H's channel B (found under
`/dev/serial/by-id`; pass the port as the first argument otherwise), 1 Mbaud.

## Pins

| tile's name | Pmod pin | FPGA port | ball (A) | ball (B) |
|---|---|---|---|---|
| IO1, IO2, IO3, IO4 | 1, 2, 3, 4 | `pmod[0..3]` | R15, P15, N16, M16 | L16, N14, M14, L14 |
| IO5, IO6, IO7, IO8 | 7, 8, 9, 10 | `pmod[4..7]` | R16, P16, M15, L15 | P14, M13, L13, L12 |

Pins 5 and 11 are ground, 6 and 12 the host's 3.3 V; every signal has 33 ohm in series on the host.  In every
register, bit k-1 is IOk.  CLK OUT (the SMA) is the 25 MHz TCXO unless `CONTROL[0]` is cleared.

## Register map

32-bit registers, 7-bit addresses, the host's protocol (`rtl/vendor/regbus.v`): command byte (bit 7 write, 6:0
address), 4 data bytes LSB first; a read answers 4 bytes; a read of 0x7F streams `DUMP_LEN` words.

| addr | name | | |
|---|---|---|---|
| 00 | ID | ro | 0x504D4231 ("PMB1"); the host's own bring-up design answers 0xEC5BA2D2 |
| 01 | VERSION | ro | the build date, 0xYYYYMMDD |
| 02 | SCRATCH | rw | |
| 03 | CONTROL | rw | [0] CLK OUT carries the TCXO (default 1).  wo: [8] restart every generator of both ports on one clock; [9] SAFE: every Pmod pin high-Z, OUT and SRC cleared, generators off (the LOCK bits stay) |
| 04 | LEDS | rw | [7:1] LED1-7 (LED0 is the heartbeat); [8] red [9] green [10] blue |
| 05 | GATE | ro | the frequency counters' gate in clocks (25000000 = 1 s; 25000 in simulation) |
| 06 | PINS | ro | [7:0] port A's pins, [15:8] port B's, [23:16] A's enables in force, [31:24] B's |
| 10 | CAP_CTRL | wo | [0] start, [1] abort |
| 11 | CAP_DIV | rw | [23:0] a sample every (div + 1) clocks |
| 12 | CAP_LEN | rw | samples, 1 .. 16384 |
| 13 | CAP_TRIG | rw | [15:0] mask ([7:0] port A): 0 starts at once, else at the first change of a masked pin (sample 0 is then the pins one clock before it) |
| 14 | CAP_STAT | ro | [0] busy, [1] done, [2] triggered, [30:16] samples taken |
| 20-3F | port A | | the table below |
| 40-5F | port B | | the same |
| 7E | DUMP_LEN | rw | words a read of 7F streams |
| 7F | DUMP | ro | the capture, two samples a word ([15:0] the earlier); a sample is [7:0] port A, [15:8] port B |

A port's registers (add 0x20 for A, 0x40 for B):

| off | name | | |
|---|---|---|---|
| 00 | OUT | rw | [7:0] the output register |
| 01 | OE | rw | [7:0] 1 = drive the pin; [15:8] LOCK: 1 = never drive it, whatever OE says |
| 02 | IN | ro | [7:0] the pins; [15:8] what the port would drive; [23:16] the enables in force |
| 03, 04 | OUT_SET, OUT_CLR | wo | ones set / clear OUT bits |
| 05 | SRC | rw | 4 bits a pin ([3:0] IO1): 0 the OUT bit; 1-4 generator 1-4; 5-8 generator 1-4 inverted (low when the generator is off or between bursts); 9 SPI SCK; 10 SPI MOSI; 11 the sampler's bit; 12 that bit inverted |
| 06 | GEN_CTRL | rw | [3:0] enable generators 1-4.  wo: [11:8] restart them (accumulator and burst counter to 0 on the same clock) |
| 07 | SPI_CFG | rw | [4:0] bits - 1; [5] LSB first; [6] CPOL; [7] CPHA; [10:8] MISO pin; [11] late sample (with CPHA 1: half a period after the trailing edge, for SSI); [31:16] half period in clocks, minus 1 |
| 08 | SPI_DATA | | write: the word, and the transfer starts (ignored while busy).  read: the raw receive register (MSB first: the word is its low n bits; LSB first: its top n) |
| 09 | STATUS | ro | [0] SPI busy; [1] the sampler's bit; [15:8] frequency counter sequence; [31:16] quadrature errors |
| 0A | SAMP_CFG | rw | [2:0] pin; [5:4] generator whose rising edge samples it; [12:8] log2 of the window.  Writing restarts the window |
| 0B, 0C | SAMP_ONES, SAMP_SEQ | ro | ones in the last complete window; windows completed |
| 0D | MEAS_CFG | rw | [2:0] frequency counter's pin; [6:4] quadrature A; [10:8] quadrature B.  wo: [16] clear the quadrature count |
| 0E | FREQ | ro | rising edges in the last gate (the pin is sampled at 25 MHz: good to 12 MHz) |
| 0F | QUAD | ro | signed position, four counts a cycle, up when A leads B |
| 10-13 | GEN1 | rw | INC (f = INC x 25 MHz / 2^32), DUTY (high while phase < DUTY; 0xFFFFFFFF always high), PHASE (added to the accumulator: an advance), BURST ([15:0] N cycles on of every [31:16] M; N = 0 continuous) |
| 14-1F | GEN2-4 | rw | the same |

Generators restarted together with the same INC keep their phase relation exactly; two with PHASE 0 and 2^31 and
DUTY = 2^31 - g x INC are both low for exactly g clocks between one's fall and the other's rise.  The SPI engine
samples MISO as the pin stood when the SCK edge left the FPGA (three clocks of pipeline are compensated), so a
slave may take almost the whole half period to answer.  The host must not write SPI_DATA again, or move a chip
select or LE, before STATUS[0] has cleared: the driver polls it.

## The driver

```python
from pmodbench import PmodBench
with PmodBench() as pb:                         # leaving the block calls safe(): all pins high-Z, generators off
    rf = pb.use('rf_mod', port='A')             # which tile is in which socket
    ...
```

`use(board, port)` reads `PROFILES`: the tile's inputs and unused lines are **locked in the gateware** and the
driver raises `ProfileError` on any attempt to drive one; its outputs are driven to their idle levels (chip
selects high, LE low, AMOD-A's audio line left high-Z until used, PHMOD's laser shunt high = current diverted).
Before `use()` nothing can be driven; `use('raw')` allows every pin.  `>` the FPGA drives, `<` the tile drives:

| board | IO1 | IO2 | IO3 | IO4 | IO5 | IO6 | IO7 | IO8 |
|---|---|---|---|---|---|---|---|---|
| `amod_a` | - | >AUDIO | >IN1 | >IN2 | - | >HEATER | <BIT | >FB |
| `amod_n` | - | >SI | >CLK | >LE | - | - | - | - |
| `amod_c` | >DSCLK | <CMP | >FCLK | >PHI1 | >TRACK | >PUMPCLK | <DSBIT | >PHI2 |
| `amod_m` | >DC_IN2 | >STEP_A1 | >STEP_A2 | >STEP_B1 | <ENC_A | <ENC_B | >DC_IN1 | >STEP_B2 |
| `amod_b` | >INHB | >INHC | <MISO | >SCK | >INHA | >CS_ENC | >MOSI | >CS_IMU |
| `rf_mod` | <MUXOUT | >SDATA | >SCLK | >LE_MAX | <RDBK | >LE_TRF | - | - |
| `phmod` | >PA_EN | - | - | - | >LASER_SHUNT | >COIL_EN | >COIL_PH | >NOISE |
| `iq_mod` | <MUXOUT | >SDATA | >SCLK | >LE_MAX | >SW_V1 | >NOISE | - | >SW_V2 |

Two rules are enforced as well: AMOD-B's two chip selects are never low together, IQ-MOD's V1 and V2 are always
complementary.  `safe()` takes the two TPS22917 enables (PHMOD IO8, IQ-MOD IO6) low before releasing them.

Examples, one per tile board (`p` is what `use()` returned; every method is also on `pb` for the last port used):

```python
# RF-MOD: r10's MAX2871 and r13's TRF3722 (CLK OUT of the host into r10's REF IN)
words, locked = p.max2871_set(915e6, 1)         # 915 MHz at -1 dBm (steps 0..3 = -4, -1, +2, +5 dBm); locked = MUXOUT
p.trf3722_read(0)                               # the readback register: chip ID, calibration result
p.trf3722_write(4, PWD_OUTBUF=1); p.trf3722_set(915e6)      # raw register access; the frequency plan (unproven)
# IQ-MOD
p.max2871_set(2.4e9, 1); p.rf_switch(2); p.out('IO6', 1)    # q3, q11's switch, q7's noise source
# AMOD-N
p.pe43711_set(12.5)                             # n8 to 12.5 dB (its SPI switch on, its seven bit switches off)
# AMOD-A
p.dsm_loop(1e6)                                 # close a6's loop at 1 MHz: returns the ones density = IN / 3.3 V
p.antiphase(p.pin('IN2'), p.pin('IN1'), 40e3, burst=(8, 400))      # a11: 8 cycles of 40 kHz every 10 ms
p.out('IO6', 1)                                 # a8's heater (0.83 W: hot)
# AMOD-C
p.clock(p.pin('DSCLK'), 1e6, gen=4); p.density(p.pin('DSBIT'), clock_gen=4, log2n=16)   # c6's bit stream
p.two_phase(p.pin('PHI1'), p.pin('PHI2'), 100e3, gap=400e-9)       # c5: never both high, 400 ns apart
p.clock(p.pin('FCLK'), 500e3, gen=3); p.inp(p.pin('CMP'))          # c4's clock; c8's bit
# AMOD-M
p.clock(p.pin('DC_IN1'), 20e3, duty=0.3); p.quad()                 # PWM into m3; (position, errors) of its encoder
# AMOD-B
p.pwm3((0.5, 0.5, 0.5), 20e3); p.mt6701_read(); p.lsm6dso_whoami() # three phases; the encoder; 0x6C
# PHMOD
p.out('IO1', 1); p.out('IO5', 0); p.clock('IO6', 20e3, duty=0.2)   # pulse amplifier on; laser on; coil PWM
# anything: a capture of all sixteen pins while something happens, as an array and as a VCD file
s = pb.capture(4096, div=4, trigger=[('A', 3)], during=lambda: p.max2871_set(915e6, 1), vcd='max.vcd')
f = p.freq('IO1')                               # Hz on a pin, 1 s gate
```

The command line (`python3 host/pmodbench.py`, no arguments, prints it) does one thing per call and **leaves
the pins as it set them**: `ident`, `safe`, `pins`, `use BOARD`, `out IO4 1`, `in`, `clock IO3 1e6`, `stop`,
`freq IO1`, `max2871 915e6 [power]`, `pe43711 12.5`, `trf3722 read N | write N WORD | set F`, `mt6701`, `whoami`,
`density IO7`, `dsm`, `quad`, `capture N DIV [file.vcd]`, `leds 0x55`; `--pmod B` and `--board NAME` before it.

On the board each register read will cost a USB round trip (the FTDI's latency timer: 16 ms by default, 1 ms
if the low-latency mode the driver asks for is granted), so expect a few milliseconds for an SPI word and up to
a second for a MAX2871 set-up.  (Expected, not measured.)

## What is verified, and how

* **`make sim`**: `PASS: tb_pmodbench, 77 checks`.  Power-up state and the host's other pins; the registers;
  generator frequency, duty, phase, inversion, bursts, cross-port restart; two-phase non-overlap (0 overlaps in
  300 periods, 240 ns dead time as set); the SPI engine in four modes, both bit orders, 1 to 32 bits, 500 kHz to
  12.5 MHz, against a slave whose data is valid only 10 ns before the sampling edge; MAX2871 (13 words, lock only
  after the datasheet's twice-with-20-ms sequence), TRF3722 (write, readback), PE43711, MT6701 (CRC), LSM6DSO;
  the delta-sigma loop round AMOD-A's comparator and RC (density 0.254 / 0.500 / 0.746 for IN = 0.825 / 1.65 /
  2.475 V); frequency counter; quadrature decoder; capture, trigger, dump.
* **`make test`**: `PASS: test_sim, 84 checks`.  `host/pmodbench.py` unchanged, on a transport that is the RTL
  in iverilog: ident, profile enforcement (driver and gateware lock, separately), `max2871_set` on RF-MOD and
  IQ-MOD (the words the model latched are the 13 the arithmetic produced; the model's own decoding gives the
  frequency asked), `pe43711_set`, `trf3722_write / read / set`, `mt6701_read`, `lsm6dso_whoami`, `clock`,
  `antiphase`, `two_phase`, `pwm3`, `density`, `dsm_loop`, `freq`, `quad`, `capture` with VCD, `safe`, the command
  line.  The two captured VCD files are also decoded by **sigrok-cli's SPI decoder** (file input only), which
  reads `A5 C3 F0 07` and `32`, the words sent.
* **`make mutants`**: 18 planted bugs (wrong SPI bit order, LOCK ignored, a pin driven at power-up, MISO sampled a
  clock early, a profile listing MUXOUT as an output, PE43711 / TRF3722 words MSB first, 2 ms instead of 20 ms,
  ...), each made in a temporary copy: all 18 caught.
* **`make bit`**: 6519 of 24288 LUTs (26 %), 2976 flip-flops, 16 of 56 block RAMs, 39 pins; 84 MHz against the
  25 MHz clock.  nextpnr's five warnings are the vendored LPF's clock constraints for pins this design leaves out.

What the simulation cannot say:

* **Nothing has run on hardware**: not the bitstream, not the driver against a real FT2232H, not one tile.
* The MT6701's and the LSM6DSO's datasheets are **not in `datasheets/`**.  Their models, and so `mt6701_read`
  and `lsm6dso_*`, follow the task's description and memory (CRC-6 x^6 + x + 1 over 18 bits, DO changing on SCK's
  rising edge, the IMU in SPI mode 3).  If the encoder's bits come out one place off, try `late=False`.
* TRF3722: the datasheet does not say whether LE stays high during the idle clock of a readback (here it does),
  gives no register write order and no start-up timing; `trf3722_set` follows its divider procedure (and
  reproduces its worked example) with Table 16's bias settings, unproven.
* MAX2871: the model locks 200 us after the sequence; the part takes about 100 ms with VAS_TEMP set (the driver
  waits up to 0.5 s).  The loop filter, RSET and CP = 7 are CostasLink's; nothing here checks the analog side.
* The models are mine, written from the same datasheets as the driver: a misreading shared by both passes.
  sigrok's decoder is the one independent reader, and it covers only bit order and clock edge.
* Electrical behaviour: edge rates into the tiles through 33 ohm, the pins' true leakage when "high-Z",
  what a tile does between power-up and `use()`.

## Notes for the tile boards (found while writing this; candidates for the rev B lists)

Checked against the netlist and the datasheet by me:

1. **AMOD-A a11**: IO4 reaches the DRV8837's pin 5 = **IN2** and IO3 pin 6 = **IN1**; the handbook says the
   reverse.  Harmless for antiphase bursts; the profile names follow the chip.
2. **AMOD-B b6**: CS ENC (IO6, also the '125 buffer's /OE) and CS IMU (IO8) have no pull-ups.  With the FPGA's
   pins high-Z (before a bitstream, before `use()`, after `safe()`) both selects float, and the buffer and the
   IMU can both drive MISO.  Pull both up.
3. **RF-MOD r13**: the TRF3722's LE (IO6) has no pull resistor, unlike r10's (100 k down), and shares SCLK /
   SDATA with r10.  The driver holds the other chip's LE low while it talks to one.
4. **AMOD-N n8**: LE has its 100 k pull-up (for the hand switches), SI and CLK have none: in serial mode with the
   pins released they float.  The driver lowers LE before clocking and leaves it low.
5. **PHMOD h10**: IO5 high diverts the laser's current and 100 k holds it low, so high-Z (and `safe()`) means
   **laser on**.  `use('phmod')` drives it high.  PHMOD h9 / IQ-MOD q7: a TPS22917's pull-down on ON lets go
   once ON has been high, so the line must be driven low before it is released (`safe()` does).
6. Missing datasheets: MT6701, LSM6DSO, DRV8311H, DRV8251A, SN74LVC1G79, AO3400A.

Reported by a second reading of the netlists and datasheets, not re-checked by me: AMOD-A a12's IO2 is
DC-coupled into the PAM8302 (about 1.3 V across the speaker at 50 % density, more when low: hence "left high-Z");
AMOD-C c5's switches want 200 ns or more of dead time (the default gap), and c3 / c4's LV1T34 inputs, c6's clock
and c7's LOGIC float when released; AMOD-M's encoder lines have neither pull-ups nor series resistors;
programming r10 with r13 switched off (or the reverse) drives an unpowered chip's pins through 33 ohm; PHMOD
h4's DRV8876 may not start from USB's 5 V less a diode (UVLO up to 4.6 V); the DRV8311H's and DRV8251A's
behaviour with floating inputs could not be checked (no datasheet).
