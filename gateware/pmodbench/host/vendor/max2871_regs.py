#!/usr/bin/env python3
# VENDORED, unmodified below this header, from the CostasLink board's gateware (it ran on real boards):
#   OpticsPCBs/CostasLink-PYNQ-Z2/gateware/max2871_regs.py  (repository commit 509c7f4, 2026-10-30)
# Copied 2026-11-15 for gateware/pmodbench.  Its `board_constants` import is satisfied by the stub beside it
# (board_constants.py: RSET 5.1 k and CP = 7, the same values as RF-MOD r10 and IQ-MOD q3).  The extensions
# pmodbench needs (output divider below 3 GHz, a chosen modulus, the output power) are in ../max2871.py.
"""MAX2871 register words for this board's two synthesizers (datasheet Tables 3-8, the register
maps; build/txt/MAX2871.txt lines 1190-1552).  Integer-N from the 25 MHz reference with no
reference division: f = 25 MHz x N, so 5800 MHz is N = 232 and the channels are 25 MHz apart.

    python3 gateware/max2871_regs.py [MHz ...]      prints the six words to send, register 5 first
    python3 gateware/max2871_regs.py --verilog [TX_MHz [RX_MHz]]
                                                    writes gateware/max2871_words.vh (the table the gateware
                                                    sends: gateware/max2871_init.v includes it)
    python3 gateware/max2871_regs.py --hex [TX_MHz [RX_MHz]]
                                                    prints the power-up sequence of both synthesizers, one
                                                    word per line, for the testbench's $readmemh

The words go out MSB first, 32 bits each, LE pulsed after each.  The power-up sequence is the
datasheet's "for a clean clock at start up" list (4-Wire Serial Interface): register 5, wait 20 ms,
register 4 with both outputs off, 3, 2, 1, 0, 5 again, then register 4 as computed so the outputs
turn on (sequence() below; the gateware's max2871_init.v sends it for the TX synthesizer, then the
RX one).  The MUX pin shows digital lock detect.

Self-check: decodes the datasheet's own 6000 MHz example (Note 3) and the defaults.
"""
import math, sys

F_REF_MHZ = 25.0          # the VCXO / TCXO
F_PFD_MHZ = 25.0          # R = 1, no doubler, no divide-by-2
from board_constants import RSET_OHM, CP_CODE      # sim/budget.py section 8: ICP = 1.63 / RSET x (1 + CP) = 2.56 mA
APWR = 1                  # RFOUTA -1 dBm per side (00 -4, 01 -1, 10 +2, 11 +5 dBm): 0 dBm into the ADL53xx LO, differential
BPWR = 1                  # RFOUTB -1 dBm when enabled (the LO MON jack)


def field(word, hi, lo, value):
    n = hi - lo + 1
    assert 0 <= value < (1 << n), "field %d:%d cannot hold %d" % (hi, lo, value)
    mask = ((1 << n) - 1) << lo
    return (word & ~mask) | (value << lo)


def regs(f_mhz, rfb_en=False, f_pfd=F_PFD_MHZ, mute_until_lock=False, cp=CP_CODE):
    """The six 32-bit words for RFOUTA = f_mhz (3000-6000 MHz, no output divider).  f_pfd = 25 MHz / R:
    the default R = 1 gives 25 MHz channels; the interference survey's R = 5 gives 5 MHz ones, every WiFi
    centre (PLAN.md section 19, Prompt 26), with the charge pump raised (cp = 15, 5.1 mA) because N is
    five times larger: the loop then slows to roughly 30-40 kHz (est), which a survey does not mind."""
    assert 3000.0 <= f_mhz <= 6000.0, "the VCO covers 3-6 GHz without the output divider"
    R = int(round(F_REF_MHZ / f_pfd))
    assert 1 <= R <= 1023 and abs(F_REF_MHZ / R - f_pfd) < 1e-9, "f_pfd must be 25 MHz / R"
    assert 0 <= cp <= 15
    n_exact = f_mhz / f_pfd
    N = int(round(n_exact))
    assert abs(N - n_exact) < 1e-9, "%.3f MHz is not a multiple of the %.3f MHz PFD: use the fractional mode" % (f_mhz, f_pfd)
    assert 16 <= N <= 65535
    r0 = field(0, 31, 31, 1)                 # INT: integer-N
    r0 = field(r0, 30, 15, N)
    r0 = field(r0, 14, 3, 0)                 # FRAC
    r0 = field(r0, 2, 0, 0)
    r1 = field(0, 30, 29, 0)                 # CPL: linearity off (integer mode)
    r1 = field(r1, 28, 27, 0)                # CPT: normal
    r1 = field(r1, 26, 15, 1)                # phase 1 (recommended)
    r1 = field(r1, 14, 3, 4095)              # M: modulus (unused in integer mode; 1 is "not valid")
    r1 = field(r1, 2, 0, 1)
    r2 = field(0, 31, 31, 0 if f_pfd <= 32 else 1)   # LDS
    r2 = field(r2, 30, 29, 0)                # SDN: low-noise mode
    r2 = field(r2, 28, 26, 0b110)            # MUX[2:0] with MUX[3] = 0: digital lock detect on the MUX pin
    r2 = field(r2, 25, 25, 0)                # DBR
    r2 = field(r2, 24, 24, 0)                # RDIV2
    r2 = field(r2, 23, 14, R)                # R (1 for the link)
    r2 = field(r2, 13, 13, 0)                # REG4DB
    r2 = field(r2, 12, 9, cp)
    r2 = field(r2, 8, 8, 1)                  # LDF: integer-N lock detect
    r2 = field(r2, 7, 7, 0)                  # LDP 10 ns
    r2 = field(r2, 6, 6, 1)                  # PDP positive: a passive (non-inverting) loop filter
    r2 = field(r2, 5, 5, 0)                  # SHDN
    r2 = field(r2, 4, 4, 0)                  # TRI
    r2 = field(r2, 3, 3, 0)                  # RST
    r2 = field(r2, 2, 0, 2)
    r3 = field(0, 31, 26, 0)                 # VCO (autoselect decides)
    r3 = field(r3, 25, 25, 0)                # VAS_SHDN: autoselect on
    r3 = field(r3, 24, 24, 1)                # VAS_TEMP: temperature compensation on
    r3 = field(r3, 18, 18, 0)                # CSM
    r3 = field(r3, 17, 17, 0)                # MUTEDEL
    r3 = field(r3, 16, 15, 0)                # CDM: fast lock off
    r3 = field(r3, 14, 3, int(round(f_pfd * 1e6 / 100e3)))   # CDIV = fPFD / 100 kHz (the VAS and ADC clock)
    r3 = field(r3, 2, 0, 3)
    bs = int(math.ceil(f_pfd * 1e6 / 50e3))  # band-select clock <= 50 kHz
    assert bs <= 1023
    r4 = field(0, 31, 29, 0b011)             # reserved: 011
    r4 = field(r4, 28, 28, 0)                # SDLDO
    r4 = field(r4, 27, 27, 0)                # SDDIV
    r4 = field(r4, 26, 26, 0)                # SDREF
    r4 = field(r4, 25, 24, bs >> 8)
    r4 = field(r4, 23, 23, 1)                # FB: fundamental feedback (DIVA not in the loop)
    r4 = field(r4, 22, 20, 0)                # DIVA: divide by 1 (3-6 GHz)
    r4 = field(r4, 19, 12, bs & 0xFF)
    r4 = field(r4, 11, 11, 0)                # SDVCO
    r4 = field(r4, 10, 10, 1 if mute_until_lock else 0)
    r4 = field(r4, 9, 9, 1)                  # BDIV: RFOUTB = VCO (fundamental)
    r4 = field(r4, 8, 8, 1 if rfb_en else 0)
    r4 = field(r4, 7, 6, BPWR)
    r4 = field(r4, 5, 5, 1)                  # RFA_EN
    r4 = field(r4, 4, 3, APWR)
    r4 = field(r4, 2, 0, 4)
    r5 = field(0, 30, 29, 0b11)              # VAS_DLY = 11 with VAS_TEMP = 1
    r5 = field(r5, 25, 25, 0)                # SDPLL
    r5 = field(r5, 24, 24, 1)                # F01: FRAC = 0 behaves as integer
    r5 = field(r5, 23, 22, 0b01)             # LD: digital lock detect
    r5 = field(r5, 18, 18, 0)                # MUX[3]
    r5 = field(r5, 6, 6, 0)
    r5 = field(r5, 5, 3, 0)
    r5 = field(r5, 2, 0, 5)
    return [r5, r4, r3, r2, r1, r0]


def regs_frac(f_mhz, mod=4095, **kw):
    """Fractional-N: f = f_pfd x (N + FRAC / MOD), for a carrier a few kHz off the 25 MHz grid (board A's
    bring-up emulates a board-to-board offset with the TX synthesizer, 2026-10-30).  The integer words of the
    channel below, then INT = 0 (register 0 bit 31), FRAC (14:3), CPL = 01 (the 10 % linearity of frac-N mode,
    register 1 bits 30:29) and LDF = 0 (frac-N lock detect, register 2 bit 8), as the datasheet's Int-N/Frac-N
    Modes section asks.  Returns (words, the frequency they make in MHz)."""
    f_pfd = kw.get("f_pfd", F_PFD_MHZ)
    n_exact = f_mhz / f_pfd
    N = int(math.floor(n_exact + 1e-12))
    frac = int(round((n_exact - N) * mod))
    if frac >= mod:
        N, frac = N + 1, 0
    w = regs(N * f_pfd, **kw)
    r5, r4, r3, r2, r1, r0 = w
    if frac:
        r0 = field(r0, 31, 31, 0)
        r0 = field(r0, 14, 3, frac)
        r1 = field(r1, 30, 29, 0b01)
        r1 = field(r1, 14, 3, mod)
        r2 = field(r2, 8, 8, 0)
    return [r5, r4, r3, r2, r1, r0], f_pfd * (N + frac / float(mod))


R4_OUTPUTS = (1 << 5) | (1 << 8)      # RFA_EN, RFB_EN
SEQ_WAIT_MS = 20                      # after the first word of the sequence (datasheet: "Register 5 ... Wait 20ms")


def sequence(words):
    """The eight words of the power-up sequence in send order: 5, [20 ms], 4 with the outputs disabled,
    3, 2, 1, 0, 5, then 4 as computed (RFOUTA on).  The datasheet's clean-start list plus the enable
    it says to do afterwards."""
    r5, r4, r3, r2, r1, r0 = words
    return [r5, r4 & ~R4_OUTPUTS, r3, r2, r1, r0, r5, r4]


def verilog_table(tx_mhz, rx_mhz):
    """gateware/max2871_words.vh: the six words of each synthesizer (as comments) and the two send
    sequences as Verilog-2005 localparams (a packed vector per sequence, word 0 in the top 32 bits);
    included inside max2871_init.v's module body."""
    L = ["// MAX2871 register words for the CostasLink board's two synthesizers.",
         "// GENERATED by gateware/max2871_regs.py --verilog %.1f %.1f : do not edit; rerun the script (make words)." % (tx_mhz, rx_mhz),
         "// Integer-N from the 25 MHz reference, R = 1: f = 25 MHz x N.  MUX = digital lock detect.",
         "// Send order after power-up (max2871_init.v): word 0, wait MAX2871_WAIT_MS, then words 1..7;",
         "// that is register 5, 4 (outputs off), 3, 2, 1, 0, 5 again, 4 (outputs on).  32 bits MSB first, LE after each.",
         "`ifndef MAX2871_WORDS_VH", "`define MAX2871_WORDS_VH",
         "localparam integer MAX2871_SEQ_LEN = 8;",
         "localparam integer MAX2871_WAIT_MS = %d;" % SEQ_WAIT_MS]
    for name, f in (("TX", tx_mhz), ("RX", rx_mhz)):
        w = regs(f)
        L.append("// %s synthesizer: %.1f MHz, N = %d" % (name, f, int(round(f / F_PFD_MHZ))))
        for i, word in enumerate(w):
            L.append("//   R%d = %08X" % (5 - i, word))
        seq = sequence(w)
        L.append("localparam [32*MAX2871_SEQ_LEN-1:0] MAX2871_%s_SEQ = {%s};" % (name, ", ".join("32'h%08X" % x for x in seq)))
    L.append("`endif")
    return "\n".join(L) + "\n"


def hex_sequence(tx_mhz, rx_mhz):
    """The TX sequence then the RX sequence, one 8-digit hex word per line ($readmemh)."""
    return "".join("%08X\n" % x for f in (tx_mhz, rx_mhz) for x in sequence(regs(f)))


def decode(words):
    """A few fields back out of the six words, for the self-check."""
    r5, r4, r3, r2, r1, r0 = words
    return dict(INT=(r0 >> 31) & 1, N=(r0 >> 15) & 0xFFFF, FRAC=(r0 >> 3) & 0xFFF, M=(r1 >> 3) & 0xFFF,
                R=(r2 >> 14) & 0x3FF, CP=(r2 >> 9) & 0xF, LDF=(r2 >> 8) & 1, PDP=(r2 >> 6) & 1,
                CDIV=(r3 >> 3) & 0xFFF, BS=(((r4 >> 24) & 3) << 8) | ((r4 >> 12) & 0xFF),
                FB=(r4 >> 23) & 1, DIVA=(r4 >> 20) & 7, RFA_EN=(r4 >> 5) & 1, APWR=(r4 >> 3) & 3,
                RFB_EN=(r4 >> 8) & 1, BDIV=(r4 >> 9) & 1, LD=(r5 >> 22) & 3)


def selfcheck():
    # the datasheet's Note 3 example: fREF 100 MHz, fPFD 25 MHz, 6000 MHz: 00780000, 00400061, 34011242, F8010003, 638FF1FC, 80400005
    ex = [0x80400005, 0x638FF1FC, 0xF8010003, 0x34011242, 0x00400061, 0x00780000]
    d = decode(ex)
    assert d["N"] == 240 and d["FRAC"] == 0, d              # 6000 / 25
    assert d["R"] == 4, d                                   # 100 MHz / 4 = 25 MHz
    assert d["FB"] == 1 and d["DIVA"] == 0 and d["RFA_EN"] == 1 and d["APWR"] == 3, d
    ours = decode(regs(5800.0))
    assert ours["N"] == 232 and ours["INT"] == 1 and ours["R"] == 1 and ours["CP"] == CP_CODE and ours["LDF"] == 1
    assert ours["BS"] == 500 and ours["CDIV"] == 250 and ours["BDIV"] == 1 and ours["RFB_EN"] == 0
    icp = 1.63 / RSET_OHM * (1 + CP_CODE)
    assert abs(icp - 2.56e-3) < 1e-5, icp
    return True


if __name__ == "__main__":
    import os
    selfcheck()
    if len(sys.argv) > 1 and sys.argv[1] in ("--verilog", "--hex"):
        fs = [float(a) for a in sys.argv[2:]] or []
        tx = fs[0] if fs else 5800.0
        rx = fs[1] if len(fs) > 1 else 5800.0            # BRINGUP.md stage 2: both at 5.800 GHz first
        if sys.argv[1] == "--hex":
            sys.stdout.write(hex_sequence(tx, rx))
        else:
            here = os.path.dirname(os.path.abspath(__file__))
            out = os.path.join(here, "max2871_words.vh")
            open(out, "w").write(verilog_table(tx, rx))
            print("wrote", os.path.relpath(out, os.path.dirname(here)))
        sys.exit(0)
    fs = [float(a) for a in sys.argv[1:]] or [5800.0, 5850.0]
    for f in fs:
        w = regs(f)
        print("%.1f MHz (N = %d): %s" % (f, int(round(f / F_PFD_MHZ)), " ".join("%08X" % x for x in w)))
    print("power-up sequence: " + " ".join("%08X" % x for x in sequence(regs(fs[0]))))
    print("  = 5, wait 20 ms, 4 (outputs off), 3, 2, 1, 0, 5, 4 (outputs on); LE after each word; MUX = lock detect")
