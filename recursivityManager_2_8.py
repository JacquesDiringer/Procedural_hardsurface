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

    
subdivisionProbability = 0.9
insetProbability = 0.5


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

    
# Test function
if __name__ == "__main__":
    
    squareSize = 4
    
    for xCoords in range(0, squareSize):
        for yCoords in range(0, squareSize):
            
            bpy.ops.mesh.primitive_plane_add(size=0.95, view_align=False, enter_editmode=False, location=(xCoords, yCoords, 0))
            
        
            # Keep track of the selected object.
            originalySelectedObject = bpy.context.active_object

            # Cut a plate in the selected object.
            #resultingFace = cutPlate(datetime.now(), originalySelectedObject, originalySelectedObject.data.polygons[0])
            #resultingFace = cutPlate(datetime.now(), originalySelectedObject, resultingFace)
            #resultingFace = cutPlate(datetime.now(), originalySelectedObject, resultingFace)
            #resultingFace = cutPlate(datetime.now(), originalySelectedObject, resultingFace)
            
            
        #    datetime.now()
            firstPolygon = originalySelectedObject.data.polygons[0]
            
            resultingFacesTuples = subdivideFaces(originalySelectedObject, [buildFaceTuple(originalySelectedObject, firstPolygon.index)])
            
            resultingFacesTuples = subdivideFaces(originalySelectedObject, resultingFacesTuples)
            resultingFacesTuples = subdivideFaces(originalySelectedObject, resultingFacesTuples)
            resultingFacesTuples = subdivideFaces(originalySelectedObject, resultingFacesTuples)
            resultingFacesTuples = subdivideFaces(originalySelectedObject, resultingFacesTuples)
            
            bpy.ops.object.mode_set(mode = 'OBJECT')
    


#    bpy.ops.object.mode_set(mode = 'EDIT')
    
    override, originalRegion3D = createOverrideContext()
    
    # Reset the view to it's original configuration.
    setRegion3D(override, originalRegion3D)
    