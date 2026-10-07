# LSC Digital Transparency Board: promo video

A 48-second 16:9 motion graphics promo for [LSynC](https://github.com/hustinooo28/LSynC), the Local Student Council's Digital Transparency Board (DSSC – Santa Cruz Extension Campus). It was built with the `ui-promo-motion` skill in this repo.

| Scene | Time | Voice-over |
|---|---|---|
| Hook | 0–3 s | "Where did your contribution go?" |
| Doubt | 3–6.6 s | "Was your attendance recorded? Where's your receipt?" |
| Brand reveal | 6.6–13.6 s | "Meet the Digital Transparency Board…" |
| Find Your Records | 13.6–19.6 s | name + student ID → contributions and attendance |
| Receipts + QR | 19.6–23.8 s | official receipt OR-2026-000001, attendance QR |
| Transparency board | 23.8–30.2 s | live fund totals + transaction ledger |
| Officers | 30.2–36.6 s | QR attendance scan, offline → syncing → synced |
| Notifications + feedback | 36.6–42.4 s | push notifications, feedback form |
| End card | 42.4–48 s | "One step better than yesterday." |

Brand colours (#080D22 navy, #526FF2 royal blue, #D6B05C gold), fonts (Space Grotesk, DM Sans), the LSC seal and the officer cards come from the LSynC repo. The student "Juan Dela Cruz", the peso amounts and the ledger entries are **sample data for the video only**.

## Rebuild

```sh
npm install                                         # fonts + gsap, served locally while rendering
# voice-over (see ../../.claude/skills/ui-promo-motion/scripts/tts.py for Kokoro setup)
python tts.py audio/lines.json audio/vo --voice af_heart --check
# soundtrack: music bed + sound effects + ducked voice-over
python audio/mix.py audio audio/vo build/mix.wav
ffmpeg -i build/mix.wav -af loudnorm=I=-14:TP=-1.5:LRA=11 build/mix-norm.wav
# video
node ../../.claude/skills/ui-promo-motion/scripts/render.cjs index.html build/promo.mp4 --fps 30 --mb 4 --audio build/mix-norm.wav
```

Open `index.html` in a browser to preview: `space` pauses, the arrow keys step frames, and `?t=24` jumps to a time.
