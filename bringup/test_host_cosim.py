"""pytest bringup/test_host_cosim.py: the plan's own calls on the Pmod host, through the real driver, into the RTL.

For each board, a tile model is plugged into the simulated ECP5 board's Pmod A (gateware/pmodbench's co-simulation:
iverilog runs the bitstream's Verilog, the driver's bytes go in over a pipe) and every host call that tiles.py makes for
that board is made in the plan's order.  It proves that the driver accepts each call under the board's pin profile
(no test tries to drive a line the tile drives), that the simulated FPGA answers, and that the answers a chip model
can give are the ones the plan expects (WHO_AM_I, the encoder's CRC, the synthesizer's lock).  It does not prove the
analog side of anything: no generator, no scope.

Skipped when the oss-cad-suite's iverilog is not installed.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
HOST = os.path.join(HERE, "..", "gateware", "pmodbench", "host")
sys.path.insert(0, HERE); sys.path.insert(0, HOST)
import tiles                    # noqa: E402

try:
    import simlink, pmodbench   # noqa: E402
    HAVE = os.path.exists(os.path.join(simlink.OSS, "bin", "iverilog"))
except Exception:               # pragma: no cover
    HAVE = False

BOARDS = [s for s in tiles.ORDER if tiles.BOARDS[s].get("pmod")]


def host_calls(stem):
    """(test id, method, args, kwargs, is_read) for every call the board's tests make, in the plan's order."""
    out = []
    for t in tiles.TESTS[stem]:
        for key, method, args, kwargs in t.host:
            out.append((t.id, method, args, kwargs, False))
        for st in t.p.get("steps", ()):
            for key, method, args, kwargs in st.get("host", ()):
                out.append((t.id, method, args, kwargs, False))
            for name, w in st.get("read", {}).items():
                if isinstance(w, tuple) and w[0] == "host":
                    out.append((t.id + " / " + name, w[1], w[2:], {}, True))
    return out


@pytest.mark.skipif(not HAVE, reason="no iverilog (oss-cad-suite) for the co-simulation")
@pytest.mark.parametrize("stem", BOARDS)
def test_plan_calls_run_on_the_rtl(stem):
    calls = host_calls(stem)
    assert calls, "%s has a Pmod plug but no test uses the host" % stem
    seen = {}
    with simlink.SimLink() as link:
        pb = pmodbench.PmodBench(transport=link)
        link.plug("A", stem)
        for where, method, args, kwargs, is_read in calls:
            name, _, pick = method.partition(".")
            try:
                r = getattr(pb, name)(*args, **kwargs)
            except Exception as e:
                raise AssertionError("%s: %s%r %r -> %s: %s" % (where, method, args, kwargs, type(e).__name__, e))
            if pick and isinstance(r, dict):
                r = r[pick]
            if is_read:
                seen[where.split(" / ")[1]] = r
            if name == "max2871_set":
                assert r[1] is True, "%s: the MAX2871 model did not lock" % where
        pb.safe()
    if stem == "amod_b":
        assert seen["WHO_AM_I"] == 0x6C and seen["encoder CRC ok"]
    if stem in ("amod_a", "amod_c"):
        assert all(0.0 <= v <= 1.0 for k, v in seen.items() if k.startswith("density"))
