#!/usr/bin/python
# ================================
# (C)2019-2021 Dmytro Holub
# heap3d@gmail.com
# --------------------------------
# modo python
# EMAG
# toybox
# merge Ambient Occlusion pass into Base Color pass
# ================================

import lx
import modo
import modo.constants as c
import os.path

# --------------------------------------variables-------------------------------------
imgSize_code_direct = '=dir'
imgSize_code_mult = '=mul'
imgSize_code_div = '=div'
imgSize_code_end = '='

ao_small_rays = 512
ao_large_rays = 512
ao_small_dist = 0.06
ao_large_dist = 2.5

userValSelectedName = 'h3d_b2lp_selectionOnly'
userValSelectedUsername = 'bake selection only'
userValSelectedDialogname = 'enable to bake selection only'

userValBakeName = 'h3d_b2lp_bakingEnabled'
userValBakeUsername = 'bake textures'
userValBakeDialogname = 'enable to bake textures to file'

userValCageName = 'h3d_b2lp_useCageForBaking'
userValCageUsername = 'use cage for baking'
userValCageDialogname = 'enable to use cage for baking'

userValScaleName = 'h3d_b2lp_useScaleMult'
userValScaleUsername = 'scale multiplier'
userValScaleDialogname = 'set scale multiplier'

userValBakeDistName = 'h3d_b2lp_bakeDistance'
userValBakeDistUsername = 'bake from object distance'
userValBakeDistDialogname = 'set bake from distance'

userValImgSizeName = 'h3d_b2lp_imageSize'
userValImgSizeList = "64;128;256;512;1024;2048;4096;8192"
userValImgSizeUsername = "choose image resolution"
userValImgSizeDialogname = "set image resolution for baking textures"

bake_lowpoly = True
bakeDistance = '0.015'
imgSize = 256   # variable declaration
lpTag = 'lowpoly'
hpTag = 'highpoly'
baseColor_Name = 'baseColor_'
normal_Name = 'normal_'
rough_Name = 'rough_'
specColor_Name = 'specColor_'
specAmount_Name = 'specAmount_'
specFresnel_Name = 'specFresnel_'
diffAmount_Name = 'diffAmount_'
lumiColor_Name = 'lumiColor_'
lumiAmount_Name = 'lumiAmount_'
tranAmount_Name = 'tranAmount_'
metalMap_Name = 'metalMap_'
aoSmall_Name = 'ao_small'
aoLarge_Name = 'ao_large'
newImagePath = ''  # global variable, image path for baking
lpMatTag = 'lp_'

lpMaterialList = set()
materialList = set()
normalMaps = set()
newImageMaps = set()
laterActivation = ()
project_name_name = 'project name'

metal_marker_search_text = 'Metal_GRP'
metalMasksParent = None  # type:modo.Item
metal_marker_present = False

bake_cage_marker = 'bake cage'
scale_mult = 1.0
splitTag = 'meshByUV_'
aoSmallTag = 'ao_small_'
aoLargeTag = 'ao_large_'
pass_1 = '__1st pass'
pass_2 = '__2nd pass'
pass_3 = '__3rd pass'
pass_tr = '__transparency pass'
pass_me_fl = '__metallic flag pass'
pass_diffColorName = '__diffuse color'
pass_metalColorName = '__metallic color'
sfx_ao_ro_me = '__ao_ro_me'
sfx_norm = '__norm'
sfx_lum = '__lum'
sfx_tr_tmp = '__tr_tmp'
sfx_bc_tmp = '__bc_tmp'
sfx_me_fl = '__metallic_flag'
sfx_di_di = '__dielectric_diff'
sfx_me_sp = '__metallic_spec'
imgName_me_fl = '__metallic_flag'
imgName_di_di = '__dielectric_diff'
imgName_me_sp = '__metallic_spec'
bakedGroupMarker = 'mesh by UV group'
prebakedMmarker = 'prebaked'
# --------------------------------------end of variables-------------------------------------


def newTexture(imgSize, imgFormat, newName, newExt, newImagePath, uvMapName, effect, createSpace='(default)', loadSpace='(default)'):
    imgName = newName
    lx.eval('clip.newStill "%s\\%s%s" x%s RGB false false format:%s colorspace:%s' % (newImagePath, imgName, newExt, imgSize, imgFormat, createSpace))
    imgMap = scene.addItem('imageMap')
    imgMap.select(True)
    lx.eval('select.subItem {%s:videoStill001} set mediaClip' % imgName)
    lx.eval('texture.setIMap {%s:videoStill001}' % imgName)
    lx.eval('item.channel textureLayer(txtrLocator)$projType uv')
    lx.eval('texture.setUV {%s}' % uvMapName)
    lx.eval('select.subItem {%s:videoStill001} set mediaClip' % imgName)
    lx.eval('select.subItem {%s} set textureLayer' % imgName)
    lx.eval('item.channel colorspace %s' % loadSpace)
    imgMap.channel('effect').set('%s' % effect)
    return imgMap


def prepare_image_map(working_map, baking=True):
    # print texture
    if baking:
        working_map.channel('pixBlend').set('nearest')
        working_map.channel('aa').set(0)
    else:
        working_map.channel('pixBlend').set('bicubic')
        working_map.channel('aa').set(1)


print()
print('start ---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- ----------')

scene = modo.scene.current()
# store selection
selectionStore = scene.selected

selectedMasks = scene.selectedByType('mask')
mat_gltf = None  # gltf material initialization
map_ao = None  # gltf ambient occlusion map initialization
map_norm = None  # gltf normal map initialization
map_lum = None  # gltf emission map initialization
map_bc = None  # gltf base color map initialization
map_tr = None  # gltf transparent amount map initialization
map_me = None  # gltf metallic map initialization
map_pass1 = None  # 1st pass map initialization
map_pass2 = None  # 2nd pass map initialization
map_pass3 = None  # 3rd pass map initialization

for mask in selectedMasks:
    print(mask.name, ':', mask.id)
    mat_gltf = map_ao = map_norm = map_lum = map_bc = map_tr = map_me = map_pass1 = map_pass2 = map_pass3 = None
    for item in mask.children():
        channel_effect = item.channel('effect').get()
        if item.type == 'glTFShader':
            mat_gltf = item  # type: modo.item.Item
        if channel_effect == 'aoGLTF':
            map_ao = item  # type: modo.item.Item
        elif channel_effect == 'normalGLTF':
            map_norm = item  # type: modo.item.Item
        elif channel_effect == 'emisGLTF':
            map_lum = item  # type: modo.item.Item
        elif channel_effect == 'baseColorGLTF':
            map_bc = item  # type: modo.item.Item
        elif channel_effect == 'tranAmount':
            map_tr = item  # type: modo.item.Item
        elif channel_effect == 'metallicGLTF':
            map_me = item  # type: modo.item.Item
        elif '__1st pass' in item.name:
            map_pass1 = item  # type: modo.item.Item
        elif '__2nd pass' in item.name:
            map_pass2 = item  # type: modo.item.Item
        elif '__3rd pass' in item.name:
            map_pass3 = item  # type: modo.item.Item

    # duplicate ao and metallic texture
    try:
        map_ao_copy = scene.duplicateItem(map_ao)
        map_me_copy = scene.duplicateItem(map_me)
    except Exception:  # skip if map_ao or map_me not found
        print('mask skipped {}:{}'.format(mask.name, mask.id))
        continue
    map_ao_copy.setParent(mask, map_bc.parentIndex)
    map_ao_copy.channel('effect').set('driverB')
    map_ao_copy.channel('blend').set('normal')
    map_me_copy.setParent(mask, map_ao_copy.parentIndex)
    map_me_copy.channel('effect').set('driverB')
    map_me_copy.channel('blend').set('screen')
    map_me_copy.channel('opacity').set(0.25)

    # create gradient driverB >> baseColorGLTF
    grad_bc_ao_tmp = scene.addItem(itype='gradient', name='bc_ao_blend')
    grad_bc_ao_tmp.setParent(mask, map_me_copy.parentIndex+1)
    grad_bc_ao_tmp.channel('color.R').envelope.keyframes[0] = (0.0, 0.0)
    grad_bc_ao_tmp.channel('color.G').envelope.keyframes[0] = (0.0, 0.0)
    grad_bc_ao_tmp.channel('color.B').envelope.keyframes[0] = (0.0, 0.0)
    grad_bc_ao_tmp.channel('color.R').envelope.keyframes.add(1.0, 1.0)
    grad_bc_ao_tmp.channel('color.G').envelope.keyframes.add(1.0, 1.0)
    grad_bc_ao_tmp.channel('color.B').envelope.keyframes.add(1.0, 1.0)
    grad_bc_ao_tmp.channel('color.R').envelope.preBehaviour = lx.symbol.iENV_LINEAR
    grad_bc_ao_tmp.channel('color.R').envelope.postBehaviour = lx.symbol.iENV_LINEAR
    grad_bc_ao_tmp.channel('color.G').envelope.preBehaviour = lx.symbol.iENV_LINEAR
    grad_bc_ao_tmp.channel('color.G').envelope.postBehaviour = lx.symbol.iENV_LINEAR
    grad_bc_ao_tmp.channel('color.B').envelope.preBehaviour = lx.symbol.iENV_LINEAR
    grad_bc_ao_tmp.channel('color.B').envelope.postBehaviour = lx.symbol.iENV_LINEAR
    grad_bc_ao_tmp.channel('param').set('driverB')
    grad_bc_ao_tmp.channel('effect').set('baseColorGLTF')
    grad_bc_ao_tmp.channel('blend').set('multiply')

    # split folder path and file name
    folder_path, map_bc_filename = os.path.split(map_ao_copy.itemGraph('shadeLoc').forward(1).channel('filename').get())
    print('folder_path : <{}>'.format(folder_path))
    print('map_bc_filename : <{}>'.format(map_bc_filename))
    # get image format
    image_format = map_bc.itemGraph('shadeLoc').forward(1).channel('format').get()
    print('image_format: <{}>'.format(image_format))
    # get new image extension
    image_ext = map_bc_filename[map_bc_filename.rfind('.'):]
    print('image_ext: <{}>'.format(image_ext))
    # get new map name
    map_bc_ao_merged_filename = '{}__bc_ao_merged'.format(map_bc_filename[:map_bc_filename.rfind('__')])
    print('map_bc_ao_merged_filename: <{}>'.format(map_bc_ao_merged_filename))
    # gen uv map name
    map_bc_uvmap_name = map_bc.itemGraph('shadeLoc').forward(0).channel('uvMap').get()
    print('map_bc_uvmap_name: <{}>'.format(map_bc_uvmap_name))
    # get image size
    clip_index = map_bc.itemGraph('shadeLoc').forward(1).index
    image_info = lx.eval('query layerservice clip.info ? {}'.format(clip_index))
    image_size = image_info.split()[1][2:]
    print('imgInfo: <{}>    imgSize: <{}>'.format(image_info, image_size))
    # select specific mesh
    mesh_name = mask.name[:(mask.name.rfind(' (Material)'))-1]
    print('mesh_name <{}>'.format(mesh_name))
    mesh = scene.item(mesh_name)
    print('mesh: <{}>    name: <{}>'.format(mesh, mesh.name))
    # create new texture
    map_bc_ao_merged = newTexture(
        imgSize=image_size, imgFormat=image_format, newName=map_bc_ao_merged_filename, newExt=image_ext, newImagePath=folder_path,
        uvMapName=map_bc_uvmap_name, effect='baseColorGLTF', createSpace='(default)', loadSpace='(default)')  # type: modo.item.Item
    print('map_bc_ao_merged: <{}>'.format(map_bc_ao_merged))
    # parent new texture
    map_bc_ao_merged.setParent(mask, grad_bc_ao_tmp.parentIndex+1)
    # disable new texture
    map_bc_ao_merged.channel('enable').set(0)
    # select mesh and texture
    mesh.select(replace=True)
    map_bc_ao_merged.select()

    # image maps preparation for sharp baking
    for imageMap in scene.items(itype='imageMap'):
        prepare_image_map(imageMap)

    # bake to texture
    lx.eval('bake.toTexture')
    map_bc_ao_merged.itemGraph('shadeLoc').forward(1).select(replace=True)
    lx.eval('clip.save')

    # remove old textures
    scene.removeItems(map_ao)
    scene.removeItems(map_ao_copy)
    scene.removeItems(map_bc)
    scene.removeItems(map_tr)
    scene.removeItems(map_me_copy)
    scene.removeItems(grad_bc_ao_tmp)

    mask_children = map_pass1.children(recursive=True)
    for child in mask_children:
        scene.removeItems(child)
    scene.removeItems(map_pass1)

    mask_children = map_pass2.children(recursive=True)
    for child in mask_children:
        scene.removeItems(child)
    scene.removeItems(map_pass2)

    mask_children = map_pass3.children(recursive=True)
    for child in mask_children:
        scene.removeItems(child)
    scene.removeItems(map_pass3)

    # enable new texture
    map_bc_ao_merged.channel('enable').set(1)
    # enable swizzling
    map_bc_ao_merged.channel('swizzling').set(1)
    # set swizzling to 'RGB'
    map_bc_ao_merged.channel('rgba').set(lx.symbol.i_IMAGEMAP_SWIZZLING_RGB)

for imageMap in scene.items(itype='imageMap'):
    prepare_image_map(imageMap, baking=False)

# purge unused materials
lx.eval('material.purge')

# parent prebaked geo to baked group
try:
    scene.deselect()
    bakedGroupItem = scene.item(name=bakedGroupMarker)
    for item in scene.items(itype=c.GROUPLOCATOR_TYPE):
        if prebakedMmarker in item.name:
            # item.setParent(bakedGroupItem)
            item.select()
    bakedGroupItem.select()
    if len(scene.selected) > 1:
        lx.eval('item.parent inPlace:1')
except Exception:
    print('no baked group found')
    modo.dialogs.alert(title='cancelled', message='no baked group found', dtype='warning')

# restore selection
scene.deselect()
for item in selectionStore:
    try:
        item.select()
    except Exception:
        print('restore selection item skipped')
        continue

print('finish.')
