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
bevelOffset = 0.01


def knifeProject(surfaceToCut, surfaceCuter, position, tbnMatrix):
    
    bpy.ops.object.mode_set(mode = 'OBJECT')
    
    # Check arguments.
    if surfaceToCut == None or surfaceCuter == None:
        print("knife project tentative with wrong arguments:")
        print("surfaceToCut = " + str(surfaceToCut))
        print("surfaceCuter = " + str(surfaceCuter))
        return
    
    # The TBN is converted to euler angles to circle around Blender's poor matrix update system.
    eulerFromTbn = tbnMatrix.to_euler()
    
    # Select only the surfaceCuter.
    bpy.ops.object.select_all(action='DESELECT')
    surfaceCuter.select_set(True)
    # Rotate it.
    bpy.ops.transform.rotate(value=eulerFromTbn.z, orient_axis='Z')
    bpy.ops.transform.rotate(value=eulerFromTbn.y, orient_axis='Y')
    bpy.ops.transform.rotate(value=eulerFromTbn.x, orient_axis='X')
    # And translate it.
    bpy.ops.transform.translate(value=(position[0], position[1], position[2]), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL')
    
    print("position = " + str(position))
    
    
    
    # Arrange selection for knife cutting operation.
    bpy.context.view_layer.objects.active = surfaceToCut
    surfaceCuter.select_set(True)
    
    direction = tbnMatrix[2]
    # Create override context for the cuts.
    override, originalRegion3D = createFaceOverrideContext(position, direction)

    # Force redraw the scene - this is considered unsavory but is necessary here.
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
    
    # The knife project has to be used in edit mode.
    bpy.ops.object.mode_set(mode = 'EDIT')

    # Knife cutting operation.
    bpy.ops.mesh.knife_project(override)
    
    # Go back to object mode. This forces an update of the mesh's internal data.
    bpy.ops.object.mode_set(mode = 'OBJECT')
    
    # Reset the view to it's configuration before the knife project.
    setRegion3D(override, originalRegion3D)
    
    # Keep the selected face resulting from the knife project.
    resultingPolygon = None
    for currentPolygon in surfaceToCut.data.polygons:
        if currentPolygon.select:
            resultingPolygon = currentPolygon
    
    return resultingPolygon


# Adds a crease in a surface, to simulate metal plates joining.
# For this function the edge to crease (resulting from the cut) must be selected.
def addCutCrease(surfaceToCrease):
    bpy.context.view_layer.objects.active = surfaceToCrease
    bpy.ops.object.mode_set(mode = 'EDIT')
    
    # Set the edges of the crease as sharp.
    bpy.ops.mesh.mark_sharp()
    
    # Create a bevel, the cutting shape of only one segment becomes 3 segments after this.
    bpy.ops.mesh.bevel(offset_type='OFFSET', offset=bevelOffset, offset_pct=0, segments=2, profile=0.5, vertex_only=False, clamp_overlap=True, loop_slide=True, mark_seam=False, mark_sharp=True)
    
    
    # Select less to only keep the middle segment selected.
    bpy.ops.mesh.select_less()
    
    # Set the bottom of the crease as sharp.
    bpy.ops.mesh.mark_sharp()
    
    # Lower the middle segment to create the crease.
    bpy.ops.transform.shrink_fatten(value=bevelOffset)

    
    # Go back to object mode.
    bpy.ops.object.mode_set(mode = 'OBJECT')
    
    
# Computes the borders of a given face in world space. This includes the size of the parent object.
# The face should be a rectangular quad.
# Warning: This algorithm assumes that the face is axis aligned.
def rectangleBorders(parentObject, face, tbnMatrix):
    minX = sys.float_info.max
    maxX = -sys.float_info.max
    minY = sys.float_info.max
    maxY = -sys.float_info.max
    
    for currentVertexIndex in face.vertices:
        currentVertex = face.id_data.vertices[currentVertexIndex]
        currentWorldCoords = parentObject.matrix_world @ currentVertex.co
        currentTangentCoords = tbnMatrix @ currentWorldCoords
        if currentTangentCoords.x < minX:
            minX = currentTangentCoords.x
        if currentTangentCoords.x > maxX:
            maxX = currentTangentCoords.x
        if currentTangentCoords.y < minY:
            minY = currentTangentCoords.y
        if currentTangentCoords.y > maxY:
            maxY = currentTangentCoords.y
    
    return (minX, maxX, minY, maxY)


# Basicaly computes the mean position of the rectangles 4 vertices to return it's center.
def rectangleCenter(parentObject, face):
    meanPosition = mathutils.Vector((0,0,0))
    for currentVertexIndex in face.vertices:
        # Find the vertex.
        currentVertex = face.id_data.vertices[currentVertexIndex]
        # Compute it's world coordinates.
        currentWorldCoords = parentObject.matrix_world @ currentVertex.co
        # Add it to the mean position.
        meanPosition = meanPosition + currentWorldCoords
        
    return meanPosition / len(face.vertices)
        
        
    

# Cuts a random shape in a surface, then gives it a crease to make it look like a plate.
def cutPlate(seed, objectToCut, cuttingShape, position, tbnMatrix):
    
    # Initialize the random seed, this is important in order to generate exactly the same content for a given seed.
    random.seed(seed)

    # Use the cutting shape to cut the currently selected surface.
    resultingFace = knifeProject(objectToCut, cuttingShape, position, tbnMatrix)

    # Delete the no longer needed cutting shape.
    dataToRemove = cuttingShape.data
    bpy.data.objects.remove(cuttingShape)
    bpy.data.meshes.remove(dataToRemove)
    
    # Crease the cut surface.
    addCutCrease(objectToCut)

    return resultingFace


# The responsibility of this function is to generate the cutting shape and place it correctly for the cutPlate function.
# It should then cut the inner rectangle to enable recursivity.
def genericCutPlate(seed, objectToCut, faceTuple):
    
    print()
    print("new cut")
    
    if objectToCut == None:
        print("Tried to cut a None object")
        return
        
    if faceTuple == None:
        print("Tried to cut a None tuple")
        return
    
    # Find the face in the object.
    faceToCut = objectToCut.data.polygons[faceTuple[0]]
    
    if faceToCut == None:
        print("Tried to cut a None face")
        return
    
    # Compute normal and tangent of the current face to cut.
    normalForCuts = faceToCut.normal.copy()
    tangentForCuts = faceTangent(objectToCut, faceToCut.index).copy()
    # Compute the biTangent thanks to the normal and tangent.
    biTangentForCuts = normalForCuts.cross(tangentForCuts)
    
    # Assemble a TBN matrix from the normal, tangent and bitangent of the face.
    tbnMatrix = mathutils.Matrix([
    [tangentForCuts.x,      tangentForCuts.y,   tangentForCuts.z    ],
    [biTangentForCuts.x,    biTangentForCuts.y, biTangentForCuts.z  ],
    [normalForCuts.x,       normalForCuts.y,    normalForCuts.z     ]
    ])
    
    # Initialize the random seed, this is important in order to generate exactly the same content for a given seed.
    random.seed(seed)
    
    # Compute the dimension of the face to cut.
    rectBorders = rectangleBorders(objectToCut, faceToCut, tbnMatrix)
    
    # Compute the center of the face to cut.
    faceCenter = rectangleCenter(objectToCut, faceToCut)
    print("faceCenter = " + str(faceCenter))
    
    rectDimension = (rectBorders[0], rectBorders[1], rectBorders[2], rectBorders[3])
    
    faceWidth   = rectDimension[1] - rectDimension[0]
    faceHeight  = rectDimension[3] - rectDimension[2]

    # Generate a cutting shape
    cuttingShapeDimension = (faceWidth * 0.5, faceHeight * 0.5)
    cuttingShape, edgesDepth = generateRectangleCuttingShape(seed=random.randint(0, 100000), position=(0,0,0), dimension=cuttingShapeDimension, recursionDepth=0)
    
    cuttingShapeOuterBounds =  [-cuttingShapeDimension[0]/2 - max(0, edgesDepth[0]), # left
                                -cuttingShapeDimension[1]/2 - max(0, edgesDepth[1]), # bottom
                                cuttingShapeDimension[0]/2 + max(0, edgesDepth[2]), # right
                                cuttingShapeDimension[1]/2 + max(0, edgesDepth[3])] # up

    cuttingShapeOuterBoundsDimension = (cuttingShapeOuterBounds[2] - cuttingShapeOuterBounds[0], # width
                                        cuttingShapeOuterBounds[3] - cuttingShapeOuterBounds[1]) # height
                                        
    cuttingShapeOuterBoundsOffset = ((  cuttingShapeOuterBounds[2] + cuttingShapeOuterBounds[0]) * 0.5, # width
                                    (   cuttingShapeOuterBounds[3] + cuttingShapeOuterBounds[1]) * 0.5) # height
    
    
    # Translation.
    cuttingShapeTranslation = (-cuttingShapeOuterBoundsOffset[0], -cuttingShapeOuterBoundsOffset[1], 0)
    bpy.ops.transform.translate(value=cuttingShapeTranslation, orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL')
    
    
    # The cutting shape should be re-scaled and translated to fit the face to cut.
    # Scale it uniformly however.
    cuttingShapeScaleFactor = cuttingShapeMargin * min(faceWidth / cuttingShapeOuterBoundsDimension[0], faceHeight / cuttingShapeOuterBoundsDimension[1])
    # Correct center for the resize.
    bpy.context.scene.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
    # Resize operation.
    bpy.ops.transform.resize(value=(cuttingShapeScaleFactor, cuttingShapeScaleFactor, 1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL')

    
    # After this rescale, the inner bounds can be calculated
    # Compute the inner bounds of the cutting shape.
    cuttingShapeInnerBounds =  [(-cuttingShapeDimension[0]/2 - min(0, edgesDepth[0])) * cuttingShapeScaleFactor + cuttingShapeTranslation[0], # left
                                (-cuttingShapeDimension[1]/2 - min(0, edgesDepth[1])) * cuttingShapeScaleFactor + cuttingShapeTranslation[1] , # bottom
                                ( cuttingShapeDimension[0]/2 + min(0, edgesDepth[2])) * cuttingShapeScaleFactor + cuttingShapeTranslation[0], # right
                                ( cuttingShapeDimension[1]/2 + min(0, edgesDepth[3])) * cuttingShapeScaleFactor + cuttingShapeTranslation[1]] # up

    cuttingShapeInnerBoundsDimension = (cuttingShapeInnerBounds[2] - cuttingShapeInnerBounds[0], # width
                                        cuttingShapeInnerBounds[3] - cuttingShapeInnerBounds[1]) # height
                                        
    cuttingShapeInnerBoundsOffset = (   (cuttingShapeInnerBounds[2] + cuttingShapeInnerBounds[0]) * 0.5, # width
                                        (cuttingShapeInnerBounds[3] + cuttingShapeInnerBounds[1]) * 0.5) # height
    
    # Cut the plate with the tech-ish shape.
    resultingFace = cutPlate(seed, objectToCut, cuttingShape, faceCenter, tbnMatrix)
    
    ## Cut the surface again to have a clean surface to work with for recursivity.
    # Generate a plane cutting shape.
    bpy.ops.mesh.primitive_plane_add(size=1, align='WORLD', enter_editmode=True, location=((0,0,0)))
    # Re-scale to fit the plane in the inner bounds.
    cleanFaceScale = (cuttingShapeInnerBoundsDimension[0] * cleanFaceMargin, cuttingShapeInnerBoundsDimension[1] * cleanFaceMargin, 1)
    bpy.ops.transform.resize(value=cleanFaceScale, orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL')
    # Translate to fit the plane in the inner bounds.
    cleanFaceTranslation = (cuttingShapeInnerBoundsOffset[0], cuttingShapeInnerBoundsOffset[1], 0)
    bpy.ops.transform.translate(value=cleanFaceTranslation, orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL')

    # Go back to object mode.
    bpy.ops.object.mode_set(mode = 'OBJECT')
 
    # The cutting plane is the active object.
    cuttingShape = bpy.context.active_object
    
    # Use the cutting shape to cut the currently selected surface.
    resultingFace = knifeProject(objectToCut, cuttingShape, faceCenter, tbnMatrix)
    
    # Delete the no longer needed cutting shape.
    dataToRemove = cuttingShape.data
    bpy.data.objects.remove(cuttingShape)
    bpy.data.meshes.remove(dataToRemove)
    
    
    if not resultingFace == None:
        resultingFaceTuple = buildFaceTuple(objectToCut, resultingFace.index)
        return resultingFaceTuple


# Test function
if __name__ == "__main__":
    
    # Delete everything in the scene.
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)

    # Create a new plane.
    bpy.ops.mesh.primitive_plane_add(align='WORLD', enter_editmode=True, location=(0, 0, 0))
#    bpy.ops.transform.resize(value=(1, 2.0, 1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, False), mirror=True, proportional='DISABLED', proportional_edit_falloff='SMOOTH', proportional_size=1)
    
    bpy.ops.object.mode_set(mode = 'OBJECT')

    
    # Keep track of the selected object.
    originalySelectedObject = bpy.context.active_object

    # Cut a plate in the selected object.
    resultingFaceTuple = genericCutPlate(datetime.now(), originalySelectedObject, buildFaceTuple(originalySelectedObject, originalySelectedObject.data.polygons[0].index))
    resultingFaceTuple = genericCutPlate(datetime.now(), originalySelectedObject, resultingFaceTuple)
    resultingFaceTuple = genericCutPlate(datetime.now(), originalySelectedObject, resultingFaceTuple)
    resultingFaceTuple = genericCutPlate(datetime.now(), originalySelectedObject, resultingFaceTuple)
#    resultingFaceTuple = genericCutPlate(0, originalySelectedObject, resultingFaceTuple)
#    resultingFaceTuple = genericCutPlate(0, originalySelectedObject, resultingFaceTuple)
    bpy.ops.object.mode_set(mode = 'EDIT')
#datetime.now()
