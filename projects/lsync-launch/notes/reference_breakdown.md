# Reference breakdown

**Method.** Each reference was downloaded or taken from the user's uploads and studied as frame strips at 2, 6 and 10 fps. Cuts were measured with ffmpeg scene detection (threshold 0.18–0.25). Audio was analysed with a spectral-flux onset detector plus an autocorrelation tempo estimate; numbers are in seconds and frames at the source rate (all 30 fps). The user's upload `Download_9` is the same film as REF_C at a lower resolution. `Download_8` (@husnixd) is a fourth reference.

**Limits.** Onset detection says *when* a sound hits, not *what* it is. Sound types below (hit / whoosh / tick) are inferred from where they land in the motion, not identified by ear. REF_B's audio sits at −44 dBFS RMS (near-silent), so its sound placement can't be described reliably.

---

## REF_A — @ddaop_ · Strava brand system (16:9, 15.2 s, 30 fps) · **primary basis**

**Cut rhythm (frames per shot)**

| Frames | Shot |
|---|---|
| 0–14 (15) | White field. "Put the athlete first" |
| 15–28 (14) | **Black** field. "Be honest and unfiltered" |
| 29–42 (14) | **Orange** field. "Give every athlete a team" |
| 43–54 (12) | White field. "Keep the record, show the score" |
| 55–114 (60) | Photo stack: a new rectangle lands every ~5 frames, offset on the grid |
| 115–144 (30) | Wordmark wipes on, left to right, on white; construction guides draw at 130 |
| 145–169 (25) | Crop push on "RAVA"; three logo-colour chips (black / orange / outline) stack in at 150, 153 and 156 |
| 170–229 (60) | Charcoal field crossed by **orange bars**; logo tile at the crossing; "You" and "are my" type on |
| 230–254 (25) | White. Giant "HIGH" (~60 % of frame height), cropped, sliding left |
| 255–284 (30) | Field split: black rises from the bottom (255), orange slides in from the right (258). Colour-spec labels in each field |
| 285–344 (60) | White. Typography spec ("Maison Neue"); four orange panels slide in from the right **offset ~2–3 frames each**, carrying a giant "a" |
| 345–379 (35) | White. Logo mark alone, centred, still |
| 380–455 (75) | White. Signature "Daop." in orange, small, held still for 2.5 s |

**Easing feel**
- Arrivals are expo/quart-out: about 80 % of the travel happens in the first 3–4 frames, then a long settle, then a dead hold.
- Big type slides run at near-constant speed (linear drift) while it is the only motion.
- Field inversions are hard cuts with no transition frames.
- Fast slides carry a small amount of motion blur; holds are perfectly still.

**Type treatment**
- Two scales and nothing between: tiny labels (~1.3 % of frame width: principles, "Brand Principles", index numbers 01–04 bottom centre, colour specs) and giant display ("HIGH", "RAVA", the "a"), deliberately cropped by the frame edge.
- Labels enter **per word**: each word rises a few pixels from its baseline and fades in within ~4 frames, the next word 3–4 frames later.
- "are my" types on **per character** (~3 frames per character), with wide tracking.
- Weights: grotesk regular for labels, bold for display. Tracking is tight on display and wide on labels.

**Solid colour**
- Exactly three fills (white, near-black, Strava orange) plus a mid grey for guides. No gradients, no glows, no shadows.
- Colour is used as **field inversions on the beat** (white → black → orange → white, one per 15 frames), **crossing bars** that divide the frame, a **three-field split** that literally shows the palette, and **stacked solid panels** offset in time.

**Transition mechanics**
- A hard cut on a field change.
- Dashed grid lines (1 px, with dot intersections) reposition between shots: the grid is the continuity device.
- Panels slide in from one edge in sequence, 2–3 frames apart.
- A wordmark is wiped on by a straight-edged mask.
- A crop-zoom into the logo.

**Sound relative to motion** (tempo measured ≈ 123 BPM)
- The three field inversions (0.47, 0.97, 1.43 s) each sit **within 10–20 ms of an onset**: a hit on every cut.
- During the photo stack, onsets fall every ~0.24 s (eighth notes at 123 BPM): **one sound per photo landing**.
- **Silence gap** from 3.34 to 4.55 s, straddling the wordmark reveal at 3.83 s: the reveal lands in space, not on a hit.
- Eighths resume during the orange-cross section (5.02–6.71 s).
- A second gap (6.71–8.38 s) around the "HIGH" cut, then eighths again through the type and panel section.
- The last onset is at 11.26 s; the logo and signature hold over the decay.

---

## REF_B — @graftmotion · Pinterest (16:9, 16.2 s, 30 fps)

**Cut rhythm.** No hard cuts were detected. The film is one continuous canvas whose content swaps through transforms.

| Time | What happens |
|---|---|
| 0–1.7 s | One word or phrase at a time ("lacking" → "Ideas for" → "your next" → "edit"), each 6–9 frames. The new word enters from the right while the old one exits left. "edit" holds 15 frames. |
| 1.7–3.0 s | "meet" → a dot grows into the logo |
| 3.0 s | A red field |
| 3.5–9.5 s | A UI board: grey placeholder cards, a search field typing, then real content filling the cards |
| 10.3–12.4 s | A cursor clicks the save button; the card collapses into a "Pined" pill |
| 12.5–16 s | Closing words, one at a time |

**Easing feel.** Expo-out arrivals, quick exits, words travelling horizontally on one baseline.

**Type treatment**
- Small-to-medium centred words, semibold.
- One accent colour on the key word.
- Strict one-idea-per-beat cadence (6–9 frames per word); the payoff word holds about twice as long.

**Solid colour.** A white field with one full red field at 3.0 s. *Conflicts with this brief:* a red **glow/blur halo** sits behind the accent words and the logo. **Not adopted.**

**Transition mechanics.**
- Word swaps on a single baseline (horizontal push).
- A dot becomes the logo.
- UI state changes stand in for cuts: placeholders become content, a button becomes a pill.

**Sound.** Near-silent (−44 dBFS RMS). Faint onsets cluster at 0.1–1.0 s during the word cadence, around 6.1–6.6 s (content fill) and around 11.7–11.8 s (the save click). Too quiet to assign sounds with confidence.

---

## REF_C — @mythiqmotion · Claude (16:9, 14.2 s, 30 fps)

**Cut rhythm.** One hard cut, at 3.20 s (frame 96). Everything else is continuous camera and UI motion.

| Time | What happens |
|---|---|
| 0–1.5 s | The logo spark rotates in; the wordmark builds |
| 1.5–3.2 s | A row of UI chips; the cursor clicks "Code" at ~2.5 s and the chip changes state on that frame |
| 3.2–4.6 s | Hard cut to a prompt box; text types at ~10–12 characters per second (current word in the accent colour) while the box re-frames |
| 4.6–6.5 s | Code scroll |
| 6.5–9 s | The generated site card, tilted in 3D |
| 9–11 s | Second prompt ("Make the gradient blue…"); the card recolours |
| 12–14 s | Logo plus "Create anything.", typed per character |

**Easing feel.** Long, smooth camera eases (power3/expo in-out); type on per character.

**Type treatment**
- A system grotesk.
- The prompt text is body-size; the end line is small and centred.
- Per-character reveal on the end line.

**Solid colour.** *Conflicts with this brief:* the whole film is built on orange radial **gradients and glows**, with a gradient recolour as its story beat. **Not adopted** beyond its interaction timing.

**Transition mechanics.** Re-framing within one surface; one hard cut, used where the context changes.

**Sound.**
- Sparse: onsets at 0.16 s (logo), 2.53 s (**the chip click: the sound lands on the state-change frame**), 3.18 s (**the hard cut**), 5.55, 6.20, 10.52 and 11.80 s (the end line).
- About 103 BPM.
- Takeaway: interaction sounds land on the exact frame the UI changes state, and the single cut carries a hit.

---

## Upload — @husnixd · "HusniXD" (1:1, 14.3 s, 30 fps)

**Cut rhythm.** Hard cuts at 2.24, 7.64, 8.64 and 11.54 s, all **within 10–20 ms of an onset**. The music has a dead-steady quarter-note pulse (onsets every ~0.49 s, ≈ 123 BPM). Shots last 2–5 s, with internal motion on the quarter note.

**Easing feel.** Snappy expo-out pops for UI elements, and a blur ramp on exits.

**Type treatment.** Bold white headline on dark ("Still looking for an editor"), built from shapes that resolve into letters; UI text at real size.

**Solid colour.** Mostly flat fields (black, a pale grey UI field, a purple band), but with a vignette and glows. **Glows not adopted.**

**Transition mechanics.**
- A search field types a name.
- A profile assembles with chips.
- A cursor click opens content.
- A full-frame solid purple band carries the CTA. *(The CTA language itself is ad-like and not adopted.)*

**Sound.** A quarter-note pulse throughout; every hard cut sits on an onset.

---

## What all four agree on (the parts this brief keeps)

1. **The beat grid owns the edit.** Cuts land on onsets within one frame (A, C, upload).
2. **One idea per beat.** A short phrase or one word per frame, with the payoff held about twice as long (A, B).
3. **Interaction proof uses the real UI, with sound on the state-change frame** (B, C, upload).
4. **A deliberate silence before the reveal** (A: 3.34–4.55 s around the wordmark).
5. **Two type scales only**: tiny labels with wide tracking, and huge display type with tight tracking, cropped by the frame (A).
6. **Solid fields as transitions**: inversions on the beat, crossing bars, offset stacked panels (A).

The references disagree on surface (A is flat; B, C and the upload use glow and gradients). This brief sides with A.
