#!/usr/bin/python
# ================================
# (C)2019-2022 Dmytro Holub
# heap3d@gmail.com
# --------------------------------
# modo python
# EMAG
# toybox
# bake from selected highpoly meshes to lowpoly
# turns off 'Antialiasing' option for textures in hires meshes
# =divN=  : divide by N
# =mulN=  : multiply by N
# =dirNN= : direct set resolution by NN (64;128;256;512;1024;2048;4096;8192)
# use cage 'bake cage' for baking
# ================================

import lx
import modo
import os.path
import random
import modo.constants as c

scene = modo.scene.current()

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


def set_project_name(name):
    try:
        project_name_item = scene.item(project_name_name)
    except LookupError:
        print('project name item not found:', name)
        print('new project name item created.')
        project_name_item = scene.addItem(c.LOCATOR_TYPE, project_name_name)
        project_name_item.select(True)
        lx.eval('channel.create projectname string username:"project name"')

    project_name_item.select(replace=True)
    lx.eval('item.channel projectname "%s"' % name)


def get_project_name():
    try:
        project_name_item = scene.item(project_name_name)
        project_name_item.select(True)
        val = lx.eval('item.channel projectname ?')
        return val
    except LookupError:
        return ''


def getImagePath():
    global newImagePath
    projectPath = lx.eval('query platformservice path.path ? project')
    scene_name = get_project_name()
    if scene_name != '':
        scene_name += '\\'
    dirPath = projectPath + '\\Images\\baking\\' + scene_name
    if not os.path.exists(dirPath):
        try:
            os.makedirs(dirPath)
        except:
            print('os.makedirs error')
            print('os.makedirs("%s")' % dirPath)

    path = dirPath
    if not os.path.exists(path):
        path = modo.dialogs.dirBrowse('Choose directory for baked images:', projectPath)
        if path is None:
            path = scene.filename
            path = path.rpartition('\\')[0]+'\\'
            print('extracted from filename: %s' % path)
        else:
            path = '%s\\' % path
    newImagePath = path
    return path


def getImagePath_tmp():
    path_tmp = '%stmp\\' % getImagePath()
    if not os.path.exists(path_tmp):
        try:
            os.makedirs(path_tmp)
        except:
            path_tmp = getImagePath()
            print('tmp dir making error')
    return path_tmp


def getLpList_selected():
    mesh_list = set()
    selected = scene.selectedByType('mesh')
    for mesh_item in selected:
        mesh_list.add(mesh_item)
        print('lpList:', mesh_item.name)
    return mesh_list


def getLpList_children(parent_item):
    children_list = parent_item.children(recursive=True, itemType=c.MESH_TYPE)
    return children_list


def get_resolution_override(name=''):
    start = -1  # variable declaration
    end = -1  # variable declaration
    code_length = 0  # variable declaration
    imgSize_default = int(imgSize)
    resolution = imgSize_default  # variable declaration
    code_mode = ''  # variable declaration
    input_size = imgSize_default  # variable declaration
    cm_mult = 'mul'
    cm_div = 'div'
    cm_dir = 'dir'
    try:
        end = name.rfind(imgSize_code_end)
        for find_code in (imgSize_code_direct, imgSize_code_div, imgSize_code_mult):
            current_find = name.find(find_code)
            if current_find != -1:
                start = current_find
                code_length = len(find_code)
                if find_code == imgSize_code_direct:
                    code_mode = cm_dir
                elif find_code == imgSize_code_div:
                    code_mode = cm_div
                elif find_code == imgSize_code_mult:
                    code_mode = cm_mult

        if start < 0 or end < 0:
            if start != end:
                print('Raising exception. start: <{}>   end: <{}>'.format(start, end))
                raise Exception('resolution override error')
            else:
                return imgSize_default

        input_number = int(name[start+code_length:end])

        if code_mode == cm_dir:
            input_size = input_number
        elif code_mode == cm_div:
            input_size = imgSize_default / input_number
        elif code_mode == cm_mult:
            input_size = imgSize_default * input_number

        if input_size > 4096:
            resolution = 8192
        elif input_size > 2048:
            resolution = 4096
        elif input_size > 1024:
            resolution = 2048
        elif input_size > 512:
            resolution = 1024
        elif input_size > 256:
            resolution = 512
        elif input_size > 128:
            resolution = 256
        elif input_size > 64:
            resolution = 128
        else:
            resolution = 64

    except Exception as error:
        print('resolution override error: <{}>, default used, UV Map: <{}>   start: <{}>   end: <{}>'.format(error.message, name, start, end))
        return imgSize_default

    return resolution


def newTexture(curMask, uvMap, newImagePath, namePrefix, effect, createSpace='(default)', loadSpace='(default)'):
    imgSize_override = get_resolution_override(uvMap.name)
    imgName = '%s%s' % (namePrefix, uvMap.name)
    lx.eval('clip.newStill "%s%s.png" x%s RGB false false format:PNG colorspace:%s' % (newImagePath, imgName, imgSize_override, createSpace))
    imgMap = scene.addItem('imageMap')
    imgMap.setParent(curMask, -1)
    imgMap.select(True)
    lx.eval('select.subItem {%s:videoStill001} set mediaClip' % imgName)
    lx.eval('texture.setIMap {%s:videoStill001}' % imgName)
    lx.eval('item.channel textureLayer(txtrLocator)$projType uv')
    lx.eval('texture.setUV {%s}' % uvMap.name)
    lx.eval('select.subItem {%s:videoStill001} set mediaClip' % imgName)
    lx.eval('select.subItem {%s} set textureLayer' % imgName)
    lx.eval('item.channel colorspace %s' % loadSpace)
    imgMap.channel('effect').set('%s' % effect)
    return imgMap


def createLpMaterial(mesh):
    for uvMap in mesh.geometry.vmaps.uvMaps:
        # print 'uvMap : %s | len : %s' % (uvMap.name, len(uvMap))
        try:
            # TODO delete existing lpMaterial and children textures

            scene.deselect()
            lpMatExisting = scene.item('%s%s (Material)' % (lpMatTag, uvMap.name))
            for texture in lpMatExisting.children():
                if texture.type == 'imageMap':  # select image maps textures only
                    texture.itemGraph('shadeLoc').forward(1).select()  # select image map for texture
            lx.eval('!delete')  # delete selected image maps
            for child in lpMatExisting.children():
                child.select()  # select mask children
            lx.eval('!delete')  # delete selected

            lpMatExisting.select(replace=True)  # select mask
            lx.eval('!delete')  # delete selected mask
        except Exception:
            print('lpMaterial not existed yet for the uvMap: <{}>'.format(uvMap.name))

        mesh.select(replace=True)
        lx.eval('select.drop polygon')
        lx.eval('select.vertexMap {%s} txuv replace' % uvMap.name)
        lx.eval('select.unmapPolygon {%s} true' % uvMap.name)
        lx.eval('poly.setMaterial "%s%s" {%s %s %s} 1.0 0.04' % (lpMatTag, uvMap.name, random.random(), random.random(), random.random()))
        curMask = scene.selectedByType('mask')[0]
        shader_items = scene.items(itype=c.DEFAULTSHADER_TYPE)
        base_shader = None
        base_shader_index = 0
        for shader in shader_items:
            if shader.parent.type == 'polyRender':
                if shader.parentIndex > base_shader_index:
                    base_shader = shader
                    base_shader_index = base_shader.parentIndex
        base_shader_index = 0
        if base_shader is None:
            for shader in shader_items:
                if shader.parent.type == 'mask':
                    if shader.parent.channel('ptag').get() == '':
                        if shader.parentIndex > base_shader_index:
                            base_shader = shader
                            base_shader_index = base_shader.parentIndex
        if base_shader is None:
            base_shader = shader_items[-1]

        if curMask.parent != base_shader.parent:
            curMask.setParent(base_shader.parent, base_shader.parentIndex)
        lx.eval('shader.setVisible {%s} false' % curMask.name)
        if curMask not in lpMaterialList:
            lpMaterialList.add(curMask)
            newImagePath = getImagePath_tmp()

            bake_cage_name = None  # variable definition
            for morph in mesh.geometry.vmaps.morphMaps:
                if bake_cage_marker in morph.name.lower():
                    bake_cage_name = morph.name

            img_baseColor = newTexture(curMask, uvMap, newImagePath, baseColor_Name, 'diffColor')
            img_norm = newTexture(curMask, uvMap, newImagePath, normal_Name, 'normal', '(none)', '(none)')
            img_rough = newTexture(curMask, uvMap, newImagePath, rough_Name, 'rough')
            img_specColor = newTexture(curMask, uvMap, newImagePath, specColor_Name, 'specColor')
            img_specAmount = newTexture(curMask, uvMap, newImagePath, specAmount_Name, 'specAmount')
            img_specFresnel = newTexture(curMask, uvMap, newImagePath, specFresnel_Name, 'specFresnel')
            img_diffAmount = newTexture(curMask, uvMap, newImagePath, diffAmount_Name, 'diffAmount')
            img_lumiColor = newTexture(curMask, uvMap, newImagePath, lumiColor_Name, 'lumiColor')
            img_lumiAmount = newTexture(curMask, uvMap, newImagePath, lumiAmount_Name, 'lumiAmount')
            img_tranAmount = newTexture(curMask, uvMap, newImagePath, tranAmount_Name, 'tranAmount')
            img_metallness = newTexture(curMask, uvMap, newImagePath, metalMap_Name, 'driverD')

            imgSize_override = get_resolution_override(uvMap.name)

            # img_ao_small
            imgName = '%s_%s' % (aoSmall_Name, uvMap.name)
            aoSmallSaveName = imgName
            lx.eval('clip.newStill "%s%s.png" x%s RGB false false format:PNG colorspace:(default)' % (newImagePath, imgName, imgSize_override))
            img_ao_small = scene.addItem('imageMap')
            img_ao_small.setParent(curMask, -1)
            img_ao_small.select(True)
            lx.eval('select.subItem {%s:videoStill001} set mediaClip' % imgName)
            lx.eval('texture.setIMap {%s:videoStill001}' % imgName)
            lx.eval('item.channel textureLayer(txtrLocator)$projType uv')
            lx.eval('texture.setUV {%s}' % uvMap.name)
            img_ao_small.channel('effect').set('diffColor')
            img_ao_small.channel('blend').set('multiply')

            # img_ao_large
            imgName = '%s_%s' % (aoLarge_Name, uvMap.name)
            aoLargeSaveName = imgName
            lx.eval('clip.newStill "%s%s.png" x%s RGB false false format:PNG colorspace:(default)' % (newImagePath, imgName, imgSize_override))
            img_ao_large = scene.addItem('imageMap')
            img_ao_large.setParent(curMask, -1)
            img_ao_large.select(True)
            lx.eval('select.subItem {%s:videoStill001} set mediaClip' % imgName)
            lx.eval('texture.setIMap {%s:videoStill001}' % imgName)
            lx.eval('item.channel textureLayer(txtrLocator)$projType uv')
            lx.eval('texture.setUV {%s}' % uvMap.name)
            img_ao_large.channel('effect').set('diffColor')
            img_ao_large.channel('blend').set('multiply')

            # texture output bake item
            # use existing texture output bake item
            try:
                bakeItemTexture = scene.item('{}{}'.format(lpMatTag, uvMap.name))
                bakeItemTexture.select(replace=True)
            except Exception:
                lx.eval('bakeItem.createTextureBake')
                lx.eval('item.name "%s%s" bakeItemTexture' % (lpMatTag, uvMap.name))

            lx.eval('item.channel bakeItemTexture$hiddenTarget false')
            lx.eval('item.channel bakeItemTexture$hiddenSource false')
            lx.eval('item.channel bakeItemTexture$hiddenOutput true')
            lx.eval('item.channel bakeItemTexture$bakeFrom true')

            if use_cage and bake_cage_name is not None:
                lx.eval('bakeItem.setCage "%s" texture' % bake_cage_name)
                lx.eval('item.channel bakeItemTexture$distance %s' % '0')
            else:
                lx.eval('item.channel bakeItemTexture$distance %s' % bakeDistanceMultiplied)

            lx.eval('item.channel bakeItemTexture$saveOutputFile true')
            lx.eval('bakeItem.target {%s} type:0' % lpItem.name)
            lx.eval('bakeItem.source {%s} type:0' % hpItem.name)
            for image in (img_rough, img_baseColor, img_specColor, img_lumiColor, img_lumiAmount, img_tranAmount, img_diffAmount, img_specAmount, img_specFresnel, img_metallness):
                newImageMaps.add(image)
                image.select()
            for image in (img_norm, ):
                normalMaps.add(image)
                image.select()
            lx.eval('bakeItem.setAsTextureOutput 1')
            if bake_lowpoly:
                lx.eval('bakeItem.bake true type:0')

            # ao_small render output bake item
            # use existing render output bake item aoSmall
            try:
                bakeItemRender_aoSmall = scene.item('{}{}'.format(aoSmall_Name, uvMap.name))
                bakeItemRender_aoSmall.select(replace=True)
            except Exception:
                lx.eval('bakeItem.createOutputBake')
                lx.eval('item.name "%s_%s_RO" bakeItemRO' % (aoSmall_Name, uvMap.name))

            lx.eval('bakeItem.target {%s} type:1' % lpItem.name)
            lx.eval('bakeItem.source {%s} type:1' % hpItem.name)
            lx.eval('bakeItem.renderOutput {%s}' % aoSmall.name)
            lx.eval('bakeItem.setUV {%s}' % uvMap.name)
            lx.eval('item.channel bakeItemRO$bakeFrom true')

            if use_cage and bake_cage_name is not None:
                lx.eval('bakeItem.setCage "%s" render' % bake_cage_name)
                lx.eval('item.channel bakeItemRO$distance %s' % '0')
            else:
                lx.eval('item.channel bakeItemRO$distance %s' % bakeDistanceMultiplied)

            lx.eval('item.channel bakeItemRO$hiddenTarget false')
            lx.eval('item.channel bakeItemRO$hiddenSource false')
            lx.eval('item.channel bakeItemRO$hiddenOutput true')
            lx.eval('item.channel bakeItemRO$saveOutputFile true')
            lx.eval('item.channel outLocation {%s}' % newImagePath)
            lx.eval('item.channel bakeItemRO$outPattern {%s}<>' % aoSmallSaveName)
            lx.eval('bakeItem.format PNG')
            lx.eval('item.channel bakeItemRO$width %s' % imgSize_override)
            lx.eval('item.channel bakeItemRO$height %s' % imgSize_override)
            if bake_lowpoly:
                lx.eval('bakeItem.bake true type:1')

            # ao_large render output bake item
            # use existing render output bake item aoLarge
            try:
                bakeItemRender_aolarge = scene.item('{}{}'.format(aoLarge_Name, uvMap.name))
                bakeItemRender_aolarge.select(replace=True)
            except Exception:
                lx.eval('bakeItem.createOutputBake')
                lx.eval('item.name "%s_%s_RO" bakeItemRO' % (aoLarge_Name, uvMap.name))

            lx.eval('bakeItem.target {%s} type:1' % lpItem.name)
            lx.eval('bakeItem.source {%s} type:1' % hpItem.name)
            lx.eval('bakeItem.renderOutput {%s}' % aoLarge.name)
            lx.eval('bakeItem.setUV {%s}' % uvMap.name)
            lx.eval('item.channel bakeItemRO$bakeFrom true')

            if use_cage and bake_cage_name is not None:
                lx.eval('bakeItem.setCage "%s" render' % bake_cage_name)
                lx.eval('item.channel bakeItemRO$distance %s' % '0')
            else:
                lx.eval('item.channel bakeItemRO$distance %s' % bakeDistanceMultiplied)

            lx.eval('item.channel bakeItemRO$hiddenTarget false')
            lx.eval('item.channel bakeItemRO$hiddenSource false')
            lx.eval('item.channel bakeItemRO$hiddenOutput true')
            lx.eval('item.channel bakeItemRO$saveOutputFile true')
            lx.eval('item.channel outLocation {%s}' % newImagePath)
            lx.eval('item.channel bakeItemRO$outPattern {%s}<>' % aoLargeSaveName)
            lx.eval('bakeItem.format PNG')
            lx.eval('item.channel bakeItemRO$width %s' % imgSize_override)
            lx.eval('item.channel bakeItemRO$height %s' % imgSize_override)
            if bake_lowpoly:
                lx.eval('bakeItem.bake true type:1')

            lx.eval('select.subItem {%s:videoStill001} set mediaClip' % aoSmallSaveName)
            lx.eval('select.subItem {%s} set textureLayer;render;environment;light;camera;scene;replicator;bake;txtrLocator' % aoSmallSaveName)
            lx.eval('!clip.reload')
            lx.eval('select.subItem {%s:videoStill001} set mediaClip' % aoLargeSaveName)
            lx.eval('select.subItem {%s} set textureLayer;render;environment;light;camera;scene;replicator;bake;txtrLocator' % aoLargeSaveName)
            lx.eval('!clip.reload')

        curMask.select(True)
    return


def prepare_image_map(texture):
    # print texture
    texture.channel('pixBlend').set('bicubic')
    texture.channel('aa').set(0)


def setup_metal_material():
    global metalMasksParent
    for mask in scene.iterItems(c.MASK_TYPE):
        if metal_marker_search_text.lower() in mask.name.lower():
            for metalMask in mask.children():
                global metal_marker_present
                metal_marker_present = False
                for material in metalMask.children():
                    if material.type == 'constant' and material.channel('effect').get() == 'driverD':
                        metal_marker_present = True

                    if material.type == 'advancedMaterial':
                        material.channel('diffCol.R').set(0.0)
                        material.channel('diffCol.G').set(0.0)
                        material.channel('diffCol.B').set(0.0)
                        material.channel('diffAmt').set(0.0)

                if not metal_marker_present:
                    print('mask.name', mask.name)
                    print('metalMask', metalMask.name)
                    scene.deselect()
                    lx.eval('shader.new constant')
                    metal_marker = scene.selected[0]
                    metal_marker.channel('effect').set('driverD')
                    metal_marker.setParent(metalMask, -1)
                    scene.deselect()


print('')
print('starting...')


bake_selected = lx.eval('user.value {%s} ?' % userValSelectedName) is not 0
bake_lowpoly = lx.eval('user.value {%s} ?' % userValBakeName) is not 0
imgSizeIndex = lx.eval('user.value {%s} ?' % userValImgSizeName)
imgSize = userValImgSizeList.split(';')[int(imgSizeIndex)]
use_cage = lx.eval('user.value {%s} ?' % userValCageName) is not 0
bakeDistance = lx.eval('user.value {%s} ?' % userValBakeDistName)
scale_mult = lx.eval('user.value {%s} ?' % userValScaleName)
if scale_mult == 0.0:
    scale_mult = 1.0
    lx.eval('user.value name:{%s} value:{%s}' % (userValScaleName, scale_mult))

bakeDistanceMultiplied = bakeDistance * scale_mult

lpItem = None
hpItem = None
for item in scene.items('groupLocator'):
    if lpTag.lower() in item.name.lower():
        lpItem = item  # type: modo.Item
    if hpTag.lower() in item.name.lower():
        hpItem = item  # type: modo.Item
if lpItem is None:
    print('lowpoly item not found')
    print('cancelled')
    modo.dialogs.alert(title='cancelled', message='lowpoly item not found', dtype='warning')
    exit()
if hpItem is None:
    print('highpoly item not found')
    print('cancelled')
    modo.dialogs.alert(title='cancelled', message='highpoly item not found', dtype='warning')
    exit()

if len(lpItem.children()) < 1 or len(hpItem.children()) < 1:
    print('highpoly or lowpoly items has no children')
    print('cancelled')
    exit()

renderItem = scene.renderItem
if renderItem is None:
    print('render item not found')
    print('cancelled')
    modo.dialogs.alert(title='cancelled', message='render item not found', dtype='warning')
    exit()

# check highpoly group locator visibility
hpItemVisStatus = hpItem.channel('visible').get()
if hpItemVisStatus == 'allOff' or hpItemVisStatus == 'off':
    # show dialog to set visibility on
    dialogRes = modo.dialogs.yesNoCancel('{} item is OFF'.format(hpItem.name), 'Do you want to turn it ON?')
    if dialogRes == 'ok' or dialogRes == 'yes':
        hpItem.channel('visible').set('default')  # turn visibility ON
    elif dialogRes == 'cancel':
        print('user cancelled')
        modo.dialogs.alert(title='cancelled', message='user cancel', dtype='warning')
        exit()
    elif dialogRes == 'no':
        # do nothing
        print('{} item visibility ignored'.format(hpItem.name))
    else:
        # do nothing
        print('{} item visibility ignored'.format(hpItem.name))

# check lowpoly group locator visibility
lpItemVisStatus = lpItem.channel('visible').get()
if lpItemVisStatus == 'allOff' or lpItemVisStatus == 'off':
    # show dialog to set visibility on
    dialogRes = modo.dialogs.yesNoCancel('{} item is OFF'.format(lpItem.name), 'Do you want to turn it ON?')
    if dialogRes == 'ok' or dialogRes == 'yes':
        lpItem.channel('visible').set('default')  # turn visibility ON
    elif dialogRes == 'cancel':
        print('user cancelled')
        modo.dialogs.alert(title='cancelled', message='user cancel', dtype='warning')
        exit()
    elif dialogRes == 'no':
        # do nothing
        print('{} item visibility ignored'.format(lpItem.name))
    else:
        # do nothing
        print('{} item visibility ignored'.format(lpItem.name))

# store selection
selection_store = scene.selected

# get list of lowpoly meshes
if bake_selected:
    lpList = getLpList_selected()
else:
    lpList = getLpList_children(lpItem)

# ---------- ---------- ---------- ---------- ----------
# ---------- scaling up scene preparation

# reset all transforms on lowpoly meshes
reset_list = getLpList_children(lpItem)
for reset_item in reset_list:
    reset_item.select(replace=True)
    lx.eval('transform.freeze')
    while len(reset_item.transforms) > 0:
        transform = reset_item.transforms[0]
        reset_item.transforms.delete(transform)

# store lpItem parent
lpItem_parent_store = lpItem.parent
# store hpItem parent
hpItem_parent_store = hpItem.parent

# create lp_scale_loc locator and parent lpItem group to it
lp_scale_loc = scene.addItem(itype=c.LOCATOR_TYPE, name='lp_scale_loc')  # type: modo.Item
scene.deselect()  # deselect all items
lpItem.select()
lp_scale_loc.select()
if scale_mult != 1.0:
    lx.eval('item.parent inPlace:1')

# create hp_scale_loc locator and parent hpItem group to it
hp_scale_loc = scene.addItem(itype=c.LOCATOR_TYPE, name='hp_scale_loc')  # type: modo.Item
scene.deselect()
hpItem.select()
hp_scale_loc.select()
if scale_mult != 1.0:
    lx.eval('item.parent inPlace:1')
print('create hp_scale_loc locator and parent hpItem group to it')

# scaling up
hpMaterialList = []
lp_scale_freeze_loc = scene.addItem(itype=c.LOCATOR_TYPE, name='lp_scale_freeze_loc')  # type: modo.Item
if scale_mult != 1.0:
    print('use scale x{}'.format(scale_mult))
    ao_small_dist = ao_small_dist * scale_mult
    ao_large_dist = ao_large_dist * scale_mult
    # scale up highpoly and lowpoly locators
    lp_scale_loc.scale.x.set(lp_scale_loc.scale.x.get() * scale_mult)
    lp_scale_loc.scale.y.set(lp_scale_loc.scale.y.get() * scale_mult)
    lp_scale_loc.scale.z.set(lp_scale_loc.scale.z.get() * scale_mult)
    hp_scale_loc.scale.x.set(hp_scale_loc.scale.x.get() * scale_mult)
    hp_scale_loc.scale.y.set(hp_scale_loc.scale.y.get() * scale_mult)
    hp_scale_loc.scale.z.set(hp_scale_loc.scale.z.get() * scale_mult)

    # scale up rounded edge width in every material
    for advMat in scene.items(itype=lx.symbol.sITYPE_ADVANCEDMATERIAL):
        if advMat.parent.name[:len(lpMatTag)] != lpMatTag:
            hpMaterialList.append(advMat)
    for material in hpMaterialList:
        material.channel('rndWidth').set(material.channel('rndWidth').get() * scale_mult)
    print('scale up')

    # freeze transforms for lowpoly items, reset transforms for lp_scale_loc
    # create lp_freeze_loc and parent lpItem children to it
    scene.deselect()
    for lp_child in lpItem.children():
        lp_child.select()
    lp_scale_freeze_loc.select()
    lx.eval('item.parent inPlace:1')
    print('create lp_freeze_loc and parent lpItem children to it')
    # freeze scale for lp_scale_freeze_loc children
    scene.deselect()
    for lp_child in lp_scale_freeze_loc.children(recursive=True):
        lp_child.select()
    lx.eval('transform.freeze scale')
    print('freeze scale for lp_scale_freeze_loc children')
    # reset scale for lp_scale_loc
    lp_scale_loc.select(replace=True)
    lx.eval('transform.reset scale')
    print('reset scale for lp_scale_loc')
    # parent lp_scale_freeze children to lpItem
    scene.deselect()
    for lp_child in lp_scale_freeze_loc.children():
        lp_child.select()
    lpItem.select()
    lx.eval('item.parent inPlace:1')
    print('parent lp_scale_freeze children to lpItem')

    # ---------- end of scaling up operations
    # ---------- ---------- ---------- ---------- ----------

scene.deselect()
for mesh_item in lpList:  # select each  items in list
    mesh_item.select()
print('low poly items found:', len(lpList))

print('current project name: <{}>'.format(get_project_name()))

if get_project_name() == '':
    project_name = os.path.splitext(scene.name)[0]
    set_project_name(project_name)

# prepare metal materials
setup_metal_material()

# prepare hires mesh textures
imageMapList = scene.items(itype='imageMap')
hires_materials = imageMapList
for imageMap in hires_materials:
    prepare_image_map(imageMap)

try:
    aoSmall = scene.item(aoSmall_Name)  # check if aoSmall exist
    lx.eval('shader.setVisible "%s" true' % aoSmall.name)
except LookupError:
    aoSmall = scene.addItem('renderOutput')  # add ao_small render output
    aoSmall.setParent(renderItem, renderItem.childCount())
    aoSmall.name = aoSmall_Name
    aoSmall.channel('effect').set('occl.ambient')
aoSmall.select(replace=True)
lx.eval('item.channel colorspace (none)')
lx.eval('item.channel renderOutput$occlRays %s' % ao_small_rays)
lx.eval('item.channel renderOutput$occlRange %s' % ao_small_dist)

try:
    aoLarge = scene.item(aoLarge_Name)  # check if aoLarge exist
    lx.eval('shader.setVisible "%s" true' % aoLarge.name)
except LookupError:
    aoLarge = scene.addItem('renderOutput')  # add ao_large render output
    aoLarge.setParent(renderItem, renderItem.childCount())
    aoLarge.name = aoLarge_Name
    aoLarge.channel('effect').set('occl.ambient')
aoLarge.select(replace=True)
lx.eval('item.channel colorspace (none)')
lx.eval('item.channel renderOutput$occlRays %s' % ao_large_rays)
lx.eval('item.channel renderOutput$occlRange %s' % ao_large_dist)

for mesh in lpList:
    createLpMaterial(mesh)

lx.eval('shader.setVisible "%s" false' % aoSmall.name)
lx.eval('shader.setVisible "%s" false' % aoLarge.name)

for image in newImageMaps:
    # print image, ':', image.name
    videoClip = image.itemGraph('shadeLoc').forward(1)
    lx.eval('select.subItem {%s:videoStill001} set textureLayer;mediaClip' % videoClip.name)
    lx.eval('clip.save')
    lx.eval('!clip.reload')

for nMap in normalMaps:
    videoClip = nMap.itemGraph('shadeLoc').forward(1)
    lx.eval('select.subItem {%s:videoStill001} set textureLayer;mediaClip' % videoClip.name)
    lx.eval('!clip.reload')

if scale_mult != 1.0:
    # scale down highpoly and lowpoly locators
    lp_scale_loc.scale.x.set(lp_scale_loc.scale.x.get() / scale_mult)
    lp_scale_loc.scale.y.set(lp_scale_loc.scale.y.get() / scale_mult)
    lp_scale_loc.scale.z.set(lp_scale_loc.scale.z.get() / scale_mult)
    hp_scale_loc.scale.x.set(hp_scale_loc.scale.x.get() / scale_mult)
    hp_scale_loc.scale.y.set(hp_scale_loc.scale.y.get() / scale_mult)
    hp_scale_loc.scale.z.set(hp_scale_loc.scale.z.get() / scale_mult)
    print('scale down highpoly and lowpoly locators')

    # parent lpItem children to lp_scale_freeze_loc
    scene.deselect()
    for lp_child in lpItem.children():
        lp_child.select()
    lp_scale_freeze_loc.select()
    lx.eval('item.parent inPlace:1')
    print('parent lpItem children to lp_scale_freeze_loc')

    # freeze scale for every lp_scale_freeze_loc children
    scene.deselect()
    for lp_child in lp_scale_freeze_loc.children(recursive=True):
        lp_child.select()
    lx.eval('transform.freeze scale')
    print('freeze scale for every lp_scale_freeze_loc children')

    # reset scale for lp_scale_loc
    lp_scale_loc.select(replace=True)
    lx.eval('transform.reset scale')
    print('reset scale for lp_scale_loc')

    # parent lp_scale_freeze_loc children back to lpItem
    scene.deselect()
    for lp_child in lp_scale_freeze_loc.children():
        lp_child.select()
    lpItem.select()
    lx.eval('item.parent inPlace:1')
    print('parent lp_scale_freeze_loc children back to lpItem')

    # unparent lpItem from lp_scale_loc
    lpItem.select(replace=True)
    if lpItem_parent_store is None:
        lx.eval('item.parent parent:{} inPlace:1')
    else:
        lpItem_parent_store.select()
        lx.eval('item.parent inPlace:1')
    # unparent hpItem from hp_scale_loc
    hpItem.select(replace=True)
    if hpItem_parent_store is None:
        lx.eval('item.parent parent:{} inPlace:1')
    else:
        hpItem_parent_store.select()
        lx.eval('item.parent inPlace:1')

    # scale down every material rounded edge width
    for material in hpMaterialList:
        material.channel('rndWidth').set(material.channel('rndWidth').get() / scale_mult)

    print('scale down every material rounded edge width')

# delete all temporal scaling items
scene.removeItems(lp_scale_loc)
scene.removeItems(hp_scale_loc)
scene.removeItems(lp_scale_freeze_loc)
print('delete all temporal scaling items')

# enable all baked materials
for mask in scene.items(itype='mask'):
    if mask.name[:3] == 'lp_':
        mask.channel('enable').set(1)

# turn off hires mesh items
hpItem.channel('visible').set('allOff')

# restore selection
scene.deselect()
for item in selection_store:
    try:
        item.select()
    except LookupError:
        print('item <{}>:<{}>:<{}> can\'t be reselected'.format(item, item.name, item.type))

print('done.')
