#!/usr/bin/env python3
"""Build everything for one board or all three: footprints and models, the project files, the
schematic, ERC and the netlist, the circuit checks, the board, DRC, the fab package and the
documents.  Stops at the first gate that fails.

    ./make.py                         all boards, every stage
    ./make.py --board amod_p          one board
    ./make.py --stage sch --board amod_p
    ./make.py --clean                 delete everything the build generates
"""
import argparse, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(ROOT, "scripts")
HW = os.path.join(ROOT, "hardware")
OUT = os.path.join(ROOT, "out")
sys.path.insert(0, SCRIPTS)
import kienv, parts                                    # noqa: E402

GENERATED = ["hardware/lib/amod.pretty/", "hardware/lib/amod.3dshapes/", "hardware/sym-lib-table", "hardware/fp-lib-table",
             "docs/images/", "docs/MANUFACTURING.md", "out/", "build/"]
for _stem in parts.BOARDS:
    GENERATED += ["hardware/%s.kicad_sch" % _stem, "hardware/%s.kicad_pcb" % _stem, "hardware/%s.kicad_pro" % _stem]
ALSO_TRANSIENT = ["hardware/%s.kicad_prl" % s for s in parts.BOARDS] + ["hardware/fp-info-cache"]


class Fail(Exception):
    pass


def banner(txt):
    print("\n=== %s %s" % (txt, "=" * max(0, 64 - len(txt))), flush=True)


def sys_py(script, *args):
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args], capture_output=True, text=True, cwd=ROOT)
    sys.stdout.write(r.stdout)
    if r.returncode:
        sys.stdout.write(r.stderr)
        raise Fail("%s failed" % script)
    return r.stdout


def kicad_py(script, *args):
    run = kienv.runner()
    cmd = ([run, "python3.11", os.path.join(SCRIPTS, script), *args] if run else [sys.executable, os.path.join(SCRIPTS, script), *args])
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    sys.stdout.write(r.stdout)
    if r.returncode:
        sys.stdout.write(r.stderr)
        raise Fail("%s failed" % script)
    return r.stdout


def count_violations(path):
    return sum(1 for line in open(path) if line.startswith("["))


def stage_libs(stem):
    banner("footprints, models and project files")
    sys_py("gen_models.py")
    sys_py("gen_footprints.py")
    sys_py("gen_symbols.py")
    kienv.cli("fp", "upgrade", os.path.join(HW, "lib", "amod.pretty"), "--force")
    sys_py("gen_project.py", stem)


def stage_sch(stem):
    banner("schematic: " + stem)
    sys_py("gen_sch.py", stem)
    sch = os.path.join(HW, stem + ".kicad_sch")
    kienv.cli("sch", "upgrade", sch)
    os.makedirs(OUT, exist_ok=True)
    rpt = os.path.join(OUT, "erc_%s.rpt" % stem)
    kienv.cli("sch", "erc", "--format", "report", "--severity-all", "-o", rpt, sch, check=False)
    n = count_violations(rpt)
    print("  ERC: %d violation(s)" % n)
    if n:
        raise Fail("ERC reported %d violations -- see %s" % (n, os.path.relpath(rpt, ROOT)))
    net = os.path.join(OUT, stem + ".net")
    kienv.cli("sch", "export", "netlist", "--format", "kicadsexpr", "-o", net, sch)
    out = sys_py("check_circuit.py", stem, net)
    if "all circuit checks passed" not in out:
        raise Fail("the schematic does not implement the tiles' netlist")
    out = sys_py("check_schematic.py", sch)
    if "no text overlaps" not in out:
        raise Fail("the schematic sheet has overlapping or stray text")


def stage_pcb(stem):
    banner("PCB: " + stem)
    pcb = os.path.join(HW, stem + ".kicad_pcb")
    net = os.path.join(OUT, stem + ".net")
    kicad_py("gen_pcb.py", stem, net, pcb)
    sys_py("gen_project.py", stem)
    rpt = os.path.join(OUT, "drc_%s.rpt" % stem)
    kienv.cli("pcb", "drc", "--format", "report", "--severity-all", "--schematic-parity", "-o", rpt, pcb, check=False)
    n = count_violations(rpt)
    print("  DRC: %d violation(s)" % n)
    if n:
        raise Fail("DRC reported %d violations -- see %s" % (n, os.path.relpath(rpt, ROOT)))


def stage_out(stem):
    banner("manufacturing outputs: " + stem)
    sys_py("gen_outputs.py", stem)
    out = sys_py("check_outputs.py", stem)
    if "ALL FAB CHECKS PASSED" not in out:
        raise Fail("the fab package did not pass its checks")


def stage_docs(stem):
    banner("documentation: " + stem)
    sys_py("gen_docs.py", stem)


def clean():
    banner("clean")
    locked = any(n.startswith("~") and n.endswith(".lck") for n in os.listdir(HW)) if os.path.isdir(HW) else False
    for rel in GENERATED + ([] if locked else ALSO_TRANSIENT):
        path = os.path.join(ROOT, rel.rstrip("/"))
        if rel.endswith("/"):
            if os.path.isdir(path):
                shutil.rmtree(path); print("  removed " + rel)
        elif os.path.exists(path):
            os.remove(path); print("  removed " + rel)


STAGES = [("libs", stage_libs), ("sch", stage_sch), ("pcb", stage_pcb), ("out", stage_out), ("docs", stage_docs)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", action="store_true")
    ap.add_argument("--stage", action="append")
    ap.add_argument("--board", action="append")
    a = ap.parse_args()
    if a.clean:
        clean(); return 0
    print(kienv.describe())
    boards = a.board or list(parts.BOARDS)
    try:
        for stem in boards:
            for name, fn in STAGES:
                if a.stage and name not in a.stage:
                    continue
                fn(stem)
    except Fail as e:
        print("\nBUILD FAILED: %s" % e)
        return 1
    print("\nBUILD OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
