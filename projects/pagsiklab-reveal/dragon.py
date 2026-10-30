"""The guide dragon: a rigged wyvern (Drogon-like: black scales, ember-red wing membranes, horned head).
build(ctx) -> armature object 'dragon' (local +x forward, +y left, +z up) with skinned meshes parented to it.
pose(arm, t, mode, ...) keys the bones for one frame: wingbeat with fold and wingtip lag, tail sway, jaw, legs."""
import bpy, bmesh, math
import numpy as np
from mathutils import Vector, Quaternion, Matrix

SCALE = 0.5

# ---------------------------------------------------------------- skeleton (rest pose: wings spread, legs down)
SPINE = [(-2.55, 0, 0.0), (-2.0, 0, -0.02), (-1.45, 0, -0.03), (-0.9, 0, -0.02), (-0.35, 0, 0.0),
         (0.25, 0, 0.03), (0.6, 0, 0.09), (0.85, 0, 0.22), (1.08, 0, 0.36), (1.28, 0, 0.42)]
# half width, half height of the body at each spine point; vertical offset of the section centre (deep chest keel)
SECT = [(0.006, 0.006, 0.0), (0.03, 0.034, 0.0), (0.055, 0.062, 0.0), (0.095, 0.105, 0.0), (0.13, 0.14, -0.01),
        (0.155, 0.17, -0.025), (0.155, 0.175, -0.03), (0.1, 0.11, -0.01), (0.08, 0.085, 0.0), (0.072, 0.078, 0.0)]
BONES = [  # name, head, tail, parent   (spine bones follow SPINE)
    ('pelvis', SPINE[4], SPINE[5], None), ('chest', SPINE[5], SPINE[6], 'pelvis'),
    ('neck1', SPINE[6], SPINE[7], 'chest'), ('neck2', SPINE[7], SPINE[8], 'neck1'), ('neck3', SPINE[8], SPINE[9], 'neck2'),
    ('head', SPINE[9], (1.66, 0, 0.36), 'neck3'), ('jaw', (1.30, 0, 0.385), (1.62, 0, 0.30), 'head'),
    ('tail1', SPINE[4], SPINE[3], 'pelvis'), ('tail2', SPINE[3], SPINE[2], 'tail1'),
    ('tail3', SPINE[2], SPINE[1], 'tail2'), ('tail4', SPINE[1], SPINE[0], 'tail3'),
]
SPINE_BONES = ['tail4', 'tail3', 'tail2', 'tail1', 'pelvis', 'chest', 'neck1', 'neck2', 'neck3']   # SPINE segment k -> bone


def wing_pts(s):
    """landmarks of one wing, s = +1 left, -1 right"""
    P = lambda x, y, z: Vector((x, s * y, z))
    return dict(shoulder=P(0.45, 0.13, 0.14), elbow=P(0.22, 0.72, 0.21), wrist=P(0.52, 1.38, 0.23),
                f1=P(0.12, 2.5, 0.17), f2=P(-0.48, 2.36, 0.11), f3=P(-0.98, 1.86, 0.06), f4=P(-1.12, 1.12, 0.03),
                hip=P(-0.5, 0.12, 0.03))


def leg_pts(s):
    P = lambda x, y, z: Vector((x, s * y, z))
    return dict(hip=P(-0.28, 0.13, -0.04), knee=P(-0.14, 0.2, -0.28), ankle=P(-0.36, 0.2, -0.43), toe=P(-0.18, 0.2, -0.47))


def catmull(pts, n):
    pts = [Vector(p) for p in pts]
    P = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(n):
        u = i / (n - 1) * (len(pts) - 1)
        k = min(int(u), len(pts) - 2)
        f = u - k
        p0, p1, p2, p3 = P[k], P[k + 1], P[k + 2], P[k + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3))
    return out, [i / (n - 1) * (len(pts) - 1) for i in range(n)]


def lerp_sect(u):
    k = min(int(u), len(SECT) - 2)
    f = u - k
    f = f * f * (3 - 2 * f)
    return [a + (b - a) * f for a, b in zip(SECT[k], SECT[k + 1])]


class Skin:
    """bmesh + per-vertex bone weights, turned into a skinned mesh object"""
    def __init__(self):
        self.bm = bmesh.new()
        self.w = []

    def v(self, co, weights):
        vert = self.bm.verts.new(co)
        self.w.append(weights)
        return vert

    def obj(self, name, material, arm, smooth=True, subsurf=0):
        me = bpy.data.meshes.new(name)
        self.bm.verts.index_update()
        self.bm.to_mesh(me)
        self.bm.free()
        me.materials.append(material)
        for p in me.polygons:
            p.use_smooth = smooth
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        groups = {}
        for i, wd in enumerate(self.w):
            tot = sum(wd.values()) or 1.0
            for b, x in wd.items():
                if x <= 1e-4:
                    continue
                if b not in groups:
                    groups[b] = ob.vertex_groups.new(name=b)
                groups[b].add([i], x / tot, 'REPLACE')
        ob.parent = arm
        mod = ob.modifiers.new('rig', 'ARMATURE')
        mod.object = arm
        if subsurf:
            ss = ob.modifiers.new('smooth', 'SUBSURF')
            ss.levels, ss.render_levels = subsurf, subsurf
        return ob


def ring_tube(sk, centers, half_w, half_h, weights, seg=14, cap=True):
    """closed elliptical tube through centers (list of Vector); weights: per-ring dict"""
    rings = []
    for k, c in enumerate(centers):
        d = (centers[min(k + 1, len(centers) - 1)] - centers[max(k - 1, 0)]).normalized()
        side = Vector((0, 0, 1)).cross(d)
        if side.length < 1e-4:
            side = Vector((0, 1, 0))
        side.normalize()
        up = d.cross(side).normalized()
        ring = []
        for j in range(seg):
            a = 2 * math.pi * j / seg
            ring.append(sk.v(c + side * math.cos(a) * half_w[k] + up * math.sin(a) * half_h[k], weights[k]))
        rings.append(ring)
    for a_, b_ in zip(rings[:-1], rings[1:]):
        for j in range(seg):
            sk.bm.faces.new((a_[j], b_[j], b_[(j + 1) % seg], a_[(j + 1) % seg]))
    if cap:
        sk.bm.faces.new(rings[0])
        sk.bm.faces.new(list(reversed(rings[-1])))
    return rings


def cone(sk, base, tip, r, weights, seg=6):
    d = (tip - base).normalized()
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 1e-4:
        side = d.cross(Vector((1, 0, 0)))
    side.normalize()
    up = d.cross(side)
    ring = [sk.v(base + (side * math.cos(2 * math.pi * j / seg) + up * math.sin(2 * math.pi * j / seg)) * r, weights) for j in range(seg)]
    t = sk.v(tip, weights)
    for j in range(seg):
        sk.bm.faces.new((ring[j], ring[(j + 1) % seg], t))
    sk.bm.faces.new(list(reversed(ring)))


def spine_weights(u):
    """u = position along SPINE (0..9); segment k belongs to SPINE_BONES[k], blended with its neighbour near the joints"""
    k = min(int(u), len(SPINE_BONES) - 1)
    f = u - k
    w = {SPINE_BONES[k]: 1.0}
    if f < 0.5 and k > 0:
        w[SPINE_BONES[k - 1]] = 0.5 - f
        w[SPINE_BONES[k]] = 0.5 + f
    elif f > 0.5 and k + 1 < len(SPINE_BONES):
        w[SPINE_BONES[k + 1]] = f - 0.5
        w[SPINE_BONES[k]] = 1.5 - f
    return w


# ---------------------------------------------------------------- materials
def materials(mat):
    scales = mat('dragon_scales', (0.06, 0.05, 0.05))
    belly = mat('dragon_belly', (0.22, 0.12, 0.07))
    membrane = mat('dragon_membrane', (0.12, 0.025, 0.02))
    horn = mat('dragon_horn', (0.55, 0.50, 0.44))
    eye = mat('dragon_eye', (1.0, 0.55, 0.1))
    _cycles_dragon(scales, belly, membrane, horn, eye)
    return scales, belly, membrane, horn, eye


def _cycles_dragon(scales, belly, membrane, horn, eye):
    def nodes(m):
        nt = m.node_tree
        return nt, nt.nodes['Principled BSDF']

    # scales: black with a bronze-red sheen in the crevices, voronoi scale bump
    for m, base, edge in ((scales, (0.025, 0.022, 0.024), (0.20, 0.06, 0.03)), (belly, (0.16, 0.08, 0.045), (0.30, 0.16, 0.08))):
        nt, b = nodes(m)
        tc = nt.nodes.new('ShaderNodeTexCoord')
        vor = nt.nodes.new('ShaderNodeTexVoronoi')
        vor.feature = 'DISTANCE_TO_EDGE'
        vor.inputs['Scale'].default_value = 70.0
        nt.links.new(tc.outputs['Object'], vor.inputs['Vector'])
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.0, 0.12
        ramp.color_ramp.elements[0].color = (*edge, 1)
        ramp.color_ramp.elements[1].color = (*base, 1)
        nt.links.new(vor.outputs['Distance'], ramp.inputs['Fac'])
        nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
        bump = nt.nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = 0.55
        bump.inputs['Distance'].default_value = 0.02
        nt.links.new(vor.outputs['Distance'], bump.inputs['Height'])
        nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
        b.inputs['Roughness'].default_value = 0.42
        b.inputs['Specular IOR Level'].default_value = 0.6
    # membrane: thin leathery skin, glows ember-red when the sun is behind it
    nt, b = nodes(membrane)
    b.inputs['Roughness'].default_value = 0.55
    tl = nt.nodes.new('ShaderNodeBsdfTranslucent')
    tl.inputs['Color'].default_value = (0.55, 0.09, 0.03, 1)
    mix = nt.nodes.new('ShaderNodeMixShader')
    mix.inputs['Fac'].default_value = 0.3
    out = nt.nodes['Material Output']
    nt.links.new(b.outputs['BSDF'], mix.inputs[1])
    nt.links.new(tl.outputs['BSDF'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    b.inputs['Base Color'].default_value = (0.12, 0.025, 0.02, 1)
    nt, b = nodes(horn)
    b.inputs['Roughness'].default_value = 0.35
    nt, b = nodes(eye)
    b.inputs['Emission Color'].default_value = (1.0, 0.45, 0.08, 1)
    b.inputs['Emission Strength'].default_value = 6.0


# ---------------------------------------------------------------- build
def build(ctx):
    mat = ctx['mat']
    scales, belly, membrane, horn, eye = materials(mat)

    arm_data = bpy.data.armatures.new('dragon_rig')
    arm = bpy.data.objects.new('dragon', arm_data)
    bpy.context.scene.collection.objects.link(arm)
    arm.show_in_front = False
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_data.edit_bones

    def bone(name, head, tail, parent):
        b = eb.new(name)
        b.head, b.tail = Vector(head), Vector(tail)
        b.roll = 0.0
        if parent:
            b.parent = eb[parent]
            b.use_connect = False
        return b

    for name, hd, tl, par in BONES:
        bone(name, hd, tl, par)
    for s, sn in ((1, 'L'), (-1, 'R')):
        W = wing_pts(s)
        bone('humerus.' + sn, W['shoulder'], W['elbow'], 'chest')
        bone('forearm.' + sn, W['elbow'], W['wrist'], 'humerus.' + sn)
        for k in range(1, 5):
            bone(f'finger{k}.' + sn, W['wrist'], W[f'f{k}'], 'forearm.' + sn)
        Lg = leg_pts(s)
        bone('thigh.' + sn, Lg['hip'], Lg['knee'], 'pelvis')
    bpy.ops.object.mode_set(mode='OBJECT')

    # ---- body: neck, torso, tail as one smooth tube
    sk = Skin()
    cs, us = catmull(SPINE, 90)
    hw, hh, weights, centres = [], [], [], []
    for c, u in zip(cs, us):
        w_, h_, dz = lerp_sect(u)
        hw.append(w_)
        hh.append(h_)
        centres.append(c + Vector((0, 0, dz)))
        weights.append(spine_weights(u))
    ring_tube(sk, centres, hw, hh, weights, seg=16)
    # dorsal spikes: neck to tail tip
    for c, u, h_ in list(zip(centres, us, hh))[4:84:3]:
        size = 0.25 + 0.75 * min(1.0, h_ / 0.2)
        cone(sk, c + Vector((0, 0, h_ * 0.85)), c + Vector((-0.06 * size, 0, h_ + 0.09 * size)), 0.02 * size, spine_weights(u), seg=4)
    body = sk.obj('dragon_body', scales, arm, subsurf=1)

    # ---- belly plates: a slightly wider strip under the chest and belly
    sk = Skin()
    sel = [k for k, u in enumerate(us) if 3.2 < u < 7.2]
    cb = [centres[k] + Vector((0, 0, -hh[k] * 0.12)) for k in sel]
    ring_tube(sk, cb, [hw[k] * 0.86 for k in sel], [hh[k] * 0.93 for k in sel], [weights[k] for k in sel], seg=16)
    sk.obj('dragon_belly', belly, arm, subsurf=1)

    # ---- head: skull + snout, lower jaw, horns, brow spikes, eyes
    sk = Skin()
    hc, hu = catmull([(1.20, 0, 0.42), (1.34, 0, 0.43), (1.48, 0, 0.405), (1.60, 0, 0.375), (1.67, 0, 0.36)], 16)
    prof = [(0.095, 0.082), (0.108, 0.08), (0.072, 0.058), (0.046, 0.04), (0.014, 0.018)]
    hw_ = [np.interp(u, range(5), [p[0] for p in prof]) for u in hu]
    hh_ = [np.interp(u, range(5), [p[1] for p in prof]) for u in hu]
    ring_tube(sk, hc, hw_, hh_, [{'head': 1.0}] * len(hc), seg=14)
    for s in (-1, 1):
        # two great horns swept back, two smaller ones beneath
        hp, _ = catmull([(1.26, s * 0.05, 0.47), (1.12, s * 0.09, 0.54), (0.96, s * 0.12, 0.56), (0.84, s * 0.13, 0.52)], 10)
        ring_tube(sk, hp, list(np.linspace(0.024, 0.003, 10)), list(np.linspace(0.024, 0.003, 10)), [{'head': 1.0}] * 10, seg=7)
        hp, _ = catmull([(1.24, s * 0.08, 0.40), (1.12, s * 0.12, 0.42), (1.00, s * 0.15, 0.40)], 8)
        ring_tube(sk, hp, list(np.linspace(0.016, 0.002, 8)), list(np.linspace(0.016, 0.002, 8)), [{'head': 1.0}] * 8, seg=6)
        for k in range(4):                                   # brow and cheek spikes
            cone(sk, Vector((1.40 - k * 0.05, s * (0.075 + 0.006 * k), 0.455 - 0.012 * k)),
                 Vector((1.36 - k * 0.07, s * (0.1 + 0.01 * k), 0.49 - 0.01 * k)), 0.008, {'head': 1.0}, seg=4)
    sk.obj('dragon_head', scales, arm, subsurf=1)
    sk = Skin()
    jc, ju = catmull([(1.26, 0, 0.385), (1.40, 0, 0.37), (1.52, 0, 0.345), (1.62, 0, 0.32)], 12)
    ring_tube(sk, jc, list(np.interp(ju, range(4), [0.07, 0.055, 0.038, 0.014])),
              list(np.interp(ju, range(4), [0.035, 0.03, 0.022, 0.012])), [{'jaw': 1.0}] * 12, seg=10)
    for k in range(7):                                       # teeth
        x = 1.36 + k * 0.035
        for s in (-1, 1):
            cone(sk, Vector((x, s * (0.04 - k * 0.003), 0.388 - k * 0.011)), Vector((x + 0.004, s * (0.04 - k * 0.003), 0.415 - k * 0.011)), 0.005, {'jaw': 1.0}, seg=4)
    sk.obj('dragon_jaw', scales, arm, subsurf=1)
    sk = Skin()
    for k in range(7):
        x = 1.38 + k * 0.035
        for s in (-1, 1):
            cone(sk, Vector((x, s * (0.045 - k * 0.003), 0.392 - k * 0.011)), Vector((x - 0.003, s * (0.045 - k * 0.003), 0.365 - k * 0.011)), 0.005, {'head': 1.0}, seg=4)
    sk.obj('dragon_teeth', horn, arm, smooth=False)
    sk = Skin()
    for s in (-1, 1):
        r = bmesh.ops.create_uvsphere(sk.bm, u_segments=10, v_segments=6, radius=0.017)
        for vv in r['verts']:
            vv.co += Vector((1.415, s * 0.078, 0.438))
            sk.w.append({'head': 1.0})
    sk.obj('dragon_eyes', eye, arm)

    # ---- wings: arm and finger bones (thin tubes) + membrane panels
    for s, sn in ((1, 'L'), (-1, 'R')):
        W = wing_pts(s)
        hum, fore = 'humerus.' + sn, 'forearm.' + sn
        fing = [f'finger{k}.' + sn for k in range(1, 5)]
        sk = Skin()
        ring_tube(sk, [W['shoulder'], (W['shoulder'] + W['elbow']) / 2, W['elbow']], [0.05, 0.04, 0.032], [0.045, 0.035, 0.03],
                  [{'chest': 0.5, hum: 0.5}, {hum: 1.0}, {hum: 0.5, fore: 0.5}], seg=8)
        ring_tube(sk, [W['elbow'], (W['elbow'] + W['wrist']) / 2, W['wrist']], [0.032, 0.025, 0.022], [0.03, 0.022, 0.02],
                  [{hum: 0.5, fore: 0.5}, {fore: 1.0}, {fore: 1.0}], seg=8)
        for k in range(1, 5):
            tip = W[f'f{k}']
            pts = [W['wrist'] + (tip - W['wrist']) * f for f in (0.0, 0.35, 0.7, 1.0)]
            ring_tube(sk, pts, [0.016, 0.012, 0.008, 0.002], [0.014, 0.01, 0.007, 0.002],
                      [{fore: 0.6, fing[k - 1]: 0.4}, {fing[k - 1]: 1.0}, {fing[k - 1]: 1.0}, {fing[k - 1]: 1.0}], seg=6)
        cone(sk, W['wrist'], W['wrist'] + Vector((0.1, s * 0.03, 0.05)), 0.014, {fore: 1.0}, seg=5)          # thumb claw
        sk.obj('dragon_wingbones_' + sn, scales, arm, subsurf=0)

        sk = Skin()
        NS, NC = 10, 7

        def grid(pt, wt):
            vs = [[sk.v(pt(i / NS, j / NC), wt(i / NS, j / NC)) for j in range(NC + 1)] for i in range(NS + 1)]
            for i in range(NS):
                for j in range(NC):
                    q = (vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1])
                    sk.bm.faces.new(q if s > 0 else tuple(reversed(q)))

        def arm_line(u):                                     # shoulder -> elbow -> wrist
            return W['shoulder'].lerp(W['elbow'], u * 2) if u < 0.5 else W['elbow'].lerp(W['wrist'], (u - 0.5) * 2)

        def billow(p, a, b, u):                              # membrane sags a little below the straight line
            return p + Vector((0, 0, -0.06 * math.sin(math.pi * u) * a * b))

        # inner panel: arm leading edge, body + finger4 trailing edge
        def inner_pt(u, c):
            lead = arm_line(u)
            trail = W['hip'].lerp(W['f4'], u)
            trail = trail.lerp(lead, 0.16 * math.sin(math.pi * u))            # scalloped trailing edge
            return billow(lead.lerp(trail, c), math.sin(math.pi * c), 1.0, u)

        def inner_w(u, c):
            a = {hum: (1 - c) * max(0.0, 1 - 2 * u), fore: (1 - c) * min(1.0, 2 * u)}
            a['pelvis'] = c * (1 - u) * 0.6
            a['chest'] = c * (1 - u) * 0.4
            a[fing[3]] = c * u
            return a
        grid(inner_pt, inner_w)

        # outer panels between neighbouring fingers, fanning from the wrist
        for k in range(3):
            fa, fb = W[f'f{k + 1}'], W[f'f{k + 2}']

            def outer_pt(r, v, fa=fa, fb=fb):
                pa, pb = W['wrist'].lerp(fa, r), W['wrist'].lerp(fb, r)
                p = pa.lerp(pb, v)
                p = p.lerp(W['wrist'], 0.17 * math.sin(math.pi * v) * r ** 2.5)   # scallop between the fingertips
                return billow(p, math.sin(math.pi * v), r, 0.5)

            def outer_w(r, v, k=k):
                return {fing[k]: (1 - v) * max(r, 0.05), fing[k + 1]: v * max(r, 0.05), fore: max(0.0, 0.25 - r)}
            grid(outer_pt, outer_w)
        sk.obj('dragon_membrane_' + sn, membrane, arm, smooth=True)

    # ---- hind legs with talons (tucked back in flight)
    sk = Skin()
    for s, sn in ((1, 'L'), (-1, 'R')):
        Lg = leg_pts(s)
        th = 'thigh.' + sn
        ring_tube(sk, [Lg['hip'], Lg['knee'], Lg['ankle'], Lg['toe']], [0.07, 0.04, 0.026, 0.02], [0.08, 0.04, 0.026, 0.016],
                  [{'pelvis': 0.5, th: 0.5}, {th: 1.0}, {th: 1.0}, {th: 1.0}], seg=8)
        for k in (-1, 0, 1):
            cone(sk, Lg['toe'] + Vector((0.0, k * 0.02, 0)), Lg['toe'] + Vector((0.07, k * 0.035, -0.03)), 0.008, {th: 1.0}, seg=4)
    sk.obj('dragon_legs', scales, arm, subsurf=1)

    arm.scale = (SCALE, SCALE, SCALE)
    arm.rotation_mode = 'XYZ'
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
    return arm


# ---------------------------------------------------------------- posing
def _rot(pb, axis_angles):
    """rotation about armature-space axes (applied in order), expressed in the bone's own rest frame"""
    Q = Quaternion()
    for axis, ang in axis_angles:
        Q = Quaternion(Vector(axis), ang) @ Q
    R = pb.bone.matrix_local.to_quaternion()
    pb.rotation_quaternion = R.inverted() @ Q @ R


ROAR = [(97.2, 99.2), (101.2, 102.9)]


def pose(arm, t, mode, fr):
    P = arm.pose.bones
    if mode == 'fly':
        amp, freq, bias = 0.62, 1.6, 0.08
    elif mode == 'glide':
        amp, freq, bias = 0.42, 1.2, 0.14
    elif mode == 'land':
        amp, freq, bias = 0.72, 2.2, 0.15
    else:
        amp = None
    ph = 2 * math.pi * (freq if amp else 1.0) * t
    stroke = math.sin(ph + 0.45 * math.sin(ph))              # +1 top of the upstroke, -1 bottom of the downstroke
    up = max(0.0, math.cos(ph))                              # how much of the recovery stroke we are in
    for s, sn in ((1, 'L'), (-1, 'R')):
        hum, fore = P['humerus.' + sn], P['forearm.' + sn]
        if amp is not None:
            e = bias + amp * stroke
            _rot(hum, [((1, 0, 0), s * e), ((0, 0, 1), s * 0.18 * up)])
            _rot(fore, [((0, 0, 1), s * 0.32 * up), ((1, 0, 0), s * 0.2 * math.sin(ph - 0.7))])
            for k in range(1, 5):
                lag = 0.32 * math.sin(ph - 1.1 - 0.15 * k)
                fan = -s * 0.22 * up * (k - 1) / 3               # the fan closes on the way up
                _rot(P[f'finger{k}.' + sn], [((1, 0, 0), s * lag), ((0, 0, 1), fan)])
            _rot(P['thigh.' + sn], [((0, 1, 0), 1.25 if mode != 'land' else 0.35)])
        else:                                                # perched: wings folded along the flanks, legs down
            _rot(hum, [((0, 0, 1), s * 1.0), ((1, 0, 0), s * 0.55)])
            _rot(fore, [((0, 0, 1), -s * 2.1), ((1, 0, 0), -s * 0.3)])
            for k in range(1, 5):
                _rot(P[f'finger{k}.' + sn], [((0, 0, 1), s * (1.5 + 0.12 * k)), ((1, 0, 0), -s * 0.25)])
            _rot(P['thigh.' + sn], [((0, 1, 0), 0.0)])
    # tail: a travelling wave, slower than the wings
    for k, b in enumerate(('tail1', 'tail2', 'tail3', 'tail4')):
        _rot(P[b], [((0, 0, 1), 0.13 * math.sin(0.45 * ph - 0.7 * k)), ((0, 1, 0), 0.07 * math.sin(ph - 0.9 * k - 0.5) - 0.04)])
    # neck keeps the head steady against the body's bob; the jaw opens on the roars
    _rot(P['neck1'], [((0, 1, 0), 0.06 * math.sin(ph + math.pi))])
    _rot(P['neck2'], [((0, 1, 0), 0.04 * math.sin(ph + math.pi)), ((0, 0, 1), 0.05 * math.sin(0.3 * ph))])
    _rot(P['neck3'], [((0, 1, 0), -0.05)])
    jaw = 0.0
    for a, b in ROAR:
        if a <= t <= b:
            u = (t - a) / (b - a)
            jaw = 0.5 * min(1.0, u / 0.15) * min(1.0, (1 - u) / 0.25)
    _rot(P['jaw'], [((0, 1, 0), jaw)])
    for pb in P:
        pb.keyframe_insert('rotation_quaternion', frame=fr)
    return -0.09 * stroke if amp is not None else 0.0
