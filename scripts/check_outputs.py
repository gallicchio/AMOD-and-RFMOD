#!/usr/bin/env python3
"""Check the fab package the way a fab's importer would.

Catches the mistakes that survive DRC and only show up as a rejected order or,
worse, a wrong board: a BOM line with no order code, a placement that misses
the board because the origins disagree, a part in the CPL that the BOM never
mentions, a drill file with no holes.
"""
import csv, math, os, re, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parts, kienv
import geometry as G
from sexp_parse import parse_file

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "out")

REQUIRED_2 = ["F_Cu", "B_Cu", "F_Mask", "B_Mask", "F_Silkscreen", "B_Silkscreen",
              "F_Paste", "B_Paste", "Edge_Cuts"]
REQUIRED_4 = REQUIRED_2 + ["In1_Cu", "In2_Cu"]


def gerber_extent(path):
    """Coordinate extent of a gerber, in mm."""
    xs, ys = [], []
    fmt = (4, 6)
    for line in open(path, errors="replace"):
        m = re.search(r"%FSLAX(\d)(\d)Y\d\d\*%", line)
        if m:
            fmt = (int(m.group(1)), int(m.group(2)))
        for m in re.finditer(r"X(-?\d+)Y(-?\d+)", line):
            xs.append(int(m.group(1)) / 10 ** fmt[1])
            ys.append(int(m.group(2)) / 10 ** fmt[1])
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def check(stem, layers, w, h, problems, notes):
    d = os.path.join(OUT, stem)
    zpath = os.path.join(d, f"{stem}-gerbers.zip")
    if not os.path.exists(zpath):
        problems.append(f"{stem}: no gerber zip")
        return
    names = zipfile.ZipFile(zpath).namelist()
    for want in (REQUIRED_4 if layers == 4 else REQUIRED_2):
        if not any(want in n for n in names):
            problems.append(f"{stem}: gerber zip has no {want} layer")
    drills = [n for n in names if n.endswith(".drl")]
    if not drills:
        problems.append(f"{stem}: no Excellon drill file")
    for dn in drills:
        body = zipfile.ZipFile(zpath).read(dn).decode("latin-1")
        if "PTH" in dn and not re.search(r"^T\d", body, re.M):
            problems.append(f"{stem}: {dn} defines no tools")
    notes.append(f"{stem}: gerber zip has {len(names)} files "
                 f"({len(drills)} drill)")

    # the outline must be the board we think we designed
    gdir = os.path.join(d, "gerbers")
    edge = [n for n in os.listdir(gdir) if "Edge_Cuts" in n]
    if edge:
        ext = gerber_extent(os.path.join(gdir, edge[0]))
        if ext:
            gw, gh = ext[2] - ext[0], ext[3] - ext[1]
            if abs(gw - w) > 0.3 or abs(gh - h) > 0.3:
                problems.append(f"{stem}: outline is {gw:.2f} x {gh:.2f} mm, "
                                f"expected {w} x {h}")
            else:
                notes.append(f"{stem}: outline {gw:.2f} x {gh:.2f} mm, "
                             f"origin at ({ext[0]:.2f}, {ext[1]:.2f})")
            if gw > 100.5 or gh > 100.5:
                problems.append(f"{stem}: {gw:.1f} x {gh:.1f} mm is outside "
                                "the 100 x 100 mm discounted size")

    # placements land on the board, and every one is in the BOM
    cpl = os.path.join(d, f"{stem}_cpl_kicad_native.csv")
    bom = os.path.join(d, f"{stem}_bom_jlcpcb_upload.csv")
    rows = list(csv.DictReader(open(cpl)))
    for r in rows:
        x, y = float(r["Mid X"]), float(r["Mid Y"])
        if not (-1 <= x <= w + 1 and -1 <= y <= h + 1):
            problems.append(f"{stem}: {r['Designator']} placed at "
                            f"({x:.1f}, {y:.1f}), off the board")
        if r["Layer"] not in ("Top", "Bottom"):
            problems.append(f"{stem}: {r['Designator']} has layer "
                            f"{r['Layer']!r}")
        rot = float(r["Rotation"])
        if not (-360 <= rot <= 360):
            problems.append(f"{stem}: {r['Designator']} rotation {rot}")

    bom_rows = list(csv.DictReader(open(bom)))
    in_bom = set()
    for b in bom_rows:
        if not b["LCSC Part #"].strip():
            problems.append(f"{stem}: BOM line {b['Designator']} "
                            f"({b['Comment']}) has no LCSC code")
        if not re.fullmatch(r"C\d+", b["LCSC Part #"].strip() or "x"):
            problems.append(f"{stem}: BOM line {b['Designator']} has a "
                            f"malformed code {b['LCSC Part #']!r}")
        in_bom.update(x.strip() for x in b["Designator"].split(","))
    placed = {r["Designator"] for r in rows}
    missing = sorted(placed - in_bom)
    extra = sorted(in_bom - placed)
    if missing:
        problems.append(f"{stem}: placed but not in the BOM: {missing}")
    if extra:
        problems.append(f"{stem}: in the BOM but not placed: {extra}")
    notes.append(f"{stem}: {len(placed)} placements, {len(bom_rows)} BOM "
                 f"lines, all with order codes")

    # The JLC copy must be the same file, turned by exactly the amounts in the
    # rotation table and moved by exactly the datums in parts.JLC_DATUM (turned
    # with the part; the CPL's y runs up), and by nothing else.
    jlc_path = os.path.join(ROOT, "out", stem, f"{stem}_cpl_jlcpcb_upload.csv")
    if not os.path.exists(jlc_path):
        problems.append(f"{stem}: no JLCPCB-corrected placement file")
        return
    lcsc_of = {}
    for b in bom_rows:
        for ref in b["Designator"].split(","):
            lcsc_of[ref.strip()] = b["LCSC Part #"].strip()
    jlc = {r["Designator"]: r for r in csv.DictReader(open(jlc_path))}
    plain = {r["Designator"]: r for r in rows}
    if set(jlc) != set(plain):
        problems.append(f"{stem}: the JLCPCB placement file lists different "
                        f"parts from {os.path.basename(cpl)}")
        return
    turned = 0
    for ref, a in plain.items():
        b = jlc[ref]
        dat = parts.JLC_DATUM.get(lcsc_of.get(ref, ""), (0.0, 0.0))
        r0 = math.radians(float(a["Rotation"]))
        ex = float(a["Mid X"]) + dat[0] * math.cos(r0) + dat[1] * math.sin(r0)
        ey = float(a["Mid Y"]) - (-dat[0] * math.sin(r0) + dat[1] * math.cos(r0))
        if a["Layer"] != b["Layer"] or abs(float(b["Mid X"]) - ex) > 0.002 or abs(float(b["Mid Y"]) - ey) > 0.002:
            problems.append(f"{stem}: {ref} moved in the JLCPCB placement "
                            f"file by other than its datum")
        want = (float(a["Rotation"])
                + parts.JLC_ROTATION.get(lcsc_of.get(ref, ""), (0,))[0]) % 360.0
        diff = (float(b["Rotation"]) - want) % 360.0
        if min(diff, 360.0 - diff) > 0.05:
            problems.append(f"{stem}: {ref} is at {b['Rotation']} deg for "
                            f"JLCPCB, expected {want:.1f}")
        elif float(b["Rotation"]) != float(a["Rotation"]):
            turned += 1
    notes.append(f"{stem}: the JLCPCB placement file turns {turned} parts "
                 f"and moves none")

    # A connector whose pins are symmetric can be placed with its cable face backwards and still fit every pad (the
    # op-amp board's KF301s, 2026-10-27).  FACE: the face a cable enters, in JLCPCB's drawing (y down) and in our
    # footprint; turned by each file's rotation, the two must agree.
    FACE = {"C474881": ((0.0, 1.0), (0.0, -1.0), "wire openings"), "C474882": ((0.0, 1.0), (0.0, -1.0), "wire-entry arrows")}
    def turn(v, deg):
        r = math.radians(deg)
        return (v[0] * math.cos(r) + v[1] * math.sin(r), -v[0] * math.sin(r) + v[1] * math.cos(r))
    faced = []
    for ref, a in plain.items():
        code = lcsc_of.get(ref, "")
        if code not in FACE:
            continue
        theirs, ours, what = FACE[code]
        t, o = turn(theirs, float(jlc[ref]["Rotation"])), turn(ours, float(a["Rotation"]))
        if a["Layer"] == "Bottom":
            t, o = (-t[0], t[1]), (-o[0], o[1])
        if t[0] * o[0] + t[1] * o[1] < 0.9:
            problems.append(f"{stem}: {ref}'s {what} (JLCPCB's drawing, turned {jlc[ref]['Rotation']}) do not face where the footprint draws them")
        else:
            faced.append(ref + " " + {(0, -1): "N", (0, 1): "S", (1, 0): "E", (-1, 0): "W"}[(round(o[0]), round(o[1]))])
    if faced:
        notes.append(f"{stem}: terminal blocks' wire faces as drawn (JLCPCB's drawing turned by the CPL): " + ", ".join(sorted(faced)))



def check_models(stem, problems, notes):
    """Every 3D model a footprint names must actually be on disk.

    gen_models.py was once not wired into the build at all, so a fresh clone
    had no models and half the board rendered as bare pads -- with nothing
    complaining.
    """
    pcb = os.path.join(ROOT, "hardware", stem + ".kicad_pcb")
    if not os.path.exists(pcb):
        return
    share = kienv.share_dir()
    subs = {"${KIPRJMOD}": os.path.join(ROOT, "hardware"),
            "${KICAD10_3DMODEL_DIR}": os.path.join(share, "3dmodels"),
            "${KICAD9_3DMODEL_DIR}": os.path.join(share, "3dmodels"),
            "${KISYS3DMOD}": os.path.join(share, "3dmodels")}
    board = parse_file(pcb)
    missing, ok = [], 0
    for fp in board.kids("footprint"):
        ref = next((p.atom(1) for p in fp.kids("property")
                    if p.atom(0) == "Reference"), "?")
        models = [m.atom(0) for m in fp.kids("model")]
        if not models:
            # Nothing is fitted here -- a mounting hole, a probe pad, a solder
            # jumper -- so there is nothing to draw.
            if ref[:2] not in ("MH", "TP", "JP") and ref[:1] != "H":
                missing.append(f"{ref} has no 3D model")
            continue
        for m in models:
            path = m
            for k, v in subs.items():
                path = path.replace(k, v)
            if os.path.exists(path):
                ok += 1
            else:
                missing.append(f"{ref} -> {os.path.basename(path)}")
    for m in missing:
        problems.append(f"{stem}: missing 3D model, {m}")
    notes.append(f"{stem}: {ok} 3D model(s) resolve on disk")





def check_codes(problems, notes):
    """Every LCSC code is the part the design thinks it is, by JLCPCB's own
    description (from the parts-API cache; scripts/jlc_api.py <code> refreshes it)."""
    import glob, jlc_api
    used = set()                                        # stock matters only for a code some board's BOM orders
    for path in glob.glob(os.path.join(OUT, "*", "*_bom_jlcpcb_upload.csv")):
        used |= {r["LCSC Part #"].strip() for r in csv.DictReader(open(path))}
    seen = 0
    for key in parts.all_keys():
        p = parts.info(key)
        code = p.get("lcsc")
        if not code:
            continue
        try:
            part, ts = jlc_api.by_code(code)
        except Exception as e:                      # no network: the cache is gitignored
            notes.append(f"LCSC codes not re-checked against JLCPCB's API ({type(e).__name__}); "
                         f"they were on {parts.STOCK_DATE}")
            return
        if part is None:
            problems.append(f"{code} ({key}): JLCPCB's parts API knows no such code")
            continue
        seen += 1
        model = part.get("componentModelEn") or ""
        text = " ".join([part.get("describe") or "", model, part.get("componentSpecificationEn") or ""])
        mpn = p.get("mpn", "")
        if mpn and not model.upper().startswith(mpn.upper()):
            problems.append(f"{code} ({key}): JLCPCB calls it {model!r}, the design says {mpn!r}")
        missing = [w for w in p.get("match", []) if w.lower() not in text.lower()]
        if missing:
            problems.append(f"{code} ({key}): JLCPCB's description {text[:60]!r}... lacks {missing}")
        stock = part.get("stockCount") or 0
        free = part.get("canPresaleNumber")             # stock less what other orders hold: negative when it is oversold
        if free is not None and free < stock:           # (2026-10-29: four codes read thousands in stock and were oversold)
            stock = max(free, 0)
        if stock < 100 and code in used:
            if p.get("stock_exception"):                # a thin stock someone accepted, with who and when (parts.PARTS)
                notes.append(f"{code} ({key}): {stock} in stock ({ts[:10]}), accepted: {p['stock_exception']}")
            else:
                problems.append(f"{code} ({key}): only {stock} free to order ({part.get('stockCount')} in stock, {ts[:10]})")
    notes.append(f"{seen} LCSC codes match JLCPCB's own descriptions (MPN, value, package)")


def check_pages(stem, problems, notes):
    """Each assembly drawing fills its Letter page less half-inch margins, centred (CLAUDE_PCB.md gate 23)."""
    import contextlib, io, fit_pdf
    for side in ("top", "bottom"):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ok = fit_pdf.check(os.path.join(OUT, stem, f"{stem}-assembly-{side}.pdf"))
        (notes if ok else problems).append(buf.getvalue().strip())


def check_pmod(stem, problems, notes):
    """Every Pmod plug's pads carry the nets the Pmod standard puts there.  The plug's footprint is JLCPCB's drawing, whose
    numbering runs the opposite way from KiCad's horizontal header (pad 1 at the other end, on the row nearest the body):
    JLCPCB's pad p is KiCad's pad 13 - p, and KiCad's pad q is Pmod pin (q + 1) / 2 (odd q) or q / 2 + 6 (even q), the
    numbering the ECP5 board's sockets use.  Rev A's first layout used KiCad's rule on JLCPCB's numbering and mirrored every
    line; this check is why that cannot happen twice."""
    import json
    path = os.path.join(ROOT, "out", stem + "_geom.json")
    if not os.path.exists(path):
        return
    pads = json.load(open(path))["pads"]
    want = {1: "/PMOD1", 2: "/PMOD2", 3: "/PMOD3", 4: "/PMOD4", 5: "GND", 6: "/PMOD_VCC",
            7: "/PMOD5", 8: "/PMOD6", 9: "/PMOD7", 10: "/PMOD8", 11: "GND", 12: "/PMOD_VCC"}
    refs = {p["ref"] for p in pads if p["ref"].startswith("J")}
    n = 0
    for ref in sorted(refs):
        mine = [p for p in pads if p["ref"] == ref]
        nums = {p["pad"] for p in mine}
        if nums != {str(k) for k in range(1, 13)} or not any(p["net"].startswith("/PMOD") for p in mine):
            continue
        for p in mine:
            q = 13 - int(p["pad"])
            pin = (q + 1) // 2 if q % 2 else q // 2 + 6
            net = p["net"]
            if net in ("", None) or net.startswith("unconnected"):
                if want[pin].startswith("/PMOD") and want[pin] != "/PMOD_VCC":
                    continue                                 # an unused IO line
            if net != want[pin]:
                problems.append(f"{stem}: {ref} pad {p['pad']} is Pmod pin {pin}, which must be {want[pin]}, and carries {net}")
        n += 1
    if n:
        notes.append(f"{stem}: {n} Pmod plug(s): every pad's net is the Pmod standard's for its pin")


def check_stock(problems, notes):
    """Every chosen part had stock when the design was frozen."""
    low = []
    for key, p in parts.PARTS.items():
        if "stock" not in p:
            continue
        need = {"SMA": 27, "TP": 40, "DIP2": 3, "DIP4": 2}.get(key, 1)
        boards = p["stock"] // need
        if boards < 50:
            low.append(f"{p['mpn']} ({p['stock']} in stock = {boards} boards)")
    if low:
        notes.append("thin stock (see docs for alternates): " + "; ".join(low))
    notes.append(f"{len(parts.PARTS)} part types, "
                 f"{len(parts.PASSIVES)} passive values, all with order codes")


def main():
    stem = sys.argv[1] if len(sys.argv) > 1 else "amod_p"
    problems, notes = [], []
    check(stem, parts.BOARDS[stem]["layers"], G.BOARD, G.BOARD, problems, notes)
    check_models(stem, problems, notes)
    check_stock(problems, notes)
    check_pmod(stem, problems, notes)
    check_pages(stem, problems, notes)
    check_codes(problems, notes)
    for n in notes:
        print(f"  ok   {n}")
    for p in problems:
        print(f"  FAIL {p}")
    print(f"\n{'ALL FAB CHECKS PASSED' if not problems else str(len(problems)) + ' PROBLEM(S)'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
