import sys
import os
import bpy
import addon_utils

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

if __name__ == '__main__': 

    dataset_name = sys.argv[5]
    target_path = sys.argv[6]
    image_resolution_x = int(sys.argv[7])
    image_resolution_y = int(sys.argv[8])
    camera_properties = sys.argv[9]
    convergence_distance = float(sys.argv[10])
    convergence_mode = sys.argv[11]
    interocular_distance = float(sys.argv[12])
    record_num = int(sys.argv[13])
    add_vertices = 1 if sys.argv[14] == 'True' else 0
    camera_variant = sys.argv[15]
    scene_num = int(sys.argv[16])
    addon_name = sys.argv[17]
    
    add_modules(addon_name, 'scripts')
    
    import dataset_generation
    
    context = bpy.context
    
    scene = dataset_generation.Scene(context,
                          {'record_num': record_num,
                           'no_select_folder': 0,
                           'source_path': '',
                           'target_path': target_path,
                           'image_resolution_y': image_resolution_y,
                           'image_resolution_x': image_resolution_x,
                           'dataset_name': dataset_name,
                           'convergence_distance': convergence_distance,
                           'interocular_distance': interocular_distance,
                           'convergence_mode': convergence_mode,
                           'camera_properties': camera_properties,
                           'add_vertices': add_vertices,
                           'camera_variant': camera_variant,
                           'addon_name': addon_name
                                    }
            )
        
            
    for i in range(record_num):
                
        scene.generate_images(context, 
                              camera_variant,
                               i, scene_num)       
                                      
    scene.return_settings(context)
    