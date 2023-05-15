
bl_info = {
    "name": "Dataset generation",
    "author": "Oksana Batonova, Elena Batrakova",
    "version": (1, 3, 2),
    "blender": (3, 3, 1),
    "location": "3D View > UI > Datasets",
    "description": ("Create a dataset from images from stereo cameras and a depth map"),
    "warning": "",
    "doc_url": "",
    "category": "3D View",
}

import sys
import os
import importlib
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
    
def check_module(module_name):
    
    try:
        module_spec = importlib.util.find_spec(module_name)
        return module_spec
    except ModuleNotFoundError:
        print('Module: {} not found'.format(module_name))
        return None
    
def install_module(module_name):
    
    try:
        python_exe = os.path.join(sys.prefix, 'bin', 'python.exe')
        subprocess.call([python_exe, "-m", "ensurepip"])
        subprocess.call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.call([python_exe, "-m", "pip", "install", module_name])
        
        return 1
        
    except OSError as e:
        print("Execution failed:", e, file=sys.stderr)
        
        return None  

def import_module(module_name):
    
    module_spec = check_module(module_name)
    
    if not module_spec:
        installed = install_module(module_name)
        
        if not installed:
            print('Module: {} not found'.format(module_name))
            
            return None
        
        module_spec = check_module(module_name)
    
    if module_spec:
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        print('Module: {} imported'.format(module_name))
        return module
    
    return None

add_modules(bl_info['name'], 'lib')
add_modules(bl_info['name'], 'scripts')

if "bpy" in locals():
    importlib.reload(geometric_utilities)
    importlib.reload(file_utilities)
    importlib.reload(dataset_generation)
else:
    import geometric_utilities, file_utilities, dataset_generation

import_module('PIL')

from PIL import Image

import subprocess
import random
import re
import time

import numpy as np
import bpy
from typing import List
from bpy.types import Operator, Panel, PropertyGroup, Object, Scene, NodeOutputFileSlotFile
from bpy.utils import register_class, unregister_class
from bpy.props import BoolProperty, IntProperty, StringProperty, PointerProperty, FloatProperty, EnumProperty, CollectionProperty


class DatasetProps(PropertyGroup):
    no_select_folder : BoolProperty(
        name = 'Use only this scene',
        description = 'Generate records only from this scene or select a folder with files',
        default = True
    )
    record_num : IntProperty(
        name = 'Number of records',
        description = 'Enter the number of records to be generated',
        default = 5,
        min = 1,
        max = 10000,
        soft_max = 100,
    )
    source_path : StringProperty(
        name = 'Source Folder',
        description = 'Select the resource folder for uploading scene files',
        subtype = 'DIR_PATH'
    )
    target_path : StringProperty(
        name = 'Target Folder',
        description = 'Select the destination folder to save the data to',
        subtype = 'DIR_PATH'
    )
    image_resolution_x : IntProperty(
        name = 'Image Weight',
        description = 'Enter the weight of images',
        default = 1920,
        min = 1,
        max = 50000,
        soft_max = 5000,
        subtype = 'PIXEL'
    )
    image_resolution_y : IntProperty(
        name = 'Image Height',
        description = 'Enter the height of images',
        default = 1080,
        min = 1,
        max = 50000,
        soft_max = 5000,
        subtype = 'PIXEL'
    )
    dataset_name : StringProperty(
        name = 'Name',
        description = 'Select the name of a dataset',
        default = 'Stereovision',
        maxlen = 30
    )
    convergence_distance : FloatProperty(
        name = 'Convergence Distance',
        default = 1.95,
        min = 1e-5
    )
    convergence_mode : EnumProperty(
        name = 'Convergence Mode',
        default = 'OFFAXIS',
        items = [ ('OFFAXIS', 'Off-Axis', ''),
                  ('PARALLEL', 'Parallel', ''),
                  ('TOE', 'Toe-in', ''),
                ]
    )
    interocular_distance : FloatProperty(
        name = 'Interocular Distance', 
        default = 0.065,
        min = 0
    )
    camera_properties : BoolProperty(
        name = 'Random',
        default = False
    )
    camera_variant : EnumProperty(
        name = 'Camera',
        default = 'STEREOVISION',
        items = [ ('STEREOVISION', 'Stereovision', ''),
                 # ('MONOCULAR', 'Monocular', ''),
                ]
    )
    add_vertices : BoolProperty(
        name = 'Add vertices',
        default = False
    )


class DatasetGeneration(Operator):
    bl_idname = 'object.dataset_generation'
    bl_label = 'Dataset Generation'
    record_num = None
    no_select_folder = None
    source_path = None
    target_path = None
    image_resolution_y = None
    image_resolution_x = None
    dataset_name = None
    convergence_mode = None
    convergence_distance = None
    interocular_distance = None
    camera_properties = None
    add_vertices = None
    camera_variant = None
    
    convergence_mode_set = ['OFFAXIS',
                            'PARALLEL',
                            'TOE'
    ]
      
    def structure(self, context):
        props = context.scene.datagenerate
        self.record_num = props.record_num
        self.no_select_folder = props.no_select_folder
        self.source_path = props.source_path
        self.target_path = props.target_path
        self.image_resolution_y = props.image_resolution_y
        self.image_resolution_x = props.image_resolution_x
        self.dataset_name = props.dataset_name
        self.convergence_distance  = props.convergence_distance
        self.interocular_distance = props.interocular_distance
        self.convergence_mode = props.convergence_mode
        self.camera_properties = props.camera_properties
        self.add_vertices = props.add_vertices
        self.camera_variant = props.camera_variant

    def generate(self, context):
        
        scene = None
        
        if self.no_select_folder:
            
            scene = dataset_generation.Scene(context,
                                  {'record_num': self.record_num,
                                   'no_select_folder': self.no_select_folder,
                                   'source_path': self.source_path,
                                   'target_path': self.target_path,
                                   'image_resolution_y': self.image_resolution_y,
                                   'image_resolution_x': self.image_resolution_x,
                                   'dataset_name': self.dataset_name,
                                   'convergence_distance': self.convergence_distance,
                                   'interocular_distance': self.interocular_distance,
                                   'convergence_mode': self.convergence_mode,
                                   'camera_properties': self.camera_properties,
                                   'add_vertices': self.add_vertices,
                                   'camera_variant': self.camera_variant,
                                   'addon_name': bl_info['name']
                                    }
            )
            
            rc_num = str(self.record_num)
            print("Number of records: " + rc_num +".")
            print("_________________________")
            
            for i in range(self.record_num):
                start = time.perf_counter()
                
                scene.generate_images(context, 
                                      self.camera_variant,
                                      i, 0)   
                end = time.perf_counter()
                print("Record "+ str(i+1)+"/"+ rc_num + ". Time: "+str(end-start)+" sec.")    
                                      
            scene.return_settings(context)    
         
        else:
            models_path = []
            for x in os.listdir(self.source_path):
                if x.endswith(".blend"):
                    models_path.append(x)
            sc_num = str(len(models_path))
            print("Number of scenes: " + sc_num+".")
            print("_________________________")
            i = 0
            for model_file in models_path:
                start = time.perf_counter()
                script_file_path = os.path.join(addon_folder(bl_info['name']), 'scripts', 'record_generation.py')
                model_file_path = os.path.join(self.source_path, model_file)
                blender_exe = bpy.app.binary_path
                f = subprocess.call([blender_exe, model_file_path, "-b",  "-P", script_file_path, 
                                     self.dataset_name, 
                                     self.target_path, 
                                     str(self.image_resolution_x), 
                                     str(self.image_resolution_y), 
                                     str(self.camera_properties), 
                                     str(self.convergence_distance), 
                                     self.convergence_mode, 
                                     str(self.interocular_distance), 
                                     str(self.record_num), 
                                     str(self.add_vertices), 
                                     str(self.camera_variant),
                                     str(i),
                                     bl_info['name']])
                       
                end = time.perf_counter()
                print("Scene "+ str(i+1)+"/"+sc_num + ". Time: "+str(end-start)+" sec.")
                i += 1
    
    
    def execute(self, context) -> set:
        self.structure(context)
        self.generate(context)
        return {'FINISHED'}
    
class OBJECT_PT_DatasetGenerationPanel(Panel):
    bl_label = 'Generation'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Datasets'
       
    def check_availability(self, context):
        props = context.scene.datagenerate
        if props.dataset_name and props.target_path:
            if props.no_select_folder or props.source_path:
                return True
        return False  
    
    def draw_header(self, context):
        layout = self.layout
        layout.label(text="Dataset")
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.datagenerate
        
        row = layout.row()
        row.prop(props, 'no_select_folder')
        
        col = layout.column()
        box = col.box()
        box_add = box.box()
        box_add.prop(props, 'source_path')
        box.prop(props, 'dataset_name')
        box.prop(props, 'record_num')
        box.prop(props, 'target_path')
        
        box_image = box.box()
        box_image.label(text="Image resolution")
        box_image.prop(props, 'image_resolution_x')
        box_image.prop(props, 'image_resolution_y')
        box.prop(props, 'camera_variant')
        
        box_camera = box.box()
        
        box_camera.label(text="Camera properties")
        
        box_camera1 = box_camera.box()
        box_camera1.prop(props, 'convergence_distance')
        box_camera.prop(props, 'convergence_mode')
        box_camera1.prop(props, 'interocular_distance')
        box_camera.prop(props, 'camera_properties')
        box.prop(props, 'add_vertices')
        box_camera.enabled = not props.camera_properties
        
        box_add.enabled = not props.no_select_folder
        box_camera.enabled = props.camera_variant == "STEREOVISION"
        row_but = layout.row()
        row_but.operator('object.dataset_generation', text='Generate')
        row_but.enabled = self.check_availability(context)
        
    
classes = [
    DatasetProps,
    DatasetGeneration,
    OBJECT_PT_DatasetGenerationPanel
]

def register(): 
    for cl in classes:
        register_class(cl)
    bpy.types.Scene.datagenerate = PointerProperty(type = DatasetProps)

def unregister():
    for cl in reversed(classes):
        unregister_class(cl)
        
if __name__ == '__main__':

    register()
    