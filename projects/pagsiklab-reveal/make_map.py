"""Paint the realm: colour texture, heightmap and tree positions."""
import numpy as np, cv2, json
from PIL import Image, ImageDraw, ImageFont
from realm import HOUSES, CAMPUS

TS = 4096          # colour texture size
HS = 1024          # heightmap size
rng = np.random.default_rng(7)


def fbm(n, seed, octaves=(4, 8, 16, 32, 64, 128), gain=0.55):
    r = np.random.default_rng(seed)
    acc, amp, tot = np.zeros((n, n), np.float32), 1.0, 0.0
    for o in octaves:
        g = r.random((o + 3, o + 3)).astype(np.float32)
        acc += cv2.resize(g, (n, n), interpolation=cv2.INTER_CUBIC) * amp
        tot += amp
        amp *= gain
    acc /= tot
    return (acc - acc.min()) / (acc.max() - acc.min())


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def land_field(n):
    v, u = np.mgrid[0:n, 0:n].astype(np.float32) / n
    field = np.full((n, n), -1.0, np.float32)
    spine = [(0.45, 0.02, 0.15), (0.47, 0.18, 0.18), (0.42, 0.34, 0.17), (0.36, 0.50, 0.165),
             (0.38, 0.66, 0.19), (0.47, 0.78, 0.15), (0.60, 0.85, 0.085), (0.74, 0.875, 0.075)]
    for (x0, y0, w0), (x1, y1, w1) in zip(spine[:-1], spine[1:]):
        for t in np.linspace(0, 1, 24):
            cx, cy, w = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, w0 + (w1 - w0) * t
            field = np.maximum(field, 1 - np.sqrt((u - cx) ** 2 + (v - cy) ** 2) / w)
    for cx, cy, r in ((0.57, 0.60, 0.11), (0.835, 0.43, 0.045), (0.24, 0.53, 0.05)):   # stormlands, Dragonstone, the Rock
        field = np.maximum(field, 1 - np.sqrt((u - cx) ** 2 + (v - cy) ** 2) / r)
    # ragged coast (extra roughness on the small island)
    isl = np.exp(-(((u - 0.835) ** 2 + (v - 0.43) ** 2) / 0.006))
    field += (fbm(n, 13, (16, 32, 64)) - 0.5) * 1.6 * isl
    field += (fbm(n, 11) - 0.5) * 0.55 + (fbm(n, 12, (64, 128, 256)) - 0.5) * 0.18
    return field, u, v


# ---------------- heightmap ----------------
field, u, v = land_field(HS)
land = smooth(0.0, 0.06, field)
ridge = 1 - np.abs(fbm(HS, 21, (6, 12, 24, 48, 96)) * 2 - 1)
ridge = ridge ** 3
mount_mask = (smooth(0.25, 0.6, field) * (smooth(0.55, 0.85, fbm(HS, 22, (3, 6, 12))) + 0.35 * smooth(0.36, 0.24, v)))
h = land * 0.22 + land * mount_mask * ridge * 1.35 + land * fbm(HS, 23) * 0.06
# flatten a plateau under every seat so the castles sit level
for hs in HOUSES + [CAMPUS]:
    cu, cv = hs['pos']
    d = np.sqrt((u - cu) ** 2 + (v - cv) ** 2)
    k = smooth(0.07, 0.025, d)
    h = h * (1 - k) + 0.24 * k
np.save('build/tex/height.npy', h.astype(np.float32))

# trees: forests in the north and the Reach, none on mountains, coast or seats
forest = fbm(HS, 31, (5, 10, 20, 40))
trees = []
for _ in range(60000):
    x, y = rng.random(), rng.random()
    i, j = int(y * HS), int(x * HS)
    if field[i, j] < 0.18 or mount_mask[i, j] * ridge[i, j] > 0.15:
        continue
    wood = forest[i, j] > (0.52 if (y < 0.32 or (0.6 < y < 0.8 and x < 0.5)) else 0.78)
    if not wood or y > 0.8:
        continue
    if min(np.hypot(x - hs['pos'][0], y - hs['pos'][1]) for hs in HOUSES + [CAMPUS]) < 0.055:
        continue
    trees.append((x, y, float(h[i, j]), 'snow' if y < 0.3 else 'green'))
    if len(trees) >= 5200:
        break
json.dump(trees, open('build/tex/trees.json', 'w'))
print('trees', len(trees))

# ---------------- colour texture ----------------
field, u, v = land_field(TS)
land = smooth(0.0, 0.02, field)
H = cv2.resize(h, (TS, TS), interpolation=cv2.INTER_CUBIC)
paper = fbm(TS, 41, (8, 16, 32, 64, 128, 256)) * 0.6 + fbm(TS, 42, (256, 512, 1024)) * 0.4

def mix(a, b, t):
    return a * (1 - t[..., None]) + np.float32(b) * t[..., None]

# biomes (RGB 0..1)
col = np.zeros((TS, TS, 3), np.float32) + np.float32([0.80, 0.77, 0.70])            # riverlands parchment
col = mix(col, [0.90, 0.92, 0.95], smooth(0.36, 0.26, v))                         # the north: snow
col = mix(col, [0.66, 0.58, 0.48], smooth(0.32, 0.22, u) * smooth(0.40, 0.46, v) * smooth(0.62, 0.56, v))   # westerlands stone
col = mix(col, [0.60, 0.66, 0.42], smooth(0.58, 0.66, v) * smooth(0.82, 0.76, v) * smooth(0.55, 0.45, u))  # the Reach
col = mix(col, [0.60, 0.64, 0.62], smooth(0.50, 0.56, u) * smooth(0.50, 0.56, v) * smooth(0.74, 0.68, v))  # stormlands
col = mix(col, [0.86, 0.70, 0.46], smooth(0.79, 0.85, v))                         # Dorne sand
col = mix(col, [0.34, 0.30, 0.30], smooth(0.07, 0.04, np.sqrt((u - 0.835) ** 2 + (v - 0.43) ** 2)))  # Dragonstone basalt
# relief shading from the heightmap
gy, gx = np.gradient(cv2.GaussianBlur(H, (0, 0), 3))
shade = np.clip(1 + (-gx + gy) * 200, 0.65, 1.3)
col *= shade[..., None]
col = mix(col, [0.97, 0.97, 0.98], smooth(0.45, 0.85, H) * 0.8)                   # snowy peaks
col *= (0.9 + 0.2 * paper)[..., None]
# sea: deep slate with engraved wave lines
sea = np.float32([0.20, 0.27, 0.32]) * (0.85 + 0.3 * paper)[..., None]
waves = (np.sin((v * 900 + fbm(TS, 51, (6, 12, 24)) * 60)) > 0.92).astype(np.float32)
sea = sea * (1 - 0.25 * waves[..., None]) + np.float32([0.42, 0.50, 0.55]) * 0.25 * waves[..., None]
shallow = smooth(-0.25, 0.0, field)
sea = mix(sea, [0.33, 0.43, 0.47], shallow * 0.7)
img = col * land[..., None] + sea * (1 - land[..., None])
# ink coastline (double line, like an engraved map)
edge = np.abs(cv2.Laplacian((field > 0).astype(np.float32), cv2.CV_32F))
ink = np.clip(cv2.GaussianBlur(cv2.dilate(edge, np.ones((5, 5), np.uint8)), (0, 0), 1.2) * 1.8, 0, 1)
ring = (np.abs(field + 0.06) < 0.004).astype(np.float32)
ink = np.maximum(ink, cv2.GaussianBlur(ring, (0, 0), 1.0) * 0.5)
img = mix(img, [0.17, 0.13, 0.10], ink * 0.85)
# the outer margin fades into one flat sea colour, exactly the colour of the open-sea plane in the scene
SEA_EDGE = np.float32([0.2534, 0.3205, 0.3685])
edge_d = np.minimum(np.minimum(u, 1 - u), np.minimum(v, 1 - v))
ef = smooth(0.0, 0.09, edge_d)[..., None]
img = img * ef + SEA_EDGE * (1 - ef)
out = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
d = ImageDraw.Draw(out)
f = ImageFont.truetype('assets/fonts/Cinzel.ttf', 64)
f.set_variation_by_axes([700])
fs = ImageFont.truetype('assets/fonts/Cinzel.ttf', 40)
fs.set_variation_by_axes([600])
for hs in HOUSES + [CAMPUS]:
    x, y = hs['pos'][0] * TS, hs['pos'][1] * TS
    label = hs['seat']
    tw = d.textlength(label, font=f)
    ty = y + 175
    d.text((x - tw / 2 + 3, ty + 3), label, font=f, fill=(255, 250, 240, 120))
    d.text((x - tw / 2, ty), label, font=f, fill=(48, 34, 24))
# region names, faint and spaced like an old map
for name, x, y in (('THE NORTH', 0.47, 0.30), ('THE WESTERLANDS', 0.23, 0.44), ('THE REACH', 0.36, 0.79),
                   ('THE STORMLANDS', 0.60, 0.70), ('DORNE', 0.63, 0.93), ('THE NARROW SEA', 0.80, 0.62),
                   ('THE SUNSET SEA', 0.08, 0.66)):
    s = ' '.join(name)
    tw = d.textlength(s, font=fs)
    d.text((x * TS - tw / 2, y * TS), s, font=fs, fill=(70, 58, 46) if 'SEA' not in name else (150, 165, 172))
out.save('build/tex/color.png')
Image.fromarray((np.clip(h / h.max(), 0, 1) * 255).astype(np.uint8)).save('build/tex/height_preview.png')
out.resize((1024, 1024), Image.LANCZOS).save('build/tex/color_preview.jpg', quality=90)
print('done')
