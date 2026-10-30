#!/bin/sh
# Runs after the 3D render: composite, master the audio, mux, make the repo copy, commit and push.
cd "$(dirname "$0")"
until grep -q -E "all frames done|finished with gaps" build/watchdog5.log 2>/dev/null; do sleep 30; done
python3 audio/score.py && python3 audio/final_mix.py || exit 1
echo "composite start $(date +%T)"
PROCS=3 python3 composite.py build/film.mp4 || exit 1
ffmpeg -v error -y -i build/score.wav -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 48000 build/score-norm.wav
ffmpeg -v error -y -i build/film.mp4 -i build/score-norm.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -shortest \
       -movflags +faststart build/PAGSIKLAB-house-reveal-master.mp4
ffmpeg -v error -y -i build/PAGSIKLAB-house-reveal-master.mp4 -c:v libx264 -preset slow -crf 21 -maxrate 5M -bufsize 10M \
       -pix_fmt yuv420p -c:a copy -movflags +faststart PAGSIKLAB-house-reveal.mp4
echo "video done $(date +%T)"
cd ../..
git add projects/pagsiklab-reveal
git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -q -m "pagsiklab-reveal: final film v3: Cycles render, rigged wyvern, recorded SFX, bolder era title (121 s, 1080p)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01SDEdxvUrEa2xjhDxFi7ajW"
git push origin claude/pagsiklab-reveal && echo "pushed $(date +%T)"
