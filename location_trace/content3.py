
#%%
import json
import os
import re

# Define file paths
project_folder = r"C:\Lakmal-Code\location_trace\Location_Trace\json"
output_file = os.path.join(project_folder, "extracted_coordinates.json")

def extract_first_coordinates_reverse():
    try:
        # Get all json.txt files sorted in natural order (json.txt, json (1).txt, json (2).txt, ...)
        json_files = sorted(
            [f for f in os.listdir(project_folder) if re.match(r"json(?: \(\d+\))?\.txt$", f)],
            key=lambda x: int(re.search(r"\((\d+)\)", x).group(1)) if re.search(r"\((\d+)\)", x) else 0,
            reverse=True  # Reverse order (last copied file first)
        )

        if not json_files:
            print("❌ No json.txt files found in the json folder")
            return

        extracted_coordinates = []  # Store extracted coordinates in order

        # Process each file (last file first)
        for json_file in json_files:
            input_file = os.path.join(project_folder, json_file)

            # Read file content
            with open(input_file, "r", encoding="utf-8") as file:
                raw_data = file.read()

            # Remove unwanted characters at the beginning (like )]}')
            clean_data = re.sub(r"^\)\]\}'\s*", "", raw_data)

            # Convert text to JSON
            try:
                data = json.loads(clean_data)
            except json.JSONDecodeError as e:
                print(f"❌ Error decoding JSON in file {json_file}: {e}")
                continue  # Skip this file

            # Extract only the **first** valid latitude & longitude from this file
            extracted = False
            for item in data:
                if isinstance(item, list):
                    for sub_item in item:
                        if isinstance(sub_item, list) and len(sub_item) > 1 and isinstance(sub_item[1], list):
                            latitude = sub_item[1][1][2]   # Latitude
                            longitude = sub_item[1][1][1]  # Longitude

                            coordinates = {"latitude": latitude, "longitude": longitude}

                            if coordinates not in extracted_coordinates:
                                extracted_coordinates.append(coordinates)
                                extracted = True
                            break  # Stop after finding the first valid coordinate
                    if extracted:
                        break

        # Check if any coordinates were extracted
        if not extracted_coordinates:
            print("⚠️ No valid coordinates extracted!")
            return

        # Save extracted coordinates to a JSON file
        with open(output_file, "w", encoding="utf-8") as out_file:
            json.dump(extracted_coordinates, out_file, indent=4)

        print("✅ Extracted coordinates saved successfully in reverse order!")

    except FileNotFoundError:
        print("❌ json.txt file not found in the json folder")
    except Exception as e:
        print(f"❌ Error: {e}")

# Run the function
extract_first_coordinates_reverse()




# #%%
# import json
# import os
# import re

# # Define file paths
# project_folder = r"C:\Lakmal-Code\location_trace\Location_Trace\json"
# output_file = os.path.join(project_folder, "extracted_coordinates.json")

# def extract_unique_coordinates_reverse():
#     try:
#         # Get all json.txt files in the json folder, sorted in reverse order (latest first)
#         json_files = sorted(
#             [f for f in os.listdir(project_folder) if re.match(r"json(?: \(\d+\))?\.txt$", f)],
#             key=lambda x: os.path.getmtime(os.path.join(project_folder, x)),
#             reverse=True  # Newest file first
#         )

#         if not json_files:
#             print("❌ No json.txt files found in the json folder")
#             return

#         unique_coordinates = []  # To store extracted coordinates

#         # Process files in reverse order (newest file first)
#         for json_file in json_files:
#             input_file = os.path.join(project_folder, json_file)

#             # Read the input file
#             with open(input_file, "r", encoding="utf-8") as file:
#                 raw_data = file.read()

#             # Remove unwanted characters at the beginning (like )]}')
#             clean_data = re.sub(r"^\)\]\}'\s*", "", raw_data)

#             # Convert the cleaned text into JSON format
#             try:
#                 data = json.loads(clean_data)
#             except json.JSONDecodeError as e:
#                 print(f"❌ Error decoding JSON in file {json_file}: {e}")
#                 continue  # Skip this file and move to the next one

#             # Extract only the **first valid latitude & longitude** from the file
#             extracted = False
#             for item in data:
#                 if isinstance(item, list):
#                     for sub_item in item:
#                         if isinstance(sub_item, list) and len(sub_item) > 1 and isinstance(sub_item[1], list):
#                             # Extract latitude and longitude
#                             longitude = sub_item[1][1][1]  # Longitude is at index 1
#                             latitude = sub_item[1][1][2]   # Latitude is at index 2
                            
#                             coordinates = {"latitude": latitude, "longitude": longitude}

#                             # Add only if it's not a duplicate
#                             if coordinates not in unique_coordinates:
#                                 unique_coordinates.append(coordinates)
#                                 extracted = True
#                             break  # Stop after finding the first valid coordinate
#                     if extracted:
#                         break

#         # **Reverse only the final extracted list** so newest data is at the top
#         unique_coordinates.reverse()

#         # Check if any coordinates were extracted
#         if not unique_coordinates:
#             print("⚠️ No valid coordinates extracted!")
#             return

#         # Save extracted coordinates to a new JSON file
#         with open(output_file, "w", encoding="utf-8") as out_file:
#             json.dump(unique_coordinates, out_file, indent=4)

#         print("✅ Extracted coordinates saved successfully!")

#     except FileNotFoundError:
#         print("❌ json.txt file not found in the json folder")
#     except Exception as e:
#         print(f"❌ Error: {e}")

# # Run the function
# extract_unique_coordinates_reverse()








# #%%
# import json
# import os
# import re

# # Define file paths
# project_folder = r"C:\Lakmal-Code\location_trace\Location_Trace\json"
# output_file = os.path.join(project_folder, "extracted_coordinates.json")

# def extract_unique_coordinates_reverse():
#     try:
#         # Get all json.txt files in the json folder
#         json_files = [f for f in os.listdir(project_folder) if re.match(r"json(?: \(\d+\))?\.txt$", f)]

#         if not json_files:
#             print("❌ No json.txt files found in the json folder")
#             return

#         unique_coordinates = []  # To store extracted coordinates

#         # Process each json.txt file in reverse order (last copied file first)
#         for json_file in reversed(json_files):
#             input_file = os.path.join(project_folder, json_file)

#             # Read the input file
#             with open(input_file, "r", encoding="utf-8") as file:
#                 raw_data = file.read()

#             # Remove unwanted characters at the beginning (like )]}')
#             clean_data = re.sub(r"^\)\]\}'\s*", "", raw_data)

#             # Convert the cleaned text into JSON format
#             try:
#                 data = json.loads(clean_data)
#             except json.JSONDecodeError as e:
#                 print(f"❌ Error decoding JSON in file {json_file}: {e}")
#                 continue  # Skip this file and move to the next one

#             # Extract only the **first valid latitude & longitude** from the file
#             extracted = False
#             for item in data:
#                 if isinstance(item, list):
#                     for sub_item in item:
#                         if isinstance(sub_item, list) and len(sub_item) > 1 and isinstance(sub_item[1], list):
#                             # Extract latitude and longitude
#                             longitude = sub_item[1][1][1]  # Longitude is at index 1
#                             latitude = sub_item[1][1][2]   # Latitude is at index 2
                            
#                             coordinates = {"latitude": latitude, "longitude": longitude}

#                             # Add only if it's not a duplicate
#                             if coordinates not in unique_coordinates:
#                                 unique_coordinates.append(coordinates)
#                                 extracted = True
#                             break  # Stop after finding the first valid coordinate
#                     if extracted:
#                         break

#         # Reverse the order of extracted coordinates
#         unique_coordinates.reverse()

#         # Check if any coordinates were extracted
#         if not unique_coordinates:
#             print("⚠️ No valid coordinates extracted!")
#             return

#         # Save extracted coordinates to a new JSON file
#         with open(output_file, "w", encoding="utf-8") as out_file:
#             json.dump(unique_coordinates, out_file, indent=4)

#         print("✅ Extracted coordinates saved successfully!")

#     except FileNotFoundError:
#         print("❌ json.txt file not found in the json folder")
#     except Exception as e:
#         print(f"❌ Error: {e}")

# # Run the function
# extract_unique_coordinates_reverse()






# #%%
# import json
# import os
# import re

# # Define file paths
# project_folder = r"C:\Lakmal-Code\location_trace\Location_Trace\json"
# input_file = os.path.join(project_folder, "json.txt")
# output_file = os.path.join(project_folder, "extracted_coordinates.json")

# def extract_first_coordinates():
#     try:
#         # Read the input file
#         with open(input_file, "r", encoding="utf-8") as file:
#             raw_data = file.read()

#         # Remove unwanted characters at the beginning (like )]}')
#         clean_data = re.sub(r"^\)\]\}'\s*", "", raw_data)  

#         # Convert the cleaned text into JSON format
#         data = json.loads(clean_data)

#         # Loop through the data to find the first valid latitude & longitude
#         for item in data:
#             if isinstance(item, list):
#                 for sub_item in item:
#                     if isinstance(sub_item, list) and len(sub_item) > 1 and isinstance(sub_item[1], list):
#                         # Extract latitude and longitude
#                         longitude = sub_item[1][1][1]  # Longitude is at index 1
#                         latitude = sub_item[1][1][2]   # Latitude is at index 2

#                         # Save extracted data to a new JSON file
#                         coordinates = {"latitude": latitude, "longitude": longitude}
#                         with open(output_file, "w", encoding="utf-8") as out_file:
#                             json.dump(coordinates, out_file, indent=4)

#                         print("✅ Extracted coordinates saved successfully!")
#                         return  # Stop after finding the first valid coordinates

#         print("⚠️ No valid latitude/longitude found!")

#     except FileNotFoundError:
#         print("❌ json.txt file not found in the project folder")
#     except json.JSONDecodeError as e:
#         print(f"❌ Error decoding JSON: {e}")

# # Run the function
# extract_first_coordinates()
