#!/usr/bin/python
# ================================
# (C)2021 Dmytro Holub
# heap3d@gmail.com
# --------------------------------
# modo python
# EMAG
# create morph map if not created already
# rename morph map
# select morph map
# push polygons with initial value
# ================================

import modo
import lx

cageMarker = 'bake cage'
userValBakeDistName = 'h3d_b2lp_bakeDistance'

scene = modo.scene.current()

print('start...')

bakeDistance = lx.eval('user.value {%s} ?' % userValBakeDistName)
print(bakeDistance)
selected = scene.selected

for mesh in selected:
    if mesh.type != 'mesh':  # skip selected non-meshes
        continue
    print(mesh, mesh.name)
    mesh.select(replace=True)
    for morph in mesh.geometry.vmaps.morphMaps:
        print(morph)
        # todo delete old morph map
        lx.eval('select.vertexMap "{}" morf replace'.format(morph.name))
        lx.eval('!vertMap.delete morf')
    # todo create new morph map
    lx.eval('!vertMap.new "{} {}" morf true'.format(mesh.name, cageMarker))
    # todo push on morph map with certain amount value
    lx.eval('tool.set xfrm.push on')
    lx.eval('tool.setAttr xfrm.push dist {}'.format(bakeDistance))
    lx.eval('tool.doApply')
    lx.eval('tool.set xfrm.push off 0')

print('done.')
