
import trimesh
import os


def convert_glb_to_obj(glb_filename, obj_filename):
    mesh = trimesh.load_mesh(glb_filename)
    mesh.export(obj_filename, file_type='obj')


input_directory = r'C:\Users\enzoc\Downloads\ExtendedMatrix-EM1.4dev\ExtendedMatrix-EM1.4dev\06_EMjson\EM3dnodes'
output_directory = r'C:\Users\enzoc\Downloads\ExtendedMatrix-EM1.4dev\ExtendedMatrix-EM1.4dev\06_EMjson\EM3dnodes'


os.makedirs(output_directory, exist_ok=True)

for filename in os.listdir(input_directory):
    if filename.lower().endswith('.glb'):
        glb_filename = os.path.join(input_directory, filename)
        obj_filename = os.path.join(output_directory, os.path.splitext(filename)[0] + '.obj')

        if not os.path.exists(obj_filename):
            convert_glb_to_obj(glb_filename, obj_filename)
        else:
            print(f"{obj_filename} already exists. Skipping conversion.")
