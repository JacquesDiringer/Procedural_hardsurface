import bpy
import bmesh

import mathutils
import random
import time
from datetime import datetime

# Import submodules.
import sys
import os
import importlib
import copy

blend_dir = os.path.dirname(bpy.data.filepath)
if blend_dir not in sys.path:
   sys.path.append(blend_dir)

# Surface cutting.  
import cut_surface0_2_8
importlib.reload(cut_surface0_2_8)
from cut_surface0_2_8 import *

# Subdivisions.
import subdivide_surface_2_8
importlib.reload(subdivide_surface_2_8)
from subdivide_surface_2_8 import *

# Insets.
import inset_surface_2_8
importlib.reload(inset_surface_2_8)
from inset_surface_2_8 import *

    
subdivisionProbability = 0.8
insetProbability = 0.1


# Parameters for other modules.
subdivide_surface_2_8.minimumLength = 0.05


# Batches generation.
seedOffsetForBatches = 0



def subdivideFaces(seed, objectToBrowse, facesTuples):
    totalFacesTuples = []
    for currentFaceTuple in facesTuples:
        if random.uniform(0, 1) < subdivisionProbability:
            generatedFacesTuples = subdivideGeneric(seed, objectToBrowse, currentFaceTuple)
            if(generatedFacesTuples is not None):
                totalFacesTuples.extend(generatedFacesTuples)
                
    # Sort the arrays from in descending order according to the index, to avoid index offsetting side effects when modifying a face.
    totalFacesTuples = sorted(totalFacesTuples, key= lambda faceTuple: faceTuple[0], reverse = True)
    print("totalFacesTuples (after subdivision) = " + str([currentTuple[0] for currentTuple in totalFacesTuples]))
    
    
    resultFacesTuples = []
    for currentFaceTuple in totalFacesTuples:
        if random.uniform(0, 1) < insetProbability:
            generatedFacesTuples = insetGeneric(seed, objectToBrowse, currentFaceTuple)
            resultFacesTuples.extend(generatedFacesTuples)
        else:
            resultFacesTuples.append(currentFaceTuple)
    
    # Sort the arrays from in descending order according to the index, to avoid index offsetting side effects when modifying a face.
    resultFacesTuples = sorted(resultFacesTuples, key= lambda faceTuple: faceTuple[0], reverse = True)
    print("resultFacesTuples (after inset) = " + str([currentTuple[0] for currentTuple in resultFacesTuples]))
        
    return resultFacesTuples


def subdivideAndCut(seed, objectToBrowse, facesTuples):
    
    print("facesTuples = " + str([currentTuple[0] for currentTuple in facesTuples]))
    
    subdividedFacesTuples = subdivideFaces(seed, objectToBrowse, facesTuples)
#    subdividedFacesTuples = facesTuples

    bpy.ops.object.mode_set(mode = 'OBJECT')

    print("subdividedFacesTuples = " + str([currentTuple[0] for currentTuple in subdividedFacesTuples]))
    
    finalFacesTuples = []
    for currentFaceTuple in subdividedFacesTuples:
        resultingFaceTuple = genericCutPlate(seed, objectToBrowse, currentFaceTuple)
        
        if resultingFaceTuple == None:
            finalFacesTuples.append(currentFaceTuple)
        else:
            finalFacesTuples.append(resultingFaceTuple)
    
    # Sort the arrays from in descending order according to the index, to avoid index offsetting side effects when modifying a face.
    finalFacesTuples = sorted(finalFacesTuples, key= lambda faceTuple: faceTuple[0], reverse = True)
    print("finalFacesTuples = " + str([currentTuple[0] for currentTuple in finalFacesTuples]))
    
    return finalFacesTuples



def recursiveGeneration(seed, objectToModify, facesToModify, recursiveDepth):
    
    # Modify cutting settings.
    cut_surface0_2_8.cuttingShapeMargin = 0.9
    cut_surface0_2_8.cleanFaceMargin = 0.7
    
    # Cut a plate in the selected object.
#    resultingFaceTuple = genericCutPlate(datetime.now(), objectToModify, buildFaceTuple(objectToModify, objectToModify.data.polygons[0].index))
#    resultingFaceTuple = genericCutPlate(datetime.now(), objectToModify, resultingFaceTuple)
#    resultingFaceTuple = genericCutPlate(datetime.now(), objectToModify, resultingFaceTuple)
#    resultingFaceTuple = genericCutPlate(datetime.now(), objectToModify, resultingFaceTuple)
    
    
#    datetime.now()
    
#    resultingFacesTuples = subdivideFaces(objectToModify, [buildFaceTuple(objectToModify, faceToModify.index)])
    
#    resultingFacesTuples = subdivideFaces(objectToModify, resultingFacesTuples)
#    resultingFacesTuples = subdivideFaces(objectToModify, resultingFacesTuples)
#    resultingFacesTuples = subdivideFaces(objectToModify, resultingFacesTuples)
#    resultingFacesTuples = subdivideFaces(objectToModify, resultingFacesTuples)


    # Subdivide and cut.
#    seedToUse = datetime.now()
#    print("seedToUse = " + str(seedToUse))
    
    for currentFaceToModify in facesToModify:
        resultingFaceTuples = subdivideAndCut(seed, objectToModify, [currentFaceToModify])
    
        # Faces should have been returned in a descending order for the index.
        if recursiveDepth > 0:
            recursiveGeneration(seed, objectToModify, resultingFaceTuples, recursiveDepth - 1)


   
 
def generateBatch(squareSize):
    
    facesCount = 0
    for xCoords in range(0, squareSize):
        for yCoords in range(0, squareSize):
            
            bpy.ops.mesh.primitive_plane_add(size=0.95, view_align=False, enter_editmode=False, location=(xCoords, yCoords, 0))
            
        
            # Keep track of the selected object.
            originalySelectedObject = bpy.context.active_object
            
            # Find the first and only polygon in it.
            firstPolygonTuple = buildFaceTuple(originalySelectedObject, originalySelectedObject.data.polygons[0].index)
            firstPolygon = originalySelectedObject.data.polygons[0]
            
            # Recursive generation.
            recursiveGeneration(seedOffsetForBatches + facesCount, originalySelectedObject, [firstPolygonTuple], 2)
            facesCount = facesCount + 1
            
            bpy.ops.object.mode_set(mode = 'OBJECT')
    


#    bpy.ops.object.mode_set(mode = 'EDIT')
    
    override, originalRegion3D = createOverrideContext()
    
    # Reset the view to it's original configuration.
    setRegion3D(override, originalRegion3D)
    

def applyToSelectedFaces():
    
    if not bpy.context.mode == 'EDIT_MESH':
        print("applyToMesh function should be performed in edit mode.")
        return
    
    # Keep a reference to the object to modify.
    objectToModify = bpy.context.edit_object
    
    # Populate an array of currently selected faces.
    # First the mandatory object mode to have up to date select values for faces.
    bpy.ops.object.mode_set(mode = 'OBJECT')
    
    # The faces should have 4 vertices exactly.
    selectedFacesIndexes = [currentFace.index for currentFace in objectToModify.data.polygons if currentFace.select and len(currentFace.vertices) == 4]
    
    totalFaces = len(selectedFacesIndexes)
    counter = 0
    
    for currentFaceIndex in selectedFacesIndexes:
        # Progression.
        counter = counter + 1
        print(str(counter) + " of " + str(totalFaces) + " faces.")
        
        # Recursive generation.
        recursiveGeneration(objectToModify, [objectToModify.data.polygons[currentFaceIndex]])
    
    # Go back in edit mode.
    bpy.ops.object.mode_set(mode = 'EDIT')
    
    
# Test function
if __name__ == "__main__":
    
    generateBatch(2)
#    applyToSelectedFaces()