import bpy
import bmesh

import copy
import mathutils
import random
import time
from datetime import datetime
from mathutils import Euler

minCuts = 1 # Minimum number of cuts per subdivision.
maxCuts = 2 # Maximum number of cuts per subdivision.
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
    
    print("objectToSubdivide : " + str(objectToSubdivide))
    
    # Find the right face despit faces that have been reindexed.
    if checkIsSameFace(objectToSubdivide, faceTuple):
        faceToSubdivideIndex = faceTuple[0]
    else:
        faceToSubdivideIndex = findFaceByVertices(objectToBrowse, faceTuple[1])
    
    # Enter edit mode for the object in argument.
    bpy.context.view_layer.objects.active = objectToSubdivide
    print("before entering edit mode")
    bpy.ops.object.mode_set(mode = 'EDIT')
    
    bpy.ops.mesh.inset(use_boundary=True, use_even_offset=True, use_relative_offset=True, use_edge_rail=False, thickness=0.001, depth=0, use_outset=False, use_select_inset=False, use_individual=False, use_interpolate=True)
    
    # Deselect everything.
    bpy.ops.mesh.select_all(action='DESELECT')
    
    bpy.ops.object.mode_set(mode = 'OBJECT')
    
    objectToSubdivide.data.validate(verbose=True)
    objectToSubdivide.update_from_editmode()    
    
    
    print("faceToSubdivideIndex : " + str(faceToSubdivideIndex))
    # TODO : test how the indexes change for the face.
    faceToSubdivide = objectToSubdivide.data.polygons[faceToSubdivideIndex]
    
    print("faceToSubdivide : " + str(faceToSubdivide))
    print("faceToSubdivide vertices : " + str(faceToSubdivide.vertices))
    print("faceToSubdivide vertices length = " + str(len(faceToSubdivide.vertices)))
    
    #try:
    print("face edges count = " + str(len(faceToSubdivide.edge_keys)))
    
    #for currentEdgeKey in faceToSubdivide.edge_keys:
        #print("edgeKey = " + str(currentEdgeKey))
    
    if len(faceToSubdivide.edge_keys) != 4:
        print("Face does not have 4 edges.")
        return
    
    if random.uniform(0, 1) < verticalProbability:
        aEdgeKey = faceToSubdivide.edge_keys[0]
        bEdgeKey = faceToSubdivide.edge_keys[2]
    else:
        aEdgeKey = faceToSubdivide.edge_keys[1]
        bEdgeKey = faceToSubdivide.edge_keys[3]
    
    #print("aEdgeKey = " + str(aEdgeKey))
    #print("bEdgeKey = " + str(bEdgeKey))
    
    aEdge = findEdge(objectToSubdivide.data, aEdgeKey)
    bEdge = findEdge(objectToSubdivide.data, bEdgeKey)
    
    aEdge.select = True
    bEdge.select = True

    bpy.ops.object.mode_set(mode = 'EDIT')
    numberOfCuts = random.randint(minCuts, maxCuts)
    bpy.ops.mesh.subdivide(number_cuts=numberOfCuts, quadcorner='INNERVERT')
    
    #objectToSubdivide.data.update()
    objectToSubdivide.data.validate(verbose=True)
    objectToSubdivide.update_from_editmode()
    
#    resultingFacesIndexes = [currentPolygon.index for currentPolygon in objectToSubdivide.data.polygons if currentPolygon.select]
    
    
    faceTuplesResult = [buildFaceTuple(objectToSubdivide, currentPolygon.index) for currentPolygon in objectToSubdivide.data.polygons if currentPolygon.select]
    
    #faceTupleResult = []
    #for currentFace in resultingFaces:
        #faceTupleResult.append((currentFace.index, currentFace.vertices))

    return faceTuplesResult 
    
    #except :
        #print("Exception handled")
        #return None


# Test function
if __name__ == "__main__":
    # Keep track of the selected object.
    originalySelectedObject = bpy.context.active_object
    
    #bpy.ops.object.mode_set(mode = 'OBJECT')
    #bpy.ops.object.mode_set(mode = 'EDIT')
    
    #originalySelectedObject.data.update()
    originalySelectedObject.data.validate(verbose=True)
    originalySelectedObject.update_from_editmode()
    
    print("originalySelectedObject : " + str(originalySelectedObject))
    
    for currentPolygon in originalySelectedObject.data.polygons:
        if currentPolygon.select:
            subdivideGeneric(datetime.now(), originalySelectedObject, buildFaceTuple(originalySelectedObject, currentPolygon.index))