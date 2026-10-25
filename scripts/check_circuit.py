#!/usr/bin/env python3
"""The exported KiCad netlist against the netlist the tiles declared: every (ref, pad, net) the
tiles say must be one connection in KiCad's netlist, no tile part may be missing, and no net may
join two tiles.  Net names differ in spelling (KiCad names a label net "/P5_IN", an unlabelled one
"Net-(R501-Pad2)"), so the comparison is by connectivity: the set of (ref, pad) groups.

    python3 scripts/check_circuit.py amod_p out/amod_p.net
"""
import importlib, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from sexp_parse import parse_file


def kicad_nets(path):
    root = parse_file(path)
    nets = {}
    for n in root.first("nets").kids("net"):
        name = n.first("name").atom(0)
        nets[name] = {(x.first("ref").atom(0), x.first("pin").atom(0)) for x in n.kids("node")}
    comps = {c.first("ref").atom(0) for c in root.first("components").kids("comp")}
    return nets, comps


def main():
    stem, path = sys.argv[1], sys.argv[2]
    mod = importlib.import_module("boards." + stem)
    ts = mod.tiles()
    knets, kcomps = kicad_nets(path)
    where = {}
    for name, nodes in knets.items():
        for node in nodes:
            where[node] = name
    declared = {}
    problems, checks = [], 0
    for t in ts:
        for ref, pad, net in t.netlist():
            declared.setdefault(net, set()).add((ref, pad))
            if ref not in kcomps:
                problems.append("%s: %s is not in the schematic" % (t.id, ref))
    # every declared net is one KiCad net (all its pins share one name) and no KiCad net spans two declared nets,
    # except GND and the rails
    for net, pins in sorted(declared.items()):
        names = {where.get(p) for p in pins}
        checks += 1
        if None in names:
            missing = [p for p in pins if p not in where]
            problems.append("%s: pins not connected in the schematic: %s" % (net, sorted(missing)[:6]))
            names.discard(None)
        if len(names) > 1:
            problems.append("%s is split in the schematic into %s" % (net, sorted(names)))
    # a KiCad net must not join pins of two different declared nets
    for name, nodes in knets.items():
        decl = {next((n for n, ps in declared.items() if node in ps), None) for node in nodes}
        decl.discard(None)
        if len(decl) > 1:
            problems.append("KiCad net %s joins the declared nets %s" % (name, sorted(decl)))
    print("  %d declared nets checked against %s" % (checks, os.path.relpath(path)))
    for p in problems:
        print("  FAIL " + p)
    if not problems:
        print("  all circuit checks passed: the schematic's connectivity is the tiles' netlist")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
