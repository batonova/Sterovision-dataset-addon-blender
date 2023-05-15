import mathutils
import sys

def min_distance_to_parallelepiped(point, vertexes):
    min_distance = sys.float_info.max
    
    for i in range(len(vertexes)):
        p1 = vertexes[i]
        p2 = vertexes[(i + 1) % len(vertexes)]
        edge = p2 - p1
        edge_length = edge.length
        if edge_length > 0:
            t = max(0, min(1, (point - p1).dot(edge) / edge_length**2))
            projection = p1 + t * edge
            distance = (point - projection).length
            if distance < min_distance:
                min_distance = distance
    
    return min_distance

def max_distance_to_parallelepiped(point, parallelepiped):
    max_distance = -sys.float_info.max
    
    for vertex in parallelepiped:
        distance = (point - vertex).length
        if distance > max_distance:
            max_distance = distance
    
    return max_distance

def find_remaining_vertices(vertex1, vertex2):
    remaining_vertices = []
    for i in range(3):
        for j in range(2):
            remaining_vertex = mathutils.Vector(vertex1)
            remaining_vertex[i] = vertex2[i] if j == 1 else vertex1[i]
            remaining_vertices.append(remaining_vertex)
            
    return remaining_vertices

def find_scene_bounds(objects):
    # Расчет границ сцены
    min_coords = [float('inf'), float('inf'), float('inf')]
    max_coords = [float('-inf'), float('-inf'), float('-inf')]
        
    for obj in objects:
        bbox = obj.bound_box
        for point in bbox:
            point_global = obj.matrix_world @ mathutils.Vector(point)
            for i in range(3):
                min_coords[i] = min(min_coords[i], point_global[i])
                max_coords[i] = max(max_coords[i], point_global[i])
    
    return min_coords, max_coords
    
def find_scene_size(objects):
    min_coords, max_coords = find_scene_bounds(objects)
    # Вычисление размеров сцены
    scene_width = max_coords[0] - min_coords[0]
    scene_length = max_coords[1] - min_coords[1]
    scene_height = max_coords[2] - min_coords[2]
    scene_size = [scene_width, scene_length, scene_height]
    
    return scene_size
    
def find_scene_center(objects):
    min_coords, max_coords = find_scene_bounds(objects)
    # Определение центра сцены
    scene_center = mathutils.Vector([(max_coords[i] - min_coords[i]) / 2 + min_coords[i] for i in range(3)])
    
    return scene_center