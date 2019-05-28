import bpy
import bmesh

import mathutils
import random
from datetime import datetime

# Import submodules.
import sys
import os
import importlib
import copy

blend_dir = os.path.dirname(bpy.data.filepath)
if blend_dir not in sys.path:
   sys.path.append(blend_dir)

import cut_surface0_2_8
importlib.reload(cut_surface0_2_8)
from cut_surface0_2_8 import *


# Test function
if __name__ == "__main__":
    # Keep track of the selected object.
    originalySelectedObject = bpy.context.active_object

    # Cut a plate in the selected object.
    cutPlate(originalySelectedObject)
    
    # Enter edit mode.
    bpy.ops.object.mode_set(mode = 'EDIT')
    
    override, originalRegion3D = createOverrideContext()
    
    # After the cutPlate function, the selected vertices are the edges at the bottom of the crease.
    # Position the 3D cursor at the center of these vertices.
    bpy.ops.view3d.snap_cursor_to_selected(override)
    +
    # Select the connected faces, this will result in having the vertices on the inner face selected.
    # We need them selected to compute the largest rectangle encased in the inner face.
    bpy.ops.mesh.select_more()
    
    selectedVerticesPositions = [currentVertex.co for currentVertex in bpy.context.edit_object.data.vertices if currentVertex.select]
    
    for currentPosition in selectedVerticesPositions:
        print(str(currentPosition))
    
    # Reset the view to it's original configuration.
    setRegion3D(override, originalRegion3D)