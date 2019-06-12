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

# Utils.
import utils_2_8
importlib.reload(utils_2_8)
from utils_2_8 import *



# Probabilities.
randomSeed = 0 # Seed for randomization, different everytime when set to negative.
poppingNewEdge = 1.0 # Probability for each edge to enter a recursive cycle if the recursivity limit has not been hit.
notchType45 = 0.5 # Probability to pop a 45 degrees notch.
outerProbability = 0.5 # Probability to have a notch coming outward rather than inward.
relativeWidthMin = 0.1 # Minimum length of a notch relative to the edge it is created from.
relativeWidthMax = 0.9 # Maximum length of a notch relative to the edge it is created from.
relativeDepthWidthRatioMax = 0.3 # Maximum depth of a notch relative to it's length.
thinnestOffset = 0.05 # The minimum distance between the beginning of a notch in the end of the initial edge.

# Rounding probabilities.
roundProbability = 0.0 # Probability of turning a 90 degrees angle into a curve.
outerRoundProbability = 0.5 # Probability of the curve to face outward.
roundSegments = 5 # Number of vertices composing the curve.

# Rectangles probabilities.
rectangleProbability = 0.5 # Probability to pop a rectangle rather than a sphere.
maximumRatioDifference = 0.2 # Maximum ratio between height and width, smaller values make for a bigger ratio. Should belong to [0 ; 1].
verticalProbability = 0.5 # Probability of poping a vertical rectangle if maximumRatioDifference is different from 1.

# Circle probabilities.
minmumCircleEdges = 3 # Minimum possible edges in a circle.
maximumCircleEdges = 6 # Maximum possible edges in a circle.


# Global settings.
recursivity = 0 # Recursivity limit.
symetry = False # When True, all edges will have the same details generated, even recursively.


# This function generates a square of 1 unit on the sides, facing up.
# Then returns it.
def generateUnitSquare():
	verts = [   (-0.5, -0.5, 0),
				(0.5, -0.5, 0),
				(0.5, 0.5, 0),
				(-0.5, 0.5, 0)] 

	mesh = bpy.data.meshes.new("UnitPlaneMesh")  # add a new mesh
	obj = bpy.data.objects.new("UnitPlane", mesh)  # add a new object using the mesh

	scene = bpy.context.scene
	#scene.objects.link(obj)  # put the object into the scene (link)
#    scene.objects.active = obj  # set as the active object in the scene
#    obj.select = True  # select object

#    mesh = bpy.context.object.data
	bm = bmesh.new()

	for v in verts:
		bm.verts.new(v)  # add a new vert

	# Refresh bmesh.
	bm.verts.ensure_lookup_table()   
	bm.edges.ensure_lookup_table()
		
	bm.edges.new((bm.verts[0], bm.verts[1]))
	bm.edges.new((bm.verts[1], bm.verts[2]))
	bm.edges.new((bm.verts[2], bm.verts[3]))
	bm.edges.new((bm.verts[3], bm.verts[0]))

	# make the bmesh the object's mesh
	bm.to_mesh(mesh)  
	bm.free()  # always do this when finished
	
	return obj


# ___________    ->    _____	   _____
#   						|_____|

def edgeToNotch90(originalBmesh, edge, relativeWidth, widthOffset, relativeDepth, outer):
	
	# Remember the original 2 vertices.
	vertA = edge.verts[0]
	vertB = edge.verts[1]
	
	# First delete the original edge (but not the associated verts).
	edgeToDelete = [edge]
	bmesh.ops.delete(originalBmesh, geom=edgeToDelete, context='EDGES')
	
	# Local coordinate system.
	vectorU = vertB.co - vertA.co
	vectorV = mathutils.Vector((-vectorU.y, vectorU.x, 0))
	
	if (outer):
		vectorV = -vectorV
	
	# Outer part.
	# C vert.
	vertC = originalBmesh.verts.new(vertA.co + widthOffset * vectorU)
	# F vert.
	vertF = originalBmesh.verts.new(vertA.co + (widthOffset + relativeWidth) * vectorU)
	
	# Inner part.
	# D vert.
	vertD = originalBmesh.verts.new(vertA.co + widthOffset * vectorU + relativeDepth * vectorV)
	# E vert.
	vertE = originalBmesh.verts.new(vertA.co + (widthOffset + relativeWidth) * vectorU + relativeDepth * vectorV)

	# Link vertices as edges.
	newEdges = []
	newEdges.append(originalBmesh.edges.new((vertA, vertC)))
	newEdges.append(originalBmesh.edges.new((vertC, vertD)))
	newEdges.append(originalBmesh.edges.new((vertD, vertE)))
	newEdges.append(originalBmesh.edges.new((vertE, vertF)))
	newEdges.append(originalBmesh.edges.new((vertF, vertB)))
	
	return newEdges




# ___________    ->    _____	   _____
#   						\_____/

def edgeToNotch45(originalBmesh, edge, relativeWidth, widthOffset, relativeDepth, outer):
	
	originalBmesh.edges.ensure_lookup_table()
	
	# Remember the original 2 vertices.
	vertA = edge.verts[0]
	vertB = edge.verts[1]
	
	# First delete the original edge (but not the associated verts).
	edgeToDelete = [edge]
	bmesh.ops.delete(originalBmesh, geom=edgeToDelete, context='EDGES')
	
	originalBmesh.edges.ensure_lookup_table()
	
	# Local coordinate system.
	vectorU = vertB.co - vertA.co
	vectorV = mathutils.Vector((-vectorU.y, vectorU.x, 0))
	
	if (outer):
		vectorV = -vectorV
	
	# Outer part.
	# C vert.
	vertC = originalBmesh.verts.new(vertA.co + widthOffset * vectorU)
	# F vert.
	vertF = originalBmesh.verts.new(vertA.co + (widthOffset + relativeWidth) * vectorU)
	
	# Inner part.
	# D vert.
	vertD = originalBmesh.verts.new(vertA.co + (widthOffset + relativeDepth) * vectorU + relativeDepth * vectorV)
	# E vert.
	vertE = originalBmesh.verts.new(vertA.co + (widthOffset + relativeWidth - relativeDepth) * vectorU + relativeDepth * vectorV)
	
	# Link vertices as edges.
	newEdges = []
	newEdges.append(originalBmesh.edges.new((vertA, vertC)))
	newEdges.append(originalBmesh.edges.new((vertC, vertD)))
	newEdges.append(originalBmesh.edges.new((vertD, vertE)))
	newEdges.append(originalBmesh.edges.new((vertE, vertF)))
	newEdges.append(originalBmesh.edges.new((vertF, vertB)))
	
	return newEdges

def vertToRound(originalBmesh, vertList, outerRound):
	
	originalBmesh.edges.ensure_lookup_table()
	
	if outerRound:
		chosenProfile = 0.125
	else:
		chosenProfile = 0.5
	
	# Rounding operation.
	bmesh.ops.bevel(originalBmesh, geom=vertList, offset_type='OFFSET', offset=1.05, segments=roundSegments, profile=chosenProfile, vertex_only=True, clamp_overlap=True)
	
	originalBmesh.edges.ensure_lookup_table()
	
	
def genericEdgeTransformation(seed, originalBmesh, edgeToTransform, recursionDepth):
	
	# Initialize the random seed, this is important in order to generate exactly the same content for a given seed.
	random.seed(seed)

	# Useful for the final depth computation.
	edgeToTransformLength = edgeLength(edgeToTransform)

	# Variables to return.
	currentDepth = None
	outer = None
	
	# Decide if there is going to be a recursion pass for this edge.
	if(random.uniform(0, 1) < poppingNewEdge):
		
		# Temp variables.
		currentWidth = random.uniform(relativeWidthMin, relativeWidthMax)
		widthOffset = random.uniform(thinnestOffset, (1.0 - thinnestOffset) - currentWidth)
		currentDepth = random.uniform(0.01, currentWidth * relativeDepthWidthRatioMax)
		outer = random.uniform(0,1) < outerProbability
		
		# Decide what the next recursive function is.
		if(random.uniform(0, 1) < notchType45):
			returnedEdges = edgeToNotch45(originalBmesh, edgeToTransform, currentWidth, widthOffset, currentDepth, outer)
		else:
			returnedEdges = edgeToNotch90(originalBmesh, edgeToTransform, currentWidth, widthOffset, currentDepth, outer)
		
			# Only for 90 degrees notches will we round some vertices up.
			# Count vertices that are encountered twice, therefore all the vertices that do not belong to the sides of this edge selection.
			vertDictionary = {}
			for currentEdge in returnedEdges:
				for currentVert in currentEdge.verts:
					if currentVert in vertDictionary:
						vertDictionary[currentVert] = vertDictionary[currentVert] + 1
					else:
						vertDictionary[currentVert] = 1
			
			# Select only the inner vertices.   		 
			innerVertices = [currentVert for currentVert, currentCount in vertDictionary.items() if currentCount >= 2]
			# Of the inner vertices, select only some randomly.
			innerVerticesRandom = [currentVert for currentVert in innerVertices if random.uniform(0,1) < roundProbability]
			
			#Randomly choose if an the rounding will be an inner or outer one.
			outerRound = random.uniform(0,1) < outerRoundProbability
			# Apply the rounding to the randomly selected vertices.
			vertToRound(originalBmesh, innerVerticesRandom, outerRound)
		
		# Recursion.
		if recursionDepth > 0:
			for currentEdge in returnedEdges:
				if symetry:
					# When symetry is enabled, take the same seed for every edge.
					futureSeed = seed
				else:
					# When symetry is disabled, randomize the seed for every edge.
					futureSeed = random.randint(0, 1000000)
			
				genericEdgeTransformation(futureSeed, originalBmesh, currentEdge, recursionDepth - 1)
		
		originalBmesh.edges.ensure_lookup_table()

		# The actual depth length is the proportional depth * the edge length.
		currentDepth = currentDepth * edgeToTransformLength
		
		if outer:
			return currentDepth
		else:
			return -currentDepth
		
		

# Loops trough edges to add detail recursively.
# The shape to change must be selected before entering the function.
def genericShapeTransformation(seed, recursionDepth):
	# Initialize the random seed, this is important in order to generate exactly the same content for a given seed.
	random.seed(seed)
	
	# Enter edit mode.
	bpy.ops.object.mode_set(mode = 'EDIT')

	# Delete the center face.
	bpy.ops.mesh.delete(type='ONLY_FACE')

	# Set the selection mode to edges.
	bpy.ops.mesh.select_mode(type="EDGE")

	# Get the active mesh
	obj = bpy.context.edit_object
	me = obj.data

	# Get a BMesh representation
	bm = bmesh.from_edit_mesh(me)

	bpy.ops.mesh.select_all(action='DESELECT')

	# Browse edges.
	bm.edges.ensure_lookup_table()

#    print("Initial edges = " + str(len(bm.edges)))
	
	# Keep track of the maximum depth (negative or positive) encountered on each edge.
	edgesDepth = []
	
	for currentEdge in range(0, len(bm.edges)):
		if symetry:
			# When symetry is enabled, take the same seed for every edge.
			futureSeed = seed
		else:
			# When symetry is disabled, randomize the seed for every edge.
			futureSeed = random.randint(0, 1000000)
			
		currentEdgeDepth = genericEdgeTransformation(futureSeed, bm, bm.edges[currentEdge], recursionDepth)
		edgesDepth.append(currentEdgeDepth)

	# Some of the previous operations can cause some vertices to be at the same position, remove duplicates.
	bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.000001)
	
#    print("Final edges = " + str(len(bm.edges)))

	bm.edges.ensure_lookup_table()


	# Show the updates in the viewport
	# and recalculate n-gon tessellation.
	bmesh.update_edit_mesh(me, True)


	# Exit edit mode.
	bpy.ops.object.mode_set(mode = 'OBJECT')

	return edgesDepth
	
		
# Generates a circle shape of 6 edges with recursive details.
def generateCircleCuttingShape(seed, position, dimension, edgeCount, recursionDepth):
	
	# Generate a plane.
	bpy.ops.mesh.primitive_circle_add(radius=0.4, vertices=edgeCount, location=(position))

	# Keep track of the created object.
	createdShape = bpy.context.active_object
	createdShape.name = "circle_cuttingShape"
	createdShape.data.name = "circle_cuttingShape_mesh"
	
	# Resize object in edit mode.
	bpy.ops.object.mode_set(mode = 'EDIT')
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.transform.resize(value=(dimension[0], dimension[1], 1.0), orient_type='GLOBAL')
	bpy.ops.object.mode_set(mode = 'OBJECT')

	# Generic function to add details on edges.
	genericShapeTransformation(seed, recursionDepth)
	
	
# Generates a rectangular shape with recursive details.
def generateRectangleCuttingShape(seed, position, dimension, recursionDepth):

	# Generate a plane.
	bpy.ops.mesh.primitive_plane_add(size=1.0, view_align=False, enter_editmode=False, location=(position))
	
	# Keep track of the created object.
	createdShape = bpy.context.active_object
	createdShape.name = "rectangle_cuttingShape"
	createdShape.data.name = "rectangle_cuttingShape_mesh"
	
	# Resize object in edit mode.
	bpy.ops.object.mode_set(mode = 'EDIT')
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.transform.resize(value=(dimension[0], dimension[1], 1.0), orient_type='GLOBAL')
	bpy.ops.object.mode_set(mode = 'OBJECT')
	
	# Generic function to add details on edges.
	edgesDepth = genericShapeTransformation(seed, recursionDepth)

	return createdShape, edgesDepth
	
	
def generateGenericCuttingShape(seed, position):
	# Initialize the random seed, this is important in order to generate exactly the same content for a given seed.
	random.seed(seed)
	
	if random.uniform(0,1) < rectangleProbability :
		# Generate a rectangle of random dimension.
		downscaleValue = random.uniform(maximumRatioDifference, 1.0)
		# Apply downscale on either x or y.
		if random.uniform(0,1) < verticalProbability :
			createdShape = generateRectangleCuttingShape(seed=seed, position=position, dimension=((downscaleValue, 1)), recursionDepth=recursivity)
		else:
			createdShape = generateRectangleCuttingShape(seed=seed, position=position, dimension=((1, downscaleValue)), recursionDepth=recursivity)
			
	else:
		# Generate a circle of random vertices.
		verticesCount = random.uniform(minmumCircleEdges, maximumCircleEdges)
		createdShape = generateCircleCuttingShape(seed=seed, position=position, dimension=((1.0, 1.0)), edgeCount=verticesCount, recursionDepth=recursivity)

	return createdShape







# Populate a square with random cutting shapes.
# squareRadius, Drives the number of shapes generated.
# generateNewCollection, When true, generate a new collection for each batch, when false, replaces the old collection content.
def generateCuttingShapesArray(squareRadius = 5, generateNewCollection = False):

	print("generating a collection of hard surface shapes")

	if not generateNewCollection:
		# Delete the old collection
		singletonCollectionIndex = bpy.context.scene.collection.children.find("hardsurface_shapes")
		if singletonCollectionIndex >= 0:
			singletonCollection = bpy.context.scene.collection.children[singletonCollectionIndex]
			# Remove meshes data to avoid orphans.
			for currentObject in singletonCollection.objects:
				bpy.data.meshes.remove(currentObject.data)
			# Remove the collection from the scene.
			bpy.context.scene.collection.children.unlink(singletonCollection)
			bpy.data.collections.remove(singletonCollection)
		
	# Create a new collection.
	testCollection = bpy.data.collections.new("hardsurface_shapes")
	# Link it to the current scene.
	bpy.context.scene.collection.children.link(testCollection)
	# Make the added collection active.
	bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[testCollection.name]

	# Make all collections invisible excepting for the new one.
	for currentChild in bpy.context.scene.collection.children:
		currentChild.hide_viewport = True
	testCollection.hide_viewport = False



	# Intialize seed.
	if randomSeed >= 0 :
		random.seed(randomSeed)
	else:
		# Take the current time to randomize the seed when we want it different each time.
		random.seed(datetime.now())

	#generateGenericShape(seed=randomSeed, position=(0, 0, 0))

	for xCoords in range(-squareRadius, squareRadius):
		for yCoords in range(-squareRadius, squareRadius):
			generateGenericCuttingShape(seed=xCoords + yCoords * squareRadius * 2, position=(xCoords, yCoords, 0))


# Test function
if __name__ == "__main__":
	generateCuttingShapesArray()