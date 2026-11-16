#!/usr/bin/env python3
"""TRF3722 register words (RF-MOD r13), from TI's datasheet (datasheets/TRF3722IRGZR_C1850395.pdf, ZHCSCN0B).

The serial port (section 7.1): 32-bit words, LEAST significant bit first, read on CLK's rising edge; LE's
rising edge loads the register named by bits 4:0, which are 01000 + n for register n (Tables 5-15: ADDR<4:3>
is always 01).  Registers 1-6 are written; register 0 is read only.  A readback is a write to register 0
with bit 31 (RB_ENABLE) set and the register's number in bits 30:28 (Table 15); the first clock after that
LE is idle and the next 32 rising edges each put a bit on RDBK, LSB first, to be read at the falling edge.

Here: the field table (FIELDS), the reset values assembled from it (RESET, checked against the tables' reset
columns by hand), pack / unpack, the readback command, and a frequency plan after section 8.4.1 with the bias
settings of Table 16.  NOTHING here has run on a TRF3722: the plan follows the datasheet's own procedure and
reproduces its worked example (section 8.4.2: 1799.68 MHz from 61.44 MHz gives RDIV 24, NINT 703, PLL_DIV 2,
the 8/9 prescaler), but the datasheet gives no register write order and no start-up timing, so words() and
the order in which the driver sends them (1, 3, 4, 5, 6, then 2 with EN_CAL, so the calibration starts with
the dividers already set) are a best reading, not a proven recipe.

    python3 trf3722.py 915e6          prints the plan and the six words
"""
import math
import sys

ADDR_BASE = 0b01000
# name: (register, msb, lsb)
FIELDS = {
    'RDIV': (1, 17, 5), 'REF_INV': (1, 19, 19), 'NEG_VCO': (1, 20, 20), 'ICP': (1, 25, 21), 'ICPDOUBLE': (1, 26, 26), 'CAL_CLK_SEL': (1, 30, 27),
    'NINT': (2, 20, 5), 'PLL_DIV_SEL': (2, 22, 21), 'PRSC_SEL': (2, 23, 23), 'VCO_SEL': (2, 27, 26), 'VCO_SEL_MODE': (2, 28, 28),
    'CAL_ACC': (2, 30, 29), 'EN_CAL': (2, 31, 31),
    'NFRAC': (3, 29, 5),
    'PWD_PLL': (4, 5, 5), 'PWD_CP': (4, 6, 6), 'PWD_VCO': (4, 7, 7), 'PWD_VCO_MUX': (4, 8, 8), 'PWD_DIV124': (4, 9, 9), 'PWD_PRESC': (4, 10, 10),
    'RSV4_11': (4, 11, 11), 'PWD_OUTBUF': (4, 12, 12), 'PWD_LO_DIV': (4, 13, 13), 'PWD_TX_DIV': (4, 14, 14), 'PWD_MOD': (4, 15, 15),
    'EN_EXTVCO': (4, 16, 16), 'EN_ISOURCE': (4, 18, 18), 'LD_ANA_PREC': (4, 20, 19), 'CP_TRISTATE': (4, 22, 21), 'SPEEDUP': (4, 23, 23),
    'LD_DIG_PREC': (4, 24, 24), 'MOD_ORD': (4, 27, 25), 'DITH_SEL': (4, 28, 28), 'DEL_SD_CLK': (4, 30, 29), 'EN_FRAC_MODE': (4, 31, 31),
    'IB_MOD_GM': (5, 7, 6), 'IB_MOD_LO': (5, 9, 8), 'VCO_BIAS': (5, 13, 10), 'VCOBUF_BIAS': (5, 15, 14), 'VCOMUX_BIAS': (5, 17, 16),
    'OUTBUF_BIAS': (5, 19, 18), 'RSV5_21': (5, 21, 21), 'VCO_CAL_IB': (5, 22, 22), 'VCO_CAL_REF': (5, 25, 23), 'VCO_AMPL_CTRL': (5, 27, 26),
    'VCO_VB_CTRL': (5, 29, 28), 'EN_LD_ISOURCE': (5, 31, 31),
    'VCO_TRIM': (6, 12, 7), 'EN_LOCKDET': (6, 13, 13), 'VCO_TEST_MODE': (6, 14, 14), 'CAL_BYPASS': (6, 15, 15), 'MUX_CTRL': (6, 18, 16),
    'ISOURCE_SINKB': (6, 19, 19), 'ISOURCE_TRIM': (6, 22, 20), 'LO_DIV_SEL': (6, 24, 23), 'LO_DIV_BIAS': (6, 26, 25), 'TX_DIV_SEL': (6, 28, 27),
    'TX_DIV_BIAS': (6, 30, 29), 'GAIN_CTRL': (6, 31, 31),
}
# the reset columns of Tables 5-12, as field values
RESET_FIELDS = dict(RDIV=1, NEG_VCO=1, ICP=0b01010, CAL_CLK_SEL=0b1000,
                    NINT=128, PLL_DIV_SEL=1, PRSC_SEL=1, VCO_SEL=2,
                    RSV4_11=1, PWD_OUTBUF=1, PWD_LO_DIV=1, PWD_TX_DIV=1, PWD_MOD=1, MOD_ORD=0b101, DEL_SD_CLK=0b10,
                    IB_MOD_GM=2, IB_MOD_LO=2, VCO_BIAS=8, VCOBUF_BIAS=2, VCOMUX_BIAS=2, OUTBUF_BIAS=2, RSV5_21=1, VCO_CAL_REF=4,
                    VCO_AMPL_CTRL=2, VCO_VB_CTRL=2, EN_LD_ISOURCE=1,
                    VCO_TRIM=32, MUX_CTRL=1, ISOURCE_TRIM=4, LO_DIV_BIAS=2, TX_DIV_SEL=2, TX_DIV_BIAS=2)
# Table 16, "Register settings with optimized bias set used in the performance measurement"
BIAS_INT = dict(ICP=0, ICPDOUBLE=0, CAL_ACC=0, PWD_PLL=0, PWD_CP=0, PWD_VCO=0, PWD_VCO_MUX=0, PWD_DIV124=0, PWD_PRESC=0,
                PWD_OUTBUF=0, PWD_LO_DIV=0, PWD_TX_DIV=0, PWD_MOD=0, EN_EXTVCO=0, EN_ISOURCE=0, LD_ANA_PREC=0, CP_TRISTATE=0, SPEEDUP=0,
                LD_DIG_PREC=0, MOD_ORD=5, DITH_SEL=0, DEL_SD_CLK=2, EN_FRAC_MODE=0, IB_MOD_GM=3, IB_MOD_LO=0, VCO_BIAS=15, VCOBUF_BIAS=2,
                OUTBUF_BIAS=2, VCOMUX_BIAS=2, VCO_CAL_IB=0, VCO_CAL_REF=3, VCO_AMPL_CTRL=0, VCO_VB_CTRL=3, EN_LD_ISOURCE=0,
                EN_LOCKDET=0, VCO_TEST_MODE=0, CAL_BYPASS=0, MUX_CTRL=1, ISOURCE_SINKB=0, ISOURCE_TRIM=4, LO_DIV_BIAS=2, TX_DIV_BIAS=1, GAIN_CTRL=0)
BIAS_BAND = {'2-3GHz': dict(IB_MOD_LO=1), '3-4.1GHz': dict(IB_MOD_GM=2)}       # the columns that differ from 256 MHz - 2 GHz
BIAS_FRAC = dict(EN_ISOURCE=1, LD_ANA_PREC=3, MOD_ORD=4, DEL_SD_CLK=0, EN_FRAC_MODE=1, MUX_CTRL=5, ISOURCE_TRIM=7)


def address(reg):
    return ADDR_BASE | (reg & 7)


def set_field(word, name, value):
    reg, hi, lo = FIELDS[name]
    n = hi - lo + 1
    if not 0 <= value < (1 << n):
        raise ValueError('TRF3722 %s is %d bits: cannot hold %d' % (name, n, value))
    mask = ((1 << n) - 1) << lo
    return (word & ~mask) | (value << lo)


def pack(reg, **fields):
    """A register's word from field values (fields not given keep their reset value)."""
    w = RESET[reg]
    for k, v in fields.items():
        if FIELDS[k][0] != reg:
            raise ValueError('%s is in register %d, not %d' % (k, FIELDS[k][0], reg))
        w = set_field(w, k, v)
    return w


def unpack(word):
    """(register, {field: value}) from a word as written or read back."""
    reg = word & 7
    if (word >> 3) & 3 != 1:
        raise ValueError('not a TRF3722 word: address bits 4:3 are %d, not 01 (%08x)' % ((word >> 3) & 3, word))
    if reg == 0:
        return 0, dict(CHIP_ID=(word >> 5) & 3, R_SAT_ERR=(word >> 12) & 1, VCO_TRIM=(word >> 15) & 0x3F, VCO_SEL=(word >> 21) & 7,
                       COUNT=(word >> 13) & 0x3FFFF, MUX_COUNT=(word >> 31) & 1)
    return reg, {k: (word >> lo) & ((1 << (hi - lo + 1)) - 1) for k, (r, hi, lo) in FIELDS.items() if r == reg}


def readback_command(reg, mux_count=0):
    """The word to write (to register 0) to read register `reg` back (Table 15)."""
    if not 0 <= reg <= 6:
        raise ValueError('TRF3722 registers are 0..6')
    return (1 << 31) | (reg << 28) | ((mux_count & 1) << 27) | address(0)


def _reset():
    w = {r: address(r) for r in range(1, 7)}
    for k, v in RESET_FIELDS.items():
        w[FIELDS[k][0]] = set_field(w[FIELDS[k][0]], k, v)
    return w


RESET = _reset()
# the same numbers summed by hand from the tables' reset columns (and in sim/models.v's trf3722_model)
assert RESET == {1: 0x41500029, 2: 0x08A0100A, 3: 0x0000000B, 4: 0x4A00F80C, 5: 0xAA2AA28D, 6: 0x5441100E}, {k: '%08X' % v for k, v in RESET.items()}


def plan(f_hz, ref_hz=25e6, rdiv=1, fractional=None):
    """The dividers for RFOUT = f_hz (section 8.4.1): TX_DIV so the VCO lands in 2050-4100 MHz, PLL_DIV so the
    prescaler sees 3000 MHz or less, NINT and NFRAC from fVCO = fPFD x PLL_DIV x (NINT + NFRAC / 2^25), the
    prescaler from NINT, and CAL_CLK_SEL for a calibration clock at or under 200 kHz (the datasheet allows up to
    600 kHz and uses 80-120 kHz in Table 16).  fractional=None chooses integer mode when it is exact."""
    if not 256.25e6 <= f_hz <= 4100e6:
        raise ValueError('TRF3722: %.6g Hz is outside 256.25 MHz .. 4.1 GHz' % f_hz)
    tx_div_sel = 0
    while f_hz * (1 << tx_div_sel) < 2050e6:
        tx_div_sel += 1
    f_vco = f_hz * (1 << tx_div_sel)
    f_pfd = ref_hz / rdiv
    for pll_div_sel in (0, 1, 2):
        pll_div = 1 << pll_div_sel
        if f_vco / pll_div > 3000e6:
            continue
        x = f_vco / (f_pfd * pll_div)
        nint = int(math.floor(x + 1e-12))
        nfrac = int(round((x - nint) * (1 << 25)))
        if nfrac == 1 << 25:
            nint, nfrac = nint + 1, 0
        frac = bool(nfrac) if fractional is None else fractional
        prsc = 1 if nint >= (75 if frac else 72) else 0          # 8/9 above, 4/5 below
        if nint < (23 if frac else 20):
            raise ValueError('TRF3722: NINT = %d is too small: lower the PFD frequency (rdiv)' % nint)
        if f_vco / (pll_div * (8 if prsc else 4)) <= 375e6 and nint < 65536:
            break
    else:
        raise ValueError('TRF3722: no PLL_DIV keeps the digital divider at or under 375 MHz for %.6g Hz' % f_hz)
    # CAL_CLK = fPFD x factor; CAL_CLK_SEL 1111 = 1/128 ... 1000 = 1 ... 0000 = 128 (Table 6)
    cal_sel, cal_hz = 15, f_pfd / 128
    for sel in range(15, -1, -1):
        if sel == 7:
            continue                                             # "NA" in Table 6
        factor = 2.0 ** (8 - sel) if sel < 8 else 2.0 ** -(sel - 8)
        if f_pfd * factor <= 200e3:
            cal_sel, cal_hz = sel, f_pfd * factor
    f_act = f_pfd * pll_div * (nint + (nfrac / float(1 << 25) if frac else 0)) / (1 << tx_div_sel)
    band = '256MHz-2GHz' if f_hz < 2e9 else '2-3GHz' if f_hz < 3e9 else '3-4.1GHz'
    return dict(tx_div_sel=tx_div_sel, pll_div_sel=pll_div_sel, rdiv=rdiv, nint=nint, nfrac=nfrac if frac else 0, prsc_sel=prsc,
                fractional=frac, cal_clk_sel=cal_sel, cal_clk_hz=cal_hz, f_pfd=f_pfd, f_vco=f_vco, f_hz=f_act, error_hz=f_act - f_hz, band=band)


def words(f_hz, ref_hz=25e6, rdiv=1, fractional=None, lo_out=False):
    """Registers 1-6 for RFOUT = f_hz with Table 16's bias settings, as {1: word, ..., 6: word}, and the plan.
    Register 2 has EN_CAL set: write it last.  The LO output buffer and divider are powered down unless lo_out."""
    p = plan(f_hz, ref_hz, rdiv, fractional)
    f = dict(BIAS_INT)
    f.update(BIAS_BAND.get(p['band'], {}))
    if p['fractional']:
        f.update(BIAS_FRAC)
    f.update(RDIV=rdiv, REF_INV=0, NEG_VCO=1, CAL_CLK_SEL=p['cal_clk_sel'], NINT=p['nint'], PLL_DIV_SEL=p['pll_div_sel'],
             PRSC_SEL=p['prsc_sel'], VCO_SEL=RESET_FIELDS['VCO_SEL'], VCO_SEL_MODE=0, EN_CAL=1, NFRAC=p['nfrac'],
             TX_DIV_SEL=p['tx_div_sel'], LO_DIV_SEL=p['tx_div_sel'], VCO_TRIM=RESET_FIELDS['VCO_TRIM'])
    if not lo_out:
        f.update(PWD_OUTBUF=1, PWD_LO_DIV=1)                     # the LO outputs are unused on r13
    w = dict(RESET)
    for k, v in f.items():
        w[FIELDS[k][0]] = set_field(w[FIELDS[k][0]], k, v)
    return w, p


WRITE_ORDER = (1, 3, 4, 5, 6, 2)


def selfcheck():
    p = plan(1799.68e6, ref_hz=61.44e6, rdiv=24)                 # the datasheet's example, section 8.4.2
    assert (p['tx_div_sel'], p['pll_div_sel'], p['nint'], p['nfrac'], p['prsc_sel']) == (1, 1, 703, 0, 1), p
    assert abs(p['f_pfd'] - 2.56e6) < 1e-6 and not p['fractional']
    w, p = words(915e6)
    # 3660 MHz: PLL_DIV 2 would give NINT 73.2, fractional, so the 4/5 prescaler (NINT < 75) and 457 MHz into the
    # digital divider, over its 375 MHz: the datasheet's rule then says PLL_DIV 4, NINT 36.6
    assert (p['tx_div_sel'], p['pll_div_sel'], p['nint'], p['prsc_sel'], p['fractional']) == (2, 2, 36, 0, True), p
    assert abs(p['error_hz']) < 1.0
    for r in range(1, 7):
        assert unpack(w[r])[0] == r
    assert unpack(w[2])[1]['NINT'] == 36 and unpack(w[6])[1]['TX_DIV_SEL'] == 2 and unpack(w[4])[1]['EN_FRAC_MODE'] == 1
    assert readback_command(3) == 0xB0000008
    return True


if __name__ == '__main__':
    selfcheck()
    f = float(sys.argv[1]) if len(sys.argv) > 1 else 915e6
    w, p = words(f)
    print(p)
    print(' '.join('R%d=%08X' % (r, w[r]) for r in WRITE_ORDER))
