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

    
# Test function
if __name__ == "__main__":
    # Keep track of the selected object.
    originalySelectedObject = bpy.context.active_object

    # Cut a plate in the selected object.
    #resultingFace = cutPlate(datetime.now(), originalySelectedObject, originalySelectedObject.data.polygons[0])
    #resultingFace = cutPlate(datetime.now(), originalySelectedObject, resultingFace)
    #resultingFace = cutPlate(datetime.now(), originalySelectedObject, resultingFace)
    #resultingFace = cutPlate(datetime.now(), originalySelectedObject, resultingFace)
    
#    datetime.now()
    firstPolygon = originalySelectedObject.data.polygons[0]
    resultingFacesIndexes = subdivideGeneric(datetime.now(), originalySelectedObject, buildFaceTuple(originalySelectedObject, firstPolygon.index))
    
    print("resultingFacesIndexes : " + str(resultingFacesIndexes))
    
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
#    time.sleep(1)

    print()
    print()
    
    recursivesFacesIndexes = []
    
    for currentFaceTuple in resultingFacesIndexes:
        generatedFacesIndexes = subdivideGeneric(datetime.now(), originalySelectedObject, buildFaceTuple(originalySelectedObject, currentFaceTuple[0]))
        print("generatedFacesIndexes : " + str(generatedFacesIndexes))
        recursivesFacesIndexes.extend(generatedFacesIndexes)
        print("recursivesFacesIndexes : " + str(recursivesFacesIndexes))
        print()
        
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        #time.sleep(1)
    
    print()
    print()
        
    for currentFaceTuple in recursivesFacesIndexes:
        generatedFacesIndexes = subdivideGeneric(datetime.now(), originalySelectedObject, buildFaceTuple(originalySelectedObject, currentFaceTuple[0]))
        print("generatedFacesIndexes 2 : " + str(generatedFacesIndexes))
        print()
#        resultingFace = cutPlate(datetime.now(), originalySelectedObject, currentFace)
#        recursivesFaces.append(generatedFaces)

        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
#        time.sleep(0.5)

    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
#    time.sleep(1)
    
    override, originalRegion3D = createOverrideContext()
    
    # Reset the view to it's original configuration.
    setRegion3D(override, originalRegion3D)
    