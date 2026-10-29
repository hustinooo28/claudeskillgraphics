"""Opening shot: a gold trophy on a stone pedestal in a dark hall, slow dolly-in (frames 0..119 = 0-5 s).
Run: blender -b --factory-startup -P intro_trophy.py -- [--stills 0,60,119] [--res 1080]"""
import bpy, bmesh, sys, os, math
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def arg(n, d=None): return argv[argv.index(n) + 1] if n in argv else d

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
res = int(arg('--res', '1080'))
sc.render.resolution_x, sc.render.resolution_y = res * 16 // 9, res
sc.render.fps = 24
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light, sh.studio_light = 'STUDIO', 'rim.sl'
sh.use_world_space_lighting = True
sh.color_type = 'MATERIAL'
sh.show_shadows, sh.shadow_intensity = True, 0.7
sh.show_cavity, sh.cavity_type = True, 'BOTH'
sh.show_specular_highlight = True
sc.display.light_direction = (0.25, 0.35, 0.9)
sc.display.render_aa = 'FXAA'
sc.view_settings.view_transform = 'Standard'
sc.world = bpy.data.worlds.new('W')
sc.world.color = (0.004, 0.004, 0.005)


def mat(name, rgb):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    return m


GOLD, STONE, BLACK, PLATE = mat('gold', (0.80, 0.52, 0.16)), mat('stone', (0.10, 0.095, 0.09)), mat('black', (0.02, 0.02, 0.02)), mat('plate', (0.9, 0.75, 0.4))


def obj(name, bm, m, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    o.location = loc
    return o


def box(sx, sy, sz, z0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(0, 0, z0 + sz / 2), verts=bm.verts)
    return bm


def lathe(profile, seg=64):
    """profile: list of (radius, z) from bottom to top"""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        ring = [bm.verts.new((r * math.cos(2 * math.pi * k / seg), r * math.sin(2 * math.pi * k / seg), z)) for k in range(seg)]
        rings.append(ring)
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(seg):
            bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


# hall floor and pedestal
obj('floor', box(40, 40, 0.1, -0.1), STONE)
obj('plinth_base', box(1.3, 1.3, 0.15, 0.0), STONE)
obj('plinth', box(1.0, 1.0, 0.95, 0.15), STONE)
obj('plinth_cap', box(1.2, 1.2, 0.1, 1.10), STONE)
# trophy base
Z0 = 1.2
obj('t_base1', box(0.46, 0.46, 0.10, Z0), BLACK)
obj('t_base2', box(0.38, 0.38, 0.08, Z0 + 0.10), BLACK)
obj('t_plate', box(0.24, 0.005, 0.05, Z0 + 0.03), PLATE, (0, -0.232, 0))
# the cup
cup = [(0.15, 0), (0.15, 0.025), (0.11, 0.04), (0.05, 0.07), (0.035, 0.18), (0.075, 0.21), (0.075, 0.23), (0.035, 0.26),
       (0.03, 0.31), (0.06, 0.34), (0.13, 0.40), (0.19, 0.48), (0.215, 0.58), (0.225, 0.66), (0.235, 0.68), (0.20, 0.69),
       (0.17, 0.74), (0.10, 0.79), (0.04, 0.82), (0.03, 0.86)]
obj('cup', lathe(cup), GOLD, (0, 0, Z0 + 0.18))
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=0.045)
obj('finial', bm, GOLD, (0, 0, Z0 + 0.18 + 0.90))
for side in (-1, 1):                       # handles: half tori standing on the cup's sides
    bm = bmesh.new()
    seg, rs = 32, 10
    R1, R2 = 0.12, 0.022
    rings = []
    for i in range(seg + 1):
        a = -math.pi / 2 + math.pi * i / seg
        c = Vector((R1 * math.cos(a), 0, R1 * math.sin(a)))
        ring = []
        for j in range(rs):
            b = 2 * math.pi * j / rs
            n = Vector((math.cos(a) * math.cos(b), math.sin(b), math.sin(a) * math.cos(b)))
            ring.append(bm.verts.new(c + n * R2))
        rings.append(ring)
    for a_, b_ in zip(rings[:-1], rings[1:]):
        for j in range(rs):
            bm.faces.new((a_[j], a_[(j + 1) % rs], b_[(j + 1) % rs], b_[j]))
    if side < 0:
        bmesh.ops.scale(bm, vec=(-1, 1, 1), verts=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj(f'handle{side}', bm, GOLD, (side * 0.17, 0, Z0 + 0.18 + 0.56))

# camera: low, slow dolly-in with a slight arc
cam_data = bpy.data.cameras.new('cam')
cam_data.lens = 50
cam_data.dof.use_dof = True
cam_data.dof.aperture_fstop = 1.4
cam = bpy.data.objects.new('cam', cam_data)
sc.collection.objects.link(cam)
sc.camera = cam
tgt = bpy.data.objects.new('t', None)
sc.collection.objects.link(tgt)
c_ = cam.constraints.new('TRACK_TO')
c_.target, c_.track_axis, c_.up_axis = tgt, 'TRACK_NEGATIVE_Z', 'UP_Y'
cam_data.dof.focus_object = tgt
for f in range(0, 121):
    u = f / 120
    e = u * u * (3 - 2 * u) * 0.6 + u * 0.4
    a = math.radians(-100 + 14 * e)
    d = 5.2 - 1.9 * e
    cam.location = (d * math.cos(a), d * math.sin(a), 1.05 + 0.35 * e)
    tgt.location = (0, 0, 1.55 + 0.1 * e)
    cam.keyframe_insert('location', frame=f)
    tgt.keyframe_insert('location', frame=f)

out = arg('--out', os.path.join(HERE, 'build', 'trophy'))
os.makedirs(out, exist_ok=True)
sc.view_layers[0].use_pass_z = True
sc.use_nodes = True
nt = sc.node_tree
rl, comp = nt.nodes['Render Layers'], nt.nodes['Composite']
mr = nt.nodes.new('CompositorNodeMapRange')
mr.inputs['From Min'].default_value, mr.inputs['From Max'].default_value = 0.0, 20.0
mr.use_clamp = True
fo = nt.nodes.new('CompositorNodeOutputFile')
fo.base_path = os.path.join(HERE, 'build', 'trophy_depth') + '/'
fo.format.file_format, fo.format.color_mode, fo.format.color_depth = 'PNG', 'BW', '16'
fo.file_slots[0].path = '#####'
nt.links.new(rl.outputs['Depth'], mr.inputs['Value'])
nt.links.new(mr.outputs['Value'], fo.inputs[0])
nt.links.new(rl.outputs['Image'], comp.inputs['Image'])
if '--stills' in argv:
    for f in [int(x) for x in arg('--stills').split(',')]:
        sc.frame_set(f)
        sc.render.filepath = os.path.join(out, f'{f:05d}.png')
        bpy.ops.render.render(write_still=True)
else:
    sc.frame_start, sc.frame_end = 0, 120
    sc.render.filepath = os.path.join(out, '#####')
    bpy.ops.render.render(animation=True)
