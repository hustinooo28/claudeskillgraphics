"""Composite the final film: 2D openers, graded 3D with atmosphere and particles, lower thirds, finale.
Usage: python3 composite.py build/film.mp4 [frame,frame,...  -> writes PNG stills instead]"""
import sys, os, math, subprocess
import cv2, numpy as np
from multiprocessing import Pool
import realm as R

FPS, W, H = R.FPS, 1920, 1080
NF = int(round((R.END + R.ROLL) * FPS)) + R.LEAD_F   # the film, then the closing line
F = lambda t: int(round(t * FPS))
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


def clamp(x): return min(max(x, 0.0), 1.0)
def prog(t, s, d): return clamp((t - s) / d)
def sm(x): x = clamp(x); return x * x * (3 - 2 * x)
def oc(x): x = clamp(x); return 1 - (1 - x) ** 3


# ---------------- cached layers ----------------
_C = {}


def txt(name):
    if name not in _C:
        im = cv2.imread(f'build/titles/{name}.png', cv2.IMREAD_UNCHANGED).astype(np.float32)
        im = cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA)
        a = im[..., 3:] / 255
        _C[name] = np.dstack([im[..., :3] * a, a[..., 0]])
    return _C[name]


def rgba_img(path, width):
    k = (path, width)
    if k not in _C:
        im = cv2.imread(path, cv2.IMREAD_UNCHANGED).astype(np.float32)
        if im.shape[2] == 3:
            im = np.dstack([im, np.full(im.shape[:2], 255, np.float32)])
        s = width / im.shape[1]
        im = cv2.resize(im, (width, int(im.shape[0] * s)), interpolation=cv2.INTER_AREA)
        a = im[..., 3:] / 255
        _C[k] = np.dstack([im[..., :3] * a, a[..., 0]])
    return _C[k]


def icon(key, size=92):
    k = ('icon', key, size)
    if k not in _C:
        im = cv2.resize(cv2.imread(f'build/tex/sigil_{key}.png').astype(np.float32), (size, size), interpolation=cv2.INTER_AREA)
        g = np.mgrid[0:size, 0:size].astype(np.float32)
        d = np.sqrt((g[0] - size / 2 + 0.5) ** 2 + (g[1] - size / 2 + 0.5) ** 2)
        a = np.clip(size / 2 - d, 0, 1)
        ring = np.clip(1 - np.abs(d - (size / 2 - 1.5)) / 1.5, 0, 1)
        im = im * (1 - ring[..., None]) + ring[..., None] * np.float32([110, 185, 230])
        _C[k] = np.dstack([im * a[..., None], a])
    return _C[k]


def over(c, pm, op=1.0, x0=0, y0=0):
    """premultiplied layer onto canvas, optional offset (clipped)"""
    if op <= 0.002:
        return c
    h, w = pm.shape[:2]
    X0, Y0, X1, Y1 = max(x0, 0), max(y0, 0), min(x0 + w, W), min(y0 + h, H)
    if X1 <= X0 or Y1 <= Y0:
        return c
    sub = pm[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    roi = c[Y0:Y1, X0:X1]
    roi *= 1 - sub[..., 3:] * op
    roi += sub[..., :3] * op
    return c


def shift(pm, dx, dy=0.0):
    return cv2.warpAffine(pm, np.float32([[1, 0, dx], [0, 1, dy]]), (W, H))


def scale_about(pm, s, cx=W / 2, cy=H / 2):
    M = cv2.getRotationMatrix2D((cx, cy), 0, s)
    return cv2.warpAffine(pm, M, (W, H))


# ---------------- grading ----------------
# (sat, shadow tint BGR, highlight tint BGR, contrast, lift)
GRADES = {   # (sat, shadow tint BGR, highlight tint BGR, contrast, lift)  -- darker, candlelit
    'neutral': (0.85, (1.10, 1.00, 0.92), (0.88, 0.98, 1.08), 1.18, -6),
    'fire': (0.95, (1.00, 0.90, 0.95), (0.75, 0.92, 1.20), 1.24, -10),
    'gold': (0.9, (1.06, 0.98, 0.94), (0.78, 0.96, 1.15), 1.2, -8),
    'green': (0.9, (1.04, 1.02, 0.94), (0.84, 1.00, 1.08), 1.16, -6),
    'cold': (0.55, (1.18, 1.05, 0.94), (1.06, 1.03, 1.00), 1.04, -6),   # flat overcast winter light
    'sun': (0.8, (1.06, 0.98, 0.92), (0.82, 0.97, 1.12), 1.10, 2),      # bleached, high exposure
    'storm': (0.6, (1.14, 1.05, 0.95), (1.00, 1.01, 1.00), 1.26, -8),
    'campus': (0.92, (1.06, 1.00, 0.94), (0.84, 0.97, 1.10), 1.14, -5),
}
FOG = {  # far fog / sky colour and a darker top (BGR)
    'neutral': ((62, 52, 44), (34, 28, 24)), 'fire': ((40, 46, 72), (14, 14, 26)), 'gold': ((52, 70, 92), (22, 26, 36)),
    'green': ((60, 72, 70), (28, 32, 30)), 'cold': ((92, 84, 78), (46, 40, 34)), 'sun': ((60, 86, 108), (28, 36, 46)),
    'storm': ((58, 56, 52), (26, 24, 22)), 'campus': ((70, 82, 92), (34, 38, 42)),
}
RAYS = {  # god-ray source (x, y), colour BGR, strength
    'neutral': ((1500, -250), (200, 225, 245), 0.35), 'fire': ((1600, -200), (90, 150, 255), 0.45),
    'gold': ((1700, -150), (110, 200, 255), 0.6), 'green': ((300, -250), (170, 235, 255), 0.5),
    'cold': ((400, -300), (255, 240, 225), 0.4), 'sun': ((1500, -150), (120, 210, 255), 0.7),
    'storm': ((900, -400), (220, 225, 225), 0.25), 'campus': ((1500, -250), (170, 225, 255), 0.6),
}
ATMOS = {   # fog reach (x near distance), light-shaft gain, sweeping cloud-shadow strength
    'neutral': (1.4, 1.0, 0.30), 'fire': (1.5, 0.7, 0.25), 'gold': (1.6, 1.7, 0.30), 'green': (1.5, 1.5, 0.30),
    'cold': (0.8, 0.5, 0.45), 'sun': (1.8, 1.4, 0.20), 'storm': (1.0, 0.4, 0.40), 'campus': (1.5, 1.6, 0.30),
}
PARTS = {'neutral': 'dust', 'fire': 'embers', 'gold': 'golddust', 'green': 'petals', 'cold': 'snow', 'sun': 'dust',
         'storm': 'rain', 'campus': 'dust'}


def grade(c, g):
    sat, sh, hi, con, lift = g
    x = np.clip(c / 255, 0, 1)
    lum = x[..., 0:1] * 0.114 + x[..., 1:2] * 0.587 + x[..., 2:3] * 0.299
    x = lum + (x - lum) * sat
    w = np.clip(lum * 1.4 - 0.2, 0, 1)
    x = x * (np.float32(sh) * (1 - w) + np.float32(hi) * w)
    x = 0.5 + (x - 0.5) * con
    x = np.clip(x, 0, 1)
    x = x * x * (3 - 2 * x) * 0.3 + x * 0.7
    return x * (255 - lift) + lift


def lerp_tuple(a, b, u):
    return tuple(lerp_tuple(x, y, u) if isinstance(x, tuple) else x + (y - x) * u for x, y in zip(a, b))


def segment(t):
    """which look applies at time t, with a blend toward the next one during flights"""
    keys = [h['grade'] for h in R.HOUSES] + ['campus']
    if t < R.HOUSE_START:
        u = sm(prog(t, R.HOUSE_START - 1.3, 1.3))
        return 'neutral', keys[0], u
    if t < R.OVERVIEW[0]:
        i = min(int((t - R.HOUSE_START) // R.HOUSE_LEN), 6)
        s = R.house_window(i)[0] if i < 6 else R.CAMPUS_WIN[0]
        lt = t - s
        nxt = keys[i + 1] if i < 6 else 'neutral'
        u = sm(prog(lt, R.HOUSE_LEN - 1.3, 1.3))
        return keys[i], nxt, u
    return 'neutral', 'neutral', 0.0


# ---------------- particles ----------------
_ld = np.zeros((H, W), np.float32)
for _x, _y, _r in np.random.default_rng(71).random((26, 3)):
    cv2.circle(_ld, (int(_x * W), int(_y * H)), int(6 + 26 * _r), 1.0, -1, cv2.LINE_AA)
LENS_DUST = cv2.GaussianBlur(_ld, (0, 0), 6)[..., None]
RNG = np.random.default_rng(9)
P = RNG.random((420, 6)).astype(np.float32)


def particles(kind, t, strength):
    """additive (or over) particle layer at half resolution -> (layer BGR, mode)"""
    if strength <= 0.01:
        return None, None
    h2, w2 = H // 2, W // 2
    lay = np.zeros((h2, w2, 3), np.float32)
    n = {'snow': 420, 'rain': 260, 'petals': 70, 'embers': 160, 'dust': 70, 'golddust': 150}[kind]
    for k in range(n):
        x0, y0, z, ph, a, b = P[k]
        z = 0.15 + 0.85 * z ** 2                            # depth: near particles are big and fast
        if kind == 'snow':
            y = (y0 * (h2 + 40) + (40 + 120 * z) * t) % (h2 + 40) - 20
            x = (x0 * w2 + 14 * math.sin(t * 0.7 + ph * 6) - (60 + 160 * z) * t) % w2
            r = 0.6 + 3.0 * z ** 2
            L = 2 + 9 * z
            cv2.line(lay, (int(x), int(y)), (int(x + L), int(y - L * 0.35)), (230, 232, 235), max(1, int(r)), cv2.LINE_AA)
        elif kind == 'rain':
            y = (y0 * (h2 + 80) + (300 + 500 * z) * t) % (h2 + 80) - 40
            x = (x0 * w2 - 90 * t) % w2
            L = 8 + 26 * z
            cv2.line(lay, (int(x), int(y)), (int(x - L * 0.25), int(y - L)), (200, 205, 205), 1, cv2.LINE_AA)
        elif kind == 'petals':
            y = (y0 * (h2 + 40) + (10 + 30 * z) * t) % (h2 + 40) - 20
            x = (x0 * w2 + 60 * t * (0.4 + z) + 25 * math.sin(t * 1.3 + ph * 6)) % w2
            ang = (t * (60 + 120 * a) + ph * 360) % 360
            ax = 1.5 + 4 * z
            cv2.ellipse(lay, (int(x), int(y)), (int(ax), max(1, int(ax * 0.45 * abs(math.cos(t * 2 + ph * 9)) + 0.5))),
                        float(ang), 0, 360, (float(70 + 40 * b), float(60 + 30 * a), float(200 + 40 * b)), -1, cv2.LINE_AA)
        elif kind == 'embers':
            y = h2 + 20 - ((y0 * (h2 + 40) + (25 + 70 * z) * t) % (h2 + 40))
            x = (x0 * w2 + 22 * math.sin(t * (0.6 + z) + ph * 6)) % w2
            fl = 0.5 + 0.5 * math.sin(t * 9 * (0.5 + z) + ph * 20)
            cv2.circle(lay, (int(x), int(y)), max(1, int(0.5 + 1.8 * z)), (40 * fl, 140 * fl, 255 * fl), -1, cv2.LINE_AA)
        else:  # dust / golddust: slow floating motes
            y = (y0 * h2 + 8 * math.sin(t * 0.5 + ph * 6) - 6 * t * (0.3 + z)) % h2
            x = (x0 * w2 + 10 * t * (a - 0.5) + 12 * math.cos(t * 0.4 + ph * 5)) % w2
            col = (90, 160, 200) if kind == 'golddust' else (110, 130, 150)
            tw = 0.45 + 0.55 * math.sin(t * (1 + 2 * a) + ph * 12) ** 2
            cv2.circle(lay, (int(x), int(y)), max(1, int(0.5 + 1.6 * z)), tuple(v * tw for v in col), -1, cv2.LINE_AA)
    blur = 0.8 if kind not in ('snow', 'petals') else 0.6
    lay = cv2.GaussianBlur(lay, (0, 0), blur)
    if kind in ('embers', 'dust', 'golddust'):
        lay = lay + cv2.GaussianBlur(lay, (0, 0), 5) * 1.4
    lay = cv2.resize(lay, (W, H), interpolation=cv2.INTER_LINEAR) * strength
    mode = 'add' if kind in ('embers', 'dust', 'golddust') else 'screen'
    return lay, mode


def apply_particles(c, kind, t, s):
    lay, mode = particles(kind, t, s)
    if lay is None:
        return c
    if mode == 'add':
        return c + lay * (0.9 if kind != 'golddust' else 1.1)
    return 255 - (255 - c) * (1 - np.clip(lay / 255, 0, 1) * (0.85 if kind != 'rain' else 0.45))


# ---------------- 3D frame treatment ----------------
WORLD_BG = np.float32([63, 56, 52])        # Workbench world colour (BGR, sRGB)
VIG = (np.clip(1 - 0.7 * (((xx - W / 2) / (W * 0.66)) ** 2 + ((yy - H / 2) / (H * 0.74)) ** 2), 0.15, 1) ** 1.3)[..., None]


SHAFT_NOISE = np.random.default_rng(12).random(720).astype(np.float32)


def god_rays(c, src, col, strength, t=0.0):
    """soft light shafts falling from an off-screen source; they breathe slowly"""
    q = 4
    gx = (xx[::q, ::q] - src[0])
    gy = (yy[::q, ::q] - src[1])
    ang = (np.degrees(np.arctan2(gy, gx)) * 1.6 + t * 2) % 720
    i0 = ang.astype(np.int32) % 720
    fr = ang - np.floor(ang)
    n = SHAFT_NOISE[i0] * (1 - fr) + SHAFT_NOISE[(i0 + 1) % 720] * fr
    n = cv2.GaussianBlur(n, (0, 0), 4)
    dist = np.sqrt(gx ** 2 + gy ** 2)
    fall = np.exp(-dist / 1100.0)
    shafts = np.clip(n - 0.42, 0, None) ** 1.3 * fall * 1.2
    shafts = cv2.resize(shafts, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
    return c + shafts * np.float32(col) * strength


def bloom(c, amt=0.35):
    q = 4
    small = cv2.resize(np.clip(c - 175, 0, None), (W // q, H // q), interpolation=cv2.INTER_AREA)
    b = cv2.GaussianBlur(small, (0, 0), 6) + cv2.GaussianBlur(small, (0, 0), 18)
    return c + cv2.resize(b, (W, H)) * amt


def fbm2(n, seed, oct=(3, 6, 12, 24)):
    r = np.random.default_rng(seed)
    acc = np.zeros((n, n * 2), np.float32)
    amp = 1
    for o in oct:
        acc += cv2.resize(r.random((o + 2, o * 2 + 2)).astype(np.float32), (n * 2, n), interpolation=cv2.INTER_CUBIC) * amp
        amp *= 0.5
    return (acc - acc.min()) / (acc.max() - acc.min())


CLOUD = fbm2(540, 4)
CLOUD_BIG = cv2.resize(fbm2(270, 6, (2, 4, 8, 16, 32)), (W * 2, H * 2), interpolation=cv2.INTER_CUBIC)


_m = cv2.resize(fbm2(270, 21, (2, 4, 8, 16)), (W * 2, H), interpolation=cv2.INTER_CUBIC)
MIST = np.hstack([_m, _m[:, ::-1]])          # mirrored so it tiles without a seam
_c = CLOUD_BIG[::2, ::2]
_c = np.vstack([np.hstack([_c, _c[:, ::-1]]), np.hstack([_c[::-1], _c[::-1, ::-1]])])
CSHADOW = np.vstack([np.hstack([_c, _c]), np.hstack([_c, _c])])   # mirror-tiled: continuous for any window


SRC3D = os.environ.get('SRC3D', 'build/v6')


HORIZON = {}                                                      # build/horizon.json, written by horizon.py
if os.path.exists('build/horizon.json'):
    import json
    HORIZON = json.load(open('build/horizon.json'))


def sky_matte(raw, dep, r=4, eps=2e-3):
    """Soft sky matte: the depth pass is one sample per pixel, so its sky test is aliased on
    silhouettes and dithers under motion blur. A guided filter fits it to the beauty pass's own
    edges, which are antialiased and already hold the blur."""
    I = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    p = (dep > 65535 * 149 / 150).astype(np.float32)
    box = lambda x: cv2.boxFilter(x, -1, (2 * r + 1, 2 * r + 1))
    mI, mp = box(I), box(p)
    a = (box(I * p) - mI * mp) / (box(I * I) - mI * mI + eps)
    b = mp - a * mI
    return np.clip(box(a) * I + box(b), 0, 1)


def treat3d(fi, t):
    raw = cv2.imread(f'{SRC3D}/frames/{fi:05d}.png')
    dep = cv2.imread(f'{SRC3D}/depth/{fi:05d}.png', cv2.IMREAD_UNCHANGED)
    if raw is None or dep is None:
        raise FileNotFoundError(fi)
    c = raw.astype(np.float32)
    sky = sky_matte(raw, dep)
    if c.shape[1] != W:                                           # 720p Cycles render -> 1080p, then a light unsharp mask
        c = cv2.resize(c, (W, H), interpolation=cv2.INTER_CUBIC)
        c = c + (c - cv2.GaussianBlur(c, (0, 0), 1.6)) * 0.45
        dep = cv2.resize(dep, (W, H), interpolation=cv2.INTER_NEAREST)
        sky = cv2.resize(sky, (W, H), interpolation=cv2.INTER_LINEAR)
    dist = dep.astype(np.float32) / 65535 * 150.0                 # scene units; sky = 150
    ga, gb, u = segment(t)
    g = lerp_tuple(GRADES[ga], GRADES[gb], u)
    far, top = lerp_tuple(FOG[ga], FOG[gb], u)
    c = grade(c, g)
    # atmospheric perspective relative to what we're looking at: the subject stays clear,
    # distance thickens into fog, and the horizon and the map's edges dissolve completely
    ground = dist[dist < 149]
    near = float(np.percentile(ground, 30)) if ground.size else 20.0
    if t < R.HOUSE_START:                                         # the low run hugs the ground: keep the near hills clear
        near = max(near, 5.0 * sm(prog(t, R.CLOUD_BREAK - 1.0, 1.0)) + near * (1 - sm(prog(t, R.CLOUD_BREAK - 1.0, 1.0))))
    reach, shaft_gain, shadow_k = lerp_tuple(ATMOS[ga], ATMOS[gb], u)
    dg = np.where(dist > 149, cv2.erode(dist, np.ones((9, 9), np.uint8)), dist)   # sky borrows its neighbour's depth
    fog = 1 - np.exp(-np.clip(dg - near * 1.15, 0, None) / (near * reach))
    fog = sky + (1 - sky) * fog * 0.85
    # drifting mist banks: denser low in frame and far away
    m1 = np.roll(MIST, int(t * 22) % (W * 4), axis=1)[:, :W]
    m2 = np.roll(MIST[::-1], int(-t * 14) % (W * 4), axis=1)[:, W:2 * W]
    mist = np.clip((m1 * 0.6 + m2 * 0.4) - 0.35, 0, 1) * 1.6
    fog = np.clip(fog + mist * (0.08 + 0.3 * fog) * (0.5 + 0.5 * yy / H), 0, 1)[..., None]
    # shadow sling: huge cloud shadows drifting over the land convey the scale of the realm
    ox, oy = int(t * 40) % (2 * W), int(t * 12) % (2 * H)
    cs = CSHADOW[oy:oy + H, ox:ox + W]
    ground_m = (1 - sky)[..., None]
    c = c * (1 - ground_m * shadow_k * np.clip((cs - 0.45) * 2.5, 0, 1)[..., None])
    hy = np.clip(yy / (H * 0.6), 0, 1)[..., None]
    fogcol = np.float32(top) * (1 - hy) + np.float32(far) * hy
    c = c * (1 - fog) + fogcol * fog
    if t < R.HOUSE_START:                                         # low run: a pale glow on the horizon keeps the sea
        gw = sm(prog(t, R.CLOUD_BREAK - 0.5, 1.0)) * (1 - sm(prog(t, 22.8, 1.0)))   # apart from the night sky
        if gw > 0:
            glow = None
            if str(fi) in HORIZON:                                  # the sea's far edge, projected from the camera
                k, b = HORIZON[str(fi)]
                dy = (k * xx[:1] + b) - yy
                glow = np.where(dy > 0, np.exp(-dy / 70.0), np.exp(dy / 8.0)).astype(np.float32)
            if glow is not None:
                c = c + (glow * sky * gw)[..., None] * (np.float32(far) * 0.9 + 18)
    src, rcol, rs = RAYS[ga] if u < 0.5 else RAYS[gb]
    c = god_rays(c, src, rcol, rs * 0.8 * shaft_gain, t)
    c = bloom(c, 0.3)
    ka, kb = PARTS[ga], PARTS[gb]
    if ka == kb:
        c = apply_particles(c, ka, t, 1.0)
    else:
        c = apply_particles(c, ka, t, 1 - u)
        c = apply_particles(c, kb, t, u)
    if 'sun' in (ga, gb):
        w = (1 - u) if ga == 'sun' else u
        if w > 0.05:
            farm = np.clip((dist - near * 1.2) / (near * 1.5), 0, 1)
            dx = (np.sin(yy / 7 + t * 7) * 2.4 * w * farm).astype(np.float32)
            c = cv2.remap(c, xx + dx, yy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if 'fire' in (ga, gb):
        w = (1 - u) if ga == 'fire' else u
        fl = 0.5 + 0.3 * math.sin(t * 13.0) + 0.2 * math.sin(t * 29.0 + 1.3)
        c = c * (1 + 0.06 * fl * w) + np.clip(1 - yy / H * 1.2, 0, 1)[..., None] * 0 + \
            np.exp(-(((xx - W / 2) / 900) ** 2 + ((yy - H * 0.95) / 380) ** 2))[..., None] * np.float32([10, 45, 120]) * fl * w
    if 'storm' in (ga, gb):
        s0 = R.house_window(5)[0]
        L = sum(math.exp(-((t - (s0 + k)) / 0.05) ** 2) for k in (1.4, 1.55, 6.2))
        c = c * (1 + 0.9 * L) + 40 * L
    c *= 1 + 0.015 * math.sin(t * 11) * math.sin(t * 3.7)        # a candle-like breath in the exposure
    if 'cold' in (ga, gb):                                        # frost flakes drifting across the lens
        w = (1 - u) if ga == 'cold' else u
        c = lens_frost(c, t, w)
    sx = 1.6 * math.sin(t * 1.9) + 0.9 * math.sin(t * 4.3 + 1)    # grounded handheld drift
    sy = 1.2 * math.sin(t * 2.3 + 2) + 0.7 * math.sin(t * 5.1)
    c = cv2.warpAffine(c, np.float32([[1.004, 0, sx - W * 0.002], [0, 1.004, sy - H * 0.002]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    return c * VIG


FROST = np.random.default_rng(44).random((16, 5)).astype(np.float32)


def lens_frost(c, t, w):
    if w <= 0.02:
        return c
    lay = np.zeros((H // 4, W // 4), np.float32)
    for x0, y0, r, sp, ph in FROST:
        y = (y0 * (H // 4 + 60) + t * (6 + 10 * sp)) % (H // 4 + 60) - 30
        x = x0 * W // 4 + 10 * math.sin(t * 0.5 + ph * 6)
        cv2.circle(lay, (int(x), int(y)), int(4 + 10 * r), 1.0, -1, cv2.LINE_AA)
    lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 3), (W, H))[..., None] * 0.35 * w
    return c * (1 - lay) + (cv2.GaussianBlur(c, (0, 0), 12) * 0.6 + 200 * 0.4) * lay


# ---------------- overlays ----------------
def lower_third(c, key, lt):
    a = sm(prog(lt, 3.6, 0.6)) * (1 - sm(prog(lt, 9.0, 0.5)))
    if a <= 0.003:
        return c
    slide = int(30 * (1 - oc(prog(lt, 3.6, 0.9))))
    shade = np.exp(-(((xx - 420) / 620) ** 2 + ((yy - 900) / 150) ** 2))[..., None] * 0.55 * a
    c = c * (1 - shade)
    ic = icon(key)
    c = over(c, ic, a, 150 - ic.shape[1] // 2 + slide // 2 - 40, 890 - ic.shape[0] // 2)
    for part, delay in (('name', 0.0), ('sub', 0.25), ('sec', 0.45)):
        aa = sm(prog(lt, 3.6 + delay, 0.6)) * (1 - sm(prog(lt, 9.0, 0.5)))
        c = over(c, shift(txt(f'{key}_{part}'), -slide), aa)
    return c


def embers_2d(c, t, s):
    return apply_particles(c, 'embers', t, s)


SPOT = None


def trophy_frame(k):
    """the trophy render at a fractional frame: its slow dolly is slowed further, so in-between frames are
    interpolated along the optical flow (the motion is a few pixels a frame at most)"""
    rd = lambda i: cv2.imread(f"{os.environ.get('TROPHY', 'build/trophy')}/{i:05d}.png").astype(np.float32)
    dd = lambda i: cv2.imread(f'build/trophy_depth/{i:05d}.png', cv2.IMREAD_UNCHANGED).astype(np.float32) / 65535 * 20
    i = min(int(k), 119)
    w = min(k - i, 1.0)
    a, da = rd(i), dd(i)
    if w < 1e-3:
        return a, da
    b, db = rd(i + 1), dd(i + 1)
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    fl = dis.calc(cv2.cvtColor(a.astype(np.uint8), cv2.COLOR_BGR2GRAY), cv2.cvtColor(b.astype(np.uint8), cv2.COLOR_BGR2GRAY), None)
    wa = cv2.remap(a, xx - w * fl[..., 0], yy - w * fl[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    wb = cv2.remap(b, xx + (1 - w) * fl[..., 0], yy + (1 - w) * fl[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return wa * (1 - w) + wb * w, da * (1 - w) + db * w


def card_trophy(t, fi):
    """the reference's opening: a trophy in a dark hall under one shaft of light"""
    global SPOT
    raw, dep = trophy_frame(min(t / R.TROPHY[1], 1.0) * 120)
    c = grade(raw * 1.05, (0.95, (1.06, 1.0, 0.95), (0.70, 0.95, 1.25), 1.3, -12))
    # warm the gold, punch its highlights
    lum = c.mean(2, keepdims=True)
    gold = np.clip((c[..., 2:3] - c[..., 0:1]) / 60, 0, 1)
    c = c * (1 + 0.5 * gold * np.clip(lum / 120, 0, 1.5))
    # the hall falls away into darkness and haze
    fog = (1 - np.exp(-np.clip(dep - 2.5, 0, None) / 4.0))[..., None]
    c = c * (1 - fog) + np.float32([16, 14, 13]) * fog
    if SPOT is None:   # a soft cone from above onto the trophy, plus a pool of light on the plinth
        cone = np.clip(1 - np.abs(xx - W / 2) / (90 + yy * 0.42), 0, 1) ** 1.6 * np.clip(yy / 300, 0, 1)
        pool = np.exp(-(((xx - W / 2) / 420) ** 2 + ((yy - H * 0.86) / 90) ** 2))
        SPOT = (cone, pool)
    cone, pool = SPOT
    haze = np.roll(MIST, int(t * 30), axis=1)[:, :W]
    c = c + (cone * (0.55 + 0.45 * haze))[..., None] * np.float32([150, 175, 200]) * 0.42
    c = c + pool[..., None] * np.float32([60, 80, 100]) * 0.5
    # dust drifting through the beam only
    lay, _ = particles('dust', t, 1.6)
    c = c + lay * cone[..., None] * 1.6
    c = bloom(c, 0.5)
    c *= sm(prog(t, 0.5, 2.2))                                   # up out of the dark as the music begins
    return c * VIG


def who_text(c, t):
    w0 = R.WHO_AT
    a = sm(prog(t, w0, 1.2)) * (1 - sm(prog(t, R.COLD_OPEN[1] - 0.9, 0.8)))
    if a <= 0.003:
        return c
    lay = scale_about(txt('who'), 1.0 + 0.03 * prog(t, w0, 5.0))
    blur = 5 * (1 - sm(prog(t, w0, 1.4)))
    if blur > 0.3:
        lay = cv2.GaussianBlur(lay, (0, 0), blur)
    return over(c, lay, a)


def card_open(t, fi):
    if t < R.TROPHY[1]:
        c = card_trophy(t, fi) * (1 - sm(prog(t, R.TROPHY[1] - 1.2, 1.2)))
    else:
        c = np.zeros((H, W, 3), np.float32)
        c = apply_particles(c, 'embers', t, 0.25)
    return who_text(c, t)


def card_credits(t, fi):
    lt = t - R.CREDITS[0]
    ak = R.LSC_AT - R.CREDITS[0]                                 # the akashic's span
    c = np.zeros((H, W, 3), np.float32)
    if lt < ak:       # the akashic, on a deep blue glow
        a = sm(prog(lt, 0.0, 0.6)) * (1 - sm(prog(lt, ak - 0.8, 0.7)))
        glow = np.exp(-(((xx - W / 2) / 520) ** 2 + ((yy - 560) / 320) ** 2))[..., None]
        c += glow * np.float32([150, 50, 10]) * 0.9 * a
        logo = rgba_img('assets/akashic.png', 760)
        lh, lw = logo.shape[:2]
        x0, y0 = W // 2 - lw // 2, 560 - lh // 2
        wipe = prog(lt, 0.3, 2.0) * (lw + 240) - 120
        mask = np.clip((wipe - np.arange(lw, dtype=np.float32)) / 120, 0, 1)[None, :, None]
        c = over(c, logo * mask, a, x0, y0)
        c = over(c, txt('ak_l1'), sm(prog(lt, 0.6, 1.0)) * a)
    else:             # the Local Student Council presents
        u = lt - ak
        u1 = R.CREDITS[1] - R.LSC_AT - 1.0                        # out ~0.4 s before the drop: a breath of black
        a = sm(prog(u, 0.0, 0.9)) * (1 - sm(prog(u, u1, 0.6)))
        c += np.exp(-(((xx - W / 2) / 700) ** 2 + ((yy - 470) / 420) ** 2))[..., None] * np.float32([40, 30, 18]) * 0.6
        c = apply_particles(c, 'embers', t, 0.3)
        seal = rgba_img('assets/lsc-seal.webp', 400)
        s = 0.96 + 0.04 * oc(prog(u, 0.0, 5.0))
        sz = int(400 * s)
        seal_s = cv2.resize(seal, (sz, sz), interpolation=cv2.INTER_AREA)
        full = np.zeros((H, W, 4), np.float32)
        full[445 - sz // 2:445 - sz // 2 + sz, W // 2 - sz // 2:W // 2 - sz // 2 + sz] = seal_s
        c += cv2.GaussianBlur(full[..., 3], (0, 0), 30)[..., None] * np.float32([60, 120, 200]) * 0.45 * a   # full-frame glow, no box edges
        c = over(c, full, a)
        for name, dl in (('lsc_l1', 0.6), ('lsc_l2', 1.0), ('lsc_l3', 2.0)):
            c = over(c, txt(name), sm(prog(u, dl, 1.0)) * (1 - sm(prog(u, u1, 0.6))))
    return c * VIG


def clouds_part(c, u, flash=0.0, op=1.0):
    """a cloud deck splits open from the centre as we fall through it; u runs 0..1"""
    if u >= 1:
        return c
    zoom = 1 + 0.9 * oc(u)                    # the deck grows and slides outward past the lens
    M = cv2.getRotationMatrix2D((W, H), 0, zoom)
    M[0, 2] -= W / 2
    M[1, 2] -= H / 2
    cl = cv2.warpAffine(CLOUD_BIG, M, (W, H))
    r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2)
    hole = (r - 0.95 * oc(u) + 0.05) / 0.25                       # grows outward
    a = np.clip(hole + (cl - 0.5) * 1.6, 0, 1)[..., None] * op
    cloud_col = np.float32([236, 234, 230]) * (0.9 + 0.1 * cl[..., None])
    c = c * (1 - a) + cloud_col * a
    return c * (1 - flash) + 255 * flash


DIVE_SEEDS = np.random.default_rng(57).random((12, 3)).astype(np.float32)


def cloud_dive(c, t):
    """the dive: layer after layer of cloud rushes past the lens, the realm glimpsed far below through the gaps,
    until we burst out under the last deck at CLOUD_BREAK"""
    t0, tb = R.MAP_IN[0], R.CLOUD_BREAK
    cover = 0.6 - 0.36 * sm(prog(t, t0 + 0.8, tb - t0 - 1.6))   # the gaps open up as we fall
    haze = 0.4 - 0.32 * sm(prog(t, t0, tb - t0))                 # the realm far below, pale with distance
    c = c * (1 - haze) + np.float32([205, 200, 194]) * haze
    P, L = 0.9, 2.2                                              # a new layer every 0.9 s, each passes in 2.2 s
    lays = []
    for k in range(12):
        born = t0 - 1.6 + k * P
        a = (t - born) / L
        if not (0 <= a < 1) or born > tb - 0.8:
            continue
        lays.append((a, k))
    for a, k in sorted(lays):                                    # far (young) layers first, the nearest on top
        sx, sy, rot = DIVE_SEEDS[k]
        zoom = 0.4 + 2.6 * a * a                                 # accelerating toward the lens
        M = cv2.getRotationMatrix2D((W, H), float(rot * 360), zoom)
        M[0, 2] -= W / 2 + (sx - 0.5) * 300
        M[1, 2] -= H / 2 + (sy - 0.5) * 200
        cl = cv2.warpAffine(CLOUD_BIG, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        thr = 1 - cover
        m = np.clip((cl - thr) / 0.12, 0, 1) * math.sin(math.pi * min(a / 0.35, 1.0) * 0.5) * (1 - sm(prog(a, 0.75, 0.25))) \
            * (1 - sm(prog(t, tb - 0.1, 0.4)))                   # whatever is left blows away with the burst
        if a > 0.4:                                              # close layers smear as they rush by
            m = cv2.GaussianBlur(m, (0, 0), 2 + 14 * (a - 0.4))
        shade = np.clip((cl - thr) / 0.3, 0, 1)[..., None]       # sunlit crowns, grey undersides at the edges
        col = np.float32([238, 236, 232]) * (0.62 + 0.38 * shade)
        c = c * (1 - m[..., None]) + col * m[..., None]
    if t > tb - 1.0:                                             # the last deck closes in, then bursts open
        c = clouds_part(c, prog(t, tb - 0.4, 1.0), 0.22 * math.exp(-((t - tb) / 0.12) ** 2), sm(prog(t, tb - 1.0, 0.6)))
    return c * sm(prog(t, t0 - 1.0 / FPS, 0.12))                # cut in on the music's drop


def title_img():
    """the council's own PAGSIKLAB lettering (gold on black) as a premultiplied full-frame layer"""
    if 'title_img' not in _C:
        im = cv2.imread('assets/pagsiklab-title.webp').astype(np.float32)[200:530, 35:1945]
        s = 1500 / im.shape[1]
        im = cv2.resize(im, (1500, int(im.shape[0] * s)), interpolation=cv2.INTER_AREA)
        a = np.clip(im.max(2) / 70.0, 0, 1) ** 0.8                 # black background keys out
        full = np.zeros((H, W, 4), np.float32)
        h, w = im.shape[:2]
        y0, x0 = 470 - h // 2, (W - w) // 2
        full[y0:y0 + h, x0:x0 + w, :3] = im                        # already premultiplied on black
        full[y0:y0 + h, x0:x0 + w, 3] = a
        _C['title_img'] = full
    return _C['title_img']


FG = {}


def dragons():
    """the two dragon cut-outs as dark silhouettes (alpha only), cropped to their bodies"""
    if 'dr' not in FG:
        im = cv2.imread('assets/dragons.webp', cv2.IMREAD_UNCHANGED).astype(np.float32)
        a = im[..., 3] / 255
        lab = cv2.connectedComponents((a > 0.08).astype(np.uint8), 8)[1]
        out = []
        for k in (1, 2):
            m = a * (lab == k)
            ys, xs = np.nonzero(m > 0.05)
            out.append(np.ascontiguousarray(m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]))
        FG['dr'] = out
    return FG['dr']


# (which dragon, start, end, x0, x1, y0, y1, width px, flip)
FLIGHTS = [(1, 1.4, 7.4, 2300, -500, 250, 120, 900, False),     # close: sweeps right to left behind the title
           (0, 5.8, 12.6, -300, 2200, 150, 70, 420, True)]       # far: a smaller one crosses high, left to right


def draw_dragons(c, t, s0, a):
    drs = dragons()
    for k, ts, te, x0, x1, y0, y1, wd, flip in FLIGHTS:
        u = (t - s0 - ts) / (te - ts)
        if not (0 < u < 1):
            continue
        m = drs[k][:, ::-1] if flip else drs[k]
        s = wd / m.shape[1]
        flap = 1 + 0.07 * math.sin((t - s0) * 5.5 + k)
        sz = (int(wd), max(int(m.shape[0] * s * flap), 2))
        mm = cv2.resize(m, sz, interpolation=cv2.INTER_AREA)
        far = wd < 500
        mm = cv2.GaussianBlur(mm, (0, 0), 1.6 if far else 1.2)
        x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u + 18 * math.sin(u * 6)
        lay = np.zeros((H, W), np.float32)
        X0, Y0 = int(x - sz[0] / 2), int(y - sz[1] / 2)
        xa, ya, xb, yb = max(X0, 0), max(Y0, 0), min(X0 + sz[0], W), min(Y0 + sz[1], H)
        if xb <= xa or yb <= ya:
            continue
        lay[ya:yb, xa:xb] = mm[ya - Y0:yb - Y0, xa - X0:xb - X0]
        fade = sm(u / 0.08) * sm((1 - u) / 0.08) * a * (0.55 if far else 0.92)
        rim = np.clip(lay - np.roll(lay, -6, axis=0), 0, 1)            # underside lit by the fire below
        c = c * (1 - lay[..., None] * fade) + lay[..., None] * np.float32([7, 7, 9]) * fade
        if not far:
            c += cv2.GaussianBlur(rim, (0, 0), 2)[..., None] * np.float32([20, 70, 170]) * fade
    return c


def fg_clouds(t, e):
    """dark storm clouds rolling across the foreground, heavier at the bottom and the corners"""
    ox = int(t * 60) % (2 * W)
    cl = CSHADOW[200:200 + H, ox:ox + W]
    cl2 = CSHADOW[600:600 + H, (int(-t * 35) % (2 * W)):(int(-t * 35) % (2 * W)) + W]
    d = np.clip(cl * 0.6 + cl2 * 0.4, 0, 1)
    wgt = np.clip((yy - H * 0.5) / (H * 0.5), 0, 1) ** 1.2 + 0.55 * np.clip(np.abs(xx - W / 2) / (W / 2) - 0.55, 0, 1) * 2
    m = np.clip((d - 0.42) * 3.0 + wgt * 1.1 - 0.55, 0, 1)
    m = push(cv2.GaussianBlur(m, (0, 0), 7), 1 + 0.14 * e, H)
    under = np.clip(m - push(np.roll(m, 18, axis=0), 1.0), 0, 1)          # fire light on the cloud bellies
    return m, cv2.GaussianBlur(under, (0, 0), 8)


FG_BOKEH = np.random.default_rng(81).random((9, 5)).astype(np.float32)


def fg_bokeh(t):
    lay = np.zeros((H // 2, W // 2, 3), np.float32)
    for x0, y0, r, sp, ph in FG_BOKEH:
        rad = 4 + 9 * r
        y = (y0 * (H // 2 + 120) - t * (22 + 40 * sp)) % (H // 2 + 120) - 60
        x = (x0 * W // 2 + 30 * math.sin(t * 0.6 + ph * 6) - t * 12) % (W // 2)
        tw = 0.35 + 0.65 * math.sin(t * (0.8 + sp) + ph * 9) ** 2
        cv2.circle(lay, (int(x), int(y)), int(rad), (float(40 * tw), float(120 * tw), float(255 * tw)), -1, cv2.LINE_AA)
    lay = cv2.GaussianBlur(lay, (0, 0), 4)
    return cv2.resize(lay, (W, H)) * 0.35


def push(img, s, cy=H / 2):
    M = cv2.getRotationMatrix2D((W / 2, cy), 0, s)
    return cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)


def finale(c, t):
    s0 = R.TITLE[0]
    e = sm(prog(t, s0, R.END - s0))                              # the slow push-in that drives the parallax
    dark = sm(prog(t, s0, 1.6))
    if dark > 0:
        k = 1 + int(14 * dark)
        c = push(cv2.GaussianBlur(c, (0, 0), k), 1 + 0.04 * e) * (1 - 0.7 * dark)     # far plane: slowest
    # middle plane: warm smoke rolling behind the lettering
    sm1 = np.roll(MIST, int(t * 26) % (W * 4), axis=1)[:, :W]
    smoke = np.clip(sm1 - 0.3, 0, 1) * np.exp(-((yy - 520) / 360) ** 2)
    c += (smoke * dark)[..., None] * np.float32([18, 42, 85])
    c = embers_2d(c, t, 0.9 * dark)
    c = draw_dragons(c, t, s0, dark)                               # dragons glide through the smoke behind the title
    tp = push(title_img(), 1 + 0.035 * e, 470)                    # title plane
    wp = prog(t, s0 + 1.2, 1.6)
    if wp > 0:
        edge = 160 + (1760 - 160) * sm(wp)
        rev = np.clip((edge - xx) / 70, 0, 1)[..., None]
        lay = tp * rev
        c = c + cv2.GaussianBlur(lay[..., 3], (0, 0), 34)[..., None] * np.float32([30, 100, 230]) * 0.85
        c = over(c, lay)
        if wp < 1:
            ee = np.exp(-((xx - edge) / 18) ** 2) * tp[..., 3]
            c += (ee + cv2.GaussianBlur(ee, (0, 0), 16) * 1.5)[..., None] * np.float32([170, 215, 255])
    # foreground: dark storm clouds rolling past the lens, a few embers drifting through
    m, under = fg_clouds(t, e)
    flick = 0.75 + 0.25 * math.sin(t * 9.0) * math.sin(t * 3.1 + 1)
    c = c * (1 - m[..., None] * 0.9 * dark) + m[..., None] * np.float32([9, 9, 12]) * dark
    c += under[..., None] * np.float32([20, 70, 170]) * 0.55 * flick * dark
    c += fg_bokeh(t) * dark
    for name, st in (('title_sub', s0 + 2.9), ('title_q', s0 + 4.0)):     # in front of the clouds
        c = over(c, push(txt(name), 1 + 0.035 * e, 470), sm(prog(t, st, 0.8)))
    # the council line and seal sit on top of everything, steady
    a = sm(prog(t, s0 + 5.2, 0.8))
    c = over(c, txt('end_lsc'), a)
    seal = rgba_img('assets/lsc-seal.webp', 96)                  # the end card carries the council seal only
    c = over(c, seal, a, W // 2 - 48, 948 - 48)
    return c * (1 - sm(prog(t, R.END - 1.6, 1.4)))


def end_card(t):
    """the closing line, on black after the film has faded out"""
    lt = t - R.END
    c = np.zeros((H, W, 3), np.float32)
    sm1 = np.roll(MIST, int(t * 18) % (W * 4), axis=1)[:, :W]                    # faint warm smoke, as in the finale
    c += (np.clip(sm1 - 0.35, 0, 1) * np.exp(-((yy - 540) / 380) ** 2) * 0.55)[..., None] * np.float32([18, 42, 85])
    c = embers_2d(c, t, 0.45)
    c *= sm(prog(lt, 0.4, 1.4))
    a = sm(prog(lt, 1.0, 1.4)) * (1 - sm(prog(lt, R.ROLL - 2.2, 1.2)))
    if a > 0.003:
        lay = scale_about(txt('end_line'), 1 + 0.02 * prog(lt, 0.0, R.ROLL))          # a slow push-in
        c += cv2.GaussianBlur(lay[..., 3], (0, 0), 16)[..., None] * np.float32([30, 100, 230]) * 0.45 * a
        c = over(c, lay, a)
    return c * VIG * (1 - sm(prog(lt, R.ROLL - 1.0, 0.9)))


def render(fi):
    seed = fi
    t = fi / FPS + 1e-6
    if t >= R.OPEN_END:                                          # from the dive on: the 3D timeline
        fi -= R.LEAD_F
        t = fi / FPS + 1e-6
    if t >= R.END:
        c = end_card(t)
    elif fi == seed and t < R.COLD_OPEN[1]:
        c = card_open(t, fi)
    elif fi == seed:
        c = card_credits(t, fi)
    else:
        c = treat3d(fi, t)
        if t < R.CLOUD_BREAK + 0.6:
            c = cloud_dive(c, t)
        if R.HOUSE_START <= t < R.OVERVIEW[0]:
            i = min(int((t - R.HOUSE_START) // R.HOUSE_LEN), 6)
            s = R.house_window(i)[0] if i < 6 else R.CAMPUS_WIN[0]
            c = lower_third(c, R.HOUSES[i]['key'] if i < 6 else 'campus', t - s)
        if R.OVERVIEW[0] <= t < R.TITLE[0]:
            a = sm(prog(t, R.OVERVIEW[0] + 1.0, 0.9)) * (1 - sm(prog(t, R.OVERVIEW[1] - 1.4, 0.8)))
            # a dark band settles behind the words so they read over the sunlit map, then gold with a warm glow
            band = np.exp(-((yy - H / 2) / 150) ** 2 - ((xx - W / 2) / 1100) ** 4)[..., None] * 0.62 * a
            c = c * (1 - band)
            era = scale_about(txt('era'), 1 + 0.03 * prog(t, R.OVERVIEW[0], 7))
            glow = cv2.GaussianBlur(era[..., 3], (0, 0), 14)[..., None]
            c = c + glow * np.float32([40, 120, 230]) * 0.55 * a
            c = over(c, era, a)
        if t >= R.TITLE[0]:
            c = finale(c, t)
    if c.mean() > 2:
        rgen = np.random.default_rng(seed)
        g1 = cv2.resize(rgen.standard_normal((H // 2, W // 2)).astype(np.float32), (W, H))
        g2 = cv2.GaussianBlur(rgen.standard_normal((H, W)).astype(np.float32), (0, 0), 0.6)
        lum = np.clip(c.mean(2) / 255, 0, 1)
        amt = (4.5 * (lum * (1 - lum)) * 2 + 0.8)[..., None]                    # strongest in the mid-tones
        c = c + (g1 * 0.6 + g2 * 0.5)[..., None] * amt
        if fi != seed:
            c = c + LENS_DUST * np.clip((c.mean(2, keepdims=True) - 90) / 120, 0, 1) * 18
    return np.clip(c, 0, 255).astype(np.uint8).tobytes()


if __name__ == '__main__':
    out = sys.argv[1]
    if len(sys.argv) > 2:
        for fi in [int(x) for x in sys.argv[2].split(',')]:
            cv2.imwrite(out.replace('.png', f'_{fi:05d}.png'), np.frombuffer(render(fi), np.uint8).reshape(H, W, 3))
        sys.exit()
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
                           '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    with Pool(int(os.environ.get('PROCS', '3'))) as pool:
        for i, fr in enumerate(pool.imap(render, range(NF), chunksize=4)):
            ff.stdin.write(fr)
            if i % 240 == 0:
                print(i, flush=True)
    ff.stdin.close()
    ff.wait()
