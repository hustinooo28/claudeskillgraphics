# claudeskillgraphics

Claude Code skills for 3D, animation, and visual design, vendored under `.claude/skills/`.

| Skills | Source |
| --- | --- |
| `threejs-*` (animation, fundamentals, geometry, interaction, lighting, loaders, materials, postprocessing, shaders, textures) | [cloudai-x/threejs-skills](https://github.com/cloudai-x/threejs-skills) |
| `gsap-*` (core, frameworks, performance, plugins, react, scrolltrigger, timeline, utils) | [greensock/gsap-skills](https://github.com/greensock/gsap-skills) |
| `design-dna` | [zanwei/design-dna](https://github.com/zanwei/design-dna) |
| `motion-design` | [lottiefiles/motion-design-skill](https://github.com/lottiefiles/motion-design-skill) |
| `genjutsu` | [genjutsu.athevon.dev](https://genjutsu.athevon.dev) |

## Using them

- **In this repo:** open it with Claude Code and the skills load automatically.
- **In another project:** copy the folders you want into that project's `.claude/skills/`.
- **Everywhere on your machine:** copy them into `~/.claude/skills/`.

## Updating

From the repo root, re-run the installer without `-g` and commit the result:

```sh
npx skills add cloudai-x/threejs-skills -a claude-code -y
npx skills add greensock/gsap-skills -a claude-code -y
npx skills add zanwei/design-dna -a claude-code -y
npx skills add lottiefiles/motion-design-skill -a claude-code -y
npx skills add https://genjutsu.athevon.dev -a claude-code -y
```

Skills run with full agent permissions — review changes before committing.
