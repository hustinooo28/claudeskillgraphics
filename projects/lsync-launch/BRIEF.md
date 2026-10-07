---
workflow: product-launch-video
flow: automation
storyboard: no
message: "The Digital Transparency Board is live — the council's records, open to every student."
destination: tiktok-reels
aspect: 1080x1920
language: en
audience: "Students of DSSC – Santa Cruz Extension Campus"
length: 24s
angle: official-launch
---

## Intent

REVISION — site launch film, v-next. An OFFICIAL LAUNCH, not an advertisement: confident, restrained,
institutional, announced rather than sold. Swiss-grid precise, editorial, calm power. States facts —
what it is, who it is for, that it is live. Type and space carry authority; the payoff is a date stamp
and a URL lockup. The previous brand-glow reel is below standard and is not iterated on — rebuilt from a
clean composition.

## Assets

- capture/ — the live site https://lsync.vercel.app (hero, Transparency Board, Find Your Records, Feedback), captured as-is. Never faked, never in a 3D device mockup; shown in a flat minimal browser frame.
- LSC seal — the council's official logo (from the LSynC repo / user upload).

## Customizations

- Formats: vertical 1080x1920 (primary) and landscape 1920x1080. 60 fps.
- Tempo lock 120 BPM: 1 beat = 30 frames, 1 bar = 120 frames; every cut and major move on a beat or an eighth (15 frames). 12 bars = 24 s.
- Storyboard (fixed by the user): Cold open → Statement → Purpose → Reveal → Site tour (01/02/03 + one interaction in bar 9) → Collapse → Endcard (NOW LIVE · seal · URL · date stamp, 90-frame still hold).
- Facts: SITE_NAME "Digital Transparency Board"; ORG_NAME "Local Student Council · DSSC – Santa Cruz Extension Campus"; URL lsync.vercel.app; date stamp "A.Y. 2026–2027" (user-confirmed).
- Sound: minimal percussive institutional bed at 120 BPM, drop on bar 6; whoosh / riser / impact+sub / UI ticks / reverse cymbal / one eighth-note silence before the reveal. Every SFX placed by frame in notes/sfx_cue_sheet.md. Mix to about −14 LUFS, true peak ≤ −1 dBTP.

## Notes

- Color: flat solid fills only — zero gradients anywhere (grep must find none). Max 3 colors + 1 neutral, pulled from the site CSS and locked as variables (--ink, --paper, --brand, --accent).
- Banned: hype words, CTA language beyond the URL and "NOW LIVE", starbursts, stickers, emoji, arrows, glows, lens flares, light leaks, chromatic aberration, glitch, glassmorphism, neon, heavy shadows, bevels, shaky camera, random 3D spins.
- Easing: enter expo.out, exit expo.in, transitions power4.inOut; no linear on visible motion except hairline draws; no bounce/elastic; overshoot ≤ 4 %.
- Vertical safe zones: no text in the top 12 % or bottom 20 %.
- References: REF_A (@ddaop_ Strava brand system — the primary basis), REF_B (@graftmotion Pinterest), REF_C (@mythiqmotion Claude), plus the user's upload Download_8 (@husnixd). Breakdown in notes/.
- Run mode: autonomous ("execute this properly in one pass"). HeyGen not signed in → local engines; all audio is generated locally and registered as host audio.
