"""Cycles look for scene.py: sun + sky light, physically based materials (masonry, polished brass, glossy water),
bevelled castle edges, motion blur and a denoised low-sample render that a 4-core CPU can finish overnight."""
import bpy, math
from mathutils import Vector


def _nodes(m):
    nt = m.node_tree
    return nt, nt.nodes['Principled BSDF']


def _coords(nt, kind='Object'):
    return nt.nodes.new('ShaderNodeTexCoord').outputs[kind]


def _noise(nt, vec, scale, detail=4.0):
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    nt.links.new(vec, n.inputs['Vector'])
    return n


def _bump(nt, b, height, strength, distance=0.02):
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = strength
    bp.inputs['Distance'].default_value = distance
    nt.links.new(height, bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return bp


def _tint(nt, b, fac, lo, hi):
    """base colour = noise-driven blend between two shades of the material's colour"""
    rgb = b.inputs['Base Color'].default_value[:3]
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*[c * lo for c in rgb], 1)
    ramp.color_ramp.elements[1].color = (*[min(c * hi, 1) for c in rgb], 1)
    nt.links.new(fac, ramp.inputs['Fac'])
    return ramp


def masonry(m, scale=26.0, mortar=0.55, windows=False):
    """stone blocks in courses: brick texture on (x + y, z) so every wall orientation gets courses"""
    nt, b = _nodes(m)
    if b.inputs['Base Color'].is_linked:
        return
    co = _coords(nt)
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(co, sep.inputs[0])
    add = nt.nodes.new('ShaderNodeMath')
    add.operation = 'ADD'
    nt.links.new(sep.outputs['X'], add.inputs[0])
    nt.links.new(sep.outputs['Y'], add.inputs[1])
    comb = nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(add.outputs[0], comb.inputs['X'])
    nt.links.new(sep.outputs['Z'], comb.inputs['Y'])
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Scale'].default_value = scale
    br.inputs['Mortar Size'].default_value = 0.018
    br.inputs['Brick Width'].default_value = 0.6
    br.inputs['Row Height'].default_value = 0.22
    rgb = b.inputs['Base Color'].default_value[:3]
    br.inputs['Color1'].default_value = (*rgb, 1)
    br.inputs['Color2'].default_value = (*[c * 0.82 for c in rgb], 1)
    br.inputs['Mortar'].default_value = (*[c * mortar for c in rgb], 1)
    nt.links.new(comb.outputs[0], br.inputs['Vector'])
    nz = _noise(nt, co, 60.0)
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type, mix.blend_type = 'RGBA', 'MULTIPLY'
    mix.inputs['Factor'].default_value = 0.35
    nt.links.new(br.outputs['Color'], mix.inputs['A'])
    nt.links.new(nz.outputs['Color'], mix.inputs['B'])
    nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
    _bump(nt, b, br.outputs['Fac'], 0.35, 0.01)
    b.inputs['Roughness'].default_value = 0.88
    if windows:
        _windows(nt, b, comb.outputs[0], mix.outputs['Result'])


def _windows(nt, b, vec, base_col):
    """arrow slits on a coarse grid; about a third of them lit from inside by warm firelight"""
    win = nt.nodes.new('ShaderNodeTexBrick')
    win.offset = 0.5
    win.inputs['Scale'].default_value = 6.5
    win.inputs['Brick Width'].default_value = 0.5
    win.inputs['Row Height'].default_value = 0.5
    win.inputs['Mortar Size'].default_value = 0.0
    win.inputs['Color1'].default_value = (0, 0, 0, 1)
    win.inputs['Color2'].default_value = (1, 1, 1, 1)
    nt.links.new(vec, win.inputs['Vector'])
    # a slit in the middle of each cell: |frac(u) - 0.5| small horizontally, a little taller vertically
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    sc_ = nt.nodes.new('ShaderNodeVectorMath')
    sc_.operation = 'MULTIPLY'
    sc_.inputs[1].default_value = (6.5 / 0.5, 6.5 / 0.5, 1)
    nt.links.new(vec, sc_.inputs[0])
    nt.links.new(sc_.outputs[0], sep.inputs[0])

    def slit(out, half):
        fr = nt.nodes.new('ShaderNodeMath'); fr.operation = 'FRACT'
        nt.links.new(out, fr.inputs[0])
        sub = nt.nodes.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = 0.5
        nt.links.new(fr.outputs[0], sub.inputs[0])
        ab = nt.nodes.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'
        nt.links.new(sub.outputs[0], ab.inputs[0])
        lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = half
        nt.links.new(ab.outputs[0], lt.inputs[0])
        return lt.outputs[0]
    # the brick rows are offset by half a cell every other row; shift x by 0.5 on odd rows like the brick node does
    row = nt.nodes.new('ShaderNodeMath'); row.operation = 'FLOOR'
    nt.links.new(sep.outputs['Y'], row.inputs[0])
    odd = nt.nodes.new('ShaderNodeMath'); odd.operation = 'MODULO'; odd.inputs[1].default_value = 2.0
    nt.links.new(row.outputs[0], odd.inputs[0])
    shift = nt.nodes.new('ShaderNodeMath'); shift.operation = 'MULTIPLY_ADD'
    shift.inputs[1].default_value = 0.5
    nt.links.new(odd.outputs[0], shift.inputs[0])
    nt.links.new(sep.outputs['X'], shift.inputs[2])
    sx = slit(shift.outputs[0], 0.09)
    sy = slit(sep.outputs['Y'], 0.2)
    hole = nt.nodes.new('ShaderNodeMath'); hole.operation = 'MULTIPLY'
    nt.links.new(sx, hole.inputs[0]); nt.links.new(sy, hole.inputs[1])
    pick = nt.nodes.new('ShaderNodeSeparateColor')            # the brick node's per-cell random value
    nt.links.new(win.outputs['Color'], pick.inputs[0])
    some = nt.nodes.new('ShaderNodeMath'); some.operation = 'GREATER_THAN'; some.inputs[1].default_value = 0.55
    nt.links.new(pick.outputs[0], some.inputs[0])
    slit_m = nt.nodes.new('ShaderNodeMath'); slit_m.operation = 'MULTIPLY'
    nt.links.new(hole.outputs[0], slit_m.inputs[0]); nt.links.new(some.outputs[0], slit_m.inputs[1])
    lit = nt.nodes.new('ShaderNodeMath'); lit.operation = 'GREATER_THAN'; lit.inputs[1].default_value = 0.76
    nt.links.new(pick.outputs[0], lit.inputs[0])
    glow = nt.nodes.new('ShaderNodeMath'); glow.operation = 'MULTIPLY'
    nt.links.new(hole.outputs[0], glow.inputs[0]); nt.links.new(lit.outputs[0], glow.inputs[1])
    dark = nt.nodes.new('ShaderNodeMix')
    dark.data_type = 'RGBA'
    dark.inputs['B'].default_value = (0.01, 0.008, 0.007, 1)
    nt.links.new(slit_m.outputs[0], dark.inputs['Factor'])
    nt.links.new(base_col, dark.inputs['A'])
    nt.links.new(dark.outputs['Result'], b.inputs['Base Color'])
    b.inputs['Emission Color'].default_value = (1.0, 0.55, 0.18, 1)
    em = nt.nodes.new('ShaderNodeMath'); em.operation = 'MULTIPLY'; em.inputs[1].default_value = 2.5
    nt.links.new(glow.outputs[0], em.inputs[0])
    nt.links.new(em.outputs[0], b.inputs['Emission Strength'])


def metal(m, rough=0.28, base=None):
    nt, b = _nodes(m)
    if base:
        b.inputs['Base Color'].default_value = (*base, 1)
    b.inputs['Metallic'].default_value = 1.0
    nz = _noise(nt, _coords(nt), 35.0, 6.0)
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['To Min'].default_value, mr.inputs['To Max'].default_value = rough * 0.6, rough * 1.5
    nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
    nt.links.new(mr.outputs['Result'], b.inputs['Roughness'])
    _bump(nt, b, nz.outputs['Fac'], 0.05)


def matte(m, rough=0.7, bump=0.15, scale=40.0, var=(0.85, 1.12)):
    nt, b = _nodes(m)
    b.inputs['Roughness'].default_value = rough
    if b.inputs['Base Color'].is_linked:
        return
    nz = _noise(nt, _coords(nt), scale)
    ramp = _tint(nt, b, nz.outputs['Fac'], *var)
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    if bump:
        _bump(nt, b, nz.outputs['Fac'], bump)


def terrain(m):
    """painted map: matte parchment land, glossy rippled water where the map sits at sea level"""
    nt, b = _nodes(m)
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs[0])
    sea = nt.nodes.new('ShaderNodeMapRange')
    sea.inputs['From Min'].default_value, sea.inputs['From Max'].default_value = 0.035, 0.0
    nt.links.new(sep.outputs['Z'], sea.inputs['Value'])
    rough = nt.nodes.new('ShaderNodeMapRange')
    rough.inputs['To Min'].default_value, rough.inputs['To Max'].default_value = 0.86, 0.3
    nt.links.new(sea.outputs['Result'], rough.inputs['Value'])
    nt.links.new(rough.outputs['Result'], b.inputs['Roughness'])
    co = _coords(nt)
    fine = _noise(nt, co, 90.0, 8.0)
    wav = nt.nodes.new('ShaderNodeTexWave')
    wav.inputs['Scale'].default_value = 1.6
    wav.inputs['Distortion'].default_value = 6.0
    wav.inputs['Detail'].default_value = 4.0
    nt.links.new(co, wav.inputs['Vector'])
    h = nt.nodes.new('ShaderNodeMath')
    h.operation = 'MULTIPLY_ADD'                             # waves * sea + fine grain
    nt.links.new(wav.outputs['Fac'], h.inputs[0])
    nt.links.new(sea.outputs['Result'], h.inputs[1])
    nt.links.new(fine.outputs['Fac'], h.inputs[2])
    _bump(nt, b, h.outputs[0], 0.12, 0.02)
    b.inputs['Specular IOR Level'].default_value = 0.3        # soft sheen on the water, no blown-out sun glare


def water(m):
    nt, b = _nodes(m)
    b.inputs['Roughness'].default_value = 0.35
    b.inputs['Specular IOR Level'].default_value = 0.25
    wav = nt.nodes.new('ShaderNodeTexWave')
    wav.inputs['Scale'].default_value = 1.6
    wav.inputs['Distortion'].default_value = 6.0
    nt.links.new(_coords(nt), wav.inputs['Vector'])
    _bump(nt, b, wav.outputs['Fac'], 0.12)


def apply(sc, cam_data, res_y, sun_dir=(-0.45, 0.55, 0.70)):
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    cy.device = 'CPU'
    cy.samples = 10
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.05
    cy.use_denoising = True
    cy.denoiser = 'OPENIMAGEDENOISE'
    cy.denoising_quality = 'BALANCED'
    cy.denoising_prefilter = 'FAST'
    cy.max_bounces, cy.diffuse_bounces, cy.glossy_bounces = 4, 2, 2
    cy.transmission_bounces, cy.volume_bounces, cy.transparent_max_bounces = 2, 0, 4
    cy.sample_clamp_indirect = 3.0
    cy.seed = 7                                              # a fixed seed keeps the residual noise from crawling
    sc.render.use_persistent_data = True
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
    sc.render.resolution_x, sc.render.resolution_y = res_y * 16 // 9, res_y
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.view_settings.exposure = 0.2
    cam_data.dof.aperture_fstop *= 1.0

    # warm low sun from the same side as the old studio light; cool sky fills the shadows
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    sc.collection.objects.link(sun)
    sun.data.energy = 3.4
    sun.data.color = (1.0, 0.86, 0.68)
    sun.data.angle = math.radians(2.5)
    sun.rotation_euler = Vector(sun_dir).normalized().to_track_quat('Z', 'Y').to_euler()
    w = sc.world
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.0, 0.6
    ramp.color_ramp.elements[0].color = (0.16, 0.15, 0.14, 1)    # warm haze at the horizon
    ramp.color_ramp.elements[1].color = (0.05, 0.08, 0.13, 1)    # deep blue overhead
    nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 1.0

    # materials, by name
    for m in bpy.data.materials:
        n = m.name
        if not m.use_nodes or n.startswith('dragon_'):
            continue
        if n in ('stone', 'darkstone'):
            masonry(m, mortar=0.55 if n == 'stone' else 0.4, windows=True)
        elif n == 'sand':
            masonry(m, scale=18.0, mortar=0.75)
        elif n in ('brass', 'name_gold'):
            metal(m, 0.26, (0.86, 0.62, 0.30) if n == 'brass' else (0.95, 0.72, 0.34))
        elif n in ('steel', 'army_steel'):
            metal(m, 0.32)
        elif n == 'copper':
            metal(m, 0.3)
        elif n.startswith('roof_'):
            matte(m, 0.5, 0.25, 70.0, (0.8, 1.1))
        elif n == 'wood':
            matte(m, 0.65, 0.2, 25.0, (0.7, 1.15))
        elif n in ('greentree', 'snowtree', 'palm'):
            matte(m, 0.85, 0.1, 12.0, (0.75, 1.15))
        elif n == 'map':
            terrain(m)
        elif n == 'sea':
            water(m)
        elif n.startswith('face_'):
            nt_, b = _nodes(m)
            b.inputs['Metallic'].default_value = 0.1
            b.inputs['Roughness'].default_value = 0.42
            tex = [n_ for n_ in nt_.nodes if n_.type == 'TEX_IMAGE'][0]       # the emblem glows faintly so it reads at a distance
            nt_.links.new(tex.outputs['Color'], b.inputs['Emission Color'])
            b.inputs['Emission Strength'].default_value = 0.35
        elif n == 'campus_glass':
            nt_, b = _nodes(m)
            b.inputs['Roughness'].default_value = 0.04
            b.inputs['Specular IOR Level'].default_value = 1.0
        elif n.startswith(('campus_white', 'paving')):
            matte(m, 0.55, 0.08, 50.0, (0.92, 1.04))
        elif n.startswith('tent_'):
            matte(m, 0.8, 0.1, 30.0, (0.85, 1.1))

    # the floating names would mirror in the glossy water and read as doubled text
    for ob in sc.objects:
        if ob.name.startswith('name_'):
            ob.visible_glossy = False
            ob.visible_shadow = False          # a hard copy of the word on the ground reads as doubled text

    # bevelled edges catch the light on every built part
    for ob in sc.objects:
        if ob.type == 'MESH' and not ob.name.startswith(('terrain', 'sea', 'trees', 'dragon', 'face_', 'name_', 'army', 'tents', 'banner')):
            bv = ob.modifiers.new('bevel', 'BEVEL')
            bv.width = 0.008
            bv.segments = 2
            bv.limit_method = 'ANGLE'
            bv.angle_limit = math.radians(35)
