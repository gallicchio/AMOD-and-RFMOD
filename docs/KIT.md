# The student kit: what the boards need that is on none of them

Everything machine-placed is on the boards.  This is what one bench needs beside the ECP5-2ADC-2DAC board and one
each of AMOD-P, AMOD-A and RF-MOD, read from the tiles' own declarations; what the second-level boards (PhMOD and
RF-MOD-2) add is in its own section at the end.  Every product was chosen in stock and
shipping to a US address on **2026-10-25**.  "Page" means the price and stock were read on the vendor's product page
that day.  "Snippet" means the vendor's page would not load for a script (Digi-Key and Mouser block them) and the
figure came from a search result: check it before ordering.

**About $650 a bench at single-unit prices**, before shipping and tax.  The SMA cables are $270 of it; cheaper
generic RG316 cables exist and were not checked.

## Power

| item | qty | product | unit price | stock as read | source |
|---|---|---|---|---|---|
| USB-C supply, fixed 5.1 V 3 A | 3 | [Raspberry Pi 5.1 V 3 A USB-C supply, Adafruit 4298](https://www.adafruit.com/product/4298) | $8.74 | in stock | page |
| USB-C cable, 1 m, 5 A e-marked | 3 | [Adafruit 4199](https://www.adafruit.com/product/4199) | $9.95 | in stock | page |

One supply per powered board (the ECP5 board, AMOD-A, RF-MOD); AMOD-P needs none.  A fixed 5 V supply suits the
boards: their USB-C inputs have only the 5.1 k CC pull-downs and negotiate nothing.  Multi-port USB-PD chargers share
their 5 V between ports and some throttle a port that has not negotiated (Anker documents cutting one to 5 W), so
they were not chosen.  AMOD-A and RF-MOD draw up to 1.5 A each, the ECP5 board about 0.7 A.  The Pi supply has its
cable attached; the separate cables are for supplies or chargers you already have.

## Cables and adapters (SMA, 50 ohm)

| item | qty | product | unit price | stock as read | source |
|---|---|---|---|---|---|
| SMA male-male, RG316, 15 cm | 6 | [Amphenol RF 135101-01-06.00 at RF Parts](https://www.rfparts.com/135101-01-06.html) | $17.90 | in stock (no count) | page |
| SMA male-male, RG316, 30 cm | 6 | [Amphenol RF 135101-01-12.00 at RF Parts](https://www.rfparts.com/135101-01-12.html) | $16.90 | in stock (no count) | page |
| SMA male-male, 0.086 in Hand-Flex, 91 cm | 2 | [Mini-Circuits 086-36SM+](https://www.minicircuits.com/WebStore/dashboard.html?model=086-36SM%2B) | $30.92 | 943 | page |
| SMA male to BNC female, DC-2 GHz | 4 | [Mini-Circuits SM-BF50+](https://www.minicircuits.com/WebStore/dashboard.html?model=SM-BF50%2B) | $8.74 | over 1,000 | page |
| SMA male 50 ohm terminator, 1 W | 2 | [Mini-Circuits ANNE-50+](https://www.minicircuits.com/WebStore/dashboard.html?model=ANNE-50%2B) | $14.84 | over 1,000 | page |
| SMA attenuator 10 dB, male-female, DC-6 GHz, 1.7 W | 2 | [Mini-Circuits VAT-10A+](https://www.minicircuits.com/WebStore/dashboard.html?model=VAT-10A%2B) | $21.07 | over 1,000 | page |
| SMA attenuator 20 dB, male-female, DC-6 GHz, 0.8 W | 1 | [Mini-Circuits VAT-20A+](https://www.minicircuits.com/WebStore/dashboard.html?model=VAT-20A%2B) | $21.07 | over 1,000 | page |
| SMA female-female barrel | 2 | [Mini-Circuits SF-SF50+](https://www.minicircuits.com/WebStore/dashboard.html?model=SF-SF50%2B) | $7.05 | over 1,000 | page |
| Pmod 2 x 6 cable, 15 cm, female both ends | 1 | [Digilent 240-109 at Digi-Key](https://www.digikey.com/en/products/detail/digilent-inc/240-109/4090168) | $3.99 | about 127 | snippet |

- **The attenuators:** a synthesizer gives up to +5 dBm and a GALI-84+ wants 0 dBm or less at its input, so put
  10 dB between them.  The 20 dB pad goes between a gain block's output and a mixer or the ADC.
- **The Pmod cable** is only for the Icepi Zero adapter, whose socket stands about 11 mm higher than an AMOD board's
  plug.  It is female at both ends, so the adapter's female socket also needs a 2 x 6 male-male gender changer
  (Digilent's "Pmod Cable Kit: 2x6-pin", 240-021-2, includes them; no US price was found).
- **The Mini-Circuits items** (the long cables, adapters, terminators, attenuators and barrels) go on one order.  Its
  own Hand-Flex 086-6SM+ ($16.67) and 086-12SM+ ($20.55), both over 1,000 in stock (page), would put the short
  cables there too.

## Antennas (RF-MOD)

| item | qty | product | unit price | stock as read | source |
|---|---|---|---|---|---|
| 2.4 GHz, 2 dBi, SMA male, stubby, tilts 0-90 degrees | 2 | [L-com LCANRBD1044](https://www.l-com.com/2.4-ghz-2.5-ghz-stubby-antenna-monopole-90-degree-angle-sma-male-connector-2-dbi-gain-lcanrbd1044) | $15.89 | 50 | page |
| 862-928 MHz, 3 dBi, SMA male, tilt-swivel, 136 mm | 2 | [L-com LCANRBD1057](https://www.l-com.com/862-928-mhz-rubber-duck-antenna-3-dbi-sma-male-tilt-swivel-lcanrbd1057) | $16.69 | 100 | page |

Both pages state standard polarity, SMA male.  Most Wi-Fi antennas are **RP-SMA** and will not mate with these
jacks.  A quarter-wave monopole made from a jack and 31 mm (2.4 GHz) or 78 mm (915 MHz) of wire also works.

## Parts that plug into the tiles

| item | tile | qty | product | unit price | stock as read | source |
|---|---|---|---|---|---|---|
| 40 kHz transmitter, 16 mm, leads 10.0 mm apart | A11 | 1 | [PUI Audio UT-1640K-TT-2-R at Digi-Key](https://www.digikey.com/en/products/detail/pui-audio-inc/UT-1640K-TT-2-R/6071961) | $4.02 | 421 at Digi-Key (PUI's distributor table) | price snippet |
| 40 kHz receiver, the transmitter's pair | A11 | 1 | [PUI Audio UR-1640K-TT-2-R at Digi-Key](https://www.digikey.com/en/products/detail/pui-audio-inc/UR-1640K-TT-2-R/6071959) | $5.08 | 203 at Digi-Key (PUI's table) | price snippet |
| Speaker, 36 mm, 8 ohm, 2 W, wire leads | A12 | 1 | [Adafruit 6486](https://www.adafruit.com/product/6486) | $1.95 | 14 | page |
| Electret capsule, 9.7 mm, 2 pins at 2.54 mm | A12 | 1 | [SparkFun COM-08635](https://www.sparkfun.com/electret-microphone.html) | $1.50 | in stock | page |
| AM loopstick, 240 uH, 10 x 70 mm ferrite rod | P13 | 1 | [Atomic-29 240 uH loopstick coil](https://atomic-29.com/products/240uh-loopstick-antenna-coil) | $4.65 | add-to-cart, no count | page |
| Tuning capacitor, 365 pF single-section air variable, 1/4 inch shaft, and a knob (optional) | P13 | 1 | [Amplified Parts 365 pF variable capacitor](https://www.amplifiedparts.com/node/5317) | $30.95 (eBay listing of the same seller) | unverified (the pages refused a script) | search snippet |
| HB100 10.525 GHz Doppler module | A5 | 1 | [MH-ET Live HB100 X at Amazon, B07YY6FD4T](https://www.amazon.com/dp/B07YY6FD4T) | $13.76 | in stock | page |
| Cable ties, 2.5 x 99 mm | P13 | 2 | [Panduit PLT1M-C at Digi-Key](https://www.digikey.com/en/products/detail/panduit-corp/PLT1M-C/280033) | about $0.25 | not shown | snippet |

- **The transducers** plug into pins 1 and 5 of A11's 1 x 5 sockets.  Those pins are 10.16 mm apart and the leads
  10.0 mm, so the leads flex in.
- **The speaker:** the PAM8302A gives about 1.5 W into 8 ohm, inside the speaker's 2 W.  Only 14 were in stock;
  Adafruit's 40 mm 4 ohm (3968) was out of stock.
- **The electret's** datasheet gives a 680 ohm load, 2.2 k maximum.  A12 biases it through 2.2 k from 5 V: inside the
  rating, at its top.  Pin 1 of the socket is the + side.
- **The loopstick** is the nearest one verified in stock, and it is off the plan: 240 uH, not 330, and no tap.  It
  tunes P13 about 17 % higher than the silkscreen says, roughly 470 kHz to 1.5 MHz, still the AM band.  Leave the
  terminal's tap pin empty.  A 350 uH coil with a 10 uH secondary on a 10 x 60 mm rod is listed on Amazon (ASIN
  B0BPQM9P79), but its page did not load: price and stock unverified.
- **The tuning capacitor** is optional: P13's switches tune the band in 15 steps without it.  Its two leads go in the
  VAR C terminal, frame (rotor) to GND so a hand on the knob does not detune it.  With the switches off, 365 pF tunes
  the kit's 240 uH coil from about 540 kHz to 2 MHz; with a switch on it tunes between that switch's steps.  Any AM
  tuning capacitor of 200-400 pF does (a polyvaricon's two AM sections in parallel are about 200 pF).
- **The cable ties** come singly from Digi-Key; a 100-pack is about $19.46 at Newark (snippet).
- **The HB100** has no distributor listing in the US; Amazon is the only source found (also B0DYYP5X1K, $12.17).  Modules
  differ in pin order ("+5V GND IF" or "IF GND +5V"): A5's header is +5 V, IF, ground on jumper wires, so wire it to the
  module's own print (`DOA_amod_a.md` item 1).  Check the photos for the bare three-pin module, not one on a carrier
  board with its own amplifier.  (Rev A's first A5 needed a resistor kit for Johnson noise; the host has that source.)

## Mechanical

| item | qty | product | unit price | stock as read | source |
|---|---|---|---|---|---|
| Rubber bumper feet, 8 mm, about 4 mm tall, pack of 4 | 2 packs | [Adafruit 550](https://www.adafruit.com/product/550) | $0.95 | in stock | page |
| M3 nylon screw and standoff set (20 x 10 mm standoffs, 120 screws) | 1 per 5 benches | [Adafruit 4685](https://www.adafruit.com/product/4685) | $16.95 | 62 | page |

- **The feet** go on AMOD-A and RF-MOD (circled on the back); the standoffs go in AMOD-P's four holes.
- **Heights:** the 4 mm feet put AMOD-A or RF-MOD's Pmod plug at the ECP5 board's socket only if that board stands
  about as high.  Otherwise use the Pmod cable.
- **3M SJ5302 feet** (7.9 x 2.2 mm) are closer to the 2-3 mm planned; Digi-Key's stock for them was unclear.

## Measuring

| item | qty | product | unit price | stock as read | source |
|---|---|---|---|---|---|
| BNC male to minigrabber lead, 91 cm | 2 | [Pomona 5187-C-36 at Digi-Key](https://www.digikey.com/en/products/detail/pomona-electronics/5187-C-36/737180) | $34.99 | 295-472 | snippet |

These are for the RH-5019 test loops, straight into a scope input.  A 10x probe with its own hook tip does the same.
Pomona's 3788 is BNC **female** and needs a BNC cable.  The long-cable experiments' coax is in the tutorial's
Appendix D, "Long cables".

## For the second-level boards (PhMOD and RF-MOD-2)

Read on 2026-10-25 as above.  Thorlabs' prices and US-warehouse stock came from its store's own product data;
Remington's from its store's options service.  Several items are per lab rather than per bench (marked).

### PhMOD: NMR and ESR

| item | tile | qty | product | unit price | stock as read | source |
|---|---|---|---|---|---|---|
| SMA male 50 ohm termination, 2 W, DC-18 GHz | Y2 | 1 | [Mini-Circuits TERM-2W-183S+](https://www.minicircuits.com/WebStore/dashboard.html?model=TERM-2W-183S%2B) | $55.00 | over 1,000 | page |
| N52 cube, 12.7 mm (1/2 in), Ni-Cu-Ni | Y3's magnet | 16 (32 for two rings) | [K&J Magnetics B888-N52](https://www.kjmagnetics.com/b888-n52-neodymium-block-magnet) | $5.74 at 10-24 | in stock (no count) | page |
| Magnet wire, 26 AWG, solderable, 1 lb (1,280 ft) | Y3, Y4, Y6 coils | 1 | [Remington Industries 26SNSP](https://www.remingtonindustries.com/magnet-wire/magnet-wire-26-awg-enameled-copper-9-spool-sizes/) | $27.71 | in stock (no count) | page |
| Film trimmer, 2.5-22 pF, 250 V, through-hole | Y3's probe | 4 | [Vishay BFC280811229 at Digi-Key](https://www.digikey.com/en/products/detail/vishay-beyschlag-draloric-bc-components/BFC280811229/3028987) | $7.46 | 730 | snippet |
| DPPH, 95 %, 1 g (per lab) | Y7 / Y4 ESR | 1 | [Thermo Scientific 044150.03](https://www.thermofisher.com/order/catalog/product/044150.03) | $125.65 (list $148.00) | add-to-cart, no count | page |
| Supply, 3-12 V adjustable, 5 A, 2.1 mm plug | Y4 | 1 | [Adafruit 4880](https://www.adafruit.com/product/4880) | $17.50 | 56 | page |
| 2.1 mm jack to screw terminals | Y4 | 1 | [Adafruit 368](https://www.adafruit.com/product/368) | $2.00 | in stock | page |

- **The termination:** Y2's pulses (1 W at under 10 % duty) average 0.1 W, so the kit's 1 W ANNE-50+ copes; the 2 W
  part is margin for a mistake left on.  A cheaper 2 W one: ShowMeCables SMTR1001 (DC-1 GHz), $23.39, 4 in stock.
- **The wire:** the 4 oz spool ($13.49) covers the probe, a Helmholtz pair and a gradient coil, not the Earth's-field
  coils (a 12 ohm polarizing coil is about 90 m, a 1,000-turn receive coil about 300 m).
- **The trimmer** stops at 22 pF: add fixed C0G capacitors beside it.  Passive Plus PPXE27000 (3.5-27 pF, 200 V) is
  $14.17 (snippet).
- **DPPH** is sold to institutional accounts only (Sigma-Aldrich D9132, 1 g, $151, snippet); one gram lasts years.
- **The magnet:** NdFeB drifts about 0.12 % per kelvin, about 20 kHz per kelvin at 17 MHz: track the Larmor frequency
  or hold the temperature.  Each cube pulls 23 lb: build the ring in a jig, wear eye protection, keep pacemakers away.

### PhMOD: radio

| item | tile | qty | product | unit price | stock as read | source |
|---|---|---|---|---|---|---|
| SMA low-pass, DC-32 MHz | Y5 to the ADCs | 2 | [Mini-Circuits SLP-30+](https://www.minicircuits.com/WebStore/dashboard.html?model=SLP-30%2B) | $52.10 | 173 | page |
| Active HF loop, MLA-30 type, USB bias box | Y5's IN A / IN B | 1 (2 for bearings) | [HAON MLA-30 at Amazon, B085ZSXF8Z](https://www.amazon.com/dp/B085ZSXF8Z) | $43.99 | in stock | page |
| WWVB 60 kHz ferrite rod, 60 x 10 mm | Y6 | 1 | [Universal-Solder 60 kHz antenna, SKU 26996](https://www.universal-solder.ca/product/loopstick-antenna-60khz-for-atomic-clock-receiver/) | $3.54 | in stock (no count) | page |
| Loop amplifier kit, 20 kHz-55 MHz (optional; you build the loop) | Y5 or Y6 | 1 | [LZ1AQ AAA-1C](https://active-antenna.eu/amplifier-kit/) | EUR 112 ex VAT | in stock | page |

- **The low-pass's** corner sits at the 65 MS/s Nyquist: under 1 dB to 32 MHz, but only 20 dB from 47 MHz, so 33-47 MHz
  folds back partly suppressed.  SLP-21.4+ is cleaner below 21 MHz but had none in stock.
- **The MLA-30** is an HF loop: its listing claims 100 kHz-30 MHz at best, so it is not for 24 or 60 kHz.  For VLF, wind
  the handbook's loop (a 1 m square of 10 turns of hookup wire) or use the ferrite rod into Y6; a small capacitor across
  the rod (tens of pF) tunes it to 60 kHz.

### Lasers and atoms (Y10, RF-MOD-2's X9)

| item | tile | qty | product | unit price | stock as read | source |
|---|---|---|---|---|---|---|
| 795 nm single-mode VCSEL, 0.25 mW, TO-46 | Y10 | 1 | [Thorlabs L795VH1](https://www.thorlabs.com/item/L795VH1) | $176.20 | 33 | page |
| 650 nm laser diode, 7 mW | Y10 | 1-2 | [Thorlabs L650P007](https://www.thorlabs.com/item/L650P007) | $20.17 | 92 | page |
| Laser diode socket, 5.6 / 9 mm | Y10 | 2 | [Thorlabs S7060R](https://www.thorlabs.com/item/S7060R) | $7.49 | 2,018 | page |
| Rb vapor cell, natural abundance, 25 x 75 mm (per lab) | Y10 | 1 | [Thorlabs GC25075-RB](https://www.thorlabs.com/item/GC25075-RB) | $615.39 | 11 | page |
| NV diamond, Element Six DNV-B14, 3 x 3 x 0.5 mm (per lab) | X9 | 1 | [Thorlabs DNVB14](https://www.thorlabs.com/item/DNVB14) | $4,091.98 | 19 | page |
| 532 nm module, 4.5 mW, Class 3R | X9 | 1 | [Thorlabs CPS532](https://www.thorlabs.com/item/CPS532) | $202.10 | 2 | page |

- **Protect the VCSEL.**  It runs at 1.2-1.5 mA (threshold 0.5 mA), and Y10 gives 100 mA per volt: 15 mV of SET is its
  whole operating current.  Put 30 dB of SMA attenuation on SET (the kit's VAT-10A+ and VAT-20A+ in series; SET is
  terminated in 50 ohm, so the pads work as designed): the DAC's full scale is then about 3 mA.
- **No laser mount reaches 3.4 GHz at a sane price** (Thorlabs' TCLDM9 and LM9LP stop at 0.5-1 GHz and cost $491-597).
  Y10 has its own bias-T: solder the VCSEL with the shortest leads to an SMA plug on the LD jack; use the socket for the
  650 nm diode and the L-I-V work.
- **The VCSEL's wavelength** spans 788-800 nm at 0.055 nm per kelvin: ask for a unit near 794.98 nm or plan to heat or
  cool it.  3.417 GHz sidebands address only Rb-87, 28 % of natural rubidium; the isotopically pure GC19075-RB87 is
  $1,171.18.  Heat the cell for optical depth.
- **The diamond** is the expensive item: DNVB1 (0.3 ppm NV) is $1,897.73 with none in US stock; Adamas quotes on request;
  Sigma's NV nanodiamond (798169, $508, snippet) gives a weaker, broader signal.  ODMR also needs a long-pass filter near
  600 nm and goggles (CPS532 is Class 3R); a 40 mW DPSS (DJ532-40, $227.52) needs more current than Y10 gives.

### RF-MOD-2

| item | tile | qty | product | unit price | stock as read | source |
|---|---|---|---|---|---|---|
| Amplifier, 0.7-3.5 GHz, +24 dBm, 12 V 0.54 A | X9's drive | 1 | [Mini-Circuits ZRL-3500+](https://www.minicircuits.com/WebStore/dashboard.html?model=ZRL-3500%2B) | $185.88 | 74 | page |
| SMA DC block, 0.1-8000 MHz | X8, Y10 | 2 | [Mini-Circuits BLK-89-S+](https://www.minicircuits.com/WebStore/dashboard.html?model=BLK-89-S%2B) | $20.26 | over 1,000 | page |
| Active GPS L1 antenna, 3-5 V, SMA | X8 | 1 | [Adafruit 960](https://www.adafruit.com/product/960) | $21.50 | in stock | page |

- **The amplifier** gives +24 dBm from about +7 dBm in (X3 through X1 at full scale); its input limit is +10 dBm.  The
  cheaper ZX60-V62+ ($92.90) gives +17.9 dBm at 3 GHz.  It runs from the same 12 V supply as Y4.  X9's termination
  then takes 0.25 W: the kit's 1 W ANNE-50+ copes.
- **The DC block** starts at 0.1 MHz: keep it out of the HF and VLF paths.  Put one between X8 and a passive antenna.
- **X5's calibration** wants an open, a short and a load on its OUT jack: the load is the kit's ANNE-50+ and the open a
  cable's bare end; only the short is missing.  NanoVNA SMA calibration sets (open, short, load; about $15) are sold on
  the marketplaces, but no listing was verified.  The same two terminators load whichever of R10's (or X3's) OUT A+ and
  OUT A- and of X5's FWD and REFL is unused.

**Rough totals:** about $860 a bench for the per-bench items above, plus the per-lab DPPH, rubidium cell and green
laser (about $940 together) and a diamond (DNVB14 $4,092, DNVB1 $1,898).

## For the Icepi Zero instead of the ECP5 board

The adapter in `icepi_adapter/` needs a 2 x 20 female socket, a 2 x 12 male header and a 2 x 6 right-angle female
socket (LCSC C22373932, or any 2.54 mm one), all hand-soldered.  It also needs the AD9280/AD9708 module it carries,
and the Pmod cable and gender changer above.
