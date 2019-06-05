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
import utils_2_8
importlib.reload(utils_2_8)
from utils_2_8 import *


# Global parameters.
minCuts = 1 # Minimum number of cuts per subdivision.
maxCuts = 4 # Maximum number of cuts per subdivision.
verticalProbability = 0.5 # Probability of doing a vertical subdivision.

# Conditions
minimumLength = 0.2


# Should be in object mode when calling this function.
def findFirstSelectedPolygon(objectToSubdivide):
    for currentPolygon in objectToSubdivide.data.polygons:
        if currentPolygon.select:
            return currentPolygon


def subdivideGeneric(seed, objectToSubdivide, faceTuple):
    
    # Initialize the random seed, this is important in order to generate exactly the same content for a given seed.
    random.seed(seed)
    
    # Find the right face despit faces that have been reindexed.
    #if checkIsSameFace(objectToSubdivide, faceTuple):
        #faceToSubdivideIndex = faceTuple[0]
    #else:
        #faceToSubdivideIndex = findFaceByVertices(objectToSubdivide, faceTuple[1])

    faceToSubdivideIndex = faceTuple[0]
    faceToSubdivide = objectToSubdivide.data.polygons[faceToSubdivideIndex]
    
    # Sanity check.
    if len(faceToSubdivide.edge_keys) != 4:
        print("Face does not have 4 edges.")
        return
    
    # Decide whether the subidivision is to happen vertically of horizontally.
    if random.uniform(0, 1) < verticalProbability:
        verticalSubdivision = True
    else:
        verticalSubdivision = False
    
    if verticalSubdivision:
        aEdgeKey = faceToSubdivide.edge_keys[0]
    else:
        aEdgeKey = faceToSubdivide.edge_keys[1]
    
    # Minimum length test.
    point0Coordinates = objectToSubdivide.data.vertices[aEdgeKey[0]].co
    point1Coordinates = objectToSubdivide.data.vertices[aEdgeKey[1]].co
    edgeLength = distance(point0Coordinates, point1Coordinates)
    if edgeLength < minimumLength:
        return None
    
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
    
    bpy.ops.object.mode_set(mode = 'OBJECT')
    faceToSubdivide_inset = findFirstSelectedPolygon(objectToSubdivide)
    
    if verticalSubdivision:
        aEdgeKey_inset = faceToSubdivide_inset.edge_keys[0]
        bEdgeKey_inset = faceToSubdivide_inset.edge_keys[2]
    else:
        aEdgeKey_inset = faceToSubdivide_inset.edge_keys[1]
        bEdgeKey_inset = faceToSubdivide_inset.edge_keys[3]
    
    # Find the chosen edges in the object's data.
    aEdge_inset = findEdge(objectToSubdivide.data, aEdgeKey_inset)
    bEdge_inset = findEdge(objectToSubdivide.data, bEdgeKey_inset)
    
    # Deselect all the faces.
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    
    # Find the index of the edges to select.
    # We get the index rather than the edge itself because of references issues.
    aEdgeIndex_inset = findEdgeIndex(objectToSubdivide.data, aEdgeKey_inset)
    bEdgeIndex_inset = findEdgeIndex(objectToSubdivide.data, bEdgeKey_inset)
    
    # Select the chosen edges. Be careful, edges can only be selected properly when in object mode.
    bpy.ops.object.mode_set(mode = 'OBJECT')
    objectToSubdivide.data.edges[aEdgeIndex_inset].select = True
    objectToSubdivide.data.edges[bEdgeIndex_inset].select = True

    bpy.ops.object.mode_set(mode = 'EDIT')
    # Randomly choose how many cuts are going to be applied.
    numberOfCuts = random.randint(minCuts, maxCuts)
    # Apply the subdivision.
    subdivisionResult = bpy.ops.mesh.subdivide(number_cuts=numberOfCuts, quadcorner='INNERVERT')
    
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