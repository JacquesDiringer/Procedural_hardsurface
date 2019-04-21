import bpy
import bmesh

import mathutils
import random
from datetime import datetime

# Probabilities.
randomSeed = 0 # Seed for randomization, different everytime when set to negative.
rectangleProbability = 0.5 # Probability to pop a rectangle rather than a sphere.
poppingNewEdge = 1.0 # Probability for each edge to enter a recursive cycle if the recursivity limit has not been hit.
notchType45 = 0.5 # Probability to pop a 45 degrees notch.
outerProbability = 0.5 # Probability to have a notch coming outward rather than inward.
relativeWidthMin = 0.1 # Minimum length of a notch relative to the edge it is created from.
relativeWidthMax = 0.9 # Maximum length of a notch relative to the edge it is created from.
relativeDepthWidthRatioMax = 0.3 # Maximum depth of a notch relative to it's length.
thinnestOffset = 0.05 # The minimum distance between the beginning of a notch in the end of the initial edge.

# Rounding probabilities.
roundProbability = 0.5 # Probability of turning a 90 degrees angle into a curve.
outerRoundProbability = 0.5 # Probability of the curve to face outward.
roundSegments = 5 # Number of vertices composing the curve.

# Rectangles probabilities.
maximumRatioDifference = 0.2 # Maximum ratio between height and width, smaller values make for a bigger ratio. Should belong to [0 ; 1].
verticalProbability = 0.5 # Probability of poping a vertical rectangle if maximumRatioDifference is different from 1.

# Circle probabilities.
minmumCircleEdges = 3 # Minimum possible edges in a circle.
maximumCircleEdges = 6 # Maximum possible edges in a circle.


# Global settings.
generateNewCollection = False # When true, generate a new collection for each batch, when false, replaces the old collection content.
recursivity = 0 # Recursivity limit.
squareRadius = 5 # Drives the number of shapes generated.
symetry = False # When True, all edges will have the same details generated, even recursively.


# ___________    ->    _____       _____
#                           |_____|

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




# ___________    ->    _____       _____
#                           \_____/

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
        
    for currentEdge in range(0, len(bm.edges)):
        if symetry:
            # When symetry is enabled, take the same seed for every edge.
            futureSeed = seed
        else:
            # When symetry is disabled, randomize the seed for every edge.
            futureSeed = random.randint(0, 1000000)
            
        genericEdgeTransformation(futureSeed, bm, bm.edges[currentEdge], recursionDepth)

    # Some of the previous operations can cause some vertices to be at the same position, remove duplicates.
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.000001)
    
#    print("Final edges = " + str(len(bm.edges)))

    bm.edges.ensure_lookup_table()


    # Show the updates in the viewport
    # and recalculate n-gon tessellation.
    bmesh.update_edit_mesh(me, True)


    # Exit edit mode.
    bpy.ops.object.mode_set(mode = 'OBJECT')
    
    
        
# Generates a circle shape of 6 edges with recursive details.
def generateCircleCuttingShape(seed, position, dimension, edgeCount, recursionDepth):
    
    # Generate a plane.
    bpy.ops.mesh.primitive_circle_add(radius=0.4, vertices=edgeCount, location=(position))
    
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
    bpy.ops.mesh.primitive_plane_add(size=0.8, view_align=False, enter_editmode=False, location=(position))
    
    # Resize object in edit mode.
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.resize(value=(dimension[0], dimension[1], 1.0), orient_type='GLOBAL')
    bpy.ops.object.mode_set(mode = 'OBJECT')
    
    # Generic function to add details on edges.
    genericShapeTransformation(seed, recursionDepth)
    
    
def generateGenericCuttingShape(seed, position):
    # Initialize the random seed, this is important in order to generate exactly the same content for a given seed.
    random.seed(seed)
    
    if random.uniform(0,1) < rectangleProbability :
        # Generate a rectangle of random dimension.
        downscaleValue = random.uniform(maximumRatioDifference, 1.0)
        # Apply downscale on either x or y.
        if random.uniform(0,1) < verticalProbability :
            generateRectangleCuttingShape(seed=seed, position=position, dimension=((downscaleValue, 1)), recursionDepth=recursivity)
        else:
            generateRectangleCuttingShape(seed=seed, position=position, dimension=((1, downscaleValue)), recursionDepth=recursivity)
            
    else:
        # Generate a circle of random vertices.
        verticesCount = random.uniform(minmumCircleEdges, maximumCircleEdges)
        generateCircleCuttingShape(seed=seed, position=position, dimension=((1.0, 1.0)), edgeCount=verticesCount, recursionDepth=recursivity)







# Main

print("starting main")

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
        generateGenericCuttingShape(seed=xCoords + yCoords * squareRadius, position=(xCoords, yCoords, 0))