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
TOTAL_F = 2400
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
    "rev_cymbal.wav": (reverse_cymbal(1.2), 1.2),
    "hit.wav": (hit(), 0.0),
    "click.wav": (S.norm(S.click(0.9), 0.9), 0.0),
    "key.wav": (tick(3200, 0.035), 0.0),
    "pop.wav": (S.norm(S.pop(720, 0.14, 0.9), 0.9), 0.0),
    "shimmer.wav": (S.norm(S.hp(S.shimmer(1.4, 0.9), 900, 2), 0.9), 0.0),
    "riser_long.wav": (riser(3.0), 0.0),
    "impact_sub.wav": (impact_sub(1.5), 0.0),
    "impact_final.wav": (S.norm(reverb(impact_sub(1.4)), 0.95), 0.0),
    "tick_ui.wav": (tick(2400), 0.0),
    "tick_soft.wav": (tick(1800, 0.06), 0.0),
}
for name, (x, _) in SFX.items():
    sf.write(ROOT / "assets/audio/sfx" / name, trim(x).astype(np.float32), SR)

# ---------------- cue list: (frame the sound lands on, file, gain dB, what it marks) ----------------
# For whooshes / reverse cymbal the frame is where the PEAK lands (the file starts earlier).
def typing(start, cps, text, gain=-27, what="key"):
    """One soft key tick per typed (non-space) character, on the frame it appears."""
    return [(start + round(i * FPS / cps), "key.wav", gain, f"{what}: '{c}'") for i, c in enumerate(text) if c != " "]

CUES = [
    (20, "shimmer.wav", -17, "rings draw around the seal"),
    (44, "hit.wav", -11, "seal arrives white-hot and lands"),
    (250, "whoosh_wipe.wav", -10, "hot capsules slide in, push the logo away"),
    (290, "shimmer.wav", -20, "capsules cool into the chips"),
    (390, "click.wav", -9, "click: Records (turns yellow)"),
    (540, "hit.wav", -7, "hard cut: Find Your Records close-up"),
] + typing(560, 13, "Juan Dela Cruz", what="name") + typing(650, 14, "2021-00001", what="ID") + [
    (750, "click.wav", -9, "click: Search Records"),
    (751, "pop.wav", -16, "button flashes yellow"),
    (800, "whoosh_wipe.wav", -11, "box flies up; data stream rises"),
    (900, "riser_long.wav", -15, "build into the card (ends f1078)"),
    (1080, "impact_sub.wav", -5, "the Transparency Board card lands"),
    (1082, "whoosh_rise.wav", -14, "card swings in, tilted"),
    (1160, "whoosh_short.wav", -20, "card turns to face us"),
    (1400, "whoosh_wipe.wav", -13, "camera drops to the prompt"),
] + typing(1452, 16, "How much did Intramurals collect?", what="question") + [
    (1590, "click.wav", -9, "send"),
    (1640, "whoosh_wipe.wav", -13, "camera rises back to the card"),
    (1656, "shimmer.wav", -11, "the Intramurals row lights up yellow"),
    (1690, "pop.wav", -15, "callout: Intramurals, P1,050 collected"),
    (1880, "whoosh_short.wav", -19, "callout drifts away"),
    (1960, "whoosh_wipe.wav", -12, "card floats up into the dark"),
    (2040, "rev_cymbal.wav", -12, "reverse swell into the finale"),
    (2042, "hit.wav", -12, "seal arcs in"),
] + typing(2100, 15, "One step better than yesterday.", gain=-25, what="finale") + [
    (2190, "impact_final.wav", -3, "'better' ignites: final impact with reverb tail"),
    (2234, "pop.wav", -17, "NOW LIVE / lsync.vercel.app"),
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
if peak_stack > 2:
    spans = [(cue_span(f, nm), f, nm) for f, nm, *_ in CUES]
    for (a0, a1), f, nm in spans:
        live_here = [(f2, n2) for (b0, b1), f2, n2 in spans if b0 <= a0 < b1]
        if len(live_here) > 2: print("stack at", f, live_here)
assert peak_stack <= 2, f"{peak_stack} SFX stacked"

# ---------------- music bed: ambient pulse, 120 BPM grid, shaped to the REF_C arc ----------------
n = int((TOTAL + 0.5) * SR)
bed = np.zeros(n)
prog = [[53, 60, 63, 67, 72], [49, 56, 60, 63, 68], [56, 60, 63, 67, 72], [51, 58, 62, 65, 70]]  # Fm9  Dbmaj7  Abmaj7  Eb
bass = [41, 37, 44, 39]
def section(t):
    f = t * FPS
    if f < 240: return "open"
    if f < 540: return "chips"
    if f < 1080: return "search"
    if f < 1640: return "board"
    if f < 2040: return "answer"
    return "finale"
for b in range(20):  # 20 bars of 2 s
    t0 = b * 4 * BEAT; ci = (b // 1) % 4; sec = section(t0 + 0.01)
    lvl = {"open": 0.035, "chips": 0.04, "search": 0.04, "board": 0.05, "answer": 0.055, "finale": 0.07}[sec]
    S.place(bed, S.pad_chord(prog[ci], 4 * BEAT + 0.6, 1100 if sec != "finale" else 1800) * lvl, t0)
    bt = S.t_(4 * BEAT)
    sub = np.sin(2 * np.pi * S.note_hz(bass[ci] - 12) * bt) * S.env(len(bt), a=0.05, d=0.1, s=0.9, r=0.3, sus_len=4 * BEAT - 0.45)
    S.place(bed, sub * (0.05 if sec == "open" else 0.11), t0)
    for e in range(8):
        te = t0 + e * BEAT / 2
        if sec in ("chips", "search") and e % 2 == 0:
            S.place(bed, S.kick(0.22), te)
        if sec in ("board", "answer") and e % 2 == 0:
            S.place(bed, S.kick(0.34), te)
        if sec in ("search", "board", "answer"):
            S.place(bed, S.hat(0.022 if e % 2 == 0 else 0.034), te)
        if sec in ("board", "answer"):
            S.place(bed, S.pluck(prog[ci][(e * 2) % 5] + 12, 0.22, 0.03), te)
bed = S.hp(bed, 30, 2)
fade_in = int(1.2 * SR); bed[:fade_in] *= np.linspace(0, 1, fade_in)
# REF_C's hard cut lands in a breath: the bed dips out for the last eighth before f540
bed[int(fs(526) * SR): int(fs(540) * SR)] *= np.linspace(1, 0.05, int(fs(540) * SR) - int(fs(526) * SR))
# the finale dissolves with the picture
fo0, fo1 = int(fs(2330) * SR), int(fs(2400) * SR)
bed[fo0:fo1] *= np.linspace(1, 0, fo1 - fo0); bed[fo1:] = 0

# ---------------- SFX bus ----------------
sfx = np.zeros(n)
for f, name, g, _ in CUES:
    x, pk = SFX[name]
    S.place(sfx, trim(x) * db(g), max(0.0, fs(f) - pk))

# light sidechain duck of the bed under the two impacts (-5 dB, 8 ms attack, 350 ms release)
duck = np.ones(n)
for f in (1080, 2190):
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

- **Bed** (`assets/audio/bed.wav`, generated): an ambient pulse following REF_C's arc (Fm9, Db maj7, Ab maj7, Eb; 120 BPM grid).
  - 0–4 s: a pad fades up from silence.
  - 4–18 s: a soft pulse arrives with the chips, and hats with the search; the bed dips out just before the hard cut at f540.
  - 18–34 s: the board, with a fuller pulse and an eighth-note shimmer arpeggio.
  - 34–40 s: a warm open pad swell under "One step better than yesterday.", dissolving with the picture.
- **Typing:** one soft key tick per typed character, on the frame it appears.
- **Processing**
  - Whooshes and the riser are high-passed at 150 Hz (4th / 2nd order).
  - The bed ducks −5 dB under the card impact (f1080) and the final impact (f2190) (8 ms attack, 120 ms hold, 350 ms release).
  - Reverb (a generated 2.2 s impulse, 32 % wet) is on `impact_final.wav` only; it is the hit under "better".
- **Loudness:** two-pass ffmpeg `loudnorm` to −14 LUFS integrated with true peak ≤ −1 dBTP, then verified with `ebur128` on the delivered MP4s.
- No copyrighted audio. Every sound is synthesised from noise and oscillators with numpy/scipy.
""")
print("stack max", peak_stack, "| cues", len(CUES))
