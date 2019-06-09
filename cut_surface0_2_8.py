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

# Cutting shapes generation.
import generate_cuttingShape0_2_8
importlib.reload(generate_cuttingShape0_2_8)
from generate_cuttingShape0_2_8 import *

# Utils.
import utils_2_8
importlib.reload(utils_2_8)
from utils_2_8 import *


cuttingShapeMargin = 0.9
cleanFaceMargin = 0.9


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
    
    
# Computes the borders of a given face in world space. This includes the size of the parent object.
# The face should be a rectangular quad.
# Warning: This algorithm assumes that the face is axis aligned.
def rectangleBorders(parentObject, face):
    minX = sys.float_info.max
    maxX = -sys.float_info.max
    minY = sys.float_info.max
    maxY = -sys.float_info.max
    
    for currentVertexIndex in face.vertices:
        currentVertex = face.id_data.vertices[currentVertexIndex]
        currentWorldCoords = parentObject.matrix_world @ currentVertex.co
        if currentWorldCoords.x < minX:
            minX = currentWorldCoords.x
        if currentWorldCoords.x > maxX:
            maxX = currentWorldCoords.x
        if currentWorldCoords.y < minY:
            minY = currentWorldCoords.y
        if currentWorldCoords.y > maxY:
            maxY = currentWorldCoords.y
    
    return (minX, maxX, minY, maxY)

# Cuts a random shape in a surface, then gives it a crease to make it look like a plate.
def cutPlate(seed, objectToCut, faceToCut, cuttingShape):
    
    # Initialize the random seed, this is important in order to generate exactly the same content for a given seed.
    random.seed(seed)

    # Use the cutting shape to cut the currently selected surface.
    resultingFace = knifeProject(objectToCut, cuttingShape)

    # Delete the no longer needed cutting shape.
    dataToRemove = cuttingShape.data
    bpy.data.objects.remove(cuttingShape)
    bpy.data.meshes.remove(dataToRemove)
    
    # Crease the cut surface.
    addCutCrease(objectToCut)

    return resultingFace


# The responsibility of this function is to generate the cutting shape and place it correctly for the cutPlate function.
# It should then cut the inner rectangle to enable recursivity.
def genericCutPlate(seed, objectToCut, faceToCut):
    
    # Initialize the random seed, this is important in order to generate exactly the same content for a given seed.
    random.seed(seed)
    
    rectBorders = rectangleBorders(objectToCut, faceToCut)
    
    rectDimension = (rectBorders[0], rectBorders[1], rectBorders[2], rectBorders[3])
    
    faceWidth   = rectDimension[1] - rectDimension[0]
    faceHeight  = rectDimension[3] - rectDimension[2]
    facePosition = ((rectDimension[1] + rectDimension[0]) * 0.5, (rectDimension[3] + rectDimension[2]) * 0.5, 0)

    # Generate a cutting shape
    cuttingShape, edgesDepth = generateRectangleCuttingShape(seed=random.randint(0, 100000), position=facePosition, dimension=(1,1), recursionDepth=0)
    
    # Compute the inner bounds of the cutting shape.
    print("edgesDepth = " + str(edgesDepth))

    cuttingShapeDimension = (1,1)                               

    cuttingShapeOuterBounds =  [cuttingShapeDimension[0]/2 + max(0, edgesDepth[0]), # left
                                cuttingShapeDimension[1]/2 + max(0, edgesDepth[1]), # bottom
                                cuttingShapeDimension[0]/2 + max(0, edgesDepth[2]), # right
                                cuttingShapeDimension[1]/2 + max(0, edgesDepth[3])] # up

    cuttingShapeOuterBoundsDimension = (cuttingShapeOuterBounds[0] + cuttingShapeOuterBounds[2], # width
                                        cuttingShapeOuterBounds[1] + cuttingShapeOuterBounds[3]) # height
                                        
    cuttingShapeOuterBoundsOffset = (cuttingShapeOuterBounds[2] - cuttingShapeOuterBounds[0], # width
                                        cuttingShapeOuterBounds[3] - cuttingShapeOuterBounds[1]) # height
    
    
    # The cutting shape should be re-scaled and translated to fit the face to cut.
    # Scale it uniformly however.
    cuttingShapeScaleFactor = cuttingShapeMargin * min(faceWidth / cuttingShapeOuterBoundsDimension[0], faceHeight / cuttingShapeOuterBoundsDimension[1])
    bpy.ops.transform.resize(value=(cuttingShapeScaleFactor, cuttingShapeScaleFactor, 1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL')                                   
    # Translation.
    cuttingShapeTranslation = (-cuttingShapeOuterBoundsOffset[0] * 0.5 * cuttingShapeScaleFactor, -cuttingShapeOuterBoundsOffset[1] * 0.5 * cuttingShapeScaleFactor, 0)
    bpy.ops.transform.translate(value=cuttingShapeTranslation, orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL')

    
    # After this rescale, the inner bounds can be calculated
    cuttingShapeInnerBounds =  [(cuttingShapeDimension[0]/2 + min(0, edgesDepth[0])) * cuttingShapeScaleFactor, # left
                                (cuttingShapeDimension[1]/2 + min(0, edgesDepth[1])) * cuttingShapeScaleFactor, # bottom
                                (cuttingShapeDimension[0]/2 + min(0, edgesDepth[2])) * cuttingShapeScaleFactor, # right
                                (cuttingShapeDimension[1]/2 + min(0, edgesDepth[3])) * cuttingShapeScaleFactor] # up

    cuttingShapeInnerBoundsDimension = (cuttingShapeInnerBounds[0] + cuttingShapeInnerBounds[2], # width
                                        cuttingShapeInnerBounds[1] + cuttingShapeInnerBounds[3]) # height
                                        
    cuttingShapeInnerBoundsOffset = (   cuttingShapeInnerBounds[2] - cuttingShapeInnerBounds[0] - cuttingShapeTranslation[0], # width
                                        cuttingShapeInnerBounds[3] - cuttingShapeInnerBounds[1] - cuttingShapeTranslation[1]) # height

    
    print("cuttingShapeInnerBounds = " + str(cuttingShapeInnerBounds))
    
    print("dimensions = " + str(cuttingShapeInnerBoundsDimension))
    
    
    # Cut the plate with the tech-ish shape.
    resultingFace = cutPlate(seed, objectToCut, faceToCut, cuttingShape)
    
    
    
    ## Cut the surface again to have a clean surface to work with for recursivity.
    # Generate a plane cutting shape.
    bpy.ops.mesh.primitive_plane_add(size=1, view_align=False, enter_editmode=True, location=(facePosition))
    bpy.ops.transform.resize(value=(cuttingShapeInnerBoundsDimension[0] * cleanFaceMargin, cuttingShapeInnerBoundsDimension[1] * cleanFaceMargin, 1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL')
    bpy.ops.transform.translate(value=(-cuttingShapeInnerBoundsOffset[0] * 0.5, -cuttingShapeInnerBoundsOffset[1] * 0.5, 0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL')

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
    resultingFace = genericCutPlate(2, originalySelectedObject, originalySelectedObject.data.polygons[0])
    resultingFace = genericCutPlate(2, originalySelectedObject, resultingFace)
#datetime.now()
