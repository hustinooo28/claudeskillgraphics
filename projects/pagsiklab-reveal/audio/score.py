"""Original score + sound design for the PAGSIKLAB house reveal (numpy/scipy only).
3/4 in D minor at 98.2 bpm, so one bar = 11/6 s and every house window (11 s) is exactly 6 bars.
Writes build/score.wav (48 kHz stereo)."""
import os, sys, math
import numpy as np
from scipy import signal
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import realm as R

SR = 48000
N = int(SR * R.END) + SR
rng = np.random.default_rng(11)
BAR = R.HOUSE_LEN / 6
BEAT = BAR / 3
THEME_START = R.HOUSE_START - 3 * BAR          # 3 bars of ostinato under the descent onto the map
BUS = {k: np.zeros((N, 2)) for k in ('music', 'drums', 'sfx', 'hits', 'vo', 'verb')}


# ---------------- primitives ----------------
def tt(d): return np.arange(int(d * SR)) / SR
def noise(d): return rng.standard_normal(int(d * SR))
def midi(n): return 440.0 * 2 ** ((n - 69) / 12)


def filt(x, kind, f, order=2):
    f = np.atleast_1d(np.clip(f, 20, SR / 2 - 200))
    sos = signal.butter(order, f if len(f) > 1 else f[0], btype=kind, fs=SR, output='sos')
    return signal.sosfilt(sos, x)


def env(n, a, d, s, r, hold):
    a, d, r = max(int(a * SR), 1), max(int(d * SR), 1), max(int(r * SR), 1)
    hold = max(int(hold * SR) - a - d, 0)
    e = np.concatenate([np.linspace(0, 1, a), np.linspace(1, s, d), np.full(hold, s), np.linspace(s, 0, r)])
    return np.pad(e, (0, max(n - len(e), 0)))[:n]


def saw(f, d, detune=(0.0,), vib=0.0):
    t = tt(d)
    out = np.zeros_like(t)
    for dt in detune:
        ff = f * (1 + dt) * (1 + vib * np.sin(2 * np.pi * 5.2 * t) * np.clip(t / 0.4, 0, 1))
        ph = np.cumsum(ff) / SR + rng.random()
        out += 2 * (ph % 1) - 1
    return out / len(detune)


def add(bus, x, start, gain=1.0, pan=0.0, send=0.25):
    i = int(start * SR)
    if i < 0:
        x, i = x[-i:], 0
    j = min(i + len(x), N)
    if j <= i:
        return
    L, Rr = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    seg = x[:j - i] * gain
    BUS[bus][i:j, 0] += seg * L
    BUS[bus][i:j, 1] += seg * Rr
    BUS['verb'][i:j, 0] += seg * L * send
    BUS['verb'][i:j, 1] += seg * Rr * send
    v = BUS.setdefault('verb_' + bus, np.zeros((N, 2)))
    v[i:j, 0] += seg * L * send
    v[i:j, 1] += seg * Rr * send


# ---------------- recorded one-shots (cut from the council's cinematic SFX reel by cut_sfx.py) ----------------
import soundfile as _sf
_SMP = {}


def smp(name, rate=1.0, mono=True):
    """a sample, peak-normalised; rate < 1 plays it slower and lower"""
    if name not in _SMP:
        x, sr = _sf.read(os.path.join(HERE, 'sfx', name + '.flac'), dtype='float64')
        _SMP[name] = signal.resample_poly(x, SR, sr) if sr != SR else x
    x = _SMP[name]
    if rate != 1.0:
        x = signal.resample(x, int(len(x) / rate))
    x = x.mean(1) if mono and x.ndim == 2 else x
    return x / (np.abs(x).max() + 1e-9)


def add_st(bus, x, start, gain=1.0, send=0.25):
    """stereo sample: left and right as recorded"""
    add(bus, x[:, 0], start, gain, pan=-1.0, send=send)
    add(bus, x[:, 1], start, gain, pan=1.0, send=send)


# ---------------- instruments ----------------
def cello(note, d, vel=1.0):
    f = midi(note)
    x = saw(f, d + 0.25, (-0.004, 0.0, 0.005), vib=0.003)
    n = len(x)
    e = env(n, 0.012, 0.12, 0.45, 0.18, d)
    cut = filt(x * e, 'lowpass', 900 + 900 * vel, order=2)
    bow = filt(noise(d + 0.25), 'bandpass', [1500, 5000]) * env(n, 0.005, 0.05, 0.0, 0.02, 0.05) * 0.15
    return (cut + bow) * vel


def strings(note, d, vel=1.0, bright=2200):
    f = midi(note)
    x = saw(f, d + 0.8, (-0.006, -0.002, 0.003, 0.007), vib=0.004)
    e = env(len(x), 0.35, 0.3, 0.85, 0.8, d)
    return filt(x * e, 'lowpass', bright) * vel


def horn(note, d, vel=1.0):
    f = midi(note)
    t = tt(d + 0.5)
    x = saw(f, d + 0.5, (-0.003, 0.003), vib=0.003) * 0.7 + np.sign(np.sin(2 * np.pi * f * t)) * 0.3
    e = env(len(x), 0.09, 0.2, 0.8, 0.4, d)
    fc = 500 + 1100 * vel * np.clip(t / 0.25, 0, 1)
    y = np.zeros_like(x)
    for k in range(0, len(x), 2048):           # brightening "swell" as the note opens up
        y[k:k + 2048] = filt(x[k:k + 2048] * e[k:k + 2048], 'lowpass', float(fc[min(k, len(fc) - 1)]))
    return y * vel


def choir(note, d, vel=1.0):
    f = midi(note)
    x = saw(f, d + 1.0, (-0.008, -0.003, 0.002, 0.007), vib=0.005)
    e = env(len(x), 0.6, 0.4, 0.85, 1.0, d)
    y = sum(filt(x, 'bandpass', [fc * 0.85, fc * 1.15]) * g for fc, g in ((730, 1.0), (1090, 0.6), (2440, 0.25)))
    return y * e * vel


def taiko(d=1.2, f=55, vel=1.0):
    t = tt(d)
    body = np.sin(2 * np.pi * np.cumsum(f * (1 + 1.3 * np.exp(-t / 0.03))) / SR) * np.exp(-t / 0.32)
    skin = filt(noise(d), 'bandpass', [120, 1500]) * np.exp(-t / 0.035) * 0.7
    return np.tanh((body + skin) * 1.8) * vel


def boom(d=3.0, f0=120, f1=28, decay=1.4):
    t = tt(d)
    f = f1 + (f0 - f1) * np.exp(-t / 0.09)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / decay)
    click = filt(noise(d), 'lowpass', 900) * np.exp(-t / 0.05) * 0.6
    return np.tanh((body + click) * 2.0)


def braam(d=4.0, root=38, bright=1500):
    t = tt(d)
    x = sum(saw(midi(root + iv), d, (-0.004, 0.0, 0.004)) / (1 + k * 0.4) for k, iv in enumerate((0, 7, 12, 15, 19)))
    e = np.minimum(t / 0.05, 1) * np.exp(-t / (d * 0.45))
    fc = 180 + bright * np.exp(-t / 0.8)
    y = np.zeros_like(x)
    for k in range(0, len(x), 2048):
        y[k:k + 2048] = filt(x[k:k + 2048], 'lowpass', float(fc[min(k, len(fc) - 1)]))
    return np.tanh(y * e * 1.4)


def riser(d):
    t = tt(d)
    u = t / d
    x = np.zeros_like(t)
    for k in range(0, len(x), 2048):
        fc = 200 * (8000 / 200) ** u[k]
        x[k:k + 2048] = filt(noise(len(x[k:k + 2048]) / SR), 'bandpass', [fc * 0.7, fc * 1.4])
    tone = sum(np.sin(2 * np.pi * np.cumsum(f0 * 2 ** (1.5 * u)) / SR) for f0 in (110, 220, 330))
    return (x * 1.2 + tone * 0.25) * u ** 2.2


def whoosh(d, f0, f1):
    t = tt(d)
    u = t / d
    x = np.zeros_like(t)
    for k in range(0, len(x), 1024):
        fc = f0 * (f1 / f0) ** u[k]
        x[k:k + 1024] = filt(noise(len(x[k:k + 1024]) / SR), 'bandpass', [fc * 0.6, fc * 1.6])
    return x * np.sin(np.pi * u) ** 2


def chime(f=1320, d=2.5):
    t = tt(d)
    return sum(np.sin(2 * np.pi * f * m * t) * a * np.exp(-t / dd) for m, a, dd in ((1, 1, 1.2), (2.76, 0.5, 0.6), (5.4, 0.3, 0.3)))


def tick(f=2600):
    t = tt(0.06)
    return filt(noise(0.06), 'bandpass', [f * 0.7, f * 1.4]) * np.exp(-t / 0.008)


def clunk():
    t = tt(0.35)
    wood = np.sin(2 * np.pi * np.cumsum(180 * (1 + 0.5 * np.exp(-t / 0.01))) / SR) * np.exp(-t / 0.06)
    return wood + filt(noise(0.35), 'bandpass', [300, 2500]) * np.exp(-t / 0.02) * 0.6


def wind(d):
    x = filt(noise(d), 'bandpass', [250, 1200])
    return x * (0.6 + 0.4 * np.sin(2 * np.pi * 0.17 * tt(d) + 1))


# ---------------- harmony ----------------
# 6-bar phrase: Dm  Bb  F  C  Gm  A   (roots as MIDI, octave 2)
PROG = [(38, 'm'), (34, 'M'), (41, 'M'), (36, 'M'), (43, 'm'), (45, 'M')]
THIRD = {'m': 3, 'M': 4}
MELODY = [  # (midi, beats) per bar, original line
    [(69, 3)], [(74, 2), (72, 1)], [(69, 3)], [(67, 2), (64, 1)], [(70, 2), (74, 1)], [(73, 3)]]


def ostinato(bar_t, root, q, vel):
    """six-eighth cello figure: root, fifth, octave, tenth, fifth, octave"""
    figure = [0, 7, 12, 12 + THIRD[q], 7, 12]
    for k, iv in enumerate(figure):
        add('music', cello(root + 12 + iv, BEAT / 2 * 0.9, vel * (1.0 if k in (0, 3) else 0.8)),
            bar_t + k * BEAT / 2, 0.16, pan=-0.25, send=0.25)


def phrase(t0, layer):
    """one 6-bar phrase (= one house). layer 0..6 adds instruments as the reveal builds"""
    for b, (root, q) in enumerate(PROG):
        bt = t0 + b * BAR
        ostinato(bt, root, q, 0.8 + 0.04 * layer)
        if layer >= 1:   # low strings: sustained root + fifth
            add('music', strings(root, BAR, 0.8, 900), bt, 0.10, pan=-0.1, send=0.4)
            add('music', strings(root + 7, BAR, 0.6, 1100), bt, 0.07, pan=0.2, send=0.4)
        if layer >= 2:   # violas: third and fifth an octave up
            add('music', strings(root + 12 + THIRD[q], BAR, 0.6, 1800), bt, 0.07, pan=0.35, send=0.5)
        if layer >= 3:   # horns carry the melody
            beat = 0
            for note, dur in MELODY[b]:
                add('music', horn(note - 12, dur * BEAT * 0.95, 0.8), bt + beat * BEAT, 0.11, pan=0.1, send=0.55)
                beat += dur
        if layer >= 4:   # high strings double the melody
            beat = 0
            for note, dur in MELODY[b]:
                add('music', strings(note, dur * BEAT * 0.98, 0.7, 3200), bt + beat * BEAT, 0.07, pan=-0.3, send=0.6)
                beat += dur
        if layer >= 5:
            add('music', choir(root + 24 + THIRD[q], BAR, 0.8), bt, 0.06, pan=0.0, send=0.8)
        # drums: downbeat taiko from the start, more as we go
        add('drums', taiko(1.2, 52, 1.0), bt, 0.32 + 0.03 * layer, pan=0.0, send=0.3)
        if layer >= 2:
            add('drums', taiko(0.8, 68, 0.6), bt + 2 * BEAT, 0.18, pan=0.3, send=0.3)
        if layer >= 4:
            add('drums', taiko(0.6, 80, 0.5), bt + 2.5 * BEAT, 0.14, pan=-0.3, send=0.3)


# ---------------- arrangement ----------------
# cold open: the trophy hall, then the words alone
add('sfx', wind(7.0) * np.minimum(tt(7.0) / 2, 1) * np.clip((7.0 - tt(7.0)) / 1.5, 0, 1), 0.0, 0.08, send=0.4)
add('music', strings(26, 6.2, 1.0, 380), 0.2, 0.18, send=0.5)
add('hits', smp('boom_cavernous_b', 0.92), 1.6, 0.55, send=0.4)
add_st('sfx', smp('drone_nocturnal', 0.66, mono=False) * np.minimum(tt(len(smp('drone_nocturnal', 0.66)) / SR) / 1.5, 1)[:, None], 0.0, 0.10, send=0.3)
add('music', choir(62, 4.5, 0.7), 1.8, 0.05, send=0.9)
add('sfx', chime(660, 3.5), 1.65, 0.035, send=0.9)


def anvil():
    t = tt(2.2)
    ring = sum(np.sin(2 * np.pi * 820 * m * t + rng.random() * 6) * a * np.exp(-t / d)
               for m, a, d in ((1, 1.0, 0.9), (2.32, 0.6, 0.5), (4.25, 0.4, 0.3), (6.63, 0.25, 0.18)))
    hit = filt(noise(2.2), 'highpass', 1800) * np.exp(-t / 0.025) * 1.5
    thump = np.sin(2 * np.pi * np.cumsum(90 * (1 + np.exp(-t / 0.02))) / SR) * np.exp(-t / 0.12)
    return ring * 0.6 + hit + thump


def sizzle(d=1.4):
    t = tt(d)
    return filt(noise(d), 'bandpass', [3000, 9000]) * np.exp(-t / 0.5) * (0.6 + 0.4 * np.sin(2 * np.pi * 23 * t))


# credits: the akashic (ink), the Local Student Council (chime)
c0 = R.CREDITS[0]
add('sfx', smp('downshifter', 1.15), c0 - 0.1, 0.30, send=0.4)
add('sfx', filt(noise(1.3), 'highpass', 3000) * np.exp(-tt(1.3) / 0.6) * 0.3, c0 + 0.25, 0.12, pan=-0.3, send=0.2)
add('music', strings(50, 3.0, 0.7, 1600), c0, 0.07, send=0.7)
add('music', strings(38, 3.4, 0.9, 900), c0 + 3.0, 0.10, send=0.6)
add('sfx', chime(990, 3.0), c0 + 3.1, 0.04, send=0.8)
add('hits', smp('braam_up_under', 1.0), c0 + 3.0, 0.30, send=0.5)
_r12 = smp('riser_12')
add('sfx', _r12, R.CLOUD_BREAK - len(_r12) / SR, 0.35, send=0.3)

# the dive: rushing air through the clouds, a deck bursting open as the music opens up, then the low run past the peaks
dive = R.CLOUD_BREAK - R.MAP_IN[0]
add('sfx', wind(dive) * (np.minimum(tt(dive) / 0.8, 1) * (0.6 + 0.4 * tt(dive) / dive)), R.MAP_IN[0], 0.14, send=0.4)
add('hits', smp('boom_big_reveal'), R.CLOUD_BREAK, 0.7, send=0.4)
add('sfx', whoosh(2.4, 300, 3000), R.CLOUD_BREAK - 0.1, 0.4, send=0.5)
add('sfx', wind(6.0) * np.exp(-tt(6.0) / 2.5), R.CLOUD_BREAK, 0.12, send=0.4)
for k, st in enumerate((19.1, 20.1, 21.1)):                  # peaks and treetops rushing past
    add('sfx', whoosh(1.1, 400, 2600), st, 0.16, pan=(0.35, -0.35, 0.2)[k], send=0.35)

# the theme: 3 bars under the descent, then one phrase per house (+ the campus)
for b in range(3):
    root, q = PROG[3 + b]
    ostinato(THEME_START + b * BAR, root, q, 0.7)
for i in range(7):
    s = R.house_window(i)[0] if i < 6 else R.CAMPUS_WIN[0]
    phrase(s, min(i, 5) + (1 if i == 6 else 0))
    # clockwork while the seat assembles
    build0 = s + 0.7
    for k in range(int(3.2 / 0.11)):
        add('sfx', tick(2200 + 900 * (k % 3)), build0 + k * 0.11, 0.07, pan=float(rng.uniform(-0.5, 0.5)), send=0.15)
    for k in range(9):
        add('sfx', clunk(), build0 + 0.4 + k * 0.32 + float(rng.uniform(-0.05, 0.05)), 0.10, pan=float(rng.uniform(-0.6, 0.6)), send=0.25)
    # the medallion lands
    add('sfx', whoosh(1.0, 600, 2500), s + 0.7 + 2.6 + 0.6, 0.12, send=0.4)
    if i < 6:
        add('hits', smp(('boom_cavernous_a', 'boom_cavernous_b', 'boom_morphing')[i % 3], (1.0, 0.95, 1.05, 0.9, 1.0, 0.93)[i]),
            s + 0.7 + 2.6 + 1.6, 0.38, send=0.35)
    else:                                    # the seat of the realm gets the big braam
        add('hits', smp('braam_massive'), s + 0.7 + 2.6 + 1.6, 0.6, send=0.5)
    add('sfx', chime(1180 + 60 * i, 2.5), s + 0.7 + 2.6 + 1.6, 0.06, pan=0.3, send=0.8)
    # flight to the next seat
    add('sfx', whoosh(1.6, 300, 1800), s + R.HOUSE_LEN - 1.45, 0.22, send=0.4)

# the guide dragon: wingbeats on every flight, a roar as it lands on the campus roof and as it takes off
def wingbeat():
    t = tt(0.45)
    x = filt(noise(0.45), 'bandpass', [90, 700]) * np.sin(np.pi * np.clip(t / 0.4, 0, 1)) ** 2
    return x + np.sin(2 * np.pi * 55 * t) * np.exp(-t / 0.12) * 0.6


def dragon_roar(d=1.8, base=70):
    t = tt(d)
    u = t / d
    f0 = base * (0.85 + 0.45 * np.sin(np.pi * np.minimum(u * 1.25, 1)) ** 0.8)
    src = saw(f0, d) * (1 + 0.5 * np.sin(2 * np.pi * 27 * t)) + noise(d) * 0.3
    x = sum(filt(src, 'bandpass', [fc * 0.75, fc * 1.3]) * g for fc, g in ((380, 1.0), (950, 0.8), (2300, 0.4)))
    return np.tanh(x * 2.5) * np.minimum(t / 0.2, 1) * np.clip((d - t) / 0.7, 0, 1)


DWELL_ = R.HOUSE_LEN - 1.3
flights = [(R.MAP_IN[0] + 1.0, R.HOUSE_START)] + [(R.house_window(i)[0] + DWELL_, R.house_window(i)[0] + R.HOUSE_LEN) for i in range(6)]
for f0_, f1_ in flights:
    k = 0
    while f0_ + k / 1.9 < f1_:
        add('sfx', wingbeat(), f0_ + k / 1.9, 0.20, pan=0.2 * math.sin(k), send=0.35)
        k += 1
add('sfx', dragon_roar(2.0, 66), R.CAMPUS_WIN[0] + 7.4, 0.32, pan=0.15, send=0.6)
for k in range(5):
    add('sfx', wingbeat(), R.CAMPUS_WIN[0] + 5.0 + k / 2.4, 0.22, send=0.35)
add('sfx', dragon_roar(1.6, 80), R.OVERVIEW[0] + 0.3, 0.30, pan=-0.2, send=0.7)
for k in range(7):
    add('sfx', wingbeat(), R.OVERVIEW[0] + 0.5 + k / 1.9, 0.2, send=0.4)

# a new era is here: the drums stop, a held chord and choir swell, then a riser into the title
o0, o1 = R.OVERVIEW
add('music', strings(38, o1 - o0, 1.0, 1400), o0, 0.12, send=0.7)
add('music', strings(45, o1 - o0, 0.8, 1800), o0, 0.08, pan=0.3, send=0.7)
add('music', strings(53, o1 - o0, 0.7, 2600), o0, 0.06, pan=-0.3, send=0.7)
add('music', choir(62, o1 - o0 - 0.5, 0.9), o0 + 0.5, 0.08, send=0.9)
add('hits', smp('boom_cavernous_a', 0.85), o0, 0.5, send=0.4)
_r02 = smp('riser_02', mono=False)
add_st('sfx', _r02, R.TITLE[0] + 0.7 - len(_r02) / SR, 0.45, send=0.3)       # rises into the breath of silence
add('sfx', smp('tension_dramatic'), o0 + 0.8, 0.22, send=0.4)

# title: silence, then the hit as the wordmark ignites
t0 = R.TITLE[0] + 1.2
add('hits', smp('boom_big_reveal'), t0, 0.9, send=0.4)
add('hits', smp('boom_earthcore', 0.9), t0, 0.55, send=0.5)
add_st('sfx', smp('drone_stellar', mono=False) * np.minimum(tt(13.0) / 3.0, 1)[:len(smp('drone_stellar'))][:, None], t0 + 2.0, 0.10, send=0.3)
add('music', braam(6.0, 38, 2400), t0, 0.5, send=0.5)
add('drums', taiko(1.5, 48, 1.0), t0, 0.5, send=0.3)
for b, (root, q) in enumerate([(38, 'm'), (34, 'M'), (45, 'M')]):
    bt = t0 + 1.0 + b * BAR * 1.5
    add('music', strings(root + 12, BAR * 1.5, 0.9, 2400), bt, 0.10, send=0.7)
    add('music', strings(root + 19, BAR * 1.5, 0.8, 2800), bt, 0.07, pan=0.3, send=0.7)
    add('music', choir(root + 24 + THIRD[q], BAR * 1.5, 0.9), bt, 0.07, send=0.9)
    add('drums', taiko(1.2, 52, 0.9), bt, 0.35, send=0.3)
add('music', strings(26, 6.0, 1.0, 600), t0 + 6.5, 0.16, send=0.6)     # final low D under the end card
add('sfx', chime(880, 4.0), t0 + 4.0, 0.05, send=0.9)

# the voice: "Who will reign?" as the words resolve on screen (deep male, pitched down, in a stone hall)
import soundfile as _sf
_vo, _sr = _sf.read(os.path.join(HERE, 'vo_who_raw.wav'), dtype='float64')
_vo = signal.resample_poly(_vo, 48000, _sr)
_vo = signal.resample(_vo, int(len(_vo) / 2 ** (-3 / 12)))          # -3 semitones (slower and lower)
_vo = filt(_vo, 'highpass', 55) + filt(_vo, 'lowpass', 220) * 0.6     # chest warmth
_vo = np.tanh(_vo / np.abs(_vo).max() * 1.6) / np.tanh(1.6)
VO_AT = 1.75
add('vo', _vo, VO_AT, 0.55, send=0.9)
add('vo', np.concatenate([np.zeros(int(0.32 * SR)), filt(_vo, 'lowpass', 1800)]), VO_AT, 0.10, pan=-0.4, send=1.0)   # hall echo
add('vo', np.concatenate([np.zeros(int(0.55 * SR)), filt(_vo, 'lowpass', 1200)]), VO_AT, 0.06, pan=0.4, send=1.0)

# ---------------- mix ----------------
ir_t = tt(3.5)
ir = np.stack([filt(rng.standard_normal(len(ir_t)), 'lowpass', 6000) * np.exp(-ir_t / 0.9) for _ in range(2)], 1)
ir[:int(0.03 * SR)] = 0
ir /= np.sqrt((ir ** 2).sum(0))
verb = np.stack([signal.fftconvolve(BUS['verb'][:, c], ir[:, c])[:N] for c in range(2)], 1)
_duck = np.ones(N)
_d0, _d1 = int((VO_AT - 0.2) * SR), int((VO_AT + len(_vo) / SR + 0.3) * SR)
_duck[_d0:_d1] = 0.55
_duck = np.convolve(_duck, np.ones(4800) / 4800, mode='same')
BUS['music'] *= _duck[:, None]
mix = BUS['music'] * 2.0 + BUS['drums'] * 0.65 + BUS['sfx'] * 1.1 + BUS['hits'] * 0.65 + BUS['vo'] + verb * 0.6
fx = BUS['sfx'] * 1.1 + BUS['hits'] * 0.6 + np.stack([signal.fftconvolve((BUS['verb_sfx'] + BUS['verb_hits'] * 0.55)[:, c], ir[:, c])[:N] for c in range(2)], 1) * 0.6
np.save(os.path.join(os.path.dirname(HERE), 'build', 'fx_stem.npy'), fx[:int(R.END * SR)].astype(np.float32))
np.save(os.path.join(os.path.dirname(HERE), 'build', 'vo_span.npy'), np.array([VO_AT, VO_AT + len(_vo) / SR]))
vo_stem = BUS['vo'] + np.stack([signal.fftconvolve(BUS['verb_vo'][:, c], ir[:, c])[:N] for c in range(2)], 1) * 0.6
np.save(os.path.join(os.path.dirname(HERE), 'build', 'vo_stem.npy'), vo_stem[:int(R.END * SR)].astype(np.float32))
# the moment of silence before the title
g = np.ones(N)
a, b = int((R.TITLE[0] + 0.7) * SR), int((R.TITLE[0] + 1.2) * SR)
g[a:b] = np.linspace(1, 0.0, b - a) ** 2
g[b - int(0.05 * SR):b] = 0
mix[:b] *= g[:b, None]
mix = np.stack([filt(mix[:, c], 'highpass', 28) for c in range(2)], 1)
fade = np.ones(N)
k0 = int((R.END - 1.6) * SR)
fade[k0:] = np.clip(np.linspace(1, 0, N - k0) * 1.6, 0, 1) ** 2
mix *= fade[:, None]
mix = mix[:int(R.END * SR)]
mix = mix / np.abs(mix).max() * 1.2
mix = np.tanh(mix) / np.tanh(1.2) * 0.9
os.makedirs(os.path.join(os.path.dirname(HERE), 'build'), exist_ok=True)
wavfile.write(os.path.join(os.path.dirname(HERE), 'build', 'score.wav'), SR, (mix * 32767).astype(np.int16))
print('score written', mix.shape[0] / SR, 's')
