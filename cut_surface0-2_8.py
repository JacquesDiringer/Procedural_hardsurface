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
    
    # Set the view to origin with a small distance so that we have a better precision for the knife projection.
    rv3d.view_location = (0,0,0)
    rv3d.view_distance = 1
    
    # Set view to TOP by directly rotating the 3D view region's view_rotation.
    rv3d.view_rotation = Euler( (0,0,0) ).to_quaternion()
    
    # Set the canera to orthographic.
    rv3d.view_perspective = 'ORTHO'
    
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
    
    return bpy.context.active_object


# Adds a crease in a surface, to simulate metal plates joining.
# For this function the edge to crease (resulting from the cut) must be selected.
def addCutCrease(surfaceToCrease):
    bpy.context.view_layer.objects.active = surfaceToCrease
    bpy.ops.object.mode_set(mode = 'EDIT')
    
    # Create a bevel, the cutting shape of only one segment becomes 3 segments after this.
    bpy.ops.mesh.bevel(offset_type='OFFSET', offset=0.5, offset_pct=0, segments=2, profile=0.5, vertex_only=False, clamp_overlap=True, loop_slide=True, mark_seam=False, mark_sharp=True)
    
    # Select less to only keep the middle segment selected.
    bpy.ops.mesh.select_less()
    
    # Lower the middle segment to create the crease.
    bpy.ops.transform.translate(value=(0, 0, -0.01), orient_type='LOCAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=True, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
    
    # Go back to object mode.
    bpy.ops.object.mode_set(mode = 'OBJECT')




# Keep track of the selected object.
originalySelectedObject = bpy.context.active_object


# Generate a cutting shape
cuttingShape = generateRectangleCuttingShape(seed=1, position=(0, 0, 0), dimension=(3, 0.5), recursionDepth=0)

# Use the cutting shape to cut the currently selected surface.
cutObject = knifeProject(originalySelectedObject, cuttingShape)

# Delete the no longer needed cutting shape.
dataToRemove = cuttingShape.data
bpy.data.objects.remove(cuttingShape)
bpy.data.meshes.remove(dataToRemove)

# Crease the cut surface.
addCutCrease(cutObject)
