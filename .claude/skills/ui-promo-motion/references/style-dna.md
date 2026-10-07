# Style DNA — measured from the references

## Pacing

Cut points detected with ffmpeg scene detection plus manual frame review:

| Reference | Length | Shots | Avg shot | Notes |
|---|---|---|---|---|
| Ride-hailing app ad (16:9) | 16.5 s (14 s content) | 7 | ~2.0 s | hook text → logo → phone → swoosh → search UI → CTA → end logo |
| Motivational kinetic reel (9:16) | 14.6 s | 8 | ~1.8 s | cursor/selection-box text, object drops, phone scroll, closing line |
| "Apple-style" tutorial teaser (16:9) | 50 s (46 s content) | ~22 | ~2.1 s | VO-driven; type + widgets; 3 dark interludes |
| Productivity-app teaser (16:9) | 20 s | 9 | ~2.2 s | type → map → icon chain on a line → app cloud → cards → logo |

Rules of thumb:
- A shot lives **1.5–3 s**. Text-only shots 1.2–2 s. Logo/end card 1.5–2.5 s.
- **Something is always moving.** Even holds have a slow push (scale 1 → 1.04 over the hold) or background drift.
- Intro hook lands within the first **0.3 s** (first word visible by frame 3–9).

## Palette

| Role | Value | Seen as |
|---|---|---|
| Canvas | `#F2F2F4` → `#FFFFFF` | soft radial gradient, lighter in centre |
| Brand tint | brand colour at 8–15 % alpha, large blurred radial | pale green wash (ride app), grey blobs (productivity) |
| Ink | `#111113` | headlines |
| Secondary ink | `#8E8E93` / `#A1A1A6` | sub-lines, words on their way out |
| Accent | one saturated brand colour | single highlighted word, logo, CTA frame |
| Dark interlude | `#0E0E10` – `#1C1C1E` with a soft white vignette | "problem" beats, end card |
| Glow | accent or `#4A8CFF` at 35–50 %, blur 40–60 px | behind hero cards |

Full-bleed brand-colour frame (e.g. `#29C04F`) is used once, for the CTA.

## Typography

- **Inter Display / SF Pro Display**, weights 600–700 for headlines, 400–500 for sub-lines.
- Tracking −0.02 to −0.03 em; line-height 1.0–1.1.
- **Mixed weight/size inside one line** (motivational reel: "here is the **truth**", "that's what builds **success**"). The key word is 2–3× bigger or a different colour.
- **One accent word per line** in the brand colour ("So, progress **slows**").
- Sub-lines are small (25–35 % of headline size), light grey, revealed word by word *after* the headline lands.

## Depth

- **Depth-of-field blur**: unfocused layers `filter: blur(6–12px)` and opacity 0.4–0.6; the focused item scales 1.15–1.3×.
- **Shadows**: cards `0 30px 60px -10px rgba(0,0,0,.14), 0 8px 20px rgba(0,0,0,.06)`; device mockups have a larger, softer shadow.
- **Radii**: cards 28–36 px; pills fully rounded; app icons 22 % of width.
- **Glass**: occasional `backdrop-filter: blur(20px)` panels with `rgba(255,255,255,.6)`.
- **Giant out-of-focus foreground shapes** (motivational reel): huge black blobs/asterisks at 10–20 px blur, slowly rotating at the frame edges, for parallax depth.

## Easing and durations (GSAP)

| Move | Ease | Duration |
|---|---|---|
| Word / element entrance | `expo.out` | 0.5–0.8 s, stagger 0.08–0.18 s |
| Card pop with settle | `back.out(1.3–1.7)` | 0.5–0.7 s |
| Exit | `power3.in` | 0.3–0.45 s, stagger 0.04–0.06 s |
| Zoom-through (shot exit) | `power3.in` | 0.4–0.6 s, scale ×2.5–4, blur 0 → 14 px |
| Zoom-from (shot entry) | `expo.out` | 0.6–0.8 s, from scale 0.3–0.5, blur 14 → 0 |
| Camera pan / follow | `expo.inOut` | 0.6–0.9 s |
| Morph (pill → circle) | `power3.inOut` | 0.3–0.4 s |
| Circle wipe | `power3.in` | 0.3–0.4 s |
| Line draw | `power2.inOut` | 0.5–0.9 s |
| Typing | stepped | 12–16 chars/s |
| Background drift | `none` / `sine.inOut` | whole shot |

Motion blur: render with sub-frame blending (`--mb 4`) rather than faking it; add `filter: blur()` only for depth-of-field and the "sharpen into focus" look.
