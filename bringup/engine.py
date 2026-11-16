"""The bring-up's vocabulary: models, measurements, checks and the packing of tests into visits.

A *test* is one measurement of one tile: which jacks a generator drives, which jacks the scope (or the
network or spectrum analyzer) reads, what the tile should do (its *model*), and the *checks* that compare
the measurement with the model.  `tiles.py` lists the tests of every tile on the nine boards with these
words; `run.py` runs them; `sim.py` plays the bench when no instrument is connected.

Levels.  A generator channel is always set for a 50 ohm load, and every gain is quoted against
**Vref50: the voltage that channel puts into a 50 ohm load** (what a straight cable into a 50 ohm scope
input reads).  So a tile with a 50 ohm input and a gain of 10 reads +20 dB, and a passive tile into a
high-impedance scope input reads up to +6 dB (the generator's open-circuit voltage is 2 x Vref50).

Loads.  '50' is the scope's 50 ohm input; '1M' is its 1 Mohm input with the cable's capacitance across
it (`CABLE_PF`, set from bench.json), which matters for every tile whose output is not 50 ohm.
"""
import math
import os
import sys
from dataclasses import dataclass, field

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))
import passive as P                                                   # noqa: E402  (the design's own ladder models)

CABLE_PF = 75.0            # pF of a 0.5 m coax (50 pF) plus the scope's input (17-25 pF); bench.json overrides
TWO_PI = 2 * math.pi


def zload(f, load):
    """The impedance a scope channel puts on a jack: 50 ohm, or 1 Mohm with the cable across it."""
    f = np.asarray(f, dtype=float)
    if str(load) == "50":
        return np.full(f.shape, 50.0 + 0j)
    return 1.0 / (1e-6 + 1j * TWO_PI * f * CABLE_PF * 1e-12)


# ---------------------------------------------------------------------------------------------------
# Models.  Lin: a linear tile, h(f, load) = V at the jack / Vref50.  Time: anything else.
# ---------------------------------------------------------------------------------------------------
class Lin:
    def __init__(self, fn):
        self.fn = fn

    def h(self, f, load="1M"):
        f = np.atleast_1d(np.asarray(f, dtype=float))
        return np.asarray(self.fn(np.maximum(f, 1e-3), load), dtype=complex)


class Time:
    """fn(t, emf, ctx) -> volts at the jack; emf is the generator's open-circuit waveform (2 x Vref50),
    or None for a test without a generator.  ctx carries the load and the host's state."""
    def __init__(self, fn):
        self.fn = fn


def ladder(elements, rs=50.0, tap=None, tap_r=0.0):
    """A ladder of ('s', Z) and ('p', Z) elements (Z from sim/passive.py's R, L, C, series_arm ...) between
    the generator's 50 ohm and the load.  tap=k reads the node after element k through tap_r instead of
    the output, with the ladder's own output terminated in 50 ohm (p11's taps)."""
    def fn(f, load):
        w = TWO_PI * f
        zl_out = zload(f, "50") if tap is not None else zload(f, load)
        mats = []
        for kind, z in elements:
            zz = z(w)
            one, zero = np.ones_like(zz), np.zeros_like(zz)
            mats.append((one, zz, zero, one) if kind == "s" else (one, zero, 1.0 / zz, one))

        def chain(ms):
            A, B, C, D = (np.ones_like(w, dtype=complex), np.zeros_like(w, dtype=complex),
                          np.zeros_like(w, dtype=complex), np.ones_like(w, dtype=complex))
            for a, b, c, d in ms:
                A, B, C, D = A * a + B * c, A * b + B * d, C * a + D * c, C * b + D * d
            return A, B, C, D
        A, B, C, D = chain(mats)
        h_out = 2.0 * zl_out / (A * zl_out + B + rs * (C * zl_out + D))      # V_out / Vref50
        if tap is None:
            return h_out
        Ar, Br, _, _ = chain(mats[tap:])                                   # from the tapped node to the output
        v_node = h_out * (Ar + Br / zl_out)
        zt = zload(f, load)
        return v_node * zt / (tap_r + zt)
    return Lin(fn)


def amp(gain, f3=None, rin=50.0, rout=49.9, hp=None, order=1):
    """An amplifier tile: input resistance rin at the jack (50: terminated), voltage gain to the op amp's
    output, a low-pass at f3 (order poles), an optional high-pass at hp, rout in series with the jack."""
    def fn(f, load):
        vin = 2.0 * rin / (rin + 50.0)                                     # the jack's voltage / Vref50
        h = np.full(f.shape, gain * vin, dtype=complex)
        if f3:
            h = h / (1 + 1j * f / f3) ** order
        if hp:
            h = h * (1j * f / hp) / (1 + 1j * f / hp)
        zl = zload(f, load)
        return h * zl / (rout + zl)
    return Lin(fn)


def flat(db, rout=50.0):
    """A matched 50 ohm two-port with `db` of gain (an RF tile below its corner), for a 50 ohm load."""
    return Lin(lambda f, load: np.full(f.shape, 10 ** (db / 20.0) + 0j))


def table(points, rout=50.0):
    """A response given as (f, dB) points, joined by straight lines on a log-frequency axis (a datasheet curve)."""
    fs = np.log10([p[0] for p in points]); gs = [p[1] for p in points]
    return Lin(lambda f, load: 10 ** (np.interp(np.log10(f), fs, gs) / 20.0) + 0j)


# ---------------------------------------------------------------------------------------------------
# Results: what a measurement (or its model) gives the checks.
# ---------------------------------------------------------------------------------------------------
class Sweep:
    """Gain against frequency for each output role (a scope sweep, a network analyzer's S21, a model)."""
    def __init__(self, f, h):
        self.f = np.asarray(f, dtype=float)
        self.h = {k: np.asarray(v, dtype=complex) for k, v in h.items()}

    def db(self, role=None):
        role = role or next(iter(self.h))
        return 20 * np.log10(np.maximum(np.abs(self.h[role]), 1e-9))

    def gain(self, f, role=None):
        return float(np.interp(math.log10(f), np.log10(self.f), self.db(role)))

    def peak(self, role=None, lo=None, hi=None):
        g = self.db(role)
        m = np.ones(len(g), bool) if lo is None else (self.f >= lo) & (self.f <= hi)
        i = np.flatnonzero(m)[int(np.argmax(g[m]))]
        return float(self.f[i]), float(g[i])

    def notch(self, role=None, lo=None, hi=None):
        g = self.db(role)
        m = np.ones(len(g), bool) if lo is None else (self.f >= lo) & (self.f <= hi)
        i = np.flatnonzero(m)[int(np.argmin(g[m]))]
        return float(self.f[i]), float(g[i])

    def corner(self, level=-3.0, side="hi", ref="max", role=None):
        """The frequency where the response is `level` dB below its reference: the level at the lowest
        frequency ('lf'), at the highest ('hf') or at the peak ('max'); on the high or the low side."""
        g = self.db(role)
        r = {"lf": g[0], "hf": g[-1], "max": g.max()}[ref]
        i0 = {"lf": 0, "hf": len(g) - 1, "max": int(np.argmax(g))}[ref]
        idx = range(i0, len(g)) if side == "hi" else range(i0, -1, -1)
        prev = i0
        for i in idx:
            if g[i] < r + level:
                if i == prev:
                    return float(self.f[i])
                t = (r + level - g[prev]) / (g[i] - g[prev])
                return float(10 ** (math.log10(self.f[prev]) + t * (math.log10(self.f[i]) - math.log10(self.f[prev]))))
            prev = i
        return float("nan")


class Shot:
    """Waveforms: one capture of several scope channels, by role."""
    def __init__(self, t, v, stim=None):
        self.t = np.asarray(t, dtype=float)
        self.v = {k: np.asarray(x, dtype=float) for k, x in v.items()}
        self.stim = stim or {}

    def _v(self, role):
        return self.v[role or next(iter(self.v))]

    def vmax(self, role=None): return float(np.percentile(self._v(role), 99.5))
    def vmin(self, role=None): return float(np.percentile(self._v(role), 0.5))
    def vpp(self, role=None): return self.vmax(role) - self.vmin(role)
    def mean(self, role=None): return float(np.mean(self._v(role)))
    def rms(self, role=None): return float(np.std(self._v(role)))

    def crossings(self, role=None):
        """Times of the rising mid-level crossings, with hysteresis: an edge counts once the signal has been under
        the lower threshold (30 % of the swing) and passes the upper one (70 %), so noise on a slow edge is one edge."""
        v = self._v(role)
        top, bot = np.percentile(v, 99), np.percentile(v, 1)
        mid, band = 0.5 * (top + bot), 0.2 * (top - bot)
        if top - bot <= 0:
            return np.array([])
        state = np.where(v > mid + band, 1, np.where(v < mid - band, -1, 0))
        idx = np.flatnonzero(state)
        if len(idx) < 2:
            return np.array([])
        st = state[idx]
        ups = np.flatnonzero((st[:-1] < 0) & (st[1:] > 0))
        out = []
        for u in ups:
            i0, i1 = idx[u], idx[u + 1]                    # last sample under the band, first over it
            seg = v[i0:i1 + 1] - mid
            k = int(np.flatnonzero(seg < 0)[-1])
            j = i0 + k
            out.append(self.t[j] - seg[k] * (self.t[j + 1] - self.t[j]) / (v[j + 1] - v[j]))
        return np.array(out)

    def freq(self, role=None):
        x = self.crossings(role)
        return float((len(x) - 1) / (x[-1] - x[0])) if len(x) > 2 else 0.0

    def delay(self, a, b, max_lag=None):
        """Seconds by which role b lags role a: the lag (0 to max_lag, default a quarter of the record) at which the
        two waveforms agree best, by cross-correlation, to a fraction of a sample."""
        x, y = self._v(a) - np.mean(self._v(a)), self._v(b) - np.mean(self._v(b))
        n = len(x); dt = float(self.t[1] - self.t[0])
        c = np.fft.irfft(np.conj(np.fft.rfft(x, 2 * n)) * np.fft.rfft(y, 2 * n))
        m = int(min(n // 4, (max_lag or 1e9) / dt))
        if m < 3:
            return float("nan")
        i = int(np.argmax(c[:m]))
        if 0 < i < m - 1:
            d = c[i - 1] - 2 * c[i] + c[i + 1]
            i = i + (0.5 * (c[i - 1] - c[i + 1]) / d if d else 0.0)
        return float(i * dt)

    def duty(self, role=None):
        v = self._v(role); mid = 0.5 * (np.percentile(v, 99) + np.percentile(v, 1))
        return float(np.mean(v > mid))

    def tone(self, f, role=None):
        """Peak amplitude of the component at f (a fit over a whole number of its cycles)."""
        v = self._v(role); t = self.t
        n = int(math.floor((t[-1] - t[0]) * f))
        if n < 1:
            return 0.0
        m = t <= t[0] + n / f
        return float(2 * abs(np.mean((v[m] - v[m].mean()) * np.exp(-1j * TWO_PI * f * t[m]))))


class Spectrum:
    def __init__(self, f, dbm):
        self.f = np.asarray(f, dtype=float); self.dbm = np.asarray(dbm, dtype=float)

    def peak(self, lo=None, hi=None):
        m = np.ones(len(self.f), bool) if lo is None else (self.f >= lo) & (self.f <= hi)
        i = np.flatnonzero(m)[int(np.argmax(self.dbm[m]))]
        return float(self.f[i]), float(self.dbm[i])

    def floor(self, lo, hi):
        m = (self.f >= lo) & (self.f <= hi)
        return float(np.median(self.dbm[m]))


class Values(dict):
    """Plain numbers by name (a supply current, a ones-density, a register read back)."""


# ---------------------------------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------------------------------
class Check:
    """One pass/fail number.  Either absolute (lo, hi), or against the model: within +-tol (same unit) or
    within +-frac (a fraction) of what the same function gives on the model's result."""
    def __init__(self, name, fn, unit="", lo=None, hi=None, tol=None, frac=None, fmt="%.3g"):
        self.name, self.fn, self.unit, self.lo, self.hi, self.tol, self.frac, self.fmt = name, fn, unit, lo, hi, tol, frac, fmt

    def run(self, meas, model=None):
        try:
            v = float(self.fn(meas))
        except Exception as e:                                             # a measurement with no edges, no peak...
            return dict(name=self.name, value=None, lo=self.lo, hi=self.hi, unit=self.unit, ok=False, why=repr(e))
        lo, hi, exp = self.lo, self.hi, None
        if self.tol is not None or self.frac is not None:
            exp = float(self.fn(model))
            d = self.tol if self.tol is not None else abs(exp) * self.frac
            lo, hi = exp - d, exp + d
        ok = (not math.isnan(v)) and (lo is None or v >= lo) and (hi is None or v <= hi)
        return dict(name=self.name, value=v, expected=exp, lo=lo, hi=hi, unit=self.unit, ok=bool(ok))


def _hz(f):
    for div, u in ((1e9, "GHz"), (1e6, "MHz"), (1e3, "kHz")):
        if f >= div:
            return "%g %s" % (f / div, u)
    return "%g Hz" % f


def G(f, tol=1.0, role=None):
    return Check("gain at %s%s" % (_hz(f), " (%s)" % role if role else ""), lambda r: r.gain(f, role), "dB", tol=tol)


def Gabs(f, lo, hi, role=None):
    return Check("gain at %s%s" % (_hz(f), " (%s)" % role if role else ""), lambda r: r.gain(f, role), "dB", lo=lo, hi=hi)


def Corner(frac=0.15, level=-3.0, side="hi", ref="lf", role=None):
    return Check("%+g dB corner (%s side)" % (level, "high" if side == "hi" else "low"),
                 lambda r: r.corner(level, side, ref, role), "Hz", frac=frac)


def PeakF(frac=0.05, role=None, lo=None, hi=None):
    return Check("peak frequency", lambda r: r.peak(role, lo, hi)[0], "Hz", frac=frac, fmt="%.6g")


def PeakFabs(lo, hi, role=None):
    return Check("peak frequency", lambda r: r.peak(role)[0], "Hz", lo=lo, hi=hi, fmt="%.7g")


def PeakG(tol=2.0, role=None, lo=None, hi=None):
    return Check("peak gain", lambda r: r.peak(role, lo, hi)[1], "dB", tol=tol)


def NotchF(frac=0.05, role=None, lo=None, hi=None):
    return Check("notch frequency", lambda r: r.notch(role, lo, hi)[0], "Hz", frac=frac, fmt="%.6g")


def W(what, lo, hi, role=None, unit="V", arg=None):
    """A waveform number within absolute bounds: what = vmax, vmin, vpp, mean, rms, freq, duty, or tone (arg = Hz)."""
    def fn(r):
        m = getattr(r, what)
        return m(arg, role) if what == "tone" else m(role)
    label = what + (" at %s" % _hz(arg) if what == "tone" else "") + (" (%s)" % role if role else "")
    return Check(label, fn, {"freq": "Hz", "duty": ""}.get(what, unit), lo=lo, hi=hi, fmt="%.5g")


def Wm(what, role=None, tol=None, frac=None, unit="V", arg=None):
    """The same number against the model."""
    c = W(what, None, None, role, unit, arg)
    c.tol, c.frac = tol, frac
    return c


def Delay(a, b, tol=15e-9):
    return Check("delay %s to %s" % (a, b), lambda r: r.delay(a, b), "s", tol=tol)


def Num(key, lo=None, hi=None, unit="", tol=None, frac=None):
    return Check(key, lambda r: r[key], unit, lo=lo, hi=hi, tol=tol, frac=frac)


def SpecPeak(f, df, lo, hi):
    return Check("level near %s" % _hz(f), lambda r: r.peak(f - df, f + df)[1], "dBm", lo=lo, hi=hi)


def SpecPeakF(f, df, tol):
    return Check("frequency near %s" % _hz(f), lambda r: r.peak(f - df, f + df)[0], "Hz", lo=f - tol, hi=f + tol, fmt="%.9g")


# ---------------------------------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------------------------------
@dataclass
class Test:
    tile: str
    name: str
    kind: str                      # bode | wave | listen | dc | seq | s21 | spec | manual
    gens: dict = field(default_factory=dict)       # role -> jack on the tile (or (tile, jack) for another tile's)
    scopes: dict = field(default_factory=dict)     # role -> (jack, load)
    ports: dict = field(default_factory=dict)      # analyzer: 'P1', 'P2' (network) or 'SA' (spectrum) -> jack
    p: dict = field(default_factory=dict)          # parameters of the measurement
    model: dict = field(default_factory=dict)      # role -> Lin | Time; 'sa': ctx -> (tones, floor); 'values': ctx -> dict
    checks: list = field(default_factory=list)
    pre: tuple = ()                # what must be set on the board before it (a DIP way, a jumper, a terminator, a cable)
    hands: bool = False            # Jason has to be there while it runs
    host: tuple = ()               # calls on the Pmod host before the measurement: (key, method, args, kwargs)
    kit: tuple = ()                # parts from outside the board (a motor, a speaker, an HB100)
    psu: bool = False              # the test reads the supply's current
    why: str = ""                  # one line: what the number comes from
    predict: str = ""              # a fault already predicted on paper (REVB.md row and what to do), shown on the card
    mot: str = ""                  # where the supply's output 2 goes for this test (the motor supply), if it is used

    @property
    def needs_host(self):
        return bool(self.host) or any(s.get("host") for s in self.p.get("steps", ()))

    @property
    def stage(self):
        if self.kit: return "kit"
        if self.hands or self.kind == "manual": return "hands"
        if self.kind == "s21": return "rf"
        if self.kind == "spec" or "SA" in self.ports: return "sa"
        if self.needs_host: return "host"
        return "lf"

    @property
    def id(self):
        return "%s.%s" % (self.tile, self.name)


def _outs(outs, load, model):
    if outs is None:
        return {}, (model if isinstance(model, dict) else {})
    if isinstance(outs, str):
        outs = [outs]
    scopes = {o: (o, load) for o in outs} if not isinstance(outs, dict) else outs
    if not isinstance(model, dict):
        model = {next(iter(scopes)): model}
    return scopes, model


def bode(tile, src, outs, f, vpp, model, checks, load="1M", name="response", refine=0, **kw):
    """Step a sine from f[0] to f[1] in f[2] log steps (or through a list) on `src`; read each output's amplitude.
    refine=n: n more passes of 21 points round the peak (a crystal's resonance is narrower than any first grid)."""
    scopes, model = _outs(outs, load, model)
    return Test(tile, name, "bode", gens={"in": src}, scopes=scopes, p=dict(f=f, vpp=vpp, refine=refine), model=model,
                checks=checks, **kw)


def wave(tile, src, shape, freq, vpp, outs, model, checks, load="1M", name="waveform", offset=0.0, cycles=6, span=None,
         duty=50.0, stim=None, **kw):
    """One capture with `shape` ('sine', 'square', 'ramp') at freq on `src`; vpp and offset are into 50 ohm.
    For two generators: src = {role: jack} and stim = {role: (shape, freq, vpp, offset)}."""
    scopes, model = _outs(outs, load, model)
    gens = {"in": src} if isinstance(src, str) else dict(src)
    if stim is None:
        stim = {"in": (shape, freq, vpp, offset, duty)}
    if span is None:
        span = cycles / min(s[1] for s in stim.values() if s[1])
    return Test(tile, name, "wave", gens=gens, scopes=scopes, p=dict(stim=stim, span=span), model=model, checks=checks, **kw)


def listen(tile, outs, model, checks, load="1M", name="output at rest", span=2e-3, **kw):
    """No generator: capture `span` seconds of each output."""
    scopes, model = _outs(outs, load, model)
    return Test(tile, name, "listen", scopes=scopes, p=dict(span=span), model=model, checks=checks, **kw)


def dc(tile, src, volts, outs, model, checks, load="1M", name="DC transfer", derive=None, **kw):
    """Put each of `volts` on `src` (the value into 50 ohm: an unterminated jack sees twice that) and read each
    output's mean, and the supply's current when psu=True.  The numbers are named '<role>@<volts>' and 'psu@<volts>';
    derive(values) -> dict adds numbers worked out from them."""
    scopes, model = _outs(outs, load, model)
    return Test(tile, name, "dc", gens={"in": src}, scopes=scopes, p=dict(volts=list(volts), derive=derive), model=model,
                checks=checks, **kw)


def seq(tile, name, steps, model, checks, gens=None, scopes=None, ports=None, derive=None, **kw):
    """A list of steps, each a dict of: host=[calls], gen={role: (shape, freq, vpp, offset)}, wait=seconds,
    read={name: 'psu' | ('scope', role, what[, arg]) | ('host', method, args...) | ('sa', f_lo, f_hi)}.
    model(ctx) -> the numbers the reads should give; derive(values) -> dict of numbers worked out from them."""
    return Test(tile, name, "seq", gens=gens or {}, scopes=scopes or {}, ports=ports or {}, p=dict(steps=steps, derive=derive),
                model={"values": model}, checks=checks, **kw)


def s21(tile, a, b, f, model, checks, power=-10.0, name=None, param="S21", **kw):
    """Network analyzer: port 1 on jack a and port 2 on jack b; f = (start, stop, points), linear.  param='S11' reads
    jack a's reflection with port 1 alone."""
    ports = {"P1": a} if b is None else {"P1": a, "P2": b}
    return Test(tile, name or "%s %s to %s" % (param, a, b), "s21", ports=ports, p=dict(f=f, power=power, param=param),
                model={"s": model}, checks=checks, **kw)


def spec(tile, port, f, model, checks, name="spectrum", rbw=None, ref=10.0, gens=None, stim=None, **kw):
    """Spectrum analyzer on `port` from f[0] to f[1]; model(ctx) -> ([(Hz, dBm), ...], floor in dBm)."""
    return Test(tile, name, "spec", ports={"SA": port}, gens=gens or {}, p=dict(f=f, rbw=rbw, ref=ref, stim=stim or {}),
                model={"sa": model}, checks=checks, **kw)


def manual(tile, name, text, **kw):
    """Something only a person can see or do; `text` says what happens, the answer goes into the log."""
    return Test(tile, name, "manual", p=dict(text=text), hands=True, **kw)


# ---------------------------------------------------------------------------------------------------
# Predicting: the model's own result, in the same form the measurement has
# ---------------------------------------------------------------------------------------------------
def freqs(spec_):
    if isinstance(spec_, (list, np.ndarray)):
        return np.asarray(spec_, dtype=float)
    f0, f1, n = spec_
    return np.logspace(math.log10(f0), math.log10(f1), int(n))


def stimulus(shape, freq, vpp50, offset50, t, duty=50.0, harmonics=300):
    """The generator's open-circuit waveform (twice its into-50-ohm setting) and its Fourier components
    [(Hz, peak amplitude)], so a linear model can be applied to it exactly."""
    a = vpp50                       # open-circuit peak amplitude = 2 x (vpp50 / 2)
    comps = [(0.0, 2.0 * offset50)]
    if shape == "sine":
        comps.append((freq, a))
    elif shape == "square":
        d = duty / 100.0
        comps[0] = (0.0, 2.0 * offset50 + a * (2 * d - 1))
        for k in range(1, harmonics):
            c = a * 4 / (math.pi * k) * math.sin(math.pi * k * d)
            if abs(c) > 1e-9 * a:
                comps.append((k * freq, c))
    elif shape == "ramp":           # a triangle
        for i, k in enumerate(range(1, harmonics, 2)):
            comps.append((k * freq, a * 8 / (math.pi ** 2 * k * k) * (-1) ** i))
    elif shape != "dc":
        raise ValueError(shape)
    return _synth(comps, None, t, None), comps


def _synth(comps, model, t, load):
    """Sum the components (through a linear model, if one is given).  The square's are cosines about the middle of
    its high half; the others are sines."""
    fs = np.array([f for f, _ in comps], dtype=float); cs = np.array([c for _, c in comps], dtype=complex)
    if model is not None:
        cs = cs * model.h(fs, load) / 2.0                   # the components are open-circuit volts: Vref50 is half
    y = np.zeros(np.shape(t))
    for f, c in zip(fs, cs):
        y = y + (c * np.exp(1j * (TWO_PI * f * t - (0.5 * math.pi if f > 0 else 0.0)))).real
    return y


def respond(test, stim, t, ctx=None):
    """Volts at each of a test's scope jacks, by role, for generators doing `stim` = {role: (shape, freq, vpp,
    offset[, duty])}: the models' answer.  The simulated scope and predict() both come here."""
    ctx = dict(ctx or {})
    emfs, comps = {}, {}
    for role, s in stim.items():
        emfs[role], comps[role] = stimulus(s[0], s[1], s[2], s[3], t, *(s[4:5]))
    emf = next(iter(emfs.values())) if len(emfs) == 1 else (emfs or None)
    v = {}
    for r, (_, load) in test.scopes.items():
        m = test.model.get(r)
        if m is None:
            continue
        if isinstance(m, Time):
            v[r] = np.asarray(m.fn(t, emf, dict(ctx, load=load, test=test, role=r)), dtype=float) * np.ones(np.shape(t))
        elif comps:
            v[r] = _synth(next(iter(comps.values())), m, t, load)
        else:
            v[r] = np.zeros(np.shape(t))
    return v


def predict(test, ctx=None, t=None):
    """What the model says the measurement will give (a Sweep, Shot, Spectrum or Values)."""
    ctx = dict(ctx or {})
    k = test.kind
    if k == "bode":
        f = freqs(test.p["f"])
        return Sweep(f, {r: test.model[r].h(f, load) for r, (_, load) in test.scopes.items() if r in test.model})
    if k == "s21":
        f0, f1, n = test.p["f"]
        f = np.linspace(f0, f1, int(n))
        return Sweep(f, {"s": test.model["s"].h(f, "50")})
    if k in ("wave", "listen"):
        if t is None:
            t = np.linspace(0, test.p["span"], 6000)
        return Shot(t, respond(test, test.p.get("stim", {}), t, ctx), dict(test.p))
    if k == "dc":
        out = Values()
        for volts in test.p["volts"]:
            for r, (_, load) in test.scopes.items():
                m = test.model.get(r)
                if m is None:
                    continue
                if isinstance(m, Time):
                    out["%s@%g" % (r, volts)] = float(np.mean(m.fn(np.zeros(4), np.full(4, 2.0 * volts), dict(ctx, load=load, test=test, role=r))))
                else:
                    out["%s@%g" % (r, volts)] = float((m.h([1e-3], load)[0] * volts).real)
            if "psu" in test.model:
                out["psu@%g" % volts] = float(test.model["psu"](volts, ctx))
        return finish(test, out)
    if k == "spec":
        tones, floor = test.model["sa"](ctx)
        f = np.linspace(test.p["f"][0], test.p["f"][1], 601)
        rbw = test.p["rbw"] or (f[-1] - f[0]) / 100
        p = np.full(f.shape, 10 ** (floor / 10.0))
        for ft, dbm in tones:
            p += 10 ** (dbm / 10.0) * np.exp(-0.5 * ((f - ft) / (0.6 * max(rbw, f[1] - f[0]))) ** 2)
        return Spectrum(f, 10 * np.log10(p))
    if k == "seq":
        return finish(test, Values(test.model["values"](ctx)))
    return None


def finish(test, vals):
    """Add the numbers a test derives from the ones it read."""
    d = test.p.get("derive")
    if d:
        try:
            vals.update(d(vals))
        except (KeyError, ZeroDivisionError, ValueError) as e:
            vals["derive failed"] = repr(e)
    return vals


def judge(test, meas, ctx=None):
    model = predict(test, ctx) if test.kind != "manual" else None
    return [c.run(meas, model) for c in test.checks]


# ---------------------------------------------------------------------------------------------------
# Visits: which cable goes where
# ---------------------------------------------------------------------------------------------------
STAGES = ["lf", "host", "hands", "rf", "sa", "kit"]
STAGE_WORDS = {"lf": "generator and scope", "host": "on the Pmod host", "hands": "with you at the bench",
               "rf": "network analyzer", "sa": "spectrum analyzer", "kit": "with parts from the kit"}
TAGS = {"lf": "v", "host": "host", "rf": "rf", "sa": "sa", "hands": "hands", "kit": "kit"}


@dataclass
class Visit:
    id: str
    stage: str
    tests: list
    conns: list = field(default_factory=list)     # (cable, tile, jack, note)
    pre: list = field(default_factory=list)       # (tile, text)
    hands: bool = False

    def cable(self, tile, jack, kinds):
        for c, t, j, _ in self.conns:
            if t == tile and j == jack and c[0] in kinds:
                return c
        raise KeyError((tile, jack, kinds))


def _tj(tile, jack):
    return jack if isinstance(jack, tuple) else (tile, jack)


def _need(tile, tests):
    """The jacks a group of tests wants on generators, scope channels and analyzer ports (unions, in order)."""
    g, s, a = [], [], []
    for t in tests:
        for j in t.gens.values():
            if _tj(tile, j) not in g: g.append(_tj(tile, j))
        for j, load in t.scopes.values():
            if _tj(tile, j) not in [x[0] for x in s]: s.append((_tj(tile, j), load))
        for port, j in t.ports.items():
            if (port, _tj(tile, j)) not in a: a.append((port, _tj(tile, j)))
    return g, s, a


def pack(letter, tests, stage, ngen=2, nscope=4):
    """Group one stage's tests into visits.  Generator-and-scope stages: as many tiles per visit as the bench has
    channels, in tile order.  Analyzer stages: a visit for each different set of jacks and cables.  Hands and kit:
    a sitting per tile."""
    by_tile = {}
    for t in tests:
        if t.stage == stage:
            by_tile.setdefault(t.tile, []).append(t)
    visits, cur, ng, ns = [], [], 0, 0

    def close():
        nonlocal cur, ng, ns
        if not cur:
            return
        v = Visit("%s.%s%d" % (letter.upper(), TAGS[stage], len(visits) + 1), stage, [t for _, ts in cur for t in ts])
        gi = si = 0
        for tile, ts in cur:
            g, s, a = _need(tile, ts)
            for tl, j in g:
                gi += 1; v.conns.append(("G%d" % gi, tl, j, "generator"))
            for (tl, j), load in s:
                si += 1; v.conns.append(("S%d" % si, tl, j, "scope, 50 ohm input" if load == "50" else "scope, 1 Mohm input"))
            for port, (tl, j) in a:
                v.conns.append((port, tl, j, "spectrum analyzer" if port == "SA" else "network analyzer port %s" % port[1]))
            for t in ts:
                for x in t.pre:
                    if (t.tile, x) not in v.pre: v.pre.append((t.tile, x))
        v.hands = stage in ("hands", "kit")
        for t in v.tests:
            if t.mot and not any(c[0] == "MOT" for c in v.conns):
                v.conns.append(("MOT", t.tile, t.mot, "supply output 2"))
        if any(t.needs_host for t in v.tests):
            v.conns.append(("HOST", "", "Pmod plug", "into the ECP5 board's Pmod A socket"))
        if gi > ngen or si > nscope:
            raise ValueError("%s needs %d generators and %d scope channels" % (v.id, gi, si))
        visits.append(v)
        cur, ng, ns = [], 0, 0

    for tile, ts in by_tile.items():
        if stage in ("rf", "sa"):
            groups = {}
            for t in ts:
                key = (tuple(sorted((k, str(j)) for k, j in t.ports.items())), tuple(sorted((k, str(j)) for k, j in t.gens.items())), t.pre)
                groups.setdefault(key, []).append(t)
            for grp in groups.values():
                cur = [(tile, grp)]; close()
            continue
        if stage in ("hands", "kit"):
            cur = [(tile, ts)]; close()
            continue
        g, s, _ = _need(tile, ts)
        if ng + len(g) > ngen or ns + len(s) > nscope:
            close()
        cur.append((tile, ts)); ng += len(g); ns += len(s)
    close()
    return visits


def needs(visit, board=None):
    """The instruments a visit uses: generators, scope, psu, vna, sa, host."""
    out = set()
    for c, *_ in visit.conns:
        out.add({"G": "generators", "S": "scope", "P": "vna", "M": "psu", "H": "host"}.get(c[0], "sa") if c != "SA" else "sa")
    if (board or {}).get("power") or any(t.psu for t in visit.tests):
        out.add("psu")
    return out


def plan(stem, board, tests, ngen=2, nscope=4):
    """Every visit of one board, in the order they are done."""
    out = []
    for st in STAGES:
        out += pack(board["letter"], tests, st, ngen, nscope)
    return out
