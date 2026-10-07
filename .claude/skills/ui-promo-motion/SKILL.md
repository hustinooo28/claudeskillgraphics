---
name: ui-promo-motion
description: Make Apple-style UI promo videos — short (10–50 s) product/app motion graphics with kinetic typography, floating UI cards, depth-of-field blur, and motivated transitions (zoom-through, shape wipe, button-to-circle wipe, swoosh reveal, camera-follow line), plus two dark variants with a real 3D camera rig (curved screen walls, orbiting card clouds, fly-into-screen; a brand-glow phone reel with a 3D iPhone, glass UI panels and light-streak transitions) — built in HTML/GSAP and rendered frame-by-frame to MP4 with voice-over, music and SFX. Use when the user asks for a motion graphics video, app promo, product teaser, kinetic typography, "Apple style" animation, 3D camera moves / viewing angles, TikTok/Reels/Shorts promo, logo reveal, or wants an HTML animation exported as MP4.
---

# UI Promo Motion

A style learned from four reference promos (a ride-hailing app ad, a motivational kinetic-type reel, an "Apple-style motion graphics" tutorial teaser, and a productivity-app teaser). All four share one grammar: **one idea per shot, a cut every 1.5–3 s, and every transition is caused by something moving in the shot.**

Read these before building:
- `references/style-dna.md` — palette, type, depth, pacing, and easing numbers measured from the references.
- `references/techniques.md` — every signature move, with its measured timing and the `motion-kit.js` call that reproduces it.
- `references/breakdowns.md` — shot-by-shot timelines of the four references. Use them as storyboard templates.
- `references/style-3d-showcase.md` — the **3D variant**: black stage, emissive glow, curved screen walls, card clouds, orbit / dolly / fly-into-screen camera moves. Read it whenever the user wants 3D, camera movement or viewing angles; build with `kit/camera3d.js` starting from `kit/template-3d.html`.
- `references/style-brand-glow-reel.md` — the **brand-glow phone reel**: dark stage lit by one drifting brand-colour glow, a 3D phone hero, the app's UI as floating glass panels, no hard cuts (text → light streak → notification → logo). Start from `kit/template-glow.html`. Phone mockups with transparent screens and their screen corners are in `kit/assets/mockups/` (`mockups.json`; warp UI in with `C3.fitQuad`).
- `references/audio.md` — voice-over (local TTS), procedural music/SFX, ducking and loudness. Read it whenever the video needs sound.

## Workflow

1. **Script in beats** (and, if there is voice-over, generate it first with `scripts/tts.py` — its line durations set the scene times). Write the video as a beat list: `t, shot, on-screen text, move, transition out`. Keep on-screen text to 1–5 words per beat. Typical arc: *hook question → problem → brand reveal → 2–4 feature shots → CTA → end logo.* 12–20 s for a teaser.
2. **Copy the kit.** Copy `kit/template.html` and `kit/motion-kit.js` into a working folder. The template is a 1080×1920 stage (switch to 1920×1080 by changing `--w/--h` and `STAGE`), a GSAP master timeline, and a demo sequence to replace.
3. **Build every beat as a timeline segment** with `motion-kit.js` helpers placed by absolute time labels on one master timeline. Never use CSS animations/transitions, `setTimeout`, or `Date.now()` — the renderer only controls GSAP time. Canvas/three.js scenes must draw from the time passed to `window.__seek(t)`.
4. **Preview** by opening the HTML in a browser (it loops; `space` pauses, `←/→` scrubs, `?t=4.2` jumps).
5. **Render** with the frame-stepping renderer:
   ```sh
   npm install --prefix <skill-dir>          # once: gsap + Inter, served locally to the renderer
   node <skill-dir>/scripts/render.cjs page.html out.mp4 --fps 30 --mb 4
   ```
   `--mb 4` renders 4 sub-frames per frame and blends them (real motion blur — this is what makes fast moves read as "premium"). Add `--audio track.mp3` to mux music, `--start/--end` to render just a section while iterating, `--jpeg` for ~2× faster drafts. Expect ~3 s of rendering per frame-second without blur, ~9 s with `--mb 4`, at 1080×1920. See `node scripts/render.cjs --help`.
6. **Check the output**: extract a contact sheet (`ffmpeg -i out.mp4 -vf "fps=2,scale=270:-1,tile=6x4" sheet.jpg`) and look at it before handing over. Fix anything that holds too long, cuts too early, or has text unreadable for < 0.6 s.

## Non-negotiables of the style

- **Light canvas, one accent.** Off-white (#F2F2F4–#FFFFFF) with a soft radial tint of the brand colour; near-black type; one saturated brand accent. Dark (#0E0E10) shots only as punctuation (1–2 per video).
- **Type is the hero.** Inter/SF Pro Display, 600–700 weight, tracking −0.02 to −0.03 em. Headlines appear **word by word** (from blur + small scale), never as a whole block.
- **Depth through blur and shadow, not 3D clutter.** Out-of-focus elements blur 6–12 px; focused cards get big soft shadows (`0 30px 60px rgba(0,0,0,.12)`) and sometimes a coloured glow.
- **Every cut is motivated.** Exit a shot by zooming through it, wiping with a shape, morphing a button into the next scene, or panning along a line. Hard cuts only on a strong beat (e.g. into a full-bleed brand-colour frame or a dark shot).
- **Fast in, slow settle.** Entrances use `expo.out` (0.5–0.8 s); exits use `power3.in` (0.3–0.45 s). Nothing moves linearly except slow background drift.
- **Hold readable text ≥ 0.6 s** after it lands; hold the final logo ≥ 1.2 s.

## Choosing a variant

| The user wants… | Variant | Start from |
|---|---|---|
| clean, bright, Apple-keynote feel; explainer; light UI | main style | `kit/template.html` |
| 3D, camera movement, viewing angles, techy/dark, a showreel | 3D showcase | `kit/template-3d.html` |
| a premium brand/app ad, a phone hero, one brand colour, VO-driven | brand-glow reel | `kit/template-glow.html` |

The variants share `motion-kit.js`, `camera3d.js`, the renderer and the audio tools, so moves can be mixed (e.g. the brand-glow reel's logo reveal inside the main style).

## Format defaults

| | Vertical (TikTok/Reels/Shorts) | Landscape |
|---|---|---|
| Stage | 1080×1920 | 1920×1080 |
| fps | 30 (60 for very fast work) | 30 |
| Headline size | 96–140 px | 90–120 px |
| Safe area | keep text out of bottom 300 px and right 140 px (platform UI) | 80 px margins |

## Limits to tell the user

Voice-over is synthetic (Kokoro). Music and effects are procedural and simple; a licensed track supplied by the user will sound better (mux it with `--audio`). No photoreal footage/people — this is shapes, type, UI, icons, logos, particles, simple 3D. Brand logos and real app UI must come from the user or be original stand-ins.
