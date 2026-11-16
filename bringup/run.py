#!/usr/bin/env python3
"""The bring-up, one step per call.  Jason cables; this measures, judges, logs, and says what comes next.

    run.py status                     where every board stands, and exactly what to do next
    run.py board amod_a               which board is on the bench now
    run.py card A.v2                  one visit's cabling card (also bringup/cards/A.v2.png)
    run.py go A.v2                    run that visit's tests (add --sim to rehearse on the simulated bench)
    run.py done A.inspect "note"      record a step that only a person does (also: skip, fail)
    run.py power amod_a               the power stage: staircase, rails, the switch walk
    run.py cal                        thru calibration: G1 into S1 and G2 into S2, straight
    run.py bench                      which instruments are assigned, and whether they answer
    run.py note "text"                a line in the log;   run.py revb "text": a line in REVB.md's inbox
    run.py off                        generators off, the host's pins released, the supply off
    run.py plan                       rewrite VISITS.md, STATUS.md and the cards' pictures from tiles.py

--sim uses the simulated bench and its own state and log (state_sim.json, data_sim/), so a rehearsal never
touches the real record.  --fault dead:p5 (see sim.py) breaks the simulated board on purpose.
"""
import argparse
import datetime
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import engine                                                            # noqa: E402
import tiles                                                             # noqa: E402
import measure                                                           # noqa: E402
from bench import Bench, NotAssigned, load_config                        # noqa: E402

GRID0, PITCH = 7.75, 21.5              # mm: the first cell's corner and the cell pitch (scripts/geometry.py)
CABLES = {"G": "generator CH%s (BNC to SMA)", "S": "scope CH%s (SMA to BNC)", "P": "network analyzer port %s", "SA": "spectrum analyzer input"}


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


class Book:
    """The state, the log and the data files (the real ones, or the rehearsal's)."""
    def __init__(self, sim=False):
        self.sim = sim
        self.state_path = os.path.join(HERE, "state_sim.json" if sim else "state.json")
        self.data_dir = os.path.join(HERE, "data_sim" if sim else "data")
        self.log_path = os.path.join(HERE, "BRINGUP_LOG_sim.md" if sim else "BRINGUP_LOG.md")
        self.state = {"active": None, "cabled": None, "steps": {}, "units": {}}
        if os.path.exists(self.state_path):
            with open(self.state_path) as f:
                self.state.update(json.load(f))

    def save(self):
        with open(self.state_path, "w") as f:
            json.dump(self.state, f, indent=1)
        if not self.sim:
            with open(os.path.join(HERE, "STATUS.md"), "w") as f:
                f.write(status_text(self, markdown=True))

    def log(self, board, step, what, result, numbers=""):
        new = not os.path.exists(self.log_path)
        with open(self.log_path, "a") as f:
            if new:
                f.write("# Bring-up log\n\nOne row per result, as `run.py` wrote it; the raw numbers are in `data/<board>/` (not in git).\n\n"
                        "| when | board | step | test | result | numbers |\n|---|---|---|---|---|---|\n")
            f.write("| %s | %s | %s | %s | %s | %s |\n" % (now(), board, step, what, result, numbers.replace("|", "/")))

    def data(self, stem, name, obj):
        d = os.path.join(self.data_dir, stem)
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, "%s_%s.json" % (datetime.datetime.now().strftime("%Y%m%d_%H%M%S"), name.replace(" ", "_").replace("/", "-")))
        with open(path, "w") as f:
            json.dump(obj, f)
        return path

    def mark(self, step, status, note=""):
        self.state["steps"][step] = {"status": status, "when": now(), "note": note}


# ---------------------------------------------------------------------------------------------------
# The boards' geometry and the plan
# ---------------------------------------------------------------------------------------------------
_GEO = {}


def geo(stem):
    if stem not in _GEO:
        with open(os.path.join(ROOT, "out", stem + "_tiles.json")) as f:
            d = json.load(f)
        _GEO[stem] = {t["id"]: t for t in d["tiles"]}
    return _GEO[stem]


def jack_info(stem, tile, jack):
    """Where a jack is and what the board prints beside it."""
    t = geo(stem)[tile]
    for j in t["jacks"]:
        if j["label"] == jack:
            ax, ay = t["x0"] + j["x"], t["y0"] + j["y"]
            col, row = int((ax - GRID0) // PITCH) + 1, int((ay - GRID0) // PITCH) + 1
            cx, cy = (ax - GRID0) % PITCH, (ay - GRID0) % PITCH
            corner = ("top" if cy < 10 else "bottom") + "-" + ("left" if cx < 10 else "right")
            silk = j.get("silk") or j["label"]
            twice = sum(1 for k in t["jacks"] if (k.get("silk") or k["label"]) == silk) > 1
            return dict(x=ax, y=ay, row=row, col=col, corner=corner, silk=silk, title=t["name"],
                        name=silk if not twice else "%s (the %s one)" % (silk, corner))
    raise KeyError("%s has no jack %r (it has %s)" % (tile, jack, [j["label"] for j in t["jacks"]]))


def steps(stem):
    """Every step of a board, in order: (id, kind, title, visit or None)."""
    b = tiles.BOARDS[stem]
    L = b["letter"].upper()
    out = [(L + ".inspect", "inspect", "look it over, unpowered", None), (L + ".setup", "setup", "set the switches and jumpers", None)]
    if b.get("power"):
        out.append((L + ".power", "power", "first power: staircase, rails, the switch walk", None))
    cfg = load_config()
    for v in engine.plan(stem, b, tiles.TESTS[stem], ngen=len(cfg["generators"])):
        out.append((v.id, v.stage, engine.STAGE_WORDS[v.stage], v))
    return out


def find(step_id):
    for stem in tiles.ORDER:
        for s in steps(stem):
            if s[0].lower() == step_id.lower():
                return stem, s
    raise SystemExit("no step %r; `run.py status` lists them" % step_id)


def cable_name(c):
    if c == "HOST": return "the ECP5 board's Pmod A socket"
    if c == "SA": return CABLES["SA"]
    return CABLES[c[0]] % c[1:]


def conn_line(stem, c, tile, jack, note):
    if c == "HOST":
        return "%-5s the board's Pmod plug (bottom edge) straight into the ECP5-2ADC-2DAC board's **Pmod A** socket; USB PROG to this PC" % c
    j = jack_info(stem, tile, jack)
    load = " -- %s" % note.split(", ")[1] if note.startswith("scope, ") else ""
    return "%-5s %-28s  ->  tile %s \"%s\", jack printed \"%s\": row %d, column %d, the cell's %s%s" % (
        c, cable_name(c), tile, j["title"], j["silk"], j["row"], j["col"], j["corner"], load)


def _num(x, unit, bare=False):
    if unit == "Hz":
        return engine._hz(float("%.4g" % x))
    return "%.4g" % x if (bare or not unit) else "%.4g %s" % (x, unit)


def check_text(c, model=None):
    """One check in words, with the model's own number where the check is against the model."""
    lo, hi = c.lo, c.hi
    if c.tol is not None or c.frac is not None:
        try:
            e = float(c.fn(model))
            d = c.tol if c.tol is not None else abs(e) * c.frac
            return "%s: %s (%s to %s)" % (c.name, _num(e, c.unit), _num(e - d, c.unit, True), _num(e + d, c.unit))
        except Exception:
            return "%s: the model's value +-%s" % (c.name, ("%g %s" % (c.tol, c.unit)) if c.tol is not None else "%g %%" % (100 * c.frac))
    if lo is not None and hi is not None: return "%s: %s to %s" % (c.name, _num(lo, c.unit, True), _num(hi, c.unit))
    if hi is not None: return "%s: under %s" % (c.name, _num(hi, c.unit))
    return "%s: over %s" % (c.name, _num(lo, c.unit))


def card(stem, v, prev=None, short=False):
    b = tiles.BOARDS[stem]
    tl = sorted({t.tile for t in v.tests}, key=lambda x: int(x[1:]))
    lines = ["== %s ==  %s (%s), %s; tiles %s" % (v.id, b["name"], b["title"], engine.STAGE_WORDS[v.stage], ", ".join(tl))]
    if prev is not None and prev.conns and v.stage == prev.stage:
        old = {c: (t, j) for c, t, j, _ in prev.conns}
        new = {c: (t, j) for c, t, j, _ in v.conns}
        moves = [c for c in new if old.get(c) != new[c]]
        gone = [c for c in old if c not in new]
        lines.append("Cables to move: %s%s" % (", ".join(moves) if moves else "none", ("; take off: " + ", ".join(gone)) if gone else ""))
    if v.pre and not v.hands:
        lines.append("First, on the board:")
        lines += ["   * " + x for _, x in v.pre]
    if v.conns:
        lines.append("Hookup (every cable of this visit):")
        lines += ["   " + conn_line(stem, *c) for c in v.conns]
    if short:
        return "\n".join(lines)
    kits = [k for t in v.tests for k in t.kit]
    if kits:
        lines.append("From the kit: " + "; ".join(dict.fromkeys(kits)))
    lines.append("What I then run, and what passes:")
    for t in v.tests:
        if t.kind == "manual":
            lines.append("   - %s: %s" % (t.id, t.p["text"]))
            continue
        if v.hands and t.pre:
            lines += ["   * you: " + x for x in t.pre]
        lines.append("   - %s%s" % (t.id, ("  (%s)" % t.why) if t.why else ""))
        try:
            model = engine.predict(t)
        except Exception:
            model = None
        lines += ["        " + check_text(c, model) for c in t.checks]
    lines.append("Then say: \"%s cabled\"%s." % (v.id, " and stay: I run one part at a time and say what to change before the next" if v.hands
                                                  else " (you can leave; I report when it is done)"))
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------------------------------
MARK = {"pass": "ok", "done": "ok", "fail": "FAIL", "skip": "skip", None: ".."}


def next_step(book, stem):
    for s in steps(stem):
        if book.state["steps"].get(s[0], {}).get("status") not in ("pass", "done", "skip"):
            return s
    return None


def status_text(book, markdown=False):
    st = book.state
    out = ["# AMOD and RF-MOD bring-up: where we are" if markdown else "AMOD and RF-MOD bring-up: where we are", "",
           "Written %s by `bringup/run.py`.  The plan: [`../BRINGUP.md`](../BRINGUP.md); every visit's card: [`VISITS.md`](VISITS.md)." % now(), ""]
    act = st.get("active")
    out.append("**Board on the bench: %s**" % (tiles.BOARDS[act]["name"] + (" (unit %s)" % st["units"].get(act, "1")) if act else "none yet (`run.py board <name>`)"))
    out.append("**Cabled now (as last confirmed): %s**" % (st.get("cabled") or "nothing"))
    out.append("")
    if markdown:
        out += ["| board | steps done | failing | next step |", "|---|---|---|---|"]
    for stem in tiles.ORDER:
        ss = steps(stem)
        done = sum(1 for s in ss if st["steps"].get(s[0], {}).get("status") in ("pass", "done", "skip"))
        bad = [s[0] for s in ss if st["steps"].get(s[0], {}).get("status") == "fail"]
        nx = next_step(book, stem)
        row = (tiles.BOARDS[stem]["name"], "%d of %d" % (done, len(ss)), ", ".join(bad) or "-", nx[0] if nx else "finished")
        out.append("| %s | %s | %s | %s |" % row if markdown else "  %-8s %-9s failing: %-22s next: %s" % row)
    out.append("")
    if act:
        nx = next_step(book, act)
        out.append("## Next, for Jason" if markdown else "NEXT, FOR JASON")
        out.append("")
        if nx is None:
            out.append("%s is finished: every step is recorded.  Choose the next board (`run.py board ...`)." % tiles.BOARDS[act]["name"])
        else:
            out.append(("```\n" if markdown else "") + step_text(book, act, nx) + ("\n```" if markdown else ""))
        last = [(k, v) for k, v in st["steps"].items() if k.lower().startswith(tiles.BOARDS[act]["letter"] + ".")]
        if last:
            out += ["", "## Last results on this board" if markdown else "LAST RESULTS ON THIS BOARD", ""]
            for k, v in last[-6:]:
                out.append("- %s: %s, %s%s" % (k, v["status"], v["when"], (" -- " + v["note"]) if v.get("note") else ""))
    return "\n".join(out) + "\n"


def step_text(book, stem, s):
    b = tiles.BOARDS[stem]
    sid, kind, title, v = s
    if kind == "inspect":
        return ("%s: %s, unpowered, with a loupe.  Photograph both sides first.\n" % (sid, b["name"]) +
                "\n".join("   [ ] " + x for x in b["inspect"]) +
                "\nThen say: \"%s done\" (or what you saw that differs; a photo helps)." % sid)
    if kind == "setup":
        return ("%s: set on %s, once:\n" % (sid, b["name"]) + "\n".join("   [ ] " + x for x in b["setup"]) +
                "\nThen say: \"%s done\"." % sid)
    if kind == "power":
        return power_text(stem)
    prev = None
    if book.state.get("cabled"):
        try:
            pstem, ps = find(book.state["cabled"])
            prev = ps[3] if pstem == stem else None
        except SystemExit:
            prev = None
    return card(stem, v, prev)


def power_text(stem):
    b = tiles.BOARDS[stem]
    L = b["letter"].upper()
    lines = ["%s.power: first power for %s.  Every tile's slide switch DOWN (off) to begin with." % (L, b["name"]),
             "Hookup:",
             "   PWR   supply output 1 (+ and -) -> the USB-C power lead -> the board's USB-C jack (right edge, tile %s)" % b["power"]]
    if b.get("socket"):
        lines += ["   S1    scope CH1, a BNC-to-clip lead (x1) on a jumper pin in the rails socket hole printed \"+5\" (top edge of tile %s)" % b["power"],
                  "   S2    scope CH2, the same, in the hole printed \"-5\"",
                  "   S3    scope CH3, the same, in the hole printed \"3V3\"; all three ground clips on a pin in a hole printed \"G\""]
    else:
        lines += ["   (this board has no rails socket: its rails are judged by the LEDs and by the supply current)"]
    lines += ["What I run: 1.0 V, 3.0 V, then 5.0 V with a low current limit, reading the current at each; the rails; then the walk:",
              "   the supply's display shows a tile's name (\"ON %s\"): slide THAT tile's switch UP; the display moves on by itself." % b["walk"][0][0],
              "   Order: " + ", ".join(w[0] for w in b["walk"]) + ".  Expected steps (mA): " +
              ", ".join("%s %g-%g" % w for w in b["walk"]) + ".",
              "Tell me which LEDs are lit on tile %s when the supply first reaches 5 V." % b["power"],
              "Then say: \"%s cabled\" and stay for the walk (about two minutes)." % (L + ".power")]
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------------------
# running
# ---------------------------------------------------------------------------------------------------
def fmt(c):
    if c.get("value") is None:
        return "%s: NO NUMBER (%s)" % (c["name"], c.get("why", ""))
    lim = "%s to %s" % ("%.4g" % c["lo"] if c["lo"] is not None else "-inf", "%.4g" % c["hi"] if c["hi"] is not None else "+inf")
    return "%s = %.5g %s (%s)" % (c["name"], c["value"], c["unit"], lim)


def make_bench(args):
    if args.sim:
        import sim
        b = Bench.sim(sim.World(args.fault or []))
        b.psu.set(5.0, 1.0); b.psu.on()                    # the rehearsal's board is already powered
        return b
    return Bench.real()


def go(args):
    book = Book(args.sim)
    stem, (sid, kind, title, v) = find(args.step)
    if kind == "power":
        return power(args, stem)
    if v is None:
        raise SystemExit("%s is a step for a person: `run.py done %s \"what you saw\"`" % (sid, sid))
    b = tiles.BOARDS[stem]
    bench = make_bench(args)
    book.state["active"], book.state["cabled"] = stem, sid
    print("%s  %s, %s" % (sid, b["name"], title))
    results, all_ok, manual = {}, True, []
    try:
        if b.get("power") and not args.sim:
            volts, amps = bench.psu.read()
            if volts < 4.5:
                raise SystemExit("the board's supply reads %.2f V: run `run.py power %s` (or `--resume`) first" % (volts, stem))
        for t in v.tests:
            if args.only and args.only.lower() not in t.id.lower():
                continue
            if t.kind == "manual":
                manual.append(t)
                print("  %-34s WITH YOU: %s" % (t.id, t.p["text"]))
                continue
            try:
                res, raw = measure.run(t, v, bench)
                out = engine.judge(t, res)
            except NotAssigned as e:
                raise SystemExit("cannot run %s: %s" % (t.id, e))
            ok = all(c["ok"] for c in out)
            all_ok &= ok
            results[t.id] = "pass" if ok else "fail"
            print("  %-34s %s" % (t.id, "pass" if ok else "FAIL"))
            for c in out:
                print("      %s %s" % ("  " if c["ok"] else "!!", fmt(c)))
            path = book.data(stem, sid + "_" + t.name, dict(test=t.id, when=now(), checks=out, raw=raw))
            book.log(b["name"], sid, t.id, "pass" if ok else "**FAIL**", "; ".join(fmt(c) for c in out))
    finally:
        bench.quiet()
    kept = book.state.setdefault("results", {}).setdefault(sid, {})
    kept.update(results)
    measured = [t.id for t in v.tests if t.kind != "manual"]
    missing = [x for x in measured if x not in kept]
    all_ok = all(kept.get(x) == "pass" for x in measured if x in kept)
    manual = [t for t in v.tests if t.kind == "manual"]
    if missing:
        book.save()
        print("\n%s: %d of %d parts measured so far (%s); still to run: %s" % (sid, len(measured) - len(missing), len(measured),
              "all pass" if all_ok else "with failures", ", ".join(missing)))
        return 0 if all_ok else 1
    status = "pass" if all_ok and not manual else ("fail" if not all_ok else "open")
    note = ", ".join("%s %s" % kv for kv in kept.items() if kv[1] == "fail")
    if manual:
        note = (note + "; " if note else "") + "with you: " + ", ".join(t.id for t in manual)
    book.mark(sid, status if status != "open" else "fail", note if status != "open" else note + " (record with `run.py done %s`)" % sid)
    book.save()
    print("\n%s: %s" % (sid, {"pass": "ALL PASS", "fail": "FAILURES: " + note, "open": "measured parts pass; the hands-on parts are still to record"}[status]))
    nx = next_step(book, stem)
    if nx and not args.sim:
        print("\nNEXT:\n" + step_text(book, stem, nx))
    return 0 if all_ok else 1


def power(args, stem=None):
    book = Book(args.sim)
    stem = stem or args.stem
    b = tiles.BOARDS[stem]
    if not b.get("power"):
        raise SystemExit("%s has no supply of its own" % b["name"])
    sid = b["letter"].upper() + ".power"
    bench = make_bench(args)
    psu = bench.psu
    ok_all, notes = True, []
    book.state["active"], book.state["cabled"] = stem, sid
    qlo, qhi = b["quiescent"]
    if args.sim:
        bench.world.base_amps = 0.5 * (qlo + qhi)
    try:
        try:                                               # the supply's one switch serves both outputs: the other one at 0 V
            psu.set(0.0, 0.05, out=bench.cfg["psu"].get("motor_output", 2))
        except Exception as e:
            print("  (output 2 not set to 0 V: %r)" % (e,))
        if not getattr(args, "resume", False):
            for volts, limit, top in ((1.0, 0.10, 0.05), (3.0, 0.20, 0.12), (5.0, 0.30, qhi)):
                psu.set(volts, limit); psu.on(); measure._wait(bench, 1.5)
                v, i = psu.read(); mode = psu.mode()
                ok = mode == "CV" and i <= top and (volts < 5 or i >= qlo * 0.3)
                ok_all &= ok
                print("  %.1f V: %.3f V, %.1f mA, %s   %s" % (volts, v, 1e3 * i, mode, "ok" if ok else "!! expected under %.0f mA in CV" % (1e3 * top)))
                book.log(b["name"], sid, "staircase %.1f V" % volts, "pass" if ok else "**FAIL**", "%.3f V, %.1f mA, %s" % (v, 1e3 * i, mode))
                if not ok:
                    psu.off()
                    raise SystemExit("supply switched off: look for a short or a turned part before going on")
        else:
            psu.set(5.0, b.get("limit", 0.9)); psu.on(); measure._wait(bench, 1.0)
        if b.get("socket") and not getattr(args, "no_rails", False) and not args.sim:
            sc = bench.scope
            chans = {"+5": (1, "1M"), "-5": (2, "1M"), "3V3": (3, "1M")}
            t, v, _ = measure.capture_ranged(bench, chans, 2e-3, {"+5": (4.0, 5.5), "-5": (-5.5, -4.0), "3V3": (2.8, 3.6)})
            for name, (lo, hi) in (("+5", (4.55, 5.15)), ("-5", (-5.25, -4.4)), ("3V3", (3.2, 3.4))):
                m, r = float(np.mean(v[name])), float(np.std(v[name]))
                ok = lo <= m <= hi; ok_all &= ok
                print("  rail %-4s %.3f V, %.1f mV rms   %s" % (name, m, 1e3 * r, "ok" if ok else "!! want %.2f to %.2f" % (lo, hi)))
                book.log(b["name"], sid, "rail " + name, "pass" if ok else "**FAIL**", "%.3f V, %.1f mV rms" % (m, 1e3 * r))
        # the walk: one tile's slide switch at a time, the supply's display saying which
        psu.set(5.0, b.get("limit", 0.9))
        base = float(np.median([psu.read()[1] for _ in range(5)]))
        print("  the walk (follow the supply's display):")
        for tile, lo, hi in b["walk"]:
            psu.say("ON " + tile.upper())
            if args.sim:                                   # the rehearsal's Jason slides the switch at once
                bench.world.base_amps += 0.5e-3 * (lo + hi) * (0.0 if tile in bench.world.dead else 1.0)
            seen, t_end = None, datetime.datetime.now() + datetime.timedelta(seconds=args.wait)
            while datetime.datetime.now() < t_end or args.sim:
                i = float(np.median([psu.read()[1] for _ in range(3)]))
                if abs(i - base) > 0.0006:
                    measure._wait(bench, 0.6)
                    i = float(np.median([psu.read()[1] for _ in range(5)]))
                    seen = i - base; base = i
                    break
                if args.sim:
                    break
            d = 1e3 * (seen or 0.0)
            ok = (lo <= d <= hi) or (seen is None and lo < 1.0)
            ok_all &= ok
            what = "%.1f mA" % d if seen is not None else "no step seen in %d s" % args.wait
            print("     %-4s %-22s want %g to %g mA   %s" % (tile, what, lo, hi, "ok" if ok else "!!"))
            book.log(b["name"], sid, "switch on " + tile, "pass" if ok else "**FAIL**", "%s (want %g to %g mA)" % (what, lo, hi))
            notes += [] if ok else ["%s %s" % (tile, what)]
        psu.say(None)
        v, i = psu.read()
        print("  all on: %.3f V, %.1f mA" % (v, 1e3 * i))
        book.log(b["name"], sid, "all tiles on", "info", "%.3f V, %.1f mA" % (v, 1e3 * i))
    finally:
        bench.quiet()
    book.mark(sid, "pass" if ok_all else "fail", "; ".join(notes))
    book.save()
    print("%s: %s.  The supply stays ON at 5.0 V, %.1f A limit; `run.py off` switches it off." % (sid, "ALL PASS" if ok_all else "FAILURES: " + "; ".join(notes), b.get("limit", 0.9)))
    return 0 if ok_all else 1


def cal(args):
    """Thru calibration: each generator channel straight into the scope channel of the same number, 50 ohm."""
    book = Book(args.sim)
    bench = make_bench(args)
    out = {}
    try:
        for n in (1, 2):
            t = engine.bode("cal", "IN", "OUT", (1e2, 3e7, 23), 1.0, engine.flat(0), [engine.G(1e3, 0.4), engine.G(1e6, 0.4), engine.G(2.5e7, 1.0)], load="50")
            v = engine.Visit("cal", "lf", [t], conns=[("G%d" % n, "cal", "IN", ""), ("S%d" % n, "cal", "OUT", "scope, 50 ohm input")])
            if args.sim:
                bench.world.visit, bench.world.test = v, t
            res, raw = measure.run_bode(t, v, bench)
            out["G%d" % n] = {"f": list(map(float, res.f)), "k": [float(abs(x)) for x in res.h["OUT"]]}
            for c in engine.judge(t, res):
                print("  G%d into S%d: %s %s" % (n, n, "ok" if c["ok"] else "!!", fmt(c)))
    finally:
        bench.quiet()
    with open(os.path.join(book.data_dir if os.path.isdir(book.data_dir) else HERE, "cal.json"), "w") as f:
        json.dump(out, f)
    print("saved; the sweeps now divide by these.")


def load_cal(sim):
    for d in (os.path.join(HERE, "data_sim" if sim else "data"), HERE):
        p = os.path.join(d, "cal.json")
        if os.path.exists(p) and not sim:
            with open(p) as f:
                for k, v in json.load(f).items():
                    measure.CAL[k] = (np.array(v["f"]), np.array(v["k"]))
            return


def plan_files():
    import pictures
    os.makedirs(os.path.join(HERE, "cards"), exist_ok=True)
    out = ["# Every visit of the bring-up, board by board", "",
           "Written by `python3 bringup/run.py plan` from `bringup/tiles.py`; do not edit by hand.  The procedure, the instruments and the "
           "cables' names are in [`../BRINGUP.md`](../BRINGUP.md).  A cable keeps its name for the whole bring-up: G1 and G2 are the "
           "generator's channels, S1 to S4 the scope's, P1 and P2 the network analyzer's ports, SA the spectrum analyzer's input.", ""]
    n = 0
    for stem in tiles.ORDER:
        b = tiles.BOARDS[stem]
        out += ["## %s: %s" % (b["name"], b["title"]), ""]
        prev = None
        for sid, kind, title, v in steps(stem):
            out += ["### %s" % sid, "", "```"]
            if v is None:
                out.append(step_text(Book(sim=True), stem, (sid, kind, title, v)))
            else:
                out.append(card(stem, v, prev))
                pictures.card_png(stem, v, os.path.join(HERE, "cards", sid + ".png"), geo(stem), jack_info)
                prev = v; n += 1
            out += ["```", ""]
            if v is not None and v.conns:
                out += ["![%s](cards/%s.png)" % (sid, sid), ""]
    with open(os.path.join(HERE, "VISITS.md"), "w") as f:
        f.write("\n".join(out))
    top = os.path.join(ROOT, "BRINGUP.md")
    text = open(top).read()
    a, z = text.index("<!-- visits:start -->"), text.index("<!-- visits:end -->")
    with open(top, "w") as f:
        f.write(text[:a] + "<!-- visits:start -->\n```\n" + "\n".join(listing()) + "\n```\n" + text[z:])
    Book().save()
    print("VISITS.md, STATUS.md and %d pictures in cards/" % n)


def listing():
    """One line per visit: the whole plan's cabling at a glance."""
    out = []
    for stem in tiles.ORDER:
        b = tiles.BOARDS[stem]
        out.append("%s (%s)" % (b["name"], b["title"]))
        for sid, kind, title, v in steps(stem):
            if v is None:
                out.append("  %-10s %s" % (sid, title)); continue
            cs = []
            for c, tile, jack, note in v.conns:
                if c == "HOST": cs.append("HOST"); continue
                arrow = "->" if c[0] == "G" else "<-" if c[0] == "S" else "-"
                load = "(50)" if "50 ohm" in note else ""
                cs.append("%s%s%s%s %s" % (c, load, arrow, tile, jack_info(stem, tile, jack)["name"]))
            if v.hands and len(v.tests) > 1:
                extra = " | %d parts, a change between each" % len(v.tests)
            elif v.stage == "kit":
                extra = " | " + "; ".join(dict.fromkeys(k for t in v.tests for k in t.kit))
            else:
                extra = (" | first: " + "; ".join(x for _, x in v.pre)) if v.pre else ""
            out.append("  %-10s %s%s" % (sid, ", ".join(cs) if cs else "(no cable) " + ", ".join(t.id for t in v.tests), extra))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["status", "board", "card", "go", "done", "skip", "fail", "power", "cal", "bench", "note", "revb", "off", "plan", "list"])
    ap.add_argument("arg", nargs="*")
    ap.add_argument("--sim", action="store_true"); ap.add_argument("--fault", action="append")
    ap.add_argument("--resume", action="store_true", help="power: skip the staircase (the board is already up)")
    ap.add_argument("--no-rails", dest="no_rails", action="store_true"); ap.add_argument("--wait", type=int, default=8)
    ap.add_argument("--only", help="go: run only the tests of the visit whose name contains this (a hands sitting goes one part at a time)")
    args = ap.parse_args()
    load_cal(args.sim)
    book = Book(args.sim)
    if args.cmd == "status":
        print(status_text(book)); book.save()
    elif args.cmd == "board":
        stem = args.arg[0]
        if stem not in tiles.BOARDS:
            raise SystemExit("boards: " + ", ".join(tiles.ORDER))
        book.state["active"] = stem
        if len(args.arg) > 1:
            book.state["units"][stem] = args.arg[1]
        book.save(); print(status_text(book))
    elif args.cmd == "card":
        stem, s = find(args.arg[0])
        print(step_text(book, stem, s))
    elif args.cmd == "go":
        args.step = args.arg[0]; sys.exit(go(args))
    elif args.cmd in ("done", "skip", "fail"):
        stem, s = find(args.arg[0])
        note = " ".join(args.arg[1:])
        book.state["active"] = stem
        book.mark(s[0], {"done": "done", "skip": "skip", "fail": "fail"}[args.cmd], note)
        book.log(tiles.BOARDS[stem]["name"], s[0], "by hand", args.cmd, note)
        book.save(); print(status_text(book))
    elif args.cmd == "power":
        args.stem = args.arg[0]; sys.exit(power(args))
    elif args.cmd == "cal":
        cal(args)
    elif args.cmd == "bench":
        for name, state, text in make_bench(args).who() if not args.sim else []:
            print("  %-6s %-13s %s" % (name, state, text))
    elif args.cmd == "note":
        book.log(tiles.BOARDS[book.state["active"]]["name"] if book.state.get("active") else "-", "-", "note", "", " ".join(args.arg)); print("logged")
    elif args.cmd == "revb":
        with open(os.path.join(HERE, "REVB.md"), "a") as f:
            f.write("\n- (%s, inbox) %s\n" % (now(), " ".join(args.arg)))
        print("added to REVB.md's inbox")
    elif args.cmd == "off":
        b = make_bench(args)
        b.quiet()
        try:
            b.psu.off(); print("supply off")
        except NotAssigned as e:
            print(e)
    elif args.cmd == "plan":
        plan_files()
    elif args.cmd == "list":
        print("\n".join(listing()))


if __name__ == "__main__":
    main()
