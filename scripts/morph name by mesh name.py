#!/usr/bin/python
# ================================
# (C)2019 Dmytro Holub
# heap3d@gmail.com
# --------------------------------
# modo python
# EMAG
# toybox
# rename every(!!!) morph maps for selected meshes
# ================================

import modo

scene = modo.scene.current()

cageMarker = 'bake cage'

for mesh in scene.selectedByType('mesh'):
    print(mesh.name)
    for morph in mesh.geometry.vmaps.morphMaps:
        morph.name = '{} {}'.format(mesh.name, cageMarker)
        print(' ', morph.name)
