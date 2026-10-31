"""Screen-space sea horizon for the low run, from the camera itself (blender -b build/scene.blend -P horizon.py).

The compositor's horizon glow needs the line where the visible sea ends (the depth pass stops at 150 units); fitting
it from the depth pass jitters whenever hills hide the sea, so project it from the animated camera instead."""
import bpy, json, math, os, sys
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import realm as R

sc = bpy.context.scene
cam = sc.camera
out = {}
for f in range(round(R.CLOUD_BREAK * R.FPS) - 24, round(R.HOUSE_START * R.FPS) + 1):
    sc.frame_set(f)
    co = cam.matrix_world.translation
    fwd = cam.matrix_world.to_3x3() @ Vector((0, 0, -1))
    yaw = math.atan2(fwd.y, fwd.x)
    pts = []
    for k in range(-40, 41):
        a = yaw + math.radians(k)
        p = Vector((co.x + 148 * math.cos(a), co.y + 148 * math.sin(a), 0.0))
        v = world_to_camera_view(sc, cam, p)
        if v.z > 0 and -0.5 < v.x < 1.5:
            pts.append((v.x * 1920, (1 - v.y) * 1080))
    if len(pts) >= 2:
        n = len(pts); mx = sum(p[0] for p in pts) / n; my = sum(p[1] for p in pts) / n
        sxx = sum((p[0] - mx) ** 2 for p in pts); sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
        k_ = sxy / sxx if sxx else 0.0
        out[f] = (k_, my - k_ * mx)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build', 'horizon.json'), 'w'))
print('horizon frames', len(out))
