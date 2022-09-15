#!/usr/bin/python
# ================================
# (C)2021 Dmytro Holub
# heap3d@gmail.com
# --------------------------------
# modo python
# EMAG
# toybox
# cleanup the scene
# ================================
import lx
import modo
import modo.constants as c

scene = modo.scene.current()

# cleanup the scene
scene.deselect()
# delete material plate mesh
specific_items = scene.items(itype=c.MESH_TYPE, name='material plate*')
for item in specific_items:
    item.select()
# delete highpoly group
specific_items = scene.items(itype=c.GROUPLOCATOR_TYPE, name='*highpoly*')
for item in specific_items:
    item.select()
# delete lowpoly group
specific_items = scene.items(itype=c.GROUPLOCATOR_TYPE, name='*lowpoly*')
for item in specific_items:
    item.select()
# delete Floor material
specific_items = scene.items(itype=c.MASK_TYPE, name='Floor (Material)')
for item in specific_items:
    item.select()
# delete roughness correction
specific_items = scene.items(itype=c.MASK_TYPE, name='roughness correction')
for item in specific_items:
    item.select()
# delete CNC_Big material group
specific_items = scene.items(itype=c.MASK_TYPE, name='CNC_Big')
for item in specific_items:
    item.select()
# delete Dielectric_GRP material group
specific_items = scene.items(itype=c.MASK_TYPE, name='Dielectric_GRP*')
for item in specific_items:
    item.select()
# delete Metal_GRP material group
specific_items = scene.items(itype=c.MASK_TYPE, name='Metal_GRP*')
for item in specific_items:
    item.select()
# delete CNC_Small material group
specific_items = scene.items(itype=c.MASK_TYPE, name='CNC.Small')
for item in specific_items:
    item.select()

if len(scene.selected) > 0:
    lx.eval('!item.delete')
