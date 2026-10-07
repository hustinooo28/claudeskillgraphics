#!/usr/bin/env bash
# Two-pass loudnorm: -14 LUFS integrated. TP ceiling -3 dBTP leaves room for AAC overshoot so the delivered MP4 stays <= -1 dBTP. Input: launch_premaster.wav -> launch_mix.wav
set -euo pipefail
cd "$(dirname "$0")/../assets/audio"
J=$(ffmpeg -hide_banner -nostats -i launch_premaster.wav -af loudnorm=I=-14:TP=-3.0:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g() { echo "$J" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
ffmpeg -hide_banner -loglevel error -y -i launch_premaster.wav -af "loudnorm=I=-14:TP=-3.0:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,aresample=48000" -ar 48000 -c:a pcm_s16le launch_mix.wav
ffmpeg -hide_banner -nostats -i launch_mix.wav -af ebur128=peak=true -f null - 2>&1 | grep -E "I:|Peak:" | tail -2
