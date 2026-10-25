# AMOD and RF-MOD: boards of analog and RF building blocks

Three 100 x 100 mm boards of "tiles" for an FPGA with fast converters (the ECP5-2ADC-2DAC board, or an Icepi Zero
with its AD9280/AD9708 module).  Each tile is one circuit with its own SMA jacks: cable a DAC to its input and its
output to an ADC, and compare the measurement with the expected result printed beside it.  The silkscreen draws every
tile's wiring as it is laid in copper.  The tutorial they serve is `icepi-zero-dac-adc/tutorial/`, whose Appendix D
specified them.

Rev A, 2026-10-25.  Designed by Claude with Jason Gallicchio, not yet ordered.

| board | what | tiles | layers | parts per board |
|---|---|---|---|---|
| [AMOD-P](docs/HANDBOOK_amod_p.md) | passive: pads, RC and LC filters, resonators, a crystal, a clipper, a delay line, LEDs, an AM loopstick | 13 | 2 | $16.97 |
| [AMOD-A](docs/HANDBOOK_amod_a.md) | active on USB-C: gain blocks, an HF LNA, Johnson noise, a one-pin ADC, a 4046 PLL, heat, a mixer, light, ultrasound, audio | 12 | 4 | $50.90 |
| [RF-MOD](docs/HANDBOOK_rf_mod.md) | 915 MHz and 2.4 GHz: a splitter, two filters, two gain blocks, two mixers, two synthesizers, power and a 25 MHz reference | 10 | 4 | $55.78 |
| [Icepi adapter](icepi_adapter/README.md) | the tutorial's 2x12 Icepi Zero adapter with a Pmod socket | | 4 | hand-soldered |

<p><img src="docs/images/amod_p-render-top.png" width="32%"> <img src="docs/images/amod_a-render-top.png" width="32%"> <img src="docs/images/rf_mod-render-top.png" width="32%"></p>

## Where things are

- `PLAN.md`: every decision with its reason, the tile tables as built, the parts and their stock on the day.
- `docs/HANDBOOK_*.md`: each tile, what to cable, what to expect, its Pmod lines.
- `docs/KIT.md`: what a bench needs beside the boards, with prices and links.
- `docs/DOA_*.md`: the assumptions to confirm before ordering; `docs/REVIEW_BRIEF.md`: the brief for a design review.
- `docs/MANUFACTURING.md`: how to order each board at JLCPCB with the files in `out/<board>/`.
- `CLAUDE_CODE_CHAT.md`: every prompt and response of the design session.
- `boards/<board>.py`: each tile's netlist, placement and wires, the one source the schematic and the board are
  generated from; `scripts/`: the generators and checks; `hardware/`: the KiCad 10 files they write.

## Building

KiCad 10 (the AppImage is found by `scripts/kienv.py`) and Python 3:

```
./make.py                     # all three boards: libraries, schematic + ERC, board + DRC, fab files and checks, docs
./make.py --board rf_mod      # one board
./make.py --board amod_a --stage sch --stage pcb
```

A build stops at the first failed gate: ERC, the schematic against the tiles' netlist, DRC, or a fab check (gerbers,
3D models, BOM and placement files, every LCSC code against JLCPCB's description and stock, every Pmod pad against the
Pmod standard).

## License

Open hardware and open source: `LICENSE` says which licence covers what (the hardware is CERN-OHL-P-2.0,
`LICENSE-HARDWARE.txt`).
