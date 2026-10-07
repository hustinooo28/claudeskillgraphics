# design.md — Digital Transparency Board launch film (v3: REF_C glow style)

**Direction (user, after v2):** follow REF_C (@mythiqmotion, the Claude film); no pale colours (saturated blue and yellow, even off the official palette); 40 seconds; every element glows in and fades out; the ending emphasises "One step better than yesterday."

## Look
- **Field:** near-black `#05060B`, lit by a streaky curtain of light falling from the top. The curtain is a pre-rendered PNG (`tools/atmos.py`) that drifts and jumps with the cuts.
- **Colour:** electric blue `#2F6BFF` (hot `#7FB0FF`) carries the film. Signal yellow `#FFC61A` (hot `#FFF1B0`) marks every action: the clicked chip, the pressed button, the lit word, the answer, and "better". The light turns from blue to yellow at the answer and stays warm for the finale.
- **Glow:** text bloom via `text-shadow`; glass boxes with a glowing rim; glow PNGs behind key elements.
- **Entrances** (`LK.hot`): every element arrives overexposed and blurred (brightness ×2–4, blur 6–20 px) and cools to its real look with expo.out.
- **Exits** (`LK.away`): elements drift, blur and dissolve into the dark. Nothing cuts out except the one REF_C hard cut (f540).
- **Typing** (`LK.type`): per character; the word being typed glows yellow, then cools to white. Key words can stay lit.
- **Type:** Space Grotesk (wordmark, headlines) and DM Sans (UI), both the site's own faces, shipped locally.
- **Site visuals:** the real dark-theme captures of lsync.vercel.app (`capture/pages-dark/`), shown on a glowing card in 3D. The Find Your Records and Ask a Question boxes are restyled recreations of the site's own forms, using the same fields, labels and buttons.

## Structure (60 fps, 2400 frames = 40 s; slot timing in `tools/hosts.py`)

| Time | Frames | Sub-composition | REF_C source | What happens |
|---|---|---|---|---|
| 0–40 s | 0–2399 | `atmos` | the light | Curtain fades up; jumps on the cut; settles behind the card; turns yellow at the answer; warm for the finale; fades out. |
| 0–9 s | 0–539 | `intro` | 0–3.2 s | Rings draw in light, the seal arrives white-hot spinning, "LSynC" builds per character from blur. White-hot capsules push the logo away and cool into the site's sections (Council, Records, Transparency, Inquiry, Updates). The cursor clicks Records (yellow) and the camera leans in. |
| 9–19.5 s | 540–1169 | `search` | 3.2–6.6 s | Hard cut to an extreme close-up of Find Your Records. "Juan Dela Cruz" (the site's own placeholder) types on while the camera pulls back, then "2021-00001". Click on Search Records; the box flies up and the real Event Allocations rows stream up in perspective. |
| 18–34 s | 1080–2039 | `board` | 6.6–12 s | The dark Transparency Board arrives white-hot on a tilted glowing card and turns to face us. The camera drops to Ask a Question, where "How much did Intramurals collect?" types with Intramurals lit, and send. The camera rises; the card scrolls to the real Intramurals row, which lights up yellow, and a callout reads "Intramurals · ₱1,050 collected". The card floats up into the dark. |
| 34–40 s | 2040–2399 | `finale` | 12–14 s | The seal arcs in white-hot under warm light. "One step better than yesterday." types on, and "better" ignites yellow with the final impact and stays lit. NOW LIVE · lsync.vercel.app, then Digital Transparency Board · Local Student Council · A.Y. 2026–2027. Everything lifts and dissolves. |

## Formats
One set of sub-compositions serves both 1920×1080 (landscape, REF_C's own format) and 1080×1920 (vertical). Each beat reads its own root size (`LK.dims`) and switches layout constants; `python3 tools/hosts.py [vertical|landscape]` rewrites the host.

## Audio
Generated locally (`tools/sound.py`, `tools/master.sh`): an ambient pulse bed following the REF_C arc, plus 102 frame-placed cues (key ticks per typed character, clicks, whooshes, shimmer on the answer, final impact with reverb under "better"). Delivered at −13.8 LUFS integrated, −2.7 dBTP. Cue list: `notes/sfx_cue_sheet.md`.
