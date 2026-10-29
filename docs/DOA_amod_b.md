# AMOD-B: what could make it dead on arrival, and what to check before paying

Rev A, 2026-10-28 (Prompt 19).  Every item is a fact the design assumed that a datasheet, JLCPCB's placement preview or
the first bench test must confirm.  The ones under **Order gate** must be confirmed before the order is placed.
`scripts/check_rotations.py` fits JLCPCB's own drawing of every part onto its footprint: on 2026-10-28 it agreed with
the rotation table on all 56 of AMOD-B's codes once the board's five new codes were added.  `scripts/check_pinouts.py`
compares each symbol's pin names with EasyEDA's for the same code: on this board every difference is a naming one
(KiCad's "+" and "-" against IN+ and IN-, the DRV8311H's ~{SLEEP} against nSLEEP, the LSM6DSO's SPC and SDI against
SCL and SDA, the INA240's pin 4 that EasyEDA calls NC and the board grounds), and each was read against the maker's
pin table.

## Order gate: pins, packages and polarity

1. **DRV8311H (b3), WQFN-24 3 x 3 mm, 0.4 mm pitch**: CPL 0.  Its pads are fourfold symmetric, so its turn comes from
   JLCPCB's pad numbers: in the preview pin 1 (nFAULT) must sit at the corner the board's dot marks; the driver is
   turned 90 on the board, VM and the outputs facing right.  TI's table: 1 nFAULT, 2 CSAREF, 3-5 SOC SOB SOA, 6 CP,
   7 VIN_AVDD, 8 VM, 9 PGND, 10-12 OUTA OUTB OUTC, 13-15 INHC INHB INHA, 16 AGND, 17 AVDD, 18-20 INLA INLB INLC,
   21 GAIN, 22 SLEW, 23 MODE, 24 nSLEEP, the pad PGND.
2. **The DRV8311H's straps, all left open (Hi-Z)**: MODE Hi-Z is 3x PWM with the 9 A trip (TI table 8-2 and the IOCP
   row), SLEW Hi-Z 180 V/us, GAIN Hi-Z 1 V/A about CSAREF / 2 (linear 0.25 V from either rail: +-1.4 A).  In 3x PWM each INHx sets its phase high
   or low and INLx low floats it (table 8-4): the three INL pins are EN, from COAST's comparator.  nSLEEP is 4.5 V
   from the tile's 5 V (10 k / 100 k), under its 5.5 V maximum.  nFAULT is left open (TI suggests 5.1 k to AVDD).
3. **MT6701 (b5), SOP-8 at +270, turned 180 on the board**: 1 VDD, 2 MODE (open: its 200 k pull-up; MagnTek's SSI
   and I2C reference circuits leave it so, which the datasheet does not say in words), 3 OUT, 4 GND, 5 PUSH (open),
   6 DO, 7 CLK, 8 CSN.  DO is push-pull and does not let go with CSN high, so it reaches MISO only through b6's
   74LVC1G125, enabled by CS ENC.
4. **LSM6DSO (b6), LGA-14 at 0**: its pads are symmetric under a half turn: pin 1 (SDO, MISO) by the preview's dot.
   SPI: 12 CS, 13 SCL, 14 SDA (MOSI), 1 SDO (MISO); 2 and 3 (the auxiliary I2C) and 6, 7 on ground; 4 INT1 open (ST:
   "INT1 must be set to '0' or left unconnected during power-on if the I2C/SPI interfaces are used"), 9 INT2, 10
   OCS_Aux, 11 SDO_Aux open.
5. **SN74LVC1G125 (b6), SOT-23-5 at +270**: JLCPCB draws it a quarter turn from KiCad (rms 0.02 mm), unlike the
   OPA810's SOT-23-5.  1 /OE, 2 A, 3 GND, 4 Y, 5 VCC.
6. **INA240A1 (b11) and the OPA2171 (b4), SOIC-8 at +270**: as the other SOIC-8s.  The INA240: 1 IN-, 2 GND, 3 REF2,
   4 NC (grounded), 5 OUT, 6 VS, 7 REF1, 8 IN+; IN- on the driver's side of the shunt, so IPA is positive for current
   into the motor.
7. **SOT-23 family**: +180 for the AO3401A switches, the DRV5055A3 halls, the TLV3501 (b3) and the LM2664; 0 for the
   OPA810s and the INA181A1 (b12).  QRE1113GR (b5) on KiCad's OnSemi_CASE100CY: +270, the sensor facing up.
8. **The motor's slots (b5)**: four NPTH slots 3.4 x 7.4 mm, 4.3-11.7 mm from the centre: check them in the drill
   file (an oval drill each), and that the motor's base holes meet them (the 2804's pattern is not published; the
   slots cover 12, 14 x 14 and 16 / 19 mm).
9. **The Pmod plug (b3's margin)**: `check_pmod` maps every pad to the Pmod standard; IO1 INHB, IO2 INHC, IO5 INHA,
   IO3 MISO, IO4 SCK, IO6 CS ENC, IO7 MOSI, IO8 CS IMU.  Pins 6 and 12 (the host's 3.3 V) join only each other.
10. **The screw terminals** (b3's motor, b8's piezo) and the DC-005 jack (b2) are through-hole: JLCPCB solders them.

## Bench, first power

11. USB-C alone: b1's LEDs; +5 V, -5 V, +3.3 V on its socket.  The -5 V rail's load is about 30 mA (seven OPA810s,
    the OPA2171, b3's level shifts, b9's sensor) of the LM2664's 40 mA: measure it.
12. b2: VMOT about 4.6 V on USB alone (VM 0.29 V); the barrel jack at 12 V, VM 0.73 V; the SMBJ12A must not conduct
    below about 13 V.  The 100 nF capacitors on VMB are 16 V parts: keep the supply at 12 V or less.
13. b3 with COAST high (all phases floating) and the motor on the terminal: switch on; nothing turns.  COAST low and
    INHA, INHB, INHC held at fixed levels: the motor locks to a step.  IA and IB read 0 V (within about 30 mV: the
    3.3 k / 10 k shift's tolerance against AVDD and -5 V) with no current.
14. b5: the MT6701 answers over SSI (24 clocks, CRC good); b7's ANG ramps once a turn as the shaft is turned by hand;
    b10's HA and HB swing as the rotor passes the halls (if they stay flat, the rotor's magnets are too high: lower the
    motor's spacers); b9's IDX pulses at a white mark.
15. b6: the LSM6DSO's WHO_AM_I (0x6C) over SPI with CS IMU low and CS ENC high; then the encoder with CS ENC low and
    CS IMU high: the two must never be low together.
16. b4: COAST high, spin the motor by hand: EA and EB show two sinusoids 120 degrees apart, a few hundred millivolts.
17. b11 and b12: IPA and I near 0 with the motor stopped; a stalled motor at 12 V draws about 1.2 A (10 ohm): IPA
    reaches 1.2 V, I up to 1.2 V.

## What is new and untried on these boards

- A brushless driver run directly from FPGA lines (3x PWM), its phases floated by a DAC through a comparator.
- A gimbal motor screwed over its own sensors: a magnetic encoder, two halls and an optical index on one tile.
- The encoder's push-pull DO shared with an IMU's MISO through a buffer; the SPI lines in nested lanes up the gutter.
- The +3.3 V pour on L3 bridged over the gimbal's side slots (they cut its strip), so the encoder's via reaches it.
