"""Voice-over with Kokoro (local, Apache-2.0) + a Whisper check that every line is intelligible.

Setup (once, ~400 MB):
  python3 -m venv .venv && .venv/bin/pip install kokoro-onnx soundfile numpy scipy faster-whisper
  mkdir -p models && for f in kokoro-v1.0.onnx voices-v1.0.bin; do
    curl -sSL -o models/$f https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f; done

usage: .venv/bin/python tts.py lines.json out_dir [--voice af_heart] [--speed 1.0] [--models models] [--check]
  lines.json: [["key", "Text to speak."], ...]  ->  out_dir/<key>.wav + out_dir/durations.json
Spell acronyms with spaces ("D S S C", "Q R") so they are read letter by letter.
Good voices: af_heart, af_bella (US female), am_michael, am_fenrir (US male), bf_emma, bm_george (UK).
"""
import argparse, json, os
import numpy as np
import soundfile as sf

ap = argparse.ArgumentParser()
ap.add_argument('lines'); ap.add_argument('out')
ap.add_argument('--voice', default='af_heart'); ap.add_argument('--speed', type=float, default=1.0)
ap.add_argument('--models', default='models'); ap.add_argument('--check', action='store_true')
a = ap.parse_args()

from kokoro_onnx import Kokoro
k = Kokoro(os.path.join(a.models, 'kokoro-v1.0.onnx'), os.path.join(a.models, 'voices-v1.0.bin'))
os.makedirs(a.out, exist_ok=True)
lines = json.load(open(a.lines))
dur = {}
for key, text in lines:
    s, sr = k.create(text, voice=a.voice, speed=a.speed, lang='en-us')
    sf.write(os.path.join(a.out, f'{key}.wav'), s, sr)
    dur[key] = round(len(s) / sr, 2)
    print(f'{key:12s} {dur[key]:5.2f}s  {text}')
json.dump(dur, open(os.path.join(a.out, 'durations.json'), 'w'), indent=1)

if a.check:
    from scipy.signal import resample_poly
    from faster_whisper import WhisperModel
    m = WhisperModel('base.en', device='cpu', compute_type='int8')
    for key, text in lines:
        s, sr = sf.read(os.path.join(a.out, f'{key}.wav'), dtype='float32')
        s = resample_poly(s, 16000, sr).astype(np.float32)  # pass audio as an array: avoids PyAV version issues
        segs, _ = m.transcribe(s, beam_size=5)
        print(f'heard {key:6s} | ' + ' '.join(x.text.strip() for x in segs))
