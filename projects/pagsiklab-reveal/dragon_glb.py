"""The guide dragon from the council's model (assets/dragon/black_dragon.glb: a black dragon with an idle animation).
The idle loop always plays underneath (breathing, face, toes); a flight layer on top beats the wings, tucks the
legs, sways the tail and opens the jaw on the roars, and fades out when the dragon lands so it settles into its idle.
build(ctx) -> (root, rig); root is an empty with local +x forward, +z up, keyed by realm_life.animate_dragon."""
import bpy, math, os
from mathutils import Vector, Matrix, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(HERE, 'assets', 'dragon', 'black_dragon.glb')
SCALE = 0.11                     # rest wingspan ~27.5 model units -> ~3 map units
CENTRE = Vector((0.0, 0.6, 2.7))  # body centre in the model's frame (faces -y, +z up, its left is +x)
ROAR = [(97.2, 99.2), (101.2, 102.9)]


class Rig:
    pass


def _material(o):
    """the model's wings are shaded as metal; make them leathery membranes (deep red-black, glowing when backlit)"""
    m = o.data.materials[0]
    nt = m.node_tree
    b = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if b is None:
        return
    for k in ('Metallic',):
        for l in list(b.inputs[k].links):
            nt.links.remove(l)
    if m.name == 'Game_dragon':                           # the wing membranes
        b.inputs['Metallic'].default_value = 0.0
        for l in list(b.inputs['Roughness'].links):
            nt.links.remove(l)
        b.inputs['Roughness'].default_value = 0.7
        src = b.inputs['Base Color'].links[0].from_socket
        mul = nt.nodes.new('ShaderNodeMix')
        mul.data_type, mul.blend_type = 'RGBA', 'MULTIPLY'
        mul.inputs['Factor'].default_value = 1.0
        mul.inputs['B'].default_value = (0.30, 0.09, 0.07, 1)
        nt.links.new(src, mul.inputs['A'])
        nt.links.new(mul.outputs['Result'], b.inputs['Base Color'])
        out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        shader = out.inputs['Surface'].links[0].from_socket
        tl = nt.nodes.new('ShaderNodeBsdfTranslucent')
        tl.inputs['Color'].default_value = (0.5, 0.08, 0.03, 1)
        mix = nt.nodes.new('ShaderNodeMixShader')
        mix.inputs['Fac'].default_value = 0.25
        nt.links.new(shader, mix.inputs[1])
        nt.links.new(tl.outputs['BSDF'], mix.inputs[2])
        nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
        ss = o.modifiers.new('smooth', 'SUBSURF')            # the membrane mesh is low-poly: smooth it after the rig
        ss.levels = ss.render_levels = 2
    else:
        b.inputs['Metallic'].default_value = 0.1


def build(ctx):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=GLB, guess_original_bind_pose=False)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:                                         # the model ships with a ground plane and a helper sphere
        if o.name.startswith(('Plane', 'Icosphere')) and o.type == 'MESH':
            bpy.data.objects.remove(o, do_unlink=True)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == 'ARMATURE')
    for o in new:
        if o.type == 'MESH' and o.data.materials:
            _material(o)
    top = next(o for o in new if o.parent is None)
    idle = arm.animation_data.action if arm.animation_data else None
    bpy.context.view_layer.update()

    # model frame -> armature space (for rotation axes and pivots)
    Mw = arm.matrix_world.copy()
    R3 = Mw.to_3x3().normalized()
    to_arm = lambda v: (R3.inverted() @ Vector(v)).normalized()
    pt_arm = lambda p: Mw.inverted() @ Vector(p)
    rig = Rig()
    rig.arm, rig.idle = arm, idle
    rig.F, rig.U, rig.L = to_arm((0, -1, 0)), to_arm((0, 0, 1)), to_arm((1, 0, 0))   # forward, up, left

    # hierarchy: root (keyed, +x forward) -> orient (turns the model to face +x, scales, centres) -> model
    root = bpy.data.objects.new('dragon', None)
    bpy.context.scene.collection.objects.link(root)
    root.rotation_mode = 'XYZ'
    orient = bpy.data.objects.new('dragon_orient', None)
    bpy.context.scene.collection.objects.link(orient)
    orient.parent = root
    orient.matrix_basis = Matrix.Rotation(math.pi / 2, 4, 'Z') @ Matrix.Scale(SCALE, 4) @ Matrix.Translation(-CENTRE)
    mw_top = top.matrix_world.copy()
    top.parent = orient
    top.matrix_parent_inverse = Matrix.Identity(4)
    top.matrix_basis = mw_top                            # keeps the import transform under the new parent

    # the idle loop runs underneath for the whole film
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = None
    if idle is not None:
        tr = ad.nla_tracks.new()
        tr.name = 'idle'
        a0, a1 = idle.frame_range
        st = tr.strips.new('idle', int(a0), idle)
        st.repeat = 30.0
        st.blend_type = 'REPLACE'
    rig.flight = bpy.data.actions.new('dragon_flight')
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'

    # pivots for the legs (feet are separate bones under the root joint, so they are carried by hand)
    B = arm.data.bones
    rig.legs = []
    for thigh, foot in (('Oberschenkel_L', 'back_food_L_'), ('Oberschenkel_R', 'back_food_R_'),
                        ('upper_arm_L', 'Hand_L'), ('upper_arm_R', 'Hand_R')):
        tb = next(b for b in B if b.name.startswith(thigh))
        fb = next(b for b in B if b.name.startswith(foot) and '.001' not in b.name)
        rig.legs.append((tb.name, fb.name, tb.head_local.copy(), 1.15 if thigh.startswith('Ober') else 0.95))
    name = lambda p: next(b.name for b in B if b.name.startswith(p))
    rig.wing = {s: dict(root=name(f'w_C_{sn}_'), fore=name(f'w2_{sn}'), tip=name(f'w3_{sn}_'), mid=name(f'w5_{sn}'),
                        midtip=name(f'w6_{sn}'), inner=name(f'w8_{sn}'), innertip=name(f'w9_{sn}'))
                for s, sn in ((1, 'L'), (-1, 'R'))}
    rig.tail = [name(f'tail_{k}') for k in (1, 2, 3)]
    rig.neck = [name(f'ACT_neck_{k}') for k in (4, 3, 2)]
    rig.jaw = name('Bone_024')

    # the flight layer: its own NLA track above the idle, influence keyed (1 in flight, 0 perched)
    fl_tr = ad.nla_tracks.new()
    fl_tr.name = 'flight'
    rig.flight_track = fl_tr
    rig.keys = []                                        # (frame, influence)
    return root, rig


def _rot(pb, axis_angles):
    """rotation about armature-space axes, expressed in the bone's rest frame (so it composes down the chain)"""
    Q = Quaternion()
    for axis, ang in axis_angles:
        Q = Quaternion(axis, ang) @ Q
    R = pb.bone.matrix_local.to_quaternion()
    pb.rotation_quaternion = R.inverted() @ Q @ R


def _carry(pb, pivot, Q):
    """move a foot bone (parented to the unposed root joint) as if it hung from a limb rotated by Q about pivot"""
    Mr = pb.bone.matrix_local
    T = Matrix.Translation(pivot) @ Q.to_matrix().to_4x4() @ Matrix.Translation(-pivot)
    pb.matrix_basis = Mr.inverted() @ T @ Mr


def pose(rig, t, mode, fr):
    arm, P = rig.arm, rig.arm.pose.bones
    F, U, L = rig.F, rig.U, rig.L
    if mode == 'fly':
        amp, freq, bias = 0.62, 1.5, 0.05
    elif mode == 'glide':
        amp, freq, bias = 0.45, 1.15, 0.1
    elif mode == 'land':
        amp, freq, bias = 0.72, 2.1, 0.12
    else:
        amp, freq, bias = 0.0, 1.0, 0.0
    ph = 2 * math.pi * freq * t
    stroke = math.sin(ph + 0.45 * math.sin(ph))          # +1 top of the upstroke, -1 bottom of the downstroke
    up = max(0.0, math.cos(ph))                          # recovery stroke
    for s, w in rig.wing.items():
        e = bias + amp * stroke
        _rot(P[w['root']], [(F, s * e), (U, s * 0.22 * up * (amp > 0))])
        _rot(P[w['fore']], [(U, s * 0.16 * up * (amp > 0)), (F, s * 0.12 * math.sin(ph - 0.7) * (amp > 0))])
        lag = 0.2 * math.sin(ph - 1.2) * (amp > 0)
        for k in ('tip', 'midtip', 'innertip'):
            _rot(P[w[k]], [(F, s * lag)])
    tuck = 1.0 if mode in ('fly', 'glide') else 0.35
    for thigh, foot, pivot, ang in rig.legs:
        Q = Quaternion(L, ang * tuck)
        _rot(P[thigh], [(L, ang * tuck)])
        _carry(P[foot], pivot, Q)
    for k, b in enumerate(rig.tail):
        _rot(P[b], [(U, 0.12 * math.sin(0.45 * ph - 0.7 * k)), (L, 0.06 * math.sin(ph - 0.9 * k - 0.5))])
    for k, b in enumerate(rig.neck):
        _rot(P[b], [(L, -0.05 * math.sin(ph + math.pi) - (0.12 if k == 0 else 0.0))])
    jaw = 0.0
    for a, b in ROAR:
        if a <= t <= b:
            u = (t - a) / (b - a)
            jaw = 0.45 * min(1.0, u / 0.15) * min(1.0, (1 - u) / 0.25)
    _rot(P[rig.jaw], [(L, jaw)])

    # write the flight layer's keys for this frame into its action
    keyed = [w[k] for w in rig.wing.values() for k in w] + [l[0] for l in rig.legs] + [l[1] for l in rig.legs] \
        + rig.tail + rig.neck + [rig.jaw]
    ad = arm.animation_data
    ad.action = rig.flight
    for n in keyed:
        P[n].keyframe_insert('rotation_quaternion', frame=fr)
        if n in [l[1] for l in rig.legs]:
            P[n].keyframe_insert('location', frame=fr)
    ad.action = None
    rig.keys.append((fr, 0.0 if mode == 'perched' else 1.0))
    return -0.06 * stroke if amp > 0 else 0.0


def finish(rig):
    """put the flight action on its NLA track, with its influence easing to 0 for the perch and back to 1 for take-off"""
    fr0 = rig.keys[0][0]
    st = rig.flight_track.strips.new('flight', fr0, rig.flight)
    st.blend_type = 'REPLACE'
    st.use_animated_influence = True
    inf = [k[1] for k in rig.keys]
    # ease every change over 12 frames so the wings fold and the legs drop smoothly
    sm = []
    for i in range(len(inf)):
        a, b = max(0, i - 6), min(len(inf), i + 7)
        sm.append(sum(inf[a:b]) / (b - a))
    for (fr, _), v in zip(rig.keys, sm):
        st.influence = v
        st.keyframe_insert('influence', frame=fr)
