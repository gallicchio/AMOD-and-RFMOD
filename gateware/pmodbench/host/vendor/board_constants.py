"""The two board constants the vendored max2871_regs.py imports (in CostasLink's repository this file is
generated from that board's budget).  The values are the same on the tile boards: RF-MOD's r10 and IQ-MOD's
q3 are "MAX2871 as CostasLink built it" (boards/rf_mod.py, synth_tile: RSET 5.1 k, CP = 7, ICP 2.56 mA)."""
RSET_OHM = 5100.0    # the MAX2871's RSET
CP_CODE = 7          # ICP = 1.63 / RSET x (1 + CP) = 2.56 mA
