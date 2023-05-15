import random
import bpy
import addon_utils
import mathutils
import os
import sys

property_dictionary = {'record_num': None,
                       'no_select_folder': None,
                       'source_path': None,
                       'target_path': None,
                       'image_resolution_y': None,
                       'image_resolution_x': None,
                       'dataset_name': None,
                       'convergence_mode': None,
                       'convergence_distance': None,
                       'interocular_distance': None,
                       'camera_properties': None,
                       'add_vertices': None,
                       'camera_variant': None
}

def addon_folder(addon_name):
    
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == addon_name:
            filepath = mod.__file__
            break
        else:
            pass
    
    source_path = os.path.dirname(filepath)
    
    return source_path

def add_modules(addon_name, folder):
    source_path = addon_folder(addon_name)
    source_path = os.path.join(source_path, folder)
    
    try:
        sys.path.index(source_path)
    except ValueError:
        sys.path.append(source_path)
        
    return source_path

add_modules("Dataset generation", 'lib')
add_modules("Dataset generation", 'scripts')

from PIL import Image

import geometric_utilities, file_utilities

class Scene():
    
    record_num = None
    no_select_folder = None
    source_path = None
    target_path = None
    image_resolution_y = None
    image_resolution_x = None
    dataset_name = None
    convergence_distance = None
    interocular_distance = None
    convergence_mode = None
    camera_properties = None
    add_vertices = None
    camera_variant = None
    
    convergence_mode_set = ['OFFAXIS',
                            'PARALLEL',
                            'TOE'
    ]
    
    min_coords = None
    max_coords = None
    scene_center = None
    scene_size = None
    camera_object_1 = None
    old_image_resolution_x = None
    old_image_resolution_y = None 
    main_camera = None
    render = None
    target_directory = None
    target_directory_images = None 
    target_directory_depth_map = None
    
    def get_objects(self, context) -> list[bpy.types.Object]:
        return [ob for ob in context.scene.objects if ob.type == 'MESH']
    
    def __init__(self, context, props: dict):
        
        self.record_num = props['record_num']
        self.no_select_folder = props['no_select_folder']
        self.source_path = props['source_path']
        self.target_path = props['target_path']
        self.image_resolution_y = props['image_resolution_y']
        self.image_resolution_x = props['image_resolution_x']
        self.dataset_name = props['dataset_name']
        self.convergence_distance = props['convergence_distance']
        self.interocular_distance = props['interocular_distance']
        self.convergence_mode = props['convergence_mode']
        self.camera_properties = props['camera_properties']
        self.add_vertices = props['add_vertices']
        self.camera_variant = props['camera_variant']
        self.addon_name = props['addon_name']
        
        self.set_initial_values(context)
        self.initial_settings(context)
        
        
    def initial_settings(self, context):    
        self.target_directory, self.target_directory_images, self.target_directory_depth_map = file_utilities.create_directories(self.target_path, 
                                                                                                                                 self.dataset_name)
        txt_file_path = file_utilities.create_txt_file(self.target_directory, 
                                                       self.dataset_name)
        
        resourses_path = os.path.join(addon_folder(self.addon_name), 'resourses')
        file_utilities.add_file(self.target_directory, 
                                resourses_path, 
                                "README.md")
        
        
    def set_initial_values(self, context):
        
        objects = self.get_objects(context)
        
        render = context.scene.render
        self.old_image_resolution_x = render.resolution_x
        self.old_image_resolution_y = render.resolution_y 
        self.main_camera = context.scene.camera
        
        camera_data_1 = bpy.data.cameras.new(name='Camera.00000.001')
        self.camera_object_1 = bpy.data.objects.new('Camera.00000.001', camera_data_1)
        context.scene.collection.objects.link(self.camera_object_1)
        context.scene.camera = self.camera_object_1
        camera = context.scene.camera
        
        self.min_coords, self.max_coords = geometric_utilities.find_scene_bounds(objects)
        self.scene_size = geometric_utilities.find_scene_size(objects)
        self.scene_center = geometric_utilities.find_scene_center(objects)
        
        render.resolution_x = self.image_resolution_x
        render.resolution_y = self.image_resolution_y
        
        if self.camera_properties:
            context.scene.camera.data.stereo.convergence_distance = self.convergence_distance
            context.scene.camera.data.stereo.convergence_mode = self.convergence_mode
            context.scene.camera.data.stereo.interocular_distance = self.interocular_distance
        else:
            random.seed(42)
            context.scene.camera.data.stereo.convergence_distance = random.uniform(1e-5, 4)
            context.scene.camera.data.stereo.interocular_distance = random.uniform(0, 4)
            context.scene.camera.data.stereo.convergence_mode = random.sample(self.convergence_mode_set, k=1)[0]
            
    
    def set_camera(self, context, record_num):
        i = record_num 
        random.seed(42 + i)
        # Установка случайного расстояния от сцены
        distance = [random.uniform(self.scene_size[i], self.scene_size[i] * 2.5) for i in range(3)]

        context.scene.camera.location = (
            self.min_coords[0] - distance[0] if random.randint(0, 1) else self.max_coords[0] + distance[0],
            self.min_coords[1] - distance[1] if random.randint(0, 1) else self.max_coords[1] + distance[1],
            self.min_coords[2] - distance[2] if random.randint(0, 1) else self.max_coords[2] + distance[2]
        )
                
        # Ориентация камеры в сторону центра сцены с небольшим отклонением
        #deviation = [random.uniform(-self.scene_size[i]*0.3, self.scene_size[i]*0.3) for i in range(3)]
        #camera_direction = mathutils.Vector(context.scene.camera.location) - mathutils.Vector(self.scene_center) + mathutils.Vector(deviation)
        camera_direction = mathutils.Vector(context.scene.camera.location) - mathutils.Vector(self.scene_center) 
        rot_quat = camera_direction.to_track_quat('Z', 'Y')
        context.scene.camera.rotation_euler = rot_quat.to_euler()
    
    def generate_images(self, context, camera_mode, record_num, scene_num):
        self.set_camera(context, record_num)
        
        if self.render == None:
            self.render = Render(camera_mode)
        
        self.render.get_images(context, 
                          self.convergence_mode, 
                          self.convergence_distance, 
                          self.interocular_distance, 
                          self.dataset_name, 
                          self.target_path, 
                          self.target_directory_images, 
                          record_num, scene_num)
                          
        self.render.get_depth_map(context, 
                                  self.dataset_name, 
                                  self.target_path, 
                                  self.target_directory_depth_map, 
                                  self.min_coords, self.max_coords, 
                                  record_num, scene_num)
         
        objects = self.get_objects(context) 
        camera = bpy.context.scene.camera                       
        txt_file_path = os.path.join(self.target_path, self.dataset_name, str(self.dataset_name + '.txt'))
        try:
            txt_file = open(txt_file_path, "a")
            txt_file.write(str(camera.location.x) + ' ' + str(camera.location.y) + ' ' + str(camera.location.z) + "\n")
            txt_file.write(str(camera.rotation_euler.x) + ' ' + str(camera.rotation_euler.y) + ' ' + str(camera.rotation_euler.z) + "\n")
            if self.add_vertices:
                for ob in objects:
                    vertices = ''
                    for vert in ob.data.vertices.values():
                        x_cord = vert.co.x
                        y_cord = vert.co.y
                        z_cord = vert.co.z
                        vertices = vertices + str(x_cord) + ' ' + str(y_cord) + ' ' + str(z_cord) + ' '
                    vertices = vertices + "\n"
                    txt_file.write(vertices)
        finally:
            txt_file.close()
            
    def return_settings(self, context):
    
        bpy.data.objects.remove(self.camera_object_1, do_unlink=True)
        render = context.scene.render
        #context.scene.node_tree = old_tree
        #context.scene.node_tree.tree.links = old_links    
        
        render.resolution_x = self.old_image_resolution_x
        render.resolution_y = self.old_image_resolution_y
        
        context.scene.camera = self.main_camera
        
        
        
class Render():
    
    camera_mode = None
    
    def __init__(self, camera_mode):
        
        self.camera_mode = camera_mode
    
    
    def get_images(self, context, convergence_mode, convergence_distance, interocular_distance, dataset_name, target_path, target_directory_images, record_num, scene_num):
        old_views_format = context.scene.render.image_settings.views_format
        old_use_multiview = context.scene.render.use_multiview 
        old_display_mode = context.scene.render.image_settings.stereo_3d_format.display_mode
        old_convergence_distance = context.scene.camera.data.stereo.convergence_distance
        old_convergence_mode = context.scene.camera.data.stereo.convergence_mode
        old_interocular_distance = context.scene.camera.data.stereo.interocular_distance
        
        context.scene.render.use_multiview = True
        context.scene.render.image_settings.views_format = 'STEREO_3D'
        context.scene.render.image_settings.stereo_3d_format.display_mode = 'SIDEBYSIDE'
        
        file_name = dataset_name + '_' + '{:04}'.format(scene_num+1) + '_' + '{:05}'.format(record_num+1) + '_cam'
        filepath = os.path.join(target_directory_images, file_name)
        context.scene.render.filepath = filepath
        bpy.ops.render.render( write_still=True )
        image = Image.open(filepath + '.png')
        file_name_l = file_name + '_left.png'
        filepath_l = os.path.join(target_directory_images, file_name_l)
        image_left = image.crop((0, 0, image.size[0]/2, image.size[1]))
        image_left.save(filepath_l)
        file_name_r = file_name + '_right.png'
        filepath_r = os.path.join(target_directory_images, file_name_r)
        image_right = image.crop((image.size[0]/2, 0, image.size[0], image.size[1]))
        image_right.save(filepath_r)
        os.remove(filepath  + '.png')
        
        txt_file_path = os.path.join(target_path, dataset_name, str(dataset_name + '.txt'))
        try:
            txt_file = open(txt_file_path, "a")
            txt_file.write(file_name_l + "\n")
            txt_file.write(file_name_r + "\n")
            txt_file.write(str(convergence_mode) + ' ' + str(convergence_distance) + ' ' + str(interocular_distance) + "\n")
            
        finally:
            txt_file.close()
        
        context.scene.render.image_settings.stereo_3d_format.display_mode = old_display_mode
        context.scene.render.image_settings.views_format = old_views_format
        context.scene.render.use_multiview = old_use_multiview 
        context.scene.camera.data.stereo.convergence_distance = old_convergence_distance
        context.scene.camera.data.stereo.convergence_mode = old_convergence_mode
        context.scene.camera.data.stereo.interocular_distance = old_interocular_distance

    def get_depth_map(self, context, dataset_name, target_path, target_directory_depth_map, min_coords, max_coords, record_num, scene_num):
        views_format = context.scene.render.image_settings.views_format
        display_mode = context.scene.render.image_settings.stereo_3d_format.display_mode
        use_multiview = context.scene.render.use_multiview 
        use_pass_z = bpy.context.scene.view_layers[0].use_pass_z   
        use_nodes = context.scene.use_nodes
        old_tree = context.scene.node_tree    
        
        context.scene.render.use_multiview = False
        context.scene.render.image_settings.views_format = 'INDIVIDUAL'
        context.scene.render.image_settings.stereo_3d_format.display_mode = 'ANAGLYPH'
        bpy.context.scene.view_layers[0].use_pass_z = True    
        bpy.context.scene.use_nodes = True
        tree = bpy.context.scene.node_tree
            
        for n in tree.nodes:
            tree.nodes.remove(n)
            
        links = tree.links
                
        rl = tree.nodes.new('CompositorNodeRLayers')
        map = tree.nodes.new(type="CompositorNodeMapRange")
        vertexes = geometric_utilities.find_remaining_vertices(min_coords, max_coords)
        min_distance = geometric_utilities.min_distance_to_parallelepiped(bpy.context.scene.camera.location, vertexes)
        max_distance = geometric_utilities.max_distance_to_parallelepiped(bpy.context.scene.camera.location, vertexes)
        map.inputs['From Min'].default_value = min_distance
        map.inputs['From Max'].default_value = max_distance
        map.inputs['To Min'].default_value = 0
        map.inputs['To Max'].default_value = 1
        links.new(rl.outputs[2], map.inputs[0])
        invert = tree.nodes.new(type="CompositorNodeInvert")
        links.new(map.outputs[0], invert.inputs[1])
            
        depthViewer = tree.nodes.new(type="CompositorNodeViewer")
        links.new(invert.outputs[0], depthViewer.inputs[0])

        links.new(rl.outputs[1], depthViewer.inputs[1])
        file_name = dataset_name + '_' + '{:04}'.format(scene_num+1) + '_' + '{:05}'.format(record_num+1) + '_depthmap'
        filepath = os.path.join(target_directory_depth_map, file_name)
        fileOutput = tree.nodes.new(type="CompositorNodeOutputFile")
        fileOutput.base_path = target_directory_depth_map
        fileOutput.file_slots[0].path = file_name + '#'
        links.new(invert.outputs[0], fileOutput.inputs[0])
        bpy.ops.render.render()
        find_file = [f for f in os.listdir(target_directory_depth_map) if os.path.isfile(os.path.join(target_directory_depth_map, f)) and file_name in f]
        find_file_path = os.path.join(target_directory_depth_map, find_file[0])
        result_file_name = find_file[0][:-5] + find_file[0][-4:]
        result_file_path = os.path.join(target_directory_depth_map, result_file_name)
        os.rename(find_file_path, result_file_path)
        try:
            os.remove(find_file_path[:-7]+'1_L.png')
            os.remove(find_file_path[:-7]+'1_R.png')
        except FileNotFoundError:
            None
        
        txt_file_path = os.path.join(target_path, dataset_name, str(dataset_name + '.txt'))
        try:
            txt_file = open(txt_file_path, "a")
            txt_file.write(result_file_name + '\n')
        finally:
            txt_file.close()
        
        context.scene.use_nodes = use_nodes
        bpy.context.scene.view_layers[0].use_pass_z = use_pass_z
        context.scene.render.image_settings.stereo_3d_format.display_mode = display_mode
        context.scene.render.image_settings.views_format = views_format
        context.scene.render.use_multiview = use_multiview

        