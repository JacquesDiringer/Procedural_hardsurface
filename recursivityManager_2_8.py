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


def subdivideFaces(objectToBrowse, facesTuples):
    totalFacesTuples = []
    for currentFaceTuple in facesTuples:
        if random.uniform(0, 1) < subdivisionProbability:
            generatedFacesTuples = subdivideGeneric(datetime.now(), objectToBrowse, currentFaceTuple)
            if(generatedFacesTuples is not None):
                totalFacesTuples.extend(generatedFacesTuples)
    
    resultFacesTuples = []
    for currentFaceTuple in totalFacesTuples:
        if random.uniform(0, 1) < insetProbability:
            generatedFacesTuples = insetGeneric(datetime.now(), objectToBrowse, currentFaceTuple)
            resultFacesTuples.extend(generatedFacesTuples)
        else:
            resultFacesTuples.append(currentFaceTuple)
        
    return resultFacesTuples



def recursiveGeneration(objectToModify, faceToModify):
    # Cut a plate in the selected object.
    #resultingFace = cutPlate(datetime.now(), originalySelectedObject, originalySelectedObject.data.polygons[0])
    #resultingFace = cutPlate(datetime.now(), originalySelectedObject, resultingFace)
    #resultingFace = cutPlate(datetime.now(), originalySelectedObject, resultingFace)
    #resultingFace = cutPlate(datetime.now(), originalySelectedObject, resultingFace)
    
    
#    datetime.now()
    
    resultingFacesTuples = subdivideFaces(objectToModify, [buildFaceTuple(objectToModify, faceToModify.index)])
    
    resultingFacesTuples = subdivideFaces(objectToModify, resultingFacesTuples)
    resultingFacesTuples = subdivideFaces(objectToModify, resultingFacesTuples)
    resultingFacesTuples = subdivideFaces(objectToModify, resultingFacesTuples)
    resultingFacesTuples = subdivideFaces(objectToModify, resultingFacesTuples)


   
 
def generateBatch(squareSize):
    
    for xCoords in range(0, squareSize):
        for yCoords in range(0, squareSize):
            
            bpy.ops.mesh.primitive_plane_add(size=0.95, view_align=False, enter_editmode=False, location=(xCoords, yCoords, 0))
            
        
            # Keep track of the selected object.
            originalySelectedObject = bpy.context.active_object
            
            # Find the first and only polygon in it.
            firstPolygon = originalySelectedObject.data.polygons[0]
            
            # Recursive generation.
            recursiveGeneration(originalySelectedObject, firstPolygon)
            
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
        recursiveGeneration(objectToModify, objectToModify.data.polygons[currentFaceIndex])
    
    # Go back in edit mode.
    bpy.ops.object.mode_set(mode = 'EDIT')
    
    
# Test function
if __name__ == "__main__":
    
#    generateBatch(4)
    applyToSelectedFaces()