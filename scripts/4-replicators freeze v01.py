#!/usr/bin/python
# ================================
# (C)2021 Dmytro Holub
# heap3d@gmail.com
# --------------------------------
# modo python
# converts all replicators in the scene to instances, then freeze all instances to mesh items
# ================================

import modo
import lx
import modo.constants as c

scene = modo.scene.current()

print()
print("start...")

# store selection
selectionStore = scene.selected

# todo get all replicators
replicatorsSet = scene.items(itype=c.REPLICATOR_TYPE)
scene.deselect()
for replicator in replicatorsSet:
    replicator.select()

# todo convert replicators to instances
if len(replicatorsSet) > 0:
    lx.eval("replicator.freeze")

# todo get all instances
instancesSet = scene.items(itype=c.MESHINST_TYPE)
scene.deselect()
for instance in instancesSet:
    instance.select()

# todo convert instances to mesh items
if len(instancesSet) > 0:
    lx.eval("item.setType mesh locator")

# restore selection
scene.deselect()
for item in selectionStore:
    item.select()

print("done.")
