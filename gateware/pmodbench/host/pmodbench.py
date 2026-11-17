#!/usr/bin/env python3
"""pmodbench from the PC: the ECP5-2ADC-2DAC board's two Pmod sockets over the FT2232H's channel B (1 Mbaud).

    from pmodbench import PmodBench
    with PmodBench() as pb:                      # channel B found under /dev/serial/by-id; or PmodBench('/dev/ttyUSB3')
        pb.ident()                               # ID, build date, the frequency counters' gate
        rf = pb.use('rf_mod', port='A')          # RF-MOD in Pmod A: its inputs locked, its outputs driven to their idle levels
        words, locked = rf.max2871_set(915e6, 1) # r10 to 915 MHz at -1 dBm; `locked` is MUXOUT (digital lock detect)
        rf.trf3722_read(0)                       # r13's readback register
        s = pb.capture(4096, div=4, during=lambda: rf.max2871_set(2.4e9, 1), vcd='max.vcd')
    # leaving the `with` calls safe(): every pin high-Z, the generators stopped

    python3 pmodbench.py [/dev/...] [--pmod A|B] [--board NAME] ident | safe | pins | use BOARD | out IO4 1 | in [IO3]
            | clock IO3 1e6 [duty] | stop | freq IO1 | max2871 915e6 [power] | pe43711 12.5 | trf3722 read N
            | trf3722 write N 0xWORD | trf3722 set 915e6 | mt6701 | whoami | density IO7 [gen] [log2n] | dsm [1e6]
            | quad | capture N DIV [file.vcd] | leds 0x55

A tile board is chosen with use(board, port): PROFILES below says which of its eight lines the FPGA may drive.
From then on any attempt to drive a line the tile drives, or one it does not use, raises ProfileError, and those
pins are also locked in the gateware (the OE register's LOCK bits), so a slip here cannot reach the board.
Before use() nothing can be driven at all; use('raw') allows every pin.  The command line leaves the pins as it
set them (so `clock IO3 1e6` keeps running); `safe` releases them.

The protocol is the host board's bring-up one (rtl/vendor/regbus.v): a command byte (bit 7 write, bits 6:0 the
register), 4 data bytes LSB first; a read answers 4 bytes; a read of 0x7F streams the capture.  The register map
is REGS / PREG below, the same as rtl/pmodbench.v's and rtl/pmod_port.v's.  IOk is pmod[k-1]: IO1-4 are Pmod
pins 1-4, IO5-8 pins 7-10.
"""
import os
import struct
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import max2871                                                  # noqa: E402
import trf3722                                                  # noqa: E402

try:
    import serial
except ImportError:
    serial = None

DEFAULT_PORT = 'auto'
BAUD = 1_000_000
ID = 0x504D4231                     # "PMB1"; the host board's own bring-up design answers 0xEC5BA2D2
F_CLK = 25e6                        # the TCXO: every time and frequency here is a count of its 40 ns
CAP_MAX = 16384

REGS = dict(ID=0x00, VERSION=0x01, SCRATCH=0x02, CONTROL=0x03, LEDS=0x04, GATE=0x05, PINS=0x06,
            CAP_CTRL=0x10, CAP_DIV=0x11, CAP_LEN=0x12, CAP_TRIG=0x13, CAP_STAT=0x14, DUMP_LEN=0x7E, DUMP=0x7F)
PORT_BASE = {'A': 0x20, 'B': 0x40}
PREG = dict(OUT=0x00, OE=0x01, IN=0x02, OUT_SET=0x03, OUT_CLR=0x04, SRC=0x05, GEN_CTRL=0x06, SPI_CFG=0x07, SPI_DATA=0x08,
            STATUS=0x09, SAMP_CFG=0x0A, SAMP_ONES=0x0B, SAMP_SEQ=0x0C, MEAS_CFG=0x0D, FREQ=0x0E, QUAD=0x0F, GEN=0x10)
G_INC, G_DUTY, G_PHASE, G_BURST = 0, 1, 2, 3
SRC_REG, SRC_GEN, SRC_GEN_INV, SRC_SCK, SRC_MOSI, SRC_BIT, SRC_BIT_INV = 0, 1, 5, 9, 10, 11, 12     # generator n: SRC_GEN + n - 1
C_CLKOUT, C_RESTART, C_SAFE = 1 << 0, 1 << 8, 1 << 9


class ProfileError(Exception):
    """An attempt to drive a pin the selected tile board drives itself or does not use (or to break one of its rules)."""


# ---- the tile boards ---------------------------------------------------------------------------------------------
def _out(role, note, idle=0, lazy=False, release_low=False):
    return dict(dir='out', role=role, note=note, idle=idle, lazy=lazy, release_low=release_low)


def _in(role, note):
    return dict(dir='in', role=role, note=note)


_UNUSED = dict(dir='unused', role='', note='not connected on this board')


def _board(title, pins, **rules):
    p = {io: pins.get(io, _UNUSED) for io in range(1, 9)}
    return dict(title=title, pins=p, **rules)


# Direction is as the FPGA sees it.  idle = the level an output is driven to by use(); lazy = left high-Z until first
# used; release_low = driven low before it is released (a TPS22917's pull-down lets go once ON has been high).
PROFILES = {
    'raw': dict(title='no board: every pin may be driven', pins={io: dict(dir='io', role='', note='') for io in range(1, 9)}),
    'amod_a': _board('AMOD-A', {
        2: _out('AUDIO', "a12: one-bit audio into the PAM8302 through 10 k / 10 n; DC-coupled, so high-Z is its only quiet state", lazy=True),
        3: _out('IN1', "a11: DRV8837 IN1 (the chip's pin 6)"),
        4: _out('IN2', "a11: DRV8837 IN2 (the chip's pin 5)"),
        6: _out('HEATER', 'a8: the heater FET (high: 0.83 W; 10 k holds it off)'),
        7: _in('BIT', "a6: the TLV3501's bit (high: the integrator is above 1.65 V)"),
        8: _out('FB', 'a6: feedback into the integrator through 10 k: the INVERTED registered bit closes the loop')}),
    'amod_n': _board('AMOD-N', {
        2: _out('SI', 'n8: PE43711 serial data'), 3: _out('CLK', 'n8: PE43711 clock'),
        4: _out('LE', 'n8: PE43711 latch enable (100 k pull-up on the tile: high when released)')}),
    'amod_c': _board('AMOD-C', {
        1: _out('DSCLK', "c6: the delta-sigma modulator's clock (about 1 MHz)"), 2: _in('CMP', "c8: the comparator's bit"),
        3: _out('FCLK', 'c4: the switched-capacitor filter clock (100 kHz - 1.5 MHz, 100 x the corner)'),
        4: _out('PHI1', 'c5: phase 1 (IN onto the capacitor)'), 5: _out('TRACK', 'c7: high track, low hold'),
        6: _out('PUMPCLK', 'c3: the charge pump clock'), 7: _in('DSBIT', "c6: the modulator's bit stream"),
        8: _out('PHI2', 'c5: phase 2 (the capacitor into the summing node); never high with PHI1')}),
    'amod_m': _board('AMOD-M', {
        1: _out('DC_IN2', 'm3: DC motor driver IN2'), 2: _out('STEP_A1', 'm4: coil A IN1'), 3: _out('STEP_A2', 'm4: coil A IN2'),
        4: _out('STEP_B1', 'm4: coil B IN1'), 5: _in('ENC_A', 'm3: encoder A'), 6: _in('ENC_B', 'm3: encoder B'),
        7: _out('DC_IN1', 'm3: DC motor driver IN1'), 8: _out('STEP_B2', 'm4: coil B IN2')}),
    'amod_b': _board('AMOD-B', {
        1: _out('INHB', 'b3: phase B'), 2: _out('INHC', 'b3: phase C'), 3: _in('MISO', "b6: the IMU's SDO, or the encoder's DO while CS ENC is low"),
        4: _out('SCK', 'b5, b6: SPI clock, idle high', idle=1), 5: _out('INHA', 'b3: phase A'),
        6: _out('CS_ENC', "b5: the MT6701's CSN, and the enable of the buffer that puts its DO on MISO", idle=1),
        7: _out('MOSI', "b6: the IMU's SDI"), 8: _out('CS_IMU', "b6: the LSM6DSO's CS", idle=1)},
        never_both_low=[(6, 8)]),
    'rf_mod': _board('RF-MOD', {
        1: _in('MUXOUT', "r10: the MAX2871's MUX pin (programmed as digital lock detect)"), 2: _out('SDATA', 'r10 and r13: serial data'),
        3: _out('SCLK', 'r10 and r13: serial clock'), 4: _out('LE_MAX', "r10: the MAX2871's LE (100 k to ground on the tile)"),
        5: _in('RDBK', "r13: the TRF3722's readback"), 6: _out('LE_TRF', "r13: the TRF3722's LE")}),
    'phmod': _board('PHMOD', {
        1: _out('PA_EN', 'h2: high, the pulse amplifier on'),
        5: _out('LASER_SHUNT', "h10: high, the laser's current diverted; released, the laser runs (100 k to ground)", idle=1),
        6: _out('COIL_EN', 'h4: the bridge on (PWM it)'), 7: _out('COIL_PH', "h4: the current's direction"),
        8: _out('NOISE', 'h9: high, the noise source on', release_low=True)}),
    'iq_mod': _board('IQ-MOD', {
        1: _in('MUXOUT', "q3: the MAX2871's MUX pin"), 2: _out('SDATA', 'q3: serial data'), 3: _out('SCLK', 'q3: serial clock'),
        4: _out('LE_MAX', "q3: the MAX2871's LE"), 5: _out('SW_V1', 'q11: RF switch V1 (RF1 on)', idle=1),
        6: _out('NOISE', 'q7: high, the noise source on', release_low=True), 8: _out('SW_V2', 'q11: RF switch V2 (RF2 on)')},
        complementary=[(5, 8)]),
}


# ---- the link -------------------------------------------------------------------------------------------------------
def find_port(pattern='/dev/serial/by-id/usb-FTDI_Dual_RS232-HS*-if01*'):
    """The FT2232H's channel B (interface 1) by its name under /dev/serial/by-id; a blank EEPROM enumerates as
    "Dual RS232-HS".  Never guesses a bare ttyUSBn: the bench's instruments are ttyUSBs too."""
    import glob
    hits = sorted(glob.glob(pattern))
    if not hits:
        raise IOError('no FT2232H channel B under /dev/serial/by-id (%s): is USB PROG plugged in?  '
                      'A programmed EEPROM changes the name: pass the port explicitly' % pattern)
    return hits[0]


class Transport:
    """What PmodBench needs from a link: write bytes, read exactly n bytes (or raise), discard what is pending,
    let `seconds` pass, and tell the time (so a simulated link can run the driver on its own clock)."""
    def write(self, data): raise NotImplementedError
    def read(self, n): raise NotImplementedError
    def flush(self): pass
    def wait(self, seconds): time.sleep(seconds)
    def now(self): return time.monotonic()
    def close(self): pass


class SerialTransport(Transport):
    def __init__(self, port=DEFAULT_PORT, baud=BAUD, timeout=1.0):
        if serial is None:
            raise ImportError('pyserial is needed: pip install pyserial (or apt install python3-serial)')
        if port in (None, 'auto'):
            port = find_port()
        self.port = port
        self.s = serial.Serial(port, baud, timeout=timeout, write_timeout=1.0)
        self.s.setDTR(False)
        self.s.setRTS(False)
        try:
            self.s.set_low_latency_mode(True)          # the FTDI's 16 ms latency timer down to 1 ms, where the OS allows
        except Exception:
            pass
        time.sleep(0.05)
        self.flush()

    def write(self, data): self.s.write(data)

    def read(self, n):
        d = self.s.read(n)
        if len(d) != n:
            raise IOError('board: wanted %d bytes, got %d (is pmodbench.bit loaded? is this channel B?)' % (n, len(d)))
        return d

    def flush(self): self.s.reset_input_buffer()
    def close(self): self.s.close()


def _pack_w(reg, val): return bytes([0x80 | reg]) + struct.pack('<I', val & 0xFFFFFFFF)
def _pack_r(reg): return bytes([reg & 0x7F])


def _io(io):
    """An IO number 1..8 from 4, 'IO4' or 'io4'."""
    if isinstance(io, str):
        io = int(io.upper().replace('IO', ''))
    if not 1 <= io <= 8:
        raise ValueError('IO numbers are 1..8, not %r' % (io,))
    return io


def crc6_mt6701(data18):
    """The MT6701's CRC over the 18 bits before it: x^6 + x + 1, MSB first, zero start."""
    c = 0
    for i in range(17, -1, -1):
        fb = ((c >> 5) ^ (data18 >> i)) & 1
        c = ((c << 1) & 0x3F) ^ (0x03 if fb else 0)
    return c


# ---- one Pmod socket ---------------------------------------------------------------------------------------------------
class Port:
    def __init__(self, bench, name):
        self.b, self.name, self.base = bench, name, PORT_BASE[name]
        self.board, self.profile = None, None
        self._out = self._oe = self._lock = self._gen_en = 0
        self._src = [0] * 8
        self._spi_cfg = None
        self._gen_freq = {}
        self._meas = None
        self.last = {}

    # -- registers
    def wr(self, reg, val): self.b.wr(self.base + (PREG[reg] if isinstance(reg, str) else reg), val)
    def rd(self, reg): return self.b.rd(self.base + (PREG[reg] if isinstance(reg, str) else reg))

    def sync(self):
        """Read the port's state back from the FPGA (a new process meeting pins an earlier one left set)."""
        self._out = self.rd('OUT') & 0xFF
        oe = self.rd('OE')
        self._oe, self._lock = oe & 0xFF, (oe >> 8) & 0xFF
        s = self.rd('SRC')
        self._src = [(s >> (4 * k)) & 15 for k in range(8)]
        self._gen_en = self.rd('GEN_CTRL') & 15
        self._spi_cfg = self.rd('SPI_CFG')
        self._meas = self.rd('MEAS_CFG')

    # -- the profile
    def use(self, board, reset=True):
        """Select the tile board in this socket.  Its inputs and unused lines are locked in the gateware; with
        reset (the default) the generators stop and its outputs are driven to their idle levels, without it the
        pins stay as an earlier process left them."""
        if board not in PROFILES:
            raise KeyError('no board called %r: %s' % (board, ', '.join(sorted(PROFILES))))
        prof = PROFILES[board]
        lock = sum(1 << (io - 1) for io, p in prof['pins'].items() if p['dir'] in ('in', 'unused'))
        if reset:
            self.wr('OE', lock << 8)                             # everything released first
            self.wr('GEN_CTRL', 0)
            self.wr('SRC', 0)
            self._gen_en, self._src, self._gen_freq, self._spi_cfg, self._meas = 0, [0] * 8, {}, None, None
            out = sum(1 << (io - 1) for io, p in prof['pins'].items() if p['dir'] == 'out' and p['idle'])
            oe = sum(1 << (io - 1) for io, p in prof['pins'].items() if p['dir'] == 'out' and not p['lazy'])
            self.board, self.profile = board, prof
            self._check_levels(out, oe)
            self.wr('OUT', out)
            self.wr('OE', oe | (lock << 8))
            self._out, self._oe, self._lock = out, oe, lock
        else:
            self.sync()
            self.board, self.profile = board, prof
            self._oe &= ~lock
            self._lock = lock
            self.wr('OE', self._oe | (lock << 8))
        return self

    def pin(self, role):
        """The IO number of a named line of the selected board ('LE_MAX', 'MISO', ...)."""
        if self.profile is None:
            raise ProfileError('Pmod %s: no board selected: call use(board) first' % self.name)
        for io, p in self.profile['pins'].items():
            if p['role'] == role:
                return io
        raise ProfileError("Pmod %s: %s has no line called %s" % (self.name, self.board, role))

    def _need(self, *boards):
        if self.board not in boards:
            raise ProfileError('Pmod %s holds %s: this needs %s' % (self.name, self.board, ' or '.join(boards)))

    def _can_drive(self, io):
        io = _io(io)
        if self.profile is None:
            raise ProfileError("Pmod %s: no board selected, so nothing may be driven: call use(board) first (use('raw') allows every pin)" % self.name)
        p = self.profile['pins'][io]
        if p['dir'] not in ('out', 'io'):
            what = "is an output of the tile (%s: %s)" % (p['role'], p['note']) if p['dir'] == 'in' else 'is not used by the board'
            raise ProfileError('Pmod %s IO%d %s: %s forbids driving it' % (self.name, io, what, self.board))
        return io

    def _check_levels(self, out, oe):
        prof = self.profile or {}
        for a, b in prof.get('never_both_low', []):
            ma, mb = 1 << (a - 1), 1 << (b - 1)
            if oe & ma and oe & mb and not out & ma and not out & mb:
                raise ProfileError('Pmod %s: IO%d and IO%d (%s, %s) must never be low together on %s'
                                   % (self.name, a, b, prof['pins'][a]['role'], prof['pins'][b]['role'], self.board))
        for a, b in prof.get('complementary', []):
            ma, mb = 1 << (a - 1), 1 << (b - 1)
            if oe & ma and oe & mb and bool(out & ma) == bool(out & mb):
                raise ProfileError('Pmod %s: IO%d and IO%d (%s, %s) must be complementary on %s'
                                   % (self.name, a, b, prof['pins'][a]['role'], prof['pins'][b]['role'], self.board))

    def _levels(self, set_mask=0, clr_mask=0):
        new = (self._out | set_mask) & ~clr_mask & 0xFF
        if new == self._out:
            return
        self._check_levels(new, self._oe)
        if set_mask and not clr_mask: self.wr('OUT_SET', set_mask)
        elif clr_mask and not set_mask: self.wr('OUT_CLR', clr_mask)
        else: self.wr('OUT', new)
        self._out = new

    def _enable(self, mask):
        if self._oe & mask != mask:
            self._check_levels(self._out, self._oe | mask)
            self._oe |= mask
            self.wr('OE', self._oe | (self._lock << 8))

    def _source(self, assign):
        src = list(self._src)
        for io, code in assign.items():
            src[io - 1] = code
        if src != self._src:
            self._src = src
            self.wr('SRC', sum(c << (4 * k) for k, c in enumerate(src)))

    # -- plain pins
    def out(self, io, v):
        """Drive IO `io` to v (0 or 1) from the output register."""
        io = self._can_drive(io)
        m = 1 << (io - 1)
        self._source({io: SRC_REG})
        self._levels(m if v else 0, 0 if v else m)
        self._enable(m)

    def out_many(self, levels):
        """Several pins in one register write: {io: level}.  (IQ-MOD's switch lines change together this way.)"""
        ios = {self._can_drive(io): v for io, v in levels.items()}
        self._source({io: SRC_REG for io in ios})
        sm = sum(1 << (io - 1) for io, v in ios.items() if v)
        cm = sum(1 << (io - 1) for io, v in ios.items() if not v)
        if self._oe & (sm | cm) != (sm | cm):                   # a pin not yet enabled: its level first, then its enable
            new = (self._out | sm) & ~cm
            self._check_levels(new, self._oe | sm | cm)
            self.wr('OUT', new); self._out = new
            self._enable(sm | cm)
        else:
            self._levels(sm, cm)

    def inp(self, io=None):
        """The pin `io` as it reads now (0 or 1), or all eight as a byte (bit k-1 = IOk)."""
        v = self.rd('IN') & 0xFF
        return v if io is None else (v >> (_io(io) - 1)) & 1

    def release(self, io=None):
        """Stop driving `io` (or every pin of the port)."""
        mask = 0xFF if io is None else 1 << (_io(io) - 1)
        if self._oe & mask:
            self._oe &= ~mask
            self.wr('OE', self._oe | (self._lock << 8))

    def state(self):
        r = self.rd('IN')
        return dict(pins=r & 0xFF, driving=(r >> 8) & 0xFF, enabled=(r >> 16) & 0xFF, out=self.rd('OUT') & 0xFF,
                    lock=(self.rd('OE') >> 8) & 0xFF, src=self.rd('SRC'), gen_en=self.rd('GEN_CTRL') & 15)

    # -- the generators
    def gen(self, n, freq, duty=0.5, phase=0.0, burst=None, start=True):
        """Program generator n (1..4): `freq` Hz, `duty` 0..1, `phase` = the fraction of a period by which it LAGS a
        phase-0 generator restarted with it, burst = (cycles on, cycles in the period) or None.  start: enable and
        restart it.  Returns the frequency set (INC x 25 MHz / 2^32)."""
        if not 1 <= n <= 4: raise ValueError('generators are 1..4')
        inc = int(round(freq / F_CLK * 2 ** 32))
        if not 1 <= inc <= 1 << 31: raise ValueError('generator: %.6g Hz is outside 0.006 Hz .. 12.5 MHz' % freq)
        dw = 0xFFFFFFFF if duty >= 1 else 0 if duty <= 0 else min(0xFFFFFFFE, int(round(duty * 2 ** 32)))
        pw = int(round((-phase % 1.0) * 2 ** 32)) & 0xFFFFFFFF
        bw = 0
        if burst:
            on, per = burst
            if not (0 < on <= 0xFFFF and on <= per <= 0xFFFF): raise ValueError('burst: (cycles on, period), 1 <= on <= period <= 65535')
            bw = on | (per << 16)
        r = PREG['GEN'] + 4 * (n - 1)
        self.wr(r + G_INC, inc); self.wr(r + G_DUTY, dw); self.wr(r + G_PHASE, pw); self.wr(r + G_BURST, bw)
        self._gen_freq[n] = inc * F_CLK / 2 ** 32
        if start:
            self.start(n)
        return self._gen_freq[n]

    def start(self, *gens):
        """Enable these generators and restart them on the same clock (their phases then hold exactly)."""
        mask = sum(1 << (n - 1) for n in gens)
        self._gen_en |= mask
        self.wr('GEN_CTRL', self._gen_en | (mask << 8))

    def stop(self, *gens):
        """Disable these generators (all four if none is named): their outputs, true and inverted, go low."""
        mask = sum(1 << (n - 1) for n in gens) if gens else 15
        self._gen_en &= ~mask
        self.wr('GEN_CTRL', self._gen_en)

    def clock(self, io, freq, duty=0.5, phase=0.0, gen=1, burst=None, invert=False):
        """A clock on IO `io` (or a list of them; None: no pin, the generator alone) from generator `gen`.
        invert: the complement while the generator is on, low while it is off or between bursts.  Returns the frequency."""
        ios = [] if io is None else [self._can_drive(x) for x in (io if isinstance(io, (list, tuple)) else [io])]
        f = self.gen(gen, freq, duty, phase, burst, start=False)
        self._source({x: (SRC_GEN_INV if invert else SRC_GEN) + gen - 1 for x in ios})
        self._enable(sum(1 << (x - 1) for x in ios))
        self.start(gen)
        return f

    def antiphase(self, io_p, io_n, freq, burst=None, gen=1):
        """A push-pull pair from one generator: io_p high in the first half of each cycle, io_n in the second, both
        low between bursts (AMOD-A's 40 kHz transducer: antiphase(4, 3, 40e3, burst=(8, 400)))."""
        io_p, io_n = self._can_drive(io_p), self._can_drive(io_n)
        f = self.gen(gen, freq, 0.5, 0.0, burst, start=False)
        self._source({io_p: SRC_GEN + gen - 1, io_n: SRC_GEN_INV + gen - 1})
        self._enable((1 << (io_p - 1)) | (1 << (io_n - 1)))
        self.start(gen)
        return f

    def two_phase(self, io_a, io_b, freq, gap=None, gens=(1, 2)):
        """Two non-overlapping phases: io_a high early in each period, io_b half a period later, with at least
        `gap` seconds (default 5 % of the period, 200 ns at least) of both-low on each side.  Both generators get
        the same increment and are restarted on the same clock, so the phases cannot drift into each other.
        Returns {'freq', 'duty', 'gap'} as set (the gap is a whole number of 40 ns clocks, rounded up)."""
        io_a, io_b = self._can_drive(io_a), self._can_drive(io_b)
        inc = int(round(freq / F_CLK * 2 ** 32))
        if gap is None: gap = max(0.05 / freq, 200e-9)
        ticks = max(1, int(-(-gap * F_CLK // 1)))               # ceil: the thresholds are `ticks` increments apart,
        dw = (1 << 31) - ticks * inc                            # so one output falls exactly that many clocks before the other rises
        if dw < inc: raise ValueError('two_phase: a %.3g s gap leaves no pulse at %.6g Hz' % (gap, freq))
        ga, gb = gens
        for g, ph in ((ga, 0), (gb, 1 << 31)):
            r = PREG['GEN'] + 4 * (g - 1)
            self.wr(r + G_INC, inc); self.wr(r + G_DUTY, dw); self.wr(r + G_PHASE, ph); self.wr(r + G_BURST, 0)
            self._gen_freq[g] = inc * F_CLK / 2 ** 32
        self._source({io_a: SRC_GEN + ga - 1, io_b: SRC_GEN + gb - 1})
        self._enable((1 << (io_a - 1)) | (1 << (io_b - 1)))
        self.start(ga, gb)
        return dict(freq=inc * F_CLK / 2 ** 32, duty=dw / 2 ** 32, gap=ticks / F_CLK)

    def pwm3(self, duties, freq=20e3, ios=None, gens=(1, 2, 3)):
        """Three PWM phases (AMOD-B: INHA, INHB, INHC), centre-aligned: each pulse straddles the generators' common
        zero.  duties: three numbers 0..1.  Returns the frequency."""
        if ios is None: ios = [self.pin('INHA'), self.pin('INHB'), self.pin('INHC')]
        ios = [self._can_drive(x) for x in ios]
        inc = int(round(freq / F_CLK * 2 ** 32))
        for g, d in zip(gens, duties):
            dw = 0xFFFFFFFF if d >= 1 else 0 if d <= 0 else min(0xFFFFFFFE, int(round(d * 2 ** 32)))
            r = PREG['GEN'] + 4 * (g - 1)
            self.wr(r + G_INC, inc); self.wr(r + G_DUTY, dw); self.wr(r + G_PHASE, (dw >> 1) if dw != 0xFFFFFFFF else 0); self.wr(r + G_BURST, 0)
            self._gen_freq[g] = inc * F_CLK / 2 ** 32
        self._source({x: SRC_GEN + g - 1 for x, g in zip(ios, gens)})
        self._enable(sum(1 << (x - 1) for x in ios))
        self.start(*gens)
        return inc * F_CLK / 2 ** 32

    # -- SPI
    def _role(self, names):
        for n in names:
            for io, p in (self.profile or {'pins': {}})['pins'].items():
                if p['role'] == n:
                    return io
        return None

    def spi(self, word, nbits=32, mode=0, lsb=False, freq=500e3, sck=None, mosi=None, miso=None, late=False, read=True, timeout=2.0):
        """Shift `nbits` (1..32) of `word` out and the same number in.  mode 0-3 (CPOL = mode >> 1, CPHA = mode & 1);
        lsb: least significant bit first; late: with CPHA = 1, sample half a period after the trailing edge (SSI).
        The pins default to the board's SCLK / SDATA / MISO lines.  Chip selects and LE are plain pins: use out().
        Returns the word received (None with read=False)."""
        if not 1 <= nbits <= 32: raise ValueError('SPI: 1..32 bits')
        sck = self._can_drive(sck if sck is not None else self._role(('SCLK', 'SCK', 'CLK')))
        mosi = mosi if mosi is not None else self._role(('SDATA', 'MOSI', 'SI'))
        miso = miso if miso is not None else self._role(('MISO',))
        if mosi is not None: mosi = self._can_drive(mosi)
        half = max(0, int(round(F_CLK / (2.0 * freq))) - 1)
        if half > 0xFFFF: raise ValueError('SPI: %.6g Hz is too slow (190 Hz at least)' % freq)
        cfg = (nbits - 1) | (int(bool(lsb)) << 5) | ((mode >> 1 & 1) << 6) | ((mode & 1) << 7) | (((_io(miso) - 1) if miso else 0) << 8) \
            | (int(bool(late)) << 11) | (half << 16)
        if cfg != self._spi_cfg:
            self.wr('SPI_CFG', cfg); self._spi_cfg = cfg       # SCK takes its idle level now, before the pin is handed over
        src = {sck: SRC_SCK}
        if mosi is not None: src[mosi] = SRC_MOSI
        self._source(src)
        self._enable(sum(1 << (x - 1) for x in src))
        self.wr('SPI_DATA', word & ((1 << nbits) - 1))
        self.b.t.wait((2 * nbits + 1) * (half + 1) / F_CLK)
        t0 = self.b.t.now()
        while self.rd('STATUS') & 1:                            # never go on (to an LE edge, say) with the word half out
            if self.b.t.now() - t0 > timeout: raise IOError('SPI: still busy after %.1f s' % timeout)
        if not read: return None
        raw = self.rd('SPI_DATA')
        return raw >> (32 - nbits) if lsb else raw & ((1 << nbits) - 1)

    # -- the one-bit sampler
    def density(self, io, clock_gen=1, log2n=12, settle=1, timeout=None):
        """The fraction of ones on IO `io`, sampled at each rising edge of generator `clock_gen`, over 2^log2n
        samples.  The window restarts now; `settle` further windows are thrown away before the one returned."""
        io = _io(io)
        self.wr('SAMP_CFG', (io - 1) | ((clock_gen - 1) << 4) | (log2n << 8))
        f = self._gen_freq.get(clock_gen) or self.rd(PREG['GEN'] + 4 * (clock_gen - 1) + G_INC) * F_CLK / 2 ** 32
        if f <= 0 or not self._gen_en_live() >> (clock_gen - 1) & 1:
            raise IOError('density: generator %d is not running' % clock_gen)
        window = (1 << log2n) / f
        if timeout is None: timeout = 3 * window * (settle + 2) + 1.0
        seq0 = self.rd('SAMP_SEQ') & 0xFFFF
        t0 = self.b.t.now()
        while True:
            self.b.t.wait(window / 4)
            seq = self.rd('SAMP_SEQ') & 0xFFFF
            if (seq - seq0) & 0xFFFF >= settle + 1:
                ones = self.rd('SAMP_ONES')
                if self.rd('SAMP_SEQ') & 0xFFFF == seq: break
            if self.b.t.now() - t0 > timeout: raise IOError('density: no complete window after %.2f s' % timeout)
        self.last['density'] = dict(ones=ones, n=1 << log2n, seq=seq)
        return ones / float(1 << log2n)

    def _gen_en_live(self):
        return self._gen_en if self._gen_freq else self.rd('GEN_CTRL') & 15

    def dsm_loop(self, freq=1e6, log2n=12, gen=1, in_io=None, fb_io=None, invert=True, settle=1):
        """Close a first-order delta-sigma loop (AMOD-A's a6): the comparator's bit on `in_io` is registered at
        `freq` and fed back, inverted, on `fb_io`.  Returns the ones-density of the registered bit over 2^log2n
        samples (a6: IN / 3.3 V).  The loop keeps running; density(in_io, gen, log2n) reads it again."""
        in_io = _io(in_io if in_io is not None else self.pin('BIT'))
        fb_io = self._can_drive(fb_io if fb_io is not None else self.pin('FB'))
        self.gen(gen, freq, start=False)
        self.wr('SAMP_CFG', (in_io - 1) | ((gen - 1) << 4) | (log2n << 8))
        self._source({fb_io: SRC_BIT_INV if invert else SRC_BIT})
        self._enable(1 << (fb_io - 1))
        self.start(gen)
        return self.density(in_io, gen, log2n, settle=settle)

    # -- the frequency counter and the quadrature decoder
    def _meas_cfg(self, f_pin=None, qa=None, qb=None, clear=False):
        cur = self._meas if self._meas is not None else self.rd('MEAS_CFG')
        f0, a0, b0 = cur & 7, (cur >> 4) & 7, (cur >> 8) & 7
        new = (f0 if f_pin is None else f_pin - 1) | ((a0 if qa is None else qa - 1) << 4) | ((b0 if qb is None else qb - 1) << 8)
        changed = new != cur
        if changed or clear:
            self.wr('MEAS_CFG', new | (int(clear) << 16)); self._meas = new
        return changed

    def freq(self, io, timeout=None):
        """The frequency on IO `io` in Hz: rising edges in one gate (1 s on the board).  The pin is sampled at 25 MHz,
        so this is good to 12 MHz and to pulses of 40 ns or more.  Waits for a whole gate after selecting the pin."""
        self._meas_cfg(f_pin=_io(io))
        gate_s = self.b.gate / F_CLK
        if timeout is None: timeout = 3.5 * gate_s + 1.0
        seq0 = (self.rd('STATUS') >> 8) & 0xFF
        t0 = self.b.t.now()
        while True:
            self.b.t.wait(gate_s / 4)
            s = self.rd('STATUS')
            if (((s >> 8) & 0xFF) - seq0) & 0xFF >= 2:          # the first gate to end was already under way
                n = self.rd('FREQ')
                if (self.rd('STATUS') >> 8) & 0xFF == (s >> 8) & 0xFF: break
            if self.b.t.now() - t0 > timeout: raise IOError('freq: no gate after %.1f s' % timeout)
        return n / gate_s

    def quad(self, a_io=None, b_io=None, reset=False):
        """The quadrature decoder: (position, errors).  Four counts a cycle, up when A leads B; an error is both
        lines changing between two 40 ns samples.  The pins default to the board's ENC_A / ENC_B (or stay as set);
        choosing new pins, or reset=True, zeroes both counts."""
        if a_io is None and self.profile is not None: a_io = self._role(('ENC_A',))
        if b_io is None and self.profile is not None: b_io = self._role(('ENC_B',))
        changed = self._meas_cfg(qa=_io(a_io) if a_io else None, qb=_io(b_io) if b_io else None)
        if changed or reset: self._meas_cfg(clear=True)
        c = self.rd('QUAD')
        return (c - (1 << 32) if c & 0x80000000 else c), self.rd('STATUS') >> 16

    # -- MAX2871 (RF-MOD r10, IQ-MOD q3)
    def _max_word(self, w, le):
        self.spi(w, 32, mode=0, read=False)
        self.out(le, 1); self.out(le, 0)

    def max2871_set(self, f_hz, power_dbm_step=1, ref_hz=25e6, lock_timeout=0.5):
        """Program the MAX2871 to f_hz (23.5 MHz - 6 GHz) at output power step 0..3 (-4, -1, +2, +5 dBm) with the
        datasheet's power-up sequence: register 5, 20 ms, registers 4 (outputs off) to 0, 20 ms, all six again, wait
        for lock, then register 4 with RFOUTA on.  RFOUTB stays disabled.  Returns (the six words [R5..R0], locked):
        locked is the MUX pin, programmed as digital lock detect.  The plan is in self.last['max2871']."""
        self._need('rf_mod', 'iq_mod')
        w, plan = max2871.words(f_hz, power_dbm_step, ref_hz)
        le, mux = self.pin('LE_MAX'), self.pin('MUXOUT')
        self.out(le, 0)
        if self.board == 'rf_mod': self.out(self.pin('LE_TRF'), 0)      # r13 shares SCLK and SDATA: its LE has no pull resistor
        for kind, v in max2871.power_up_steps(w):
            if kind == 'w': self._max_word(v, le)
            elif kind == 'wait': self.b.t.wait(v)
            else:                                               # the VCO is being chosen with the outputs off
                t0 = self.b.t.now()
                while not self.inp(mux) and self.b.t.now() - t0 < lock_timeout:
                    self.b.t.wait(min(0.01, lock_timeout / 20))
        locked = bool(self.inp(mux))
        self.last['max2871'] = dict(plan=plan, words=w, locked=locked)
        return w, locked

    def max2871_locked(self):
        self._need('rf_mod', 'iq_mod')
        return bool(self.inp(self.pin('MUXOUT')))

    def rf_switch(self, path):
        """IQ-MOD's q11: path 1 (V1 high, V2 low) or 2, both lines in one register write."""
        self._need('iq_mod')
        if path not in (1, 2): raise ValueError('rf_switch: path 1 or 2')
        self.out_many({self.pin('SW_V1'): path == 1, self.pin('SW_V2'): path == 2})

    # -- PE43711 (AMOD-N n8)
    def pe43711_set(self, db):
        """Set the step attenuator (0 .. 31.75 dB in 0.25 dB steps; the tile's SPI switch on, its seven bit switches
        off).  Eight bits LSB first while LE is low, then LE high and low again.  Returns the attenuation set."""
        self._need('amod_n')
        code = int(round(db * 4))
        if not 0 <= code <= 127: raise ValueError('PE43711: 0 .. 31.75 dB, not %r' % (db,))
        le = self.pin('LE')
        self.out(le, 0)
        self.spi(code, 8, mode=0, lsb=True, read=False)
        self.out(le, 1); self.out(le, 0)
        return code / 4.0

    # -- TRF3722 (RF-MOD r13)
    def trf3722_write(self, reg, value=None, **fields):
        """Write register 1..6: `value` (a 32-bit word; its address bits are set for you) or field values on top of
        the reset word (trf3722.FIELDS).  Returns the word sent."""
        self._need('rf_mod')
        if not 1 <= reg <= 6: raise ValueError('TRF3722: registers 1..6 are written')
        w = trf3722.pack(reg, **fields) if value is None else (value & ~0x1F & 0xFFFFFFFF) | trf3722.address(reg)
        self._trf_word(w)
        return w

    def _trf_word(self, w):
        le = self.pin('LE_TRF')
        self.out(self.pin('LE_MAX'), 0)                         # r10 shares SCLK and SDATA: keep its LE low
        self.out(le, 0)
        self.spi(w, 32, mode=0, lsb=True, read=False)
        self.out(le, 1); self.out(le, 0)

    def trf3722_read(self, reg, mux_count=0):
        """Read register 0..6 back: the readback command to register 0, one idle clock, then 32 clocks with RDBK
        sampled at each falling edge.  (The datasheet's Figure 131 does not say whether LE is still high during the
        idle clock; here it is, and it falls before the 32.)"""
        self._need('rf_mod')
        le, rd = self.pin('LE_TRF'), self.pin('RDBK')
        self.out(self.pin('LE_MAX'), 0)
        self.out(le, 0)
        self.spi(trf3722.readback_command(reg, mux_count), 32, mode=0, lsb=True, read=False)
        self.out(le, 1)
        self.spi(0, 1, mode=0, lsb=True, read=False)
        self.out(le, 0)
        return self.spi(0, 32, mode=1, lsb=True, miso=rd)

    def trf3722_set(self, f_hz, ref_hz=25e6, rdiv=1):
        """Program r13 to f_hz (256 MHz - 4.1 GHz): registers 1, 3, 4, 5, 6, then 2 with EN_CAL.  Never run on a part:
        see trf3722.py.  Returns ({register: word}, plan)."""
        self._need('rf_mod')
        w, plan = trf3722.words(f_hz, ref_hz, rdiv)
        for r in trf3722.WRITE_ORDER:
            self._trf_word(w[r])
        self.last['trf3722'] = dict(plan=plan, words=w)
        return w, plan

    # -- MT6701 and LSM6DSO (AMOD-B)
    def mt6701_read(self, check=True):
        """The encoder's angle over SSI: CS ENC low, 24 clocks (SCK idles high; each bit is taken half a period after
        the rising edge that launches it), CS ENC high.  Returns {'angle' (degrees), 'raw' (14 bits), 'status' (4 bits),
        'crc_ok'}; a wrong CRC raises IOError unless check=False."""
        self._need('amod_b')
        cs = self.pin('CS_ENC')
        self.out(self.pin('CS_IMU'), 1)
        self.spi_idle(mode=3)
        self.out(cs, 0)
        w = self.spi(0, 24, mode=3, late=True, freq=500e3)
        self.out(cs, 1)
        raw, status, crc = w >> 10, (w >> 6) & 0xF, w & 0x3F
        ok = crc6_mt6701(w >> 6) == crc
        if check and not ok:
            raise IOError('MT6701: CRC %02x does not match the 18 bits before it (word %06x)' % (crc, w))
        return dict(angle=raw * 360.0 / 16384, raw=raw, status=status, crc_ok=ok, word=w)

    def spi_idle(self, mode=3, freq=500e3):
        """Hand the board's SCK line to the SPI engine at its idle level before a chip select falls."""
        sck = self._can_drive(self._role(('SCLK', 'SCK', 'CLK')))
        half = max(0, int(round(F_CLK / (2.0 * freq))) - 1)
        cfg = ((self._spi_cfg or 0) & 0xFFFF & ~0xC0) | ((mode >> 1 & 1) << 6) | ((mode & 1) << 7) | (half << 16)
        if cfg != self._spi_cfg:
            self.wr('SPI_CFG', cfg); self._spi_cfg = cfg
        self._source({sck: SRC_SCK})
        self._enable(1 << (sck - 1))

    def lsm6dso_read(self, addr, n=1):
        """Read n (1..3) registers of the IMU from `addr` (SPI mode 3: bit 7 of the first byte is the read flag)."""
        self._need('amod_b')
        if not 1 <= n <= 3: raise ValueError('lsm6dso_read: 1..3 bytes')
        cs = self.pin('CS_IMU')
        self.out(self.pin('CS_ENC'), 1)
        self.spi_idle(mode=3)
        self.out(cs, 0)
        w = self.spi((0x80 | (addr & 0x7F)) << (8 * n), 8 * (n + 1), mode=3)
        self.out(cs, 1)
        d = [(w >> (8 * (n - 1 - i))) & 0xFF for i in range(n)]
        return d[0] if n == 1 else d

    def lsm6dso_write(self, addr, value):
        self._need('amod_b')
        cs = self.pin('CS_IMU')
        self.out(self.pin('CS_ENC'), 1)
        self.spi_idle(mode=3)
        self.out(cs, 0)
        self.spi(((addr & 0x7F) << 8) | (value & 0xFF), 16, mode=3, read=False)
        self.out(cs, 1)

    def lsm6dso_whoami(self):
        """WHO_AM_I (0x0F): an LSM6DSO answers 0x6C."""
        return self.lsm6dso_read(0x0F)


# ---- the board ---------------------------------------------------------------------------------------------------------
class PmodBench:
    def __init__(self, port=DEFAULT_PORT, transport=None, check=True):
        self.t = transport or SerialTransport(port)
        self.A, self.B = Port(self, 'A'), Port(self, 'B')
        self.ports = {'A': self.A, 'B': self.B}
        self.cur = self.A
        self.gate = 25_000_000
        self._clkout = 1
        if check:
            self.resync()
            self.ident()

    def close(self): self.t.close()
    def __enter__(self): return self

    def __exit__(self, *a):
        try:
            self.safe()
        finally:
            self.close()

    def __getattr__(self, name):                                # pb.out(4, 1) is the last-used port's out(4, 1)
        if name in ('cur', 't', 'A', 'B', 'ports'): raise AttributeError(name)
        return getattr(self.cur, name)

    # -- the bus
    def wr(self, reg, val): self.t.write(_pack_w(REGS[reg] if isinstance(reg, str) else reg, val))

    def rd(self, reg):
        self.t.write(_pack_r(REGS[reg] if isinstance(reg, str) else reg))
        return struct.unpack('<I', self.t.read(4))[0]

    def resync(self):
        """Five 0x00 bytes complete any half-sent write and read the ID up to five times; drop the replies."""
        self.t.write(b'\x00' * 5)
        self.t.wait(getattr(self.t, 'settle', 0.05))
        self.t.flush()

    def ident(self):
        i = self.rd('ID')
        if i == 0xEC5BA2D2:
            raise IOError('board: it is running its own bring-up design (ID ec5ba2d2, booted from its flash), not pmodbench: '
                          'load build/pmodbench.bit into the FPGA with `openFPGALoader -c ft2232 build/pmodbench.bit` '
                          '(no -f: the flash is the ECP5 bring-up\'s)')
        if i != ID:
            raise IOError('board: ID register reads %08x, not %08x (is build/pmodbench.bit loaded?)' % (i, ID))
        self.gate = self.rd('GATE')
        self._clkout = self.rd('CONTROL') & 1
        return {'id': i, 'version': '%08x' % self.rd('VERSION'), 'gate_s': self.gate / F_CLK}

    def scratch_test(self, n=8):
        import random
        for _ in range(n):
            v = random.getrandbits(32)
            self.wr('SCRATCH', v)
            got = self.rd('SCRATCH')
            if got != v: raise IOError('scratch: wrote %08x read %08x' % (v, got))
        return n

    def leds(self, value=0, rgb=0):
        """LED1-7 from bits 1-7 of `value` (LED0 is the heartbeat), RGB from `rgb` (bit 0 red, 1 green, 2 blue)."""
        self.wr('LEDS', (value & 0xFE) | ((rgb & 7) << 8))

    def clk_out(self, on=True):
        """CLK OUT carries the 25 MHz TCXO (the reference of RF-MOD's r10 and IQ-MOD's q3), or is held low."""
        self._clkout = int(bool(on))
        self.wr('CONTROL', self._clkout)

    # -- the ports
    def use(self, board, port='A', reset=True):
        p = self.ports[port.upper()]
        p.use(board, reset=reset)
        self.cur = p
        return p

    def restart_all(self):
        """Restart every generator of both ports on the same clock."""
        self.wr('CONTROL', self._clkout | C_RESTART)

    def safe(self):
        """Every Pmod pin high-Z and every generator off, in one register write.  A line whose tile wants it driven
        low before it is let go (a TPS22917's ON) is taken low first.  The LOCK bits stay."""
        for p in self.ports.values():
            low = sum(1 << (io - 1) for io, d in (p.profile or {'pins': {}})['pins'].items() if d.get('release_low')) & p._oe
            if low:
                p.wr('SRC', sum(0 if low >> k & 1 else c << (4 * k) for k, c in enumerate(p._src)))
                p.wr('OUT_CLR', low)
        self.wr('CONTROL', self._clkout | C_SAFE)
        for p in self.ports.values():
            p._out = p._oe = p._gen_en = 0
            p._src = [0] * 8

    def pins(self):
        v = self.rd('PINS')
        return {'A': v & 0xFF, 'B': (v >> 8) & 0xFF, 'A_driven': (v >> 16) & 0xFF, 'B_driven': (v >> 24) & 0xFF}

    # -- the logic analyser
    def capture(self, n=1024, div=0, trigger=None, during=None, vcd=None, timeout=None):
        """n samples (up to 16384) of all sixteen pins, one every (div + 1) x 40 ns, as a numpy uint16 array: bit k-1
        is port A's IOk, bit 8 + k-1 port B's.  trigger: None starts at once; a 16-bit mask (or a list of (port, io))
        waits for the first change on one of those pins, and sample 0 is then the pins 40 ns before it.  during: a
        function called once the capture is armed (put the traffic to be captured in it).  vcd: also write this file."""
        import numpy as np
        n = min(max(1, int(n)), CAP_MAX)
        mask = 0
        if isinstance(trigger, int): mask = trigger & 0xFFFF
        elif trigger: mask = sum(1 << ((_io(io) - 1) + (8 if str(pt).upper() == 'B' else 0)) for pt, io in trigger)
        self.wr('CAP_DIV', div); self.wr('CAP_LEN', n); self.wr('CAP_TRIG', mask); self.wr('CAP_CTRL', 1)
        if during: during()
        span = n * (div + 1) / F_CLK
        if timeout is None: timeout = 2 * span + (10.0 if mask else 1.0)
        t0 = self.t.now()
        while True:
            s = self.rd('CAP_STAT')
            if s & 2: break
            if self.t.now() - t0 > timeout:
                self.wr('CAP_CTRL', 2)
                raise IOError('capture: not done after %.1f s (%s, %d samples)' % (timeout, 'triggered' if s & 4 else 'never triggered', (s >> 16) & 0x7FFF))
            self.t.wait(min(span / 2 + 20e-6, 0.05))
        words = (n + 1) // 2
        self.wr('DUMP_LEN', words)
        self.t.write(_pack_r(REGS['DUMP']))
        w = np.frombuffer(self.t.read(4 * words), dtype='<u4')
        s = np.empty(2 * words, dtype=np.uint16)
        s[0::2] = w & 0xFFFF
        s[1::2] = w >> 16
        s = s[:n].copy()
        if vcd: self.write_vcd(vcd, s, div)
        return s

    def signal_names(self):
        names = []
        for pn in 'AB':
            p = self.ports[pn]
            for io in range(1, 9):
                role = p.profile['pins'][io]['role'] if p.profile else ''
                names.append('%s_IO%d%s' % (pn, io, '_' + role if role else ''))
        return names

    def write_vcd(self, path, samples, div=0, names=None):
        """The capture as a Value Change Dump (GTKWave, PulseView, sigrok-cli -I vcd): sixteen one-bit signals,
        A_IO1.. then B_IO1.., named after the selected boards' lines; time in ns."""
        names = names or self.signal_names()
        step = (div + 1) * int(round(1e9 / F_CLK))
        ids = [chr(33 + k) for k in range(16)]
        with open(path, 'w') as f:
            f.write('$date pmodbench capture $end\n$version pmodbench.py $end\n$timescale 1 ns $end\n$scope module pmod $end\n')
            for k in range(16):
                f.write('$var wire 1 %s %s $end\n' % (ids[k], names[k]))
            f.write('$upscope $end\n$enddefinitions $end\n')
            prev = None
            for i, v in enumerate(samples):
                v = int(v)
                if prev is None:
                    f.write('#0\n$dumpvars\n' + ''.join('%d%s\n' % (v >> k & 1, ids[k]) for k in range(16)) + '$end\n')
                elif v != prev:
                    f.write('#%d\n' % (i * step) + ''.join('%d%s\n' % (v >> k & 1, ids[k]) for k in range(16) if (v ^ prev) >> k & 1))
                prev = v
            f.write('#%d\n' % (len(samples) * step))
        return path


# ---- the command line -----------------------------------------------------------------------------------------------------
_CHIP_BOARD = {'max2871': 'rf_mod', 'trf3722': 'rf_mod', 'pe43711': 'amod_n', 'mt6701': 'amod_b', 'whoami': 'amod_b', 'dsm': 'amod_a', 'quad': 'amod_m'}


def main(argv, transport=None):
    args = list(argv)
    port, pmod, board = DEFAULT_PORT, 'A', None
    if args and args[0].startswith('/dev/'): port = args.pop(0)
    while args and args[0] in ('--pmod', '--board'):
        k, v = args.pop(0), args.pop(0)
        if k == '--pmod': pmod = v.upper()
        else: board = v
    if not args:
        print(__doc__); return 2
    cmd = args.pop(0)
    pb = PmodBench(port, transport=transport)
    try:
        if cmd == 'ident':
            print(pb.ident()); print(pb.pins())
        elif cmd == 'safe':
            pb.safe(); print('every Pmod pin is high-Z, the generators are off')
        elif cmd == 'pins':
            print(pb.pins())
            for n in 'AB': print(n, pb.ports[n].state())
        elif cmd == 'leds':
            pb.leds(int(args[0], 0))
        elif cmd == 'capture':
            n, div = int(args[0]) if args else 1024, int(args[1]) if len(args) > 1 else 0
            s = pb.capture(n, div, vcd=args[2] if len(args) > 2 else None)
            print('%d samples, %g s apart; A toggled %s, B toggled %s' % (len(s), (div + 1) / F_CLK,
                  bin(int((s & 0xFF).max() ^ (s & 0xFF).min())), bin(int((s >> 8).max() ^ (s >> 8).min()))))
        else:
            if cmd == 'use':
                p = pb.use(args[0], pmod, reset=True)
                print('Pmod %s is %s:' % (pmod, p.profile['title']))
                for io, d in sorted(p.profile['pins'].items()): print('  IO%d %-6s %-12s %s' % (io, d['dir'], d['role'], d['note']))
                return 0
            p = pb.use(board or _CHIP_BOARD.get(cmd, 'raw'), pmod, reset=False)
            if cmd == 'out': p.out(args[0], int(args[1], 0))
            elif cmd == 'in': print(p.inp(args[0]) if args else '0x%02x' % p.inp())
            elif cmd == 'release': p.release(args[0] if args else None)
            elif cmd == 'clock': print('%.6f Hz' % p.clock(_io(args[0]), float(args[1]), float(args[2]) if len(args) > 2 else 0.5))
            elif cmd == 'stop': p.stop()
            elif cmd == 'freq': print('%.1f Hz' % p.freq(args[0]))
            elif cmd == 'max2871':
                w, locked = p.max2871_set(float(args[0]), int(args[1]) if len(args) > 1 else 1)
                pl = p.last['max2871']['plan']
                print('%.6f MHz (VCO %.3f MHz / %d): %s: %s' % (pl['f_hz'] / 1e6, pl['f_vco'] / 1e6, 1 << pl['diva'],
                      ' '.join('%08X' % x for x in w), 'LOCKED' if locked else 'NOT locked (MUXOUT low)'))
            elif cmd == 'pe43711': print('%.2f dB' % p.pe43711_set(float(args[0])))
            elif cmd == 'trf3722':
                if args[0] == 'read':
                    w = p.trf3722_read(int(args[1]))
                    print('%08X %s' % (w, trf3722.unpack(w)[1] if (w >> 3) & 3 == 1 else '(address bits wrong: no chip?)'))
                elif args[0] == 'write': print('%08X' % p.trf3722_write(int(args[1]), int(args[2], 0)))
                else:
                    w, pl = p.trf3722_set(float(args[1]))
                    print(pl); print(' '.join('R%d=%08X' % (r, w[r]) for r in trf3722.WRITE_ORDER))
            elif cmd == 'mt6701': print(p.mt6701_read())
            elif cmd == 'whoami': print('0x%02X' % p.lsm6dso_whoami())
            elif cmd == 'density': print('%.5f' % p.density(args[0], int(args[1]) if len(args) > 1 else 1, int(args[2]) if len(args) > 2 else 12))
            elif cmd == 'dsm': print('%.5f' % p.dsm_loop(float(args[0]) if args else 1e6))
            elif cmd == 'quad': print(p.quad())
            else:
                print(__doc__); return 2
    finally:
        pb.close()                                              # not safe(): the command line leaves the pins as set
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
