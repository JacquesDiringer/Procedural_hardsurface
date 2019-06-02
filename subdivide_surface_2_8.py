import bpy
import bmesh

import mathutils
import random
import time
from datetime import datetime
from mathutils import Euler

# Import submodules.
import sys
import os
import importlib
import copy

# Utils.
import utils
importlib.reload(utils)
from utils import *


minCuts = 1 # Minimum number of cuts per subdivision.
maxCuts = 4 # Maximum number of cuts per subdivision.
verticalProbability = 0.5 # Probability of doing a vertical subdivision.


def subdivideGeneric(seed, objectToSubdivide, faceTuple):
    
    # Initialize the random seed, this is important in order to generate exactly the same content for a given seed.
    random.seed(seed)
    
    # Find the right face despit faces that have been reindexed.
    #if checkIsSameFace(objectToSubdivide, faceTuple):
        #faceToSubdivideIndex = faceTuple[0]
    #else:
        #faceToSubdivideIndex = findFaceByVertices(objectToSubdivide, faceTuple[1])

    faceToSubdivideIndex = faceTuple[0]
    
    bpy.ops.object.mode_set(mode = 'EDIT')
    # Deselect everything.
    bpy.ops.mesh.select_all(action='DESELECT')
    
    # Selecting faces only works when not in edit mode, for some reason.
    bpy.ops.object.mode_set(mode = 'OBJECT')
    # Select only the face to inset.
    objectToSubdivide.data.polygons[faceToSubdivideIndex].select = True
    
    # Enter edit mode for the object in argument.
    bpy.context.view_layer.objects.active = objectToSubdivide
    bpy.ops.object.mode_set(mode = 'EDIT')
    
    bpy.ops.mesh.inset(thickness=0.0001)
    
    # Deselect everything again.
    bpy.ops.mesh.select_all(action='DESELECT')
    
    bpy.ops.object.mode_set(mode = 'OBJECT')
    
    objectToSubdivide.data.validate(verbose=True)
    objectToSubdivide.update_from_editmode()    
    
    faceToSubdivide = objectToSubdivide.data.polygons[faceToSubdivideIndex]

    if len(faceToSubdivide.edge_keys) != 4:
        print("Face does not have 4 edges.")
        return
    
    # Randomly choose if the cut if going to be vertical or horizontal.
    if random.uniform(0, 1) < verticalProbability:
        aEdgeKey = faceToSubdivide.edge_keys[0]
        bEdgeKey = faceToSubdivide.edge_keys[2]
    else:
        aEdgeKey = faceToSubdivide.edge_keys[1]
        bEdgeKey = faceToSubdivide.edge_keys[3]
    
    # Find the chosen edges in the object's data.
    aEdge = findEdge(objectToSubdivide.data, aEdgeKey)
    bEdge = findEdge(objectToSubdivide.data, bEdgeKey)
    
    # Select the chosen edges. Be careful, edges can only be selected properly when in object mode.
    aEdge.select = True
    bEdge.select = True

    bpy.ops.object.mode_set(mode = 'EDIT')
    # Randomly choose how many cuts are going to be applied.
    numberOfCuts = random.randint(minCuts, maxCuts)
    # Apply the subdivision.
    bpy.ops.mesh.subdivide(number_cuts=numberOfCuts, quadcorner='INNERVERT')
    
    # Refresh data.
    objectToSubdivide.data.validate(verbose=True)
    objectToSubdivide.update_from_editmode()
    
    # Return an array of face tuples for the selected faces.
    # The selected faces are the ones resulting of the subdivision.
    faceTuplesResult = [buildFaceTuple(objectToSubdivide, currentPolygon.index) for currentPolygon in objectToSubdivide.data.polygons if currentPolygon.select]

    return faceTuplesResult


# Test function
if __name__ == "__main__":
    # Keep track of the selected object.
    originalySelectedObject = bpy.context.active_object
    
    originalySelectedObject.data.validate(verbose=True)
    originalySelectedObject.update_from_editmode()
    
    for currentPolygon in originalySelectedObject.data.polygons:
        if currentPolygon.select:
            subdivideGeneric(datetime.now(), originalySelectedObject, buildFaceTuple(originalySelectedObject, currentPolygon.index))