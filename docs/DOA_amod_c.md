# AMOD-C: what could make it dead on arrival, and what to check before paying

Rev A, 2026-10-28 (Prompt 19).  Every item is a fact the design assumed that a datasheet, JLCPCB's placement preview or
the first bench test must confirm.  The ones under **Order gate** must be confirmed before the order is placed.
`scripts/check_rotations.py` fits JLCPCB's own drawing of every part onto its footprint: on 2026-10-28 it agreed with
the rotation table on all of AMOD-C's codes (209 across the boards, 0 differ) once AMOD-C's fifteen new codes were
added.  `scripts/check_pinouts.py` compares each symbol's pin names with EasyEDA's for the same code: it found the
DMMT3904W wrong (item 1), now fixed, and nothing else on this board.

## Order gate: pins, packages and polarity

1. **DMMT3904W (c9 Q903, c10 Q1002): 1 B2, 2 B1, 3 C1, 4 E1, 5 E2, 6 C2** (Diodes' drawing and EasyEDA's symbol agree).
   The first build gave it the BCM857BS's order (1 E1 ... 6 C1), which would have left both tiles dead; both pairs are
   now turned 180 on the board and rewired.  CPL 0 (board 180, JLCPCB's drawing KiCad's turned 180).  In the preview
   the pin-1 mark sits at the bottom-right corner as the board shows it.  The BCM857BS (c9's mirror, Q902) is 1 E1,
   2 B1, 3 C2, 4 E2, 5 B2, 6 C1, as its symbol says.
2. **SOT-23 family at +180** (JLCPCB's "-BR" drawings): every AO3401A switch FET, the AO3400A (c2), the MMBT3904s, the
   BAT54S (c12: 1 A1, 2 K2, 3 the joint), the TLV3501, TLV62568, TPS7A2033, 74LVC1G79, 74LVC1G3157 and the LM2664.
   The OPA810 is "-TL" (0 more than the board).  The SC-70-5 parts differ: the SN74LV1T34 is +180, the TLV3201 +270.
3. **SOIC, MSOP and TSSOP at +270** (pins in rows on JLCPCB's drawings): TLC555, ICL7660A, OPA2810, LF398 (SOIC-14),
   OPA2197 and MAX7410 (MSOP-8), TMUX4053 (TSSOP-16).  A half turn on any of these puts the supply on a signal pin.
4. **The 1 x 2 header (c10, J1003)**: +270 with JLCPCB's origin between its pins (as AMOD-A's sockets).  Through-hole:
   JLCPCB solders it.
5. **The Pmod plug (c9's margin)**: `check_pmod` maps every pad to the Pmod standard; pins 6 and 12 (the host's 3.3 V)
   are joined to each other and nothing else; 5 and 11 ground.  IO1 c6 clock, IO2 c8 bit, IO3 c4 clock, IO4 and IO8
   c5's phases, IO5 c7's track, IO6 c3's clock, IO7 c6's bit.
6. **TMUX4053 (c5)**: EN is active low (tied to ground); SELx high connects SxB to Dx (TI's Table 9-3): phi1 high puts
   IN on the capacitor's top plate, phi2 high puts its bottom plate on the summing node.
7. **TLV3501 (c6)**: SOT-23-6 is 1 -IN, 2 V-, 3 +IN, 4 V+, 5 OUT, 6 SHDN (TI's Pin Functions); SHDN grounded runs it.
8. **LF398 (c7)**: SOIC-14 1 IN, 3 V-, 7 OUT, 8 Ch, 10 LOGIC REF (ground), 11 LOGIC (IO5), 12 V+; 14 (offset) open.
9. **ICL7660A (c3)**: driven at OSC (pin 7) through 1 k from a 5 V buffer, as Intersil allows for an outside clock; LV
   (pin 6) open, as required above 3.5 V; BOOST (pin 1) open.
10. **MAX7410 (c4)**: 1 COM, 2 IN, 3 GND, 4 VDD, 5 OUT, 6 OS (on COM), 7 SHDN (high: on), 8 CLK (from the buffer, 5 V).
    134 in stock at JLCPCB on 2026-10-28: enough for a few boards; the order should not wait.
11. **TLV3201 (c8)**: the stocked part is the automotive TLV3201AQDCKRQ1 (SC-70-5: 1 OUT, 2 V-, 3 IN+, 4 IN-, 5 V+),
    1,279 in stock; the same die as the TLV3201.

## Bench, first power

12. USB-C in: c1's LEDs; +5 V, -5 V and +3.3 V on its socket.  The -5 V rail is 40 mA; the five +-5 V tiles together
    draw about 25 mA.
13. c2: BUCK~ shows a few mV of ripple at 1.5 MHz; the DC at the buck (a probe on its output capacitor) is 3.6 V with
    TRIM open, 4.2 V with TRIM at 0 V.  LOAD at 0.5 V draws 50 mA (0.5 V across the 10 ohm shunt).  LOAD only from 0 to
    1 V: it reaches the op amp through 1 k, so a negative swing is safe but does nothing.
14. c3: a 100 kHz square on IO6 (the pump at 50 kHz, Rout = 1 / (f C) + 60 = 80 ohm): about -4.6 V at the pump with
    its 1 k load, -0.81 V on OUT through its /5.7.  At 2 kHz on IO6 (Rout 1.06 k) it falls to about -2.4 V.
15. c4: 1 MHz on IO3 (corner 10 kHz): a 1 kHz sine on IN passes, 20 kHz is 30 dB down, 40 kHz 60 dB.
16. c5: two non-overlapping 100 kHz phases on IO4 and IO8 (R = 10 k): a 0.1 V step on IN ramps OUT at 1 V/ms.
17. c6: 1 MHz on IO1, IN open (0 V): IO7 is half ones; IN at +1 V: about 80 % ones (0.5 + 1/3.3).  INT1 and INT2 on a
    scope show the two integrators at about a quarter, offset 0.38 V.  Keep IN within +-1.5 V.
18. c7: a 1 kHz sine on IN, a 10 kHz pulse train on IO5: OUT is the sine sampled and held.
19. c8: IN at 0.5 V, DAC swept from -1 to +1 V: BIT on IO2 changes at DAC = 0.5 V.
20. c9: IN- at 0 V, IN+ swept +-0.2 V: OUT a tanh, +-1 V, its slope about -10 V/V at the middle.
21. c10: jumper on: about 2 MHz of bandwidth; parked: several times more.  The gain at 100 kHz about -3 into 50 ohm.
22. c11: OUT near 6.9 kHz; CV at +1 V lowers it.
23. c12: a 10 kHz sine of 1 V on IN: OUT is |IN|, 0 to 1 V, no flat spot at the crossings.

## What it is not

The board has not been built.  The numbers above are calculated (c6's swings simulated); c2's ripple, c10's
bandwidths and c7's droop depend on parts whose spread the datasheets give only loosely.  It needs gateware on the
host for c3-c8 (clocks, phases, a decimator, a SAR search): the tutorial's.
