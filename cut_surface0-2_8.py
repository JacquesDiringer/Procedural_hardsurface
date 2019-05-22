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
generateCuttingShapesArray()