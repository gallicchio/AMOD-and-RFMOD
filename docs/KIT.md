# The student kit: what the boards need that is on none of them

Everything machine-placed is on the boards.  This is what one bench needs beside the ECP5-2ADC-2DAC board and one
each of AMOD-P, AMOD-N, AMOD-A and RF-MOD, read from the tiles' own declarations; what AMOD-C and the two motor boards
(AMOD-M and AMOD-B, read on 2026-10-28) and the second-level boards (PhMOD and IQ-MOD) add is in their own sections
toward the end.  Every product was chosen in stock and
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
| 40 kHz transmitter, 16 mm, leads 10.0 mm apart | a11 | 1 | [PUI Audio UT-1640K-TT-2-R at Digi-Key](https://www.digikey.com/en/products/detail/pui-audio-inc/UT-1640K-TT-2-R/6071961) | $4.02 | 421 at Digi-Key (PUI's distributor table) | price snippet |
| 40 kHz receiver, the transmitter's pair | a11 | 1 | [PUI Audio UR-1640K-TT-2-R at Digi-Key](https://www.digikey.com/en/products/detail/pui-audio-inc/UR-1640K-TT-2-R/6071959) | $5.08 | 203 at Digi-Key (PUI's table) | price snippet |
| Speaker, 36 mm, 8 ohm, 2 W, wire leads | a12 | 1 | [Adafruit 6486](https://www.adafruit.com/product/6486) | $1.95 | 14 | page |
| Electret capsule, 9.7 mm, 2 pins at 2.54 mm | a12 | 1 | [SparkFun COM-08635](https://www.sparkfun.com/electret-microphone.html) | $1.50 | in stock | page |
| AM loopstick, 240 uH, 10 x 70 mm ferrite rod | p13 | 1 | [Atomic-29 240 uH loopstick coil](https://atomic-29.com/products/240uh-loopstick-antenna-coil) | $4.65 | add-to-cart, no count | page |
| Tuning capacitor, 365 pF single-section air variable, 1/4 inch shaft, and a knob (optional) | p13 | 1 | [Amplified Parts 365 pF variable capacitor](https://www.amplifiedparts.com/node/5317) | $30.95 (eBay listing of the same seller) | unverified (the pages refused a script) | search snippet |
| HB100 10.525 GHz Doppler module | a5 | 1 | [MH-ET Live HB100 X at Amazon, B07YY6FD4T](https://www.amazon.com/dp/B07YY6FD4T) | $13.76 | in stock | page |
| Cable ties, 2.5 x 99 mm | p13 | 2 | [Panduit PLT1M-C at Digi-Key](https://www.digikey.com/en/products/detail/panduit-corp/PLT1M-C/280033) | about $0.25 | not shown | snippet |

- **The transducers** plug into pins 1 and 5 of a11's 1 x 5 sockets.  Those pins are 10.16 mm apart and the leads
  10.0 mm, so the leads flex in.
- **The speaker:** the PAM8302A gives about 1.5 W into 8 ohm, inside the speaker's 2 W.  Only 14 were in stock;
  Adafruit's 40 mm 4 ohm (3968) was out of stock.  On 2026-10-28 the 6486 was out of stock too, as were Adafruit's
  8 ohm 1 W mini ovals (3923, 4227).  The 3 in 8 ohm 1 W speaker of the motors section (Adafruit 1313) does for a12
  with the volume kept down (1 W against the amplifier's 1.5 W).
- **The electret's** datasheet gives a 680 ohm load, 2.2 k maximum.  a12 biases it through 2.2 k from 5 V: inside the
  rating, at its top.  Pin 1 of the socket is the + side.
- **The loopstick** is the nearest one verified in stock, and it is off the plan: 240 uH, not 330, and no tap.  It
  tunes p13 about 17 % higher than the silkscreen says, roughly 470 kHz to 1.5 MHz, still the AM band.  Leave the
  terminal's tap pin empty.  A 350 uH coil with a 10 uH secondary on a 10 x 60 mm rod is listed on Amazon (ASIN
  B0BPQM9P79), but its page did not load: price and stock unverified.
- **The tuning capacitor** is optional: p13's switches tune the band in 15 steps without it.  Its two leads go in the
  VAR C terminal, frame (rotor) to GND so a hand on the knob does not detune it.  With the switches off, 365 pF tunes
  the kit's 240 uH coil from about 540 kHz to 2 MHz; with a switch on it tunes between that switch's steps.  Any AM
  tuning capacitor of 200-400 pF does (a polyvaricon's two AM sections in parallel are about 200 pF).
- **The cable ties** come singly from Digi-Key; a 100-pack is about $19.46 at Newark (snippet).
- **The HB100** has no distributor listing in the US; Amazon is the only source found (also B0DYYP5X1K, $12.17).  Modules
  differ in pin order ("+5V GND IF" or "IF GND +5V"): a5's header is +5 V, IF, ground on jumper wires, so wire it to the
  module's own print (`DOA_amod_a.md` item 1).  Check the photos for the bare three-pin module, not one on a carrier
  board with its own amplifier.  (Rev A's first a5 needed a resistor kit for Johnson noise; the host has that source.)

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

## AMOD-N (the second passive board)

Nothing new to buy: its tiles use what is above and below.

- **n8 and n9** run on the host's 3.3 V through AMOD-N's own Pmod plug, n8 even when it is set by hand on its
  switch.  Plug the board into the host's Pmod; when
  another board holds it, the 2 x 6 cable above with a 2 x 6 male-male changer does the job (the Icepi adapter's
  arrangement).
- **n7's DC** comes from a bench supply's clip leads on its DC and GND loops: PhMOD's adjustable supply below, with
  its 2.1 mm jack-to-terminals adapter, does it.
- **n10's dipole:** the SMA-to-BNC adapter and the BNC-to-minigrabber lead above put the dipole's two halves on OUT's pin
  and shell.
- **n1** is the calibration set for board-level work with a NanoVNA or IQ-MOD's reflectometer.

## AMOD-C (the conversion board)

Nothing new to buy beyond a third USB-C supply for its power tile c1 (or one moved from another board): its tiles
take a DAC or the FPGA's lines in and give an ADC something out.

## Motors and actuators (AMOD-M and AMOD-B)

Read on **2026-10-28**, "page" and "snippet" as above, for one bench with one AMOD-M and one AMOD-B.  Each board's power
tile (m1, b1) takes a 5 V USB-C supply as AMOD-A's does (Power, above): one more each, or one moved between boards.

| item | tile | qty | product | unit price | stock as read | source |
|---|---|---|---|---|---|---|
| Motor supply, 3-12 V adjustable, 5 A, 5.5 / 2.1 mm plug, centre positive | m2, b2 | 1 | [Adafruit 4880](https://www.adafruit.com/product/4880) | $17.50 | 44 | page (polarity: snippet) |
| DC gearmotor, N20, 6 V, 1:100, magnetic hall encoder (14 counts a motor turn, 3-5 V) | m3 | 1 | [Adafruit 4639](https://www.adafruit.com/product/4639) | $12.50 | in stock | page |
| Stepper, NEMA 17, bipolar, 200 steps, 12 V 350 mA, 35 ohm a winding | m4 | 1 | [Adafruit 324](https://www.adafruit.com/product/324) | $14.00 | in stock | page |
| Micro servo, TowerPro SG92R, 3-6 V | m5 | 1 | [Adafruit 169](https://www.adafruit.com/product/169) | $5.95 | in stock | page |
| Push-pull solenoid, 12 V, 40 ohm (about 0.3 A), 5.5 mm throw | m6 | 1 | [Adafruit 412](https://www.adafruit.com/product/412) | $7.50 | in stock | page |
| Speaker, 3 in, 8 ohm, 1 W | m7 | 1 | [Adafruit 1313](https://www.adafruit.com/product/1313) | $1.95 | in stock | page |
| NdFeB disc, 4.76 x 1.59 mm, N52, axial | m9 | 4 | [K&J Magnetics D31-N52](https://www.kjmagnetics.com/proddetail.asp?prod=D31-N52) | $0.24 | in stock (no count) | page |
| Load cell, 5 kg straight bar (TAL220B), 1.0 mV/V, 200 mm leads | m11 | 1 | [SparkFun SEN-14729](https://www.sparkfun.com/load-cell-5kg-straight-bar-tal220b.html) | $15.50 | in stock | page |
| Jumper cap, 2-pin, 2.54 mm | m6 | 3 | [SparkFun PRT-09044](https://www.sparkfun.com/jumper-2-pin.html) | $0.10 | in stock | page |
| JST PH 6-way cable pair, 2.0 mm, 20 cm | m3 | 1 | [Adafruit 5090](https://www.adafruit.com/product/5090) | $0.95 | in stock | page |
| JST XH 4-way cable pair, 2.5 mm, 20 cm | m4, m11 | 2 | [Adafruit 4874](https://www.adafruit.com/product/4874) | $0.95 | in stock | page |
| Gimbal motor GBM2804H-100T, 12N14P, 10 ohm, hollow shaft 7 mm outside | b5 | 1 | [iFlight GBM2804H-100T](https://shop.iflight.com/ipower-gimbal-brushless-motor-gbm2804h-100t-pro218) | $18.99 | in stock (no count) | page |
| Diametric NdFeB disc, 6.00 x 2.50 mm, N35 | b5 | 3 | [Radial Magnets 8995 at Digi-Key](https://www.digikey.com/en/products/detail/radial-magnets-inc/8995/5126077) | about $0.24 | 4,709-19,991 on Digi-Key's regional sites | snippet |
| Piezo element, 30 mm, enclosed, mounting holes, wires attached | b8 | 1 | [Adafruit 1739](https://www.adafruit.com/product/1739) | $0.95 | in stock | page |

**About $100 a bench for this section** at single-unit prices, or about $82 where the bench already has PhMOD's
Adafruit 4880; before shipping and tax, from five vendors (Adafruit, SparkFun, K&J, Digi-Key, iFlight).

- **The supply** goes from 3 to 12 V, inside m2's 5-16 V and b2's 5-12 V.  12 V for the stepper and the solenoid; about
  6 V for the N20 (6 V nominal) and for m7 with the 8 ohm speaker (m7's back: "8 ohm at 5-6 V").  Digi-Key's and
  Jameco's listings give it as centre positive; Adafruit's page does not say.  It is PhMOD's h4 supply: a bench that
  has one needs no second.  Not Adafruit 5130 (3-24 V): it passes AMOD-B's 12 V and AMOD-M's 16 V.  No fixed 12 V
  2 A adapter was in stock on 2026-10-28 (Pololu 1471, 1774, 1468 and Adafruit 352 out of stock; Bel/CUI's at
  Digi-Key 25 weeks).
- **The N20's encoder:** the datasheet Adafruit links (Chihai CHF-GM12-N20VA) prints the encoder board's pins M1, GND,
  C1, C2, VCC, M2: m3's PH order (1 M1, 2 GND, 3 A, 4 B, 5 3.3 V, 6 M2); if the count runs backwards, swap A and B in
  the gateware.  The encoder has its own 3.3 k pull-ups.  Its plug is narrower than a PH (it fits inside the motor's
  12.2 mm), so **make the lead**: cut the free end off Adafruit's harness and solder it to the half of the 5090 pair
  that mates m3's header, pin 1 to pin 1, going by the encoder board's printed labels.  From 12 V keep the duty under
  about 50 % (the motor is rated 4.5-6 V).  No encoder motor with a confirmed 2.0 mm PH plug was found (DFRobot's
  FIT0521 has m3's pin order on a cable of unstated series; Pololu's use a 1.0 mm SH plug).
- **The stepper's** coils are red and yellow (A), green and brown or gray (B): solder them to an XH half of a 4874,
  red to pin 1 (A+), yellow 2 (A-), green 3 (B+), brown or gray 4 (B-).  35 ohm at 12 V is 0.34 A, under m4's 1 A
  limit.  Reversing one coil reverses the direction.
- **The servo:** m5's header is S, +5 V, GND; the orange wire on S.
- **The solenoid** draws 0.3 A at 12 V.  Adafruit's 5 V solenoid (2776, 4.5 ohm) would draw 2.7 A at 12 V: only
  with the supply at 5-6 V.
- **The speaker:** m7 puts 4 x IN across it, +-4 V full scale, 1 W into 8 ohm at its rating; solder two wires for the
  terminal.  No 30 ohm speaker for m7 at 12 V was in stock.
- **The hall magnet:** a D31 gives 410 mT at its face against the DRV5055A3's +-85 mT: hold it a few millimetres above
  the sensor.  Turning it over changes the sign.
- **The load cell's** colours match m11's XH: red E+ to pin 1, black E- to 2, white S- to 3, green S+ to 4, on an XH
  half of a 4874.  1.0 mV/V at 5 V gives 5 mV at 5 kg, about 1 V after m11's gain of 201.
- **The cable pairs** are inline plug and socket: only one half mates the board's header.  Check before soldering.
- **The gimbal motor's** leads are 300 mm of 28 AWG with no plug: twist and tin each and put them straight into b3's
  3-way terminal (thin for a 5 mm terminal: fold the stripped end over once).  The phase order does not matter:
  swapping two reverses the motor, and the electrical-angle calibration takes up the offset.  iFlight's page does not
  say where it ships from; no US distributor stocks it (Robot Pi Shop lists it at $21.99, snippet).
- **The motor's screws:** iFlight answers "M2" for the base; users of other 2804s report M3, and the base pattern is
  not published.  Measure the motor, then screw it through b5's slots with spacers or washers that put the magnet
  0.5-2 mm over the MT6701 (about 1 mm).  Not priced.
- **The diametric magnet** (6 mm) is wider than the motor's 5 mm bore: glue it centred on the end of the 7 mm shaft
  that faces the board.  K&J's D42DIA-N52 (6.35 x 3.17 mm, $0.60, page) is the alternate; give it a little more gap.
- **The piezo element** screws or tapes to the motor's mount; its two wires go in b8's terminal (either way round: the
  sign flips).  A bare 27 mm brass disc with leads (Murata 7BB-27-4L0) is more sensitive but was not found in US stock.
- **Alternates** (read 2026-10-28): stepper SparkFun ROB-09238 (12 V 0.33 A, $26.95, page; pair its coils with an
  ohmmeter); gearmotor DFRobot FIT0521 (25 mm, 6 V, 34:1, $19.90, page; stalls at 3.2 A, m3 limits at 2 A); voice
  coil Adafruit 1674 bone-conductor transducer (8 ohm, 1 W, $8.95, page); load cell Adafruit 4541 (5 kg, $3.95, page;
  colours unstated); hall magnet K&J D4H1 (6.35 x 2.54 mm, $0.35, page).

## For the second-level boards (PhMOD and IQ-MOD)

Read on 2026-10-25 as above.  Thorlabs' prices and US-warehouse stock came from its store's own product data;
Remington's from its store's options service.  Several items are per lab rather than per bench (marked).

### PhMOD: NMR and ESR

| item | tile | qty | product | unit price | stock as read | source |
|---|---|---|---|---|---|---|
| SMA male 50 ohm termination, 2 W, DC-18 GHz | h2 | 1 | [Mini-Circuits TERM-2W-183S+](https://www.minicircuits.com/WebStore/dashboard.html?model=TERM-2W-183S%2B) | $55.00 | over 1,000 | page |
| N52 cube, 12.7 mm (1/2 in), Ni-Cu-Ni | h3's magnet | 16 (32 for two rings) | [K&J Magnetics B888-N52](https://www.kjmagnetics.com/b888-n52-neodymium-block-magnet) | $5.74 at 10-24 | in stock (no count) | page |
| Magnet wire, 26 AWG, solderable, 1 lb (1,280 ft) | h3, h4, h6 coils | 1 | [Remington Industries 26SNSP](https://www.remingtonindustries.com/magnet-wire/magnet-wire-26-awg-enameled-copper-9-spool-sizes/) | $27.71 | in stock (no count) | page |
| Film trimmer, 2.5-22 pF, 250 V, through-hole | h3's probe | 4 | [Vishay BFC280811229 at Digi-Key](https://www.digikey.com/en/products/detail/vishay-beyschlag-draloric-bc-components/BFC280811229/3028987) | $7.46 | 730 | snippet |
| DPPH, 95 %, 1 g (per lab) | h7 / h4 ESR | 1 | [Thermo Scientific 044150.03](https://www.thermofisher.com/order/catalog/product/044150.03) | $125.65 (list $148.00) | add-to-cart, no count | page |
| Supply, 3-12 V adjustable, 5 A, 2.1 mm plug | h4 | 1 | [Adafruit 4880](https://www.adafruit.com/product/4880) | $17.50 | 56 | page |
| 2.1 mm jack to screw terminals | h4 | 1 | [Adafruit 368](https://www.adafruit.com/product/368) | $2.00 | in stock | page |

- **The termination:** h2's pulses (1 W at under 10 % duty) average 0.1 W, so the kit's 1 W ANNE-50+ copes; the 2 W
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
| SMA low-pass, DC-32 MHz | h5 to the ADCs | 2 | [Mini-Circuits SLP-30+](https://www.minicircuits.com/WebStore/dashboard.html?model=SLP-30%2B) | $52.10 | 173 | page |
| Active HF loop, MLA-30 type, USB bias box | h5's IN A / IN B | 1 (2 for bearings) | [HAON MLA-30 at Amazon, B085ZSXF8Z](https://www.amazon.com/dp/B085ZSXF8Z) | $43.99 | in stock | page |
| WWVB 60 kHz ferrite rod, 60 x 10 mm | h6 | 1 | [Universal-Solder 60 kHz antenna, SKU 26996](https://www.universal-solder.ca/product/loopstick-antenna-60khz-for-atomic-clock-receiver/) | $3.54 | in stock (no count) | page |
| Loop amplifier kit, 20 kHz-55 MHz (optional; you build the loop) | h5 or h6 | 1 | [LZ1AQ AAA-1C](https://active-antenna.eu/amplifier-kit/) | EUR 112 ex VAT | in stock | page |

- **The low-pass's** corner sits at the 65 MS/s Nyquist: under 1 dB to 32 MHz, but only 20 dB from 47 MHz, so 33-47 MHz
  folds back partly suppressed.  SLP-21.4+ is cleaner below 21 MHz but had none in stock.
- **The MLA-30** is an HF loop: its listing claims 100 kHz-30 MHz at best, so it is not for 24 or 60 kHz.  For VLF, wind
  the handbook's loop (a 1 m square of 10 turns of hookup wire) or use the ferrite rod into h6; a small capacitor across
  the rod (tens of pF) tunes it to 60 kHz.

### Lasers and atoms (h10, IQ-MOD's q9)

| item | tile | qty | product | unit price | stock as read | source |
|---|---|---|---|---|---|---|
| 795 nm single-mode VCSEL, 0.25 mW, TO-46 | h10 | 1 | [Thorlabs L795VH1](https://www.thorlabs.com/item/L795VH1) | $176.20 | 33 | page |
| 650 nm laser diode, 7 mW | h10 | 1-2 | [Thorlabs L650P007](https://www.thorlabs.com/item/L650P007) | $20.17 | 92 | page |
| Laser diode socket, 5.6 / 9 mm | h10 | 2 | [Thorlabs S7060R](https://www.thorlabs.com/item/S7060R) | $7.49 | 2,018 | page |
| Rb vapor cell, natural abundance, 25 x 75 mm (per lab) | h10 | 1 | [Thorlabs GC25075-RB](https://www.thorlabs.com/item/GC25075-RB) | $615.39 | 11 | page |
| NV diamond, Element Six DNV-B14, 3 x 3 x 0.5 mm (per lab) | q9 | 1 | [Thorlabs DNVB14](https://www.thorlabs.com/item/DNVB14) | $4,091.98 | 19 | page |
| 532 nm module, 4.5 mW, Class 3R | q9 | 1 | [Thorlabs CPS532](https://www.thorlabs.com/item/CPS532) | $202.10 | 2 | page |

- **Protect the VCSEL.**  It runs at 1.2-1.5 mA (threshold 0.5 mA), and h10 gives 100 mA per volt: 15 mV of SET is its
  whole operating current.  Put 30 dB of SMA attenuation on SET (the kit's VAT-10A+ and VAT-20A+ in series; SET is
  terminated in 50 ohm, so the pads work as designed): the DAC's full scale is then about 3 mA.
- **No laser mount reaches 3.4 GHz at a sane price** (Thorlabs' TCLDM9 and LM9LP stop at 0.5-1 GHz and cost $491-597).
  h10 has its own bias-T: solder the VCSEL with the shortest leads to an SMA plug on the LD jack; use the socket for the
  650 nm diode and the L-I-V work.
- **The VCSEL's wavelength** spans 788-800 nm at 0.055 nm per kelvin: ask for a unit near 794.98 nm or plan to heat or
  cool it.  3.417 GHz sidebands address only Rb-87, 28 % of natural rubidium; the isotopically pure GC19075-RB87 is
  $1,171.18.  Heat the cell for optical depth.
- **The diamond** is the expensive item: DNVB1 (0.3 ppm NV) is $1,897.73 with none in US stock; Adamas quotes on request;
  Sigma's NV nanodiamond (798169, $508, snippet) gives a weaker, broader signal.  ODMR also needs a long-pass filter near
  600 nm and goggles (CPS532 is Class 3R); a 40 mW DPSS (DJ532-40, $227.52) needs more current than h10 gives.

### IQ-MOD

| item | tile | qty | product | unit price | stock as read | source |
|---|---|---|---|---|---|---|
| Amplifier, 0.7-3.5 GHz, +24 dBm, 12 V 0.54 A | q9's drive | 1 | [Mini-Circuits ZRL-3500+](https://www.minicircuits.com/WebStore/dashboard.html?model=ZRL-3500%2B) | $185.88 | 74 | page |
| SMA DC block, 0.1-8000 MHz | q8, h10 | 2 | [Mini-Circuits BLK-89-S+](https://www.minicircuits.com/WebStore/dashboard.html?model=BLK-89-S%2B) | $20.26 | over 1,000 | page |
| Active GPS L1 antenna, 3-5 V, SMA | q8 | 1 | [Adafruit 960](https://www.adafruit.com/product/960) | $21.50 | in stock | page |

- **The amplifier** gives +24 dBm from about +7 dBm in (q3 through q1 at full scale); its input limit is +10 dBm.  The
  cheaper ZX60-V62+ ($92.90) gives +17.9 dBm at 3 GHz.  It runs from the same 12 V supply as h4.  q9's termination
  then takes 0.25 W: the kit's 1 W ANNE-50+ copes.
- **The DC block** starts at 0.1 MHz: keep it out of the HF and VLF paths.  Put one between q8 and a passive antenna.
- **q5's calibration** wants an open, a short and a load: AMOD-N's n1 has all three and a thru (Prompt 17), and a
  calibration through a cable to it puts the reference plane at the board's surface, where every tile's pads are.  The
  same two terminators load whichever of r10's (or q3's) OUT A+ and
  OUT A- and of q5's FWD and REFL is unused.

**Rough totals:** about $860 a bench for the per-bench items above, plus the per-lab DPPH, rubidium cell and green
laser (about $940 together) and a diamond (DNVB14 $4,092, DNVB1 $1,898).

## For the Icepi Zero instead of the ECP5 board

The adapter in `icepi_adapter/` needs a 2 x 20 female socket, a 2 x 12 male header and a 2 x 6 right-angle female
socket (LCSC C22373932, or any 2.54 mm one), all hand-soldered.  It also needs the AD9280/AD9708 module it carries,
and the Pmod cable and gender changer above.
