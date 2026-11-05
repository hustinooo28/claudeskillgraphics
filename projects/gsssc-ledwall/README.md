# GSSSC LED wall loop: Mapping Research on Curriculum and Instruction Management in Teaching Mathematics

A 24-second seamless loop for the LED wall at the DSSC Graduate School Supreme Student Council session (November 7, 2026, 8:00 AM–12 NN, DSSC Mini Theater). It's built from the poster's own artwork: the background gradient, the faint campus photo and the red glow are pulled straight out of `GSSSC_2.svg`, and the seals out of `GSSSC_1.svg`. The text is live Montserrat, sized line by line to the poster's widths so the held frame matches the poster.

**File for the wall:** `GSSSC-LED-wall-loop-1080p.mp4` (1920×1080, 30 fps, H.264, silent). Set the player to loop. Frame 0 and the last frame are the same state, so there's no jump at the seam.

| Time | What happens |
|---|---|
| 0–2 s | A light flare sweeps the wall and the faint "research map" network fades up. Both seals spin in, each with a ring pulse. |
| 1.2–2 s | DAVAO DEL SUR STATE COLLEGE builds letter by letter from the centre, then the council line. |
| 2–3.5 s | The headline lands word by word out of blur, and a light sweep runs across it. |
| 3.6–5 s | Date, time and venue rise in, the dividers draw, and the audience line fades up. |
| 5–21 s | Full poster on hold for reading. The background keeps moving (drifting gradient, slow campus push-in, breathing red glow, network nodes, rising maths symbols). Light sweeps at 8.5, 13.5 and 18 s, seal pulses at 10.5 and 16 s, and the date line glows at 11.6 s. |
| 21.4–23 s | Content lifts out of focus in reverse order, and the wall breathes before the loop restarts. |

## Live playback

`index.html` also plays in a browser as a live loop: open it full screen on the LED wall's PC (F11). Space pauses, ←/→ step. It loads GSAP and Montserrat from jsDelivr, so the PC needs internet access, or run `npm install` first and use the MP4.

## Rebuild

```sh
npm install
node ../../.claude/skills/ui-promo-motion/scripts/render.cjs index.html build/GSSSC-LED-wall-loop-1080p.mp4 --fps 30 --mb 4 --crf 16
```

For a wall with a different pixel size (say 3840×1080 or 1536×640), change `--w/--h` in `index.html`, or ask for a re-layout. A non-16:9 wall needs the layout moved, not just scaled.

`LOOP` in `index.html` sets the loop length. Every ambient motion completes a whole number of cycles per loop, so it stays seamless at any length.
