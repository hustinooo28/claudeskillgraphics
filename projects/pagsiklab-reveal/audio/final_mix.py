"""Final soundtrack: the council's chosen music track, edited to the picture, with the film's sound design on top.
Needs build/track.wav (48 kHz stereo) and build/fx_stem.npy (from score.py). Writes build/score.wav."""
import os, sys
import numpy as np
from scipy import signal
from scipy.io import wavfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import realm as R

SR = 48000
B = os.path.join(os.path.dirname(HERE), 'build')
sr, tr = wavfile.read(os.path.join(B, 'track.wav'))
tr = tr.astype(np.float64) / 32768
N = int(R.END * SR)
fx = np.load(os.path.join(B, 'fx_stem.npy')).astype(np.float64)
vo0, vo1 = np.load(os.path.join(B, 'vo_span.npy'))

STINGER = 164.5                       # the track's final hit
TITLE_HIT = R.TITLE[0] + 1.2          # PAGSIKLAB ignites
OFF = STINGER - TITLE_HIT             # track time = video time + OFF, from the map onward
CUT = R.MAP_IN[0]                     # cut from the quiet intro to the full section as we fall onto the realm
XF = int(0.25 * SR)

music = np.zeros((N, 2))
a = tr[:int(CUT * SR) + XF].copy()                                     # 0:00-0:18 under the cold open
music[:len(a)] += a * np.r_[np.ones(len(a) - XF), np.linspace(1, 0, XF)][:, None]
s0 = int((CUT + OFF) * SR) - XF
b = tr[s0:s0 + N - int(CUT * SR) + XF]
b = b * np.r_[np.linspace(0, 1, XF), np.ones(len(b) - XF)][:, None]
music[int(CUT * SR) - XF:int(CUT * SR) - XF + len(b)] += b

# the music sits under the voice and opens up afterward
g = np.ones(N)
g[int((vo0 - 0.3) * SR):int((vo1 + 0.4) * SR)] = 0.45
g = np.convolve(g, np.ones(9600) / 9600, mode='same')
music *= g[:, None] * 0.9
# effects sit under the music: a slow level rider keeps them ~10 dB below it (never louder than a floor),
# and a soft limiter rounds off the transients so no single hit jumps out
def movavg(x, win):
    """centred moving average via cumulative sums (np.convolve is far too slow for second-long windows)"""
    c = np.cumsum(np.r_[0.0, x])
    y = (c[win:] - c[:-win]) / win
    pad = len(x) - len(y)
    return np.pad(y, (pad // 2, pad - pad // 2), mode='edge')


def env_rms(x, win):
    p = movavg((x ** 2).mean(1) if x.ndim == 2 else x ** 2, win)
    return np.sqrt(np.maximum(p, 0) + 1e-12)


win = int(0.6 * SR)
m_env, f_env = env_rms(music, win), env_rms(fx, win)
target = np.maximum(m_env * 10 ** (-10 / 20), 10 ** (-38 / 20))
g_fx = np.clip(target / (f_env + 1e-9), 0.0, 1.7) * 0.9      # duck loud effects, lift buried ones a little
g_fx = movavg(g_fx, int(0.25 * SR))
fx = fx * g_fx[:, None]
lim = 10 ** (-16 / 20)
fx = np.tanh(fx / lim) * lim
vo = np.load(os.path.join(B, 'vo_stem.npy')).astype(np.float64)
mix = music + fx + vo * 1.0
if os.environ.get('MIX_REPORT'):
    lvl = lambda x: 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-12)
    for nm, a, b in [('cold open', 0, 7), ('forge', 7, 12), ('credits', 12, 18), ('houses', 24, 90), ('campus', 90, 101), ('title', 108, 118)]:
        i, j = int(a * SR), int(b * SR)
        print('%-10s music %6.1f  fx %6.1f  vo %6.1f dB' % (nm, lvl(music[i:j]), lvl(fx[i:j]), lvl(vo[i:j])))
e = np.ones(N)
k0 = int((R.END - 1.6) * SR)
e[k0:] = np.linspace(1, 0, N - k0) ** 2
mix *= e[:, None]
mix = np.stack([signal.sosfilt(signal.butter(2, 28, 'high', fs=SR, output='sos'), mix[:, c]) for c in range(2)], 1)
mix = mix / np.abs(mix).max() * 1.15
mix = np.tanh(mix) / np.tanh(1.15) * 0.9
wavfile.write(os.path.join(B, 'score.wav'), SR, (mix * 32767).astype(np.int16))
print('final mix written; track offset %.2f s (video %.1f s = track %.1f s)' % (OFF, CUT, CUT + OFF))
