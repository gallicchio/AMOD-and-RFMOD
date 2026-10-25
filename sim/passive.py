#!/usr/bin/env python3
"""Responses of the passive tiles: a two-port ladder of series and shunt elements between a source
and a load, by ABCD matrices (numpy).  The silkscreen's expected-response sketches, the schematic's
notes and the handbook's numbers all come from here, so they cannot disagree with the parts.

    element: ("series", Z) or ("shunt", Y) where Z, Y are callables of omega returning complex ohms
             or siemens; helpers below build them from R, L, C values and series/parallel arms.
    response(elements, f, Rs=50, Rl=50) -> complex voltage transfer V_load / V_source_open,
             normalised so a straight-through gives 0 dB when Rs = Rl.
"""
import math
import numpy as np


def R(r):
    return lambda w: np.full_like(w, complex(r), dtype=complex)


def L(l, esr=0.0):
    return lambda w: 1j * w * l + esr


def C(c, esr=0.0):
    return lambda w: 1.0 / (1j * w * c) + esr


def series_arm(*zs):
    return lambda w: sum(z(w) for z in zs)


def parallel_arm(*zs):
    return lambda w: 1.0 / sum(1.0 / z(w) for z in zs)


def crystal(f_s, c_m, q, c0):
    """A quartz crystal: the motional arm (L, C, R from f_s, C_m, Q) in parallel with the holder C0."""
    w_s = 2 * math.pi * f_s
    l_m = 1.0 / (w_s ** 2 * c_m)
    r_m = w_s * l_m / q
    return parallel_arm(series_arm(L(l_m), C(c_m), R(r_m)), C(c0))


def response(elements, f, Rs=50.0, Rl=50.0):
    w = 2 * math.pi * np.asarray(f, dtype=float)
    A = np.ones_like(w, dtype=complex); B = np.zeros_like(w, dtype=complex)
    Cc = np.zeros_like(w, dtype=complex); D = np.ones_like(w, dtype=complex)
    for kind, fn in elements:
        if kind == "series":
            z = fn(w)
            a, b, c, d = 1.0, z, 0.0, 1.0
        elif kind == "shunt":
            y = 1.0 / fn(w)
            a, b, c, d = 1.0, 0.0, y, 1.0
        else:
            raise ValueError(kind)
        A, B, Cc, D = A * a + B * c, A * b + B * d, Cc * a + D * c, Cc * b + D * d
    # V_load / V_source with Rs and Rl: Vl/Vs = Rl / (A Rl + B + Rs (C Rl + D)); a thru with Rs = Rl gives 1/2
    h = Rl / (A * Rl + B + Rs * (Cc * Rl + D))
    return h * (1 + Rs / Rl)


def db(h):
    return 20 * np.log10(np.maximum(np.abs(h), 1e-12))


def corner(f, g_db, level=-3.0):
    """The first frequency at which the response falls below `level` (from the low end), Hz."""
    g = np.asarray(g_db)
    below = np.where(g < level)[0]
    if len(below) == 0:
        return None
    i = below[0]
    if i == 0:
        return float(f[0])
    # interpolate in log f
    f0, f1, g0, g1 = f[i - 1], f[i], g[i - 1], g[i]
    t = (level - g0) / (g1 - g0) if g1 != g0 else 0.0
    return float(math.exp(math.log(f0) + t * (math.log(f1) - math.log(f0))))


def peak(f, g_db):
    i = int(np.argmax(g_db))
    return float(f[i]), float(g_db[i])


def logspace(f0, f1, n=600):
    return np.logspace(math.log10(f0), math.log10(f1), n)


if __name__ == "__main__":
    f = logspace(1e5, 1e8)
    lp9 = [("shunt", C(220e-12)), ("series", L(1.5e-6)), ("shunt", C(680e-12)), ("series", L(1.5e-6)), ("shunt", C(220e-12))]
    g = db(response(lp9, f))
    print("P5: -3 dB at %.2f MHz, at 18 MHz %.1f dB" % (corner(f, g) / 1e6, g[np.argmin(abs(f - 18e6))]))
    bp = [("series", series_arm(L(2.7e-6), C(270e-12))), ("shunt", series_arm(L(330e-9), C(2.2e-9))), ("series", series_arm(L(2.7e-6), C(270e-12)))]
    g = db(response(bp, f))
    fp, gp = peak(f, g)
    lo = [x for x, y in zip(f, g) if y > gp - 3]
    print("P7: peak %.2f MHz %.1f dB, -3 dB band %.2f-%.2f MHz" % (fp / 1e6, gp, min(lo) / 1e6, max(lo) / 1e6))
    f2 = logspace(1e3, 1e7)
    lp100 = [("shunt", C(30e-9)), ("series", L(150e-6)), ("shunt", C(30e-9))]
    print("P6: -3 dB at %.1f kHz" % (corner(f2, db(response(lp100, f2))) / 1e3))
    for cadd in (0, 47e-12, 100e-12, 147e-12):
        rlc = [("series", series_arm(L(100e-6, 10.0), C(220e-12 + cadd)))]
        fp, gp = peak(f2, db(response(rlc, f2)))
        print("P4 +%3.0f pF: peak %.3f MHz %.2f dB" % (cadd * 1e12, fp / 1e6, gp))
    fx = np.linspace(3.99e6, 4.01e6, 4001)
    xt = [("series", crystal(4.0e6, 15e-15, 50000, 4e-12))]
    g = db(response(xt, fx))
    fp, gp = peak(fx, g)
    print("P8: peak %.5f MHz %.2f dB" % (fp / 1e6, gp))
