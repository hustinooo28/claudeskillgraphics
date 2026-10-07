"""LSC brand-glow reel soundtrack: music bed (bars locked to the seal impact) + SFX cues + ducked voice-over.

usage: python mix.py <skill scripts dir (synth.py)> <vo dir> <out.wav>
"""
import sys
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

sys.path.insert(0, sys.argv[1])
import synth as S  # noqa: E402

VO_DIR, OUT = sys.argv[2], sys.argv[3]
SR, TOTAL = S.SR, 40.0

# Voice-over start times (seconds) — must match index.html.
VO = {'every': 0.5, 'meet': 4.0, 'enter': 7.3, 'appear': 9.9, 'receipt': 13.8, 'funds': 18.6, 'officer': 24.5, 'peso': 28.5, 'end': 33.0}

# Music: 120 BPM; SHIFT puts a downbeat exactly on the seal impact at 3.85 s (bars at 2k - SHIFT).
SHIFT = 0.15
sections = [(0, 1.85, 0), (1.85, 3.85, 1), (3.85, 33.85, 2), (33.85, 37.85, 1), (37.85, 60, 0)]
music = S.music(TOTAL + SHIFT, bpm=120, sections=[(a + SHIFT, b + SHIFT, k) for a, b, k in sections])[int(SHIFT * SR):]
music = music[: int(TOTAL * SR)]

sfx = np.zeros(int(TOTAL * SR))
P = lambda x, at, g=1.0: S.place(sfx, x * g, at)  # noqa: E731

# --- A: kinetic open, streak, seal
for at, f in [(0.45, 560), (1.45, 640), (2.28, 720)]:
    P(S.swoosh(0.4), at, 0.45)
    P(S.pop(f, 0.1, 0.3), at + 0.22)
P(S.riser(1.6), 2.15, 0.9)
P(S.whoosh(0.35), 3.22, 0.5)
P(S.glitch(0.18, 0.18), 3.3)
P(S.pop(1500, 0.08, 0.3), 3.6)
P(S.impact(), 3.83)
P(S.shimmer(), 3.95, 0.8)
P(S.swoosh(0.55), 4.3, 0.55)
P(S.whoosh(0.45), 6.33, 0.6)
# --- B: phone
P(S.whoosh(0.65, up=False), 6.75, 0.8)
P(S.pop(260, 0.22, 0.6), 7.25)
P(S.impact(1.0, 0.35), 7.25)
P(S.swoosh(0.4), 7.45, 0.45)
for i in range(14):
    P(S.tick(), 7.9 + i / 17)
for i in range(10):
    P(S.tick(), 8.8 + i / 17)
P(S.click(), 9.5)
P(S.whoosh(0.55), 9.52, 0.75)
# --- C: panel world
P(S.shimmer(1.2, 0.22), 10.0)
for i in range(4):
    P(S.pop(420 + i * 90, 0.1, 0.22), 10.05 + i * 0.08)
P(S.pop(880, 0.1, 0.35), 12.38)
P(S.ding((1318.5, 1975.5), 0.9, 0.25), 12.42)
P(S.whoosh(0.85), 13.52, 0.75)
P(S.pop(520, 0.12, 0.35), 15.9)
P(S.shimmer(1.0, 0.2), 16.2)
for at in (17.4, 17.65):
    P(S.click(), at)
    P(S.ding((1568, 2093), 0.7, 0.18), at + 0.28)
P(S.whoosh(0.85), 18.47, 0.75)
for i in range(3):
    P(S.pop(600 + i * 110, 0.1, 0.25), 19.2 + i * 0.12)
P(S.pop(1100, 0.08, 0.28), 20.28)
P(S.swoosh(0.35), 21.68, 0.35)
P(S.swoosh(0.35), 22.74, 0.35)
P(S.whoosh(0.4), 23.9, 0.9)
# --- D: officers
P(S.pop(300, 0.2, 0.5), 24.3)
P(S.whoosh(1.0), 24.9, 0.22)
P(S.ding((1318.5, 1975.5), 1.0, 0.32), 25.9)
P(S.glitch(0.2, 0.18), 26.45)
P(S.pop(560, 0.12, 0.35), 26.5)
P(S.swoosh(0.4), 27.33, 0.4)
P(S.ding((1760, 2637), 1.0, 0.28), 28.12)
P(S.shimmer(1.0, 0.2), 28.15)
P(S.whoosh(0.45), 28.33, 0.7)
# --- E: peso line, notification, seal
P(S.swoosh(0.45), 28.55, 0.4)
P(S.swoosh(0.45), 29.4, 0.4)
P(S.whoosh(0.35), 31.12, 0.5)
P(S.glitch(0.16, 0.16), 31.2)
P(S.pop(700, 0.12, 0.35), 31.55)
P(S.ding((1975.5, 2637), 0.9, 0.3), 31.58)
P(S.whoosh(0.35, up=False), 32.43, 0.45)
P(S.pop(1500, 0.08, 0.3), 32.7)
P(S.impact(1.6, 0.75), 32.9)
P(S.shimmer(), 33.0, 0.8)
P(S.swoosh(0.5), 33.25, 0.5)
P(S.shimmer(1.4, 0.25), 34.75)
# --- F: wipe into credits
P(S.pop(700, 0.12, 0.25), 36.85)
P(S.whoosh(0.75), 37.2, 0.7)
P(S.impact(1.8, 0.35), 37.95)

# Voice-over (24 kHz -> 48 kHz)
vo = np.zeros(int(TOTAL * SR))
for k, at in VO.items():
    a, sr = sf.read(f'{VO_DIR}/{k}.wav', dtype='float64')
    a = resample_poly(a, SR, sr)
    S.place(vo, a / (np.max(np.abs(a)) or 1) * 0.85, at)

# Duck the music ~12 dB under the voice, held through word gaps (see references/audio.md).
win = int(0.45 * SR)
envv = np.convolve(np.abs(vo), np.ones(win) / win, mode='same')
duck = 1 - 0.75 * np.clip(envv / 0.025, 0, 1)
duck = np.convolve(duck, np.ones(win) / win, mode='same')

mix = music * 0.45 * duck + sfx * 0.5 + vo
if np.max(np.abs(mix)) > 0.98:
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
mix = mix / max(np.max(np.abs(mix)), 1e-9) * 0.95
sf.write(OUT, np.stack([mix, mix], axis=1), SR, subtype='PCM_16')
print('wrote', OUT, f'{len(mix) / SR:.2f}s')
