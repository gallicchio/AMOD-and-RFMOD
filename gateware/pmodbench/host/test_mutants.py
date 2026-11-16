#!/usr/bin/env python3
"""Do the tests catch bugs?  Each mutant below is one planted bug: a one-line change to the RTL or to the driver.
The whole directory is copied to a temporary place, the change is made in the copy (never here), and the
test that should notice is run there: the self-checking testbench for an RTL mutant, a scenario of the
co-simulation for a driver mutant.  A mutant is "caught" when that test fails.  `make mutants` runs them all in
parallel (about a minute) and fails if any mutant survives.

    python3 host/test_mutants.py [word]      only the mutants whose name contains the word
"""
import concurrent.futures
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
OSS = os.path.expanduser(os.environ.get('OSS_CAD_SUITE', '~/mudd/133electronics/icepi-zero-dac-adc/tools/oss-cad-suite'))
RTL = ['rtl/pmodbench.v', 'rtl/pmod_port.v', 'rtl/capture.v', 'rtl/vendor/uart.v', 'rtl/vendor/regbus.v', 'sim/models.v', 'sim/tiles.v']

# (name, file, the line as it is, the line with the bug, the test: 'tb' or a co-simulation scenario's name)
MUTANTS = [
    ('RTL: the SPI engine shifts out from the wrong end (bit order)', 'rtl/pmod_port.v',
     'wire        tx_bit = spi_lsb ? tx_sh[0] : tx_sh[31];', 'wire        tx_bit = spi_lsb ? tx_sh[31] : tx_sh[0];', 'tb'),
     ('RTL: the LOCK bits do not gate the output enables (a locked input pin can be driven)', 'rtl/pmod_port.v',
     'wire [7:0] oe_now = oe_r & ~lock_r;', 'wire [7:0] oe_now = oe_r;', 'tb'),
    ('RTL: a pin is driven at power-up', 'rtl/pmod_port.v',
     'reg [7:0]  out_r = 0, oe_r = 0, lock_r = 0;', "reg [7:0]  out_r = 0, oe_r = 8'h10, lock_r = 0;", 'tb'),
    ('RTL: MISO is sampled one clock early', 'rtl/pmod_port.v',
     'module pmod_port #(parameter SPI_SKEW = 3) (', 'module pmod_port #(parameter SPI_SKEW = 2) (', 'tb'),
    ("RTL: a generator's inverted output ignores the burst gate and the enable", 'rtl/pmod_port.v',
     'gn[gi] <= on && !hi;', 'gn[gi] <= !hi;', 'tb'),
    ('RTL: the PHASE register is ignored (two "non-overlapping" phases coincide)', 'rtl/pmod_port.v',
     'wire [31:0] ph = acc + phase;', 'wire [31:0] ph = acc;', 'tb'),
    ('RTL: the capture packs its two samples a word the wrong way round', 'rtl/capture.v',
     "mem_wd <= count[0] ? {prev, lo} : {16'h0000, prev};", "mem_wd <= count[0] ? {lo, prev} : {16'h0000, prev};", 'tb'),
    ('RTL: the quadrature decoder counts the wrong way', 'rtl/pmod_port.v',
     "4'b0001, 4'b0111, 4'b1110, 4'b1000: q_cnt <= q_cnt + 32'd1;", "4'b0001, 4'b0111, 4'b1110, 4'b1000: q_cnt <= q_cnt - 32'd1;", 'tb'),
    ("driver: RF-MOD's profile lists IO1 (MUXOUT, the tile's output) as an FPGA output", 'host/pmodbench.py',
     """1: _in('MUXOUT', "r10: the MAX2871's MUX pin (programmed as digital lock detect)"), 2: _out('SDATA', 'r10 and r13: serial data'),""",
     """1: _out('MUXOUT', "r10: the MAX2871's MUX pin (programmed as digital lock detect)"), 2: _out('SDATA', 'r10 and r13: serial data'),""",
     'bus, profiles'),
    ('driver: the profile check never refuses (only the gateware lock is left)', 'host/pmodbench.py',
     "if p['dir'] not in ('out', 'io'):", "if p['dir'] not in ('out', 'io', 'in', 'unused'):", 'bus, profiles'),
    ('driver: the PE43711 word goes out MSB first', 'host/pmodbench.py',
     'self.spi(code, 8, mode=0, lsb=True, read=False)', 'self.spi(code, 8, mode=0, lsb=False, read=False)', 'pe43711'),
    ('driver: the TRF3722 word goes out MSB first', 'host/pmodbench.py',
     'self.spi(w, 32, mode=0, lsb=True, read=False)', 'self.spi(w, 32, mode=0, lsb=False, read=False)', 'trf3722'),
    ('driver: the MAX2871 pauses are 2 ms, not the 20 ms the datasheet asks', 'host/max2871.py',
     'SEQ_WAIT_S = 0.020 ', 'SEQ_WAIT_S = 0.002 ', 'max2871 on rf_mod'),
    ('driver: the MAX2871 output divider is one step off below 3 GHz', 'host/max2871.py',
     "r4 = _m.field(r4, 22, 20, p['diva'])", "r4 = _m.field(r4, 22, 20, max(0, p['diva'] - 1))", 'max2871 on rf_mod'),
    ('driver: the MT6701 is read in plain SPI mode 3 (each bit sampled as it changes)', 'host/pmodbench.py',
     'w = self.spi(0, 24, mode=3, late=True, freq=500e3)', 'w = self.spi(0, 24, mode=3, late=False, freq=500e3)', 'mt6701'),
    ("driver: AMOD-A's loop is closed with the bit, not its inverse", 'host/pmodbench.py',
     'self._source({fb_io: SRC_BIT_INV if invert else SRC_BIT})', 'self._source({fb_io: SRC_BIT if invert else SRC_BIT_INV})', 'mt6701'),
    ('driver: two_phase() gives both generators the same phase', 'host/pmodbench.py',
     'for g, ph in ((ga, 0), (gb, 1 << 31)):', 'for g, ph in ((ga, 0), (gb, 0)):', 'generators'),
    ('driver: safe() releases the pins without the SAFE strobe (generators left running, port B forgotten)', 'host/pmodbench.py',
     "self.wr('CONTROL', self._clkout | C_SAFE)", "self.A.wr('OE', self.A._lock << 8)", 'bus, profiles'),
]


def run_mutant(m):
    name, path, old, new, test = m
    tmp = tempfile.mkdtemp(prefix='pmodbench_mutant_')
    try:
        tree = os.path.join(tmp, 'pmodbench')
        shutil.copytree(TOP, tree, ignore=shutil.ignore_patterns('build', '__pycache__', '*.vcd', '*.bit'))
        os.makedirs(os.path.join(tree, 'build'))
        f = os.path.join(tree, path)
        src = open(f).read()
        if src.count(old) != 1:
            return name, False, 'the line to change was found %d times in %s: update test_mutants.py' % (src.count(old), path)
        open(f, 'w').write(src.replace(old, new))
        if test == 'tb':
            vvp = os.path.join(tree, 'build', 'tb.vvp')
            subprocess.check_call([os.path.join(OSS, 'bin', 'iverilog'), '-g2012', '-I', os.path.join(tree, 'sim'), '-o', vvp, '-s', 'tb_pmodbench',
                                   os.path.join(tree, 'sim', 'tb_pmodbench.v')] + [os.path.join(tree, x) for x in RTL])
            out = subprocess.run([os.path.join(OSS, 'bin', 'vvp'), '-n', vvp], cwd=os.path.join(tree, 'build'), capture_output=True, text=True, timeout=1200).stdout
        else:
            out = subprocess.run([sys.executable, os.path.join(tree, 'host', 'test_sim.py'), test], capture_output=True, text=True, timeout=1200)
            out = out.stdout + out.stderr
        fails = [l.strip() for l in out.splitlines() if l.startswith('FAIL:')]
        passed = any(l.startswith('PASS:') for l in out.splitlines())
        if passed or not fails:
            return name, False, 'NOT caught (%s)' % ('the test passed' if passed else 'no verdict: ' + out[-200:].replace('\n', ' | '))
        first = fails[0][6:]
        return name, True, '%d failing check%s, the first: %s' % (len(fails) - 1, '' if len(fails) == 2 else 's', first[:150])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv):
    todo = [m for m in MUTANTS if not argv or argv[0] in m[0]]
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(16, len(todo))) as ex:
        res = list(ex.map(run_mutant, todo))
    caught = 0
    for (name, ok, text), m in zip(res, todo):
        print('%s %s\n        [%s] %s' % ('caught:  ' if ok else 'SURVIVED:', name, 'tb_pmodbench' if m[4] == 'tb' else 'test_sim ' + m[4], text))
        caught += ok
    print('%d mutants, %d caught' % (len(res), caught))
    print('PASS: test_mutants, every planted bug was caught' if caught == len(res) else 'FAIL: test_mutants, %d planted bug(s) survived' % (len(res) - caught))
    return 0 if caught == len(res) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
