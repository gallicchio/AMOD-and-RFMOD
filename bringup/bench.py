"""The instruments, real and simulated, behind one small set of words.

    bench = Bench.real(cfg)        # from bringup/bench.json, through ~/mudd/lab-instrument-control's drivers
    bench = Bench.sim(world)       # sim.World plays the board and the instruments

    bench.gen('G1').set('sine', 1e6, 0.5)        # volts peak to peak INTO 50 OHM, always
    bench.scope.setup(1, '50', 0.1); t, v = bench.scope.capture([1, 2], span=1e-3)     # v[ch] in volts
    bench.psu.read()               # (volts, amps) of the board's output
    bench.vna.sweep(...), bench.sa.sweep(...), bench.host.<any method of pmodbench.PmodBench>

Nothing here talks to an instrument that bench.json does not name: the bench PC's other instruments belong to
other work (lab-instrument-control/AGENTS.md).  Every instrument is opened only when a test first asks for it.
"""
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "bench.json")
DEFAULT = {
    "_about": "Which instruments this bring-up may use.  null = not assigned: the tool will not touch it.",
    "lab_control": "~/mudd/lab-instrument-control",
    "cable_pf": 75,
    "scope_min_scale": 0.0005,
    "generators": [{"label": "G1", "driver": "sdg1032x", "host": None, "usb_serial": None, "channel": 1},
                   {"label": "G2", "driver": "sdg1032x", "host": None, "usb_serial": None, "channel": 2}],
    "scope": {"driver": "sds2104x", "host": None, "usb_serial": None},
    "psu": {"driver": "e36xxa", "serial": None, "board_output": 1, "motor_output": 2},
    "dmm": {"driver": "fluke45", "serial": None},
    "sa": {"driver": "dsa875", "host": None, "usb_serial": None},
    "vna": {"driver": "hp87xx", "gpib": None, "prologix": None},
    "host": {"port": None},
}


def load_config():
    if not os.path.exists(CONFIG):
        with open(CONFIG, "w") as f:
            json.dump(DEFAULT, f, indent=1)
    with open(CONFIG) as f:
        cfg = json.load(f)
    for k, v in DEFAULT.items():
        cfg.setdefault(k, v)
    return cfg


class NotAssigned(Exception):
    """bench.json does not name the instrument a test needs."""


def round125(x, up=True):
    """The next 1-2-5 step at or above x (a scope's volts or seconds per division)."""
    e = math.floor(math.log10(x)); m = x / 10 ** e
    for s in (1, 2, 5, 10):
        if m <= s * (1 + 1e-9):
            return s * 10 ** e
    return 10 ** (e + 1)


# ---------------------------------------------------------------------------------------------------
# Real instruments
# ---------------------------------------------------------------------------------------------------
def _lab(cfg, *folders):
    root = os.path.expanduser(cfg["lab_control"])
    for f in folders:
        p = os.path.join(root, f)
        if p not in sys.path:
            sys.path.insert(0, p)


class RealGen:
    """One channel of an SDG1032X, set for a 50 ohm load so its numbers are volts into 50 ohm."""
    def __init__(self, dev, ch, label):
        self.dev, self.ch, self.label = dev, ch, label
        self.dev.output(ch, on=False, load=50)

    def set(self, shape, freq=0.0, vpp=0.0, offset=0.0, duty=50.0):
        if shape == "dc":
            self.dev.dc(self.ch, offset)
        elif shape == "sine":
            self.dev.sine(self.ch, freq, vpp, offset)
        elif shape == "square":
            self.dev.square(self.ch, freq, vpp, offset, duty)
        elif shape == "ramp":
            self.dev.ramp(self.ch, freq, vpp, offset)
        else:
            raise ValueError(shape)
        self.dev.output(self.ch, on=True)

    def off(self):
        self.dev.output(self.ch, on=False)


class RealScope:
    """SDS2104X Plus: 50 ohm or 1 Mohm inputs, forced acquisitions (no trigger is needed to read an amplitude)."""
    def __init__(self, dev, min_scale):
        self.dev, self.min_scale, self.max_scale = dev, min_scale, 10.0

    def setup(self, ch, load, scale, offset=0.0, coupling="DC"):
        self.dev.channel(ch, on=True, scale=scale, offset=offset, coupling=coupling, impedance="50" if str(load) == "50" else "1M",
                         probe=1, bwlimit="FULL")

    def off(self, ch):
        self.dev.channel(ch, on=False)

    def capture(self, chs, span):
        self.dev.timebase(scale=round125(span / 10.0), delay=0.0)
        self.dev.acquire(mdepth="100k")
        self.dev.acquire_now(timeout=max(10.0, 4 * span + 5))
        v, t = {}, None
        for ch in chs:
            t, v[ch], _ = self.dev.waveform(ch)
        return t - t[0], v


class RealPsu:
    def __init__(self, dev, out):
        self.dev, self.out = dev, out

    def set(self, volts, amps, out=None):
        self.dev.set(volts, amps, out or self.out)

    def on(self): self.dev.output(True)
    def off(self): self.dev.off()
    def read(self, out=None): return self.dev.measure(out or self.out)
    def mode(self, out=None): return self.dev.mode(out or self.out)

    def say(self, text):
        try:
            self.dev.display_text(text[:12] if text else None)
        except Exception:
            pass


class RealSa:
    def __init__(self, dev):
        self.dev = dev

    def sweep(self, f0, f1, rbw=None, ref=10.0):
        self.dev.frequency(start=f0, stop=f1)
        self.dev.amplitude(ref_level=ref)
        if rbw:
            self.dev.bandwidth(rbw=rbw)
        return self.dev.trace(1, fresh=True)


class RealVna:
    """HP 8719ES / 8720ES.  The calibration is the operator's (hp/hp.md): this only sweeps and reads."""
    def __init__(self, dev):
        self.dev = dev

    def sweep(self, f0, f1, n, power, param="S21"):
        self.dev.power(power)
        self.dev.sweep(start=f0, stop=f1, points=int(n))
        return self.dev.trace(param, fresh=True, require_cal=True)


class Bench:
    def __init__(self):
        self.cfg, self.world, self._open, self.is_sim = None, None, {}, False

    # -- construction ----------------------------------------------------------------------------
    @classmethod
    def real(cls, cfg=None):
        b = cls(); b.cfg = cfg or load_config()
        return b

    @classmethod
    def sim(cls, world):
        import sim
        b = cls(); b.cfg = dict(DEFAULT); b.world = world; b.is_sim = True
        b._open = {"G1": sim.SimGen(world, "G1"), "G2": sim.SimGen(world, "G2"), "scope": sim.SimScope(world), "psu": sim.SimPsu(world),
                   "sa": sim.SimSa(world), "vna": sim.SimVna(world), "host": sim.SimHost(world)}
        return b

    @property
    def cable_pf(self): return float(self.cfg.get("cable_pf", 75))

    # -- the instruments, opened when first asked for ----------------------------------------------
    def _usb(self, vendor, product, serial):
        from scpi_link import usbtmc_node
        return usbtmc_node(vendor, product, serial=serial)

    def gen(self, label):
        if label in self._open:
            return self._open[label]
        g = next((x for x in self.cfg["generators"] if x["label"] == label), None)
        if g is None or not (g.get("host") or g.get("usb_serial")):
            raise NotAssigned("generator %s: put its address (host) or serial number (usb_serial) in bringup/bench.json" % label)
        _lab(self.cfg, "", "siglent")
        from siglent_SDG1032X import SDG1032X, USB_VENDOR, USB_PRODUCT
        key = ("sdg", g.get("host"), g.get("usb_serial"))
        if key not in self._open:
            self._open[key] = (SDG1032X(usb=self._usb(USB_VENDOR, USB_PRODUCT, g["usb_serial"]), vlimit=10.0) if g.get("usb_serial")
                               else SDG1032X(g["host"], vlimit=10.0))
        self._open[label] = RealGen(self._open[key], g["channel"], label)
        return self._open[label]

    @property
    def scope(self):
        if "scope" not in self._open:
            s = self.cfg["scope"]
            if not (s.get("host") or s.get("usb_serial")):
                raise NotAssigned("scope: put its address or serial number in bringup/bench.json")
            _lab(self.cfg, "", "siglent")
            from siglent_SDS2104X import SDS2104X, USB_VENDOR, USB_PRODUCT
            dev = SDS2104X(usb=self._usb(USB_VENDOR, USB_PRODUCT, s["usb_serial"])) if s.get("usb_serial") else SDS2104X(s["host"])
            self._open["scope"] = RealScope(dev, float(self.cfg.get("scope_min_scale", 0.0005)))
        return self._open["scope"]

    @property
    def psu(self):
        if "psu" not in self._open:
            p = self.cfg["psu"]
            if not p.get("serial"):
                raise NotAssigned("power supply: put its serial port (/dev/serial/by-id/...) in bringup/bench.json")
            _lab(self.cfg, "", "hp")
            from agilent_E36xxA import AgilentE36xxA
            self._open["psu"] = RealPsu(AgilentE36xxA(serial=p["serial"]), p.get("board_output", 1))
        return self._open["psu"]

    @property
    def sa(self):
        if "sa" not in self._open:
            s = self.cfg["sa"]
            if not (s.get("host") or s.get("usb_serial")):
                raise NotAssigned("spectrum analyzer: put its address or serial number in bringup/bench.json")
            _lab(self.cfg, "", "rigol")
            import rigol_DSA875 as rd
            dev = rd.DSA875(usb=self._usb(rd.USB_VENDOR, rd.USB_PRODUCT, s["usb_serial"])) if s.get("usb_serial") else rd.DSA875(s["host"])
            self._open["sa"] = RealSa(dev)
        return self._open["sa"]

    @property
    def vna(self):
        if "vna" not in self._open:
            v = self.cfg["vna"]
            if v.get("gpib") is None:
                raise NotAssigned("network analyzer: put its GPIB address (and the Prologix adapter's port) in bringup/bench.json")
            _lab(self.cfg, "", "hp")
            from hp_87xxES import HP87xxES
            self._open["vna"] = RealVna(HP87xxES(v["gpib"], prologix=v.get("prologix")))
        return self._open["vna"]

    @property
    def host(self):
        if "host" not in self._open:
            h = self.cfg["host"]
            if not h.get("port"):
                raise NotAssigned("Pmod host: put the ECP5 board's serial port in bringup/bench.json ('auto' finds an FT2232H's second channel)")
            sys.path.insert(0, os.path.join(HERE, "..", "gateware", "pmodbench", "host"))
            import pmodbench
            self._open["host"] = pmodbench.PmodBench(port=None if h["port"] == "auto" else h["port"])
        return self._open["host"]

    # -- leaving things safe -----------------------------------------------------------------------
    def quiet(self):
        """Generators off, the host's pins released.  The supply stays as it is."""
        for k, v in list(self._open.items()):
            if isinstance(k, str) and k.startswith("G"):
                try: v.off()
                except Exception as e: print("  (%s off: %r)" % (k, e))
        if "host" in self._open:
            try: self._open["host"].safe()
            except Exception as e: print("  (host safe: %r)" % (e,))

    def close(self):
        self.quiet()
        for k, v in list(self._open.items()):
            dev = getattr(v, "dev", v)
            if hasattr(dev, "close") and not self.is_sim:
                try: dev.close()
                except Exception: pass
        self._open = {} if not self.is_sim else self._open

    def who(self):
        """Ask each assigned instrument who it is (*IDN? only).  Unassigned ones are listed as such."""
        out = []
        for name, getter in (("G1", lambda: self.gen("G1").dev.idn), ("G2", lambda: self.gen("G2").dev.idn), ("scope", lambda: self.scope.dev.link.idn),
                             ("psu", lambda: self.psu.dev.idn), ("sa", lambda: self.sa.dev.link.idn), ("vna", lambda: self.vna.dev.link.idn),
                             ("host", lambda: self.host.ident())):
            try:
                out.append((name, "ok", str(getter())))
            except NotAssigned as e:
                out.append((name, "not assigned", str(e)))
            except Exception as e:
                out.append((name, "NO ANSWER", repr(e)))
        return out
