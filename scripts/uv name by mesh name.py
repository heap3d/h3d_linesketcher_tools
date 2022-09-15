#!/usr/bin/python
# ================================
# (C)2019 Dmytro Holub
# heap3d@gmail.com
# --------------------------------
# modo python
# EMAG
# toybox
# rename every(!!!) uv maps for selected meshes
# ================================
import modo

scene = modo.scene.current()

for mesh in scene.selectedByType('mesh'):
    print(mesh.name)
    for uv in mesh.geometry.vmaps.uvMaps:
        uv.name = '{} bake'.format(mesh.name)
        print(' ', uv.name)
