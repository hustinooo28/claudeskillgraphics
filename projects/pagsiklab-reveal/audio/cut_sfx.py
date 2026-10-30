"""Cuts the council's cinematic SFX reel (FlameSound "Cinematic SFX", free edition) into named one-shots in audio/sfx/.
usage: python3 audio/cut_sfx.py REEL.mp4"""
import os, subprocess, sys
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
# name: (window start, window end) in the reel; each cut starts at its onset inside the window
CUTS = {
    'intro_hit':        (5.6, 9.6),
    'impact_metallic':  (9.83, 13.75),
    'tension_dramatic': (13.75, 17.3),
    'downshifter':      (17.3, 21.3),
    'boom_cavernous_b': (21.3, 24.4),
    'noise_short':      (24.4, 25.7),
    'boom_earthcore':   (25.7, 29.6),
    'boom_cavernous_a': (29.6, 33.4),
    'braam_massive':    (33.6, 37.6),
    'boom_morphing':    (37.6, 40.2),
    'riser_12':         (40.2, 42.6),
    'boom_big_reveal':  (42.6, 45.5),
    'drone_nocturnal':  (45.5, 50.0),
    'riser_02':         (50.0, 58.25),
    'braam_up_under':   (58.25, 62.6),
    'drone_stellar':    (63.0, 76.0),
}
ONSET = {'impact_metallic', 'drone_nocturnal', 'riser_02', 'drone_stellar', 'tension_dramatic', 'riser_12', 'downshifter'}   # keep window start

wav = subprocess.run(['ffmpeg', '-v', 'error', '-i', sys.argv[1], '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'],
                     capture_output=True, check=True).stdout
x = np.frombuffer(wav, np.float32).reshape(-1, 2).astype(np.float64)
m = np.abs(x).mean(1)
hop = int(0.005 * SR)
os.makedirs(os.path.join(HERE, 'sfx'), exist_ok=True)
for name, (a, b) in CUTS.items():
    i, j = int(a * SR), int(b * SR)
    if name not in ONSET:                      # snap to the transient: the steepest 40 ms energy rise in the window
        e = np.array([np.sqrt((m[k:k + hop] ** 2).mean()) for k in range(i, j - hop, hop)])
        db = 20 * np.log10(e + 1e-9)
        rise = db[8:] - db[:-8]
        k0 = int(np.argmax(rise[:len(rise) // 2 + 1]))
        i = i + k0 * hop
    seg = x[i:j].copy()
    fi, fo = int(0.004 * SR), int(min(0.35, (j - i) / SR * 0.25) * SR)
    seg[:fi] *= np.linspace(0, 1, fi)[:, None]
    seg[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 2
    sf.write(os.path.join(HERE, 'sfx', name + '.flac'), seg.astype(np.float32), SR)
    print('%-18s %6.2f s  from %.2f  peak %.1f dB' % (name, len(seg) / SR, i / SR, 20 * np.log10(np.abs(seg).max())))
