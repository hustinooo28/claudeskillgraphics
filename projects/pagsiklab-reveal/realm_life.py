"""Life on the map for scene.py: the guide dragon, floating 3D seat names, and marching armies.
Imported inside Blender after the seats and the camera exist: build(ctx) with the scene's helpers."""
import bpy, bmesh, math, json, os
import numpy as np
from mathutils import Vector, Matrix
import realm as R


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


# ======================================================================== dragon
def _tube(bm, pts, radii, seg=10, flatten=1.0):
    """sweep a ring along a polyline (local x forward) -> closed tube"""
    rings = []
    for k, (p, r) in enumerate(zip(pts, radii)):
        p = Vector(p)
        d = (Vector(pts[min(k + 1, len(pts) - 1)]) - Vector(pts[max(k - 1, 0)])).normalized()
        side = d.cross(Vector((0, 0, 1)))
        if side.length < 1e-4:
            side = Vector((0, 1, 0))
        side.normalize()
        up = side.cross(d).normalized()
        ring = []
        for j in range(seg):
            a = 2 * math.pi * j / seg
            ring.append(bm.verts.new(p + side * math.cos(a) * r + up * math.sin(a) * r * flatten))
        rings.append(ring)
    for a_, b_ in zip(rings[:-1], rings[1:]):
        for j in range(seg):
            bm.faces.new((a_[j], a_[(j + 1) % seg], b_[(j + 1) % seg], b_[j]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])


def build_dragon(ctx):
    """the council's dragon model if it is present, else the procedural wyvern (dragon.py)"""
    import dragon_glb as G
    if os.path.exists(G.GLB):
        root, rig = G.build(ctx)
        return root, ('glb', rig)
    import dragon as DR
    arm = DR.build(ctx)
    return arm, ('proc', arm)


def dragon_path(t, ctx):
    """position (Vector) and mode of the dragon at time t; it leads the camera from seat to seat"""
    SEATS = ctx['SEATS']
    DWELL = R.HOUSE_LEN - 1.3

    def circle(i, u):
        st = SEATS[i]
        cam_a = math.radians([210, 160, 230, 200, 250, 300, 242][i]) + math.radians(55) * u   # the camera's orbit angle
        # patrols in wide banking arcs on the far side of the seat, so it never crosses the lens
        a = cam_a + math.pi + 1.25 * math.sin(2 * math.pi * 0.6 * u)
        rad = 3.0 if i < 6 else 3.6
        z = st['z'] + 2.4 + 0.25 * math.sin(u * 2 * math.pi * 1.5)
        return Vector((st['x'] + rad * math.cos(a), st['y'] + rad * math.sin(a), z))

    if t < R.HOUSE_START:                                   # leads the camera down through the clouds and low over the
        cam = ctx['camera_at']                              # north (ahead and to the right), then peels off to Dragonstone
        a = cam(min(t + 1.8, R.HOUSE_START))[0]
        b = cam(min(t + 2.0, R.HOUSE_START + 0.2))[0]
        fwd = Vector((b.x - a.x, b.y - a.y, 0.0))
        fwd = fwd.normalized() if fwd.length > 1e-6 else Vector((1.0, 0.0, 0.0))
        lead = a + fwd.cross(Vector((0, 0, 1))) * 0.9 + Vector((0, 0, 0.3))
        w = ease((t - 21.6) / (R.HOUSE_START - 21.6))
        return lead.lerp(circle(0, 0.0), w) + Vector((0, 0, 1.5 * math.sin(w * math.pi))), 'fly'
    if t < R.OVERVIEW[0]:
        i = min(int((t - R.HOUSE_START) // R.HOUSE_LEN), 6)
        lt = t - (R.house_window(i)[0] if i < 6 else R.CAMPUS_WIN[0])
        if i == 6:                                          # the campus: circle, spiral down, land on the roof
            st = SEATS[6]
            roof = Vector((st['x'], st['y'] + 0.2, st['z'] + 1.0 + 0.32))
            if lt < 4.5:
                return circle(6, lt / DWELL), 'glide'
            p0 = circle(6, 4.5 / DWELL)
            u = ease((lt - 4.5) / 3.2)
            mid = (p0 + roof) / 2 + Vector((0, 0, 1.2))
            if lt < 7.7:
                return (1 - u) ** 2 * p0 + 2 * (1 - u) * u * mid + u ** 2 * roof, 'land'
            return roof, 'perched'
        if lt < DWELL:
            return circle(i, lt / DWELL), 'glide'
        u = ease(min((lt - DWELL) / (R.HOUSE_LEN - DWELL) * 1.15, 1.0))  # arrives a beat before the camera
        p0, p1 = circle(i, 1.0), circle(i + 1, 0.0)
        mid = (p0 + p1) / 2 + Vector((0, 0, 3.0))
        return (1 - u) ** 2 * p0 + 2 * (1 - u) * u * mid + u ** 2 * p1, 'fly'
    st = SEATS[6]                                           # a new era: it takes off and climbs past the camera
    roof = Vector((st['x'], st['y'] + 0.2, st['z'] + 1.0 + 0.32))
    u = ease((t - R.OVERVIEW[0]) / 4.0)
    return roof.lerp(Vector((st['x'] + 6, st['y'] - 14, 26.0)), u) + Vector((0, 0, 2.5 * math.sin(u * math.pi))), 'fly'


def animate_dragon(ctx, root, wings):
    import dragon as DR, dragon_glb as G
    kind, rig = wings
    FPS, F = R.FPS, ctx['F']
    t0, t1 = R.MAP_IN[0], R.END
    prev_yaw = None
    for fr in range(F(t0), F(t1) + 1):
        t = fr / FPS
        p, mode = dragon_path(t, ctx)
        q, _ = dragon_path(t + 1 / FPS, ctx)
        v = q - p
        if mode == 'perched':
            yaw = prev_yaw if prev_yaw is not None else 0.0
            pitch, bank = (0.15 if kind == 'proc' else 0.0), 0.0
        else:
            yaw = math.atan2(v.y, v.x) if v.length > 1e-5 else (prev_yaw or 0.0)
            if prev_yaw is not None:                         # unwrap so keyframes don't spin
                while yaw - prev_yaw > math.pi:
                    yaw -= 2 * math.pi
                while yaw - prev_yaw < -math.pi:
                    yaw += 2 * math.pi
            horiz = math.hypot(v.x, v.y)
            pitch = math.atan2(v.z, horiz) if horiz > 1e-6 else 0.0
            yaw_rate = (yaw - prev_yaw) * FPS if prev_yaw is not None else 0.0
            bank = max(-0.7, min(0.7, -0.35 * yaw_rate))
        prev_yaw = yaw
        if kind == 'glb':
            bob = G.pose(rig, t, mode, fr)
        else:
            bob = DR.pose(rig, t, mode, fr) * DR.SCALE / 0.62 * 0.8
        root.location = p + Vector((0, 0, bob))
        root.rotation_euler = (bank, -pitch * 0.8 - 0.5 * bob, yaw)
        root.keyframe_insert('location', frame=fr)
        root.keyframe_insert('rotation_euler', frame=fr)
    if kind == 'glb':
        G.finish(rig)


# ======================================================================== floating names
def build_names(ctx):
    mat, link = ctx['mat'], ctx['link']
    font = bpy.data.fonts.load(ctx['font'])
    gold = mat('name_gold', (0.85, 0.66, 0.30))
    names = []
    seats = list(zip([h['seat'] for h in R.HOUSES] + [R.CAMPUS['seat']], ctx['SEATS']))
    for i, (label, st) in enumerate(seats):
        cu = bpy.data.curves.new(f'name_{i}', 'FONT')
        cu.body = label
        cu.font = font
        cu.size = 0.55 if i < 6 else 0.62
        cu.space_character = 1.12
        cu.extrude = 0.05
        cu.bevel_depth = 0.006
        cu.align_x, cu.align_y = 'CENTER', 'CENTER'
        ob = link(bpy.data.objects.new(f'name_{i}', cu))
        ob.data.materials.append(gold)
        ob.rotation_mode = 'XYZ'
        names.append((ob, st))
    return names


def animate_names(ctx, names, cam_pos_at=None):
    """names lie flat on the map, just below each seat (where the painted labels were), hovering a little"""
    FPS, F, ground = R.FPS, ctx['F'], ctx['ground']
    bpy.context.view_layer.update()
    for k, (ob, st) in enumerate(names):
        hw, hh = ob.dimensions.x / 2 + 0.1, ob.dimensions.y / 2 + 0.1
        d = 1.75 if k < 6 else 2.3
        # try below / above / beside the seat; take the spot with the least relief under the whole word
        best = None
        for ox, oy in ((0, -d), (0, d), (d + hw * 0.6, 0), (-d - hw * 0.6, 0), (0, -d - 0.6), (0, d + 0.6)):
            xs = np.linspace(st['x'] + ox - hw, st['x'] + ox + hw, 13)
            ys = np.linspace(st['y'] + oy - hh, st['y'] + oy + hh, 5)
            hs = [ground(a, b) for a in xs for b in ys]
            relief = max(hs) - min(hs)
            if best is None or relief < best[0] - 0.02:
                best = (relief, st['x'] + ox, st['y'] + oy, max(hs))
        _, x, y, base = best
        ob.rotation_euler = (0, 0, 0)
        s0 = R.house_window(k)[0] if k < 6 else R.CAMPUS_WIN[0]
        for fr in range(F(R.MAP_IN[0]), F(R.END) + 1, 3):
            t = fr / FPS
            lt = t - s0
            # this house's own name sinks into the map while the camera settles on it (the lower third names it)
            gone = ease((lt - 1.2) / 1.0) * (1 - ease((lt - (R.HOUSE_LEN - 1.4)) / 0.9))
            ob.location = (x, y, base + 0.14 + 0.035 * math.sin(t * 1.4 + k) - 0.5 * gone)
            sc = max(1 - gone, 0.001)
            ob.scale = (sc, sc, sc)
            ob.keyframe_insert('location', frame=fr)
            ob.keyframe_insert('scale', frame=fr)


# ======================================================================== armies
def build_armies(ctx):
    mat, mesh_obj, ground, F = ctx['mat'], ctx['mesh_obj'], ctx['ground'], ctx['F']
    rng = np.random.default_rng(17)
    h = ctx['height']
    HS = h.shape[0]
    trees = np.array([(x, y) for x, y, z, k in json.load(open(os.path.join(ctx['tex'], 'trees.json')))])
    seats = [hs['pos'] for hs in R.HOUSES] + [R.CAMPUS['pos']]
    steel, wood = mat('army_steel', (0.42, 0.42, 0.44)), ctx['M']['wood']
    banner_mats = {hs['key']: ctx['ROOF'][hs['key']] for hs in R.HOUSES}
    picked = []
    tries = 0
    while len(picked) < 16 and tries < 20000:
        tries += 1
        u, v = rng.uniform(0.15, 0.85), rng.uniform(0.08, 0.9)
        i, j = int(v * HS), int(u * HS)
        if not (0.16 < h[i, j] < 0.30):                       # on land, not in mountains
            continue
        if len(trees) and np.min(np.hypot(trees[:, 0] - u, trees[:, 1] - v)) < 0.03:
            continue
        if min(math.hypot(u - a, v - b) for a, b in seats) < 0.085:
            continue
        if any(math.hypot(u - a, v - b) < 0.07 for a, b in picked):
            continue
        # flat enough for a block of men
        win = h[max(i - 12, 0):i + 12, max(j - 12, 0):j + 12]
        if win.max() - win.min() > 0.05:
            continue
        picked.append((u, v))
    regiments = []
    for n, (u, v) in enumerate(picked):
        cx, cy = R.to_world((u, v))
        nearest = min(range(6), key=lambda k: math.hypot(u - R.HOUSES[k]['pos'][0], v - R.HOUSES[k]['pos'][1]))
        key = R.HOUSES[nearest]['key']
        heading = rng.uniform(0, 2 * math.pi)
        rows, cols = (5, 9) if n % 3 else (4, 7)
        cav = n % 4 == 0                                       # every fourth regiment is cavalry
        sp = 0.085 if not cav else 0.12
        bm_s, bm_b = bmesh.new(), bmesh.new()
        ch, sh_ = math.cos(heading), math.sin(heading)
        for r in range(rows):
            for c in range(cols):
                lx, ly = (r - rows / 2) * sp, (c - cols / 2) * sp
                x, y = cx + lx * ch - ly * sh_ + rng.normal(0, 0.006), cy + lx * sh_ + ly * ch + rng.normal(0, 0.006)
                z = ground(x, y)
                if cav:
                    b = bmesh.ops.create_cube(bm_s, size=1)               # horse
                    bmesh.ops.scale(bm_s, vec=(0.075, 0.025, 0.04), verts=b['verts'])
                    bmesh.ops.rotate(bm_s, cent=(0, 0, 0), matrix=Matrix.Rotation(heading, 3, 'Z'), verts=b['verts'])
                    bmesh.ops.translate(bm_s, vec=(x, y, z + 0.05), verts=b['verts'])
                    zb = z + 0.07
                else:
                    zb = z
                b = bmesh.ops.create_cone(bm_s, cap_ends=True, segments=6, radius1=0.016, radius2=0.012, depth=0.055)   # body
                bmesh.ops.translate(bm_s, vec=(x, y, zb + 0.028), verts=b['verts'])
                b = bmesh.ops.create_uvsphere(bm_s, u_segments=6, v_segments=4, radius=0.011)          # helm
                bmesh.ops.translate(bm_s, vec=(x, y, zb + 0.066), verts=b['verts'])
                b = bmesh.ops.create_cone(bm_s, cap_ends=False, segments=3, radius1=0.0025, radius2=0.0015, depth=0.14)  # spear
                bmesh.ops.translate(bm_s, vec=(x + 0.012 * sh_, y - 0.012 * ch, zb + 0.07), verts=b['verts'])
        # banner bearers at the front corners
        for c in (0, cols - 1):
            lx, ly = (rows / 2 + 0.6) * sp, (c - cols / 2) * sp
            x, y = cx + lx * ch - ly * sh_, cy + lx * sh_ + ly * ch
            z = ground(x, y)
            b = bmesh.ops.create_cone(bm_s, cap_ends=False, segments=3, radius1=0.003, radius2=0.003, depth=0.2)
            bmesh.ops.translate(bm_s, vec=(x, y, z + 0.1), verts=b['verts'])
            b = bmesh.ops.create_cube(bm_b, size=1)
            bmesh.ops.scale(bm_b, vec=(0.004, 0.05, 0.07), verts=b['verts'])
            bmesh.ops.rotate(bm_b, cent=(0, 0, 0), matrix=Matrix.Rotation(heading, 3, 'Z'), verts=b['verts'])
            bmesh.ops.translate(bm_b, vec=(x - 0.025 * sh_, y + 0.025 * ch, z + 0.165), verts=b['verts'])
        o1 = mesh_obj(f'regiment_{n}', bm_s, steel)
        o2 = mesh_obj(f'banners_{n}', bm_b, banner_mats[key])
        o2.parent = o1
        # march slowly forward across the whole film
        o1.keyframe_insert('location', frame=F(R.CLOUD_BREAK))           # (held still before: the dive sees them from afar)
        o1.location = (0.55 * ch, 0.55 * sh_, 0.0)
        o1.keyframe_insert('location', frame=F(R.END))
        for fc in o1.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
        # some regiments camp beside a few tents
        if n % 2 == 0:
            bm_t = bmesh.new()
            for k in range(4):
                a = heading + math.pi + (k - 1.5) * 0.45
                x, y = cx + 0.55 * math.cos(a), cy + 0.55 * math.sin(a)
                b = bmesh.ops.create_cone(bm_t, cap_ends=True, segments=6, radius1=0.07, radius2=0.0, depth=0.11)
                bmesh.ops.translate(bm_t, vec=(x, y, ground(x, y) + 0.055), verts=b['verts'])
            mesh_obj(f'tents_{n}', bm_t, mat(f'tent_{n}', (0.62, 0.55, 0.42)))
        regiments.append(o1)
    print('ARMIES', len(regiments), 'regiments')
    return regiments
