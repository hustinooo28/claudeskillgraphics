# PAGSIKLAB 2026: the house reveal

A 121-second 16:9 intro for **PAGSIKLAB**, the Mini Olympics of DSSC – Sta. Cruz Extension Campus, presented by the Local Student Council and produced by *the akashic*. It reveals which team is which Game of Thrones house in the style of the show's opening titles: a camera flies over a model of the realm while each seat assembles itself out of the map with turning gears, and the house medallion rises above it.

The 3D is a real Blender scene (Workbench renderer, so it renders on a CPU in about an hour) with a depth pass; the compositor uses that depth for atmospheric fog and drifting mist, then grades each house (cold North, amber South, bleached Dorne, storm, fire), adds light shafts, bloom, weather particles, frost on the lens, a slight handheld drift, crushed blacks, a heavy vignette and grain. The score is original and synthesized.

| Time | Scene | Sound |
|---|---|---|
| 0–5 s | A gold trophy on a stone plinth in a dark hall, one shaft of light, dust in the beam: "WHO WILL REIGN?" | Low strings, wind, a deep boom |
| 5–7 s | The words alone on black | Held note |
| 7–12 s | **2026** forged at the anvil: three hammer blows throw sparks, the numerals glow white-hot and cool to iron, embers rise into darkness | Anvil clangs, sizzle, fire bed |
| 12–15 s | *the akashic* logo inks itself in on a deep blue glow: *a production by* | An ink-stroke whoosh |
| 15–18 s | The Local Student Council seal: *presents* | Strings, a chime |
| 18–24 s | Falling through clouds onto the realm; the cello ostinato starts | Cloud whoosh, the theme |
| 24–90 s | Six reveals of 11 s (6 bars) each, in team order. The seat builds out of the map, the medallion rises, and a lower third names the house, team, seat, motto and sections. Each house has its own grade and weather. | Clockwork ticks and clunks during each build, a hit when the medallion lands; the score adds a layer per house |
| 90–101 s | **The Seat of the Realm**: the DSSC Sta. Cruz Extension Campus assembles in the centre of the map, with the LSC seal as its medallion | The full theme with choir |
| 101–108 s | "A NEW ERA IS HERE": the camera pulls up over all seven seats | Held chord, choir swell, riser |
| 108–121 s | A breath of silence, then **PAGSIKLAB** ignites left to right; *Mini Olympics 2026*; "Who will claim the throne?"; the LSC seal and the akashic logo | Title impact, final chords, fade |

| Team | House | Seat | Look and weather | Sections |
|---|---|---|---|---|
| 1 | Targaryen | Dragonstone (island of black spires) | Fire grade, rising embers | BSAB-1B, BSAB-2B, DIT-2A, BSAB-3B |
| 2 | Lannister | Casterly Rock (towers on a great rock) | Gold light, golden dust | BSAB-3A, ACT-1B, BSIT-3B, BSIT-2A |
| 3 | Tyrell | Highgarden (concentric ring walls) | Green and warm, drifting rose petals | BSIT-4A, BSAB-4B, DIT-3A, BPA-2A |
| 4 | Stark | Winterfell (curtain wall and great keep) | Cold, snow | ACT-1A, BSIT-2B, BSIT-4B, DIT-2B |
| 5 | Martell | Sunspear (sandstone domes and a spire) | Sun-baked, heat shimmer | BSIT-3A, BSAB-4A, BSIT-1B, BSAB-2A |
| 6 | Baratheon | Storm's End (one colossal drum tower) | Storm, rain and lightning | BSIT-1A, BPA-1A, BSAB-1A |

Teams, sections, seats and mottos come from the council's Mini Olympics sheet. The house sigils are fan imagery supplied by the council, and the music is original (no Game of Thrones theme).

## Files

| File | What it does |
|---|---|
| `realm.py` | The single source of truth: seats, teams and every timing (24 fps) |
| `make_map.py` | Paints the realm (colour texture, heightmap, tree positions) into `build/tex/` |
| `make_sigils.py` | Sets each sigil and the LSC seal into a bronze medallion face; draws the campus sign |
| `intro_trophy.py` | The opening shot: the trophy on its plinth in the dark hall (with depth) |
| `scene.py` | Builds the Blender scene: terrain, trees, the six castles and the campus, their build animations, the camera path, and a 16-bit depth pass |
| `titles.py`, `titles.js` | Every on-screen word, rendered in Cinzel to transparent layers |
| `composite.py` | The film: openers, sky, haze, grading, light shafts, bloom, per-house particles, lower thirds and the finale |
| `audio/score.py` | The score and sound design, locked to the 11-second house windows |

## Rebuild

Needs Blender 4.2 (any build with Workbench; headless works with Mesa's `libegl1`), Python with `numpy scipy opencv-python pillow`, Node with Playwright, and `ffmpeg`.

```sh
python3 make_map.py && python3 make_sigils.py
blender -b --factory-startup -P intro_trophy.py
blender -b --factory-startup -P scene.py -- --frames 432-2904 --out build/v2/frames     # ~1.3 h on 4 CPU cores
python3 titles.py && node titles.js build/titles.json
python3 audio/score.py
python3 composite.py build/film.mp4
ffmpeg -i build/score.wav -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 48000 build/score-norm.wav
ffmpeg -i build/film.mp4 -i build/score-norm.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest PAGSIKLAB-house-reveal.mp4
```

`scene.py -- --stills 600,2200` renders single frames for checking; `composite.py build/check.png 600,2200` composites them.
