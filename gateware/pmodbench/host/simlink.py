#!/usr/bin/env python3
"""A Transport that is the RTL: host/pmodbench.py's bytes go to sim/tb_cosim.v running in iverilog's vvp, over two
named pipes, and the simulated board's replies come back the same way, so the driver runs unchanged, polling loops
and all, on simulated time (wait() and now() are the simulation's clock, not the wall's).  The link also plugs the
tile models into the two sockets, turns their knobs and reads their checkers (tiles.v's report).

    with SimLink() as link:
        pb = PmodBench(transport=link)
        link.plug('A', 'rf_mod')
        ...
        link.query()['A']['max']['locked']
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import pmodbench                                                 # noqa: E402

OSS = os.path.expanduser(os.environ.get('OSS_CAD_SUITE', '~/mudd/133electronics/icepi-zero-dac-adc/tools/oss-cad-suite'))
BUILD = os.path.join(TOP, 'build')
RTL = ['rtl/pmodbench.v', 'rtl/pmod_port.v', 'rtl/capture.v', 'rtl/vendor/uart.v', 'rtl/vendor/regbus.v']
SIM = ['sim/models.v', 'sim/tiles.v']
TILES = dict(none=0, amod_a=1, amod_n=2, amod_c=3, amod_m=4, amod_b=5, rf_mod=6, phmod=7, iq_mod=8, spi_jig=9, loop_jig=10)


def compile_tb(top='tb_cosim', defines=(), out=None, rtl=None):
    """iverilog the design, the models and one testbench into build/<top>.vvp (always: the sources may have changed)."""
    os.makedirs(BUILD, exist_ok=True)
    out = out or os.path.join(BUILD, top + '.vvp')
    cmd = [os.path.join(OSS, 'bin', 'iverilog'), '-g2012', '-I', os.path.join(TOP, 'sim'), '-o', out, '-s', top]
    cmd += ['-D' + d for d in defines]
    cmd += [os.path.join(TOP, 'sim', top + '.v')] + [os.path.join(TOP, f) for f in (rtl or RTL) + SIM]
    subprocess.check_call(cmd)
    return out


class SimLink(pmodbench.Transport):
    settle = 0.0005                                              # what resync() waits: 25 bytes at 1 Mbaud, not a USB round trip

    def __init__(self, vvp=None, read_timeout_note=True):
        self.vvp = vvp or compile_tb()
        self.dir = tempfile.mkdtemp(prefix='pmodbench_cosim_')
        self.cmd_path, self.resp_path = os.path.join(self.dir, 'cmd.fifo'), os.path.join(self.dir, 'resp.fifo')
        os.mkfifo(self.cmd_path); os.mkfifo(self.resp_path)
        self.log = open(os.path.join(BUILD, 'cosim_vvp.log'), 'w')
        self.proc = subprocess.Popen([os.path.join(OSS, 'bin', 'vvp'), '-n', self.vvp, '+cmd=' + self.cmd_path, '+resp=' + self.resp_path],
                                     stdout=self.log, stderr=subprocess.STDOUT, cwd=BUILD)
        self.cmd = open(self.cmd_path, 'w')                      # the testbench opens them in the same order
        self.resp = open(self.resp_path, 'r')
        self.rx = bytearray()                                    # bytes the board has sent that read() has not handed out
        self.seen = 0                                            # bytes the board has sent in all
        self.t_ns = 0.0
        self.bytes_out = 0

    # -- the Transport
    def write(self, data):
        self.cmd.write(''.join('S %02x\n' % x for x in data))
        self.bytes_out += len(data)

    def _until_marker(self):
        self.cmd.flush()
        while True:
            line = self.resp.readline()
            if not line:
                raise IOError('the simulation ended (see build/cosim_vvp.log)')
            f = line.split()
            if f[0] == 'u':
                if f[1] == 'xx':
                    raise IOError('the simulated board sent an undefined byte (X): a register read saw an undriven or contended bit')
                self.rx.append(int(f[1], 16)); self.seen += 1
            elif f[0] == 'r':
                self.t_ns = float(f[2])
                return

    def read(self, n):
        if len(self.rx) < n:
            self.cmd.write('R %d\n' % (self.seen + n - len(self.rx)))
            self._until_marker()
        if len(self.rx) < n:
            raise IOError('board: wanted %d bytes, got %d (simulated; 200 ms passed)' % (n, len(self.rx)))
        d = bytes(self.rx[:n]); del self.rx[:n]
        return d

    def flush(self):
        self.cmd.write('Y\n'); self._until_marker()
        del self.rx[:]

    def wait(self, seconds):
        self.cmd.write('W %d\n' % max(1, int(round(seconds * 1e9))))
        self.t_ns += seconds * 1e9

    def now(self):
        return self.t_ns * 1e-9

    def close(self):
        if self.proc.poll() is None:
            try:
                self.cmd.write('E\n'); self.cmd.flush()
                self.proc.wait(timeout=30)
            except Exception:
                self.proc.kill()
        for f in (self.cmd, self.resp, self.log):
            try: f.close()
            except Exception: pass
        for p in (self.cmd_path, self.resp_path):
            if os.path.exists(p): os.unlink(p)
        if os.path.isdir(self.dir): os.rmdir(self.dir)

    def __enter__(self): return self
    def __exit__(self, *a): self.close()

    # -- the bench around the board
    def plug(self, port, tile):
        """Put a tile model ('rf_mod', 'amod_b', ..., 'spi_jig', 'loop_jig', 'none') into Pmod 'A' or 'B'."""
        self.cmd.write('P %d %d\n' % ('AB'.index(port.upper()), TILES[tile]))

    def knob(self, port, name, value):
        """Set a model's knob (sim/tiles.v set_param): vin, level, cmp, steps, step_ns, glitch, angle, status, clear..."""
        self.cmd.write('V %d %s %r\n' % ('AB'.index(port.upper()), name, float(value)))

    def query(self):
        """Everything the sockets' models and checkers know: {'A': {'max': {...}, 'm3': {...}, ...}, 'B': {...}}."""
        self.cmd.write('Q\n'); self.cmd.flush()
        out = {'A': {}, 'B': {}}
        while True:
            line = self.resp.readline()
            if not line: raise IOError('the simulation ended (see build/cosim_vvp.log)')
            f = line.split()
            if f[0] == 'u':
                self.rx.append(int(f[1], 16)); self.seen += 1
            elif f[0] == 'q':
                if f[1] == 'end': return out
                port, key = f[1].split('.', 1)
                d = {}
                for kv in f[2:]:
                    k, v = kv.split('=')
                    d[k] = float(v) if '.' in v else int(v, 0)
                out[port][key] = d

    def words(self, port, chip):
        """The words a chip model latched, in order ('max' or 'trf')."""
        q = self.query()[port]
        n = q[chip]['n'] if chip == 'max' else q[chip]['writes']
        return [q['%s.w%d' % (chip, i)]['v'] for i in range(n)]
