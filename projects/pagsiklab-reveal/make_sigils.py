"""Medallion faces: each house sigil set into a round bronze coin face (1024 px, RGB)."""
import numpy as np, cv2

N = 1024
yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
R = np.sqrt((xx - N / 2) ** 2 + (yy - N / 2) ** 2) / (N / 2)

# (file, mode, crop params, crush (lo, span)) -- crops are in the source image's pixels
SPECS = {   # the council's emblem set (cut out by cut_emblems.py); Baratheon keeps the earlier stag until its emblem arrives
    'stark': ('../emblems/stark.png', 'alpha', (0, 0, 522, 365), None),
    'baratheon': ('28.webp', 'rect', (232, 345, 256, 480), (0.22, 0.2)),
    'tyrell': ('../emblems/tyrell.png', 'alpha', (0, 0, 345, 343), None),
    'martell': ('../emblems/martell.png', 'alpha', (0, 0, 237, 255), None),
    'lannister': ('../emblems/lannister.png', 'alpha', (0, 0, 443, 558), None),
    'targaryen': ('../emblems/targaryen.png', 'alpha', (0, 0, 464, 499), None),
    'campus': ('../lsc-seal.webp', 'disc', (1000, 1000, 985), None),     # the Local Student Council seal
}


def face_base():
    """dark bronze coin: radial falloff, brushed grain, engraved rings"""
    r = np.random.default_rng(3)
    grain = cv2.GaussianBlur(r.standard_normal((N, N)).astype(np.float32), (0, 0), 1.2)
    grain = cv2.blur(grain, (1, 31)) * 0.6 + grain * 0.4
    base = np.float32([30, 42, 58]) * (1.25 - 0.45 * R)[..., None] + grain[..., None] * 6
    for rr, w, amp in ((0.965, 0.012, 70), (0.90, 0.006, 45), (0.885, 0.004, -25)):
        ring = np.exp(-((R - rr) / w) ** 2)
        base += ring[..., None] * np.float32([60, 110, 150]) * amp / 70
    return base


def sigil_layer(spec):
    f, mode, p, crush = spec
    im = cv2.imread('assets/sigils/' + f, cv2.IMREAD_UNCHANGED).astype(np.float32)
    if im.shape[2] == 3:
        im = np.dstack([im, np.full(im.shape[:2], 255, np.float32)])
    if mode == 'disc':
        cx, cy, r = p
        x, y, w, h = cx - r, cy - r, 2 * r, 2 * r
    else:
        x, y, w, h = p
    sub = im[int(y):int(y + h), int(x):int(x + w)]
    hh, ww = sub.shape[:2]
    gy, gx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    if mode == 'alpha':
        a = sub[..., 3] / 255
    elif mode == 'disc':
        d = np.sqrt((gx - ww / 2) ** 2 + (gy - hh / 2) ** 2) / (ww / 2)
        a = np.clip((1 - d) / 0.02, 0, 1)
    elif mode == 'ellipse':
        d = np.sqrt(((gx - ww / 2) / (ww / 2)) ** 2 + ((gy - hh / 2) / (hh / 2)) ** 2)
        a = np.clip((1 - d) / 0.4, 0, 1) ** 1.5
    else:
        fx = np.clip(np.minimum(gx, ww - gx) / (ww * 0.12), 0, 1)
        fy = np.clip(np.minimum(gy, hh - gy) / (hh * 0.12), 0, 1)
        a = (fx * fy) ** 1.2
    rgb = sub[..., :3]
    if crush:
        lo, span = crush
        lum = rgb.mean(2) / 255
        a = a * np.clip((lum - lo) / span, 0, 1) ** 0.7       # photo background drops out
    return rgb, a, mode


for key, spec in SPECS.items():
    out = face_base()
    rgb, a, mode = sigil_layer(spec)
    if key == 'baratheon' and spec[0] == '28.webp':
        rgb = np.clip(rgb * 1.9, 0, 255)          # the stag is a thin gold line drawing
    if key == 'tyrell' and spec[0] == '25.webp':
        a = a * np.clip((rgb.mean(2) - 60) / 120, 0, 1) ** 0.3 * np.clip((235 - rgb.mean(2)) / 40, 0, 1)
    hh, ww = a.shape
    fit = (0.86 if mode == 'disc' else 0.80 if mode == 'alpha' else 0.70) * N
    s = fit / max(hh, ww)
    rgb = cv2.resize(rgb, (int(ww * s), int(hh * s)), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    a = cv2.resize(a, (int(ww * s), int(hh * s)), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    h2, w2 = a.shape
    y0, x0 = (N - h2) // 2, (N - w2) // 2
    full_a = np.zeros((N, N), np.float32)
    full_rgb = np.zeros((N, N, 3), np.float32)
    full_a[y0:y0 + h2, x0:x0 + w2] = a
    full_rgb[y0:y0 + h2, x0:x0 + w2] = rgb
    # embossed relief: a soft shadow under the sigil
    sh = cv2.GaussianBlur(np.roll(np.roll(full_a, 10, 0), 6, 1), (0, 0), 9)
    out *= (1 - 0.6 * sh)[..., None]
    out = out * (1 - full_a[..., None]) + full_rgb * full_a[..., None]
    out[R > 1.0] = (30, 42, 58)
    cv2.imwrite(f'build/tex/sigil_{key}.png', np.clip(out, 0, 255).astype(np.uint8))
    print(key, 'ok')
cv2.imwrite('build/tex/sigils_preview.jpg',
            np.hstack([cv2.resize(cv2.imread(f'build/tex/sigil_{k}.png'), (256, 256)) for k in SPECS]))


# ---------------- the campus sign band (as on the real building) ----------------
from PIL import Image, ImageDraw, ImageFont
W_, H_ = 2600, 360
sign = Image.new('RGB', (W_, H_), (24, 70, 170))
d = ImageDraw.Draw(sign)
big = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 100)
small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 80)
for text, font, y in (('DAVAO DEL SUR STATE COLLEGE', big, 55), ('STA. CRUZ EXTENSION CAMPUS', small, 205)):
    tw = d.textlength(text, font=font)
    d.text(((W_ - tw) / 2, y), text, font=font, fill=(245, 247, 250))
seal = Image.open('assets/lsc-seal.webp').convert('RGB').resize((250, 250), Image.LANCZOS)
mask = Image.new('L', (250, 250), 0)
ImageDraw.Draw(mask).ellipse((0, 0, 249, 249), fill=255)
for x in (55, W_ - 305):
    sign.paste(seal, (x, 55), mask)
sign.save('build/tex/campus_sign.png')
print('sign ok')
