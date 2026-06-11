import os
import shutil
import sys

def get_subfolders(parent_folder):
    return [os.path.join(parent_folder, subfolder) for subfolder in os.listdir(parent_folder) if os.path.isdir(os.path.join(parent_folder, subfolder))]

def combine_folders(parent_folder, output_folder):
    input_folders = get_subfolders(parent_folder)
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for folder in input_folders:
        if not os.path.exists(folder):
            print(f"Warning: {folder} does not exist and will be skipped.")
            continue
        
        for root, _, files in os.walk(folder):
            for file in files:
                src_path = os.path.join(root, file)
                dest_path = os.path.join(output_folder, file)
                
                # Rename file if a conflict exists
                counter = 1
                while os.path.exists(dest_path):
                    name, ext = os.path.splitext(file)
                    dest_path = os.path.join(output_folder, f"{name}_{counter}{ext}")
                    counter += 1
                
                shutil.copy2(src_path, dest_path)
                print(f"Copied {src_path} -> {dest_path}")
        
        # Remove the subfolder after copying its contents
        shutil.rmtree(folder)
        print(f"Deleted folder: {folder}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python combine_folders.py <parent_folder> <output_folder>")
        sys.exit(1)
    
    parent_folder = sys.argv[1]
    output_folder = sys.argv[2]
    
    combine_folders(parent_folder, output_folder)
