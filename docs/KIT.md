# The student kit: what the boards need that is on none of them

Everything machine-placed is on the boards.  This is what a bench needs beside them, read from the tiles' own
declarations (2026-10-25).  Quantities are for one bench with the ECP5-2ADC-2DAC board and one of each AMOD board.

## Power

| item | why | how many |
|---|---|---|
| USB-C power supply, 5 V at 3 A per port (any USB-PD charger offers 5 V 3 A) | AMOD-A and RF-MOD each draw up to 1.5 A at 5 V (A12's class-D at full volume, A8's heater; RF-MOD's gain blocks through the 7.8 V boost and the synthesizers); the ECP5 board about 0.7 A | one port per powered board: three, or one multi-port charger whose 5 V ports each give 3 A at once |
| USB-C cables (C to C, or A to C from a 3 A source) | the same | three |

AMOD-P needs no power.

## Cables and adapters (SMA everywhere, 50 ohm)

| item | why | how many |
|---|---|---|
| SMA male-male cables, RG316, 15 cm (6 in) | tile to neighbouring tile | 6 |
| SMA male-male cables, RG316, 30 cm (12 in) | tile to the ECP5 board's jacks, across a board | 6 |
| SMA male-male cables, 1 m | to the oscilloscope, between two benches' RF-MOD boards | 2 |
| SMA male to BNC female adapters | the oscilloscope's inputs | 4 |
| SMA 50 ohm terminators (male) | an unused output, a calibration load | 2 |
| SMA attenuators, 10 dB and 20 dB (DC-6 GHz, male-female) | a synthesizer (up to +5 dBm) into a gain block (keep its input under 0 dBm); the gain block's +20 dBm into a mixer or the ADC | 2 x 10 dB, 1 x 20 dB |
| SMA female-female barrels | joining two cables | 2 |
| 2 x 6 Pmod extension cable, 15 cm | the Icepi Zero adapter (its socket stands about 11 mm above the Icepi), or any height mismatch | 1 |

## Antennas (RF-MOD)

| item | why | how many |
|---|---|---|
| 2.4 GHz whip, SMA **male** (centre pin), 2-3 dBi | on R5's OUT (transmit) and R12's IN (receive) | 2 per board |
| 915 MHz whip, SMA male, 2-3 dBi | the same at 915 MHz | 2 per board |

Most Wi-Fi antennas are **RP-SMA** (reverse polarity: a socket where SMA has a pin) and do not mate with these jacks.
Buy "SMA male" whips, or make a quarter-wave monopole from a jack and 31 mm (2.4 GHz) or 78 mm (915 MHz) of wire.

## Transducers and parts that plug into the tiles

| item | tile | fits |
|---|---|---|
| 40 kHz ultrasonic transducer pair, TCT40-16T and TCT40-16R (16 mm, 10 mm lead spacing) | AMOD-A A11 | pins 1 and 5 of each 1 x 5 socket (10.16 mm apart) |
| Speaker, 4-8 ohm, 1-3 W, 20-40 mm, with wire leads | AMOD-A A12 | the 2-way screw terminal |
| Electret microphone capsule, 2 pin, 6-10 mm, with leads (for example CUI CMA-6542PF) | AMOD-A A12 | the 1 x 2 socket, pin 1 the + side |
| Ferrite-rod AM antenna coil, about 330 uH, 50-100 mm, with a tap | AMOD-P P13 | the 3-way screw terminal (ends and tap), held by a cable tie through the two slots |
| A few 1/4 W through-hole resistors, 100 ohm to 1 M | AMOD-A A5 (Johnson noise) | the 1 x 2 socket |
| Small cable ties, 2.5 mm wide | AMOD-P P13 | the slots |

## Mechanical

| item | why | how many |
|---|---|---|
| Stick-on rubber feet, 8 mm (3M SJ5303 class) | AMOD-A and RF-MOD have no mounting holes; the four places are circled on the back | 8 |
| M3 standoffs and screws, or the same feet | AMOD-P's four holes | 4 |
| Feet or standoffs matching the ECP5 board's height | an AMOD board's Pmod plug mates only when the two boards stand level; otherwise use the extension cable | as needed |

## For the Icepi Zero instead of the ECP5 board

The adapter in `icepi_adapter/` (hand-soldered: a 2 x 20 female socket, a 2 x 12 male header, a 2 x 6 right-angle
female socket), the AD9280/AD9708 module it carries, and the Pmod extension cable above.

## Measuring

An oscilloscope with BNC inputs (the SMA-BNC adapters above) and probes with mini-grabber or hook tips for the RH-5019
test loops.  The long-cable experiments' coax is listed in the tutorial's Appendix D, "Long cables".
