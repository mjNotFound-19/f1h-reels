"""A modern F1 power unit, synthesized (no recordings): 1.6 L turbo V6, so the firing note is rpm / 20 Hz (three
firings per revolution), about 600 Hz at 12,000 rpm. Exhaust resonances shape the harmonics; each combustion pulse
adds rasp; a turbo whistle and the MGU-K's electric whine sit on top. Used by soundtrack.py.

    blip(n)          a rev on the grid, a little higher with each start light
    launch(seconds, shift_every)   off the line and up through the gears, ignition cut and crackle on each upshift
    passby(seconds, dir)          a car flying past at ~300 km/h: Doppler pitch drop, distance and stereo pan
All return float arrays at SR (mono; passby returns stereo [n, 2]).
"""
import numpy as np
from scipy.signal import butter, lfilter

SR = 44100
rng = np.random.default_rng(7)
RES = [(420, 260), (1150, 500), (2700, 900)]      # exhaust and airbox resonances (centre Hz, width Hz)


def _filt(x, kind, cut, order=2):
    b, a = butter(order, np.asarray(cut) / (SR / 2), kind)
    return lfilter(b, a, x)


def voice(rpm, throttle=None):
    """The engine at an rpm curve (one value per sample); throttle 0..1 scales the rasp and loudness."""
    n = len(rpm)
    thr = np.ones(n) if throttle is None else throttle
    f = rpm / 20.0
    ph = 2 * np.pi * np.cumsum(f) / SR
    out = np.zeros(n)
    for k in range(1, 15):                         # harmonics of the firing note, shaped by the resonances
        fk = f * k
        gain = sum(np.exp(-((fk - c) / w) ** 2) for c, w in RES) * 0.9 + 0.35 / k ** 0.7
        gain = np.where(fk < SR / 2 - 500, gain, 0)
        out += gain * np.sin(k * ph + 0.7 * k)
    pulse = (0.5 + 0.5 * np.cos(ph)) ** 6           # combustion pulses: noise gated at the firing rate
    out += 1.6 * _filt(rng.standard_normal(n), 'band', [900, 6000]) * pulse * thr
    out += 0.05 * np.sin(2 * np.pi * np.cumsum(7600 * (rpm / 12500)) / SR) * thr     # turbo whistle
    out += 0.06 * np.sin(2 * np.pi * np.cumsum(rpm / 60 * 6.5) / SR)                 # MGU-K whine
    out *= 0.25 + 0.75 * thr
    out = np.tanh(1.7 * out / (np.max(np.abs(out)) + 1e-9) * 2.2)                    # mechanical grit
    return _filt(_filt(out, 'high', 70), 'low', 10500)


def _env(n, a, r):
    e = np.ones(n); na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na); e[-nr:] = np.linspace(1, 0, nr)
    return e


def blip(i=0, dur=0.42):
    """A rev on the grid: up from 7000 rpm and back, a little higher with each light."""
    n = int(dur * SR); t = np.arange(n) / SR
    peak = 9800 + i * 550
    rpm = 7000 + (peak - 7000) * np.exp(-((t - 0.11) / 0.08) ** 2)
    return voice(rpm, np.clip(1.2 - t / dur, 0.2, 1)) * _env(n, 0.01, 0.15) * 0.8


def launch(dur=4.6, shift_every=0.476, gears=7):
    """Off the line: rpm climbs through each gear, drops ~2,300 on the upshift (on the beat), with a 35 ms
    ignition cut and exhaust crackle; fades out over the last 1.4 s as the music takes over."""
    n = int(dur * SR); t = np.arange(n) / SR
    g = np.minimum((t / shift_every).astype(int), gears - 1)
    within = (t - g * shift_every) / shift_every
    lo, hi = 9700 + 220 * g, 12400 + 60 * g
    rpm = lo + (hi - lo) * (1 - np.exp(-2.4 * np.clip(within, 0, 1))) / (1 - np.exp(-2.4))
    thr = np.ones(n)
    crack = np.zeros(n)
    for s in range(1, gears):
        i = int(s * shift_every * SR); j = min(n, i + int(0.035 * SR))
        thr[i:j] = 0.15                             # ignition cut on the upshift
        for _ in range(5):                          # crackle: short filtered pops just after the cut
            p = i + int(rng.uniform(0.004, 0.05) * SR)
            if p + 300 < n:
                crack[p:p + 300] += rng.uniform(0.3, 0.8) * np.exp(-np.arange(300) / 40) * rng.choice([-1, 1])
    out = voice(rpm, thr) + _filt(crack, 'band', [600, 5000]) * 1.5
    fade = np.clip((dur - t) / 1.4, 0, 1) ** 1.5
    return out * _env(n, 0.005, 0.05) * fade


def passby(dur=1.4, direction=1, speed=85.0, dist=7.0):
    """A car passing at `speed` m/s, `dist` m away: Doppler shift, 1/r loudness, air absorption, stereo pan."""
    n = int(dur * SR); t = np.arange(n) / SR - dur / 2
    x = speed * t * direction
    r = np.sqrt(x ** 2 + dist ** 2)
    vr = speed * (speed * t) / r                     # rate the distance changes: negative coming in
    shift = 343.0 / (343.0 + vr)
    rpm = 11800 * shift
    eng = voice(rpm, np.ones(n))
    near = dist / r
    loud = near ** 1.2
    dark = _filt(eng, 'low', 2200)                  # far away: the top end fades first
    eng = dark + (eng - dark) * near
    air = _filt(rng.standard_normal(n), 'band', [400, 4000]) * near ** 2 * 0.35
    mono = (eng + air) * loud
    pan = np.clip(x / (dist * 3), -1, 1)
    left, right = mono * np.sqrt((1 - pan) / 2), mono * np.sqrt((1 + pan) / 2)
    return np.stack([left, right], axis=1) * _env(n, 0.02, 0.05)[:, None]
