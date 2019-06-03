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

insetThickness      = 0.01   # Thickness of the inset operation.
insetDepth          = 0.01   # Depth of the inset operation.
insetRelativeOffset = True # True of the offset value should represent a proportion of offset.

inwardProbability   = 0.5   # Probability of the inset to go in the surface's direction.


def insetGeneric(seed, objectToInset, faceTuple):
    
    # Initialize the random seed, this is important in order to generate exactly the same content for a given seed.
    random.seed(seed)
    
    # Find the right face despit faces that have been reindexed.
    #if checkIsSameFace(objectToInset, faceTuple):
        #print("face corresponding")
        #faceToSubdivideIndex = faceTuple[0]
    #else:
        #print("no correspondance")
        #faceToSubdivideIndex = findFaceByVertices(objectToInset, faceTuple[1])
        
    faceToSubdivideIndex = faceTuple[0]
    
    
    bpy.ops.object.mode_set(mode = 'EDIT')
    # Deselect everything.
    bpy.ops.mesh.select_all(action='DESELECT')
    
    # Selecting faces only works when not in edit mode, for some reason.
    bpy.ops.object.mode_set(mode = 'OBJECT')
    # Select only the face to inset.
    objectToInset.data.polygons[faceToSubdivideIndex].select = True
    
    # Enter edit mode for the object in argument.
    bpy.context.view_layer.objects.active = objectToInset
    bpy.ops.object.mode_set(mode = 'EDIT')
    
    # Randomly pick if the inset is to be made inward or outward.
    if random.uniform(0, 1) < inwardProbability:
        finalDepth = -insetDepth
    else:
        finalDepth = insetDepth
    
    # Perform the inset operation.
    bpy.ops.mesh.inset(thickness=insetThickness, depth=finalDepth, use_relative_offset=insetRelativeOffset)
    
    # Refresh data.
    objectToInset.data.validate(verbose=True)
    objectToInset.update_from_editmode()
    
    # Return an array of face tuples for the selected face.
    # The selected face is the one resulting of the inset.
    faceTuplesResult = [buildFaceTuple(objectToInset, currentPolygon.index) for currentPolygon in objectToInset.data.polygons if currentPolygon.select]

    return faceTuplesResult


# Test function
if __name__ == "__main__":
    # Keep track of the selected object.
    originalySelectedObject = bpy.context.active_object
    
    originalySelectedObject.data.validate(verbose=True)
    originalySelectedObject.update_from_editmode()
    
    for currentPolygon in originalySelectedObject.data.polygons:
        if currentPolygon.select:
            insetGeneric(datetime.now(), originalySelectedObject, buildFaceTuple(originalySelectedObject, currentPolygon.index))