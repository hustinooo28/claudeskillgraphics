"""Build the soundtrack: music bed (bars locked to the cuts) + SFX cues + voice-over with ducking.

usage: python mix.py <synth.py dir> <vo dir> <out.wav>
"""
import sys
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

sys.path.insert(0, sys.argv[1])
import synth as S  # noqa: E402

VO_DIR, OUT = sys.argv[2], sys.argv[3]
SR, TOTAL = S.SR, 48.0

# Voice-over start times (seconds), matching index.html.
VO = {'hook': 0.6, 'doubt': 3.4, 'brand': 7.4, 'records': 14.0, 'receipt': 20.0,
      'funds': 24.2, 'officer': 30.6, 'notify': 37.0, 'end': 43.2}

# Music: 120 BPM, shifted so a bar starts on the brand impact at 6.7 s.
SHIFT = 1.3
sections = [(0, 2.7, 0), (2.7, 6.7, 1), (6.7, 42.4, 2), (42.4, 44.7, 1), (44.7, 60, 0)]
music = S.music(TOTAL + SHIFT, bpm=120, sections=[(a + SHIFT, b + SHIFT, k) for a, b, k in sections])[int(SHIFT * SR):]
music = music[: int(TOTAL * SR)]

sfx = np.zeros(int(TOTAL * SR))
P = lambda x, at, g=1.0: S.place(sfx, x * g, at)  # noqa: E731

# S1 hook
P(S.swoosh(0.5), 0.05, 0.5)
P(S.swoosh(0.4), 2.5, 0.5)
# S2 doubt cards
for at, f in [(3.25, 520), (3.75, 640), (4.55, 760)]:
    P(S.pop(f), at)
for at in (3.7, 4.2, 4.7):
    P(S.pop(1250, 0.08, 0.3), at)
P(S.riser(1.75), 4.95)
P(S.whoosh(0.6), 6.0, 0.8)
# S3 brand
P(S.impact(), 6.68)
P(S.shimmer(), 6.9, 0.8)
P(S.swoosh(0.5), 7.55, 0.5)
P(S.whoosh(0.55), 13.05, 0.7)
# S4 records: typing, click, slide, success
for i in range(14):
    P(S.tick(), 14.2 + i / 16)
for i in range(10):
    P(S.tick(), 15.3 + i / 15)
P(S.click(), 16.45)
P(S.swoosh(0.5), 16.75, 0.6)
P(S.pop(880, 0.1, 0.35), 18.2)
P(S.ding((1318.5, 1975.5), 0.9, 0.22), 18.25)
P(S.whoosh(0.8, up=False), 19.1, 0.7)
# S5 receipt + QR
P(S.pop(500), 19.75)
P(S.click(), 20.85)
P(S.ding((1568, 2093), 0.8, 0.2), 21.15)
P(S.pop(700), 20.9)
P(S.shimmer(1.0, 0.2), 21.4)
P(S.click(), 22.4)
P(S.ding((1568, 2093), 0.8, 0.2), 22.7)
P(S.whoosh(0.5), 23.3, 0.7)
# S6 funds
for i, at in enumerate((24.3, 24.42, 24.54)):
    P(S.pop(600 + i * 120, 0.1, 0.3), at)
P(S.pop(1100, 0.08, 0.25), 24.4)
for i in range(3):
    P(S.pop(420 + i * 80, 0.1, 0.22), 25.9 + i * 0.14)
P(S.swoosh(0.35), 26.65, 0.35)
P(S.swoosh(0.35), 27.55, 0.35)
P(S.whoosh(0.5), 29.7, 0.7)
# S7 officers
P(S.pop(300, 0.18, 0.5), 30.25)
P(S.whoosh(1.1, up=True), 30.75, 0.25)
P(S.ding((1318.5, 1975.5), 1.0, 0.35), 31.85)
P(S.glitch(0.22, 0.2), 32.45)
P(S.pop(560), 32.5)
P(S.swoosh(0.4), 34.05, 0.45)
P(S.ding((1760, 2637), 1.0, 0.3), 35.4)
P(S.shimmer(1.2, 0.22), 35.45)
P(S.whoosh(0.5), 36.1, 0.7)
# S8 notifications + feedback
for i in range(3):
    P(S.ding((1975.5, 2637), 0.6, 0.18), 36.85 + i * 0.55)
P(S.pop(520), 39.2)
P(S.swoosh(0.35), 39.85, 0.35)
for i in range(50):
    P(S.tick(0.12), 40.3 + i / 30)
P(S.click(), 41.7)
P(S.swoosh(0.4), 41.85, 0.4)
P(S.whoosh(0.45), 41.95, 0.6)
# S9 end
P(S.impact(1.6, 0.6), 42.48)
P(S.shimmer(), 42.7, 0.7)
P(S.swoosh(0.5), 43.15, 0.4)
P(S.shimmer(1.4, 0.25), 44.75)

# Voice-over track (24 kHz -> 48 kHz)
vo = np.zeros(int(TOTAL * SR))
for k, at in VO.items():
    a, sr = sf.read(f'{VO_DIR}/{k}.wav', dtype='float64')
    a = resample_poly(a, SR, sr)
    S.place(vo, a / (np.max(np.abs(a)) or 1) * 0.85, at)

# Duck music under the voice: smoothed VO envelope -> up to about -12 dB, held through word gaps.
win = int(0.45 * SR)
envv = np.convolve(np.abs(vo), np.ones(win) / win, mode='same')
duck = 1 - 0.75 * np.clip(envv / 0.025, 0, 1)
duck = np.convolve(duck, np.ones(win) / win, mode='same')

mix = music * 0.45 * duck + sfx * 0.5 + vo
# Gentle bus limiter
peak = np.max(np.abs(mix))
mix = np.tanh(mix * 1.1) / np.tanh(1.1) if peak > 0.98 else mix
mix = mix / max(np.max(np.abs(mix)), 1e-9) * 0.95
stereo = np.stack([mix, mix], axis=1)
sf.write(OUT, stereo, SR, subtype='PCM_16')
print('wrote', OUT, f'{len(mix) / SR:.2f}s')
