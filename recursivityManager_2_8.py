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
insetProbability = 0.5


# Parameters for other modules.
subdivide_surface_2_8.minimumLength = 0.05
# Modify cutting settings.
cut_surface0_2_8.bevelOffset = 0.001
cut_surface0_2_8.cuttingShapeMargin = 0.9
cut_surface0_2_8.cleanFaceMargin = 0.7
# Modify cutting shapes generation.
generate_cuttingShape0_2_8.roundProbability = 0.0

# Recursive settings.
recursiveDepth = 1
subdivisionOverCutProbability = 0.7

# Batches generation.
batchSize = 5
seedOffsetForBatches = 6



def subdivideFaces(seed, objectToBrowse, facesTuples):
    
    # Initialize the random seed, this is important in order to generate exactly the same content for a given seed.
    random.seed(seed)
    
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


def subdivideOrCut(seed, objectToBrowse, facesTuples):
    
    # Initialize the random seed, this is important in order to generate exactly the same content for a given seed.
    random.seed(seed)
    
    print("subdivideOrCut facesTuples = " + str([currentTuple[0] for currentTuple in facesTuples]))
    
    # Final result to return.
    finalFacesTuples = []
    
    for currentFaceTuple in facesTuples:
        resultingFacesTuples = []
        
        # Randomly pick a subdivision or cut operation.
        subdivisionOverCut = random.uniform(0, 1) < subdivisionOverCutProbability
        
        if subdivisionOverCut:
            resultingFacesTuples = subdivideFaces(random.randint(0, 100000), objectToBrowse, [currentFaceTuple])
        else:
            resultingFacesTuples = [genericCutPlate(random.randint(0, 100000), objectToBrowse, currentFaceTuple)]
        # This might be necessary to refresh the object, check this.
        bpy.ops.object.mode_set(mode = 'OBJECT')
            
        # Add the resulting faces to the final total array.
        if resultingFacesTuples == None:
            finalFacesTuples.append(currentFaceTuple)
        else:
            finalFacesTuples.extend(resultingFacesTuples)
    
    # Filter out empty elements.
    finalFacesTuples = [currentTuple for currentTuple in finalFacesTuples if not (currentTuple == [] or currentTuple == None) ]
    
    print("finalFacesTuples before sort = " + str([currentTuple[0] for currentTuple in finalFacesTuples]))
    
    # Sort the arrays from in descending order according to the index, to avoid index offsetting side effects when modifying a face.
    finalFacesTuples = sorted(finalFacesTuples, key= lambda faceTuple: faceTuple[0], reverse = True)
    print("finalFacesTuples after sort = " + str([currentTuple[0] for currentTuple in finalFacesTuples]))
    
    return finalFacesTuples



def recursiveGeneration(seed, objectToModify, facesToModify, recursiveDepth):
    
    # Initialize the random seed, this is important in order to generate exactly the same content for a given seed.
    random.seed(seed)

    # Subdivide or cut recursively.
    # Traverse the created faces in a descending order according to their index, to avoid issues with index offsetting when creating new faces.
    for currentFaceToModify in facesToModify:
        resultingFaceTuples = subdivideOrCut(random.randint(0, 100000), objectToModify, [currentFaceToModify])
    
        # Faces should have been returned in a descending order for the index.
        if recursiveDepth > 0:
            recursiveGeneration(random.randint(0, 100000), objectToModify, resultingFaceTuples, recursiveDepth - 1)

   
 
def generateBatch(squareSize):

    #datetime.now()
    # Initialize the random seed, this is important in order to generate exactly the same content for a given seed.
    #random.seed(1)
    random.seed(datetime.now())
    
    facesCount = 0
    for xCoords in range(0, squareSize):
        for yCoords in range(0, squareSize):
            
            bpy.ops.mesh.primitive_plane_add(size=0.95, align='WORLD', enter_editmode=False, location=(xCoords, yCoords, 0))
            
            #bpy.ops.transform.rotate(value=1.1055, orient_axis='X', orient_type='GLOBAL', orient_matrix=((-0.527618, 0.849482, 6.25849e-07), (-0.432952, -0.268908, -0.860373), (0.730871, 0.453949, -0.509665)), orient_matrix_type='VIEW', mirror=True)
            bpy.ops.transform.rotate(value=random.uniform(0, 4), orient_axis='Z', orient_type='VIEW', orient_matrix=((0.993576, 0.113164, 4.95464e-07), (-0.0669248, 0.587603, -0.806377), (0.0912528, -0.801197, -0.591402)), orient_matrix_type='VIEW')
            #bpy.ops.transform.rotate(value=-1.5708, orient_axis='X', orient_type='GLOBAL', orient_matrix=((-0.527618, 0.849482, 6.25849e-07), (-0.432952, -0.268908, -0.860373), (0.730871, 0.453949, -0.509665)), orient_matrix_type='VIEW', mirror=True)
            
            position = (1,0,0)
            bpy.ops.transform.translate(value=(-position[0], -position[1], -position[2]), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL')
            
            bpy.ops.object.transform_apply() # TODO: remove this later, only for temporary edit mode normal direction test.
            
        
            # Keep track of the selected object.
            originalySelectedObject = bpy.context.active_object
            
            # Find the first and only polygon in it.
            firstPolygonTuple = buildFaceTuple(originalySelectedObject, originalySelectedObject.data.polygons[0].index)
            firstPolygon = originalySelectedObject.data.polygons[0]
            
            # Recursive generation.
            recursiveGeneration(seedOffsetForBatches + facesCount, originalySelectedObject, [firstPolygonTuple], recursiveDepth)
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
    # Sort the array from in descending order according to the index, to avoid index offsetting side effects when modifying a face.
    selectedFacesIndexes = [currentFace.index for currentFace in objectToModify.data.polygons if currentFace.select and len(currentFace.vertices) == 4]
    selectedFacesIndexes = sorted(selectedFacesIndexes, reverse = True)
    
    totalFaces = len(selectedFacesIndexes)
    counter = 0
    
    for currentFaceIndex in selectedFacesIndexes:
        # Progression.
        counter = counter + 1
        print(str(counter) + " of " + str(totalFaces) + " faces.")
        
        # Build tuple.
        firstPolygonTuple = buildFaceTuple(objectToModify, objectToModify.data.polygons[currentFaceIndex].index)
        
        # Recursive generation.
        recursiveGeneration(counter, objectToModify, [firstPolygonTuple], recursiveDepth)
    
    # Go back in edit mode.
    bpy.ops.object.mode_set(mode = 'EDIT')
    
    
# Test function
if __name__ == "__main__":
    
    print("////// Recusivity manager launch //////")
    
#    generateBatch(batchSize)
    applyToSelectedFaces()