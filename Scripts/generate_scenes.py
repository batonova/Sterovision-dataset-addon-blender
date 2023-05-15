import bpy
import random
import os
from mathutils import Euler, Vector

if __name__ == '__main__':
    
    scene_num = 10
    max_figure_num = 5

    # Создаем папку для сохранения сцен
    path = 'C:/labsss/'
    folder_path = os.path.join(path, 'scenes')
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Создание списка фигур
    shapes = ['Cube', 
              'Cone', 
              'Cylinder', 
              'UV_Sphere', 
              'ICO_Sphere', 
              #'Monkey', 
              'Torus']

    functions = {'Cone': bpy.ops.mesh.primitive_cone_add,
                'Cube': bpy.ops.mesh.primitive_cube_add,
                'Cylinder': bpy.ops.mesh.primitive_cylinder_add,
                'UV_Sphere': bpy.ops.mesh.primitive_uv_sphere_add,
                'ICO_Sphere': bpy.ops.mesh.primitive_ico_sphere_add,
                #'Monkey': bpy.ops.mesh.primitive_monkey_add,
                'Torus': bpy.ops.mesh.primitive_torus_add
    }

    # Создание списка цветов
    colors = [(1.0, 0.0, 0.0, 1.0), 
              (0.0, 1.0, 0.0, 1.0), 
              (0.0, 0.0, 1.0, 1.0), 
              (1.0, 1.0, 0.0, 1.0), 
              (0.0, 1.0, 1.0, 1.0)]

    # Создание списка материалов
    materials = []
    for color in colors:
        mat = bpy.data.materials.new(name=f"Material_{color}")
        mat.diffuse_color = color
        materials.append(mat)
        
    # Установка начальных параметров сцены
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)

    # Создание сцен
    for i in range(scene_num):
        # Создание новой сцены
        bpy.ops.scene.new(type='EMPTY')
        scene = bpy.context.scene
        
        figure_num = random.randint(1, max_figure_num)
        # Создание фигур на сцене
        for j in range(figure_num):
            shape = random.choice(shapes)
            color = random.choice(colors)
            material = materials[colors.index(color)]
            size = [random.uniform(0.5, 2.0) for i in range(3)]
            rotation = Euler((random.uniform(0, 2*3.14), random.uniform(0, 2*3.14), random.uniform(0, 2*3.14)), 'XYZ')
            location = Vector([random.uniform(-5.0 - max_figure_num//10*5, 5.0 + max_figure_num//10*5) for i in range(3)])
            functions[shape]()
            obj = bpy.context.object
            obj.name = f'{shape}_{j+1}'
            obj.location = location
            obj.scale = Vector(size)
            obj.rotation_euler = rotation
            obj.active_material = material
            
        light_set = [1] if random.randint(0, 1) else [1, -1]  
        # Установка света на сцене
        for j in light_set:
            lamp_data = bpy.data.lights.new(name="Light", type='POINT')
            lamp = bpy.data.objects.new(name="Light", object_data=lamp_data)
            bpy.context.collection.objects.link(lamp)
            lamp.location = Vector((-6*j - j*max_figure_num//10*5, j*6  + j*max_figure_num//10*5, j*6  + j*max_figure_num//10*5))
            lamp.data.energy = random.randint(1, 3) * 1000
            lamp.data.distance = 10


        # Сохранение сцены в файл
        scene_path = os.path.join(folder_path, f'Scene_{i+1}.blend')
        bpy.ops.wm.save_as_mainfile(filepath=scene_path)

        # Удаление сцены из памяти
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        
        bpy.ops.scene.delete()
