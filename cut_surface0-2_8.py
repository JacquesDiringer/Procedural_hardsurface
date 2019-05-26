import bpy
import bmesh

import mathutils
import random
from datetime import datetime
from mathutils import Euler

# Import submodules.
import sys
import os
import importlib

blend_dir = os.path.dirname(bpy.data.filepath)
if blend_dir not in sys.path:
   sys.path.append(blend_dir)

import generate_cuttingShape0_2_8

importlib.reload(generate_cuttingShape0_2_8)

from generate_cuttingShape0_2_8 import *



def view3d_find( return_area = False ):
    # returns first 3d view, normally we get from context
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            v3d = area.spaces[0]
            rv3d = v3d.region_3d
            for region in area.regions:
                if region.type == 'WINDOW':
                    if return_area: return region, rv3d, v3d, area
                    return region, rv3d, v3d
    return None, None

def createOverrideContext():
    region, rv3d, v3d, area = view3d_find(True)

    # Define context override dictionary for overriding the knife_project operator's context
    override = {
        'scene'            : bpy.context.scene,
        'region'           : region,
        'area'             : area,
        'space'            : v3d,
        'active_object'    : bpy.context.object,
        'window'           : bpy.context.window,
        'screen'           : bpy.context.screen,
        'selected_objects' : bpy.context.selected_objects,
        'edit_object'      : bpy.context.object
    }
    
    # Set view to TOP by directly rotating the 3D view region's view_rotation
    rv3d.view_rotation = Euler( (0,0,0) ).to_quaternion()
    
    return override


def knifeProject(surfaceToCut, surfaceCuter):
    
    # Arrange selection for knife cutting operation.
    bpy.context.view_layer.objects.active = surfaceToCut
    surfaceCuter.select_set(True)
    
    override = createOverrideContext()

    # Force redraw the scene - this is considered unsavory but is necessary here.
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

    # The knife project has to be used in edit mode.
    bpy.ops.object.mode_set(mode = 'EDIT')

    # Knife cutting operation.
    bpy.ops.mesh.knife_project(override)

    # Go back to object mode.
    bpy.ops.object.mode_set(mode = 'OBJECT')



# Keep track of the selected object.
originalySelectedObject = bpy.context.active_object


# Generate a cutting shape
cuttingShape = generateRectangleCuttingShape(seed=1, position=(0, 0, 0), dimension=(3, 0.5), recursionDepth=0)

# Use the cutting shape to cut the currently selected surface.
knifeProject(originalySelectedObject, cuttingShape)
