import bpy
import bmesh

import mathutils
import random
from datetime import datetime

# Import submodules.
import sys
import os
import importlib

blend_dir = os.path.dirname(bpy.data.filepath)
if blend_dir not in sys.path:
   sys.path.append(blend_dir)

import generate_cuttingShape0_2_8

importlib.reload(generate_cuttingShape0_2_8)

from generate_cuttingShape0_2_8 import *




# Test function.
createdShape = generateRectangleCuttingShape(seed=1, position=(0, 0, 0), dimension=(3, 0.5), recursionDepth=0)

print(str(createdShape))