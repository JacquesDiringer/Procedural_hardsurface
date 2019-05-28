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
	cutPlate(originalySelectedObject, originalySelectedObject.data.polygons[0])
	
	# Enter edit mode.
	bpy.ops.object.mode_set(mode = 'EDIT')
	
	override, originalRegion3D = createOverrideContext()
	
	# Reset the view to it's original configuration.
	setRegion3D(override, originalRegion3D)