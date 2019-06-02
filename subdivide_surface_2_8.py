import bpy
import bmesh

import copy
import mathutils
import random
import time
from datetime import datetime
from mathutils import Euler

minCuts = 1 # Minimum number of cuts per subdivision.
maxCuts = 4 # Maximum number of cuts per subdivision.
verticalProbability = 0.5 # Probability of doing a vertical subdivision.

def findEdge(mesh, edgeKey):
    for currentEdge in mesh.edges:
        currentEdgeKey = currentEdge.key
        if (currentEdgeKey[0] == edgeKey[0] and currentEdgeKey[1] == edgeKey[1]):
            return currentEdge
        

def buildFaceTuple(objectToBrowse, faceIndex):
    polygon = objectToBrowse.data.polygons[faceIndex]
    
    verticesArray = []
    for currentVertexIndex in polygon.vertices:
        # Make a deep copy of the vertex to be sure it doesn't get modified accidentaly.
        currentCoordinates = objectToBrowse.data.vertices[currentVertexIndex].co
        verticesArray.append((currentCoordinates.x, currentCoordinates.y, currentCoordinates.z))
    
    return (faceIndex, verticesArray)



# The face tuple should contain first the index of the face, then an array of vertices.
def checkIsSameFace(objectToBrowse, faceTuple):
    faceIndex = faceTuple[0]
    verticesArray = faceTuple[1]
    
    faceToCheck = objectToBrowse.data.polygons[faceIndex]
    
    polygonMatches = True
    
    for currentVertexIndexFromPolygon in faceToCheck.vertices:
        currentVertexFromPolygon = objectToBrowse.data.vertices[currentVertexIndexFromPolygon]
        foundSameVertice = False
        for currentVertexFromArray in verticesArray:
            if  currentVertexFromArray[0] == currentVertexFromPolygon.co.x and currentVertexFromArray[1] == currentVertexFromPolygon.co.y and currentVertexFromArray[2] == currentVertexFromPolygon.co.z:
                foundSameVertice = True
        # If one of the vertices doesn't match, then the polygon doesn't match.
        if foundSameVertice == False:
            polygonMatches = False
    
    # If all the vertices in the polygon matched, then polygonMatches is still True.
    return polygonMatches


# Function to find a face in an object according to the position of the vertices it contains.
# This function is necessary because faces tend to change index when others are created.
def findFaceByVertices(objectToBrowse, verticesArray):
    foundFace = None
    
    dataToBrowse = objectToBrowse.data
    
    for currentPolygon in dataToBrowse.polygons:
        if checkIsSameFace(objectToBrowse, (currentPolygon.index, verticesArray)):
            foundFace = currentPolygon.index
    
    return foundFace


def subdivideGeneric(seed, objectToSubdivide, faceTuple):
    
    # Initialize the random seed, this is important in order to generate exactly the same content for a given seed.
    random.seed(seed)
    
    # Find the right face despit faces that have been reindexed.
    if checkIsSameFace(objectToSubdivide, faceTuple):
        faceToSubdivideIndex = faceTuple[0]
    else:
        faceToSubdivideIndex = findFaceByVertices(objectToBrowse, faceTuple[1])
    
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
    
    # Deselect everything again.
    bpy.ops.mesh.select_all(action='DESELECT')
    
    bpy.ops.object.mode_set(mode = 'OBJECT')
    
    objectToSubdivide.data.validate(verbose=True)
    objectToSubdivide.update_from_editmode()    
    
    faceToSubdivide = objectToSubdivide.data.polygons[faceToSubdivideIndex]

    if len(faceToSubdivide.edge_keys) != 4:
        print("Face does not have 4 edges.")
        return
    
    # Randomly choose if the cut if going to be vertical or horizontal.
    if random.uniform(0, 1) < verticalProbability:
        aEdgeKey = faceToSubdivide.edge_keys[0]
        bEdgeKey = faceToSubdivide.edge_keys[2]
    else:
        aEdgeKey = faceToSubdivide.edge_keys[1]
        bEdgeKey = faceToSubdivide.edge_keys[3]
    
    # Find the chosen edges in the object's data.
    aEdge = findEdge(objectToSubdivide.data, aEdgeKey)
    bEdge = findEdge(objectToSubdivide.data, bEdgeKey)
    
    # Select the chosen edges. Be careful, edges can only be selected properly when in object mode.
    aEdge.select = True
    bEdge.select = True

    bpy.ops.object.mode_set(mode = 'EDIT')
    # Randomly choose how many cuts are going to be applied.
    numberOfCuts = random.randint(minCuts, maxCuts)
    # Apply the subdivision.
    bpy.ops.mesh.subdivide(number_cuts=numberOfCuts, quadcorner='INNERVERT')
    
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