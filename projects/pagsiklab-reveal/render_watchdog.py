"""Render build/scene.blend in short chunks with a watchdog.
A Blender process on the software GL driver can drop into a slow state (40-100 s/frame instead of ~2 s)
and stay there; each chunk runs in a fresh process, and a process that stalls is restarted.
Resumable: finished frames are skipped. usage: python3 render_watchdog.py BLENDER FIRST LAST [CHUNK]"""
import os, sys, time, subprocess, glob

BLENDER, FIRST, LAST = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
CHUNK = int(sys.argv[4]) if len(sys.argv) > 4 else 40
FRAMES, DEPTH = os.environ.get('FRAMES', 'build/v3/frames'), os.environ.get('DEPTH', 'build/v3/depth')
STALL = 20.0          # seconds without a new frame -> restart


def done(f):
    for d in (FRAMES, DEPTH):
        p = f'{d}/{f:05d}.png'
        if not os.path.exists(p) or os.path.getsize(p) < 1000:
            return False
    return True


def clean_partial():
    """remove empty or truncated frames left by a killed process"""
    for d in (FRAMES, DEPTH):
        for p in glob.glob(f'{d}/*.png'):
            if os.path.getsize(p) < 1000:
                os.remove(p)


def log(msg):
    print(time.strftime('%H:%M:%S'), msg, flush=True)


f = FIRST
while f <= LAST:
    if done(f):
        f += 1
        continue
    a = f
    b = min(a + CHUNK - 1, LAST)
    clean_partial()
    cmd = [BLENDER, '-b', os.environ.get('BLEND', 'build/scene.blend'), '--python-expr',
           f'import bpy; s=bpy.context.scene; s.frame_start={a}; s.frame_end={b}; bpy.ops.render.render(animation=True)']
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    last_progress, last_count, t0 = time.time(), -1, time.time()
    while p.poll() is None:
        time.sleep(2)
        count = sum(done(k) for k in range(a, b + 1))
        if count != last_count:
            last_count, last_progress = count, time.time()
        elif time.time() - last_progress > STALL + (25 if count == 0 else 0):   # first frame includes loading
            log(f'chunk {a}-{b}: stalled at {count} frames, restarting')
            p.kill()
            p.wait()
            break
    log(f'chunk {a}-{b}: {sum(done(k) for k in range(a, b + 1))}/{b - a + 1} frames in {time.time() - t0:.0f}s')
    while f <= b and done(f):
        f += 1
clean_partial()
log('all frames done' if all(done(k) for k in range(FIRST, LAST + 1)) else 'finished with gaps')
