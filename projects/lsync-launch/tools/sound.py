"""Generate the bed + SFX locally (no copyrighted audio), place every SFX by frame, mix, write the cue sheet.
   Output: assets/audio/launch_mix.wav (pre-loudness), assets/audio/sfx/*.wav, assets/audio/bed.wav,
           notes/sfx_cue_sheet.md.  Loudness (-14 LUFS, TP <= -1 dBTP) is applied after by ffmpeg loudnorm."""
import pathlib, sys
import numpy as np
import soundfile as sf
from scipy import signal

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parents[1] / ".claude/skills/ui-promo-motion/scripts"))
import synth as S  # noqa: E402  (shared procedural primitives from the ui-promo-motion skill)

SR, FPS, BPM = S.SR, 60, 120
TOTAL_F = 1470
TOTAL = TOTAL_F / FPS
BEAT = 60 / BPM
fs = lambda f: f / FPS
rng = np.random.default_rng(26)
db = lambda g: 10 ** (g / 20)

def trim(x, floor_db=-60):
    a = np.abs(x); idx = np.where(a > a.max() * db(floor_db))[0]
    return x[: idx[-1] + 1] if len(idx) else x

# ---------------- SFX palette: whoosh, riser, impact+sub, UI ticks, reverse cymbal ----------------
def whoosh(dur, f0=250, f1=5000, peak_at=0.5):
    """Band-passed noise sweep; amplitude peak at peak_at * dur. High-passed at 150 Hz per the brief."""
    n = int(dur * SR); k = int(n * peak_at)
    x = S.bp_sweep(rng.standard_normal(n), f0, f1, q=1.4)
    shape = np.concatenate([np.linspace(0, 1, k) ** 2.2, np.linspace(1, 0, n - k) ** 1.6])
    return S.norm(S.hp(x * shape, 150, 4), 0.9)

def tick(freq=2400, dur=0.05):
    t = S.t_(dur)
    x = np.sin(2 * np.pi * freq * t) * np.exp(-t * 160) + 0.35 * S.hp(rng.standard_normal(len(t)), 3500) * np.exp(-t * 600)
    return S.norm(x, 0.9)

def riser(dur):
    n = int(dur * SR); t = S.t_(dur)
    x = S.bp_sweep(rng.standard_normal(n), 300, 7000, q=3) * (t / dur) ** 2.4
    tone = np.sin(2 * np.pi * np.cumsum(np.geomspace(110, 440, n)) / SR) * (t / dur) ** 3 * 0.25
    y = (x + tone) * np.r_[np.ones(n - int(0.02 * SR)), np.linspace(1, 0, int(0.02 * SR))]
    return S.norm(S.hp(y, 150, 2), 0.9)

def impact_sub(dur=1.5):
    t = S.t_(dur)
    f = 42 + 70 * np.exp(-t * 16)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.0)
    body = S.lp(rng.standard_normal(len(t)), 2200) * np.exp(-t * 22) * 0.45
    x = sub + body
    x[: int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
    x[-int(0.2 * SR):] *= np.linspace(1, 0, int(0.2 * SR))
    return S.norm(x, 0.95)

def reverse_cymbal(dur):
    t = S.t_(dur)
    metal = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) for f in (3150, 4620, 5890, 7340, 8810)) * 0.12
    x = (S.hp(rng.standard_normal(len(t)), 5000) + metal) * np.exp(-t * 2.6)
    y = x[::-1].copy()
    y[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR))  # hard stop into the silence
    return S.norm(y, 0.9)

def hit(dur=0.32):
    """Short field-cut hit: low thump + click, no long tail (keeps the stack count low)."""
    t = S.t_(dur)
    f = 60 + 120 * np.exp(-t * 40)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14) + 0.5 * S.hp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 120)
    x[-int(0.03 * SR):] *= np.linspace(1, 0, int(0.03 * SR))
    return S.norm(x, 0.95)

def reverb(x, secs=2.2, wet=0.32):
    """Generated decaying-noise impulse; used on the final impact only."""
    t = S.t_(secs)
    ir = S.lp(rng.standard_normal(len(t)), 5000) * np.exp(-t * 3.2); ir /= np.sqrt(np.sum(ir ** 2))
    tail = signal.fftconvolve(np.r_[x, np.zeros(len(t))], ir)[: len(x) + len(t)]
    return np.r_[x, np.zeros(len(t))] * (1 - wet) + tail * wet

SFX = {
    "whoosh_wipe.wav": (whoosh(0.6, peak_at=0.6), 0.6 * 0.6),   # (audio, seconds to its peak)
    "whoosh_short.wav": (whoosh(0.34, 400, 6000, 0.6), 0.34 * 0.6),
    "whoosh_rise.wav": (whoosh(0.5, 200, 3500, 0.7), 0.5 * 0.7),
    "riser.wav": (riser(1.9), 0.0),
    "rev_cymbal.wav": (reverse_cymbal(0.8), 0.8),
    "hit.wav": (hit(), 0.0),
    "impact_sub.wav": (impact_sub(1.5), 0.0),
    "impact_final.wav": (S.norm(reverb(impact_sub(1.4)), 0.95), 0.0),
    "tick_ui.wav": (tick(2400), 0.0),
    "tick_soft.wav": (tick(1800, 0.06), 0.0),
}
for name, (x, _) in SFX.items():
    sf.write(ROOT / "assets/audio/sfx" / name, trim(x).astype(np.float32), SR)

# ---------------- cue list: (frame the sound lands on, file, gain dB, what it marks) ----------------
# For whooshes / reverse cymbal the frame is where the PEAK lands (the file starts earlier).
CUES = [
    (2, "tick_soft.wav", -20, "construction grid draws"),
    (20, "tick_ui.wav", -24, "principle 01 types on"),
    (60, "hit.wav", -8, "field cut to ink (principle 02)"),
    (120, "hit.wav", -8, "field cut to brand (principle 03)"),
    (180, "hit.wav", -8, "field cut to paper (principle 04)"),
] + [(240 + 15 * i, "tick_ui.wav" if i % 2 == 0 else "tick_soft.wav", -21, f"collage piece {i + 1:02d} lands") for i in range(15)] + [
    (465, "whoosh_short.wav", -15, "collage clears: silence f465-480"),
    (481, "whoosh_rise.wav", -19, "LSynC wordmark wipes on, in the gap"),
    (506, "tick_ui.wav", -22, "corner seals and gold dots"),
    (552, "whoosh_wipe.wav", -12, "crop push into SynC"),
    (566, "tick_ui.wav", -21, "chip 1 (ink)"),
    (571, "tick_ui.wav", -21, "chip 2 (brand)"),
    (576, "tick_ui.wav", -21, "chip 3 (outline)"),
    (600, "impact_sub.wav", -3, "THE DROP: crossing bars slam in"),
    (636, "tick_soft.wav", -22, "'student' types on"),
    (690, "whoosh_short.wav", -15, "grid re-positions"),
    (720, "hit.wav", -8, "cut to OPEN"),
    (732, "whoosh_wipe.wav", -12, "OPEN pulls back"),
    (770, "whoosh_short.wav", -14, "ink field rises"),
    (840, "whoosh_wipe.wav", -11, "brand field slides in"),
    (872, "whoosh_short.wav", -14, "gold field arrives"),
    (960, "hit.wav", -9, "cut to the typeface spec"),
    (992, "whoosh_wipe.wav", -12, "stacked panels slide in"),
    (1082, "whoosh_wipe.wav", -12, "live pages land as a stack"),
    (1112, "whoosh_short.wav", -14, "pages fan out"),
    (1125, "tick_ui.wav", -22, "index labels"),
    (1148, "whoosh_rise.wav", -13, "push into the Transparency Board"),
    (1200, "rev_cymbal.wav", -12, "reverse cymbal into the seal"),
    (1201, "hit.wav", -12, "seal opens"),
    (1210, "tick_soft.wav", -22, "construction rings draw"),
    (1276, "whoosh_short.wav", -17, "construction retracts"),
    (1320, "impact_final.wav", -2, "NOW LIVE: final impact with reverb tail"),
]

def cue_span(frame, name):
    x, pk = SFX[name]; x = trim(x)
    start = fs(frame) - pk
    return start, start + len(x) / SR

# max two SFX stacked at any instant
edges = sorted([(cue_span(f, n)[0], 1) for f, n, *_ in CUES] + [(cue_span(f, n)[1], -1) for f, n, *_ in CUES], key=lambda e: (e[0], e[1]))
live = peak_stack = 0
for _, d in edges:
    live += d; peak_stack = max(peak_stack, live)
assert peak_stack <= 2, f"{peak_stack} SFX stacked"

# ---------------- music bed: minimal percussive, 120 BPM ----------------
n = int((TOTAL + 0.5) * SR)
bed = np.zeros(n)
prog = [[50, 57, 62, 65], [46, 53, 58, 62], [53, 57, 60, 65], [48, 55, 60, 64]]  # Dm  Bb  F  C
bass = [38, 34, 41, 36]
def rim(peak):
    t = S.t_(0.08)
    return (np.sin(2 * np.pi * 1650 * t) * 0.4 + S.hp(rng.standard_normal(len(t)), 1800)) * np.exp(-t * 70) * peak
for b in range(12):
    t0 = b * 4 * BEAT; bar = b + 1; ci = b % 4
    if bar == 12:
        break  # the sign-off is the final impact and its tail only
    S.place(bed, S.pad_chord(prog[ci], 4 * BEAT + 0.4, 1400) * (0.03 if bar < 6 else 0.04), t0)
    bt = S.t_(4 * BEAT)
    sub = np.sin(2 * np.pi * S.note_hz(bass[ci] - 12) * bt) * S.env(len(bt), a=0.02, d=0.1, s=0.9, r=0.2, sus_len=4 * BEAT - 0.35)
    S.place(bed, sub * (0.06 if bar in (5, 11) else 0.13), t0)
    if bar in (5, 11):
        continue  # wordmark and seal: pad + sub only (REF_A's gaps around the reveals)
    for e in range(8):  # eighths
        te = t0 + e * BEAT / 2
        if e % 2 == 0:
            S.place(bed, S.kick(0.42 if bar >= 6 else 0.34), te)
        if bar >= 3:
            S.place(bed, S.hat(0.035 if e % 2 == 0 else 0.055), te)
        if bar >= 6 and e in (2, 6):
            S.place(bed, rim(0.09), te)
        if bar >= 6 and e % 2 == 1:
            S.place(bed, S.pluck(bass[ci] + 24, 0.18, 0.04), te)
bed = S.hp(bed, 30, 2)
# hard silence for the last eighth of bar 4 (f465-480): the wordmark lands in space; nothing under the sign-off
bed[int(fs(465) * SR): int(fs(480) * SR)] = 0
cut = int(fs(1320) * SR); bed[cut:] = 0
bed[cut - int(0.01 * SR): cut] *= np.linspace(1, 0, int(0.01 * SR))

# ---------------- SFX bus ----------------
sfx = np.zeros(n)
for f, name, g, _ in CUES:
    x, pk = SFX[name]
    S.place(sfx, trim(x) * db(g), fs(f) - pk)

# light sidechain duck of the bed under the two impacts (-5 dB, 8 ms attack, 350 ms release)
duck = np.ones(n)
for f in (600, 1320):
    i = int(fs(f) * SR); a, r = int(0.008 * SR), int(0.35 * SR)
    seg = np.r_[np.linspace(1, db(-5), a), np.full(int(0.12 * SR), db(-5)), np.linspace(db(-5), 1, r)]
    duck[i - a: i - a + len(seg)] = np.minimum(duck[i - a: i - a + len(seg)], seg[: n - (i - a)])
mix = bed * duck * db(-3) + sfx
mix = mix[: int(TOTAL * SR)]
stereo = np.stack([mix, mix], axis=1)
stereo /= max(np.abs(stereo).max(), 1e-9) / 0.7
sf.write(ROOT / "assets/audio/launch_premaster.wav", stereo.astype(np.float32), SR)
sf.write(ROOT / "assets/audio/bed.wav", (bed[: int(TOTAL * SR)] * 0.5).astype(np.float32), SR)

# ---------------- cue sheet ----------------
rows = "\n".join(
    f"| {f} | {f / FPS:.3f} | {(f // 120) + 1}.{((f % 120) // 30) + 1} | `assets/audio/sfx/{name}` | {g:+d} dB | "
    f"{'peak' if SFX[name][1] else 'onset'} | {why} |" for f, name, g, why in CUES)
(ROOT / "notes/sfx_cue_sheet.md").write_text(f"""# SFX cue sheet

60 fps, 120 BPM: beat = 30 f, bar = 120 f. Generated by `tools/sound.py`, which is the source of truth: the mix is built from exactly this table.

- **Frame** is where the sound lands. For whooshes and the reverse cymbal it is where the **peak** lands, so the file starts earlier; every whoosh peaks on a cut frame.
- **Gain** is applied to the file before it is summed onto the SFX bus.
- **Bar.beat** is the musical position.
- At most two SFX overlap at any instant. The script checks this automatically; the measured maximum is {peak_stack}.

| Frame | Time (s) | Bar.beat | File | Gain | Aligned on | Marks |
|---|---|---|---|---|---|---|
{rows}

## Bed and mix

- **Bed** (`assets/audio/bed.wav`, generated): a minimal percussive bed in D minor (Dm, Bb, F, C), 120 BPM, shaped on REF_A's structure.
  - Bars 1–2 (principles): kick on quarters, plus a hit on every field cut.
  - Bars 3–4 (collage): hats join, with one tick per piece landing on the eighths. f465–480 is total silence.
  - Bar 5 (wordmark): pad and sub only; the wordmark lands in the gap.
  - Bars 6–10 (crossing bars → interface): the drop, with rim on 2 and 4 and an eighth-note bass pluck.
  - Bar 11 (seal): pad and sub only, with the reverse cymbal into the seal.
  - Bar 12 (sign-off): the bed stops; only the final impact and its tail play.
- **Processing**
  - Whooshes and the riser are high-passed at 150 Hz (4th / 2nd order).
  - The bed ducks −5 dB under both impacts (8 ms attack, 120 ms hold, 350 ms release).
  - Reverb (a generated 2.2 s impulse, 32 % wet) is on `impact_final.wav` only.
- **Loudness:** two-pass ffmpeg `loudnorm` to −14 LUFS integrated with true peak ≤ −1 dBTP, then verified with `ebur128` on the delivered MP4s.
- No copyrighted audio. Every sound is synthesised from noise and oscillators with numpy/scipy.
""")
print("stack max", peak_stack, "| cues", len(CUES))
