#!/usr/bin/python
# ================================
# (C)2021 Dmytro Holub
# heap3d@gmail.com
# --------------------------------
# modo python
# EMAG
# toybox
# run full bake queue in one click
# ================================

import modo
import lx
import os.path

baked_id = '_auto_baked'
gltf_id = '_gltf'
ao_id = '_ao'
freezed_id = '_freezed'
cleanup_enabled = True

scene = modo.scene.current()

lx.eval('@{scripts/1-bake2lowpoly v11.1.py}')
# save as baked scene name
filename = scene.filename
basename = os.path.basename(scene.filename)
dirname = os.path.dirname(scene.filename)
name, ext = os.path.splitext(basename)
name_inc = '{}{}'.format(name, baked_id)
lx.eval('scene.saveAs "{}\\{}{}" $LXOB false'.format(dirname, name_inc, ext))

lx.eval('@{scripts/2-lowpoly2gltf v07.py}')
# save as gltf scene name
name_inc = '{}{}'.format(name_inc, gltf_id)
lx.eval('scene.saveAs "{}\\{}{}" $LXOB false'.format(dirname, name_inc, ext))

lx.eval('@{scripts/3-mergeAO_BC v04.py}')
# save as ao scene name
name_inc = '{}{}'.format(name_inc, ao_id)
lx.eval('scene.saveAs "{}\\{}{}" $LXOB false'.format(dirname, name_inc, ext))

lx.eval('@{scripts/4-replicators freeze v01.py}')
# cleanup the scene
if cleanup_enabled:
    lx.eval('@{scripts/5-cleanup v01.py}')
# save as freezed scene name
name_inc = '{}{}'.format(name_inc, freezed_id)
lx.eval('scene.saveAs "{}\\{}{}" $LXOB false'.format(dirname, name_inc, ext))

# export as .glb
lx.eval('scene.saveAs "{}\\{}{}" gltf.bin true'.format(dirname, name_inc, '.glb'))
