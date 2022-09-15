#!/usr/bin/python
# ================================
# (C)2019-2021 Dmytro Holub
# heap3d@gmail.com
# --------------------------------
# modo python
# EMAG
# toybox
# bake from lowpoly to gltf
# ================================

import lx
import modo
import os.path
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
    # print 'projectPath :', projectPath
    scene_name = get_project_name()
    if scene_name != '':
        scene_name += '\\'
    dirPath = projectPath + '\\Images\\baking\\' + scene_name
    if not os.path.exists(dirPath):
        try:
            os.mkdir(dirPath)
        except:
            print('os.mkdir error')
            print('os.mkdir("%s")' % dirPath)
            pass
    path = dirPath
    # print 'temp path :', path
    if not os.path.exists(path):
        path = modo.dialogs.dirBrowse('Choose directory for baked images:', projectPath)
        if path is None:
            path = scene.filename
            path = path.rpartition('\\')[0]+'\\'
            print('extracted from filename: %s' % path)
        else:
            path = '%s\\' % path
    newImagePath = path
    print('images path : %s' % path)
    return path


def getImagePath_tmp():
    path_tmp = '%stmp\\' % getImagePath()
    if not os.path.exists(path_tmp):
        try:
            os.mkdir(path_tmp)
        except:
            path_tmp = getImagePath()
            # print 'tmp dir making error'
    # print 'path_tmp = %s' % path_tmp
    return path_tmp


def meshProcessed(mesh):
    if mesh.geometry.numPolygons <= 0:
        print('no polygons in mesh: %s' % mesh.name)
        return True
    if splitTag.lower() in mesh.name.lower():
        print('split tag found in mesh: %s' % mesh.name)
        return True
    # if udimPartTag.lower() in mesh.name.lower():
    #     print 'udim part tag found in mesh: %s' % mesh.name
    #     return True
    return False


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
                print('Raising exeption. start: <{}>   end: <{}>'.format(start, end))
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

    # print 'UV Map: <{}> - resolution override set to [{}]'.format(name, resolution)
    return resolution


def generateMaterials(mesh):
    for vmap in mesh.geometry.vmaps.uvMaps:
        # print vmap, ':', vmap.name
        # print mesh, ':', mesh.name
        searchName = mesh.name.split(splitTag)[1]
        # print 'searchName:', searchName, 'vmap.name:', vmap.name, 'mesh.name:', mesh.name
        if searchName == vmap.name:
            uvMap = vmap
    # print 'generateMaterials', ':', mesh, ':', mesh.name, ':',  uvMap, ':', uvMap.name
    newImagePath = getImagePath()
    newImagePath_tmp = getImagePath_tmp()
    # baseIndex = 0
    masterShader = None
    for item in scene.renderItem.children(recursive=False, itemType='mask'):
        baseIndex = item.parentIndex + 1
    for item in scene.renderItem.children():
        if item.type == 'defaultShader':
            masterShader = item
            baseIndex = masterShader.parentIndex
    # print masterShader
    if masterShader is None:
        # print 'before addItem'
        masterShader = scene.addItem('defaultShader')
        print('default shader added : %s' % masterShader.name)

    masterShader.setParent(scene.renderItem, index=baseIndex)
    mask = scene.addItem('mask')
    mask.select(True)
    lx.eval('item.editorColor lightblue')
    lx.eval('shader.setVisible "%s" false' % mask.name)
    mask.setParent(scene.renderItem, index=baseIndex)
    mask.itemGraph('shadeLoc') >> mesh.itemGraph('shadeLoc')
    # print 'generating %s mask' % mask.name

    mask_1 = scene.addItem('mask', '%s ao_ro_me_lum_norm *RGB*' % pass_1)
    mask_1.setParent(mask, -1)
    mask_1.select(True)
    lx.eval('item.editorColor lightgreen')
    lx.eval('shader.setVisible "%s" false' % mask_1.name)
    grad_ro = scene.addItem('gradient', 'roughness')
    grad_ro.setParent(mask_1, -1)
    grad_ro.select(True)
    grad_ro.channel('color.R').envelope.keyframes[0] = (0.0, 0.0)
    grad_ro.channel('color.G').envelope.keyframes[0] = (0.0, 0.0)
    grad_ro.channel('color.G').envelope.keyframes.add(1.0, 1.0)
    grad_ro.channel('color.G').envelope.preBehaviour = lx.symbol.iENV_LINEAR
    grad_ro.channel('color.G').envelope.postBehaviour = lx.symbol.iENV_LINEAR
    grad_ro.channel('color.B').envelope.keyframes[0] = (0.0, 0.0)
    grad_ro.channel('param').set('rough')
    grad_ro.channel('effect').set('diffColor')
    grad_me = scene.addItem('gradient', 'metallic')
    grad_me.setParent(mask_1, -1)
    grad_me.channel('color.R').envelope.keyframes[0] = (0.0, 0.0)
    grad_me.channel('color.G').envelope.keyframes[0] = (0.0, 0.0)
    grad_me.channel('color.B').envelope.keyframes[0] = (0.0, 0.0)
    grad_me.channel('color.B').envelope.keyframes.add(1.0, 1.0)
    grad_me.channel('color.B').envelope.preBehaviour = lx.symbol.iENV_LINEAR
    grad_me.channel('color.B').envelope.postBehaviour = lx.symbol.iENV_LINEAR
    grad_me.channel('param').set('driverD')  # metallic >> ao_ro_me
    grad_me.channel('effect').set('diffColor')
    grad_me.channel('blend').set('add')

    matTag = mesh.name.split(splitTag)[1]
    print('matTag :', matTag)
    aoSmallSearchName = '%s%s (Image)' % (aoSmallTag, matTag)
    aoLargeSearchName = '%s%s (Image)' % (aoLargeTag, matTag)
    print('ao search names:', aoSmallSearchName, ';', aoLargeSearchName)
    for image in scene.items('imageMap'):
        # print image, ':', image.name, ':', image.type
        if aoSmallSearchName in image.name:
            aoSmallImage = image
            # print aoSmallImage
        if aoLargeSearchName in image.name:
            aoLargeImage = image
            # print aoLargeImage
    aoSmallImage.channel('effect').set('driverC')
    aoSmallImage.channel('blend').set('normal')
    aoLargeImage.channel('effect').set('driverC')
    aoLargeImage.channel('blend').set('multiply')
    grad_ao = scene.addItem('gradient', 'ambient occlusion')
    grad_ao.setParent(mask_1, -1)
    grad_ao.channel('color.R').envelope.keyframes[0] = (0.0, 0.0)
    grad_ao.channel('color.R').envelope.keyframes.add(1.0, 1.0)
    grad_ao.channel('color.R').envelope.preBehaviour = lx.symbol.iENV_LINEAR
    grad_ao.channel('color.R').envelope.postBehaviour = lx.symbol.iENV_LINEAR
    grad_ao.channel('color.G').envelope.keyframes[0] = (0.0, 0.0)
    grad_ao.channel('color.B').envelope.keyframes[0] = (0.0, 0.0)
    grad_ao.channel('param').set('driverC')
    grad_ao.channel('effect').set('diffColor')
    grad_ao.channel('blend').set('add')

    grad_lum = scene.addItem('gradient', 'lumi color x lumi amnt')
    grad_lum.setParent(mask_1, -1)
    grad_lum.channel('color.R').envelope.keyframes[0] = (0.0, 0.0)
    grad_lum.channel('color.R').envelope.keyframes.add(1.0, 1.0)
    grad_lum.channel('color.R').envelope.preBehaviour = lx.symbol.iENV_LINEAR
    grad_lum.channel('color.R').envelope.postBehaviour = lx.symbol.iENV_LINEAR
    grad_lum.channel('color.G').envelope.keyframes[0] = (0.0, 0.0)
    grad_lum.channel('color.G').envelope.keyframes.add(1.0, 1.0)
    grad_lum.channel('color.G').envelope.preBehaviour = lx.symbol.iENV_LINEAR
    grad_lum.channel('color.G').envelope.postBehaviour = lx.symbol.iENV_LINEAR
    grad_lum.channel('color.B').envelope.keyframes[0] = (0.0, 0.0)
    grad_lum.channel('color.B').envelope.keyframes.add(1.0, 1.0)
    grad_lum.channel('color.B').envelope.preBehaviour = lx.symbol.iENV_LINEAR
    grad_lum.channel('color.B').envelope.postBehaviour = lx.symbol.iENV_LINEAR
    grad_lum.channel('param').set('lumiAmount')
    grad_lum.channel('effect').set('lumiColor')
    grad_lum.channel('blend').set('multiply')

    mask_2 = scene.addItem('mask', '%s bc_tr *RGB* --- metal: diffuse=0 spec=100' % pass_2)
    mask_2.setParent(mask, -1)
    mask_2.select(True)
    lx.eval('item.editorColor lightgreen')
    lx.eval('shader.setVisible "%s" false' % mask_2.name)
    mask_tr = scene.addItem('mask', '%s *RGB*' % pass_tr)
    mask_tr.setParent(mask_2, -1)
    mask_tr.select(True)
    lx.eval('item.editorColor lightgreen')
    lx.eval('shader.setVisible "%s" false' % mask_tr.name)
    grad_trsc = scene.addItem('gradient', 'transparency scan')
    grad_trsc.setParent(mask_tr, -1)
    grad_trsc.channel('color.R').envelope.keyframes[0] = (0.0, 1.0)
    grad_trsc.channel('color.R').envelope.keyframes.add(0.0, 1.0)
    grad_trsc.channel('color.R').envelope.preBehaviour = lx.symbol.iENV_LINEAR
    grad_trsc.channel('color.R').envelope.postBehaviour = lx.symbol.iENV_LINEAR
    grad_trsc.channel('color.G').envelope.keyframes[0] = (0.0, 1.0)
    grad_trsc.channel('color.G').envelope.keyframes.add(0.0, 1.0)
    grad_trsc.channel('color.G').envelope.preBehaviour = lx.symbol.iENV_LINEAR
    grad_trsc.channel('color.G').envelope.postBehaviour = lx.symbol.iENV_LINEAR
    grad_trsc.channel('color.B').envelope.keyframes[0] = (0.0, 1.0)
    grad_trsc.channel('color.B').envelope.keyframes.add(0.0, 1.0)
    grad_trsc.channel('color.B').envelope.preBehaviour = lx.symbol.iENV_LINEAR
    grad_trsc.channel('color.B').envelope.postBehaviour = lx.symbol.iENV_LINEAR
    grad_trsc.channel('param').set('tranAmount')
    grad_trsc.channel('effect').set('diffColor')
    mask_me = scene.addItem('mask', '%s driver D *RGB*' % pass_me_fl)
    mask_me.setParent(mask_2, -1)
    mask_me.select(True)
    lx.eval('item.editorColor lightgreen')
    lx.eval('shader.setVisible "%s" false' % mask_me.name)
    grad_mesc = scene.addItem('gradient', 'metallic scan')
    grad_mesc.setParent(mask_me, -1)
    grad_mesc.channel('color.R').envelope.keyframes[0] = (0.0, 0.0)
    grad_mesc.channel('color.R').envelope.keyframes.add(1.0, 1.0)
    grad_mesc.channel('color.R').envelope.preBehaviour = lx.symbol.iENV_LINEAR
    grad_mesc.channel('color.R').envelope.postBehaviour = lx.symbol.iENV_LINEAR
    grad_mesc.channel('color.G').envelope.keyframes[0] = (0.0, 0.0)
    grad_mesc.channel('color.G').envelope.keyframes.add(1.0, 1.0)
    grad_mesc.channel('color.G').envelope.preBehaviour = lx.symbol.iENV_LINEAR
    grad_mesc.channel('color.G').envelope.postBehaviour = lx.symbol.iENV_LINEAR
    grad_mesc.channel('color.B').envelope.keyframes[0] = (0.0, 0.0)
    grad_mesc.channel('color.B').envelope.keyframes.add(1.0, 1.0)
    grad_mesc.channel('color.B').envelope.preBehaviour = lx.symbol.iENV_LINEAR
    grad_mesc.channel('color.B').envelope.postBehaviour = lx.symbol.iENV_LINEAR
    grad_mesc.channel('param').set('driverD')
    grad_mesc.channel('effect').set('diffColor')

    mask_diffColor = scene.addItem('mask', '%s pass *RGB*' % pass_diffColorName)
    mask_diffColor.setParent(mask_2, -1)
    mask_diffColor.channel('enable').set(False)
    mask_diffColor.select(True)
    lx.eval('item.editorColor lightgreen')
    grad_diffAmountScan = scene.addItem('gradient', '__diffAmount scan')
    grad_diffAmountScan.setParent(mask_diffColor, -1)
    grad_diffAmountScan.channel('color.R').envelope.keyframes[0] = (0.0, 0.0)
    grad_diffAmountScan.channel('color.R').envelope.keyframes.add(1.0, 1.0)
    grad_diffAmountScan.channel('color.R').envelope.preBehaviour = lx.symbol.iENV_LINEAR
    grad_diffAmountScan.channel('color.R').envelope.postBehaviour = lx.symbol.iENV_LINEAR
    grad_diffAmountScan.channel('color.G').envelope.keyframes[0] = (0.0, 0.0)
    grad_diffAmountScan.channel('color.G').envelope.keyframes.add(1.0, 1.0)
    grad_diffAmountScan.channel('color.G').envelope.preBehaviour = lx.symbol.iENV_LINEAR
    grad_diffAmountScan.channel('color.G').envelope.postBehaviour = lx.symbol.iENV_LINEAR
    grad_diffAmountScan.channel('color.B').envelope.keyframes[0] = (0.0, 0.0)
    grad_diffAmountScan.channel('color.B').envelope.keyframes.add(1.0, 1.0)
    grad_diffAmountScan.channel('color.B').envelope.preBehaviour = lx.symbol.iENV_LINEAR
    grad_diffAmountScan.channel('color.B').envelope.postBehaviour = lx.symbol.iENV_LINEAR
    grad_diffAmountScan.channel('param').set('diffAmount')
    grad_diffAmountScan.channel('effect').set('diffColor')
    grad_diffAmountScan.channel('blend').set('multiply')

    mask_metalColor = scene.addItem('mask', '%s pass *RGB*' % pass_metalColorName)
    mask_metalColor.setParent(mask_2, -1)
    mask_metalColor.channel('enable').set(False)
    mask_metalColor.select(True)
    lx.eval('item.editorColor lightgreen')
    grad_specAmountScan = scene.addItem('gradient', '__specAmount scan')
    grad_specAmountScan.setParent(mask_metalColor, -1)
    grad_specAmountScan.channel('color.R').envelope.keyframes[0] = (0.0, 0.0)
    grad_specAmountScan.channel('color.R').envelope.keyframes.add(1.0, 1.0)
    grad_specAmountScan.channel('color.R').envelope.preBehaviour = lx.symbol.iENV_LINEAR
    grad_specAmountScan.channel('color.R').envelope.postBehaviour = lx.symbol.iENV_LINEAR
    grad_specAmountScan.channel('color.G').envelope.keyframes[0] = (0.0, 0.0)
    grad_specAmountScan.channel('color.G').envelope.keyframes.add(1.0, 1.0)
    grad_specAmountScan.channel('color.G').envelope.preBehaviour = lx.symbol.iENV_LINEAR
    grad_specAmountScan.channel('color.G').envelope.postBehaviour = lx.symbol.iENV_LINEAR
    grad_specAmountScan.channel('color.B').envelope.keyframes[0] = (0.0, 0.0)
    grad_specAmountScan.channel('color.B').envelope.keyframes.add(1.0, 1.0)
    grad_specAmountScan.channel('color.B').envelope.preBehaviour = lx.symbol.iENV_LINEAR
    grad_specAmountScan.channel('color.B').envelope.postBehaviour = lx.symbol.iENV_LINEAR
    grad_specAmountScan.channel('param').set('specAmount')
    grad_specAmountScan.channel('effect').set('specColor')
    grad_specAmountScan.channel('blend').set('multiply')

    mask_3 = scene.addItem('mask', '%s bc *RGB*' % pass_3)
    mask_3.setParent(mask, -1)
    mask_3.select(True)
    lx.eval('item.editorColor lightgreen')
    lx.eval('shader.setVisible "%s" false' % mask_3.name)

    imgSize_override = get_resolution_override(uvMap.name)

    imgName_ao_ro_me = '%s%s' % (mesh.name, sfx_ao_ro_me)
    lx.eval('clip.newStill "%s%s.png" x%s RGB false false format:PNG' % (newImagePath, imgName_ao_ro_me, imgSize_override))
    img_ao_ro_me = scene.addItem('imageMap')
    img_ao_ro_me.setParent(mask_1, -1)
    img_ao_ro_me.select(True)
    lx.eval('item.editorColor red')
    lx.eval('shader.setVisible "%s" false' % img_ao_ro_me.name)
    lx.eval('select.subItem {%s:videoStill001} set mediaClip' % imgName_ao_ro_me)
    lx.eval('texture.setIMap {%s:videoStill001}' % imgName_ao_ro_me)
    lx.eval('item.channel textureLayer(txtrLocator)$projType uv')
    lx.eval('texture.setUV "%s"' % uvMap.name)
    img_ao_ro_me.channel('effect').set('diffColor')
    # print 'after ao ro me'

    imgName_norm = '%s%s' % (mesh.name, sfx_norm)
    lx.eval('clip.newStill "%s%s.png" x%s RGB false false format:PNG' % (newImagePath, imgName_norm, imgSize_override))
    img_norm = scene.addItem('imageMap')
    img_norm.setParent(mask_1, -1)
    img_norm.select(True)
    lx.eval('item.editorColor red')
    lx.eval('shader.setVisible "%s" false' % img_norm.name)
    lx.eval('select.subItem {%s:videoStill001} set mediaClip' % imgName_norm)
    lx.eval('texture.setIMap {%s:videoStill001}' % imgName_norm)
    lx.eval('item.channel textureLayer(txtrLocator)$projType uv')
    lx.eval('texture.setUV "%s"' % uvMap.name)
    img_norm.channel('effect').set('normal')
    lx.eval('select.subItem {%s:videoStill001} set mediaClip' % imgName_norm)
    lx.eval('select.subItem %s set textureLayer' % img_norm.id)
    lx.eval('item.channel colorspace (none)')
    # print 'after norm'

    imgName_lum = '%s%s' % (mesh.name, sfx_lum)
    lx.eval('clip.newStill "%s%s.png" x%s RGB false false format:PNG' % (newImagePath, imgName_lum, imgSize_override))
    img_lum = scene.addItem('imageMap')
    img_lum.setParent(mask_1, -1)
    img_lum.select(True)
    lx.eval('item.editorColor red')
    lx.eval('shader.setVisible "%s" false' % img_lum.name)
    lx.eval('select.subItem {%s:videoStill001} set mediaClip' % imgName_lum)
    lx.eval('texture.setIMap {%s:videoStill001}' % imgName_lum)
    lx.eval('item.channel textureLayer(txtrLocator)$projType uv')
    lx.eval('texture.setUV "%s"' % uvMap.name)
    img_lum.channel('effect').set('lumiColor')
    # print 'after lum'

    imgName_tr_tmp = '%s%s' % (mesh.name, sfx_tr_tmp)
    lx.eval('clip.newStill "%s%s.png" x%s RGB false false format:PNG' % (newImagePath_tmp, imgName_tr_tmp, imgSize_override))
    img_tr_tmp = scene.addItem('imageMap')
    img_tr_tmp.setParent(mask_tr, -1)
    img_tr_tmp.select(True)
    lx.eval('item.editorColor red')
    lx.eval('shader.setVisible "%s" false' % img_tr_tmp.name)
    lx.eval('select.subItem {%s:videoStill001} set mediaClip' % imgName_tr_tmp)
    lx.eval('texture.setIMap {%s:videoStill001}' % imgName_tr_tmp)
    lx.eval('item.channel textureLayer(txtrLocator)$projType uv')
    lx.eval('texture.setUV "%s"' % uvMap.name)
    img_tr_tmp.channel('effect').set('diffColor')
    # print 'after tr tmp'

    lx.eval('clip.newStill "%s%s.png" x%s RGB false false format:PNG' % (newImagePath_tmp, imgName_me_fl, imgSize_override))
    img_me_fl = scene.addItem('imageMap')
    img_me_fl.setParent(mask_me, -1)
    img_me_fl.select(True)
    lx.eval('item.editorColor red')
    lx.eval('shader.setVisible "%s" false' % img_me_fl.name)
    lx.eval('select.subItem {%s:videoStill001} set mediaClip' % imgName_me_fl)
    lx.eval('texture.setIMap {%s:videoStill001}' % imgName_me_fl)
    lx.eval('item.channel textureLayer(txtrLocator)$projType uv')
    lx.eval('texture.setUV "%s"' % uvMap.name)
    img_me_fl.channel('effect').set('diffColor')
    # print 'after me fl'

    # print 'before di di'
    lx.eval('clip.newStill "%s%s.png" x%s RGB false false format:PNG' % (newImagePath_tmp, imgName_di_di, imgSize_override))
    img_di_di = scene.addItem('imageMap')
    img_di_di.setParent(mask_diffColor, -1)
    img_di_di.select(True)
    lx.eval('item.editorColor red')
    lx.eval('shader.setVisible "%s" false' % img_di_di.name)
    lx.eval('select.subItem {%s:videoStill001} set mediaClip' % imgName_di_di)
    lx.eval('texture.setIMap {%s:videoStill001}' % imgName_di_di)
    lx.eval('item.channel textureLayer(txtrLocator)$projType uv')
    lx.eval('texture.setUV "%s"' % uvMap.name)
    img_di_di.channel('effect').set('diffColor')
    # print 'after di di'

    lx.eval('clip.newStill "%s%s.png" x%s RGB false false format:PNG' % (newImagePath_tmp, imgName_me_sp, imgSize_override))
    img_me_sp = scene.addItem('imageMap')
    img_me_sp.setParent(mask_metalColor, -1)
    img_me_sp.select(True)
    lx.eval('item.editorColor red')
    lx.eval('shader.setVisible "%s" false' % img_me_sp.name)  # disable img_me_sp
    lx.eval('select.subItem {%s:videoStill001} set mediaClip' % imgName_me_sp)
    lx.eval('texture.setIMap {%s:videoStill001}' % imgName_me_sp)
    lx.eval('item.channel textureLayer(txtrLocator)$projType uv')
    lx.eval('texture.setUV "%s"' % uvMap.name)
    img_me_sp.channel('effect').set('specColor')
    # print 'after me sp'

    img3_me_sp = scene.addItem('imageMap')
    img3_me_sp.setParent(mask_3, -1)
    img3_me_sp.select(True)
    lx.eval('item.editorColor pink')
    lx.eval('shader.setVisible "%s" false' % img3_me_sp.name)  # disable img3_me_sp
    lx.eval('select.subItem {%s:videoStill001} set mediaClip' % imgName_me_sp)
    lx.eval('texture.setIMap {%s:videoStill001}' % imgName_me_sp)
    lx.eval('item.channel textureLayer(txtrLocator)$projType uv')
    lx.eval('texture.setUV "%s"' % uvMap.name)
    img3_me_sp.channel('effect').set('diffColor')
    # print 'after img3 me sp'

    # print 'before img3 me fl'
    img3_me_fl = scene.addItem('imageMap')
    img3_me_fl.setParent(mask_3, -1)
    img3_me_fl.select(True)
    lx.eval('item.editorColor pink')
    lx.eval('shader.setVisible "%s" false' % img3_me_fl.name)  # disable img3_me_fl
    lx.eval('select.subItem {%s:videoStill001} set mediaClip' % imgName_me_fl)
    lx.eval('texture.setIMap {%s:videoStill001}' % imgName_me_fl)
    lx.eval('item.channel textureLayer(txtrLocator)$projType uv')
    lx.eval('texture.setUV "%s"' % uvMap.name)
    img3_me_fl.channel('effect').set('diffColor')
    img3_me_fl.channel('blend').set('multiply')
    # print 'after img3 me fl'

    img3_di_di = scene.addItem('imageMap')
    img3_di_di.setParent(mask_3, -1)
    img3_di_di.select(True)
    lx.eval('item.editorColor pink')
    lx.eval('shader.setVisible "%s" false' % img3_di_di.name)  # disable img3_di_di
    lx.eval('select.subItem {%s:videoStill001} set mediaClip' % imgName_di_di)
    lx.eval('texture.setIMap {%s:videoStill001}' % imgName_di_di)
    lx.eval('item.channel textureLayer(txtrLocator)$projType uv')
    lx.eval('texture.setUV "%s"' % uvMap.name)
    img3_di_di.channel('effect').set('diffColor')
    img3_di_di.channel('blend').set('add')
    # print 'after img3 di di'

    imgName_bc_tmp = '%s%s' % (mesh.name, sfx_bc_tmp)
    lx.eval('clip.newStill "%s%s.png" x%s RGB false false format:PNG' % (newImagePath_tmp, imgName_bc_tmp, imgSize_override))
    img_bc_tmp = scene.addItem('imageMap')
    img_bc_tmp.setParent(mask_3, -1)
    img_bc_tmp.select(True)
    lx.eval('item.editorColor red')
    lx.eval('shader.setVisible "%s" false' % img_bc_tmp.name)  # disable img_bc_tmp
    lx.eval('select.subItem {%s:videoStill001} set mediaClip' % imgName_bc_tmp)
    lx.eval('texture.setIMap {%s:videoStill001}' % imgName_bc_tmp)
    lx.eval('item.channel textureLayer(txtrLocator)$projType uv')
    lx.eval('texture.setUV "%s"' % uvMap.name)
    img_bc_tmp.channel('effect').set('diffColor')
    # print 'after bc tmp'

    return mesh


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


def getTodoList():  # selected meshes except processed(detection by key words in name)
    lpItem = None
    for item in scene.items('groupLocator'):
        if lpTag.lower() in item.name.lower():
            # print item.name
            lpItem = item
            # print 'lpItem:', lpItem.id, lpItem.name
    if lpItem is None:
        print('lowpoly item not found')
        print('cancelled')
        modo.dialogs.alert(title='cancelled', message='lowpoly item not found', dtype='warning')
        exit()

    # get list of lowpoly meshes
    if bake_selected:
        lpList = getLpList_selected()
    else:
        lpList = getLpList_children(lpItem)
    scene.deselect()  # deselect all items
    for mesh_item in lpList:  # select each  items in list
        mesh_item.select()
    print('low poly items found:', len(lpList))

    meshSelected = scene.selectedByType('mesh')
    todoList = set()

    # -----filter out processed meshes
    for mesh in meshSelected:
        if not meshProcessed(mesh):
            todoList.add(mesh)
        else:
            print('todo list: %s - filtered out' % mesh.name)
            continue
    return todoList


def getUvMapsNameList(todo_list):
    uvMapsNameList = set()
    for mesh in todo_list:
        for uvMap in mesh.geometry.vmaps.uvMaps:
            uvMapsNameList.add(uvMap.name)
    return uvMapsNameList


def prepare_image_map(preparing_texture):
    # print texture
    preparing_texture.channel('pixBlend').set('nearest')
    preparing_texture.channel('aa').set(0)


print('')
print('starting...')

# if not lx.eval('query scriptsysservice userValue.isDefined ? {%s}' % userValSelectedName):
#     lx.eval('user.defNew {%s} boolean life:config' % userValSelectedName)
#     lx.eval('user.def {%s} username {%s}' % (userValSelectedName, userValSelectedUsername))
#     lx.eval('user.def {%s} dialogname {%s}' % (userValSelectedName, userValSelectedDialogname))
#     lx.eval('user.value {%s} %s' % (userValSelectedName, 'false'))
# if not lx.eval('query scriptsysservice userValue.isDefined ? {%s}' % userValBakeName):
#     lx.eval('user.defNew {%s} boolean life:config' % userValBakeName)
#     lx.eval('user.def {%s} username {%s}' % (userValBakeName, userValBakeUsername))
#     lx.eval('user.def {%s} dialogname {%s}' % (userValBakeName, userValBakeDialogname))
#     lx.eval('user.value {%s} %s' % (userValBakeName, 'true'))
# if not lx.eval('query scriptsysservice userValue.isDefined ? {%s}' % userValImgSizeName):
#     lx.eval('user.defNew {%s} integer life:config' % userValImgSizeName)
#     lx.eval('user.def {%s} list {%s}' % (userValImgSizeName, userValImgSizeList))
#     lx.eval('user.def {%s} username {%s}' % (userValImgSizeName, userValImgSizeUsername))
#     lx.eval('user.def {%s} dialogname {%s}' % (userValImgSizeName, userValImgSizeDialogname))
#     lx.eval('user.value {%s} %s' % (userValImgSizeName, 4))

bake_selected = lx.eval('user.value {%s} ?' % userValSelectedName) is not 0
bakeOn = lx.eval('user.value {%s} ?' % userValBakeName) is not 0
imgSizeIndex = lx.eval('user.value {%s} ?' % userValImgSizeName)
imgSize = userValImgSizeList.split(';')[int(imgSizeIndex)]

# prepare image maps for sharp baking
mask_list = scene.items(itype='mask')
for mask in mask_list:
    if mask.name[:3] == 'lp_':
        for imageMap in mask.childrenByType('imageMap'):
            prepare_image_map(imageMap)

todoList = getTodoList()
# for mesh in todoList:
#     print mesh, ':', mesh.name
# TODO baked group locator should not be duplicated
try:
    meshByUvGroupLocator = scene.item(bakedGroupMarker)
except LookupError:
    meshByUvGroupLocator = scene.addItem('groupLocator', bakedGroupMarker)
meshByUvGroupLocator.setParent()
meshByUvList = set()
uvMapsNameList = getUvMapsNameList(todoList)
for uvMapName in uvMapsNameList:
    # print uvMapName
    scene.deselect()
    # print 'scene selected', scene.selected
    for mesh in todoList:
        scene.select(mesh, True)
    lx.eval('select.drop polygon')
    lx.eval('vertMap.list txuv "%s"' % uvMapName)
    lx.eval('select.unmapPolygon "%s" true' % uvMapName)
    lx.eval('select.cut')
    newMesh = scene.addMesh('%s%s' % (splitTag, uvMapName))
    newMesh.setParent(meshByUvGroupLocator)
    newMesh.select(True)
    lx.eval('select.paste')
    meshByUvList.add(newMesh)
# -----create materials for baking from updated material list
for mesh in meshByUvList:
    # print mesh, ':', mesh.name
    generateMaterials(mesh)
# -----bake textures
for item in meshByUvList:
    scene.deselect()    #deselect all
    # print
    # print 'deselect all'
    # print scene.selected
    print(item, ':', item.name)
    item.select(True)   #select mesh
    masterMask = None
    passOne = None
    passTwo = None
    passThree = None
    passTransparency = None
    passMetallicFlag = None
    pass_metalColor = None
    pass_diffColor = None
    texture_ao_ro_me = None
    texture_norm = None
    texture_lum = None
    texture_tr_tmp = None
    texture_me_fl = None
    texture_di_di = None
    texture_me_sp = None
    texture_bc_tmp = None
    # -----find master mask for item
    for mask in scene.iterItemsFast('mask'):
        if ('%s (Item)' % item.name) in mask.name:
            masterMask = mask
    # -----fill all pass variables
    for mask in masterMask.children(recursive=True, itemType='mask'):
        if pass_1 in mask.name:
            passOne = mask
            # print 'passOne found:', passOne.name
            continue
        if pass_2 in mask.name:
            passTwo = mask
            # print 'passTwo found:', passTwo.name
            continue
        if pass_3 in mask.name:
            passThree = mask
            # print 'passThree found:', passThree.name
            continue
        if pass_tr in mask.name:
            passTransparency = mask
            # print 'passTransparency found:', passTransparency.name
            continue
        if pass_me_fl in mask.name:
            passMetallicFlag = mask
            # print 'passMetallicFlag found:', passMetallicFlag.name
            continue
    for texture in passOne.children():
        if sfx_ao_ro_me in texture.name:
            texture_ao_ro_me = texture
            # print 'texture_ao_ro_me found:', texture_ao_ro_me.name
            continue
        if sfx_norm in texture.name:
            texture_norm = texture
            # print 'texture_norm found:', texture_norm.name
            continue
        if sfx_lum in texture.name:
            texture_lum = texture
            # print 'texture_lum found:', texture_norm.name
            continue
    for texture in passTwo.children():
        # print 'passTwo.children:', texture.name
        # print '   ', pass_metalColorName, ':', texture.name
        # print '   ', pass_diffColorName, ':', texture.name
        if pass_metalColorName in texture.name:
            pass_metalColor = texture
            # print 'pass_metalColor found:', pass_metalColor.name
            continue
        if pass_diffColorName in texture.name:
            pass_diffColor = texture
            # print 'pass_diffColor found:', pass_diffColor.name
            continue
    for texture in pass_metalColor.children():
        # print 'pass_metalColor:', texture.name
        if sfx_me_sp in texture.name:
            texture_me_sp = texture
            # print 'texture_me_sp found:', texture_me_sp.name
            continue
    for texture in pass_diffColor.children():
        # print 'pass_diffColor.children:', texture.name
        if sfx_di_di in texture.name:
            texture_di_di = texture
            # print 'texture_di_di found:', texture_di_di.name
            continue
    for texture in passTransparency.children():
        if sfx_tr_tmp in texture.name:
            texture_tr_tmp = texture
            # print 'texture_tr_tmp found:', texture_tr_tmp.name
            continue
    for texture in passMetallicFlag.children():
        if sfx_me_fl in texture.name:
            texture_me_fl = texture
            # print 'texture_me_fl found:', texture_me_fl.name
            continue

    for texture in passThree.children():
        if sfx_bc_tmp in texture.name:
            texture_bc_tmp = texture
            # print 'texture_bc_tmp found:', texture_bc_tmp.name
            continue
        if sfx_me_fl in texture.name:
            pass_3_me_fl = texture
            # print 'pass_3_me_fl found:', pass_3_me_fl.name
            continue
        if sfx_di_di in texture.name:
            pass_3_di_di = texture
            # print 'pass_3_di_di found:', pass_3_di_di.name
            continue
        if sfx_me_sp in texture.name:
            pass_3_me_sp = texture
            # print 'pass_3_me_sp found:', pass_3_me_sp.name
            continue

    print(item, ':', item.name)
    # do image maps preparation before every baking
    # -----bake pass 1
    lx.eval('shader.setVisible "%s" true' % masterMask.name)  # enable master mask

    lx.eval('shader.setVisible "%s" true' % passOne.name)  # enable pass 1 mask
    # lx.eval('shader.setVisible "%s" true' % texture_ao_ro_me.name)  # enable ao_ro_me texture
    texture_ao_ro_me.select(True)
    # print 'ao_ro_me :', texture_ao_ro_me, ':', texture_ao_ro_me.name
    # image maps preparation
    for imageMap in scene.items(itype='imageMap'):
        prepare_image_map(imageMap)
    if bakeOn:
        lx.eval('bake.toTexture')  # bake ao_ro_me texture
    videoClip = texture_ao_ro_me.itemGraph('shadeLoc').forward(1)
    lx.eval('select.subItem {%s:videoStill001} set textureLayer;mediaClip' % videoClip.name)
    if bakeOn:
        lx.eval('clip.save')
    # lx.eval('!clip.reload')

    # lx.eval('shader.setVisible "%s" false' % texture_ao_ro_me.name)  # disable ao_ro_me texture
    # lx.eval('shader.setVisible "%s" true' % texture_norm.name)  # enable norm texture
    texture_norm.select(True)
    # print 'norm :', texture_norm, ':', texture_norm.name
    # image maps preparation
    for imageMap in scene.items(itype='imageMap'):
        prepare_image_map(imageMap)
    if bakeOn:
        lx.eval('bake.toTexture')  # bake norm texture
    videoClip = texture_norm.itemGraph('shadeLoc').forward(1)
    lx.eval('select.subItem {%s:videoStill001} set textureLayer;mediaClip' % videoClip.name)
    if bakeOn:
        lx.eval('clip.save')
    # lx.eval('!clip.reload')

    # lx.eval('shader.setVisible "%s" false' % texture_norm.name)  # disable norm texture
    # lx.eval('shader.setVisible "%s" true' % texture_lum.name)  # enable lum texture
    texture_lum.select(True)
    # print 'lum :', texture_lum, ':', texture_lum.name
    # image maps preparation
    for imageMap in scene.items(itype='imageMap'):
        prepare_image_map(imageMap)
    if bakeOn:
        lx.eval('bake.toTexture')  # bake lum texture
    videoClip = texture_lum.itemGraph('shadeLoc').forward(1)
    lx.eval('select.subItem {%s:videoStill001} set textureLayer;mediaClip' % videoClip.name)
    if bakeOn:
        lx.eval('clip.save')
    # lx.eval('!clip.reload')

    # lx.eval('shader.setVisible "%s" false' % texture_lum.name)  # disable lum texture
    lx.eval('shader.setVisible "%s" false' % passOne.name) # disable pass 1 mask

    # -----bake pass 2
    lx.eval('shader.setVisible "%s" true' % passTwo.name)  # enable pass 2 mask
    lx.eval('shader.setVisible "%s" true' % passTransparency.name)  # enable transparency pass
    # lx.eval('shader.setVisible "%s" true' % texture_tr_tmp.name)  # enable tr_tmp texture
    texture_tr_tmp.select(True)
    # print 'tr_tmp :', texture_tr_tmp, ':', texture_tr_tmp.name
    # image maps preparation
    for imageMap in scene.items(itype='imageMap'):
        prepare_image_map(imageMap)
    if bakeOn:
        lx.eval('bake.toTexture')  # bake tr_tmp texture
    videoClip = texture_tr_tmp.itemGraph('shadeLoc').forward(1)
    lx.eval('select.subItem {%s:videoStill001} set textureLayer;mediaClip' % videoClip.name)
    if bakeOn:
        lx.eval('clip.save')
    # lx.eval('!clip.reload')

    # lx.eval('shader.setVisible "%s" false' % texture_tr_tmp.name)  # disable tr_tmp texture
    lx.eval('shader.setVisible "%s" false' % passTransparency.name)  # disable transparency pass
    lx.eval('shader.setVisible "%s" true' % passMetallicFlag.name)  # enable metallic flag pass
    # lx.eval('shader.setVisible "%s" true' % texture_me_fl.name)  # enable me_fl texture
    texture_me_fl.select(True)
    # print 'me_fl :', texture_me_fl, ':', texture_me_fl.name
    # image maps preparation
    for imageMap in scene.items(itype='imageMap'):
        prepare_image_map(imageMap)
    if bakeOn:
        lx.eval('bake.toTexture')  # bake me_fl texture
    videoClip = texture_me_fl.itemGraph('shadeLoc').forward(1)
    lx.eval('select.subItem {%s:videoStill001} set textureLayer;mediaClip' % videoClip.name)
    if bakeOn:
        lx.eval('clip.save')
    # lx.eval('!clip.reload')

    lx.eval('shader.setVisible "%s" false' % passMetallicFlag.name)  # disable metallic flag pass
    lx.eval('shader.setVisible "%s" true' % pass_diffColor.name)  # enable diffuse color pass
    texture_di_di.select(True)
    # print 'di_di :', texture_di_di, ':', texture_di_di.name
    # image maps preparation
    for imageMap in scene.items(itype='imageMap'):
        prepare_image_map(imageMap)
    if bakeOn:
        lx.eval('bake.toTexture')  # bake di_di texture
    videoClip = texture_di_di.itemGraph('shadeLoc').forward(1)
    lx.eval('select.subItem {%s:videoStill001} set textureLayer;mediaClip' % videoClip.name)
    if bakeOn:
        lx.eval('clip.save')
    # lx.eval('!clip.reload')

    lx.eval('shader.setVisible "%s" false' % pass_diffColor.name)  # disable diffuse color pass
    lx.eval('shader.setVisible "%s" true' % pass_metalColor.name)  # enable metallic color pass
    texture_me_sp.select(True)
    # print 'me_sp :', texture_me_sp, ':', texture_me_sp.name
    # image maps preparation
    for imageMap in scene.items(itype='imageMap'):
        prepare_image_map(imageMap)
    if bakeOn:
        lx.eval('bake.toTexture')  # bake me_sp texture
    videoClip = texture_me_sp.itemGraph('shadeLoc').forward(1)
    lx.eval('select.subItem {%s:videoStill001} set textureLayer;mediaClip' % videoClip.name)
    if bakeOn:
        lx.eval('clip.save')
    # lx.eval('!clip.reload')

    lx.eval('shader.setVisible "%s" false' % pass_metalColor.name)  # disable metallic color pass
    lx.eval('shader.setVisible "%s" false' % passTwo.name)  # disable pass 2 mask

    # -----bake pass 3
    # print passThree, ':', passThree.name
    passThree.channel('enable').set(True)
    pass_3_me_sp.channel('enable').set(True)
    pass_3_me_fl.channel('enable').set(True)
    pass_3_di_di.channel('enable').set(True)
    # lx.eval('shader.setVisible "%s" true' % texture_bc_tmp.name)  # enable bc_tmp texture
    texture_bc_tmp.select(True)
    # print 'bc_tmp :', texture_bc_tmp, ':', texture_bc_tmp.name
    # image maps preparation
    for imageMap in scene.items(itype='imageMap'):
        prepare_image_map(imageMap)
    if bakeOn:
        lx.eval('bake.toTexture')  # bake bc_tmp texture
    videoClip = texture_bc_tmp.itemGraph('shadeLoc').forward(1)
    lx.eval('select.subItem {%s:videoStill001} set textureLayer;mediaClip' % videoClip.name)
    if bakeOn:
        lx.eval('clip.save')
    # lx.eval('!clip.reload')

    # lx.eval('shader.setVisible "%s" false' % texture_bc_tmp.name)  # disable bc_tmp texture
    lx.eval('shader.setVisible "%s" false' % passThree.name)  # disable pass 3 mask

    lx.eval('shader.setVisible "%s" false' % masterMask.name)  # disable master mask

    gltfShader = scene.addItem('glTFShader')
    gltfShader.setParent(masterMask, -1)
    gltfShader.channel('emissive').set((1.0, 1.0, 1.0))
    # gltfShader.channel('enable').set(False)
    final_ao = scene.duplicateItem(texture_ao_ro_me)
    final_ao.setParent(masterMask, -1)
    final_ao.channel('enable').set(True)
    final_ao.channel('effect').set('aoGLTF')
    final_ao.channel('swizzling').set(True)
    final_ao.channel('rgba').set('red')
    final_ro = scene.duplicateItem(final_ao)
    final_ro.channel('effect').set('roughnessGLTF')
    final_ro.channel('rgba').set('green')
    final_me = scene.duplicateItem(final_ro)
    final_me.channel('effect').set('metallicGLTF')
    final_me.channel('rgba').set('blue')

    final_norm = scene.duplicateItem(texture_norm)
    final_norm.setParent(masterMask, -1)
    final_norm.channel('enable').set(True)
    final_norm.channel('effect').set('normalGLTF')
    final_lum = scene.duplicateItem(texture_lum)
    final_lum.setParent(masterMask, -1)
    final_lum.channel('enable').set(True)
    final_lum.channel('effect').set('emisGLTF')
    final_bc = scene.duplicateItem(texture_bc_tmp)
    final_bc.setParent(masterMask, -1)
    final_bc.channel('enable').set(True)
    final_bc.channel('effect').set('baseColorGLTF')
    final_bc.channel('swizzling').set(True)
    final_bc.channel('rgba').set('ignore')
    final_tr = scene.duplicateItem(final_bc)
    final_tr.channel('effect').set('tranAmount')
    final_tr.channel('rgba').set('only')
    final_tr.channel('enable').set(False)
    final_tr.channel('invert').set(True)

    lx.eval('item.componentMode item true')

# change mask item to polygon tag
mask_search = 'meshByUV_'
print('mask item to polygon material tag')
for mask in scene.items('mask'):
    mask.select(replace=True)
    is_item_mask = lx.eval('mask.setMesh ?') != '(all)'
    if mask.name[:len(mask_search)] == mask_search and is_item_mask:
        print(mask.name, ':', mask.id)
        materialTagName = mask.name.split('(Item)')[0]
        print(materialTagName)
        mesh = mask.itemGraph('shadeLoc').forward()[0]
        print(mesh, ':', mesh.name)
        mesh.select(replace=True)
        for polygon in mesh.geometry.polygons:
            polygon.select()
        lx.eval('poly.setMaterial "%s"' % materialTagName)
        lx.eval('select.subItem "%s" set textureLayer;render;environment;light;camera;scene;replicator;bake;mediaClip;txtrLocator' % mask.id)
        scene.removeItems(scene.item('%s (Material)' % materialTagName), True)
        lx.eval('mask.setPTag "%s"' % materialTagName)
        lx.eval('mask.setMesh (all)')
        mesh.geometry.polygons.select()
        mask.channel('enable').set(1)

# select new gltf masks
scene.deselect()
for mask in scene.items('mask'):
    if mask.name[:len(mask_search)] == mask_search:
        mask.select()

print('done.')
