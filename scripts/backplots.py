"""Expected responses for the back panels (gen_pcb.back_panels): each a dict(x, y, xlog, xlim, ylim, xt, yt, name) from
the numbers the tiles' own documents quote, not from a measurement.  The ladder tiles of AMOD-P draw their simulation
(tiles.ladder); these are the others."""
import math


def logspace(a, b, n=80):
    return [10 ** (math.log10(a) + (math.log10(b) - math.log10(a)) * k / (n - 1)) for k in range(n)]


def linspace(a, b, n=80):
    return [a + (b - a) * k / (n - 1) for k in range(n)]


def amplifier(gain_db, f3, f1=1e4, f2=1e8, fl=None, name="gain"):
    """A gain block's magnitude: flat at gain_db, one pole at f3 (and one zero-pole pair at fl for a high-pass)."""
    f = logspace(f1, f2)
    y = []
    for x in f:
        m = gain_db - 10 * math.log10(1 + (x / f3) ** 2)
        if fl:
            m -= 10 * math.log10(1 + (fl / x) ** 2)
        y.append(m)
    top = 10 * math.ceil(gain_db / 10.0)
    return dict(x=f, y=y, xlog=True, xlim=(f1, f2), ylim=(top - 40.0, top), xt=(hz(f1), hz(f2)), yt=("%d" % top, "%d dB" % (top - 40)),
                name="")


def points(pts, xlog=True, ylim=(-60.0, 0.0), xt=None, yt=None, name=""):
    """A response read off a datasheet's table: straight lines between its points (on a log axis when xlog)."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return dict(x=xs, y=ys, xlog=xlog, xlim=(min(xs), max(xs)), ylim=ylim, xt=xt or (hz(min(xs)), hz(max(xs))),
                yt=yt or ("%g" % ylim[1], "%g dB" % ylim[0]), name=name)


def open_stub(f0, f1=0.1e9, f2=6e9, loss_db_per_wave=0.3):
    """S21 of a line with a quarter-wave open stub across it (resonant at f0 and 3 f0): S21 = 2 / (2 + j tan(theta)), with
    a little loss so the notch has a floor."""
    f = linspace(f1, f2, 240)
    y = []
    for x in f:
        th = math.pi / 2 * x / f0
        a = loss_db_per_wave / 8.686 * (x / f0) / 4             # nepers along the stub at this frequency
        z = complex(a, th)
        t = (math.e ** (2 * z) - 1) / (math.e ** (2 * z) + 1)    # tanh of (a + j th): the stub's admittance is tanh / Z0 for an open end
        s21 = 2 / (2 + t)
        y.append(20 * math.log10(max(abs(s21), 1e-4)))
    return dict(x=f, y=y, xlog=False, xlim=(f1, f2), ylim=(-40.0, 0.0), xt=("0.1G", "6G"), yt=("0", "-40 dB"), name="")


def clapp(L=10e-6, C1=220e-12, C2=220e-12, Cb=1e-9):
    """n9's frequency against TUNE: the varactor's cathode at (3.3 V + TUNE) / 2, its capacitance off the BB133's typical
    curve (digitised: 40 pF at 0.5 V, 35 at 1, 27 at 2, 22 at 3, 15.5 at 5 V), in series with the feedback pair."""
    cv = [(0.5, 40e-12), (1.0, 35e-12), (2.0, 27e-12), (3.0, 22e-12), (5.0, 15.5e-12)]

    def C(v):
        for (a, ca), (b, cb) in zip(cv, cv[1:]):
            if v <= b:
                return ca + (cb - ca) * (v - a) / (b - a)
        return cv[-1][1]
    xs = linspace(-2.0, 2.0, 41)
    ys = []
    for vt in xs:
        c = 1 / (1 / C1 + 1 / C2 + 1 / C((3.3 + vt) / 2) + 1 / Cb)
        ys.append(1 / (2 * math.pi * math.sqrt(L * c)) / 1e6)
    return dict(x=xs, y=ys, xlog=False, xlim=(-2.0, 2.0), ylim=(9.0, 12.0), xt=("-2V", "+2V"), yt=("12", "9 MHz"), name="")


def clipper(R=1000.0, Is=2.52e-9, n=1.752, vmax=4.0):
    """p10's OUT against IN: R in series, two 1N4148s antiparallel to ground, OUT at high impedance.  Vin = Vout + R I(Vout)
    with the diode's SPICE model (Is 2.52 nA, n 1.752), solved by bisection."""
    vt = 0.02585 * n

    def vin(vo):
        return vo + R * Is * (math.exp(vo / vt) - math.exp(-vo / vt))
    xs, ys = linspace(-vmax, vmax, 81), []
    for x in xs:
        lo, hi = -1.0, 1.0
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if vin(mid) < x else (lo, mid)
        ys.append((lo + hi) / 2)
    return dict(x=xs, y=ys, xlog=False, xlim=(-vmax, vmax), ylim=(-1.0, 1.0), xt=("IN -4V", "+4V"), yt=None, name="OUT +-1 V")


def hz(v):
    for m, s in ((1e9, "G"), (1e6, "M"), (1e3, "k")):
        if v >= m:
            return "%g%s" % (round(v / m, 3), s)
    return "%g" % v
