# The student kit: what the boards need that is on none of them

Everything machine-placed is on the boards.  This is what one bench needs beside the ECP5-2ADC-2DAC board and one
each of AMOD-P, AMOD-A and RF-MOD, read from the tiles' own declarations.  Every product was chosen in stock and
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
| 1/4 W resistor kit, 20 values 0 ohm-1 M, 500 pieces | A5 | 1 | [SparkFun COM-10969](https://www.sparkfun.com/resistor-kit-1-4w-500-total.html) | $9.95 | "in stock" but cart says backorder | page |
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
- **The cable ties** come singly from Digi-Key; a 100-pack is about $19.46 at Newark (snippet).

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

## For the Icepi Zero instead of the ECP5 board

The adapter in `icepi_adapter/` needs a 2 x 20 female socket, a 2 x 12 male header and a 2 x 6 right-angle female
socket (LCSC C22373932, or any 2.54 mm one), all hand-soldered.  It also needs the AD9280/AD9708 module it carries,
and the Pmod cable and gender changer above.
