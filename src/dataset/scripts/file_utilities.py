import os
from shutil import copyfile

def create_directories(target_path, dataset_name):
    
    target_directory = os.path.join(target_path, dataset_name) 
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)
    target_directory_images = os.path.join(target_directory, 'images')
    if not os.path.exists(target_directory_images):
        os.makedirs(target_directory_images)
    target_directory_depth_map = os.path.join(target_directory, 'depthmap')
    if not os.path.exists(target_directory_depth_map):
        os.makedirs(target_directory_depth_map)
        
    return target_directory, target_directory_images, target_directory_depth_map

def create_txt_file(target_directory, dataset_name):
    
    txt_file_path = os.path.join(target_directory, str(dataset_name + '.txt'))
    try:
        txt_file = open(txt_file_path, "a")
    finally:
        txt_file.close()
    
    return txt_file_path

def add_file(target_directory, source_directory, file_name):

    readme_source = os.path.join(source_directory, file_name)
    readme_target = os.path.join(target_directory, file_name)
    copyfile(readme_source, readme_target)
    
    return readme_target