# Audio: voice-over, music, sound effects

Promo videos in this style live on sound: a voice-over carries the story, a music bed sets the pace, and every move has a sound effect. Everything below runs offline.

## Order of work

1. **Write the VO first, one line per scene**, 1.5–6 s each. Generate it with `scripts/tts.py` and use the measured durations to place scenes: each scene starts ~0.4 s before its line, and visuals land on the key word.
2. **Build the visuals** against those times.
3. **Write a cue list** of sound effects at the exact times of the moves (pop on every card landing, whoosh on every zoom/wipe, tick per typed character, click on cursor clicks, ding on success states, impact + shimmer on the logo, riser into the brand reveal).
4. **Mix** with `scripts/synth.py` (see `projects/lsync-promo/audio/mix.py` in this repo for a complete example), then loudness-normalize and mux with the renderer's `--audio`.

## Voice — `scripts/tts.py`
Kokoro (82M, Apache-2.0) via `kokoro-onnx`, ~1 s of compute per line on CPU. `af_heart` is the most natural default. `--check` transcribes every line with Whisper and prints what it heard: fix the text (spell acronyms out, add commas for pauses) until every line comes back word for word.

## Music and effects — `scripts/synth.py`
Procedural, so there are no licensing questions.
- `music(total, bpm, sections)` makes a pad, sub-bass, arpeggio, hats, kick and clap bed in A minor (Am–F–C–G). `sections` sets intensity per time range: 0 = pad only, 1 = adds hats and pluck, 2 = full beat. Use 0–1 for the hook and the problem, 2 from the brand reveal, then 1 → 0 for the end card.
- **Lock bars to the cuts:** at 120 BPM a bar is 2 s. Generate a little extra and slice the start off so a downbeat falls on the brand-reveal impact.
- Effects: `whoosh`, `swoosh`, `pop(freq)`, `click`, `tick`, `ding(freqs)`, `riser(dur)`, `impact`, `glitch`, `shimmer`. Vary the `pop` pitch across a stagger (520 → 640 → 760 Hz) so repeated cards sound like a phrase rather than a repeat.

## Mix levels (measured on the LSC promo)
| Stem | Under voice | In gaps |
|---|---|---|
| Voice | −18 to −22 dBFS RMS | — |
| Music | ~12 dB below the voice (ducked) | ~1 dB below where the voice would be |
| SFX | short peaks, 0.2–0.6 gain | — |

Ducking: smooth the VO envelope over ~0.45 s, then cut music gain by up to 75 % so it stays down through word gaps. Then run `ffmpeg -i mix.wav -af loudnorm=I=-14:TP=-1.5:LRA=11 mix-norm.wav` (social platforms target −14 LUFS).

**You cannot listen**, so check numerically: measure the RMS of each stem in a few windows, and run Whisper on the *final mix*. Every line should transcribe correctly over the music.
