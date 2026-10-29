"""Cut the council's house emblems out of their backgrounds -> assets/emblems/<house>.png (RGBA)."""
import cv2, numpy as np

def cut_light(im, thr=232, min_area=900, feather=1.2):
    """white / checkerboard backgrounds: big connected regions of bright, unsaturated pixels"""
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    bright = ((im.min(2) >= thr) & (hsv[..., 1] < 30)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(bright, 4)
    bg = np.zeros(bright.shape, np.uint8)
    for i in range(1, n):
        x, y, w, h, a = st[i]
        touches = x == 0 or y == 0 or x + w >= im.shape[1] or y + h >= im.shape[0]
        if a >= min_area or (touches and a > 30):
            bg[lab == i] = 1
    bg = cv2.morphologyEx(bg, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    a = 1 - cv2.GaussianBlur(bg.astype(np.float32), (0, 0), feather)
    a = np.clip((a - 0.25) / 0.75, 0, 1)
    return a

def cut_dark(im, thr=62):
    """dark wall background: the bright metal sigil, holes filled. The wall has a soft light gradient,
    so subtract a heavily blurred copy (the wall) and keep what stands out from it"""
    lum = im.mean(2).astype(np.float32)
    wall = cv2.medianBlur(im, 61).mean(2).astype(np.float32)
    m = ((lum - wall) > 18).astype(np.uint8) | (lum > 150).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    k = 1 + np.argmax(st[1:, 4])
    m = (lab == k).astype(np.uint8)
    ff = m.copy(); h, w = m.shape
    cv2.floodFill(ff, np.zeros((h + 2, w + 2), np.uint8), (0, 0), 1)
    m = m | (1 - ff)
    return np.clip(cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.0) * 1.3 - 0.15, 0, 1)

SRC = {'targaryen': ('light', 236), 'lannister': ('light', 236), 'tyrell': ('light', 238), 'stark': ('light', 205), 'martell': ('dark', 62)}
prev = []
for k, (mode, thr) in SRC.items():
    im = cv2.imread(f'assets/emblems/{k}_src.png')
    a = cut_light(im, thr) if mode == 'light' else cut_dark(im, thr)
    # drop specks: keep only components that are a real part of the emblem
    n, lab, st, _ = cv2.connectedComponentsWithStats((a > 0.5).astype(np.uint8), 8)
    keep = np.zeros(a.shape, np.float32)
    big = st[1:, 4].max()
    for i in range(1, n):
        if st[i, 4] > 0.01 * big:
            keep[lab == i] = 1
    a = a * cv2.dilate(keep, np.ones((5, 5), np.uint8))
    ys, xs = np.nonzero(a > 0.05)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    out = np.dstack([im, (a * 255).astype(np.uint8)])[y0:y1, x0:x1]
    cv2.imwrite(f'assets/emblems/{k}.png', out)
    t = np.full((260, 260, 3), (40, 30, 70), np.float32)
    s = 250 / max(out.shape[:2]); o = cv2.resize(out, (int(out.shape[1] * s), int(out.shape[0] * s)), interpolation=cv2.INTER_AREA).astype(np.float32)
    oy, ox = (260 - o.shape[0]) // 2, (260 - o.shape[1]) // 2
    al = o[..., 3:] / 255
    t[oy:oy + o.shape[0], ox:ox + o.shape[1]] = t[oy:oy + o.shape[0], ox:ox + o.shape[1]] * (1 - al) + o[..., :3] * al
    prev.append(t)
cv2.imwrite('build/tex/emblems_cut.jpg', np.hstack(prev).astype(np.uint8))
print('ok')
