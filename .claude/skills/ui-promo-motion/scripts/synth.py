"""Procedural music bed + UI sound effects for promo videos (numpy/scipy only)."""
import numpy as np
from scipy import signal

SR = 48000
rng = np.random.default_rng(7)


def t_(dur):
    return np.arange(int(dur * SR)) / SR


def env(n, a=0.005, d=0.1, s=0.0, r=0.05, sus_len=0.0):
    a_n, d_n, s_n, r_n = int(a * SR), int(d * SR), int(sus_len * SR), int(r * SR)
    e = np.concatenate([
        np.linspace(0, 1, max(a_n, 1)),
        np.linspace(1, s, max(d_n, 1)),
        np.full(s_n, s),
        np.linspace(s, 0, max(r_n, 1)),
    ])
    if len(e) < n:
        e = np.pad(e, (0, n - len(e)))
    return e[:n]


def lp(x, cutoff, order=2):
    b, a = signal.butter(order, min(cutoff, SR / 2 - 100) / (SR / 2), 'low')
    return signal.lfilter(b, a, x)


def hp(x, cutoff, order=2):
    b, a = signal.butter(order, cutoff / (SR / 2), 'high')
    return signal.lfilter(b, a, x)


def bp_sweep(noise, f0, f1, q=2.0):
    """Band-pass sweep by processing in short blocks."""
    out = np.zeros_like(noise)
    blk = 512
    freqs = np.geomspace(f0, f1, len(noise) // blk + 1)
    zi = None
    for i, f in enumerate(freqs):
        seg = noise[i * blk:(i + 1) * blk]
        if not len(seg):
            break
        lo, hi = f / (1 + 1 / q), f * (1 + 1 / q)
        b, a = signal.butter(2, [max(lo, 30) / (SR / 2), min(hi, SR / 2 - 200) / (SR / 2)], 'band')
        if zi is None:
            zi = signal.lfilter_zi(b, a) * 0
        y, zi = signal.lfilter(b, a, seg, zi=zi)
        out[i * blk:i * blk + len(seg)] = y
    return out


def norm(x, peak=0.9):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


# ---------------- sound effects ----------------

def whoosh(dur=0.6, up=True, peak=0.6):
    n = int(dur * SR)
    noise = rng.standard_normal(n)
    f0, f1 = (300, 6000) if up else (6000, 300)
    x = bp_sweep(noise, f0, f1, q=1.5)
    shape = np.sin(np.linspace(0, np.pi, n)) ** 1.5
    return norm(x * shape, peak)


def swoosh(dur=0.45, peak=0.55):
    """Shorter, airier pass-by with a slight pitch dip."""
    n = int(dur * SR)
    x = bp_sweep(rng.standard_normal(n), 1800, 500, q=1.2)
    x += 0.5 * bp_sweep(rng.standard_normal(n), 5000, 2000, q=2)
    shape = np.concatenate([np.linspace(0, 1, int(n * 0.35)) ** 2, np.linspace(1, 0, n - int(n * 0.35)) ** 1.2])
    return norm(x * shape, peak)


def pop(freq=620, dur=0.12, peak=0.5):
    t = t_(dur)
    f = freq * (1 + 0.6 * np.exp(-t * 60))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 38)
    return norm(x, peak)


def click(peak=0.35):
    t = t_(0.03)
    x = rng.standard_normal(len(t)) * np.exp(-t * 400)
    x = hp(x, 2000) + 0.6 * np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 250)
    return norm(x, peak)


def tick(peak=0.18):
    t = t_(0.02)
    return norm(hp(rng.standard_normal(len(t)), 4000) * np.exp(-t * 500), peak)


def ding(freqs=(1318.5, 1975.5), dur=1.2, peak=0.4):
    t = t_(dur)
    x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * (3 + i * 2)) for i, f in enumerate(freqs))
    x += 0.3 * np.sin(2 * np.pi * freqs[0] * 2.01 * t) * np.exp(-t * 8)
    return norm(x * env(len(t), a=0.002, d=dur, s=0, r=0.01), peak)


def riser(dur=1.5, peak=0.45):
    n = int(dur * SR)
    t = t_(dur)
    x = bp_sweep(rng.standard_normal(n), 200, 8000, q=3) * (t / dur) ** 2
    tone = np.sin(2 * np.pi * np.cumsum(np.geomspace(110, 880, n)) / SR) * (t / dur) ** 3 * 0.3
    return norm(x + tone, peak)


def impact(dur=1.8, peak=0.85):
    t = t_(dur)
    f = 55 + 90 * np.exp(-t * 18)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
    crack = lp(rng.standard_normal(len(t)), 3000) * np.exp(-t * 25) * 0.5
    tail = lp(rng.standard_normal(len(t)), 900) * np.exp(-t * 2.5) * 0.15
    return norm(boom + crack + tail, peak)


def glitch(dur=0.35, peak=0.4):
    n = int(dur * SR)
    x = np.zeros(n)
    pos = 0
    while pos < n:
        seg = int(rng.uniform(0.01, 0.04) * SR)
        f = rng.choice([180, 360, 720, 1440, 95])
        tt = np.arange(min(seg, n - pos)) / SR
        x[pos:pos + len(tt)] = signal.square(2 * np.pi * f * tt) * rng.uniform(0.3, 1)
        pos += seg
    return norm(lp(x, 4000) * env(n, a=0.002, d=0.01, s=1, r=0.05, sus_len=dur), peak)


def shimmer(dur=1.6, peak=0.3):
    t = t_(dur)
    x = np.zeros(len(t))
    for i, f in enumerate([2093, 2637, 3136, 4186]):
        start = int(i * 0.06 * SR)
        tt = t[: len(t) - start]
        x[start:] += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 3.5)
    return norm(x, peak)


# ---------------- music bed ----------------

def note_hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def pad_chord(notes, dur, bright=1800):
    t = t_(dur)
    x = np.zeros(len(t))
    for n in notes:
        f = note_hz(n)
        for det in (-0.12, 0.0, 0.12):
            ph = rng.uniform(0, 2 * np.pi)
            x += signal.sawtooth(2 * np.pi * f * (1 + det / 100) * t + ph)
    x = lp(x, bright, 2)
    return x * env(len(t), a=0.35, d=0.2, s=0.85, r=0.5, sus_len=max(dur - 1.05, 0))


def kick(peak=1.0):
    t = t_(0.45)
    f = 48 + 110 * np.exp(-t * 35)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) * peak


def hat(peak=0.25, open_=False):
    t = t_(0.25 if open_ else 0.06)
    return hp(rng.standard_normal(len(t)), 7000) * np.exp(-t * (18 if open_ else 90)) * peak


def clap(peak=0.4):
    t = t_(0.25)
    x = np.zeros(len(t))
    for d in (0, 0.012, 0.024):
        s = int(d * SR)
        x[s:] += rng.standard_normal(len(t) - s) * np.exp(-t[: len(t) - s] * 40)
    return signal.lfilter(*signal.butter(2, [900 / (SR / 2), 3500 / (SR / 2)], 'band'), x) * peak


def pluck(n, dur=0.3, peak=0.25):
    t = t_(dur)
    f = note_hz(n)
    x = (signal.square(2 * np.pi * f * t, 0.3) * 0.5 + np.sin(2 * np.pi * f * t))
    return lp(x, 2500) * np.exp(-t * 9) * peak


def place(buf, x, at):
    i = int(at * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(x))
    buf[i:j] += x[: j - i]


def music(total, bpm=120, sections=None):
    """sections: list of (start, end, intensity) with intensity 0 (pad only), 1 (pad+hats+pluck), 2 (full beat)."""
    beat = 60 / bpm
    bar = beat * 4
    buf = np.zeros(int((total + 2) * SR))
    # C major-ish progression in A minor: Am - F - C - G  (MIDI)
    prog = [[57, 60, 64, 69], [53, 57, 60, 65], [48, 55, 60, 64], [55, 59, 62, 67]]
    bass = [45, 41, 48, 43]
    arp = [[69, 72, 76, 72], [65, 69, 72, 69], [67, 72, 76, 72], [67, 71, 74, 71]]
    sections = sections or [(0, total, 2)]

    def intensity(t):
        for s, e, k in sections:
            if s <= t < e:
                return k
        return 0

    nbars = int(np.ceil(total / bar)) + 1
    for b in range(nbars):
        t0 = b * bar
        if t0 > total:
            break
        ci = b % 4
        k = intensity(t0 + 0.01)
        place(buf, pad_chord(prog[ci], bar + 0.6) * 0.06, t0)
        # sub bass
        bt = t_(bar)
        bx = np.sin(2 * np.pi * note_hz(bass[ci] - 12) * bt) * env(len(bt), a=0.02, d=0.1, s=0.9, r=0.2, sus_len=bar - 0.35)
        place(buf, bx * (0.16 if k >= 1 else 0.08), t0)
        for q in range(8):
            tq = t0 + q * beat / 2
            if tq > total:
                break
            if k >= 1:
                place(buf, hat(0.05 if q % 2 == 0 else 0.08), tq)
                place(buf, pluck(arp[ci][q % 4], peak=0.07), tq)
            if k >= 2:
                if q % 2 == 0:
                    place(buf, kick(0.5), tq)
                if q in (2, 6):
                    place(buf, clap(0.12), tq)
    buf = buf[: int(total * SR)]
    fade = int(1.5 * SR)
    buf[-fade:] *= np.linspace(1, 0, fade)
    return buf
