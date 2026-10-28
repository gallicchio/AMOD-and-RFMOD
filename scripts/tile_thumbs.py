#!/usr/bin/env python3
"""A picture of each tile for the handbook: render the board's top at 25 px/mm, find the board in the picture and cut
out each tile's frame with a little margin, as docs/images/tiles/<stem>_<id>.jpg (JPEG: a render compresses badly as PNG).

    python3 scripts/tile_thumbs.py rf_mod            # after the pcb stage (needs out/rf_mod_tiles.json)
    python3 scripts/tile_thumbs.py rf_mod --only R5  # one tile, for a look at its silk
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import kienv
from PIL import Image

BOARD = 100.0
PX, PY = 2700, 2700            # the render: the board fills about 2500 px of it
MARGIN = 0.9                   # mm round each tile, so its frame and the names by its edge show
SCALE = 15.0                   # px/mm in the thumbnails: a cell is 300 px


def render(stem, path):
    pcb = os.path.join(ROOT, "hardware", stem + ".kicad_pcb")
    kienv.cli("pcb", "render", "--width", str(PX), "--height", str(PY), "--quality", "basic", "--background", "opaque",
              "--side", "top", "-o", path, pcb)


def board_box(img):
    """The board's extent in the render: the columns and rows that hold solder-mask green."""
    w, h = img.size
    small = img.resize((w // 4, h // 4))
    px = small.load()
    xs, ys = [], []
    for y in range(small.size[1]):
        for x in range(small.size[0]):
            r, g, b = px[x, y][:3]
            if g > r + 12 and g > b + 4 and g < 110:
                xs.append(x); ys.append(y)
    return min(xs) * 4, min(ys) * 4, (max(xs) + 1) * 4, (max(ys) + 1) * 4


def main():
    stem = sys.argv[1]
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    meta = json.load(open(os.path.join(ROOT, "out", stem + "_tiles.json")))
    tmp = os.path.join(ROOT, "out", stem + "-render-thumbs.png")
    render(stem, tmp)
    img = Image.open(tmp).convert("RGB")
    x0, y0, x1, y1 = board_box(img)
    sx, sy = (x1 - x0) / BOARD, (y1 - y0) / BOARD
    outdir = os.path.join(ROOT, "docs", "images", "tiles")
    os.makedirs(outdir, exist_ok=True)
    made = []
    for t in meta["tiles"]:
        if only and t["id"] != only:
            continue
        box = (x0 + (t["x0"] - MARGIN) * sx, y0 + (t["y0"] - MARGIN) * sy,
               x0 + (t["x0"] + t["w"] + MARGIN) * sx, y0 + (t["y0"] + t["h"] + MARGIN) * sy)
        crop = img.crop(tuple(int(round(v)) for v in box))
        wmm, hmm = t["w"] + 2 * MARGIN, t["h"] + 2 * MARGIN
        crop = crop.resize((int(wmm * SCALE), int(hmm * SCALE)), Image.LANCZOS)
        path = os.path.join(outdir, "%s_%s.jpg" % (stem, t["id"]))
        crop.save(path, quality=88, optimize=True)
        made.append(path)
    os.remove(tmp)
    print("  %d tile pictures in %s (board at %.1f px/mm in the render)" % (len(made), os.path.relpath(outdir, ROOT), sx))


if __name__ == "__main__":
    main()
