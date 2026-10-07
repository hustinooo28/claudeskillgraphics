# Variant: dark glow 3D showcase

Learned from a 24-second portfolio reel by @hatsu6961 (16:9). It is the same promo grammar as the main style, but staged in **3D space with a moving camera**. Use it when the user asks for 3D, camera movement, viewing angles, or a "techy" / premium dark look. The kit is `kit/camera3d.js`, and `kit/template-3d.html` is a working 13.6 s demo of every move below.

## Look

| | |
|---|---|
| Stage | pure black `#000` |
| Light | one warm emissive colour (orange `#FF5A1F`): neon wave, card rims, ambient bloom. Swap it for the brand colour. |
| Type | small, quiet white or black text (40–56 px on 1920), regular/medium weight, one accent word in red (`#E5322D`). It never shouts; the 3D does the shouting. |
| Interludes | white frames for typography (intro and outro), dark with a soft diagonal light beam for the question line |
| Glow | `border: 2px solid rgba(255,150,110,.95); box-shadow: 0 0 26px 4px rgba(255,90,31,.9), 0 0 120px 24px rgba(255,80,20,.38)` |
| Accent flash | a 2-frame colour invert on every big cut (white ↔ black, orange ↔ cyan) |

## Shot list of the reference

| t (s) | Shot | Camera / move |
|---|---|---|
| 0–2.6 | White. "Welcome" → "to my" → **Portfolio** (red), centred, one word group at a time | static; words blur in and out |
| 2.6–2.9 | Flash to grey, invert, cut to black | — |
| 2.9–3.3 | Black, glowing orange neon wave across the middle, "Portofolio" | wave flows sideways |
| 3.0–3.4 | Dashed guide lines slide in from the edges and frame a rectangle; a white panel grows inside it | 2D |
| 3.4–4.0 | Panel content flashes (pink, white, an inverted cyan frame) | — |
| 4.0–4.5 | The panel becomes a **curved screen** (convex cylinder, dashed outline curving with it) showing a red moodboard | **dolly in** until it nearly fills the frame |
| 4.5–5.0 | **Pan along the curve** to the next panel, with heavy motion blur | cylinder rotates ~25° in 0.4 s |
| 5.0–5.5 | White logo panel; an iris inverts it to black | hold |
| 5.5–6.0 | Pan again, then **pull back**: a 2×2 grid of curved panels (chat UI, file icons, "38 GB", Drive) | dolly out + slight tilt |
| 6.0–7.8 | Grid panels animate their contents | slow drift / truck |
| 7.8–8.1 | **Push through** the wall with blur, then a white wave flash | fast dolly in |
| 8.1–9.8 | Dark, soft diagonal light beam; "Got a project in mind?" (small) | beam drifts; text words blur in |
| 9.8–10.4 | A glowing white card rises from below; a stack of cards appears behind it | crane up |
| 10.4–15.5 | **Card cloud**: 6–10 glowing UI cards floating at different depths, tilted 10–25° | slow **orbit** + crane; cards slide past at different speeds (parallax); far cards blur |
| 15.5–16.4 | Camera rushes forward past cards and **flies into one screen** | fast dolly with motion blur |
| 16.4–17.3 | Inside the screen: 3D logo, then a glowing cyan planet horizon with tool icons bursting outward | push in |
| 17.3 | **Whip pan** left into white | — |
| 17.5–20.4 | White. "Let's bring your ideas" word by word, blur out; "to" stays; **"life"** resolves out of scrambled letters, in red | static |
| 20.4–22 | Invert cut to black: "life" in cyan, then the "Hatsu." wordmark with a soft glow; fade | static |

Rhythm: three acts (white type → 3D work → white type). 3D shots run 1.5–5 s and keep the camera moving the whole time. Cuts land on a flash.

## Camera vocabulary (`camera3d.js`)

The camera is `rig.cam = { x, y, z, rx, ry, rz, focus, dof }`. The z = 0 plane renders 1:1 when `cam.z = fov`.

| Move | How | Typical timing |
|---|---|---|
| **Dolly in/out** | tween `cam.z` | 0.6–1.0 s `expo.inOut`; a punch-through is 0.45 s `power3.in` down to z ≈ 200 |
| **Truck / crane** | tween `cam.x` / `cam.y` | over the whole shot, `sine.inOut` |
| **Pan / tilt** | tween `cam.ry` / `cam.rx` (±5–10°) | layered on a dolly so the move never feels flat |
| **Orbit** | `tl.add(rig.orbit({ cx, cz, radius, from, to, duration }), at)` | 20–40° over 2–3 s |
| **Fly into a screen** | `tl.to(rig.cam, { ...rig.frame(card, 1.2), duration: .75, ease: 'expo.inOut' })`, then cut to the screen's content full-frame | 0.6–0.9 s |
| **Pan along a curved wall** | `tl.to(wall, { ry: wall.panTo(px), ease: 'power2.inOut', duration: .75 })` + `C3.motionBlur(view).swell(22, .75)` | 0.7–0.8 s |
| **Whip pan** | `C3.whip(el)`; cut on the blurriest frame | 0.3 s |

Depth of field: objects added with `rig.add` blur in proportion to their distance from `cam.focus` (`dof` px per 1000 px, capped at `maxBlur`). `rig.orbit` and `rig.frame` set `focus` for you.

## Building blocks

- `C3.curvedWall(rig, src, { width, height, radius, strips, border })`: an image or SVG mapped on a convex cylinder (72 strips is smooth at 1080p). Tile several panels into one texture and pan between them. Build textures with `C3.panelSVG(w, h, bg, blocks)`, or use real screenshots (PNG) of the user's app.
- `rig.add(el, { x, y, z, rx, ry })`: any DOM element (a real HTML UI card) placed in 3D. Tween the returned object's `x/y/z/ry/s`; the rig re-applies it every frame.
- `C3.neonWave(svg, { y, amp, thickness, color })`: glowing tube; tween `wave.phase` with `onUpdate: wave.draw`.
- `C3.guides(container, rect)`: dashed design-tool guides sliding in to frame a rectangle.
- `C3.scramble(el, text, { duration })`: deterministic glyph-scramble reveal.
- `C3.invertFlash(tl, '#stage', at)`: 2-frame invert on a cut.
- Ambient bloom: a big blurred radial gradient in the glow colour behind the 3D layer, drifting slowly.

## Lighting and a reactive environment (always on for 3D)

A 3D move only sells when the **surroundings react** and the **surfaces are lit**. Flat, unlit cards over a 2D backdrop read as cardboard sliding over wallpaper.

- **Put the background in the world.** Use `C3.backdrop(rig, el, { z: -3000, cover })` for glows, gradients and the neon wave, so they parallax against the subject as the camera dollies, orbits or cranes. With `cover: 1` and `camZ` set to the camera's starting z, the 3D backdrop matches a 2D one exactly, so you can swap one for the other mid-shot without a visible jump.
- **Give it a floor.** `C3.floor(rig, { y, pool, line })` adds a perspective grid with a light pool. It foreshortens with every camera move and is the strongest single cue that the camera really moves. Ground objects with `rig.addShadow(obj, floor)`: a soft contact shadow that spreads and fades as the object rises (a phone landing, a card lifting).
- **Light every surface.** `rig.light = { x, y, z, ambient, spec, shininess }` is a point key light in world space:
  - Objects added with `lit: true` (or `lit: 'glare'` for glass and screens) shade as they turn away from it.
  - A Blinn specular glare slides across them as they rotate.
  - `C3.curvedWall` strips are shaded smoothly (per-edge gradients), so a highlight band glides along the curve as the wall pans.
  - `C3.phone` gets screen glare plus side walls that brighten or darken with the light.
- **Tie the light to what the viewer sees.** If a glow blob is visible, drive `rig.light` from its position every frame (`MK.onFrame`), so highlights always come from the visible light source. Sweep the light against the camera move (orbit left, light right) for the richest glints, and pulse the glow when something lands.

Defaults that look right: `ambient` 0.4–0.65, `spec` 0.55–0.75, `shininess` 22–30, with the key light above, to one side and in front (`y` ≈ −1000, `z` ≈ 1500–2600).

## Avoiding the "stretched / smeared" look (learned the hard way)

- **Keep curves gentle.** A curved wall should wrap **~25° per panel and ≤ 120° in total** (`C3.curvedWall` defaults to 70° and clamps at 120°). A 160° wrap reads as a drum, and its edges fold and stretch.
- **Use a long lens for 3D scenes.** Use `fov` 1800–2400 for walls and card clouds; short lenses (≤ 1200) exaggerate perspective at the frame edges. Move the camera back instead (`cam.z = fov × objectWidth / desiredScreenWidth`).
- **Respect the motion-blur speed limit.** Sub-frame blending (`--mb 4`) shows anything moving faster than ~40 px per frame as **stacked copies**, not a smear. For fast pans and whips, add a directional blur with `C3.motionBlur(el, 'x').swell(peak, duration)` (~20 px peak for a full-panel pan). For zoom-throughs, ramp an isotropic `blur()` on the moving layer. Pans of a full screen width should take **≥ 0.7 s** with `power2.inOut`.
- **Don't swap a flat panel for a 3D one in a single frame.** Put the content on the flat panel first, then dissolve over 0.15–0.2 s into the 3D object, framed at the same size.

## Gotchas

- The rig updates through `MK.onFrame`, so **every** tween on `rig.cam` or a placed object is frame-exact. Don't rely on `onUpdate` ordering.
- Objects closer than 40 px to the eye are hidden, so the camera can pass through cards safely.
- CSS 3D cannot intersect planes correctly. Keep cards at clearly different depths, and don't put two curved walls in the same space.
- Large blurred box-shadows on many 3D cards are the slow part of rendering. Expect ~0.25 s per sub-frame at 1080p.
