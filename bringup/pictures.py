"""A picture for each visit: the board as it lies on the bench (USB-C on the right, the Pmod plug at the bottom),
every tile with the name it prints, every jack as a ring, and a coloured dot with the cable's name on each jack
this visit uses.  Drawn from out/<board>_tiles.json, so it is the board's own geometry."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                     # noqa: E402
from matplotlib.patches import Rectangle, Circle    # noqa: E402

import tiles as T                                   # noqa: E402

# one colour per kind of cable, the same in every picture (generator, scope, network analyzer, spectrum analyzer)
COLOUR = {"G": "#d55e00", "S": "#0072b2", "P": "#7b3294", "SA": "#009e73"}
WORD = {"G": "generator", "S": "scope", "P": "network analyzer", "SA": "spectrum analyzer"}


def card_png(stem, visit, path, geo, jack_info):
    b = T.BOARDS[stem]
    fig, ax = plt.subplots(figsize=(7.2, 7.9), dpi=110)
    ax.add_patch(Rectangle((0, 0), 100, 100, fc="#f3f6f1", ec="#333333", lw=1.5))
    used_tiles = {t for _, t, _, _ in visit.conns}
    for t in geo.values():
        on = t["id"] in used_tiles
        ax.add_patch(Rectangle((t["x0"], t["y0"]), t["w"], t["h"], fc="#ffffff" if on else "#e9ece7", ec="#222222" if on else "#9aa39a", lw=1.4 if on else 0.7))
        ax.text(t["x0"] + t["w"] / 2, t["y0"] + t["h"] / 2 - 1.0, t["id"], ha="center", va="center", fontsize=13 if on else 10,
                color="#111111" if on else "#8a8f8a", weight="bold")
        ax.text(t["x0"] + t["w"] / 2, t["y0"] + t["h"] / 2 + 2.6, t["name"], ha="center", va="center", fontsize=6.5, color="#333333" if on else "#8a8f8a")
        for j in t["jacks"]:
            ax.add_patch(Circle((t["x0"] + j["x"], t["y0"] + j["y"]), 2.1, fc="none", ec="#b08d2e" if on else "#c9c3ae", lw=1.0))
    pw = geo.get(b.get("power") or "")
    if pw:
        ax.add_patch(Rectangle((98.5, pw["y0"] + 5.5), 4.0, 9.0, fc="#bbbbbb", ec="#333333", lw=1.0))
        ax.text(104.0, pw["y0"] + 10, "USB-C", rotation=90, ha="left", va="center", fontsize=7)
    pm = geo.get(b.get("pmod") or "")
    if pm:
        ax.add_patch(Rectangle((pm["x0"] + 1.0, 99.0), 16.0, 4.5, fc="#444444", ec="#111111", lw=1.0))
        ax.text(pm["x0"] + 9.0, 105.3, "Pmod plug", ha="center", va="top", fontsize=7)
    legend = []
    for c, tile, jack, note in visit.conns:
        if c == "MOT":
            legend.append("MOT: supply output 2 on " + jack)
            continue
        if c == "HOST":
            if pm:
                ax.add_patch(Rectangle((pm["x0"] + 1.0, 99.0), 16.0, 4.5, fc="#e69f00", ec="#111111", lw=1.2))
            legend.append("HOST: Pmod plug into the ECP5-2ADC-2DAC rev A's Pmod A (rev A only: non-standard)")
            continue
        j = jack_info(stem, tile, jack)
        kind = "SA" if c == "SA" else c[0]
        ax.add_patch(Circle((j["x"], j["y"]), 3.3, fc=COLOUR[kind], ec="#111111", lw=1.0, zorder=5))
        ax.text(j["x"], j["y"], c, ha="center", va="center", fontsize=8, color="white", weight="bold", zorder=6)
        up = j["corner"].startswith("top")
        ax.text(j["x"], j["y"] + (-4.6 if up else 4.6), j["silk"], ha="center", va="bottom" if up else "top", fontsize=6.5, color="#111111", zorder=6,
                bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))
        load = " (50 ohm input)" if "50 ohm" in note else " (1 Mohm input)" if "1 Mohm" in note else ""
        legend.append("%s: %s%s on %s \"%s\"" % (c, WORD[kind] + (" CH" + c[1:] if kind in "GS" else " port " + c[1:] if kind == "P" else ""), load, tile, j["silk"]))
    ax.set_xlim(-3, 109); ax.set_ylim(133, -9)
    ax.set_aspect("equal"); ax.axis("off")
    ax.text(0, -4.5, "%s   %s (%s)" % (visit.id, b["name"], b["title"]), fontsize=12, weight="bold", va="center")
    y = 110.5
    for line in legend + ["first: " + x for _, x in visit.pre][:9]:
        ax.text(0, y, line if len(line) < 112 else line[:109] + "...", fontsize=7.2, va="top")
        y += 2.9
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
