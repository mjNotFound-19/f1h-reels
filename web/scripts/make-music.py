"""Original backing track for the f1.h videos, synthesised here (no samples, no third-party audio, no
existing melody: the motif below was written for this project).

    python web/scripts/make-music.py <seconds> <out.wav>

Motorsport-broadcast feel: a driving sixteenth-note string ostinato, low brass chords, big drums and a short
heroic motif. 126 BPM, D minor (Dm - Bb - F - C, one bar each). Builds in 8-bar blocks, ends on a held hit.
Everything is generated with numpy/scipy.
"""
import sys
import wave

import numpy as np
from scipy.signal import butter, lfilter

SR = 44100
BPM = 126
BEAT = 60 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(16)

dur = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0
out = sys.argv[2] if len(sys.argv) > 2 else 'music.wav'
N = int(dur * SR)


def hz(m):                      # MIDI note -> frequency
    return 440.0 * 2 ** ((m - 69) / 12)


def filt(x, kind, cut, order=2):
    b, a = butter(order, np.asarray(cut) / (SR / 2), kind)
    return lfilter(b, a, x)


def saw(f, n, ph=0.0):
    t = np.arange(n) / SR
    return 2 * ((f * t + ph) % 1.0) - 1


def add(buf, at, x, gain=1.0):
    i = int(at * SR)
    if i >= N or i < 0:
        return
    x = x[:N - i]
    buf[i:i + len(x)] += gain * x


def env(n, a, r):               # attack / release in seconds
    k = np.arange(n) / SR
    return np.minimum(1, k / a) * np.minimum(1, (n / SR - k) / r)


# root (bass octave) and the chord's third / fifth, one bar each: Dm, Bb, F, C
CHORDS = [dict(root=38, third=41, fifth=45), dict(root=34, third=38, fifth=41),
          dict(root=41, third=45, fifth=48), dict(root=36, third=40, fifth=43)]
# the motif: two notes a bar (half notes), an 8-bar phrase that rises and resolves (MIDI, around D5)
MOTIF = [(74, 77), (74, 70), (72, 77), (76, 72), (74, 77), (82, 77), (81, 77), (76, 79)]

n_bars = int(np.ceil(dur / BAR))
END = max(0.0, dur - 4.4)                       # final held hit from here
last_bar = int(END // BAR)


def section(bar):               # which layers play in this bar
    if bar < 2:
        return {'ost_soft'}                                         # opening: ticking strings under the first shot
    if bar < 10:
        return {'ost', 'kick', 'bass', 'brass'}
    if bar < 18:
        return {'ost', 'kick', 'bass', 'brass', 'snare', 'motif'}
    if bar < last_bar - 2:
        return {'ost', 'kick', 'bass', 'brass', 'snare', 'motif', 'taiko', 'high'}
    return {'ost_soft', 'bass', 'motif'}                            # breath before the end card


strL, strR = np.zeros(N), np.zeros(N)
brassL, brassR = np.zeros(N), np.zeros(N)
bass, drums, kick_env = np.zeros(N), np.zeros(N), np.zeros(N)
lead = np.zeros(N)


def stab(m, length=0.11):       # short bowed-string note
    n = int(length * 2.4 * SR)
    t = np.arange(n) / SR
    x = saw(hz(m - 0.06), n, rng.random()) + saw(hz(m + 0.07), n, rng.random())
    return x * np.minimum(1, t / 0.006) * np.exp(-t / (length * 0.55))


def kick():
    n = int(0.30 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(48 + 80 * np.exp(-t * 30)) / SR) * np.exp(-t * 12)


def taiko():                    # big low drum
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * np.cumsum(58 + 45 * np.exp(-t * 18)) / SR) * np.exp(-t * 4.5)
    skin = filt(rng.standard_normal(n), 'band', [150, 900]) * np.exp(-t * 22)
    return body + 0.5 * skin


def snare():
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    return filt(rng.standard_normal(n), 'band', [1200, 5200]) * np.exp(-t * 20) + 0.5 * np.sin(2 * np.pi * 185 * t) * np.exp(-t * 30)


for bar in range(n_bars):
    t0 = bar * BAR
    if t0 >= END:
        break
    on = section(bar)
    c = CHORDS[bar % 4]
    r = c['root']
    # sixteenth-note ostinato on root / fifth / octave, accents on the beat
    if 'ost' in on or 'ost_soft' in on:
        pat = [r + 24, r + 24, c['fifth'] + 24, r + 24, r + 36, r + 24, c['fifth'] + 24, c['third'] + 24]
        g0 = 0.050 if 'ost' in on else 0.026
        for s in range(16):
            x = stab(pat[s % 8])
            g = g0 * (1.35 if s % 4 == 0 else 0.8 if s % 2 else 1.0)
            add(strL, t0 + s * BEAT / 4, x, g * (0.65 if s % 2 else 1.0))
            add(strR, t0 + s * BEAT / 4, x, g * (1.0 if s % 2 else 0.65))
    # low brass: root, fifth, octave, third; swells into each bar
    if 'brass' in on:
        n = int((BAR + 0.25) * SR)
        e = env(n, 0.09, 0.3) * (0.75 + 0.25 * np.minimum(1, np.arange(n) / (0.8 * SR)))
        for m, pan in ((r, 0.5), (c['fifth'], 0.35), (r + 12, 0.6), (c['third'] + 12, 0.7)):
            x = sum(saw(hz(m + d), n, rng.random()) for d in (-0.05, 0, 0.06)) * e * 0.036
            add(brassL, t0, x, 1 - pan)
            add(brassR, t0, x, pan)
    for b in range(4):
        tb = t0 + b * BEAT
        if 'kick' in on:
            add(drums, tb, kick(), 0.62)
            add(kick_env, tb, np.exp(-np.arange(int(0.25 * SR)) / (0.08 * SR)))
        if 'snare' in on and b in (1, 3):
            add(drums, tb, snare(), 0.20)
        if 'bass' in on:
            for e8 in range(2):
                n = int(BEAT / 2 * SR)
                t = np.arange(n) / SR
                x = (saw(hz(r - 12), n) * 0.5 + np.sin(2 * np.pi * hz(r - 12) * t)) * np.exp(-t * 6) * np.minimum(1, t / 0.004)
                add(bass, tb + e8 * BEAT / 2, x, 0.26)
    if 'taiko' in on:
        for at, g in ((0, 0.5), (2.5 * BEAT, 0.3), (3.5 * BEAT, 0.36)) + (((3.75 * BEAT, 0.3),) if bar % 4 == 3 else ()):
            add(drums, t0 + at, taiko(), g)
    # motif: two half notes a bar, with vibrato; an octave higher in the last block
    if 'motif' in on:
        for k, m in enumerate(MOTIF[bar % 8]):
            m += 12 if 'high' in on else 0
            n = int((2 * BEAT + 0.12) * SR)
            t = np.arange(n) / SR
            vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(1, t / 0.35)
            ph = np.cumsum(hz(m) * vib) / SR
            x = (2 * (ph % 1) - 1) * 0.6 + np.sin(2 * np.pi * ph) * 0.8
            add(lead, t0 + k * 2 * BEAT, x * env(n, 0.05, 0.14), 0.060 if 'high' in on else 0.075)

strL, strR = filt(strL, 'band', [260, 4200]), filt(strR, 'band', [260, 4200])
brassL, brassR = filt(brassL, 'low', 1500), filt(brassR, 'low', 1500)
bass = filt(bass, 'low', 380)
lead = filt(lead, 'low', 3400)
d = int(0.75 * BEAT * SR)                        # motif echo
leadL, leadR = lead.copy(), lead.copy()
leadR[d:] += 0.30 * lead[:-d]
leadL[2 * d:] += 0.18 * lead[:-2 * d]

L, R = np.zeros(N), np.zeros(N)


def riser(length):
    n = int(length * SR)
    t = np.arange(n) / n
    x = rng.standard_normal(n)
    y = np.zeros(n)
    for k in range(8):                                                # rising band, in slices
        a, b = k * n // 8, (k + 1) * n // 8
        y[a:b] = filt(x, 'high', 500 + 900 * k)[a:b]
    return y * t ** 2


def flyby(length=1.1):          # a car passing: filtered noise with a falling pitch, left to right
    n = int(length * SR)
    t = np.arange(n) / n
    f = 260 * (1.25 - 0.5 * t)                                         # Doppler drop
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + np.sin(2 * np.pi * np.cumsum(f * 2.01) / SR) * 0.25
    x = (filt(rng.standard_normal(n), 'band', [300, 2600]) * 0.6 + tone) * np.exp(-((t - 0.5) / 0.22) ** 2)
    return x * (1 - t), x * t


# opening hit under the first shot, risers into each block, a fly-by at each block change
t = np.arange(int(2.5 * SR)) / SR
hit = np.sin(2 * np.pi * np.cumsum(38 + 70 * np.exp(-t * 16)) / SR) * np.exp(-t * 2.6)
add(L, 0, hit, 0.55)
add(R, 0, hit, 0.55)
for bar in (2, 10, 18):
    if bar * BAR < END:
        rz = riser(1.9)
        add(L, bar * BAR - 1.9, rz, 0.06)
        add(R, bar * BAR - 1.9, rz, 0.06)
        fl, fr = flyby()
        add(L, bar * BAR - 0.55, fl, 0.10)
        add(R, bar * BAR - 0.55, fr, 0.10)

# end card: held D minor hit
c = CHORDS[0]
n = int((dur - END) * SR)
t = np.arange(n) / SR
endc = sum(saw(hz(m + dd), n, rng.random()) for m in (c['root'], c['fifth'], c['root'] + 12, c['third'] + 12, c['root'] + 24)
           for dd in (-0.07, 0.07)) * 0.035
endc = filt(endc, 'low', 1700) * np.exp(-t / 2.3)
boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-t * 18)) / SR) * np.exp(-t * 3.0)
tk = np.zeros(n)
x = taiko()[:n]
tk[:len(x)] = x
add(L, END, endc + 0.6 * boom + 0.3 * tk)
add(R, END, endc + 0.6 * boom + 0.3 * tk)

# mix: brass and bass duck slightly under the kick; a little room on everything
duck = 1 - 0.4 * np.clip(kick_env, 0, 1)
swell = np.minimum(1, np.arange(N) / (2.0 * SR))
L += strL * swell + brassL * duck + bass * duck + drums + leadL
R += strR * swell + brassR * duck + bass * duck + drums + leadR


def room(x):                    # four short feedback delays
    y = np.zeros_like(x)
    for ms, g in ((29.7, 0.72), (37.1, 0.70), (41.1, 0.68), (43.7, 0.66)):
        D = int(ms / 1000 * SR)
        a = np.zeros(D + 1)
        a[0], a[D] = 1, -g
        y += lfilter([1], a, x)
    return filt(y, 'low', 4500) * 0.25


mix = np.stack([L + 0.16 * room(L), R + 0.16 * room(R)], 1)
mix = filt(mix.T, 'high', 28).T
mix = np.tanh(mix * 1.4) / np.tanh(1.4)                                # gentle saturation / limiter
fade = int(3.0 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 1.5
mix *= 0.89 / np.abs(mix).max()

with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print(f'{out}: {dur:.1f} s, peak {np.abs(mix).max():.2f}, rms {np.sqrt((mix ** 2).mean()):.3f}')
