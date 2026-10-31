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
N = int(SR * (R.END + R.LEAD)) + SR             # film length: the opener is LEAD longer than the 3D timeline
OFS = 0.0                                      # added to every placement: 0 for the opener (film time), LEAD after
rng = np.random.default_rng(11)
BAR = R.HOUSE_LEN / 6
BEAT = BAR / 3
THEME_START = R.HOUSE_START - 3 * BAR          # 3 bars of ostinato under the descent onto the map
BUS = {k: np.zeros((N, 2)) for k in ('music', 'drums', 'sfx', 'hits', 'vo', 'verb', 'amb', 'trans')}


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
    i = int((start + OFS) * SR)
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


# the cold open (film time): a low hall tone under the trophy, a soft swell as the question appears
add('sfx', filt(noise(12.0), 'lowpass', 140) * np.minimum(tt(12.0) / 3.0, 1) * np.clip((12.6 - tt(12.0)) / 2.0, 0, 1), 0.5, 0.10, send=0.6)
add('hits', smp('boom_cavernous_b', 0.8), R.WHO_AT, 0.18, send=0.6)
# credits: the akashic (ink), the Local Student Council (chime), each on a swell of the track
c0, c1 = R.CREDITS[0], R.LSC_AT
add('sfx', smp('downshifter', 1.15), c0 - 0.1, 0.30, send=0.4)
add('sfx', filt(noise(2.4), 'highpass', 3000) * np.exp(-tt(2.4) / 0.9) * 0.3, c0 + 0.35, 0.12, pan=-0.3, send=0.2)   # the ink
add('music', strings(50, 3.0, 0.7, 1600), c0, 0.07, send=0.7)
add('music', strings(38, 3.4, 0.9, 900), c1, 0.10, send=0.6)
add('sfx', chime(990, 3.0), c1 + 0.1, 0.04, send=0.8)
add('hits', smp('braam_up_under', 1.0), c1, 0.30, send=0.5)
# into the drop: a riser through the breath of black, the music lands on the first frame in the clouds
_r12 = smp('riser_12')
add('sfx', _r12, R.OPEN_END - len(_r12) / SR, 0.35, send=0.3)
add('hits', smp('boom_big_reveal'), R.OPEN_END, 0.55, send=0.4)

OFS = R.LEAD                                   # everything below is placed on the 3D timeline
# the dive: rushing air through the clouds, a deck bursting open, then the low run past the peaks
dive = R.CLOUD_BREAK - R.MAP_IN[0]
add('sfx', wind(dive) * (np.minimum(tt(dive) / 0.8, 1) * (0.6 + 0.4 * tt(dive) / dive)), R.MAP_IN[0], 0.14, send=0.4)
add('hits', smp('boom_big_reveal', 0.9), R.CLOUD_BREAK, 0.45, send=0.4)
add('sfx', whoosh(2.4, 300, 3000), R.CLOUD_BREAK - 0.1, 0.4, send=0.5)
add('sfx', wind(6.0) * np.exp(-tt(6.0) / 2.5), R.CLOUD_BREAK, 0.12, send=0.4)
# the music steps up into its fullest section as the camera rises toward the first seat (final_mix.py's jump):
# a short riser into it and a deep hit on its downbeat
UP = 34.71 - 0.08 - R.LEAD
_r = smp('riser_12', 1.1)
add('sfx', _r, UP - len(_r) / SR, 0.25, send=0.3)
add('hits', smp('boom_cavernous_a', 0.9), UP, 0.4, send=0.4)
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

# ---------------- the world: an ambience for every seat, and a fly-by on every flight ----------------
# Two stems of their own, both written at unit level: final_mix.py sets them against the music's own loudness
# moment by moment (the beds well under it, the fly-bys and thunder a few dB under its peaks), so the music leads.
def colored(d, slope=-1.0):
    """noise with a 1/f^(slope) spectrum: -1 pink, -2 brown"""
    n = int(d * SR)
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    X *= np.maximum(f, 20.0) ** (slope / 2)
    x = np.fft.irfft(X, n)
    return x / (x.std() + 1e-12)


def drift(d, rate, lo=0.0, hi=1.0):
    """a smooth random modulator between lo and hi, changing about `rate` times a second"""
    k = max(int(d * rate) + 4, 4)
    pts = rng.random(k)
    y = np.interp(np.linspace(0, k - 3, int(d * SR)), np.arange(k), pts)
    y = filt(y, 'lowpass', max(rate * 1.5, 0.3), order=1) if rate < 10 else y
    y = (y - y.min()) / (np.ptp(y) + 1e-9)
    return lo + (hi - lo) * y


def tv_band(x, fc, q):
    """band-pass whose centre follows fc (an array, one value per sample), filtered in short blocks"""
    y = np.zeros_like(x)
    zi = np.zeros((1, 2))
    for k in range(0, len(x), 512):
        f0 = float(np.clip(fc[k], 40, SR / 2 - 400))
        sos = signal.butter(1, [f0 / (1 + 0.5 / q), f0 * (1 + 0.5 / q)], btype='band', fs=SR, output='sos')
        y[k:k + 512], zi = signal.sosfilt(sos, x[k:k + 512], zi=zi)
    return y


def grains(d, rate, f_lo, f_hi, dec=0.004, shape=1.6):
    """sparse random impulses (crackle, droplets, sand), each a tiny decaying burst"""
    n = int(d * SR)
    x = np.zeros(n)
    m = rng.poisson(rate * d)
    idx = rng.integers(0, n, m)
    x[idx] = (rng.pareto(shape, m) + 1) ** 0.8 * rng.choice([-1, 1], m)
    k = tt(dec * 6)
    x = signal.fftconvolve(x, np.exp(-k / dec) * rng.standard_normal(len(k)))[:n]
    return filt(x, 'bandpass', [f_lo, f_hi])


def unit(x):
    return x / (np.sqrt((x ** 2).mean()) + 1e-12)


def stereo(l, r):
    return np.stack([l, r], 1)


def fade_io(x, a, b):
    t = np.arange(len(x)) / SR
    e = np.minimum(t / max(a, 1e-3), 1) * np.clip((len(x) / SR - t) / max(b, 1e-3), 0, 1)
    return x * (e[:, None] if x.ndim == 2 else e)


def bird(f0):
    """a songbird phrase: a quick run of chirps"""
    out = []
    for _ in range(int(rng.integers(3, 8))):
        d = float(rng.uniform(0.035, 0.09))
        t = tt(d)
        u = t / d
        f = f0 * float(rng.uniform(0.85, 1.2)) * (1 + float(rng.uniform(-0.35, 0.35)) * u)
        ph = 2 * np.pi * np.cumsum(f) / SR
        out.append((np.sin(ph) + 0.15 * np.sin(2 * ph)) * np.sin(np.pi * u) ** 2)
        out.append(np.zeros(int(float(rng.uniform(0.02, 0.07)) * SR)))
    return np.concatenate(out)


def cry(f_hi, f_lo, d, rough=0.3):
    """a distant raptor / gull cry: a falling, slightly rough tone"""
    t = tt(d)
    u = t / d
    f = f_hi * (f_lo / f_hi) ** u ** 0.7 * (1 + 0.012 * np.sin(2 * np.pi * 31 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.45 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph)
    x = x * (1 + rough * filt(noise(d), 'lowpass', 300))
    return filt(x * np.sin(np.pi * np.minimum(u * 1.4, 1)) ** 0.6 * np.clip((1 - u) * 4, 0, 1), 'lowpass', 3200)


def howl(f0, d=3.2):
    """a lone wolf far off: rising, held with a tremble, falling away"""
    t = tt(d)
    u = t / d
    f = f0 * (0.75 + 0.35 * np.sin(np.pi * np.minimum(u * 2.2, 1) / 2) - 0.22 * np.clip((u - 0.65) / 0.35, 0, 1) ** 1.5)
    f = f * (1 + 0.012 * np.sin(2 * np.pi * 5.5 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph) + 0.08 * filt(noise(d), 'bandpass', [600, 1800])
    return filt(x * np.sin(np.pi * u) ** 0.8, 'lowpass', 1800)


def bell(f=130.81, d=7.0):
    """a great bronze bell on C (hum, prime, minor third, fifth, nominal ... all with their own decays)"""
    t = tt(d)
    parts = ((0.5, 0.8, 4.5), (1.0, 0.7, 3.2), (1.2, 0.55, 2.4), (1.5, 0.35, 1.8), (2.0, 0.6, 1.6),
             (2.51, 0.3, 0.9), (2.66, 0.25, 0.8), (3.01, 0.2, 0.6))
    x = sum(np.sin(2 * np.pi * f * m * (1 + 0.0007 * k) * t + k) * a * np.exp(-t / dd) for k, (m, a, dd) in enumerate(parts))
    strike = filt(noise(d), 'bandpass', [800, 3500]) * np.exp(-t / 0.012) * 0.6
    return x + strike


def thunder(close=True, d=6.0):
    """close: a tearing crack, then the roll; far: only the roll"""
    t = tt(d)
    roll = filt(colored(d, -2.0), 'lowpass', 160 if close else 110)
    sw = sum(np.exp(-((t - c) / w) ** 2) for c, w in zip(rng.uniform(0.2, d * 0.7, 5), rng.uniform(0.3, 0.9, 5)))
    roll = unit(roll) * (0.3 + sw) * np.exp(-t / (d * 0.45)) * np.minimum(t / (0.05 if close else 0.6), 1)
    if not close:
        return roll
    crack = filt(noise(d), 'highpass', 700) * np.exp(-t / 0.09) * 3.0
    rip = filt(noise(d), 'bandpass', [250, 2500]) * np.exp(-t / 0.45) * (0.5 + drift(d, 40)) * 1.4
    return roll + crack + rip


def flyby(d, pan0, pan1, peak=0.65):
    """the camera tearing through the air between seats: rising rush, a low whoomp at the fastest point,
    a falling (doppler) tail; swept across the stereo field the way the world moves on screen"""
    t = tt(d)
    u = t / d
    e = np.where(u < peak, (u / peak) ** 2.5, np.exp(-(u - peak) / 0.12))
    fc = np.where(u < peak, 300 * (2600 / 300) ** (u / peak), 2600 * (700 / 2600) ** np.clip((u - peak) / (1 - peak), 0, 1))
    air = tv_band(colored(d, -0.5), fc, 1.2) * e
    hiss = filt(noise(d), 'highpass', 4000) * e ** 1.5 * 0.25
    whoomp = np.sin(2 * np.pi * np.cumsum(55 * (1 - 0.4 * u)) / SR) * np.exp(-((u - peak) / 0.09) ** 2) * 0.9
    x = unit(air + hiss) + whoomp
    pan = pan0 + (pan1 - pan0) * np.clip((u - peak + 0.35) / 0.6, 0, 1)
    return stereo(x * np.cos((pan + 1) * np.pi / 4), x * np.sin((pan + 1) * np.pi / 4))


# the beds: one per seat, ~unit RMS
def bed_fire(d):      # Dragonstone: a volcanic rumble under the rock, the hiss and crackle of fire
    rum = filt(colored(d, -2), 'lowpass', 90) * drift(d, 0.4, 0.5, 1.0)
    roar = filt(noise(d), 'bandpass', [180, 900]) * drift(d, 2.0, 0.3, 1.0) * 0.35
    ch = [grains(d, 22, 1200, 7000, 0.003) * 0.9 for _ in range(2)]
    return stereo(unit(rum) + unit(roar) * 0.6 + unit(ch[0]) * 0.55, unit(rum) + unit(roar) * 0.6 + unit(ch[1]) * 0.55)


def bed_surf(d):      # Casterly Rock: surf breaking on the cliffs, gusts over the rock, a gull far off
    t = tt(d)
    w = np.zeros(len(t))
    for c in np.arange(float(rng.uniform(0.5, 2.0)), d, 5.6):
        w += np.where(t < c, np.exp(-((t - c) / 1.6) ** 2), np.exp(-(t - c) / 2.2))
    wash = filt(colored(d, -1), 'lowpass', 500) * 0.5
    crash = tv_band(colored(d, -1), 400 + 2200 * w, 0.7) * w
    gust = filt(noise(d), 'bandpass', [300, 1400]) * drift(d, 0.5, 0.1, 0.8) ** 2
    l, r = unit(wash) + unit(crash) * 1.2 + unit(gust) * 0.4, unit(wash) + unit(np.roll(crash, 9000)) * 1.2 + unit(gust) * 0.4
    g = cry(1900, 1300, 0.42) * 0.25
    at = int(d * 0.55 * SR)
    l[at:at + len(g)] += unit(g)[:len(l) - at] * 0.45
    return stereo(l, r)


def bed_meadow(d):    # Highgarden: a warm breeze in the leaves, songbirds all around
    rust = [filt(noise(d), 'bandpass', [1800, 7000]) * (0.3 + filt(np.abs(noise(d)), 'lowpass', 14)) * drift(d, 0.3, 0.3, 1.0) for _ in range(2)]
    breeze = filt(colored(d, -1), 'bandpass', [200, 900]) * drift(d, 0.25, 0.4, 1.0)
    l, r = unit(rust[0]) * 0.6 + unit(breeze) * 0.5, unit(rust[1]) * 0.6 + unit(breeze) * 0.5
    for _ in range(int(d * 0.9)):
        b = bird(float(rng.uniform(2600, 5200))) * 1.1
        at = int(rng.uniform(0, d - 1.0) * SR)
        p = float(rng.uniform(-0.9, 0.9))
        n = min(len(b), len(l) - at)
        l[at:at + n] += b[:n] * math.cos((p + 1) * math.pi / 4)
        r[at:at + n] += b[:n] * math.sin((p + 1) * math.pi / 4)
    return stereo(l, r)


def bed_blizzard(d):  # Winterfell: a howling gale, driven snow, and a wolf somewhere in the dark
    t = tt(d)
    how = [tv_band(colored(d, -1), drift(d, 0.35, 320, 880), 6.0) * drift(d, 0.4, 0.4, 1.0) for _ in range(2)]
    snow = [filt(noise(d), 'highpass', 2500) * drift(d, 0.6, 0.2, 1.0) for _ in range(2)]
    low = filt(colored(d, -2), 'lowpass', 120)
    l, r = unit(how[0]) + unit(snow[0]) * 0.45 + unit(low) * 0.5, unit(how[1]) + unit(snow[1]) * 0.45 + unit(low) * 0.5
    hw = howl(410)
    at = int(d * 0.42 * SR)
    n = min(len(hw), len(l) - at)
    l[at:at + n] += unit(hw)[:n] * 0.6
    r[at:at + n] += unit(hw)[:n] * 0.4
    return stereo(l, r)


def bed_desert(d):    # Sunspear: hot dry wind, sand hissing over the dunes, the dunes' low song, a hawk high above
    sand = [filt(noise(d), 'bandpass', [2500, 10000]) * drift(d, 0.5, 0.3, 1.0) ** 1.5 for _ in range(2)]
    grit = [grains(d, 260, 3000, 11000, 0.0015, 2.5) for _ in range(2)]
    wind_ = filt(colored(d, -1), 'bandpass', [150, 700]) * drift(d, 0.3, 0.5, 1.0)
    t = tt(d)
    song = (np.sin(2 * np.pi * 98 * t) + 0.4 * np.sin(2 * np.pi * 196.6 * t)) * drift(d, 0.2, 0.2, 1.0)
    l = unit(sand[0]) * 0.7 + unit(grit[0]) * 0.35 + unit(wind_) * 0.8 + unit(song) * 0.18
    r = unit(sand[1]) * 0.7 + unit(grit[1]) * 0.35 + unit(wind_) * 0.8 + unit(song) * 0.18
    hk = cry(2900, 2100, 0.9, 0.5)
    at = int(d * 0.3 * SR)
    n = min(len(hk), len(l) - at)
    r[at:at + n] += unit(hk)[:n] * 0.4
    l[at:at + n] += unit(hk)[:n] * 0.2
    return stereo(l, r)


def bed_storm(d):     # Storm's End: hard rain on stone, the wind driving it (the thunder is placed on the lightning)
    wash = [filt(colored(d, -1), 'bandpass', [400, 9000]) for _ in range(2)]
    drops = [grains(d, 900, 1500, 9000, 0.002, 2.2) for _ in range(2)]
    gust = filt(noise(d), 'bandpass', [250, 1100]) * drift(d, 0.6, 0.2, 1.0) ** 2
    return stereo(unit(wash[0]) + unit(drops[0]) * 0.6 + unit(gust) * 0.6, unit(wash[1]) + unit(drops[1]) * 0.6 + unit(gust) * 0.6)


def bed_campus(d):    # the seat of the realm: a warm breeze and palms rustling
    rust = [filt(noise(d), 'bandpass', [1200, 5000]) * (0.4 + filt(np.abs(noise(d)), 'lowpass', 9)) * drift(d, 0.3, 0.3, 1.0) for _ in range(2)]
    breeze = filt(colored(d, -1), 'bandpass', [150, 700]) * drift(d, 0.2, 0.5, 1.0)
    return stereo(unit(rust[0]) * 0.6 + unit(breeze), unit(rust[1]) * 0.6 + unit(breeze))


def bed_sky(d):       # the overview: thin high-altitude wind
    return stereo(*[unit(filt(colored(d, -1), 'bandpass', [300, 2500]) * drift(d, 0.3, 0.4, 1.0)) for _ in range(2)])


def put(bus, x, start, gain, send=0.2):
    add(bus, x[:, 0], start, gain, pan=-1.0, send=send)
    add(bus, x[:, 1], start, gain, pan=1.0, send=send)


# where the camera whips from seat to seat (fastest frame, measured on the render) and which way the world moves
WHIPS = [(34.33, -0.8), (45.25, -0.8), (55.96, -0.6), (67.08, -0.8), (78.00, -0.2), (88.96, -0.7)]
BEDS = [bed_fire, bed_surf, bed_meadow, bed_blizzard, bed_desert, bed_storm, bed_campus]
LEVEL = [1.0, 0.9, 0.8, 1.0, 0.9, 1.15, 0.7]            # relative bed levels (the storm leans in, the campus is gentle)
edges = [22.4] + [w for w, _ in WHIPS] + [R.OVERVIEW[0] + 0.4]
XF_ = 0.9                                                 # beds cross-fade under each fly-by
for k, fn in enumerate(BEDS):
    a, b = edges[k] - XF_ / 2, edges[k + 1] + XF_ / 2
    put('amb', fade_io(fn(b - a), 1.6 if k == 0 else XF_, XF_), a, LEVEL[k], send=0.15)
put('amb', fade_io(bed_sky(R.OVERVIEW[1] - R.OVERVIEW[0] - 0.4), 1.0, 1.8), R.OVERVIEW[0] - 0.2, 0.6, send=0.2)

# fly-bys: each crests on the whip's fastest frame
for pk, dir_ in WHIPS:
    d = 1.7
    put('trans', flyby(d, -dir_, dir_), pk - 0.65 * d, 1.0, send=0.2)
put('trans', flyby(1.6, 0.6, -0.4), 22.04 - 0.65 * 1.6, 0.6, send=0.2)   # the pull-up out of the low run

# Storm's End: thunder on the lightning (flashes at +1.4/+1.55 and +6.2 s into the window), distant rolls between
s5 = R.house_window(5)[0]
th = thunder(True, 6.5)
put('trans', stereo(th, np.roll(th, 400)), s5 + 1.40, 1.0, send=0.5)
th = thunder(True, 6.0)
put('trans', stereo(np.roll(th, 300), th), s5 + 6.20, 0.9, send=0.5)
for at, g_ in ((s5 - 0.2, 0.55), (s5 + 4.0, 0.45), (s5 + 9.2, 0.4)):
    th = thunder(False, 5.0)
    put('trans', stereo(th, th), at, g_, send=0.6)

# the seat of the realm: the great bell tolls as it rises and as the council's medallion lands
cw = R.CAMPUS_WIN[0]
for at, g_ in ((cw + 1.0, 0.5), (cw + 3.1, 0.55), (cw + 5.3, 0.7)):
    b_ = bell()
    put('trans', stereo(b_, np.roll(b_, 240)), at, g_, send=0.7)


# the voice: "Who will reign?" as the words resolve on screen (deep male, pitched down, in a stone hall)
import soundfile as _sf
_vo, _sr = _sf.read(os.path.join(HERE, 'vo_who_raw.wav'), dtype='float64')
_vo = signal.resample_poly(_vo, 48000, _sr)
_vo = signal.resample(_vo, int(len(_vo) / 2 ** (-3 / 12)))          # -3 semitones (slower and lower)
_vo = filt(_vo, 'highpass', 55) + filt(_vo, 'lowpass', 220) * 0.6     # chest warmth
_vo = np.tanh(_vo / np.abs(_vo).max() * 1.6) / np.tanh(1.6)
VO_AT = R.WHO_AT + 0.15
OFS = 0.0                                      # the voice is in the opener: film time
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
np.save(os.path.join(os.path.dirname(HERE), 'build', 'fx_stem.npy'), fx[:int((R.END + R.LEAD) * SR)].astype(np.float32))
np.save(os.path.join(os.path.dirname(HERE), 'build', 'vo_span.npy'), np.array([VO_AT, VO_AT + len(_vo) / SR]))
def stem(bus, wet):
    return BUS[bus] + np.stack([signal.fftconvolve(BUS['verb_' + bus][:, c], ir[:, c])[:N] for c in range(2)], 1) * wet
np.save(os.path.join(os.path.dirname(HERE), 'build', 'amb_stem.npy'), stem('amb', 0.5)[:int((R.END + R.LEAD) * SR)].astype(np.float32))
np.save(os.path.join(os.path.dirname(HERE), 'build', 'trans_stem.npy'), stem('trans', 0.6)[:int((R.END + R.LEAD) * SR)].astype(np.float32))
vo_stem = BUS['vo'] + np.stack([signal.fftconvolve(BUS['verb_vo'][:, c], ir[:, c])[:N] for c in range(2)], 1) * 0.6
np.save(os.path.join(os.path.dirname(HERE), 'build', 'vo_stem.npy'), vo_stem[:int((R.END + R.LEAD) * SR)].astype(np.float32))
# the moment of silence before the title
g = np.ones(N)
a, b = int((R.TITLE[0] + 0.7 + R.LEAD) * SR), int((R.TITLE[0] + 1.2 + R.LEAD) * SR)
g[a:b] = np.linspace(1, 0.0, b - a) ** 2
g[b - int(0.05 * SR):b] = 0
mix[:b] *= g[:b, None]
mix = np.stack([filt(mix[:, c], 'highpass', 28) for c in range(2)], 1)
fade = np.ones(N)
k0 = int((R.END + R.LEAD - 1.6) * SR)
fade[k0:] = np.clip(np.linspace(1, 0, N - k0) * 1.6, 0, 1) ** 2
mix *= fade[:, None]
mix = mix[:int((R.END + R.LEAD) * SR)]
mix = mix / np.abs(mix).max() * 1.2
mix = np.tanh(mix) / np.tanh(1.2) * 0.9
os.makedirs(os.path.join(os.path.dirname(HERE), 'build'), exist_ok=True)
wavfile.write(os.path.join(os.path.dirname(HERE), 'build', 'score.wav'), SR, (mix * 32767).astype(np.int16))
print('score written', mix.shape[0] / SR, 's')
