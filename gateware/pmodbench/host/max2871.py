#!/usr/bin/env python3
"""MAX2871 register words for the tile boards' synthesizers (RF-MOD r10, IQ-MOD q3), 23.5 MHz to 6 GHz.

The arithmetic that ran on real boards is CostasLink's max2871_regs.py, vendored unmodified in vendor/:
it makes the six words for a VCO frequency of 3-6 GHz (integer-N, or fractional-N with a given modulus).
This file adds only what the tiles need on top of it:
  * the output divider: below 3 GHz RFOUTA = VCO / 2^DIVA (register 4 bits 22:20, datasheet Table 7), with
    FB = 1 (the VCO's fundamental feeds the N counter), so N + F/M = fVCO / fPFD as the vendored code assumes;
  * a modulus chosen so the frequency is exact when it can be (F/M = the fraction in lowest terms, M <= 4095);
  * the output power (APWR, register 4 bits 4:3: 0, 1, 2, 3 = -4, -1, +2, +5 dBm);
  * the datasheet's power-up sequence written out in full (power_up_steps).
RFOUTB is never enabled (register 4 bit 8 = 0: the pins are open on the tiles) and the MUX pin is the
digital lock detect (register 2 bits 28:26 = 110, register 5 bit 18 = 0), both as the vendored code sets them.

    python3 max2871.py 915e6 [power_step]        prints the plan, the six words and the power-up sequence
"""
import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vendor'))
import max2871_regs as _m                                    # noqa: E402

POWER_DBM = (-4, -1, 2, 5)                                   # APWR 0..3
SEQ_WAIT_S = 0.020                                           # the datasheet's 20 ms
R4_OUTPUTS = _m.R4_OUTPUTS                                   # RFA_EN | RFB_EN
R4_RFB_EN = 1 << 8


def power_code(p):
    """APWR from a step (0..3) or a level in dBm (-4, -1, 2, 5); 2 means +2 dBm either way."""
    table = {0: 0, 1: 1, 2: 2, 3: 3, -4: 0, -1: 1, 5: 3}
    if p not in table:
        raise ValueError('MAX2871 output power: a step 0..3 or one of -4, -1, 2, 5 dBm, not %r' % (p,))
    return table[p]


def plan(f_hz, ref_hz=25e6, r=1, max_mod=4095):
    """DIVA, N, F and M for RFOUTA = f_hz from a reference of ref_hz divided by r.  Returns a dict with the
    frequency these make ('f_hz', exact as a Fraction in 'f_exact')."""
    if not 23.5e6 <= f_hz <= 6000e6:
        raise ValueError('MAX2871: %.6g Hz is outside 23.5 MHz .. 6 GHz' % f_hz)
    diva = 0
    while f_hz * (1 << diva) < 3000e6:
        diva += 1
    assert diva <= 7
    f_pfd = Fraction(ref_hz) / r
    ratio = Fraction(f_hz) * (1 << diva) / f_pfd
    n = ratio.numerator // ratio.denominator
    fm = (ratio - n).limit_denominator(max_mod)
    if fm == 1:
        n, fm = n + 1, Fraction(0)
    f, m = fm.numerator, fm.denominator
    if f and not 19 <= n <= 4091:
        raise ValueError('MAX2871: N = %d is outside 19..4091 (fractional mode)' % n)
    if not f and not 16 <= n <= 65535:
        raise ValueError('MAX2871: N = %d is outside 16..65535' % n)
    f_exact = f_pfd * (n + fm) / (1 << diva)
    return dict(diva=diva, n=n, frac=f, mod=m if f else 0, r=r, f_pfd=float(f_pfd), f_vco=float(f_pfd * (n + fm)),
                f_hz=float(f_exact), f_exact=f_exact, error_hz=float(f_exact - Fraction(f_hz)))


def words(f_hz, power=1, ref_hz=25e6, r=1, cp=None):
    """The six words [R5, R4, R3, R2, R1, R0] for RFOUTA = f_hz at output power step `power`, and the plan.
    The VCO-frequency words come from the vendored regs_frac(); register 4 then gets DIVA and APWR."""
    p = plan(f_hz, ref_hz, r)
    old_ref = _m.F_REF_MHZ
    _m.F_REF_MHZ = ref_hz / 1e6
    try:
        kw = dict(f_pfd=p['f_pfd'] / 1e6)
        if cp is not None:
            kw['cp'] = cp
        w, f_vco_mhz = _m.regs_frac(p['f_vco'] / 1e6, mod=p['mod'] or 4095, **kw)
    finally:
        _m.F_REF_MHZ = old_ref
    r5, r4, r3, r2, r1, r0 = w
    r4 = _m.field(r4, 22, 20, p['diva'])
    r4 = _m.field(r4, 4, 3, power_code(power))
    w = [r5, r4, r3, r2, r1, r0]
    d = _m.decode(w)                                         # the vendored decoder agrees with the plan, or we stop here
    if (d['N'], d['FRAC'], d['DIVA'], d['R'], d['RFB_EN'], d['RFA_EN'], d['FB']) != (p['n'], p['frac'], p['diva'], r, 0, 1, 1) \
            or (p['frac'] and d['M'] != p['mod']) or d['INT'] != (0 if p['frac'] else 1):
        raise AssertionError('MAX2871: the words %s do not decode to the plan %s' % (d, p))
    assert abs(f_vco_mhz * 1e6 - p['f_vco']) < 1.0
    assert not r4 & R4_RFB_EN, 'RFOUTB must stay disabled on the tiles'
    return w, p


def power_up_steps(w):
    """The datasheet's start-up ("4-Wire Serial Interface"): register 5, wait 20 ms, then 4 with both outputs
    off, 3, 2, 1, 0; "the registers should be programmed twice with at least a 20 ms pause" between the passes,
    so again 5, 4 (outputs off), 3, 2, 1, 0; the output is enabled afterwards by register 4 as computed (the
    caller waits for lock first: with VAS_TEMP = 1 the outputs must be off while the VCO is being chosen).
    Returns a list of ('w', word), ('wait', seconds) and one ('lock', None) where the caller should wait."""
    r5, r4, r3, r2, r1, r0 = w
    off = r4 & ~R4_OUTPUTS
    return ([('w', r5), ('wait', SEQ_WAIT_S)] + [('w', x) for x in (off, r3, r2, r1, r0)] + [('wait', SEQ_WAIT_S)] +
            [('w', x) for x in (r5, off, r3, r2, r1, r0)] + [('lock', None), ('w', r4)])


def selfcheck():
    _m.selfcheck()
    w, p = words(5800e6)                                     # the same words as CostasLink's, but for APWR's place
    assert w == _m.regs(5800.0), (w, _m.regs(5800.0))
    w, p = words(915e6, power=3)
    assert (p['diva'], p['n'], p['frac'], p['mod']) == (2, 146, 2, 5) and p['error_hz'] == 0, p     # 3660 MHz = 25 x 146.4
    d = _m.decode(w)
    assert (d['DIVA'], d['N'], d['FRAC'], d['M'], d['INT'], d['LDF'], d['APWR'], d['RFB_EN']) == (2, 146, 2, 5, 0, 0, 3, 0), d
    w, p = words(2400e6)
    assert (p['diva'], p['n'], p['frac']) == (1, 192, 0) and _m.decode(w)['INT'] == 1
    assert plan(23.5e6)['diva'] == 7 and plan(6000e6)['n'] == 240
    return True


if __name__ == '__main__':
    selfcheck()
    f = float(sys.argv[1]) if len(sys.argv) > 1 else 915e6
    pw = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    w, p = words(f, pw)
    print('%.6f MHz: VCO %.3f MHz / %d, N = %d + %d/%d, error %.3f Hz, %+d dBm' %
          (p['f_hz'] / 1e6, p['f_vco'] / 1e6, 1 << p['diva'], p['n'], p['frac'], p['mod'] or 1, p['error_hz'], POWER_DBM[power_code(pw)]))
    print('R5..R0: ' + ' '.join('%08X' % x for x in w))
    print('power-up: ' + ' '.join('%08X' % v if k == 'w' else ('[20 ms]' if k == 'wait' else '[lock]') for k, v in power_up_steps(w)))
