import bpy
import bmesh

import copy
import mathutils
import random
import time
from datetime import datetime
from mathutils import Euler




### 3D Context creation. ###

def view3d_find( return_area = False ):
    # returns first 3d view, normally we get from context
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            v3d = area.spaces[0]
            rv3d = v3d.region_3d
            for region in area.regions:
                if region.type == 'WINDOW':
                    if return_area: return region, rv3d, v3d, area
                    return region, rv3d, v3d
    return None, None

def createOverrideContext():
    region, rv3d, v3d, area = view3d_find(True)

    # Define context override dictionary for overriding the knife_project operator's context
    override = {
        'scene'            : bpy.context.scene,
        'region'           : region,
        'area'             : area,
        'space'            : v3d,
        'active_object'    : bpy.context.object,
        'window'           : bpy.context.window,
        'screen'           : bpy.context.screen,
        'selected_objects' : bpy.context.selected_objects,
        'edit_object'      : bpy.context.object,
        'region_3d'        : rv3d
    }
    
    originalRegion3D = {
        'view_location'     : copy.copy(rv3d.view_location),
        'view_distance'     : rv3d.view_distance,
        'view_rotation'     : copy.copy(rv3d.view_rotation),
        'view_perspective'  : rv3d.view_perspective}
    
    # Set the view to origin with a small distance so that we have a better precision for the knife projection.
    rv3d.view_location = (0,0,0)
    rv3d.view_distance = 1
    
    # Set view to TOP by directly rotating the 3D view region's view_rotation.
    rv3d.view_rotation = Euler( (0,0,0) ).to_quaternion()
    
    # Set the canera to orthographic.
    rv3d.view_perspective = 'ORTHO'
    
    return override, originalRegion3D

def setRegion3D(override, originalConfiguration):
    rv3d = override['region_3d']
    
    rv3d.view_location      = originalConfiguration['view_location']
    rv3d.view_distance      = originalConfiguration['view_distance']
    rv3d.view_rotation      = originalConfiguration['view_rotation']
    rv3d.view_perspective   = originalConfiguration['view_perspective']
    
    
### Handling meshes. ###


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
