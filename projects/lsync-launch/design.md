# design.md — Digital Transparency Board · official launch film

## Palette (locked; exact hex from the live site's CSS, lsync.vercel.app)

| Variable | Hex | Site token | Role |
|---|---|---|---|
| `--ink` | `#080D22` | `--dssc-deep-navy` | darkest brand neutral; open and close fields, all ink type |
| `--paper` | `#F4F6FC` | `--dssc-off-white` | the neutral; tour field, type on dark |
| `--brand` | `#526FF2` | `--dssc-royal-blue` | full-frame field wipes, the reveal field, the purpose panel |
| `--accent` | `#D6B05C` | `--dssc-gold` | used sparingly: the cold-open hairline, index numbers 01–03, the reveal underline, the NOW LIVE dot |

That is three colours plus one neutral. Flat solid fills only. **No gradients, no glows, no blur halos, no shadows, no transparency used as tint.** Every colour in the composition files is written as one of the four `var(--…)` values.

## Structure — REF_A (Strava brand system) applied to the launch

The film is built as a brand-system film, the way REF_A presents Strava: principles → imagery → wordmark → crossing bars → colour → type → the product → the mark → signature. Every section is one sub-composition (`compositions/`), and the slot timing lives in `tools/hosts.py`.

| Bar | Frames | Section | What moves |
|---|---|---|---|
| 1–2 | 0–239 | `principles` | A dashed construction grid draws itself. Four principles type on per word, one per second. The field inverts paper → ink → brand → paper on the beat, and the guides slide to a new grid on each cut. |
| 3–4 | 240–479 | `stack` | A collage of the council's real officer cards and crops of the live site. One piece lands on every eighth (15 f), the four newest stay, and the layer pushes in continuously. It clears at f465, then f465–480 is silent. |
| 5 | 480–599 | `wordmark` | The LSynC wordmark wipes on in the gap. Guides draw with a gold dot and a seal at each corner, and a spec block types in. A crop push into "SynC" follows, while three wordmark chips (ink, brand, outline) stack in. |
| 6 | 600–719 | `cross` | The drop. Brand bars slam across an ink field, with the seal on a tile at the crossing. "Every" slides out of the top edge, "student" types per character, and the grid re-positions at f690. |
| 7–8 | 720–959 | `palette` | Giant cropped "OPEN" pulls back. Ink rises, brand slides in, then gold, each field carrying its hex and RGB spec; the split keeps sliding. |
| 9 | 960–1079 | `type` | "Space Grotesk" builds per character, the glyph set rises line by line, and five brand panels stack in 3 f apart with a giant "a". |
| 10 | 1080–1199 | `interface` | The three live pages land as a stack, fan into a row with index labels 01–03, then a crop push into the Transparency Board. |
| 11 | 1200–1319 | `mark` | The seal opens from its centre inside dashed rings and axes, then the construction retracts and the seal stands alone. |
| 12 | 1320–1469 | `signoff` | NOW LIVE · lsync.vercel.app · Digital Transparency Board · Local Student Council · A.Y. 2026–2027, small and centred, then still for 90+ frames. |

## Typography (the site's own faces, shipped locally under `assets/fonts/`)

| Role | Face | Size (vertical / landscape) | Tracking | Use |
|---|---|---|---|---|
| Giant display | Space Grotesk 700 | 250–440 px, cropped by the frame | −0.05em | Every, OPEN, LSynC, a |
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

## Site visuals

Real captures from https://lsync.vercel.app (1440 × 900 at 2×, light theme, captured 7 Oct 2026): landing, Transparency Board (plus a full-page plate for the scroll), and Feedback & Communication. Shown in a flat browser frame: a 2 px `--ink` border, a solid `--paper` toolbar with the URL in label type, no shadow, no device mockup. The captures contain the site's own soft background tints; they are the real UI and are not repainted.

## Build notes

- **Registry checked first** (`/hyperframes-registry`). `directional-wipe` uses gradients, box-shadow and blur, and `browser-device-stage` carries a box-shadow and device chrome, so both are rejected. The solid wipes and the flat browser frame are hand-built.
- **Beats** are one sub-composition each under `compositions/`: cold-open, statement, purpose, reveal, tour, collapse, endcard. Each has its own paused timeline; slot timing lives in `tools/hosts.py`.
- **Motion blur:** an SVG `feGaussianBlur` with a vertical-only `stdDeviation`, used only on the browser frame's 18 f rise at f720 and ramped 36 → 0 over 10 f. It is never applied to a solid field, because a blurred field edge would read as a gradient.
- **Audio:** generated locally (`tools/sound.py`), premixed and loudness-normalised (`tools/master.sh`), and registered as host audio in `audio_meta.json`. Cues are in `notes/sfx_cue_sheet.md`.
