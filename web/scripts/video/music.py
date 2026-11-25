"""The f1.h reel score: an original track written to the reel's edit (126 BPM, D minor), the way a promo editor
scores a cut. Every section change lands on a picture cut. Instruments are in synth.py; nothing is sampled.

  intro      (start -> lights out)   a low drone swelling, ticking hats, a riser; a breath of silence before the drop
  the drop   (lights out)            crash + sub impact; kick, rolling bass and wide chords all land at once
  each cut   (the reel's "cut" cues) a one-beat riser, the drums drop out for half a beat, a crash on the cut,
                                     and the next section is bigger: the arpeggio comes in, then open hats, then
                                     the arpeggio goes up an octave and the chords open up
  the end    ("end" cue)             the band stops on a final D minor stab and impact, ringing out in the room

    build(cues, duration) -> stereo float array [n, 2] at 44.1 kHz, peak -1 dBFS
"""
import numpy as np

from synth import (SR, clap, crash, filt, hat, hz, impact, kick, pluck, reverb, riser, sub, supersaw)

BEAT = 60 / 126
CHORDS = {                                     # close voicings around D3, and the bass note for each
    'Dm': (('D3', 'F3', 'A3', 'D4'), 'D2'),
    'Bb': (('Bb2', 'D3', 'F3', 'Bb3'), 'Bb1'),
    'C': (('C3', 'E3', 'G3', 'C4'), 'C2'),
    'F': (('C3', 'F3', 'A3', 'C4'), 'F1'),
}
# one chord per two-beat-offset bar, so the cuts (6, 14 and 22 beats after lights out) fall on chord changes
PROGRESSION = ['Dm', 'Bb', 'Dm', 'C', 'Bb', 'F', 'Dm', 'C']


def _add(buf, x, t, gain=1.0):
    """Mix a mono or stereo sound into the stereo buffer at time t (seconds)."""
    i = int(round(t * SR))
    if i >= len(buf) or i + len(x) <= 0: return
    x = x if x.ndim == 2 else np.stack([x, x], axis=1)
    if i < 0: x, i = x[-i:], 0
    r = min(len(x), int(0.0008 * SR)); x = x.copy(); x[:r] *= np.linspace(0, 1, r)[:, None]   # no clicks on onsets
    j = min(len(buf), i + len(x)); buf[i:j] += x[: j - i] * gain


def _pan(x, p):
    """p from -1 (left) to 1 (right), constant power."""
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1)


def _bass(freq, dur):
    """The rolling bass: a sub sine with a short filtered saw on top for definition on phone speakers."""
    n = int(dur * SR); t = np.arange(n) / SR
    saw = 2 * ((freq * 2 * t) % 1.0) - 1
    top = filt(saw, 'low', 900) * (0.25 + 0.75 * np.exp(-t / 0.06)) * 0.6
    return sub(freq, dur, 0.55) + top * np.minimum(1, t / 0.003)


def _comp(x, thr=0.25, ratio=3.0, attack=0.004, release=0.12):
    """Glue compressor on a stereo bus: linked peak detector, smooth gain."""
    from scipy.signal import lfilter
    level = np.max(np.abs(x), axis=1)
    a = np.exp(-1 / (release * SR))
    envl = lfilter([1 - a], [1, -a], level)              # release-shaped envelope
    envl = np.maximum(envl, filt(level, 'low', 1 / (2 * np.pi * attack)))
    g = np.where(envl > thr, (thr / np.maximum(envl, 1e-9)) ** (1 - 1 / ratio), 1.0)
    return x * g[:, None]


def _ducker(n, kicks, depth=0.6, recover=0.13):
    """Sidechain: the bass and chords dip on every kick and swell back (the pumping feel)."""
    g = np.ones(n); t = np.arange(n) / SR
    for k in kicks:
        i = int(k * SR); j = min(n, i + int(4 * recover * SR))
        g[i:j] = np.minimum(g[i:j], 1 - depth * np.exp(-(t[i:j] - k) / recover))
    return g


def build(cues, duration):
    n = int(duration * SR) + SR
    out_t = next((q['t'] for q in cues if q['type'] == 'lightsout'), 6 * BEAT)
    end_t = next((q['t'] for q in cues if q['type'] == 'end'), duration - 3)
    cuts = sorted(q['t'] for q in cues if q['type'] == 'cut' and out_t < q['t'] < end_t)
    beats = np.arange(out_t, end_t - 1e-6, BEAT)          # the groove's beat grid, from lights out to the end card

    drums, bass, synths, fx = (np.zeros((n, 2)) for _ in range(4))

    # ---- intro: tension under the start lights --------------------------------------------------------------
    k = int(out_t * SR); t = np.arange(k) / SR
    drone = (np.sin(2 * np.pi * hz('D1') * t) + 0.5 * np.sin(2 * np.pi * hz('D2') * t)
             + 0.25 * filt(supersaw(hz('A2'), out_t, voices=5, bright=0.0)[:, 0], 'low', 300))
    drone *= (t / out_t) ** 1.5 * 0.4
    pad = sum(supersaw(hz(x), out_t, voices=7, bright=1.0) for x in CHORDS['Dm'][0]) / 4
    dark, open_ = filt(pad, 'low', 350), filt(pad, 'low', 3500)
    o = ((t / out_t) ** 2)[:, None]
    _add(synths, (dark * (1 - o) + open_ * o) * (0.3 + 0.7 * t / out_t)[:, None], 0, 1.4)
    _add(bass, drone[: max(0, k - int(0.06 * SR))], 0)                  # the breath before the drop: 60 ms of nothing
    for i in range(int(out_t / (BEAT / 2)) - 1):
        _add(drums, _pan(hat(level=0.18 + 0.1 * (i % 2)), 0.3 if i % 2 else -0.3), i * BEAT / 2)
    _add(fx, riser(2 * BEAT, 0.5), out_t - 2 * BEAT)

    # ---- the drop ---------------------------------------------------------------------------------------------
    _add(drums, crash(0.55), out_t)
    _add(bass, impact(0.45), out_t)

    # ---- sections: energy steps up at every cut ----------------------------------------------------------------
    def section(tb):
        return sum(tb >= c - 1e-6 for c in cuts)                       # 0 before the first cut, 1 after it, ...

    kicks = []
    for bi, tb in enumerate(beats):
        s = section(tb)
        next_cut = next((c for c in cuts if c > tb + 1e-6), end_t)
        dropout = next_cut - tb <= BEAT + 1e-6          # the beat before a cut: only the kick, the riser takes over
        _add(drums, kick(0.55), tb); kicks.append(tb)
        if bi % 2 == 1 and not dropout:
            _add(drums, _pan(clap(0.8), 0.05), tb)
        if not dropout:                                               # offbeat hat; open hats from the second cut on
            _add(drums, _pan(hat(open_=s >= 2, level=0.32), 0.25), tb + BEAT / 2)
            if s >= 1:
                for q in (0.25, 0.75):
                    _add(drums, _pan(hat(level=0.12), -0.35), tb + q * BEAT)

    for c in cuts:                                                     # the editor's move on every cut
        _add(fx, riser(BEAT, 0.55), c - BEAT)
        _add(drums, crash(0.5), c)
        _add(bass, impact(0.25), c)

    # ---- harmony: chords, rolling bass, arpeggio ----------------------------------------------------------------
    marks = [out_t] + [out_t + (2 + 4 * i) * BEAT for i in range(64)]
    marks = [m for m in marks if m < end_t - 1e-6] + [end_t]
    for ci in range(len(marks) - 1):
        a, b = marks[ci], marks[ci + 1]
        notes, root = CHORDS[PROGRESSION[ci % len(PROGRESSION)]]
        s = section(a + 1e-3)
        bright = (0.45, 0.6, 0.75, 0.9)[min(s, 3)]
        pad = sum(supersaw(hz(x), b - a + 0.05, voices=7, detune=0.011 + 0.003 * s, bright=bright) for x in notes) / len(notes)
        m = len(pad); fade = np.minimum(1, np.arange(m) / (0.008 * SR)) * np.minimum(1, (m - np.arange(m)) / (0.04 * SR))
        _add(synths, pad * fade[:, None], a, 2.3 + 0.3 * s)
        tb = a
        while tb < b - 1e-6:                                          # bass on the offbeat 8ths (the kick owns the beat)
            _add(bass, _bass(hz(root), BEAT / 2 * 0.9), tb + BEAT / 2, 0.8)
            tb += BEAT
        if s >= 1:                                                     # 16th-note arpeggio over the chord
            oct_up = 2.0 if s >= 3 else 1.0
            tones = [hz(x) * 2 * oct_up for x in notes]
            pattern = [0, 2, 3, 1, 2, 3, 0, 2]
            i, tb = 0, a
            while tb < b - BEAT / 4 + 1e-6:
                f = tones[pattern[i % len(pattern)] % len(tones)]
                _add(synths, _pan(pluck(f, 0.2, 0.5), -0.45 if i % 2 else 0.45), tb)
                i += 1; tb += BEAT / 4

    # ---- the end: a final stab, ringing out -----------------------------------------------------------------------
    notes, root = CHORDS['Dm']
    stab = sum(supersaw(hz(x), 3.2, voices=7, detune=0.014, bright=0.8) for x in notes + ('A4', 'D5')) / 6
    stab *= np.exp(-np.arange(len(stab)) / (0.9 * SR))[:, None]
    _add(synths, stab, end_t, 2.2)
    _add(bass, sub(hz('D1'), 2.6, 0.55) * np.exp(-np.arange(int(2.6 * SR)) / (0.8 * SR)), end_t)
    _add(bass, impact(0.5), end_t)
    _add(drums, kick(0.65), end_t)
    _add(drums, crash(0.6), end_t)

    # ---- mix ------------------------------------------------------------------------------------------------------
    pump = _ducker(n, kicks)[:, None]
    bass = filt(bass, 'high', 28) * pump
    synths = reverb(filt(synths, 'high', 160), 1.6, 0.25) * (0.35 + 0.65 * pump)
    drums = reverb(filt(drums, 'high', 38), 0.9, 0.1)
    fx = reverb(filt(fx, 'high', 200), 1.8, 0.3)
    mixdown = 1.0 * drums + 0.75 * bass + 1.0 * synths + 0.55 * fx
    mixdown = _comp(mixdown, thr=0.35, ratio=2.5)
    mixdown = mixdown / (np.sqrt(np.mean(mixdown[: int(end_t * SR)] ** 2)) + 1e-9) * 0.2   # about -14 dBFS RMS
    mixdown = 0.9 * np.tanh(mixdown / 0.9)                                                  # soft ceiling at -1 dBFS
    return mixdown[:n]


if __name__ == '__main__':                     # python music.py cues.json out.wav  (the score alone, for listening)
    import json, sys, wave
    c = json.load(open(sys.argv[1]))
    x = build(c['cues'], c['duration'])[: int(c['duration'] * SR)]
    with wave.open(sys.argv[2], 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    print(f'score: {c["duration"]:.2f} s, peak {np.max(np.abs(x)):.2f}, rms {np.sqrt(np.mean(x ** 2)):.3f}')
