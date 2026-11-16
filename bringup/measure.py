"""How each kind of test is run on a bench (real or simulated): set the generators, range the scope, capture, fit.

run(test, visit, bench) -> (result, raw): result is what engine's checks read (a Sweep, Shot, Spectrum or Values);
raw is a dict of plain lists that goes into the day's data file.
"""
import math
import time

import numpy as np

import engine
from engine import Sweep, Shot, Spectrum, Values, TWO_PI
from bench import round125

CAL = {}          # generator cable -> (frequencies, measured / nominal): the thru calibration, when one was taken


def _chan(cable):
    return int(cable[1:])


def _wait(bench, seconds):
    if not bench.is_sim:
        time.sleep(seconds)


def _cables(test, visit):
    g = {r: visit.cable(*engine._tj(test.tile, j), "G") for r, j in test.gens.items()}
    s = {r: (visit.cable(*engine._tj(test.tile, j), "S"), load) for r, (j, load) in test.scopes.items()}
    return g, s


def _host(bench, calls, vals=None):
    for key, method, args, kwargs in calls:
        r = getattr(bench.host, method)(*args, **kwargs)
        if key and vals is not None:
            vals[key] = r
    return vals


def capture_ranged(bench, chans, span, guess):
    """One capture with each channel's volts/div fitted to what it sees: chans = {role: (channel, load)},
    guess = {role: (expected low, expected high)} volts.  Returns t, {role: volts}, {role: scale}.
    A channel that clips is opened up and one that fills under 1.5 divisions is closed down, up to four times."""
    sc = bench.scope
    scale, offset = {}, {}
    for r, (ch, load) in chans.items():
        lo, hi = guess.get(r, (-0.1, 0.1))
        offset[r] = -0.5 * (lo + hi)
        scale[r] = min(sc.max_scale, max(sc.min_scale, round125(max(hi - lo, 1e-4) / 5.0)))
    for attempt in range(5):
        for r, (ch, load) in chans.items():
            sc.setup(ch, load, scale[r], offset[r])
        t, v = sc.capture([ch for ch, _ in chans.values()], span)
        again = False
        for r, (ch, load) in chans.items():
            y = v[ch]
            top, bot = float(np.max(y)) + offset[r], float(np.min(y)) + offset[r]      # on the screen, in volts from its centre
            if (top > 3.9 * scale[r] or bot < -3.9 * scale[r]) and scale[r] < sc.max_scale:
                scale[r] = min(sc.max_scale, round125(scale[r] * 2.5)); again = True
                if attempt >= 1:
                    offset[r] = -0.5 * (float(np.max(y)) + float(np.min(y)))
            elif (top - bot) < 1.5 * scale[r] and scale[r] > sc.min_scale and attempt < 3:
                new = max(sc.min_scale, round125(max(top - bot, sc.min_scale) / 5.0))
                if new < scale[r]:
                    offset[r] = -0.5 * (float(np.max(y)) + float(np.min(y)))
                    scale[r] = new; again = True
        if not again:
            break
    else:
        # still off the screen after five tries: something is far from what the model expects.  Look once with
        # the widest window, so the log holds the real level and not a clipped one.
        for r, (ch, load) in chans.items():
            scale[r], offset[r] = min(sc.max_scale, 2.0), 0.0
            sc.setup(ch, load, scale[r], 0.0)
        t, v = sc.capture([ch for ch, _ in chans.values()], span)
    return t, {r: v[ch] for r, (ch, _) in chans.items()}, scale


def _amp_at(t, y, f):
    """Peak amplitude of the component at f: a fit over a whole number of cycles."""
    n = int(math.floor((t[-1] - t[0]) * f))
    m = t <= t[0] + n / f if n >= 1 else np.ones(len(t), bool)
    return 2 * abs(np.mean((y[m] - np.mean(y[m])) * np.exp(-1j * TWO_PI * f * t[m])))


def _vref(cable, f, vpp):
    """Peak volts the generator puts into 50 ohm at f: its setting, corrected by the thru calibration if there is one."""
    k = 1.0
    if cable in CAL:
        cf, ck = CAL[cable]
        k = float(np.interp(math.log10(f), np.log10(cf), ck))
    return 0.5 * vpp * k


def run_bode(test, visit, bench):
    g, s = _cables(test, visit)
    gen = bench.gen(g["in"])
    model = engine.predict(test)
    vpp = test.p["vpp"]
    chans = {r: (_chan(c), load) for r, (c, load) in s.items()}
    done = {}

    def point(f):
        gen.set("sine", f, vpp)
        _wait(bench, 0.05)
        guess = {}
        for r in chans:
            a = vpp * 10 ** (model.gain(min(max(f, model.f[0]), model.f[-1]), r) / 20.0) if r in model.h else vpp
            a = max(a, 2e-4)
            guess[r] = (-0.6 * a, 0.6 * a)
        t, v, _ = capture_ranged(bench, chans, 12.0 / f, guess)
        done[f] = {r: _amp_at(t, v[r], f) / _vref(g["in"], f, vpp) for r in chans}

    for f in engine.freqs(test.p["f"]):
        point(float(f))
    first = next(iter(chans))
    for _ in range(int(test.p.get("refine", 0))):
        fs = sorted(done)
        i = int(np.argmax([done[f][first] for f in fs]))
        lo, hi = fs[max(i - 1, 0)], fs[min(i + 1, len(fs) - 1)]
        for f in np.linspace(lo, hi, 21)[1:-1]:
            if float(f) not in done:
                point(float(f))
    gen.off()
    fs = sorted(done)
    res = Sweep(fs, {r: [done[f][r] for f in fs] for r in chans})
    return res, {"f": fs, **{"gain_dB_" + r: list(map(float, res.db(r))) for r in chans}}


def _set_gens(bench, test, visit, stim):
    g, _ = _cables(test, visit)
    for role, s in stim.items():
        bench.gen(g[role]).set(s[0], s[1], s[2], s[3], *(s[4:5]))


def _gens_off(bench, test, visit):
    g, _ = _cables(test, visit)
    for c in g.values():
        bench.gen(c).off()


def _guess(pred, role):
    y = pred.v.get(role)
    if y is None or len(y) == 0:
        return (-0.1, 0.1)
    lo, hi = float(np.min(y)), float(np.max(y))
    pad = 0.15 * (hi - lo) + 2e-3
    return (lo - pad, hi + pad)


def run_shot(test, visit, bench):
    """wave and listen: one capture."""
    _, s = _cables(test, visit)
    stim = test.p.get("stim", {})
    _set_gens(bench, test, visit, stim)
    _wait(bench, 0.3)
    pred = engine.predict(test)
    chans = {r: (_chan(c), load) for r, (c, load) in s.items()}
    t, v, scale = capture_ranged(bench, chans, test.p["span"], {r: _guess(pred, r) for r in chans})
    _gens_off(bench, test, visit)
    res = Shot(t, v, dict(test.p))
    raw = {"dt": float(t[1] - t[0]), "scale": scale}
    for r in v:
        step = max(1, len(v[r]) // 2000)
        raw["v_" + r] = [round(float(x), 5) for x in v[r][::step]]
        raw["step_" + r] = step
    return res, raw


def run_dc(test, visit, bench):
    g, s = _cables(test, visit)
    gen = bench.gen(g["in"])
    pred = engine.predict(test)
    chans = {r: (_chan(c), load) for r, (c, load) in s.items()}
    vals = Values()
    for volts in test.p["volts"]:
        gen.set("dc", offset=volts)
        _wait(bench, 0.4)
        if chans:
            guess = {r: (pred.get("%s@%g" % (r, volts), 0.0) - 0.3, pred.get("%s@%g" % (r, volts), 0.0) + 0.3) for r in chans}
            t, v, _ = capture_ranged(bench, chans, 2e-3, guess)
            for r in chans:
                vals["%s@%g" % (r, volts)] = float(np.mean(v[r]))
        if test.psu:
            vals["psu@%g" % volts] = float(np.mean([bench.psu.read()[1] for _ in range(4)]))
    gen.off()
    engine.finish(test, vals)
    return vals, dict(vals)


def _read(bench, test, visit, key, what, expect):
    """One of a seq step's reads."""
    world = bench.world
    if world is not None:
        if what == "psu":
            world.hint = (key, "psu", None)
        elif what[0] == "scope":
            world.hint = (key, what[2], what[3] if len(what) > 3 else None)
        else:
            world.hint = (key, what[0], None)
    if what == "psu":
        return float(np.mean([bench.psu.read()[1] for _ in range(4)]))
    kind = what[0]
    if kind == "host":                                    # "method" or "method.field" when the method returns a dict
        name, _, pick = what[1].partition(".")
        r = getattr(bench.host, name)(*what[2:])
        if pick and isinstance(r, dict):
            r = r[pick]
        return float(r) if r is not None else float("nan")
    if kind == "sa":
        f, p = bench.sa.sweep(what[1], what[2])
        return float(np.median(p))
    if kind == "scope":
        role, stat = what[1], what[2]
        arg = what[3] if len(what) > 3 else None
        _, s = _cables(test, visit)
        cable, load = s[role]
        e = abs(expect.get(key, 0.1)) if expect else 0.1
        if stat == "mean":
            span, guess = 2e-3, (expect.get(key, 0.0) - 0.3, expect.get(key, 0.0) + 0.3)
        elif stat == "freq":
            span, guess = 30.0 / max(e, 1.0), (-1.0, 1.0)
        elif stat == "tone":
            span, guess = 40.0 / arg, (-1.3 * e - 1e-3, 1.3 * e + 1e-3)
        elif stat == "rms":
            span, guess = 2e-4, (-4 * e - 1e-3, 4 * e + 1e-3)
        else:
            span, guess = 2e-3, (-0.7 * e - 1e-3, 0.7 * e + 1e-3)
        t, v, _ = capture_ranged(bench, {role: (_chan(cable), load)}, span, {role: guess})
        sh = Shot(t, v)
        return float(sh.tone(arg, role)) if stat == "tone" else float(getattr(sh, stat)(role))
    raise ValueError(what)


def run_seq(test, visit, bench):
    g, _ = _cables(test, visit)
    expect = dict(test.model["values"]({}))
    vals = Values()
    mot = bench.cfg["psu"].get("motor_output", 2) if bench.cfg else 2
    try:
        for step in test.p["steps"]:
            if "mot" in step:                                  # the motor supply: the PSU's output 2, 0.5 A at most here
                bench.psu.set(step["mot"], 0.5, out=mot)
            if step.get("host"):
                _host(bench, step["host"], vals)
            for role, s in step.get("gen", {}).items():
                bench.gen(g[role]).set(s[0], s[1], s[2], s[3], *(s[4:5]))
            _wait(bench, step.get("wait", 0.0))
            for key, what in step.get("read", {}).items():
                vals[key] = _read(bench, test, visit, key, what, expect)
    finally:
        for c in g.values():
            bench.gen(c).off()
        if any("mot" in st for st in test.p["steps"]):
            bench.psu.set(0.0, 0.05, out=mot)
        if bench.world is not None:
            bench.world.hint = None
    engine.finish(test, vals)
    return vals, {k: (v if isinstance(v, (int, float, str, bool)) or v is None else repr(v)) for k, v in vals.items()}


def run_s21(test, visit, bench):
    f0, f1, n = test.p["f"]
    f, h = bench.vna.sweep(f0, f1, n, test.p["power"], test.p["param"])
    res = Sweep(f, {"s": h})
    step = max(1, len(f) // 201)
    return res, {"f": [float(x) for x in f[::step]], "dB": [round(float(x), 3) for x in res.db("s")[::step]]}


def run_spec(test, visit, bench):
    _set_gens(bench, test, visit, test.p.get("stim", {}))
    _wait(bench, 0.5)
    f, p = bench.sa.sweep(test.p["f"][0], test.p["f"][1], test.p["rbw"], test.p["ref"])
    _gens_off(bench, test, visit)
    res = Spectrum(f, p)
    step = max(1, len(f) // 301)
    return res, {"f": [float(x) for x in f[::step]], "dBm": [round(float(x), 2) for x in p[::step]]}


RUNNERS = {"bode": run_bode, "wave": run_shot, "listen": run_shot, "dc": run_dc, "seq": run_seq, "s21": run_s21, "spec": run_spec}


def run(test, visit, bench):
    engine.CABLE_PF = bench.cable_pf
    extra = Values()
    if bench.world is not None:
        bench.world.visit, bench.world.test = visit, test
    if test.host:
        _host(bench, test.host, extra)
        _wait(bench, 0.2)
    res, raw = RUNNERS[test.kind](test, visit, bench)
    if extra:
        raw["host"] = {k: (bool(v) if isinstance(v, (bool, np.bool_)) else v) for k, v in extra.items()}
    return res, raw
