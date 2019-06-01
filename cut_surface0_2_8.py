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
import copy

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
        'edit_object'      : bpy.context.object,
        'region_3d'        : rv3d
    }
    
    originalRegion3D = {
        'view_location'     : copy.copy(rv3d.view_location),
        'view_distance'     : rv3d.view_distance,
        'view_rotation'     : copy.copy(rv3d.view_rotation),
        'view_perspective'  : rv3d.view_perspective}
    
    # Set the view to origin with a small distance so that we have a better precision for the knife projection.
    rv3d.view_location = (0,0,0)
    rv3d.view_distance = 1
    
    # Set view to TOP by directly rotating the 3D view region's view_rotation.
    rv3d.view_rotation = Euler( (0,0,0) ).to_quaternion()
    
    # Set the canera to orthographic.
    rv3d.view_perspective = 'ORTHO'
    
    return override, originalRegion3D

def setRegion3D(override, originalConfiguration):
    rv3d = override['region_3d']
    
    rv3d.view_location      = originalConfiguration['view_location']
    rv3d.view_distance      = originalConfiguration['view_distance']
    rv3d.view_rotation      = originalConfiguration['view_rotation']
    rv3d.view_perspective   = originalConfiguration['view_perspective']


def knifeProject(surfaceToCut, surfaceCuter):
    
    # Arrange selection for knife cutting operation.
    bpy.context.view_layer.objects.active = surfaceToCut
    surfaceCuter.select_set(True)
    
    override, originalRegion3D = createOverrideContext()

    # Force redraw the scene - this is considered unsavory but is necessary here.
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
    
    # The knife project has to be used in edit mode.
    bpy.ops.object.mode_set(mode = 'EDIT')

    # Knife cutting operation.
    bpy.ops.mesh.knife_project(override)
    
    # Go back to object mode. This forces an update of the mesh's internal data.
    bpy.ops.object.mode_set(mode = 'OBJECT')
    
    # Keep the selected face resulting from the knife project.
    resultingPolygon = None
    for currentPolygon in surfaceToCut.data.polygons:
        if currentPolygon.select:
            resultingPolygon = currentPolygon
    
    # Reset the view to it's configuration before the knife project.
    setRegion3D(override, originalRegion3D)
    
    return resultingPolygon


# Adds a crease in a surface, to simulate metal plates joining.
# For this function the edge to crease (resulting from the cut) must be selected.
def addCutCrease(surfaceToCrease):
    bpy.context.view_layer.objects.active = surfaceToCrease
    bpy.ops.object.mode_set(mode = 'EDIT')
    
    # Set the edges of the crease as sharp.
    bpy.ops.mesh.mark_sharp()
    
    bevelOffset = 0.01
    # Create a bevel, the cutting shape of only one segment becomes 3 segments after this.
    bpy.ops.mesh.bevel(offset_type='OFFSET', offset=bevelOffset, offset_pct=0, segments=2, profile=0.5, vertex_only=False, clamp_overlap=True, loop_slide=True, mark_seam=False, mark_sharp=True)
    
    
    # Select less to only keep the middle segment selected.
    bpy.ops.mesh.select_less()
    
    # Set the bottom of the crease as sharp.
    bpy.ops.mesh.mark_sharp()
    
    # Lower the middle segment to create the crease.
    bpy.ops.transform.translate(value=(0, 0, -bevelOffset * 2), orient_type='LOCAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=True, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
    
    # Go back to object mode.
    bpy.ops.object.mode_set(mode = 'OBJECT')
    
    
# Computes the borders of a given face.
# The face should be a rectangular quad.
def rectangleBorders(face):
    minX = sys.float_info.max
    maxX = -sys.float_info.max
    minY = sys.float_info.max
    maxY = -sys.float_info.max
    
    for currentVertexIndex in face.vertices:
        currentVertex = face.id_data.vertices[currentVertexIndex]
        if currentVertex.co.x < minX:
            minX = currentVertex.co.x
        if currentVertex.co.x > maxX:
            maxX = currentVertex.co.x
        if currentVertex.co.y < minY:
            minY = currentVertex.co.y
        if currentVertex.co.y > maxY:
            maxY = currentVertex.co.y
    
    return (minX, maxX, minY, maxY)

# Cuts a random shape in a surface, then gives it a crease to make it look like a plate.
def cutPlate(seed, objectToCut, faceToCut):
    
    # Initialize the random seed, this is important in order to generate exactly the same content for a given seed.
    random.seed(seed)
    
    rectDimension = rectangleBorders(faceToCut)
    
    rectDimension = (rectDimension[0] * objectToCut.scale.x, rectDimension[1] * objectToCut.scale.x, rectDimension[2] * objectToCut.scale.y, rectDimension[3] *objectToCut.scale.y)
    
    faceWidth   = rectDimension[1] - rectDimension[0]
    faceHeight  = rectDimension[3] - rectDimension[2]
    facePosition = ((rectDimension[1] + rectDimension[0]) * 0.5, (rectDimension[3] + rectDimension[2]) * 0.5, 0)

    # Generate a cutting shape
    cuttingShape = generateRectangleCuttingShape(seed=random.randint(0, 100000), position=facePosition, dimension=(faceWidth * 0.9, faceHeight * 0.9), recursionDepth=0)

    # Use the cutting shape to cut the currently selected surface.
    knifeProject(objectToCut, cuttingShape)

    # Delete the no longer needed cutting shape.
    dataToRemove = cuttingShape.data
    bpy.data.objects.remove(cuttingShape)
    bpy.data.meshes.remove(dataToRemove)
    
    # Crease the cut surface.
    addCutCrease(objectToCut)
    
    
    ## Cut the surface again to have a clean surface to work with again.
    # Generate a plane cutting shape.
    bpy.ops.mesh.primitive_plane_add(size=0.5, view_align=False, enter_editmode=True, location=(facePosition))
    bpy.ops.transform.resize(value=(faceWidth, faceHeight, 1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL')
    # Go back to object mode.
    bpy.ops.object.mode_set(mode = 'OBJECT')
 
    # The cutting plane is the active object.
    cuttingShape = bpy.context.active_object
    
    # Use the cutting shape to cut the currently selected surface.
    resultingFace = knifeProject(objectToCut, cuttingShape)
    
    # Delete the no longer needed cutting shape.
    dataToRemove = cuttingShape.data
    bpy.data.objects.remove(cuttingShape)
    bpy.data.meshes.remove(dataToRemove)

    return resultingFace



# Test function
if __name__ == "__main__":
    # Keep track of the selected object.
    originalySelectedObject = bpy.context.active_object

    # Cut a plate in the selected object.
    resultingFace = cutPlate(datetime.now(), originalySelectedObject, originalySelectedObject.data.polygons[0])
