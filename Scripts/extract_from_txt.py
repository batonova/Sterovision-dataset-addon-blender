# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import filedialog

def data_extraction(lines):
    
    left_camera_images = []
    right_camera_images = []
    camera_characteristics = []
    depth_map_images = []
    camera_coordinates = []
    camera_rotations = []
        
    # Process the lines
    for i in range(0, len(lines), 6):
       # Extract left and right camera images
       left_camera_images.append(lines[i].strip())
       right_camera_images.append(lines[i+1].strip())
        
       # Extract camera characteristics
       convergence_mode, convergence_distance, interocular_distance = lines[i+2].strip().split()
       camera_characteristics.append({
           'convergence_mode': convergence_mode,
           'convergence_distance': float(convergence_distance),
           'interocular_distance': float(interocular_distance)
       })
        
       # Extract depth map image
       depth_map_images.append(lines[i+3].strip())
        
       # Extract camera coordinates
       camera_coordinates.append(list(map(float, lines[i+4].strip().split())))
        
       # Extract camera rotations
       camera_rotations.append(list(map(float, lines[i+5].strip().split())))
    
    return left_camera_images, right_camera_images, camera_characteristics, depth_map_images, camera_coordinates, camera_rotations

def execute_data_extraction():
    # Open file dialog to select a text file
    file_path = filedialog.askopenfilename(filetypes=[('Text Files', '*.txt')])
    
    # Execute the data extraction code with the selected file
    if file_path:
        
        
        # Open the file for reading
        with open(file_path, 'r') as file:
            lines = file.readlines()
        
        left_camera_images, right_camera_images, camera_characteristics, depth_map_images, camera_coordinates, camera_rotations = data_extraction(lines)
        
        # Print the extracted data
        print("Left Camera Images:", left_camera_images)
        print("Right Camera Images:", right_camera_images)
        print("Camera Characteristics:", camera_characteristics)
        print("Depth Map Images:", depth_map_images)
        print("Camera Coordinates:", camera_coordinates)
        print("Camera Rotations:", camera_rotations)


if __name__ == '__main__'
    # Create the main window
    window = tk.Tk()
    window.title("Data Extraction")
    window.geometry("300x100")
    
    # Checkbox variable
    check_var = tk.IntVar()
    
    # Checkbox
    checkbox = tk.Checkbutton(window, text="Enable", variable=check_var)
    checkbox.pack(pady=10)
    
    # Button
    button = tk.Button(window, text="Select File", command=execute_data_extraction)
    button.pack()
    
    # Start the main event loop
    window.mainloop()