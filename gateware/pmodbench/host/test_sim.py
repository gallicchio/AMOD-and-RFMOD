#!/usr/bin/env python3
"""host/pmodbench.py against the RTL: the driver's own bytes go through the simulated UART into rtl/pmodbench.v
(sim/tb_cosim.v in iverilog, host/simlink.py), with the tile models of sim/tiles.v in the two Pmod sockets, and
what the driver returns is compared with what the models saw.  Unlike the host board's test_sim.py, which this
imitates, the link is live (two pipes), so the driver's polling loops run as they will on the board.

    python3 host/test_sim.py            every scenario, in parallel (about a minute); `make test`
    python3 host/test_sim.py max2871    only the scenarios whose name contains the word

Each scenario has its own simulation.  The capture scenario also hands its VCD files to sigrok-cli's SPI decoder
when sigrok-cli is installed (file input only: it never touches a device), as an independent reading.
"""
import concurrent.futures
import os
import shutil
import subprocess
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import max2871                                                   # noqa: E402
import pmodbench                                                 # noqa: E402
import simlink                                                   # noqa: E402
import trf3722                                                   # noqa: E402
from pmodbench import PmodBench, ProfileError                    # noqa: E402

BUILD = simlink.BUILD


class Checks(list):
    def __call__(self, what, ok):
        self.append((bool(ok), what))
        return bool(ok)

    def raises(self, what, exc, fn):
        try:
            fn()
        except exc:
            return self(what, True)
        except Exception as e:                                   # the wrong refusal is a failure too
            return self(what + ' (raised %s: %s)' % (type(e).__name__, e), False)
        return self(what + ' (nothing was raised)', False)


def near(a, b, tol): return abs(a - b) <= tol


# ---- the scenarios: each gets (c, link, pb) ---------------------------------------------------------------------------
def s_bus_profiles(c, link, pb):
    i = pb.ident()
    c('ident: ID 0x504D4231, the build date, a 1 ms gate in simulation (%s)' % i, i['id'] == pmodbench.ID and i['version'] == '20261115' and i['gate_s'] == 0.001)
    c('scratch register through the UART', pb.scratch_test(3) == 3)
    c('power-up: no pin is driven', pb.pins() == {'A': 0, 'B': 0, 'A_driven': 0, 'B_driven': 0})
    c.raises('before use(): nothing may be driven', ProfileError, lambda: pb.A.out(4, 1))
    link.plug('A', 'rf_mod')
    rf = pb.use('rf_mod', 'A')
    c('use(rf_mod): its outputs driven (IO2, 3, 4, 6), nothing else', pb.pins()['A_driven'] == 0x2E)
    c.raises('rf_mod: driving IO1 (MUXOUT, an output of the tile) is refused', ProfileError, lambda: rf.out(1, 1))
    c.raises('rf_mod: driving IO7 (unused) is refused', ProfileError, lambda: rf.out(7, 1))
    c.raises('rf_mod: a clock on IO5 (RDBK) is refused', ProfileError, lambda: rf.clock(5, 1e6))
    c.raises('rf_mod: SPI with MOSI on IO1 is refused', ProfileError, lambda: rf.spi(0, 8, mosi=1))
    c.raises('rf_mod: a helper for another board is refused', ProfileError, lambda: rf.pe43711_set(3))
    c('rf_mod: after the refusals the pins are as they were', pb.pins()['A_driven'] == 0x2E)
    rf.wr('OE', 0xFF | (rf._lock << 8))                         # a driver gone wrong: every enable set
    c('the gateware lock holds IO1, 5, 7, 8 undriven whatever OE says', pb.pins()['A_driven'] == 0x2E)
    rf.wr('OE', rf._oe | (rf._lock << 8))
    rf.out(4, 1); a = rf.inp(4); rf.out(4, 0); b = rf.inp(4)
    c('out() and inp() on IO4', (a, b) == (1, 0))
    link.plug('B', 'amod_b')
    mb = pb.use('amod_b', 'B')
    c('use(amod_b): SCK and both chip selects idle high', pb.pins()['B_driven'] == 0xFB and mb.inp() & 0xA8 == 0xA8)
    mb.out(6, 0)
    c.raises('amod_b: the second chip select low while the first is low is refused', ProfileError, lambda: mb.out(8, 0))
    c('amod_b: and IO8 stayed high', mb.inp(8) == 1)
    mb.out(6, 1)
    mb.release()                                                # (a tile is not swapped under driven pins)
    link.plug('B', 'iq_mod')
    iq = pb.use('iq_mod', 'B')
    c('use(iq_mod): V1 high, V2 low', (iq.inp(5), iq.inp(8)) == (1, 0))
    c.raises('iq_mod: V1 low while V2 is low is refused', ProfileError, lambda: iq.out(5, 0))
    iq.rf_switch(2)
    c('iq_mod: rf_switch(2) swaps both lines in one write', (iq.inp(5), iq.inp(8)) == (0, 1))
    iq.out(6, 1)                                                # the noise source on: its TPS22917 must be taken low before release
    link.knob('B', 'clear', 0)
    pb.leds(0xAA, rgb=5)
    c('LEDS register', pb.rd('LEDS') == 0x5AA)
    pb.safe()
    q = link.query()
    c('safe(): every pin of both ports high-Z', pb.pins()['A_driven'] == 0 and pb.pins()['B_driven'] == 0)
    c('safe(): the noise switch line was driven low before it was released', q['B']['m6']['falls'] == 1)
    c('the bench saw no contention, no chip-select fight, no switch state with V1 = V2 (%s %s)' % (q['A']['sock'], q['B']['sock']),
      q['A']['sock']['contention'] == 0 and q['B']['sock']['contention'] == 0 and q['B']['sock']['cs_fight'] == 0 and q['B']['sock']['sw_equal'] == 0)
    rf.out(4, 1)
    c('after safe() the profile still stands (IO4 can be driven again, IO1 cannot)', pb.pins()['A_driven'] == 0x08)
    c.raises('... IO1 still refused', ProfileError, lambda: rf.out(1, 0))
    # the command line, on the same simulated board
    class Keep(pmodbench.Transport):                             # main() closes its transport: keep ours
        def __getattr__(self, n): return getattr(link, n)
        def write(self, d): link.write(d)
        def read(self, n): return link.read(n)
        def flush(self): link.flush()
        def wait(self, s): link.wait(s)
        def now(self): return link.now()
        def close(self): pass
        settle = link.settle
    rc = pmodbench.main(['--board', 'rf_mod', 'out', 'IO6', '1'], transport=Keep())
    c('command line: --board rf_mod out IO6 1 (and IO4 left as it was)', rc == 0 and pb.pins()['A_driven'] == 0x28 and pb.pins()['A'] & 0x28 == 0x28)
    try:
        pmodbench.main(['--board', 'rf_mod', 'out', 'IO1', '1'], transport=Keep()); ok = False
    except ProfileError:
        ok = True
    c('command line: out IO1 on rf_mod is refused', ok and pb.pins()['A_driven'] == 0x28)
    rc = pmodbench.main(['safe'], transport=Keep())
    c('command line: safe', rc == 0 and pb.pins()['A_driven'] == 0)


def s_generators(c, link, pb):
    raw = pb.use('raw', 'A')
    f = raw.clock(3, 1e6, duty=0.25)
    link.knob('A', 'clear', 0); link.wait(100e-6)
    m = link.query()['A']['m3']
    c('clock(IO3, 1 MHz, 25 %%): %.3f Hz set; the pin shows 1000 ns periods, 240-280 ns high (%s)' % (f, m),
      near(f, 1e6, 1.0) and m['min_period'] == 1000.0 and m['max_period'] == 1000.0 and 240 <= m['min_high'] and m['max_high'] <= 280 and m['rises'] >= 98)
    raw.clock(4, 1e6, duty=0.25, phase=0.25, gen=2); raw.start(1, 2)
    link.wait(50e-6)
    q = link.query()['A']
    lag = (q['m4']['t_rise'] - q['m3']['t_rise']) % 1000.0
    c('clock(phase=0.25): IO4 lags IO3 by a quarter period (%.0f ns)' % lag, 210 <= lag <= 290)
    raw.stop()
    link.wait(5e-6)
    c('stop(): the clock pins are low', raw.inp() & 0x0C == 0)
    pb.safe()
    # AMOD-A's ultrasound bridge: antiphase bursts, 8 cycles of 40 kHz in every 20
    link.plug('A', 'amod_a')
    a = pb.use('amod_a', 'A')
    c('use(amod_a): IO3, 4, 6, 8 driven; IO2 (audio) left high-Z until used', pb.pins()['A_driven'] == 0xAC)
    f = a.antiphase(a.pin('IN2'), a.pin('IN1'), 40e3, burst=(8, 20), gen=3)
    link.wait(250e-6); link.knob('A', 'clear', 0); link.wait(1000e-6)
    q = link.query()['A']
    c('antiphase(40 kHz, burst 8 of 20): 16 pulses on each line in two burst periods, never both high (%.2f Hz)' % f,
      q['m4']['rises'] == 16 and q['m3']['rises'] == 16 and q['hb']['overlaps'] == 0 and near(q['m4']['max_low'], 312500, 100))
    a.stop(); pb.safe()
    # AMOD-C: the two switch phases, the filter clock, the modulator's density, the comparator's bit
    link.plug('A', 'amod_c')
    cc = pb.use('amod_c', 'A')
    r = cc.two_phase(cc.pin('PHI1'), cc.pin('PHI2'), 100e3, gap=300e-9)
    cc.clock(cc.pin('FCLK'), 500e3, gen=3)
    link.knob('A', 'clear', 0); link.wait(2e-3)
    q = link.query()['A']
    c('two_phase(100 kHz, gap 300 ns): gap set %.0f ns; never both high in 200 periods, shortest dead time %.0f ns'
      % (r['gap'] * 1e9, q['c5']['min_gap']), q['c5']['overlaps'] == 0 and q['c5']['edges'] >= 390 and q['c5']['min_gap'] >= 300 and near(r['gap'], 320e-9, 1e-12))
    c('a third generator alongside: 500 kHz on FCLK', q['m3']['min_period'] == 2000.0 and q['m3']['max_period'] == 2000.0)
    link.knob('A', 'level', 0.3)
    cc.clock(cc.pin('DSCLK'), 1e6, gen=4)
    d = cc.density(cc.pin('DSBIT'), clock_gen=4, log2n=10)
    c('density(): 0.3 of the modulator model\'s bits are ones (%.4f)' % d, near(d, 0.3, 0.004))
    link.knob('A', 'cmp', 1); hi = cc.inp(cc.pin('CMP')); link.knob('A', 'cmp', 0); lo = cc.inp(cc.pin('CMP'))
    c('inp(CMP) follows the comparator model', (hi, lo) == (1, 0))
    c.raises('amod_c: driving DSBIT is refused', ProfileError, lambda: cc.out(7, 1))
    c('AMOD-A and AMOD-C: no contention', q['sock']['contention'] == 0)
    pb.safe()
    # the frequency counter (loopback jig), the quadrature decoder (AMOD-M), three PWM phases (AMOD-B), on Pmod B
    link.plug('B', 'loop_jig')
    lb = pb.use('raw', 'B')
    lb.clock(1, 1e6)
    f = lb.freq(5)
    c('freq(): 1 MHz looped back onto IO5 reads %.0f Hz (1 kHz steps with the 1 ms gate)' % f, near(f, 1e6, 1001))
    pb.safe()
    link.plug('B', 'amod_m')
    mm = pb.use('amod_m', 'B')
    z = mm.quad(reset=True)
    link.knob('B', 'step_ns', 2000); link.knob('B', 'steps', 200); link.wait(500e-6)
    up = mm.quad()
    link.knob('B', 'steps', -450); link.wait(1000e-6)
    dn = mm.quad()
    c('quad(): 0, then +200, then -250 after 450 back, no errors (%s %s %s)' % (z, up, dn), (z, up, dn) == ((0, 0), (200, 0), (-250, 0)))
    c.raises('amod_m: driving ENC_A is refused', ProfileError, lambda: mm.out(5, 1))
    pb.safe()
    link.plug('B', 'amod_b')
    mb = pb.use('amod_b', 'B')
    f = mb.pwm3((0.25, 0.5, 0.75), 20e3)
    link.knob('B', 'clear', 0); link.wait(300e-6)
    q = link.query()['B']
    hi = [q[k]['high'] for k in ('m5', 'm1', 'm2')]                       # INHA, INHB, INHC
    ctr = [(q[k]['t_fall'] - q[k]['high'] / 2) % 50000.0 for k in ('m5', 'm1', 'm2')]
    c('pwm3(0.25, 0.5, 0.75 at 20 kHz): highs of %.0f, %.0f, %.0f ns, centred on one instant' % tuple(hi),
      near(hi[0], 12500, 45) and near(hi[1], 25000, 45) and near(hi[2], 37500, 45) and max(ctr) - min(ctr) <= 41 and near(f, 20e3, 0.01))
    c('AMOD-B: no contention, the chip selects untouched (%s)' % q['sock'], q['sock']['contention'] == 0 and q['sock']['cs_fight'] == 0 and mb.inp() & 0xA0 == 0xA0)
    pb.safe()


def _max(c, link, pb, port, board, f_hz, power):
    link.plug(port, board)
    p = pb.use(board, port)
    w, locked = p.max2871_set(f_hz, power)
    want_w, plan = max2871.words(f_hz, power)
    sent = [v for k, v in max2871.power_up_steps(want_w) if k == 'w']
    got = link.words(port, 'max')
    q = link.query()[port]
    c('%s max2871_set(%.6g Hz, step %d): MUXOUT read locked' % (board, f_hz, power), locked is True and q['max']['locked'] == 1 and p.max2871_locked())
    c('  the six words returned are the arithmetic\'s: %s' % ' '.join('%08X' % x for x in w), w == want_w)
    c('  the model latched exactly the 13 words of the power-up sequence, in order', got == sent and len(got) == 13)
    c('  the pause between the two passes was at least 20 ms; no word of the wrong length; no timing violation',
      q['max']['pause_ok'] == 1 and q['max']['passes'] == 2 and q['max']['bad_len'] == 0 and q['max']['viol'] == 0)
    c('  the model decodes the words to %.6f MHz (VCO %.3f MHz)' % (q['max']['f_out'] / 1e6, q['max']['f_vco'] / 1e6),
      near(q['max']['f_out'], f_hz, 1.0) and near(q['max']['f_vco'], plan['f_vco'], 1.0))
    c('  RFOUTB was never enabled; no contention', q['max']['rfb_on'] == 0 and all(not x & 0x100 for x in got if x & 7 == 4) and q['sock']['contention'] == 0)
    return p


def s_max2871_rf_mod(c, link, pb):
    _max(c, link, pb, 'A', 'rf_mod', 915e6, 3)


def s_max2871_iq_mod(c, link, pb):
    p = _max(c, link, pb, 'B', 'iq_mod', 2400e6, 1)
    p.rf_switch(2); p.rf_switch(1)
    c('  iq_mod: the RF switch lines never matched', link.query()['B']['sock']['sw_equal'] == 0)


def s_pe43711_trf3722(c, link, pb):
    link.plug('B', 'amod_n')
    c('AMOD-N plugged, pins released: LE reads high (its pull-up)', pb.B.inp(4) == 1)
    n = pb.use('amod_n', 'B')
    r = [n.pe43711_set(12.5)]; q1 = link.query()['B']['pe']
    r.append(n.pe43711_set(31.75)); q2 = link.query()['B']['pe']
    r.append(n.pe43711_set(0)); q3 = link.query()['B']['pe']
    c('pe43711_set(12.5), (31.75), (0): the model latched 50, 127, 0 (%s)' % r, (q1['att'], q2['att'], q3['att']) == (50, 127, 0) and r == [12.5, 31.75, 0.0])
    c('  one latch a call, eight bits each, bit 7 low, no clock while LE was high, no timing violation',
      q3['latches'] == 3 and q3['bad_len'] == 0 and q3['bad_d7'] == 0 and q3['clk_while_le'] == 0 and q3['viol'] == 0)
    c.raises('  32 dB is refused', ValueError, lambda: n.pe43711_set(32))
    link.plug('A', 'rf_mod')
    rf = pb.use('rf_mod', 'A')
    w = rf.trf3722_write(1, RDIV=2, ICP=3, CAL_CLK_SEL=14)
    q = link.query()['A']
    c('trf3722_write(1, fields): %08X is in the model\'s register 1' % w, q['trf']['r1'] == w and trf3722.unpack(w)[1]['RDIV'] == 2)
    c('trf3722_read(1) returns it', rf.trf3722_read(1) == w)
    c('trf3722_read(4), (6): the reset values', rf.trf3722_read(4) == trf3722.RESET[4] and rf.trf3722_read(6) == trf3722.RESET[6])
    r0 = rf.trf3722_read(0)
    c('trf3722_read(0): %08X, chip ID 1' % r0, r0 == 0x00500028 and trf3722.unpack(r0)[1]['CHIP_ID'] == 1)
    w6 = rf.trf3722_write(6, 0x12345600)
    c('trf3722_write(6, raw word): the address bits are set for it', w6 == 0x1234560E and rf.trf3722_read(6) == 0x1234560E)
    n0 = link.query()['A']['trf']['writes']
    words, plan = rf.trf3722_set(915e6)
    q = link.query()['A']
    got = [q['trf.w%d' % i]['v'] for i in range(n0, q['trf']['writes'])]
    c('trf3722_set(915 MHz): registers 1, 3, 4, 5, 6, 2 arrive in that order', got == [words[r] for r in trf3722.WRITE_ORDER])
    c('  and read back (register 2 without EN_CAL, which clears itself)',
      all(rf.trf3722_read(r) == (words[r] & 0x7FFFFFFF if r == 2 else words[r]) for r in range(1, 7)))
    q = link.query()['A']
    c('  no bad address, short word or timing violation; the MAX2871 on the same lines latched nothing; no contention',
      q['trf']['bad_addr'] == 0 and q['trf']['short_words'] == 0 and q['trf']['viol'] == 0 and q['max']['n'] == 0 and q['sock']['contention'] == 0)


def s_amod_b_dsm(c, link, pb):
    link.plug('B', 'amod_b')
    mb = pb.use('amod_b', 'B')
    q0 = link.query()['B']                                       # (with the pins floating, before use(), the models saw anything)
    link.knob('B', 'angle', 0x1A5C); link.knob('B', 'status', 2)
    r = mb.mt6701_read()
    q = link.query()['B']
    c('mt6701_read(): angle %d (%.2f deg), status %d, CRC ok' % (r['raw'], r['angle'], r['status']),
      r['raw'] == 0x1A5C and r['status'] == 2 and r['crc_ok'] and near(r['angle'], 0x1A5C * 360 / 16384.0, 1e-9))
    c('  the 24 bits are the ones the model sent, in 24 clocks, SCK idling high', r['word'] == q['mt']['sent'] and q['mt']['nclk'] == 24 and q['mt']['mode_viol'] == q0['mt']['mode_viol'])
    link.knob('B', 'angle', 0x2F01); link.knob('B', 'status', 0)
    r = mb.mt6701_read()
    c('  another angle (MSB set): %d' % r['raw'], r['raw'] == 0x2F01 and r['crc_ok'])
    who = mb.lsm6dso_whoami()
    c('lsm6dso_whoami(): 0x%02X' % who, who == 0x6C)
    mb.lsm6dso_write(0x10, 0x60)
    c('lsm6dso_write / read of CTRL1_XL, and two registers in one frame', mb.lsm6dso_read(0x10) == 0x60 and mb.lsm6dso_read(0x0F, 2) == [0x6C, 0x60])
    q = link.query()['B']
    c('  SPI mode 3 as the model wants it; the chip selects never low together; no contention (%s %s %s)' % (q['imu'], q0['imu'], q['sock']),
      q['imu']['mode_viol'] == q0['imu']['mode_viol'] and q['sock']['cs_fight'] == 0 and q['sock']['contention'] == 0)
    link.plug('A', 'amod_a')
    a = pb.use('amod_a', 'A')
    link.knob('A', 'vin', 1.1)
    d1 = a.dsm_loop(1e6, log2n=11)
    link.knob('A', 'vin', 2.2)
    d2 = a.density(a.pin('BIT'), 1, 11)
    c('dsm_loop() round a6: IN 1.1 V gives a ones density of %.4f (1/3), 2.2 V %.4f (2/3)' % (d1, d2), near(d1, 1 / 3.0, 0.01) and near(d2, 2 / 3.0, 0.01))
    c('  no contention on AMOD-A', link.query()['A']['sock']['contention'] == 0)


def _bits(s, clk_bit, data_bit, rising=True):
    """The data line at each clock edge of a capture (numpy uint16 samples)."""
    out, prev = [], int(s[0]) >> clk_bit & 1
    for v in s[1:]:
        cur = int(v) >> clk_bit & 1
        if cur != prev and bool(cur) == rising: out.append(int(v) >> data_bit & 1)
        prev = cur
    return out


def read_vcd(path):
    """A plain reader for the VCD files write_vcd makes: {name: [(time_ns, value), ...]}."""
    names, sig, t = {}, {}, 0
    for line in open(path):
        f = line.split()
        if not f: continue
        if f[0] == '$var': names[f[3]] = f[4]; sig[f[4]] = []
        elif f[0].startswith('#'): t = int(f[0][1:])
        elif f[0][0] in '01' and f[0][1:] in names: sig[names[f[0][1:]]].append((t, int(f[0][0])))
    return sig


def find_sigrok():
    exe = shutil.which('sigrok-cli') or os.path.expanduser('~/.local/bin/sigrok-cli')
    return exe if os.path.exists(exe) else None


def sigrok_spi(vcd, clk, mosi, bitorder='msb-first', cpol=0, cpha=0):
    """The bytes sigrok-cli's SPI decoder reads on `mosi` from a VCD file (file input only), or None without sigrok-cli."""
    exe = find_sigrok()
    if not exe: return None
    out = subprocess.run([exe, '-i', vcd, '-I', 'vcd', '-P', 'spi:clk=pmod.%s:mosi=pmod.%s:cpol=%d:cpha=%d:bitorder=%s:wordsize=8' % (clk, mosi, cpol, cpha, bitorder),
                          '-A', 'spi=mosi-data'], capture_output=True, text=True, timeout=120)
    if out.returncode != 0: raise IOError('sigrok-cli: ' + out.stderr.strip()[-300:])
    return [int(l.split(':')[1], 16) for l in out.stdout.splitlines() if ':' in l]


def s_capture_vcd(c, link, pb):
    link.plug('A', 'rf_mod'); link.plug('B', 'amod_n')
    rf = pb.use('rf_mod', 'A'); n = pb.use('amod_n', 'B')
    word = 0xA5C3F007
    vcd1 = os.path.join(BUILD, 'cosim_max_word.vcd')
    s = pb.capture(2048, div=4, trigger=[('A', rf.pin('SCLK'))], during=lambda: rf._max_word(word, rf.pin('LE_MAX')), vcd=vcd1)
    bits = _bits(s, 2, 1)                                        # SDATA (IO2) at SCLK's (IO3) rising edges
    got = sum(b << (31 - i) for i, b in enumerate(bits[:32]))
    le = [int(v) >> 3 & 1 for v in s]
    c('capture(2048, div 4, trigger on SCLK): %d samples; 32 clocks; SDATA at their rising edges is %08X; LE pulses after them'
      % (len(s), got), len(s) == 2048 and len(bits) == 32 and got == word and le[0] == 0 and max(le) == 1 and le[-1] == 0)
    v = read_vcd(vcd1)
    c('the VCD names the sixteen lines after the boards (A_IO3_SCLK, B_IO4_LE, ...) and holds the same edges',
      len(v) == 16 and 'A_IO3_SCLK' in v and 'B_IO4_LE' in v and sum(1 for t, x in v['A_IO3_SCLK'] if x == 1 and t > 0) == 32)
    link.wait(200e-6)
    vcd2 = os.path.join(BUILD, 'cosim_pe43711.vcd')
    s2 = pb.capture(1024, div=4, trigger=[('B', n.pin('CLK'))], during=lambda: n.pe43711_set(12.5), vcd=vcd2)
    bits = _bits(s2 >> 8, 2, 1)
    c('capture of pe43711_set(12.5): eight clocks, SI LSB first is %d' % sum(b << i for i, b in enumerate(bits[:8])), len(bits) == 8 and sum(b << i for i, b in enumerate(bits)) == 50)
    c('the models agree: the MAX2871 latched %08X, the PE43711 50' % link.words('A', 'max')[0], link.words('A', 'max') == [word] and link.query()['B']['pe']['att'] == 50)
    a = sigrok_spi(vcd1, 'A_IO3_SCLK', 'A_IO2_SDATA')
    b = sigrok_spi(vcd2, 'B_IO3_CLK', 'B_IO2_SI', bitorder='lsb-first')
    if a is None:
        c('sigrok-cli is not installed: its SPI decoder was NOT run on the VCD files (skipped)', True)
    else:
        c('sigrok-cli\'s SPI decoder reads the MAX2871 capture as %s' % ' '.join('%02X' % x for x in a), a == [0xA5, 0xC3, 0xF0, 0x07])
        c('sigrok-cli\'s SPI decoder reads the PE43711 capture (LSB first) as %s' % ' '.join('%02X' % x for x in b), b == [50])
    pb.safe()
    raw = pb.use('raw', 'A'); link.plug('A', 'none')
    raw.clock(1, 1e6)
    s3 = pb.capture(101, div=0)
    e = sum(1 for i in range(1, len(s3)) if (int(s3[i]) ^ int(s3[i - 1])) & 1)
    c('capture(101) untriggered at 25 MS/s of a 1 MHz clock: an odd length, %d edges in 4 us' % e, len(s3) == 101 and e == 8)
    pb.safe()


SCENARIOS = [('bus, profiles, pins, command line', s_bus_profiles), ('generators, density, freq, quad, pwm3', s_generators),
             ('max2871 on rf_mod', s_max2871_rf_mod), ('max2871 on iq_mod', s_max2871_iq_mod),
             ('pe43711 and trf3722', s_pe43711_trf3722), ('mt6701, lsm6dso, dsm_loop', s_amod_b_dsm), ('capture, vcd, sigrok', s_capture_vcd)]


def run_scenario(fn, vvp):
    c = Checks()
    link = None
    try:
        link = simlink.SimLink(vvp)
        pb = PmodBench(transport=link)
        fn(c, link, pb)
    except Exception as e:
        tb = traceback.extract_tb(sys.exc_info()[2])
        where = ' <- '.join('%s:%d' % (os.path.basename(f.filename), f.lineno) for f in tb[-3:])
        c('the scenario stopped: %s: %s (%s)' % (type(e).__name__, e, where), False)
    finally:
        if link: link.close()
    return c


def run_all(only=None, vvp=None, quiet=False):
    """Run the scenarios (those whose name contains `only`) in parallel; returns [(scenario, ok, text), ...]."""
    vvp = vvp or simlink.compile_tb()
    todo = [(n, f) for n, f in SCENARIOS if not only or only in n]
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(todo)) as ex:
        futs = [(n, ex.submit(run_scenario, f, vvp)) for n, f in todo]
        res = []
        for n, fu in futs:
            cs = fu.result()
            if not quiet: print('%s:' % n)
            for ok, what in cs:
                if not quiet: print(('  ok: ' if ok else 'FAIL: ') + what)
                res.append((n, ok, what))
    return res


def main(argv):
    res = run_all(argv[0] if argv else None)
    fails = sum(1 for _, ok, _ in res if not ok)
    print('%d checks, %d failures' % (len(res), fails))
    print('PASS: test_sim, %d checks' % len(res) if not fails else 'FAIL: test_sim, %d of %d checks failed' % (fails, len(res)))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
