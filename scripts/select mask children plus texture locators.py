#!/usr/bin/python
# ================================
# (C)2020 Dmytro Holub
# heap3d@gmail.com
# --------------------------------
# modo python
# select mask children and texture locators for preselected masks
# ================================

import modo
import modo.constants as c

scene = modo.scene.current()

selected_mask = scene.selectedByType('mask')
print(selected_mask)
for item in selected_mask:
    for child_item in item.children(recursive=True):
        child_item.select()

items = scene.selected
for item in items:
    try:
        for i in item.itemGraph('shadeLoc').forward():
            i.select()
    except LookupError:
        pass

for textureLoc in scene.selectedByType(itype=c.TXTRLOCATOR_TYPE):
    textureLoc.parent.select()
