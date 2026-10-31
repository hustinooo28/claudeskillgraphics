"""Final soundtrack: the council's chosen music track, edited to the picture, with the film's sound design on top.
Needs build/track.wav (48 kHz stereo) and build/fx_stem.npy (from score.py). Writes build/score.wav."""
import os, sys
import numpy as np
from scipy import signal
from scipy.ndimage import minimum_filter1d
from scipy.io import wavfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import realm as R

SR = 48000
B = os.path.join(os.path.dirname(HERE), 'build')
sr, tr = wavfile.read(os.path.join(B, 'track.wav'))
tr = tr.astype(np.float64) / 32768
N = int((R.END + R.LEAD) * SR)                                         # film length
fx = np.load(os.path.join(B, 'fx_stem.npy')).astype(np.float64)
vo0, vo1 = np.load(os.path.join(B, 'vo_span.npy'))

# The track plays from its first note under the opener, so its intro (swells at 0.5, 8.25, 13.5, 18.75, 23.75 s)
# carries the trophy and the credits and its drop (26.30 s) lands on the first frame in the clouds. The film from
# there to the title is 42 s shorter than the track from its drop to its final hit, so one jump of 30 bars (5 of the
# track's 6-bar phrases, phrase start to phrase start) inside the full section closes the gap.
BAR = 1.3952                          # 172 bpm, 4/4 (from the onsets: phrase hits at 34.71 and 151.92 s, 84 bars apart)
DROP, STINGER = 26.30, 164.5          # the track's drop and its final hit
JUMP = 30 * BAR
P0 = 0.08                             # track = film + P0 before the jump; splits the 0.14 s residue between drop and title
JSRC = 34.71 + 5 * 6 * BAR            # 76.57 s: a phrase start whose next phrase matches the one 30 bars on most closely
JF = JSRC - P0                        # film time of the jump
XF = int(0.04 * SR)

music = np.zeros((N, 2))
i0 = int(JF * SR)
a = tr[int(P0 * SR):int(P0 * SR) + i0 + XF]
music[:len(a)] += a * np.r_[np.ones(len(a) - XF), np.cos(np.linspace(0, np.pi / 2, XF))][:, None]
s0 = int((JF + P0 + JUMP) * SR)
b = tr[s0:s0 + N - i0]
b = b * np.r_[np.sin(np.linspace(0, np.pi / 2, XF)), np.ones(len(b) - XF)][:, None]
music[i0:i0 + len(b)] += b
DROP_FILM, HIT_FILM = DROP - P0, STINGER - P0 - JUMP

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

# the world: ambience beds well under the music, fly-bys and thunder a few dB under it, always led by it
amb = np.load(os.path.join(B, 'amb_stem.npy')).astype(np.float64)
trans = np.load(os.path.join(B, 'trans_stem.npy')).astype(np.float64)
m_slow = env_rms(music, int(2.0 * SR))
m_fast = env_rms(music, int(0.3 * SR))
amb = amb * (m_slow * 10 ** (-17 / 20))[:, None]
trans = trans * (m_slow * 10 ** (-8 / 20))[:, None]
for x, win, head in ((amb, 0.4, -10), (trans, 0.05, -3)):        # safety: never within `head` dB of the music
    lim_g = np.minimum(1.0, m_fast * 10 ** (head / 20) / (env_rms(x, int(win * SR)) + 1e-9))
    lim_g = movavg(minimum_filter1d(lim_g, int(0.06 * SR)), int(0.03 * SR))   # hold the dips, then smooth them
    x *= np.clip(lim_g, 0, 1)[:, None]

mix = music + fx + vo * 1.0 + amb + trans
if os.environ.get('MIX_REPORT'):
    lvl = lambda x: 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-12)
    L_ = R.LEAD
    for nm, a, b in [('trophy', 0.5, 12.6), ('credits', 13.5, 26.0), ('dive', 26.3, 31.3), ('houses', 24 + L_, 90 + L_),
                     ('storm', 79 + L_, 90 + L_), ('campus', 90 + L_, 101 + L_), ('title', 108 + L_, 118 + L_)]:
        i, j = int(a * SR), int(b * SR)
        print('%-8s music %6.1f  fx %6.1f  amb %6.1f  trans %6.1f  vo %6.1f dB' % (nm, lvl(music[i:j]), lvl(fx[i:j]), lvl(amb[i:j]), lvl(trans[i:j]), lvl(vo[i:j])))
e = np.ones(N)
k0 = int((R.END + R.LEAD - 1.6) * SR)
e[k0:] = np.linspace(1, 0, N - k0) ** 2
mix *= e[:, None]

# the closing line: after the film's own fade, a quiet drone with one soft low hit as the words appear
import soundfile as sf
def sfx(name):
    x, r = sf.read(os.path.join(HERE, 'sfx', name + '.flac'), dtype='float64')
    x = signal.resample_poly(x, SR, r) if r != SR else x
    x = x if x.ndim == 2 else np.stack([x, x], 1)
    return x / np.sqrt((x ** 2).mean() + 1e-12)                      # unit RMS
ref = np.sqrt((music[int((R.TITLE[0] + R.LEAD) * SR):k0] ** 2).mean())
NC = int(R.ROLL * SR)
cred = np.zeros((NC, 2))
bed = sfx('drone_stellar')[:NC - int(0.3 * SR)]
tb = np.arange(len(bed)) / SR
bed *= (np.minimum(tb / 1.8, 1) * np.clip((R.ROLL - 0.6 - tb) / 2.5, 0, 1))[:, None]
cred[int(0.3 * SR):int(0.3 * SR) + len(bed)] += bed * ref * 10 ** (-18 / 20)
hit = sfx('boom_cavernous_a')[:NC - SR]
cred[SR:SR + len(hit)] += hit * ref * 10 ** (-17 / 20) * np.linspace(1, 0, len(hit))[:, None] ** 1.5
mix = np.r_[mix, cred]
mix = np.stack([signal.sosfilt(signal.butter(2, 28, 'high', fs=SR, output='sos'), mix[:, c]) for c in range(2)], 1)
mix = mix / np.abs(mix).max() * 1.15
mix = np.tanh(mix) / np.tanh(1.15) * 0.9
wavfile.write(os.path.join(B, 'score.wav'), SR, (mix * 32767).astype(np.int16))
print('final mix written, %.1f s; track from its top, drop %.2f s on the first cloud frame %.2f s; jump %.2f -> %.2f s at film %.2f; '
      'final hit %.2f s vs title %.2f s' % (len(mix) / SR, DROP, R.OPEN_END, JSRC, JSRC + JUMP, JF, HIT_FILM, R.TITLE[0] + 1.2 + R.LEAD))
