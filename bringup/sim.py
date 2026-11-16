"""A simulated bench: the board is each test's own model, the instruments are stand-ins with the real ones' words.

It exists so that every visit of the plan runs end to end before any hardware is connected: the cabling tables, the
autoranging, the fits, the checks, the log and the state.  `faults` breaks things on purpose, to show that a test
can fail:

    dead:p5        the tile gives no output            gain:a2:0.5    its output is half what it should be
    swap:S1,S2     two cables are on each other's jacks  shift:p4:1.2   its response sits 20 % up in frequency
    host:off       the Pmod host's calls do nothing
"""
import numpy as np

import engine
from engine import Lin, Time


class World:
    def __init__(self, faults=(), seed=1):
        self.rng = np.random.default_rng(seed)
        self.visit, self.test = None, None
        self.gens = {}                       # cable -> (shape, freq, vpp, offset, duty) or None
        self.hint = None                     # for a seq read: (key, what, arg)
        self.host_log = []
        self.walk = []                       # the supply currents a power walk will see, in order
        self.base_amps = 0.02
        self.dead, self.gain, self.shift, self.swap, self.host_off = set(), {}, {}, None, False
        for f in faults:
            k, _, rest = f.partition(":")
            a = rest.split(":")
            if k == "dead": self.dead.add(a[0])
            elif k == "gain": self.gain[a[0]] = float(a[1])
            elif k == "shift": self.shift[a[0]] = float(a[1])
            elif k == "swap": self.swap = tuple(rest.split(","))
            elif k == "host": self.host_off = True
            else: raise ValueError("unknown fault %r" % f)

    # -- what is on a cable ---------------------------------------------------------------------------
    def where(self, cable):
        if self.swap and cable in self.swap:
            cable = self.swap[1 - self.swap.index(cable)]
        for c, tile, jack, _ in self.visit.conns:
            if c == cable:
                return tile, jack
        return None

    def role_of(self, cable, table):
        """The role a cable's jack plays in the running test (table: role -> jack or (jack, load))."""
        at = self.where(cable)
        for role, j in table.items():
            jack = j[0] if (isinstance(j, tuple) and j[1] in ("50", "1M")) else j
            if at == engine._tj(self.test.tile, jack):
                return role
        return None

    def expected(self):
        vals = dict(self.test.model["values"]({})) if "values" in self.test.model else {}
        if self.test.tile in self.dead:
            vals = {k: 0.0 for k in vals}
        g = self.gain.get(self.test.tile)
        if g:
            vals = {k: v * g for k, v in vals.items()}
        return vals

    def stims(self):
        out = {}
        for cable, s in self.gens.items():
            if s is None:
                continue
            role = self.role_of(cable, self.test.gens)
            if role:
                out[role] = s
        return out

    def volts(self, cable, t, load):
        """The waveform a scope channel sees."""
        test = self.test
        role = self.role_of(cable, test.scopes) if test else None
        noise = 0.00012 * self.rng.standard_normal(t.shape)
        if role is None or test.tile in self.dead:
            return noise
        if test.kind == "seq":
            return noise + self._hinted(t)
        m = test.model.get(role)
        if m is None:
            return noise
        k = self.shift.get(test.tile)
        if k and isinstance(m, Lin):
            m = Lin(lambda f, ld, m=m, k=k: m.fn(f / k, ld))
        st = self.stims()
        one = dict(test.__dict__); one["model"] = {role: m}; one["scopes"] = {role: (test.scopes[role][0], load)}
        probe = engine.Test(**one)
        y = engine.respond(probe, st, t, {})[role]
        return noise + y * self.gain.get(test.tile, 1.0)

    def _hinted(self, t):
        if not self.hint:
            return 0.0
        key, what, arg = self.hint
        v = self.expected().get(key, 0.0)
        span = t[-1] - t[0]
        if what == "mean": return np.full(t.shape, v)
        if what == "rms": return v * self.rng.standard_normal(t.shape)
        if what == "vpp": return 0.5 * v * np.sin(2 * np.pi * 7.3 / span * t)
        if what == "freq": return 0.5 * np.sign(np.sin(2 * np.pi * v * t + 0.3)) if v else np.zeros(t.shape)
        if what == "tone": return v * np.sin(2 * np.pi * arg * t + 0.7)
        return np.zeros(t.shape)


class SimGen:
    def __init__(self, world, label):
        self.w, self.label = world, label

    def set(self, shape, freq=0.0, vpp=0.0, offset=0.0, duty=50.0):
        self.w.gens[self.label] = (shape, freq, vpp, offset, duty)

    def off(self):
        self.w.gens[self.label] = None


class SimScope:
    """Eight bits over eight divisions, clipping a little beyond the screen, as the real one does."""
    min_scale, max_scale = 0.0005, 10.0

    def __init__(self, world):
        self.w, self.ch = world, {}

    def setup(self, ch, load, scale, offset=0.0, coupling="DC"):
        self.ch[ch] = (str(load), float(scale), float(offset))

    def off(self, ch):
        self.ch.pop(ch, None)

    def capture(self, chs, span):
        n = 5000
        t = np.linspace(0.0, span, n)
        v = {}
        for ch in chs:
            load, scale, offset = self.ch[ch]
            y = self.w.volts("S%d" % ch, t, load) + offset
            lsb = scale * 8.4 / 254.0
            v[ch] = np.clip(np.round(y / lsb) * lsb, -4.2 * scale, 4.2 * scale) - offset
        return t, v


class SimPsu:
    def __init__(self, world):
        self.w, self.on_, self.v, self.limit = world, False, 0.0, 0.1
        self.text = None

    def set(self, volts, amps, out=None): self.v, self.limit = volts, amps
    def on(self): self.on_ = True
    def off(self): self.on_ = False; self.v = 0.0
    def mode(self, out=None): return "CV" if self.on_ else "OFF"
    def say(self, text): self.text = text

    def read(self, out=None):
        if not self.on_:
            return 0.0, 0.0
        if self.w.walk:
            self.w.base_amps = self.w.walk.pop(0)
        amps = self.w.base_amps * min(1.0, self.v / 4.0)
        t = self.w.test
        if t is not None and t.kind == "dc" and "psu" in t.model:
            s = self.w.stims().get("in")
            amps = float(t.model["psu"](s[3] if s else 0.0, {})) * (0.0 if t.tile in self.w.dead else 1.0)
        if t is not None and t.kind == "seq" and self.w.hint and self.w.hint[1] == "psu":
            amps = self.w.expected().get(self.w.hint[0], amps)
        return self.v, amps + 0.0002 * self.w.rng.standard_normal()


class SimSa:
    def __init__(self, world): self.w = world

    def sweep(self, f0, f1, rbw=None, ref=10.0):
        t = self.w.test
        f = np.linspace(f0, f1, 601)
        if t.kind == "seq":
            v = self.w.expected().get(self.w.hint[0], -90.0) if self.w.hint else -90.0
            return f, np.full(f.shape, v) + 0.3 * self.w.rng.standard_normal(f.shape)
        s = engine.predict(t)
        p = np.interp(f, s.f, s.dbm)
        if t.tile in self.w.dead or (self.w.host_off and t.needs_host):
            p = np.full(f.shape, -75.0)
        return f, p + 20 * np.log10(self.w.gain.get(t.tile, 1.0)) + 0.3 * self.w.rng.standard_normal(f.shape)


class SimVna:
    def __init__(self, world): self.w = world

    def sweep(self, f0, f1, n, power, param="S21"):
        t = self.w.test
        f = np.linspace(f0, f1, int(n))
        k = self.w.shift.get(t.tile, 1.0)
        h = t.model["s"].h(f / k, "50") * self.w.gain.get(t.tile, 1.0)
        if t.tile in self.w.dead:
            h = h * 1e-4
        return f, h * 10 ** (0.03 * self.w.rng.standard_normal(f.shape) / 20.0)


class SimHost:
    """Records every call; answers reads from the running test's expected values."""
    def __init__(self, world): self.w = world

    def __getattr__(self, name):
        def call(*args, **kwargs):
            self.w.host_log.append((name, args, kwargs))
            if self.w.host_off:
                return 0
            if name == "ident": return {"id": "sim"}
            if name == "max2871_set" or name == "trf3722_set": return True
            if self.w.hint and self.w.test is not None and self.w.test.kind == "seq":
                return self.w.expected().get(self.w.hint[0], 0)
            return None
        return call
