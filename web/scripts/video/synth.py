"""Instruments for the f1.h reel score (music.py), synthesized here: no samples, no third-party audio.
Mono instruments return float arrays at SR; stereo ones return [n, 2]."""
import numpy as np
from scipy.signal import butter, lfilter

SR = 44100
rng = np.random.default_rng(126)


def filt(x, kind, cut, order=2):
    b, a = butter(order, np.asarray(cut) / (SR / 2), kind)
    return lfilter(b, a, x, axis=0)


def hz(note):
    """'D3', 'Bb2', 'F#4' -> frequency."""
    names = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    n, rest = names[note[0]], note[1:]
    if rest[0] in 'b#':
        n += -1 if rest[0] == 'b' else 1; rest = rest[1:]
    return 440.0 * 2 ** ((n + 12 * (int(rest) + 1) - 69) / 12)


def env(n, a=0.005, d=0.1, s=1.0, r=0.05):
    """Attack, decay to sustain level, release at the end (seconds)."""
    t = np.arange(n) / SR; e = np.ones(n) * s
    na = max(1, int(a * SR)); e[:na] = np.linspace(0, 1, na)
    nd = int(d * SR); e[na:na + nd] = 1 - (1 - s) * (1 - np.exp(-np.arange(min(nd, n - na)) / (nd / 4 + 1)))
    nr = min(n, int(r * SR)); e[n - nr:] *= np.linspace(1, 0, nr)
    return e


def kick(level=1.0):
    n = int(0.42 * SR); t = np.arange(n) / SR
    f = 46 + 110 * np.exp(-t / 0.028)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.24)
    click = filt(rng.standard_normal(n), 'high', 2500) * np.exp(-t / 0.004) * 0.35
    return np.tanh(1.6 * (body + click)) * level


def clap(level=1.0):
    n = int(0.3 * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for k, off in enumerate((0, 0.011, 0.022)):           # three hands, slightly apart
        i = int(off * SR); x[i:] += rng.standard_normal(n - i) * np.exp(-(t[: n - i]) / (0.006 if k < 2 else 0.12))
    return filt(x, 'band', [900, 4200]) * 0.9 * level


def hat(open_=False, level=1.0):
    n = int((0.32 if open_ else 0.07) * SR); t = np.arange(n) / SR
    x = filt(rng.standard_normal(n), 'high', 7000) * np.exp(-t / (0.11 if open_ else 0.016))
    return x * level


def crash(level=1.0):
    n = int(2.4 * SR); t = np.arange(n) / SR
    noise = filt(rng.standard_normal(n), 'high', 3500) * np.exp(-t / 0.7)
    metal = sum(np.sin(2 * np.pi * f * t + p) for f, p in ((3150, 0), (4410, 1), (5790, 2), (7020, 3))) * 0.04 * np.exp(-t / 0.9)
    x = (noise + metal) * level
    return np.stack([x, filt(np.roll(x, 300), 'high', 3000)], axis=1)


def impact(level=1.0):
    """A cinematic sub hit: a sine falling from 70 to 30 Hz with a dull thud on top."""
    n = int(1.6 * SR); t = np.arange(n) / SR
    sub = np.sin(2 * np.pi * np.cumsum(30 + 40 * np.exp(-t / 0.15)) / SR) * np.exp(-t / 0.6)
    thud = filt(rng.standard_normal(n), 'low', 300) * np.exp(-t / 0.08) * 0.8
    return np.tanh(1.4 * (sub + thud)) * level


def supersaw(freq, dur, voices=7, detune=0.012, bright=1.0):
    """A wide detuned saw stack: voices spread left and right; darker with bright < 1."""
    n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros((n, 2))
    for v in range(voices):
        d = 1 + detune * (v - (voices - 1) / 2) / ((voices - 1) / 2)
        ph = rng.uniform(0, 1)
        saw = 2 * ((freq * d * t + ph) % 1.0) - 1
        pan = (v / (voices - 1)) if voices > 1 else 0.5
        out[:, 0] += saw * np.sqrt(1 - pan); out[:, 1] += saw * np.sqrt(pan)
    out /= voices
    return filt(out, 'low', 800 + 6000 * bright)


def pluck(freq, dur=0.22, level=1.0):
    """A short bright saw note whose filter closes fast (an arpeggio voice)."""
    n = int(dur * SR); t = np.arange(n) / SR
    saw = 2 * ((freq * t) % 1.0) - 1 + 0.5 * (2 * ((freq * 1.005 * t) % 1.0) - 1)
    k = np.exp(-t / 0.05)
    x = filt(saw, 'low', 900) * (1 - k) + filt(saw, 'low', 5000) * k
    return x * np.exp(-t / 0.12) * level


def sub(freq, dur, level=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(4 * np.pi * freq * t)
    return np.tanh(1.3 * x) * env(n, 0.004, 0.05, 0.85, 0.03) * level


def riser(dur, level=1.0):
    """Noise sweeping up and a tone rising an octave, building to the end."""
    n = int(dur * SR); t = np.arange(n) / n
    noise = rng.standard_normal(n)
    lo, hi = filt(noise, 'band', [300, 1500]), filt(noise, 'band', [2500, 9000])
    sweep = lo * (1 - t) + hi * t
    tone = np.sin(2 * np.pi * np.cumsum(220 * 2 ** t) / SR) * 0.15
    x = (sweep * 0.5 + tone) * t ** 2.2 * level
    return np.stack([x, x * 0.9], axis=1)


def reverb(x, seconds=1.4, mix=0.22, seed=3):
    """Stereo room: decaying noise impulse responses, a different one per side."""
    from scipy.signal import fftconvolve
    r = np.random.default_rng(seed); n = int(seconds * SR)
    out = np.zeros_like(x)
    for ch in range(2):
        ir = r.standard_normal(n) * np.exp(-np.arange(n) / (SR * seconds / 5)); ir = filt(ir, 'low', 7000)
        ir /= np.sqrt(np.sum(ir ** 2))
        out[:, ch] = fftconvolve(x[:, ch], ir)[: len(x)]
    return (1 - mix) * x + mix * out
