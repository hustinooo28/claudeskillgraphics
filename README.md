# claudeskillgraphics

Claude Code skills for 3D, animation, and visual design, vendored under `.claude/skills/`.

| Skills | Source |
| --- | --- |
| `threejs-*` (animation, fundamentals, geometry, interaction, lighting, loaders, materials, postprocessing, shaders, textures) | [cloudai-x/threejs-skills](https://github.com/cloudai-x/threejs-skills) |
| `gsap-*` (core, frameworks, performance, plugins, react, scrolltrigger, timeline, utils) | [greensock/gsap-skills](https://github.com/greensock/gsap-skills) |
| `design-dna` | [zanwei/design-dna](https://github.com/zanwei/design-dna) |
| `motion-design` | [lottiefiles/motion-design-skill](https://github.com/lottiefiles/motion-design-skill) |
| `genjutsu` | [genjutsu.athevon.dev](https://genjutsu.athevon.dev) |
| `ui-promo-motion` | Original. Learned from nine reference promo videos: style guide, GSAP motion kit, a CSS 3D camera rig, an HTML → MP4 frame-by-frame renderer, and voice-over / music / SFX tools |

## Using them

- **In this repo:** open it with Claude Code and the skills load automatically.
- **In another project:** copy the folders you want into that project's `.claude/skills/`.
- **Everywhere on your machine:** copy them into `~/.claude/skills/`.

## Projects

- [`projects/lsync-promo`](projects/lsync-promo): a 48 s promo for the LSC Digital Transparency Board (LSynC)

## Rendering videos (`ui-promo-motion`)

```sh
cd .claude/skills/ui-promo-motion && npm install      # gsap + Inter, served locally while rendering
node scripts/render.cjs kit/template.html demo.mp4 --fps 30 --mb 4
```

Requires Node 18+, `ffmpeg`, and Playwright with Chromium (`npm i -g playwright && npx playwright install chromium`).

## Updating

For the third-party skills, re-run the installer from the repo root without `-g` and commit the result:

```sh
npx skills add cloudai-x/threejs-skills -a claude-code -y
npx skills add greensock/gsap-skills -a claude-code -y
npx skills add zanwei/design-dna -a claude-code -y
npx skills add lottiefiles/motion-design-skill -a claude-code -y
npx skills add https://genjutsu.athevon.dev -a claude-code -y
```

Skills run with full agent permissions — review changes before committing.
