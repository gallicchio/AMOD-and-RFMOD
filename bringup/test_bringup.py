"""pytest bringup/: the whole plan against the simulated bench, before any instrument is connected.

What this proves: every jack a test names is on its board; every visit fits the bench's channels; a board that does
what its models say passes every check; a board broken on purpose fails the checks that should catch it; and the
command line keeps its record.  What it cannot prove: that the models are right.  The first real board does that.
"""
import os
import subprocess
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import engine, measure, sim, tiles, run          # noqa: E402
from bench import Bench                          # noqa: E402


def stem_letter(stem):
    return tiles.BOARDS[stem]["letter"].upper()


def visits(stem):
    return engine.plan(stem, tiles.BOARDS[stem], tiles.TESTS[stem])


def run_board(stem, faults=()):
    w = sim.World(faults); b = Bench.sim(w); b.psu.set(5, 1); b.psu.on()
    bad = {}
    for v in visits(stem):
        for t in v.tests:
            if t.kind == "manual":
                continue
            res, _ = measure.run(t, v, b)
            fails = [c["name"] for c in engine.judge(t, res) if not c["ok"]]
            if fails:
                bad[t.id] = fails
    return bad


@pytest.mark.parametrize("stem", tiles.ORDER)
def test_every_card_can_be_written(stem):
    """Every jack named in tiles.py exists on the board, and every visit fits two generators and four scope channels."""
    prev = None
    for v in visits(stem):
        text = run.card(stem, v, prev)
        assert v.id in text
        assert sum(1 for c in v.conns if c[0][0] == "G") <= 2 and sum(1 for c in v.conns if c[0][0] == "S" and c[0] != "SA") <= 4
        if any(c[0] == "HOST" for c in v.conns):          # the plug's orientation is checked before the first host visit
            ids = [s[0] for s in run.steps(stem)]
            assert stem_letter(stem) + ".plug" in ids and ids.index(stem_letter(stem) + ".plug") < ids.index(v.id)
        cables = [c[0] for c in v.conns]
        assert len(cables) == len(set(cables)), "a cable is used twice in " + v.id
        prev = v


@pytest.mark.parametrize("stem", tiles.ORDER)
def test_a_good_board_passes(stem):
    assert run_board(stem) == {}


@pytest.mark.parametrize("stem,fault,caught", [
    ("amod_p", "dead:p5", "p5.response"), ("amod_p", "shift:p4:1.2", "p4.response"), ("amod_p", "gain:p1:0.7", "p1.response"),
    ("amod_p", "shift:p8:1.001", "p8.response"), ("amod_p", "dead:p11", "p11.delays"), ("amod_a", "gain:a2:0.5", "a2.response"),
    ("amod_a", "dead:a7", "a7.lock at 100 kHz"), ("amod_a", "swap:S1,S2", "a2.response"), ("amod_a", "host:off", "a6.ones density against IN"),
    ("amod_n", "shift:n4:1.2", "n4.S21 IN to OUT"), ("amod_n", "gain:n8:0.5", "n8.S21 at 0 dB"), ("rf_mod", "gain:r5:0.3", "r5.S21 IN to OUT"),
    ("rf_mod", "host:off", "r10.OUT A+ at 915 MHz"), ("amod_c", "dead:c9", "c9.DC transfer"), ("amod_c", "gain:c12:0.5", "c12.waveform"),
    ("phmod", "gain:h5:0.5", "h5.channel A"), ("iq_mod", "dead:q6", "q6.volts against power at 20 MHz"), ("amod_m", "dead:m2", "m2.VMOT on USB power"),
    ("amod_b", "host:off", "b6.IMU and encoder answer")])
def test_a_broken_board_fails(stem, fault, caught):
    assert caught in run_board(stem, [fault])


def test_ladder_agrees_with_the_designs_own_model():
    """engine.ladder against sim/passive.py's response(), which the silkscreen's numbers came from."""
    P = engine.P
    f = np.logspace(5, 7.4, 200)
    lp = [("p", P.C(220e-12)), ("s", P.L(1.5e-6)), ("p", P.C(680e-12)), ("s", P.L(1.5e-6)), ("p", P.C(220e-12))]
    mine = engine.ladder(lp).h(f, "50")
    theirs = P.response([("shunt" if k == "p" else "series", z) for k, z in lp], f)
    assert np.allclose(mine, theirs, rtol=1e-9)
    s = engine.Sweep(f, {"o": mine})
    assert 8.5e6 < s.corner(-3, "hi", "lf") < 9.3e6          # the tile prints 9 MHz


def test_delay_line_is_400_ns():
    t = [x for x in tiles.TESTS["amod_p"] if x.id == "p11.delays"][0]
    shot = engine.predict(t)
    assert 85e-9 < shot.delay("t100", "t200") < 112e-9 and 85e-9 < shot.delay("t200", "t300") < 112e-9


def test_host_calls_exist_in_the_driver():
    """Every call tiles.py makes on the Pmod host is a method of gateware/pmodbench's driver, with arguments that fit."""
    import inspect
    path = os.path.join(HERE, "..", "gateware", "pmodbench", "host")
    if not os.path.exists(os.path.join(path, "pmodbench.py")):
        pytest.skip("gateware/pmodbench/host/pmodbench.py is not there yet")
    sys.path.insert(0, path)
    import pmodbench
    calls = []
    for stem in tiles.ORDER:
        for t in tiles.TESTS[stem]:
            calls += list(t.host)
            for st in t.p.get("steps", ()):
                calls += list(st.get("host", ()))
                calls += [(None, w[1], w[2:], {}) for w in st.get("read", {}).values() if isinstance(w, tuple) and w[0] == "host"]
    assert calls
    for _, method, args, kwargs in calls:
        method = method.partition(".")[0]
        fn = getattr(pmodbench.PmodBench, method, None) or getattr(pmodbench.Port, method, None)   # the bench passes a port's words on
        assert fn is not None, "the driver has no method %r" % method
        inspect.signature(fn).bind(None, *args, **kwargs)


def test_command_line_keeps_its_record(tmp_path):
    env = dict(os.environ)
    for f in ("state_sim.json", "BRINGUP_LOG_sim.md"):
        if os.path.exists(os.path.join(HERE, f)):
            os.remove(os.path.join(HERE, f))
    r = lambda *a: subprocess.run([sys.executable, os.path.join(HERE, "run.py"), *a, "--sim"], capture_output=True, text=True, env=env)
    assert r("go", "P.v1").returncode == 0
    assert r("power", "amod_a").returncode == 0
    bad = r("go", "P.v2", "--fault", "shift:p4:1.3")
    assert bad.returncode == 1 and "FAIL" in bad.stdout
    part = r("go", "P.hands1", "--only", "DIP 2")
    assert "still to run" in part.stdout
    st = r("status").stdout
    assert "P.v2" in st and "AMOD-P" in st
    log = open(os.path.join(HERE, "BRINGUP_LOG_sim.md")).read()
    assert "p1.response" in log and "switch on a4" in log


def test_motor_supply_is_set_and_returned_to_zero():
    """AMOD-M's driver tests run from the supply's output 2 (REVB 1.5), which must be back at 0 V afterwards."""
    w = sim.World(); b = Bench.sim(w); b.psu.set(5, 1); b.psu.on()
    v = [x for x in visits("amod_m") if any(t.id == "m3.bridge with no motor" for t in x.tests)][0]
    assert any(c[0] == "MOT" for c in v.conns)
    t = [x for x in v.tests if x.id == "m3.bridge with no motor"][0]
    res, _ = measure.run(t, v, b)
    assert all(c["ok"] for c in engine.judge(t, res)) and b.psu.out2 == 0.0


def test_unassigned_instruments_make_a_visit_wait():
    cfg = dict(run.load_config())
    cfg["host"] = {"port": None}
    s = [x for x in run.steps("amod_a") if x[0] == "A.host1"][0]
    assert any("Pmod host" in w for w in run.waiting_for("amod_a", s, cfg))
    s = [x for x in run.steps("amod_p") if x[0] == "P.inspect"][0]
    assert run.waiting_for("amod_p", s, cfg) == []
