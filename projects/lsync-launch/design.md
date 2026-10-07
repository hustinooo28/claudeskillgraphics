# design.md — Digital Transparency Board · official launch film

## Palette (locked; exact hex from the live site's CSS, lsync.vercel.app)

| Variable | Hex | Site token | Role |
|---|---|---|---|
| `--ink` | `#080D22` | `--dssc-deep-navy` | darkest brand neutral; open and close fields, all ink type |
| `--paper` | `#F4F6FC` | `--dssc-off-white` | the neutral; tour field, type on dark |
| `--brand` | `#526FF2` | `--dssc-royal-blue` | full-frame field wipes, the reveal field, the purpose panel |
| `--accent` | `#D6B05C` | `--dssc-gold` | used sparingly: the cold-open hairline, index numbers 01–03, the reveal underline, the NOW LIVE dot |

That is three colours plus one neutral. Flat solid fills only. **No gradients, no glows, no blur halos, no shadows, no transparency used as tint.** Every colour in the composition files is written as one of the four `var(--…)` values.

## Typography (the site's own faces, shipped locally under `assets/fonts/`)

| Role | Face | Size (vertical / landscape) | Tracking | Use |
|---|---|---|---|---|
| Display | Space Grotesk 700 | 220 / 240 px | −0.045em | 1–3 words per frame |
| Display S | Space Grotesk 700 | 136 / 144 px | −0.04em | purpose panels, site name lockup |
| Label | Space Grotesk 500, uppercase | 30 / 26 px | +0.12em | org name, index, feature labels, URL, date, NOW LIVE |
| Feature | Space Grotesk 600 | 80 / 64 px | −0.03em | tour feature names (2 words), endcard URL |

- **No body copy.**
- Entries:
  - display uses a line mask reveal: a line rises out of a clipped baseline, 16 frames, expo.out;
  - labels step in per word with 3-frame offsets;
  - the site-name lockup staggers 1 frame per character.
- Every settled word stays on screen ≥ 36 frames.

## Grid

- 12 columns; outer margin 6 % of width (vertical 65 px, landscape 115 px); gutter 16 / 24 px.
- Everything snaps to column edges and to a baseline unit of 8 px.
- **Vertical safe zone:** no text above y = 230 px (12 %) or below y = 1536 px (bottom 20 %).
- Layout in both formats comes from the same sub-compositions, via CSS container units (`cqw`/`cqh`) and a landscape container query (`assets/shared.css`).
- A project may have only one root composition (`lint: multiple_root_compositions`). `tools/hosts.py [vertical|landscape]` therefore rewrites `index.html` and each beat's root size from one slot table. Vertical is the committed state.

## Motion tokens

| Token | Value |
|---|---|
| fps | 60 |
| tempo | 120 BPM → beat = 30 f (0.5 s), eighth = 15 f, bar = 120 f (2 s) |
| enter | `expo.out` |
| exit | `expo.in` |
| transition | `power4.inOut` |
| hairline draw | `none` (linear is allowed only here) |
| fast move | 8–12 f |
| standard move | 14–20 f |
| reading hold | ≥ 36 f |
| final hold | 90 f, perfectly still |
| overshoot | none (≤ 4 % allowed; not used) |
| motion blur | directional SVG blur on fast horizontal moves only, ramped 0 → peak → 0 inside the move; never on holds |

## BPM map (frames at 60 fps; every cut and major move starts on a beat or an eighth)

| Bar | Frames | Seconds | Beat | Field |
|---|---|---|---|---|
| 1 | 0–119 | 0–2 | Cold open | ink |
| 2 | 120–239 | 2–4 | Statement A | brand (wipe f120) |
| 3 | 240–359 | 4–6 | Statement B | paper (wipe f240) · riser starts f240 |
| 4 | 360–479 | 6–8 | Purpose | ink + two panels |
| 5 | 480–599 | 8–10 | Purpose hold | reverse cymbal into f600 · silence f585–599 |
| 6 | 600–719 | 10–12 | **Reveal** | brand, hard cut f600 · impact + sub f600 · music drops in |
| 7 | 720–839 | 12–14 | Tour 01 | paper |
| 8 | 840–959 | 14–16 | Tour 02 | paper |
| 9 | 960–1079 | 16–18 | Tour 02 · scroll interaction | paper |
| 10 | 1080–1199 | 18–20 | Tour 03 | paper |
| 11 | 1200–1319 | 20–22 | Collapse | paper → ink panel → full ink by f1290 |
| 12 | 1320–1469 | 22–24.5 | Endcard | ink · final impact f1320 · settled by f1380 · still to f1469 (90 f) |

Total: 1470 frames (24.5 s), which is the 12 bars plus a 30-frame decay tail.

## Copy (facts only; no hype, no CTA beyond the URL and NOW LIVE)

| Beat | Copy |
|---|---|
| Cold open | LOCAL STUDENT COUNCIL / DSSC — SANTA CRUZ EXTENSION CAMPUS |
| Statement | The council’s records / made public. (bar 2 · bar 3, max 3 words per frame) |
| Purpose (`ONE_LINE_PURPOSE`) | For every / student. (two panels) |
| Reveal | LSC seal · Digital Transparency Board · LOCAL STUDENT COUNCIL |
| Tour | 01 / 03 Your records · 02 / 03 Public finances (+ EVENT ALLOCATIONS, bar 9) · 03 / 03 Direct feedback |
| Endcard | NOW LIVE · seal · Digital Transparency Board · LSYNC.VERCEL.APP · A.Y. 2026–2027 |

## Site visuals

Real captures from https://lsync.vercel.app (1440 × 900 at 2×, light theme, captured 7 Oct 2026): landing, Transparency Board (plus a full-page plate for the scroll), and Feedback & Communication. Shown in a flat browser frame: a 2 px `--ink` border, a solid `--paper` toolbar with the URL in label type, no shadow, no device mockup. The captures contain the site's own soft background tints; they are the real UI and are not repainted.

## Build notes

- **Registry checked first** (`/hyperframes-registry`). `directional-wipe` uses gradients, box-shadow and blur, and `browser-device-stage` carries a box-shadow and device chrome, so both are rejected. The solid wipes and the flat browser frame are hand-built.
- **Beats** are one sub-composition each under `compositions/`: cold-open, statement, purpose, reveal, tour, collapse, endcard. Each has its own paused timeline; slot timing lives in `tools/hosts.py`.
- **Motion blur:** an SVG `feGaussianBlur` with a vertical-only `stdDeviation`, used only on the browser frame's 18 f rise at f720 and ramped 36 → 0 over 10 f. It is never applied to a solid field, because a blurred field edge would read as a gradient.
- **Audio:** generated locally (`tools/sound.py`), premixed and loudness-normalised (`tools/master.sh`), and registered as host audio in `audio_meta.json`. Cues are in `notes/sfx_cue_sheet.md`.
