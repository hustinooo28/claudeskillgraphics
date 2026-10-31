# PAGSIKLAB 2026: the house reveal

A 129-second 16:9 intro (121 s of film and an 8-second closing line) for **PAGSIKLAB**, the Mini Olympics of DSSC – Sta. Cruz Extension Campus, presented by the Local Student Council and produced by *the akashic*. It reveals which team is which Game of Thrones house in the style of the show's opening titles: a camera flies over a model of the realm while each seat assembles itself out of the map with turning gears, and the house medallion rises above it.

The 3D is a real Blender scene rendered with Cycles (sun and sky light, masonry, polished brass, glossy water, motion blur; 10 samples plus denoising at 720p, upscaled to 1080p, about 13 hours on a 4-core CPU) with a depth pass; the compositor uses that depth for atmospheric fog and drifting mist, then grades each house (cold North, amber South, bleached Dorne, storm, fire), adds light shafts, bloom, weather particles, frost on the lens, a slight handheld drift, crushed blacks, a heavy vignette and grain. The music is the council's chosen epic Game of Thrones theme cover (not stored in this repo; put it at `build/track.wav`), edited so its final stinger lands on the title; the sound effects come from the council's royalty-free cinematic SFX reel (FlameSound, free edition), cut into one-shots by `audio/cut_sfx.py`, with clockwork, wingbeats and the voice generated here.

| Time | Scene | Sound |
|---|---|---|
| 0–5 s | A gold trophy on a stone plinth in a dark hall, one shaft of light, dust in the beam: "WHO WILL REIGN?" | Low strings, wind, a deep boom |
| 5–7 s | The words alone on black | Held note |
| 7–10 s | *the akashic* logo inks itself in on a deep blue glow: *a production by* | An ink-stroke whoosh |
| 10–13 s | The Local Student Council seal: *presents* | Strings, a chime |
| 13–18 s | A dive from high above the Westerlands: layer after layer of cloud rushes past the lens, the realm glimpsed far below through the gaps, with the dragon diving ahead | Rushing air, a long riser |
| 18–24 s | The last cloud deck bursts open and the camera races low over the snowy peaks of the great Westerlands massif, the forests below it and the stormlands woods, the dragon just ahead, then pulls up over the coast into Dragonstone | The music opens up with a big hit; whooshes as the peaks and treetops rush past |
| 24–90 s | Six reveals of 11 s (6 bars) each, in team order. The seat builds out of the map, the medallion rises, and a lower third names the house, team, seat, motto and sections. Each house has its own grade and weather. | Clockwork ticks and clunks during each build, a hit when the medallion lands; the score adds a layer per house |
| 90–101 s | **The Seat of the Realm**: the DSSC Sta. Cruz Extension Campus assembles in the centre of the map, with the LSC seal as its medallion | The full theme with choir |
| 101–108 s | "A NEW ERA IS HERE": the camera pulls up over all seven seats | Held chord, choir swell, riser |
| 108–121 s | A breath of silence, then **PAGSIKLAB** ignites left to right; *Mini Olympics 2026*; "Who will claim the throne?"; the LSC seal and the akashic logo | Title impact, final chords, fade |
| 121–129 s | After the fade to black: *One Step Better Than Yesterday.* on dark smoke and embers | A quiet drone and one soft low hit |

| Team | House | Seat | Look and weather | Sections |
|---|---|---|---|---|
| 1 | Targaryen | Dragonstone (island of black spires) | Fire grade, rising embers | BSAB-1B, BSAB-2B, DIT-2A, BSAB-3B |
| 2 | Lannister | Casterly Rock (towers on a great rock) | Gold light, golden dust | BSAB-3A, ACT-1B, BSIT-3B, BSIT-2A |
| 3 | Tyrell | Highgarden (concentric ring walls) | Green and warm, drifting rose petals | BSIT-4A, BSAB-4B, DIT-3A, BPA-2A |
| 4 | Stark | Winterfell (curtain wall and great keep) | Cold, snow | ACT-1A, BSIT-2B, BSIT-4B, DIT-2B |
| 5 | Martell | Sunspear (sandstone domes and a spire) | Sun-baked, heat shimmer | BSIT-3A, BSAB-4A, BSIT-1B, BSAB-2A |
| 6 | Baratheon | Storm's End (one colossal drum tower) | Storm, rain and lightning | BSIT-1A, BPA-1A, BSAB-1A |

Teams, sections, seats and mottos come from the council's Mini Olympics sheet. The house sigils, the PAGSIKLAB lettering and the music track were supplied by the council; the music is a fan cover of the Game of Thrones theme, so this cut is for the event screens, not paid promotion.

## Files

| File | What it does |
|---|---|
| `realm.py` | The single source of truth: seats, teams and every timing (24 fps) |
| `make_map.py` | Paints the realm (colour texture, heightmap, tree positions) into `build/tex/` |
| `make_sigils.py` | Sets each sigil and the LSC seal into a bronze medallion face; draws the campus sign |
| `intro_trophy.py` | The opening shot: the trophy on its plinth in the dark hall (with depth) |
| `dragon_glb.py` | The guide dragon, from the council's model `assets/dragon/black_dragon.glb`: its idle animation always plays underneath, and a flight layer beats the wings, tucks the legs, sways the tail and opens the jaw on the roars, fading out when it perches |
| `dragon.py` | The fallback guide dragon (used if the model file is missing): a rigged wyvern (black scales, ember-red wing membranes, horned head, glowing eyes) with bat-like wings on an arm, wrist and four finger bones; the wings fold on the upstroke and the tips lag, the tail sways, the jaw opens on the roars |
| `realm_look.py` | The Cycles look: lighting, materials, bevels, motion blur and render settings |
| `realm_life.py` | The dragon's flight path (flies alongside the camera, patrols behind each seat, lands on the campus roof), the seat names as extruded brass lettering floating flat on the map (each sinks away while its house is revealed), and marching regiments with house banners and tent camps |
| `cut_emblems.py` | Cuts the council's house emblems out of their backgrounds for the medallions and lower thirds |
| `scene.py` | Builds the Blender scene: terrain, trees, the six castles and the campus, their build animations, the camera path, and a 16-bit depth pass |
| `horizon.py` | Projects the sea horizon from the camera for the low run, so the compositor's horizon glow sits steady |
| `titles.py`, `titles.js` | Every on-screen word, rendered in Cinzel to transparent layers |
| `composite.py` | The film: openers, sky, haze, grading, light shafts, bloom, per-house particles, lower thirds, the finale and the closing line |
| `audio/cut_sfx.py`, `audio/sfx/` | The recorded one-shots (impacts, booms, braams, risers, drones) cut from the SFX reel |
| `audio/score.py` | Sound design locked to the picture (recorded impacts and booms, clockwork, wingbeats, the voice), plus a synthesized fallback score; also writes the effects stem |
| `audio/final_mix.py` | Edits the council's music track to the picture (quiet intro under the cold open, full section from the descent, final stinger on the title) and lays the effects on top; a quiet bed under the closing line |
| `audio/vo_who_raw.wav` | "Who will reign?" (Kokoro `bm_george`), pitched down 3 semitones in `score.py` |

## Rebuild

Needs Blender 4.2 (any build with Workbench; headless works with Mesa's `libegl1`), Python with `numpy scipy opencv-python pillow`, Node with Playwright, and `ffmpeg`.

```sh
python3 make_map.py && python3 make_sigils.py
blender -b --factory-startup -P intro_trophy.py
blender -b --factory-startup -P scene.py -- --save --out build/v6/frames && python3 render_watchdog.py blender 312 2904 100   # ~13 h on 4 CPU cores
blender -b build/scene.blend -P horizon.py
python3 titles.py && node titles.js build/titles.json
python3 audio/score.py && python3 audio/final_mix.py      # needs build/track.wav
python3 composite.py build/film.mp4
ffmpeg -i build/score.wav -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 48000 build/score-norm.wav
ffmpeg -i build/film.mp4 -i build/score-norm.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest PAGSIKLAB-house-reveal.mp4
```

`scene.py -- --stills 600,2200` renders single frames for checking; `composite.py build/check.png 600,2200` composites them.
