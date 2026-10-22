#%%
import shutil
import os
import re

# Function to find and copy all downloaded json.txt files to the project folder's json folder
def copy_json_files_to_project_folder():
    downloads_folder = os.path.expanduser('~') + r'\\Downloads'  # Path to Downloads folder
    project_folder = r"C:\Lakmal-Code\location_trace\Location_Trace"  # Path to project folder
    json_folder = os.path.join(project_folder, 'json')  # Path to json folder in the project

    # Create 'json' folder if it doesn't exist
    os.makedirs(json_folder, exist_ok=True)

    # Get all matching "json*.txt" files in the Downloads folder
    json_files = [f for f in os.listdir(downloads_folder) if re.match(r"json(?: \(\d+\))?\.txt$", f)]

    if not json_files:
        print("❌ No json.txt files found in Downloads folder")
        return

    # Get the full path of all json files
    json_files = [os.path.join(downloads_folder, f) for f in json_files]

    # Copy each json.txt file to the project folder's json folder
    for json_file in json_files:
        try:
            # Copy the file to the 'json' folder inside the project folder
            destination_path = os.path.join(json_folder, os.path.basename(json_file))
            shutil.copy(json_file, destination_path)
            print(f"✅ File '{os.path.basename(json_file)}' copied to {destination_path}")
        except Exception as e:
            print(f"❌ Error copying file {json_file}: {e}")

# Call the function to copy all json.txt files to the project folder's json folder
copy_json_files_to_project_folder()
