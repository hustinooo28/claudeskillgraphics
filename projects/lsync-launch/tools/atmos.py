"""Pre-rendered light assets (blurred PNGs) so the composition never runs big CSS blurs at render time."""
import pathlib
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

OUT = pathlib.Path(__file__).resolve().parent.parent / "assets/fx"
rng = np.random.default_rng(11)

def save(rgb, alpha, name):
    a = np.clip(alpha, 0, 1)
    img = np.dstack([np.clip(rgb[..., i], 0, 255) for i in range(3)] + [a * 255]).astype(np.uint8)
    Image.fromarray(img, "RGBA").save(OUT / name, optimize=True)

def curtain(w, h, core, hot, name, cols=46):
    """Light falling from the top through vertical slats: streaky, soft, brightest top-centre-left."""
    x = np.linspace(0, 1, w)[None, :]; y = np.linspace(0, 1, h)[:, None]
    streaks = np.zeros(w)
    for c in rng.uniform(0, 1, cols):
        streaks += rng.uniform(0.4, 1.0) * np.exp(-((np.linspace(0, 1, w) - c) ** 2) / (2 * rng.uniform(0.004, 0.018) ** 2))
    streaks = streaks / streaks.max()
    across = np.exp(-((x - 0.42) ** 2) / (2 * 0.26 ** 2))          # brightest left of centre
    down = np.exp(-(y / 0.42) ** 1.6)                              # falls off downward
    inten = (0.55 + 0.45 * streaks[None, :]) * across * down
    inten = gaussian_filter(inten, sigma=(h * 0.012, w * 0.006))
    inten /= inten.max()
    t = inten[..., None]
    rgb = np.array(core)[None, None, :] * (1 - t ** 2) + np.array(hot)[None, None, :] * t ** 2
    save(rgb, inten ** 1.15, name)

def blob(size, color, name, falloff=2.2):
    y, x = np.mgrid[-1:1:size * 1j, -1:1:size * 1j]
    r = np.sqrt(x ** 2 + y ** 2)
    a = np.clip(1 - r, 0, 1) ** falloff
    rgb = np.ones((size, size, 3)) * np.array(color)[None, None, :]
    save(rgb, a, name)

curtain(2400, 1500, (20, 60, 230), (140, 190, 255), "curtain-blue.png")
curtain(2400, 1500, (230, 150, 10), (255, 236, 150), "curtain-yellow.png", cols=38)
blob(800, (60, 120, 255), "glow-blue.png")
blob(800, (255, 200, 40), "glow-yellow.png")
blob(800, (255, 255, 255), "glow-white.png", falloff=3)
print("ok", sorted(p.name for p in OUT.iterdir()))
