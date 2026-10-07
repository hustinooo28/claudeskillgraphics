# Variant: brand-glow phone reel

Learned from two 16:9 brand spots by @rikibosso (Shopify "First Sale", Spotify "Single Click", about 21 s each), plus @aimgraphics_dreyan's Maya ad and a McDonald's logo spot by @maleah.id. It's the most "agency" of the styles: **one continuous camera, no hard cuts, one brand colour glowing in the dark, a 3D phone as the hero, and the app's UI rebuilt as floating glass panels.**

The editor bins visible in the Spotify recording show how such a project is organized. Copy that structure:
`01 Scenes 16x9 · 02 Scenes 9x16 · 03 Voice-over · 04 Music stems · 05 SFX (Whooshes, UI & foley, Hits & impacts, Glitch & light) · 06 Graphics (Logos, App icons, Photos)`. Scene list: `S01 Logo · S02 iPhone · S03 Island · S04 Shortcut · S05 Now playing · S06 Listen · S07 With… · S08 Fill to… · S09 Lock… · S10 End card`.

## Look

| | |
|---|---|
| Stage | near-black navy `#05070C` to `#0B0F14`, never pure black |
| Brand glow | one huge soft radial blob of the brand colour (40–70 % of frame, blur 80–140 px) that **drifts and breathes** behind everything, plus a second dimmer blob. It is the scene's light source: glass panels pick up its tint. |
| UI | the app's real screens rebuilt as **dark glass panels** (`rgba(28,32,36,.72)`, 1px `rgba(255,255,255,.08)` border, 20–28 px radius, backdrop blur), at 120–160 % of real size |
| Type | white, semibold, centred; the accent word in the brand colour **with an underline stroke**; the first word of a line often starts with **wide tracking** ("L i s t e n", "S e l l") that tightens as the rest of the line arrives |
| Phone | photoreal iPhone with thickness, shot from low angles, rim-lit by the glow |
| End | the logo on the glow, then a separate tiny "made by" card under a warm spotlight cone |

## Shot grammar (Shopify spot, 22 s)

| t | Beat | Move |
|---|---|---|
| 0–1.3 | Glow fades up. A tiny app icon pops with a thin ring pulse; the wordmark **slides out from behind the icon** (masked) with motion blur | push in slightly |
| 1.3–2.0 | The logo blurs up and away; a phone **tumbles in from above**, rotating through 3D, and lands upright with a glowing ring on the floor | fast tilt down |
| 2.0–3.2 | Lock screen (9:41) → swipe → home screen; camera circles from a low angle | orbit ±20° |
| 3.2–4.0 | The app icon is tapped: it **zooms to fill the frame** (app-open), blurring | push through the icon |
| 4.0–8.4 | Rebuilt app UI: "Products" list as floating rows in 3D, tilted ~15°. Each row in turn **scales up and comes into focus**; the others blur (DOF) | slow dolly + crane, rows scroll |
| 8.4–11.4 | Whip to "Live View" dashboard (map, $0.00, Orders 0): a map dot pings, counters tick | truck right across the panels |
| 11.4–15.2 | Glow only. "S e l l" (tracked) → "Sell what you make" (accent underlined) → whole line streaks out → "and hear your first sale" | text appears word by word with horizontal blur |
| 15.2–16.4 | The line **collapses into a glowing horizontal light streak**, which **expands into a notification pill** ("Order #1001 · $38.00") with a ring flash | — |
| 16.4–17.3 | The pill shrinks into a glowing dot → the dot becomes the logo icon (ring pulse) | — |
| 17.3–20 | The wordmark slides out; logo hold; glow drifts | slow push |
| 20–22.7 | Black; a thin light line expands; "made by riccardo bosso" under a warm spotlight | — |

The Spotify spot uses the same skeleton. It adds an extreme **low-angle phone** (screen almost edge-on), a **Dynamic Island "Now Playing"** expansion, an **album-art fill transition** (one artwork scales to fill the frame), a **3D UI plane** of horizontal cards ("Late Night Drive", "Sunday Slow") viewed at an angle, and a grid of album cards that the camera pans across.

The Maya ad adds a **macro fly-over**: the camera skims centimetres above a tilted phone screen, so UI elements pass by huge and blurred. Then it pulls back to the phone with floating 3D bank cards and big "Global" type, then to a bright gradient set with the phone centred and glass info pills orbiting it, each pointed at by a cursor.

The McDonald's spot is flat 2D but has two moves worth stealing:
- **Logo construction:** the mark draws as a stroke from one line, sunburst ticks flash around it, and the logo card shrinks into a small square that slides to the corner as the hero layout fills the frame.
- **Logo-mask wipe:** the logo's own shape, scaled huge, is the matte that reveals the next scene. Then it shrinks back to the logo.

## Rules of the variant

1. **No hard cuts.** Every shot hands off through an object: logo → phone, icon → app UI, text → light streak → notification → dot → logo. When you must change scenes, whip with blur or push through something.
2. **The glow moves in every shot.** Animate its position and scale slowly (`sine.inOut`, 3–6 s), and pulse it on hits.
3. **Depth of field everywhere.** Exactly one sharp element at a time; neighbours blur 4–10 px.
4. **Sound design is half the spot.** Whoosh on every move, UI foley on taps, a hit on the logo, glitch/light sounds on streaks. A voice-over line every 2–4 s; music stems duck under it.
5. **Pace:** a new idea every 1.5–3 s, about 21 s total for the 16:9 cut, with a separate 9:16 cut from the same scenes.

Fast moves (phone tumble, whips, pushes through icons) follow the motion-blur rules in `style-3d-showcase.md`: a directional or isotropic blur ramp on top of `--mb 4`, never sub-frame blending alone.

## Kit mapping (`kit/camera3d.js`)

| Move | Helper |
|---|---|
| Brand glow blob | `C3.glow(el, { color })` + tween `x/y/scale`; pulse with `C3.pulse`. Drive `rig.light` from its position each frame so shading and glare match the glow |
| Stage floor + contact shadow | `C3.floor(rig, { pool: brand })`, `rig.addShadow(phone, floor)` |
| Parallax glow behind 3D UI | `C3.backdrop(rig, glowEl, { z: -3500 })` |
| 3D phone with live screen | `C3.phone(rig, { screen: htmlElement })`: an extruded rounded slab (stacked layers) with the screen on the front face; tumble/orbit it with the rig |
| Mockup PNG with UI warped into its screen | `C3.fitQuad(contentEl, w, h, quad)` with the corners from `kit/assets/mockups/mockups.json` |
| Logo: icon pop + ring + wordmark slide-out | `C3.logoReveal(iconEl, wordEl, ringEl)` |
| Tracked word that tightens | `C3.track(el, { from: '0.6em', to: '-0.02em' })` |
| Text → light streak → pill | `C3.streak(textEl, lineEl)` then `C3.streakToPill(lineEl, pillEl)` |
| App-open zoom | `C3.appOpen(iconEl, uiEl)` |
| Logo-mask wipe | `C3.maskWipe(sceneEl, maskUrl)` (CSS `mask-image` scaled from logo size to cover) |
| Spotlight end card | `.spotlight` CSS (warm radial cone) + a thin line expanding with `scaleX` |
