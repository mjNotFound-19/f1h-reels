"""Soundtrack for an f1.h reel: the original score (music.py: 126 BPM, D minor, written to the edit's cues) with the
start-light beeps, the synthesized engine (engine.py) and small effects on the reel's cues, mixed as one piece.
Generated here: no samples, no third-party audio.

    python web/scripts/video/soundtrack.py <cues.json> <out.wav>
"""
import json
import sys
import wave
from pathlib import Path

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine  # noqa: E402  (the synthesized F1 power unit)
import music as score  # noqa: E402  (the original score, cut to the edit)

SR = 44100
rng = np.random.default_rng(21)
D = {'D1': 36.71, 'D2': 73.42, 'A2': 110.0, 'D3': 146.83, 'F4': 349.23, 'A4': 440.0, 'D5': 587.33, 'A5': 880.0}


def filt(x, kind, cut, order=2):
    b, a = butter(order, np.asarray(cut) / (SR / 2), kind)
    return lfilter(b, a, x)


def env(n, attack, decay):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(attack, 1e-4)) * np.exp(-t / decay)


def tone(f, dur, attack=0.002, decay=0.1, sweep=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    fr = f * sweep ** (t / dur)                                 # pitch glide over the note
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * env(n, attack, decay)


def noise(dur, lo, hi, attack=0.002, decay=0.1):
    n = int(dur * SR)
    return filt(rng.standard_normal(n), 'band', [lo, hi]) * env(n, attack, decay)


def mx(*parts):
    """Layers of different lengths, summed (each padded with silence)."""
    out = np.zeros(max(len(p) for p in parts))
    for p in parts: out[: len(p)] += p
    return out


def sfx(kind):
    if kind == 'light':                                          # start light: a crisp broadcast-style beep (original)
        return mx(0.3 * tone(D['D5'] * 2, 0.16, 0.002, 0.11), 0.12 * tone(D['A5'] * 2, 0.16, 0.002, 0.08), 0.08 * tone(D['D5'], 0.16, 0.002, 0.09))
    if kind == 'lightsout':                                      # the drop: low D boom, a crack, a long tail
        return mx(0.9 * tone(D['D2'], 1.8, 0.004, 0.55, sweep=0.5), 0.5 * tone(D['D1'], 1.8, 0.01, 0.8), 0.35 * noise(0.6, 200, 6000, 0.001, 0.08))
    if kind == 'impact':
        return mx(0.55 * tone(D['D2'], 0.9, 0.003, 0.3, sweep=0.6), 0.22 * noise(0.3, 300, 5000, 0.001, 0.05))
    if kind == 'hit':                                            # a tom-like thump on D3
        return mx(0.35 * tone(D['D3'], 0.4, 0.002, 0.09, sweep=0.7), 0.08 * noise(0.1, 500, 3000, 0.001, 0.02))
    if kind == 'whoosh':                                         # filtered noise rising then falling, 0.55 s
        n = int(0.55 * SR); t = np.arange(n) / n
        x = rng.standard_normal(n) * np.sin(np.pi * t) ** 2
        lo = filt(x, 'band', [400, 2500]); hi = filt(x, 'band', [2500, 8000])
        return 0.28 * (lo * (1 - t) + hi * t)
    if kind == 'tick':
        return mx(0.06 * tone(D['A5'], 0.06, 0.001, 0.012), 0.03 * tone(D['D5'], 0.06, 0.001, 0.01))
    if kind == 'end':
        return mx(0.6 * tone(D['D2'], 2.5, 0.004, 0.9), 0.3 * tone(D['A2'], 2.5, 0.01, 0.9), 0.2 * tone(D['F4'], 2.5, 0.02, 0.7))
    return np.zeros(1)


def reverb(x, seconds=1.1, mix=0.18):
    n = int(seconds * SR)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (SR * seconds / 5))
    ir = filt(ir, 'low', 6000) / np.sqrt(np.sum(ir ** 2))
    return (1 - mix) * x + mix * fftconvolve(x, ir)[: len(x)]


def read_wav(p):
    with wave.open(str(p)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        return a.reshape(-1, w.getnchannels()).mean(axis=1) if w.getnchannels() > 1 else a


def main(cues_path, out):
    c = json.loads(Path(cues_path).read_text())
    dur, cues = c['duration'], c['cues']
    n = int(dur * SR) + SR
    music = score.build(cues, dur)[:n]                           # the score, written to this edit (music.py)
    fx = np.zeros(n); duck = np.ones(n); car = np.zeros((n, 2))
    own_lights = Path(__file__).with_name('sfx') / 'lights.wav'        # Manas's own clip, if he adds one
    first_light = next((q['t'] for q in cues if q['type'] == 'light'), None)
    if own_lights.exists() and first_light is not None:
        clip = read_wav(own_lights); i = int(first_light * SR); j = min(n, i + len(clip)); fx[i:j] += clip[: j - i] * 0.9
    for q in cues:
        i = int(q['t'] * SR)
        if q['type'] in ('blip', 'launch'):                        # no engine under the lights or the launch: the score carries it
            continue
        if q['type'] in ('blip', 'launch', 'passby'):              # the engine (stereo)
            s = (engine.blip(q.get('n', 0)) * 0.5 if q['type'] == 'blip' else engine.launch() * 0.75 if q['type'] == 'launch'
                 else engine.passby(direction=q.get('dir', 1)) * 1.1)
            s = np.stack([s, s], axis=1) if s.ndim == 1 else s
            j = min(n, i + len(s)); car[i:j] += s[: j - i]
            if q['type'] == 'launch':                              # the music gives way to the launch, then returns
                d = int(2.4 * SR); jj = min(n, i + d); duck[i:jj] = np.minimum(duck[i:jj], 0.55 + 0.45 * np.linspace(0, 1, jj - i) ** 2)
            continue
        if q['type'] == 'light' and own_lights.exists():
            continue
        if q['type'] in ('lightsout', 'end', 'cut'):              # the score plays these
            continue
        s = sfx(q['type']) * (0.5 if q['type'] == 'impact' else 1.0)
        if q.get('soft'): s = s * 0.6
        j = min(n, i + len(s)); fx[i:j] += s[: j - i]
    fade = np.clip((dur - np.arange(n) / SR) / 0.6, 0, 1)        # the last 0.6 s fades out
    mix = (0.85 * music * duck[:, None] + reverb(fx)[:, None] + 0.5 * car) * fade[:, None]   # engine in front, in stereo
    mix = np.tanh(1.2 * mix) / np.tanh(1.2)                      # gentle limiter
    mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.89              # -1 dBFS peak
    mix[: int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))[:, None]
    pcm = (mix[: int(dur * SR)] * 32767).astype(np.int16)
    with wave.open(out, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f'soundtrack: {dur:.2f} s, {len(cues)} cues -> {out}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
