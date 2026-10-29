"""The tile grid: every board is 100 x 100 mm, 4 x 4 cells of 20 mm with 1.5 mm gutters and 7.75 mm
margins (the geometry of Appendix D's sketches), y down from the top-left corner.

A tile occupies one or more cells in a row.  Its jacks sit in "slots": INSET from the cell's
edges at any corner, and, for a two-cell tile, at the middle of its top and bottom edges.  Every
pair of slots on a board is then at least 11.0 mm apart whatever the neighbours do (adjacent
corners of a cell: 20 - 2 x 4.75 = 10.5 ... the TL/TR pair of one cell is 10.5 mm; see below),
which `check_spacing` asserts for the actual jacks a board fits.

    corner slots   TL (4.75, 4.75)  TR (W - 4.75, 4.75)  BL (4.75, 15.25)  BR (W - 4.75, 15.25)
    middle slots   TM (W / 2, 4.75)  BM (W / 2, 15.25)            (W = the tile's width)

Within one cell TL and TR are 10.5 mm apart; across a gutter two facing corners are 11.0; a middle
slot is 16 mm from its own corners.  The SMA body (6.5 mm square) stays 1.5 mm inside the cell.
"""
import math

BOARD = 100.0
T, GAP, M0 = 20.0, 1.5, 7.75          # cell, gutter, margin to the first cell
INSET = 4.75                           # jack centre from the cell's edge
JACK_BODY = 6.5                        # BWSMA-KE-Z001 body, square
MIN_JACK_SPACING = 14.3                # rev A after Prompt 12: every jack at a cell's top-left or bottom-right corner (the
                                       # checkerboard: 14.85 within a cell, 15.2 across a gutter); a few by hand at 14.4
HOLES = [(4.0, 4.0), (BOARD - 4.0, 4.0), (4.0, BOARD - 4.0), (BOARD - 4.0, BOARD - 4.0)]
CORNER_R = 3.0


def cell_origin(c, r):
    """Top-left corner of cell (c, r), board mm."""
    return (M0 + c * (T + GAP), M0 + r * (T + GAP))


def tile_frame(cells):
    """(x0, y0, w, h) of a tile that spans `cells` (a list of (c, r)): contiguous cells in one row, or a full rectangle
    of them (AMOD-B's gimbal motor sits on 2 x 2, Prompt 19), the gutters between them part of the tile."""
    cs = sorted({c for c, r in cells})
    rs = sorted({r for c, r in cells})
    assert cs == list(range(cs[0], cs[0] + len(cs))), "a tile's cells are contiguous: %r" % (cells,)
    assert rs == list(range(rs[0], rs[0] + len(rs))), "a tile's rows are contiguous: %r" % (cells,)
    assert len(set(cells)) == len(cs) * len(rs), "a tile of several rows is a full rectangle: %r" % (cells,)
    x0, y0 = cell_origin(cs[0], rs[0])
    w = len(cs) * T + (len(cs) - 1) * GAP
    h = len(rs) * T + (len(rs) - 1) * GAP
    return x0, y0, w, h


def slot(cells, name):
    """Local (x, y) of a jack slot in a tile's frame."""
    x0, y0, w, h = tile_frame(cells)
    named = {"TL": (INSET, INSET), "TR": (w - INSET, INSET), "BL": (INSET, h - INSET),
             "BR": (w - INSET, h - INSET), "TM": (w / 2, INSET), "BM": (w / 2, h - INSET),
             "TMr": (w / 2 + 3.75, INSET),          # a two-cell tile's middle jack moved right, clear of the tile above-left's BR
             "TLo": (INSET - 0.5, INSET - 0.5),     # the diagonal pair 0.5 mm further out (P8: room for a crystal across it)
             "BRo": (w - INSET + 0.5, h - INSET + 0.5)}
    if name in named:
        return named[name]
    # the checkerboard slots of a multi-cell tile: TLk / BRk are cell k's top-left and bottom-right corners (k from 0)
    k = int(name[2:])
    assert name[:2] in ("TL", "BR") and 0 <= k < len(cells), name
    assert len({r for c, r in cells}) == 1, "numbered slots are for a tile in one row: %r" % (cells,)
    x0 = k * (T + GAP)
    return (x0 + INSET, INSET) if name[:2] == "TL" else (x0 + T - INSET, h - INSET)


def check_spacing(jacks, minimum=MIN_JACK_SPACING):
    """jacks: [(name, x, y)] board mm.  Returns the offending pairs (empty when fine)."""
    bad = []
    for i in range(len(jacks)):
        for j in range(i + 1, len(jacks)):
            d = math.hypot(jacks[i][1] - jacks[j][1], jacks[i][2] - jacks[j][2])
            if d < minimum - 1e-6:
                bad.append((jacks[i][0], jacks[j][0], round(d, 2)))
    return bad


if __name__ == "__main__":
    for r in range(4):
        print("  ".join("(%d,%d) at %5.2f,%5.2f" % (c, r, *cell_origin(c, r)) for c in range(4)))
    # the worst case: every corner of every cell filled
    J = []
    for r in range(4):
        for c in range(4):
            for s in ("TL", "TR", "BL", "BR"):
                x0, y0 = cell_origin(c, r)
                sx, sy = slot([(c, r)], s)
                J.append(("%d%d%s" % (c, r, s), x0 + sx, y0 + sy))
    bad = check_spacing(J)
    print(len(J), "slots; pairs under %.1f mm: %d" % (MIN_JACK_SPACING, len(bad)))
    dmin = min(math.hypot(a[1] - b[1], a[2] - b[2]) for i, a in enumerate(J) for b in J[i + 1:])
    print("closest pair %.2f mm" % dmin)
