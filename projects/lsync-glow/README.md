# LSC Digital Transparency Board: brand-glow reel

A 40-second 16:9 reel for [LSynC](https://github.com/hustinooo28/LSynC), the Local Student Council's Digital Transparency Board (DSSC – Santa Cruz Extension Campus). It's built with the `ui-promo-motion` skill's **brand-glow reel** variant: one continuous camera, a royal-blue glow that lights every 3D surface, a lit 3D phone, and the app's UI rebuilt as floating glass panels.

| Time | Scene | Voice-over |
|---|---|---|
| 0–3.4 s | "Every peso. / event. / student." Kinetic type on the glow, collapsing into a light streak | "Every peso. Every event. Every student." |
| 3.4–6.8 s | The streak becomes a dot, then the LSC seal (impact + ring); "Digital Transparency Board" slides out | "Meet the Digital Transparency Board." |
| 6.8–10 s | A lit 3D iPhone tumbles onto a blue floor; lock screen → Find Your Records; name and ID are typed | "Students enter their name and student ID," |
| 10–13.6 s | The camera pushes into the screen, which dissolves into glass panels: profile, ₱350 counter, attendance, *Fully Paid* | "…and their contributions and attendance appear. Instantly." |
| 13.6–18.5 s | Truck to the official receipt OR-2026-000001 and the scannable QR; orbit; both "Saved" | "Official receipts, and a personal attendance QR code…" |
| 18.5–24.3 s | Truck to the Transparency Board: live totals count up, LIVE badge, ledger rows pull focus | "Plus the council's finances, in real time…" |
| 24.3–28.8 s | Whip to the angled blue iPhone with the scanner UI warped onto its screen; *Present*; Offline → Syncing → Synced | "Officers scan attendance at events, even offline." |
| 28.8–33 s | "So everyone can see / where every peso goes." → light streak → *Payment confirmed* notification → dot | "So everyone can see where every peso goes." |
| 33–37.2 s | Seal and wordmark; "One Step Better Than Yesterday." | "Digital Transparency Board. One step better than yesterday." |
| 37.2–40 s | A circular wipe opens out of the seal into the spotlight credits (the three developers) | — |

The student "Juan Dela Cruz", all peso amounts and the ledger entries are **sample data for the video**.

## Rebuild

```sh
npm install
# voice-over (Kokoro, checked with Whisper): see ../../.claude/skills/ui-promo-motion/scripts/tts.py
python tts.py audio/lines.json audio/vo --voice af_heart --check
python audio/mix.py ../../.claude/skills/ui-promo-motion/scripts audio/vo build/mix.wav
ffmpeg -i build/mix.wav -af loudnorm=I=-14:TP=-1.5:LRA=11 build/mix-norm.wav
node ../../.claude/skills/ui-promo-motion/scripts/render.cjs index.html build/reel.mp4 --fps 30 --mb 4 --audio build/mix-norm.wav
```

Open `index.html` in a browser to preview it (`space` pauses, the arrow keys step frames, `?t=18` jumps to a time).
