"""Blender scene for the PAGSIKLAB house reveal (GoT-opening-titles style), rendered with Workbench.
Run:  blender -b --factory-startup -P scene.py -- [--frames A-B | --stills f1,f2,...] [--out DIR] [--res 1080]
Frames are global video frames at 24 fps (frame 0 = video start); the 3D part covers MAP_IN..TITLE."""
import bpy, bmesh, sys, os, math, json
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import realm as R

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default

FPS = R.FPS
F = lambda t: int(round(t * FPS))
TEX = os.path.join(HERE, 'build', 'tex')
rng = np.random.default_rng(5)

# ---------------- scene / render ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
res = int(arg('--res', '1080'))
sc.render.resolution_x, sc.render.resolution_y = res * 16 // 9, res
sc.render.fps = FPS
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'
sh.studio_light = 'outdoor.sl'
sh.use_world_space_lighting = True
sh.studiolight_rotate_z = math.radians(-35)
sh.color_type = 'TEXTURE'
sh.show_shadows = True
sh.shadow_intensity = 0.55
sh.show_cavity = True
sh.cavity_type = 'BOTH'
sh.cavity_ridge_factor = 0.6
sh.cavity_valley_factor = 1.0
sh.curvature_ridge_factor = 0.5
sh.curvature_valley_factor = 0.7
sh.show_specular_highlight = True
sc.display.light_direction = (-0.45, 0.55, 0.70)
sc.display.shadow_shift = 0.05
sc.display.shadow_focus = 0.4
sc.display.render_aa = 'FXAA'
world = bpy.data.worlds.new('W')
sc.world = world
world.color = (0.035, 0.04, 0.05)
sc.render.image_settings.file_format = 'PNG'
sc.view_settings.view_transform = 'Standard'     # keep texture colours exact; the look is graded in compositing
sc.render.film_transparent = False


def mat(name, rgb, tex=None):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    if tex:
        n = m.node_tree.nodes.new('ShaderNodeTexImage')
        n.image = bpy.data.images.load(tex)
        m.node_tree.links.new(n.outputs['Color'], bsdf.inputs['Base Color'])
        m.node_tree.nodes.active = n
    return m


M = dict(
    stone=mat('stone', (0.62, 0.60, 0.57)), dark=mat('darkstone', (0.22, 0.21, 0.22)),
    sand=mat('sand', (0.83, 0.64, 0.42)), wood=mat('wood', (0.42, 0.26, 0.15)),
    brass=mat('brass', (0.78, 0.56, 0.26)), steel=mat('steel', (0.55, 0.57, 0.60)),
    copper=mat('copper', (0.66, 0.36, 0.20)), snowtree=mat('snowtree', (0.72, 0.78, 0.78)),
    greentree=mat('greentree', (0.18, 0.30, 0.17)),
)
ROOF = {h['key']: mat('roof_' + h['key'], h['color']) for h in R.HOUSES}


def link(ob):
    sc.collection.objects.link(ob)
    return ob


def mesh_obj(name, bm, material):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    for p in me.polygons:
        p.use_smooth = False
    return link(bpy.data.objects.new(name, me))


# ---------------- terrain ----------------
h = np.load(os.path.join(HERE, 'build/tex/height.npy'))
HS = h.shape[0]
HEIGHT_SCALE = 1.0
N = 400
bm = bmesh.new()
bm.loops.layers.uv.new('UVMap')          # create_grid only writes UVs into an existing layer
bmesh.ops.create_grid(bm, x_segments=N, y_segments=N, size=R.MAP_SIZE / 2, calc_uvs=True)
for v in bm.verts:
    u = (v.co.x / R.MAP_SIZE) + 0.5
    vv = 0.5 - v.co.y / R.MAP_SIZE
    i, j = min(max(int(vv * HS), 0), HS - 1), min(max(int(u * HS), 0), HS - 1)
    v.co.z = float(h[i, j]) * HEIGHT_SCALE
terrain = mesh_obj('terrain', bm, mat('map', (1, 1, 1), os.path.join(TEX, 'color.png')))
for p in terrain.data.polygons:
    p.use_smooth = True


# open sea to the horizon, just under the map's sea level
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=400)
bmesh.ops.translate(bm, vec=(0, 0, -0.01), verts=bm.verts)
mesh_obj('sea', bm, mat('sea', (0.052, 0.084, 0.112)))      # matches the sea painted at the map's edge


def ground(x, y):
    u, vv = x / R.MAP_SIZE + 0.5, 0.5 - y / R.MAP_SIZE
    i, j = min(max(int(vv * HS), 0), HS - 1), min(max(int(u * HS), 0), HS - 1)
    return float(h[i, j]) * HEIGHT_SCALE


# ---------------- trees ----------------
trees = json.load(open(os.path.join(TEX, 'trees.json')))
for kind in ('snow', 'green'):
    bm = bmesh.new()
    for x, y, z, k in trees:
        if k != kind:
            continue
        wx, wy = (x - 0.5) * R.MAP_SIZE, (0.5 - y) * R.MAP_SIZE
        s = rng.uniform(0.7, 1.3)
        res_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.07 * s, radius2=0, depth=0.26 * s)
        bmesh.ops.translate(bm, verts=res_['verts'], vec=(wx, wy, z * HEIGHT_SCALE + 0.13 * s))
    mesh_obj('trees_' + kind, bm, M['snowtree' if kind == 'snow' else 'greentree'])


# ---------------- part builders (local coords, base at z=0) ----------------
def bm_box(sx, sy, sz):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(0, 0, sz / 2), verts=bm.verts)
    return bm


def bm_cyl(r, hgt, seg=24):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=hgt)
    bmesh.ops.translate(bm, vec=(0, 0, hgt / 2), verts=bm.verts)
    return bm


def bm_cone(r, hgt, seg=16):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=0, depth=hgt)
    bmesh.ops.translate(bm, vec=(0, 0, hgt / 2), verts=bm.verts)
    return bm


def bm_dome(r):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=r)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-4], context='VERTS')
    return bm


def bm_gear(r, teeth, thick, hole=0.25):
    bm = bmesh.new()
    pts = []
    n = teeth * 4
    for k in range(n):
        a = 2 * math.pi * k / n
        rr = r * (1.0 if (k % 4) in (1, 2) else 0.84)
        pts.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), 0)))
    f = bm.faces.new(pts)
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, vec=(0, 0, thick), verts=[e for e in ext['geom'] if isinstance(e, bmesh.types.BMVert)])
    hub = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=r * hole, radius2=r * hole, depth=thick * 1.8)
    bmesh.ops.translate(bm, vec=(0, 0, thick / 2), verts=hub['verts'])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def merlons(bm_parent, r, z, n, size):
    """crenellation ring around a round tower"""
    for k in range(n):
        a = 2 * math.pi * k / n
        b = bmesh.ops.create_cube(bm_parent, size=1)
        bmesh.ops.scale(bm_parent, vec=(size, size, size * 1.3), verts=b['verts'])
        bmesh.ops.translate(bm_parent, vec=(r * math.cos(a), r * math.sin(a), z + size * 0.65), verts=b['verts'])


def flag(hgt):
    """thin pole with a pennant, base at z=0"""
    bm = bm_cyl(0.008, hgt, 6)
    b = bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.scale(bm, vec=(0.16, 0.006, 0.09), verts=b['verts'])
    bmesh.ops.translate(bm, vec=(0.08, 0, hgt - 0.05), verts=b['verts'])
    return bm


def tower(r, hgt, roof=True, crenel=True):
    bm = bm_cyl(r, hgt, 20)
    if crenel:
        merlons(bm, r * 0.92, hgt, 10, r * 0.28)
    parts = [(bm, 'wall')]
    if roof:
        parts.append((bm_cone(r * 1.12, hgt * 0.55), 'roof', hgt))
        parts.append((flag(0.28), 'roof', hgt + hgt * 0.5))
    return parts


def wall(length, hgt, thick=0.12):
    bm = bm_box(length, thick, hgt)
    n = max(int(length / 0.18), 2)
    for k in range(n):
        if k % 2:
            continue
        b = bmesh.ops.create_cube(bm, size=1)
        bmesh.ops.scale(bm, vec=(length / n * 0.9, thick * 1.1, 0.07), verts=b['verts'])
        bmesh.ops.translate(bm, vec=(-length / 2 + (k + 0.5) * length / n, 0, hgt + 0.035), verts=b['verts'])
    return bm


# ---------------- castles ----------------
SEATS = []   # per house: list of dict(ob, base_z, delay)


def place(key, bm, material, x, y, z=0.0, rot=0.0, delay=0.0, spin=False):
    ob = mesh_obj(f'{key}_{len(bpy.data.objects)}', bm, material)
    ob.location = (x, y, z)
    ob.rotation_euler.z = rot
    return dict(ob=ob, z=z, delay=delay, spin=spin)


def build_house(i, hs):
    key = hs['key']
    cx, cy = R.to_world(hs['pos'])
    gz = ground(cx, cy)
    roof, stone = ROOF[key], M['stone']
    parts = []
    st = hs['style']

    def P(bm, material, x, y, z=0.0, rot=0.0, d=0.0):
        parts.append(place(key, bm, material, cx + x, cy + y, gz + z, rot, d))

    def T(r, hgt, x, y, d, material=None, roofed=True, z=0.0):
        for item in tower(r, hgt, roof=roofed):
            bmx, kind = item[0], item[1]
            zz = z + (item[2] if len(item) > 2 else 0)
            P(bmx, (material or stone) if kind == 'wall' else roof, x, y, zz, 0, d + (0.25 if kind == 'roof' else 0))

    # gears under every castle: they rise first and keep turning
    for k, (gx, gy, gr, gt) in enumerate(((-1.05, -0.75, 0.42, 12), (0.95, -0.85, 0.32, 9), (0.15, 1.05, 0.36, 10), (-0.95, 0.75, 0.24, 8))):
        g = place(key, bm_gear(gr, gt, 0.07), M['brass'] if k % 2 == 0 else M['steel'], cx + gx, cy + gy, gz + 0.02, 0, k * 0.15, spin=(1 if k % 2 else -1) * (0.9 / gr))
        parts.append(g)

    if st == 'keep':                      # Winterfell: square curtain wall, round corner towers, great keep
        L = 1.7
        for k, (x, y, rot) in enumerate(((0, L / 2, 0), (0, -L / 2, 0), (L / 2, 0, math.pi / 2), (-L / 2, 0, math.pi / 2))):
            P(wall(L, 0.32), stone, x, y, 0, rot, 0.8 + k * 0.1)
        for k, (x, y) in enumerate(((L / 2, L / 2), (-L / 2, L / 2), (L / 2, -L / 2), (-L / 2, -L / 2))):
            T(0.17, 0.55, x, y, 1.2 + k * 0.1)
        P(bm_box(0.75, 0.55, 0.62), stone, -0.15, 0.1, 0, 0, 1.6)
        T(0.15, 0.95, 0.35, 0.25, 1.9)
        T(0.12, 0.75, -0.45, -0.35, 2.0)
        P(bm_box(0.4, 0.3, 0.3), M['wood'], 0.3, -0.45, 0, 0.2, 2.1)
    elif st == 'rock':                    # Casterly Rock: a great rock with towers on top
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
        for v in bm.verts:
            n = 0.85 + 0.3 * math.sin(v.co.x * 5.1 + v.co.y * 3.3) * math.cos(v.co.z * 4.2)
            v.co = Vector((v.co.x * 1.05 * n, v.co.y * 0.85 * n, max(v.co.z, -0.1) * 0.95 * n))
        bmesh.ops.translate(bm, vec=(0, 0, 0.1), verts=bm.verts)
        P(bm, M['sand'], 0, 0, -0.05, 0.3, 0.6)
        for k, (x, y, r, hh) in enumerate(((0.0, 0.0, 0.17, 0.9), (0.38, 0.2, 0.12, 0.6), (-0.35, 0.18, 0.12, 0.55), (0.1, -0.35, 0.1, 0.5))):
            T(r, hh, x, y, 1.4 + k * 0.15, z=0.75)
        P(wall(1.2, 0.18), stone, 0, 0.0, 0.75, 0.5, 1.9)
    elif st == 'rings':                   # Highgarden: concentric ring walls, green roofs
        for ring_i, (rr, hh, n) in enumerate(((1.25, 0.18, 16), (0.85, 0.26, 12), (0.48, 0.34, 8))):
            for k in range(n):
                a = 2 * math.pi * (k + 0.5) / n
                seg = 2 * rr * math.sin(math.pi / n)
                P(wall(seg * 1.02, hh, 0.09), stone, rr * math.cos(a), rr * math.sin(a), 0, a + math.pi / 2, 0.6 + ring_i * 0.5 + k * 0.03)
            for k in range(0, n, 4 if n > 8 else 2):
                a = 2 * math.pi * k / n
                T(0.1, hh + 0.2, rr * math.cos(a), rr * math.sin(a), 0.8 + ring_i * 0.5 + k * 0.03)
        T(0.2, 1.0, 0, 0, 2.2)
    elif st == 'drum':                    # Storm's End: one colossal drum tower
        P(bm_cyl(1.0, 0.25, 40), stone, 0, 0, 0, 0, 0.6)
        bm = bm_cyl(0.72, 1.35, 40)
        merlons(bm, 0.68, 1.35, 20, 0.12)
        P(bm, M['dark'], 0, 0, 0.25, 0, 1.0)
        P(bm_cyl(0.6, 0.06, 40), M['dark'], 0, 0, 1.6, 0, 1.6)
        for k in range(5):
            a = math.radians(200 + k * 28)
            T(0.1, 0.45, 1.0 * math.cos(a), 1.0 * math.sin(a), 1.8 + k * 0.08)
    elif st == 'domes':                   # Sunspear: sandstone blocks, domes, a slender spire
        for k, (x, y, sx, sy, hh) in enumerate(((-0.4, -0.2, 0.7, 0.5, 0.35), (0.35, -0.3, 0.5, 0.6, 0.28), (0.1, 0.45, 0.9, 0.4, 0.3), (-0.6, 0.5, 0.4, 0.4, 0.22))):
            P(bm_box(sx, sy, hh), M['sand'], x, y, 0, 0, 0.6 + k * 0.15)
        for k, (x, y, r, z) in enumerate(((-0.4, -0.2, 0.22, 0.35), (0.35, -0.3, 0.2, 0.28), (0.1, 0.45, 0.17, 0.3))):
            P(bm_dome(r), roof, x, y, z, 0, 1.4 + k * 0.15)
        P(bm_cyl(0.09, 1.25, 16), M['sand'], 0.75, 0.25, 0, 0, 1.8)
        P(bm_dome(0.11), roof, 0.75, 0.25, 1.25, 0, 2.1)
        P(wall(2.0, 0.16, 0.08), M['sand'], 0, -0.85, 0, 0, 1.0)
    elif st == 'dragonstone':             # Dragonstone: black spires and a dragon-crowned keep
        P(bm_box(0.9, 0.7, 0.55), M['dark'], 0, 0, 0, 0.2, 0.6)
        for k in range(9):
            a = 2 * math.pi * k / 9 + 0.3
            rr = 0.55 + 0.35 * (k % 2)
            hh = 0.55 + 0.6 * ((k * 37) % 5) / 5
            P(bm_cone(0.11, hh, 6), M['dark'], rr * math.cos(a), rr * math.sin(a), 0.0, 0, 0.9 + k * 0.1)
        T(0.2, 1.15, 0, 0, 1.6, M['dark'])
        P(wall(1.6, 0.2), M['dark'], 0, -0.75, 0, 0, 1.0)

    # pedestal + medallion (sigil coin) high above the castle
    ped_d = 2.6
    P(bm_cyl(0.18, 0.06, 24), M['brass'], 1.55, 1.25, 0, 0, ped_d - 0.4)
    pole = place(key, bm_cyl(0.035, 1.9, 12), M['brass'], cx + 1.55, cy + 1.25, gz, 0, ped_d - 0.3)
    parts.append(pole)
    medal = build_medal(key, cx + 1.55, cy + 1.25, gz + 2.2)
    parts.append(dict(ob=medal, z=gz + 2.2, delay=ped_d, medal=True))
    SEATS.append(dict(key=key, x=cx, y=cy, z=gz, parts=parts, medal=medal))


def build_medal(key, x, y, z):
    """coin: brass rim + textured faces; stands upright, rotates about Z"""
    rim = bpy.data.objects.new('medal_' + key, None)
    link(rim)
    rim.location = (x, y, z)
    bm = bm_cyl(0.5, 0.08, 48)
    bmesh.ops.translate(bm, vec=(0, 0, -0.04), verts=bm.verts)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=__import__('mathutils').Matrix.Rotation(math.pi / 2, 3, 'X'), verts=bm.verts)
    coin = mesh_obj('coin_' + key, bm, M['brass'])
    coin.parent = rim
    face_mat = mat('face_' + key, (1, 1, 1), os.path.join(TEX, f'sigil_{key}.png'))
    for side in (-1, 1):
        bm = bmesh.new()
        seg = 64
        vs = [bm.verts.new((0.47 * math.cos(2 * math.pi * k / seg), 0, 0.47 * math.sin(2 * math.pi * k / seg))) for k in range(seg)]
        f = bm.faces.new(vs if side < 0 else list(reversed(vs)))
        uv = bm.loops.layers.uv.new()
        for loop in f.loops:
            co = loop.vert.co
            loop[uv].uv = ((co.x * -side) / 0.94 + 0.5, co.z / 0.94 + 0.5)
        bmesh.ops.translate(bm, vec=(0, side * 0.0415, 0), verts=bm.verts)
        face = mesh_obj(f'face_{key}_{side}', bm, face_mat)
        face.parent = rim
    return rim


for i, hs in enumerate(R.HOUSES):
    build_house(i, hs)


def bm_plane_uv(w, h):
    """vertical plane facing -y with UVs 0..1, base at z=0"""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    vs = [bm.verts.new(c) for c in ((-w / 2, 0, 0), (w / 2, 0, 0), (w / 2, 0, h), (-w / 2, 0, h))]
    f = bm.faces.new(vs)
    for loop, c in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv].uv = c
    return bm


def build_campus():
    """DSSC Sta. Cruz Extension Campus: white neoclassical front, portico, balcony, blue sign, palms"""
    cx, cy = R.to_world(R.CAMPUS['pos'])
    gz = ground(cx, cy)
    parts = []
    white, glass = mat('campus_white', (0.90, 0.90, 0.87)), mat('campus_glass', (0.10, 0.13, 0.16))
    blue, palm = mat('campus_blue', (0.10, 0.27, 0.66)), mat('palm', (0.20, 0.38, 0.16))
    sign = mat('campus_sign', (1, 1, 1), os.path.join(TEX, 'campus_sign.png'))

    def P(bm, material, x, y, z=0.0, rot=0.0, d=0.0):
        parts.append(place('campus', bm, material, cx + x, cy + y, gz + z, rot, d))

    for k, (gx, gy, gr, gt) in enumerate(((-1.6, 0.6, 0.42, 12), (1.55, 0.7, 0.32, 9), (-1.2, -1.45, 0.3, 9), (1.3, -1.4, 0.26, 8))):
        parts.append(place('campus', bm_gear(gr, gt, 0.07), M['brass'] if k % 2 == 0 else M['steel'],
                           cx + gx, cy + gy, gz + 0.02, 0, k * 0.15, spin=(1 if k % 2 else -1) * (0.9 / gr)))
    P(bm_box(3.0, 2.0, 0.03), mat('paving', (0.70, 0.69, 0.66)), 0, -0.2, 0, 0, 0.4)
    P(bm_box(2.0, 1.0, 0.95), white, 0, 0.2, 0, 0, 0.6)                         # main block
    for sx in (-1, 1):
        P(bm_box(0.75, 0.9, 0.72), white, sx * 1.35, 0.25, 0, 0, 0.8)            # wings
        P(bm_box(0.6, 0.02, 0.2), glass, sx * 1.35, -0.21, 0.42, 0, 1.0)
        P(bm_box(0.6, 0.02, 0.2), glass, sx * 1.35, -0.21, 0.1, 0, 1.0)
    # portico: two round columns in the middle, square pillars at the corners
    for k, x in enumerate((-0.45, -0.15, 0.15, 0.45)):
        if abs(x) > 0.3:
            P(bm_box(0.13, 0.13, 0.5), white, x, -0.62, 0.03, 0, 1.2 + k * 0.08)
        else:
            P(bm_cyl(0.05, 0.5, 16), white, x, -0.62, 0.03, 0, 1.2 + k * 0.08)
    P(bm_box(0.32, 0.02, 0.38), glass, 0, -0.31, 0.03, 0, 1.3)                    # entrance
    P(bm_box(1.1, 0.45, 0.07), white, 0, -0.5, 0.53, 0, 1.6)                    # entablature / balcony floor
    P(bm_box(1.1, 0.03, 0.11), white, 0, -0.71, 0.6, 0, 1.7)                    # balustrade rail
    for k in range(9):
        P(bm_cyl(0.012, 0.1, 6), white, -0.48 + k * 0.12, -0.70, 0.6, 0, 1.75)
    crest = bm_cyl(0.09, 0.03, 20)
    bmesh.ops.rotate(crest, cent=(0, 0, 0), matrix=__import__('mathutils').Matrix.Rotation(math.pi / 2, 3, 'X'), verts=crest.verts)
    P(crest, white, 0, -0.72, 0.78, 0, 1.85)
    P(bm_box(1.5, 0.02, 0.24), glass, 0, -0.31, 0.62, 0, 1.9)                    # upper windows
    P(bm_box(2.1, 1.1, 0.05), white, 0, 0.2, 0.95, 0, 2.0)                      # roof slab
    P(bm_box(1.9, 0.12, 0.27), blue, 0, -0.33, 0.97, 0, 2.2)                    # sign band
    P(bm_plane_uv(1.86, 0.25), sign, 0, -0.395, 0.98, 0, 2.2)
    for k, (x, y) in enumerate(((-1.25, -0.85), (1.2, -0.95), (-0.85, -1.15))):  # palm trees
        P(bm_cyl(0.025, 0.9, 8), M['wood'], x, y, 0, 0, 2.4 + k * 0.1)
        for j in range(6):
            leaf = bm_box(0.32, 0.06, 0.015)
            bmesh.ops.translate(leaf, vec=(0.16, 0, 0), verts=leaf.verts)
            bmesh.ops.rotate(leaf, cent=(0, 0, 0), matrix=__import__('mathutils').Matrix.Rotation(-0.35, 3, 'Y'), verts=leaf.verts)
            P(leaf, palm, x, y, 0.88, j * math.pi / 3, 2.5 + k * 0.1)
    P(bm_cyl(0.18, 0.06, 24), M['brass'], 1.55, 1.25, 0, 0, 2.2)
    parts.append(place('campus', bm_cyl(0.035, 1.9, 12), M['brass'], cx + 1.55, cy + 1.25, gz, 0, 2.3))
    medal = build_medal('campus', cx + 1.55, cy + 1.25, gz + 2.2)
    parts.append(dict(ob=medal, z=gz + 2.2, delay=2.6, medal=True))
    SEATS.append(dict(key='campus', x=cx, y=cy, z=gz, parts=parts, medal=medal))


build_campus()


# ---------------- animation ----------------
def key_build(seat, t0):
    """parts rise out of the ground, staggered by their delay; gears spin forever after"""
    for p in seat['parts']:
        ob = p['ob']
        ts = t0 + p['delay']
        dims = ob.dimensions if ob.type == 'MESH' else Vector((1, 1, 1))
        drop = (p['z'] - (seat['z'] - dims.z - 0.3)) if not p.get('medal') else 3.2
        if p.get('medal'):
            ob.location.z = p['z'] - drop
            ob.rotation_euler.z = math.radians(-540)
            ob.keyframe_insert('location', index=2, frame=F(ts))
            ob.keyframe_insert('rotation_euler', index=2, frame=F(ts))
            ob.location.z = p['z']
            ob.keyframe_insert('location', index=2, frame=F(ts + 1.6))
            ob.rotation_euler.z = math.radians(0)
            ob.keyframe_insert('rotation_euler', index=2, frame=F(ts + 2.1))
            continue
        ob.location.z = p['z'] - drop
        ob.keyframe_insert('location', index=2, frame=F(ts))
        ob.location.z = p['z'] + 0.04
        ob.keyframe_insert('location', index=2, frame=F(ts + 0.55))
        ob.location.z = p['z']
        ob.keyframe_insert('location', index=2, frame=F(ts + 0.75))
        if p.get('spin'):
            ob.rotation_euler.z = 0
            ob.keyframe_insert('rotation_euler', index=2, frame=F(ts))
            ob.rotation_euler.z = p['spin'] * (R.END - ts)
            ob.keyframe_insert('rotation_euler', index=2, frame=F(R.END))
            for fc in ob.animation_data.action.fcurves:
                if fc.data_path == 'rotation_euler':
                    for kp in fc.keyframe_points:
                        kp.interpolation = 'LINEAR'


BUILD_AT = 0.7      # seconds into a house window when its castle starts assembling
for i, seat in enumerate(SEATS):
    s = R.house_window(i)[0] if i < 6 else R.CAMPUS_WIN[0]
    key_build(seat, s + BUILD_AT)

# ---------------- camera ----------------
cam_data = bpy.data.cameras.new('cam')
cam_data.lens = 32
cam_data.clip_start, cam_data.clip_end = 0.05, 400
cam_data.dof.use_dof = True
cam_data.dof.aperture_fstop = float(arg('--fstop', '0.28'))
cam = link(bpy.data.objects.new('cam', cam_data))
sc.camera = cam
tgt = link(bpy.data.objects.new('target', None))
con = cam.constraints.new('TRACK_TO')
con.target, con.track_axis, con.up_axis = tgt, 'TRACK_NEGATIVE_Z', 'UP_Y'
cam_data.dof.focus_object = tgt


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def seat_pose(i, u):
    """orbit around seat i; u in 0..1 over the house's dwell time"""
    st = SEATS[i]
    a0 = math.radians([210, 160, 230, 200, 250, 300, 242][i])
    a = a0 + math.radians(55) * u
    k = 1.45 if i == 6 else 1.0          # the campus is bigger than a castle
    d = (8.0 - 2.6 * ease(u)) * k
    hgt = (3.6 - 1.0 * ease(u)) * k
    tz = st['z'] + 0.35 + 1.6 * ease((u - 0.45) / 0.55)
    cxp = st['x'] + d * math.cos(a)
    cyp = st['y'] + d * math.sin(a)
    tx = st['x'] + 0.55 * ease((u - 0.45) / 0.55)
    ty = st['y'] + 0.45 * ease((u - 0.45) / 0.55)
    return Vector((cxp, cyp, st['z'] + hgt)), Vector((tx, ty, tz))


DWELL = R.HOUSE_LEN - 1.3          # last 1.3 s of each window is the flight to the next seat
OVER_CAM = (Vector((0.0, -26.0, 30.0)), Vector((0.0, -1.0, 0.0)))
OVER_CAM2 = (Vector((0.0, -18.0, 24.0)), Vector((0.0, 1.0, 0.0)))
START_CAM = (Vector((10.0, -34.0, 38.0)), Vector((6.0, 0.0, 0.0)))


def bez(p0, p1, u, lift):
    m = (p0 + p1) / 2 + Vector((0, 0, lift))
    return (1 - u) ** 2 * p0 + 2 * (1 - u) * u * m + u ** 2 * p1


def camera_at(t):
    if t < R.HOUSE_START:                                   # descend onto the realm, glide to Dragonstone
        u = ease((t - R.MAP_IN[0]) / (R.HOUSE_START - R.MAP_IN[0]))
        c1, t1 = seat_pose(0, 0.0)
        return bez(START_CAM[0], c1, u, 4.0), bez(START_CAM[1], t1, u, 0.0)
    if t < R.OVERVIEW[0]:
        i = min(int((t - R.HOUSE_START) // R.HOUSE_LEN), 6)          # 6 = the campus
        lt = t - (R.house_window(i)[0] if i < 6 else R.CAMPUS_WIN[0])
        if lt < DWELL:
            return seat_pose(i, lt / DWELL)
        u = ease((lt - DWELL) / (R.HOUSE_LEN - DWELL))
        c0, t0 = seat_pose(i, 1.0)
        c1, t1 = seat_pose(i + 1, 0.0) if i < 6 else OVER_CAM
        return bez(c0, c1, u, 3.5), bez(t0, t1, u, 1.0)
    u = ease((t - R.OVERVIEW[0]) / (R.END - R.OVERVIEW[0]))
    return OVER_CAM[0].lerp(OVER_CAM2[0], u), OVER_CAM[1].lerp(OVER_CAM2[1], u)


for fr in range(F(R.MAP_IN[0]), F(R.END) + 1):
    c, tg = camera_at(fr / FPS)
    gmin = ground(c.x, c.y) + 0.6
    if c.z < gmin:
        c.z = gmin
    cam.location, tgt.location = c, tg
    cam.keyframe_insert('location', frame=fr)
    tgt.keyframe_insert('location', frame=fr)
    cam_data.dof.focus_distance = (c - tg).length
    cam_data.dof.keyframe_insert('focus_distance', frame=fr)

sc.frame_start, sc.frame_end = F(R.MAP_IN[0]), F(R.END)

# ---------------- output ----------------
out = arg('--out', os.path.join(HERE, 'build', 'frames'))
os.makedirs(out, exist_ok=True)
if '--save' in argv:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'build', 'scene.blend'))
# depth pass for atmospheric fog in compositing: 16-bit PNG, 0..150 units -> 0..1 (sky = 1)
sc.view_layers[0].use_pass_z = True
sc.use_nodes = True
nt = sc.node_tree
rl, comp = nt.nodes['Render Layers'], nt.nodes['Composite']
mr = nt.nodes.new('CompositorNodeMapRange')
mr.inputs['From Min'].default_value, mr.inputs['From Max'].default_value = 0.0, 150.0
mr.inputs['To Min'].default_value, mr.inputs['To Max'].default_value = 0.0, 1.0
mr.use_clamp = True
fo = nt.nodes.new('CompositorNodeOutputFile')
fo.base_path = os.path.join(os.path.dirname(out.rstrip('/')), 'depth') + '/'
fo.format.file_format, fo.format.color_mode, fo.format.color_depth = 'PNG', 'BW', '16'
fo.file_slots[0].path = '#####'
nt.links.new(rl.outputs['Depth'], mr.inputs['Value'])
nt.links.new(mr.outputs['Value'], fo.inputs[0])
nt.links.new(rl.outputs['Image'], comp.inputs['Image'])

if '--profile' in argv:
    import time
    sc.frame_set(600)
    sc.render.filepath = os.path.join(out, 'prof.png')
    base = dict(shadows=sh.show_shadows, cavity=sh.show_cavity, dof=cam_data.dof.use_dof, aa=sc.display.render_aa)
    def setcfg(c):
        sh.show_shadows, sh.show_cavity, cam_data.dof.use_dof, sc.display.render_aa = c['shadows'], c['cavity'], c['dof'], c['aa']
    tests = [('all on', {}), ('no shadows', dict(shadows=False)), ('no cavity', dict(cavity=False)),
             ('no dof', dict(dof=False)), ('aa 5', dict(aa='5')), ('aa fxaa', dict(aa='FXAA')),
             ('bare', dict(shadows=False, cavity=False, dof=False, aa='FXAA'))]
    for name, ch in tests:
        setcfg({**base, **ch})
        bpy.ops.render.render(write_still=True)          # warm-up
        t = time.time(); bpy.ops.render.render(write_still=True)
        print('PROF', name, '%.2fs' % (time.time() - t), flush=True)
    t = time.time(); sc.frame_set(601); print('PROF frame_set', '%.2fs' % (time.time() - t), flush=True)
elif '--stills' in argv:
    for fr in [int(x) for x in arg('--stills').split(',')]:
        sc.frame_set(fr)
        sc.render.filepath = os.path.join(out, f'{fr:05d}.png')
        bpy.ops.render.render(write_still=True)
        print('STILL', fr, flush=True)
elif '--frames' in argv:
    a, b = [int(x) for x in arg('--frames').split('-')]
    sc.frame_start, sc.frame_end = a, b
    sc.render.filepath = os.path.join(out, '#####')
    sc.render.use_overwrite = False
    bpy.ops.render.render(animation=True)
