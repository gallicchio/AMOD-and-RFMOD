# The rev A bring-up, from the bench PC

The procedure is [`../BRINGUP.md`](../BRINGUP.md); **where we are is [`STATUS.md`](STATUS.md)**.  This folder is the
tool that runs it and the record it keeps.

| file | what |
|---|---|
| [`STATUS.md`](STATUS.md) | the board on the bench, what is cabled, what passed, **the next card**.  Rewritten after every step |
| [`VISITS.md`](VISITS.md), `cards/` | every visit of every board: its cables, what to set, what is measured, what passes, and a picture.  Written by `run.py plan` |
| `BRINGUP_LOG.md` | one row per number judged, as it happened |
| [`REVB.md`](REVB.md) | what rev B should change, each row with what showed it |
| `state.json` | the tool's memory (which steps are done); in git, so a new session knows where the last one stopped |
| `bench.json` | which instruments this bring-up may use (addresses, serial numbers); written with nothing assigned the first time; not in git |
| `data/` | raw readings, a JSON file per test; not in git |
| `tiles.py` | **every test of every tile**: the jacks, the stimulus, the model, the limits.  The one place to change a number |
| `engine.py` | the words tiles.py is written in (models, measurements, checks) and the packing of tests into visits |
| `measure.py` | how each kind of test is run: stepped-sine sweeps with a fit at each frequency, captures with the scope ranged to the signal, DC tables, sequences with the Pmod host, analyzer sweeps |
| `bench.py` | the instruments, through `~/mudd/lab-instrument-control`'s drivers; nothing is opened that `bench.json` does not name |
| `sim.py` | a simulated bench (each tile is its own model; an 8-bit scope, noise, a supply, a host) and faults to inject |
| `run.py` | the command line: `status`, `card`, `go`, `power`, `cal`, `done`, `bench`, `off`, `plan`, `list` |
| `pictures.py` | the cards' pictures, drawn from the boards' own geometry (`../out/<board>_tiles.json`) |
| `test_bringup.py` | `python3 -m pytest bringup/`: the whole plan against the simulated bench |

## How the pieces talk

```
 bench PC  --LAN or USB-->  SDG1032X generator (G1, G2)        --BNC-SMA-->   a tile's input jacks
           --LAN or USB-->  SDS2104X Plus scope (S1-S4)        <--SMA-BNC--   a tile's output jacks
           --USB-RS232-->   E3646A supply, output 1 (PWR)      --USB-C lead-> the board's USB-C: 5.0 V, its current read back
           --USB-C-->       ECP5-2ADC-2DAC (HOST), pmodbench   --Pmod A-->    the board's Pmod plug: clocks, SPI, bits
           --Prologix-->    8720ES network analyzer (P1, P2)   --SMA-->       the RF tiles' jacks
           --USB-->         DSA875 spectrum analyzer (SA)      <--SMA--       a synthesizer's or a mixer's output
```

## Setting up (once)

1. `python3 bringup/run.py bench` writes `bench.json` with every instrument unassigned and lists them.  Fill in the ones
   this bring-up may use: a `host` (LAN address) or `usb_serial` for the generator, scope and spectrum analyzer; the
   supply's `/dev/serial/by-id/...` path (find it with `python3 ~/mudd/lab-instrument-control/scpi_link.py identify`,
   which only asks `*IDN?`); the analyzer's GPIB address and the Prologix adapter's port; `"port": "auto"` for the host.
   Run `bench` again: each should answer with its name.
2. `python3 bringup/run.py cal` with G1 joined to S1 and G2 to S2.
3. `python3 bringup/run.py board amod_p 1`, then `status`.

## A day at the bench, as commands

```
run.py status                 # where we are; the next card
run.py done P.inspect "all as drawn; photos in ~/Pictures/amod_p_1"
run.py done P.setup
run.py go P.v1                # after "P.v1 cabled"
run.py go P.hands1 --only "DIP 1"       # a hands sitting, one part at a time
run.py power amod_a           # the power stage (stay for the walk)
run.py go A.v1 --sim          # rehearse a visit on the simulated bench; --fault gain:a2:0.5 breaks it on purpose
run.py revb "a3's corner read 0.9 MHz, not 1.4"
run.py off                    # generators off, host released, supply off
```

A failed check prints `!!` beside the number with its limits.  Before believing it: the card's cables again (a loose
SMA is the usual dead tile), then `go` once more; then it goes into `REVB.md` with the visit and the number.

## Changing the plan

Edit `tiles.py` (a limit, a model, a new test), then `python3 -m pytest bringup/` and `python3 bringup/run.py plan`:
the cards, `VISITS.md` and `BRINGUP.md`'s table are rewritten from it, and a jack that does not exist on the board, a
visit that needs more channels than the bench has, or a host call the driver does not have fails the tests.
