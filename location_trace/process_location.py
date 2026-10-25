#%%
import os
import pandas as pd
import json
import subprocess
from datetime import datetime
import re

# Paths
downloads_folder = os.path.expanduser("~/Downloads")
output_folder = "./locations"
extracted_coordinates_file = "./json/extracted_coordinates.json"
generate_map_script = "./generate_map.py"
chart_script = "./chart.py"

# Function to load extracted coordinates
def load_extracted_coordinates():
    if not os.path.exists(extracted_coordinates_file):
        print("❌ extracted_coordinates.json not found!")
        return []
    with open(extracted_coordinates_file, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print("❌ Error decoding extracted_coordinates.json")
            return []

# Function to clean and convert time format
def clean_and_convert_time(time_str):
    if isinstance(time_str, str):
        time_str = re.sub(r"\u00e2\u20ac\u00af", "", time_str).strip()  # Remove unwanted characters
        try:
            return datetime.strptime(time_str, "%I:%M %p").strftime("%H:%M")
        except ValueError:
            return time_str  # Return as is if format is incorrect
    return time_str

# Function to merge and process location files
def merge_and_process_files(file_list, extracted_coordinates):
    all_data = []
    for file in file_list:
        with open(file, 'r', encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    all_data.extend(data)
                else:
                    all_data.append(data)
            except json.JSONDecodeError:
                print(f"⚠️ Skipping {file}: JSON Decode Error.")
            except Exception as e:
                print(f"⚠️ Skipping {file}: {str(e)}")

    if not all_data:
        print("⚠️ No valid data to process.")
        return None

    df = pd.DataFrame(all_data)
    required_columns = ["googleAccount", "serverTime", "localTime", "longitude", "latitude"]
    for col in required_columns:
        if col not in df.columns:
            df[col] = None

    # Convert time fields to 24-hour format
    time_fields = ["localTime", "startLocalTime", "endLocalTime"]
    for field in time_fields:
        if field in df.columns:
            df[field] = df[field].apply(clean_and_convert_time)

    df.drop_duplicates(subset=["serverTime"], keep="first", inplace=True)
    df.sort_values(by="serverTime", ascending=False, inplace=True)

    # Replace longitude & latitude from extracted_coordinates.json
    if extracted_coordinates:
        for i, coord in enumerate(extracted_coordinates):
            if i < len(df):
                df.loc[df.index[i], "longitude"] = coord["longitude"]
                df.loc[df.index[i], "latitude"] = coord["latitude"]

    df.drop(columns=["timestamp", "accuracy", "batteryPercentage"], errors='ignore', inplace=True)
    unique_accounts = df["googleAccount"].dropna().unique()

    if len(unique_accounts) == 0:
        print("❌ No valid Google account found. No file will be created.")
        return None

    google_account = unique_accounts[0]
    output_file = os.path.join(output_folder, f"{google_account}.json")
    output_map = os.path.join(output_folder, f"{google_account}_map.html")
    output_chart = os.path.join(output_folder, f"{google_account}_battery_chart.html")
    os.makedirs(output_folder, exist_ok=True)

    # Save the processed JSON data
    with open(output_file, 'w', encoding="utf-8") as json_file:
        json.dump(df.to_dict(orient="records"), json_file, indent=4)

    return google_account, output_file, output_map, output_chart

# Function to get JSON files from Downloads
def get_json_files_from_downloads():
    return [os.path.join(downloads_folder, file) for file
            in os.listdir(downloads_folder) if file.endswith(".json")]

# Function to call generate_map.py
def run_generate_map():
    try:
        result = subprocess.run(["python", generate_map_script]
                                , check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✅ generate_map.py executed successfully!")
        print(result.stdout.decode())
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running generate_map.py: {e}")
        print(e.stderr.decode())

# Function to call chart.py
def run_chart():
    try:
        result = subprocess.run(["python", chart_script], check=True
                                , stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✅ chart.py executed successfully!")
        print(result.stdout.decode())
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running chart.py: {e}")
        print(e.stderr.decode())

# %%
# Function to open files in browser with proper URL
def open_files_in_browser(file1, file2, file3):
    url1 = f"file:///{os.path.abspath(file1)}"
    url2 = f"file:///{os.path.abspath(file2)}"
    url3 = f"file:///{os.path.abspath(file3)}"

    # Open the files in 3 browser tabs
    try:
        subprocess.run(["open", url1], check=True)
        subprocess.run(["open", url3], check=True)
        subprocess.run(["open", url2], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error opening files in browser: {e}")
        print(e.stderr.decode())

# %%
if __name__ == "__main__":
    extracted_coordinates = load_extracted_coordinates()
    file_list = get_json_files_from_downloads()
    created_file, output_file, output_map, output_chart = merge_and_process_files(file_list
                                                                                  , extracted_coordinates)

    if created_file:
        print(f"✅ Processing complete! Data saved in: {created_file}.json")
        run_generate_map()
        run_chart()

        # Open the files in browser
        open_files_in_browser(output_file, output_map, output_chart)
    else:
        print("⚠️ No valid Google account found. No file created.")











# #%%
# import os
# import pandas as pd
# import json
# import subprocess
# from datetime import datetime
# import re

# # Paths
# downloads_folder = os.path.expanduser("~/Downloads")
# output_folder = "./locations"
# extracted_coordinates_file = "./json/extracted_coordinates.json"
# generate_map_script = "./generate_map.py"
# chart_script = "./chart.py"

# # Function to load extracted coordinates
# def load_extracted_coordinates():
#     if not os.path.exists(extracted_coordinates_file):
#         print("❌ extracted_coordinates.json not found!")
#         return []
#     with open(extracted_coordinates_file, "r", encoding="utf-8") as f:
#         try:
#             return json.load(f)
#         except json.JSONDecodeError:
#             print("❌ Error decoding extracted_coordinates.json")
#             return []

# # Function to clean and convert time format
# def clean_and_convert_time(time_str):
#     if isinstance(time_str, str):
#         time_str = re.sub(r"\u00e2\u20ac\u00af", "", time_str).strip()  # Remove unwanted characters
#         try:
#             return datetime.strptime(time_str, "%I:%M %p").strftime("%H:%M")
#         except ValueError:
#             return time_str  # Return as is if format is incorrect
#     return time_str

# # Function to merge and process location files
# def merge_and_process_files(file_list, extracted_coordinates):
#     all_data = []
#     for file in file_list:
#         with open(file, 'r', encoding="utf-8") as f:
#             try:
#                 data = json.load(f)
#                 if isinstance(data, list):
#                     all_data.extend(data)
#                 else:
#                     all_data.append(data)
#             except json.JSONDecodeError:
#                 print(f"⚠️ Skipping {file}: JSON Decode Error.")
#             except Exception as e:
#                 print(f"⚠️ Skipping {file}: {str(e)}")

#     if not all_data:
#         print("⚠️ No valid data to process.")
#         return None

#     df = pd.DataFrame(all_data)
#     required_columns = ["googleAccount", "serverTime", "localTime", "longitude", "latitude"]
#     for col in required_columns:
#         if col not in df.columns:
#             df[col] = None

#     # Convert time fields to 24-hour format
#     time_fields = ["localTime", "startLocalTime", "endLocalTime"]
#     for field in time_fields:
#         if field in df.columns:
#             df[field] = df[field].apply(clean_and_convert_time)

#     df.drop_duplicates(subset=["serverTime"], keep="first", inplace=True)
#     df.sort_values(by="serverTime", ascending=False, inplace=True)

#     # Replace longitude & latitude from extracted_coordinates.json
#     if extracted_coordinates:
#         for i, coord in enumerate(extracted_coordinates):
#             if i < len(df):
#                 df.loc[df.index[i], "longitude"] = coord["longitude"]
#                 df.loc[df.index[i], "latitude"] = coord["latitude"]

#     df.drop(columns=["timestamp", "accuracy", "batteryPercentage"], errors='ignore', inplace=True)
#     unique_accounts = df["googleAccount"].dropna().unique()

#     if len(unique_accounts) == 0:
#         print("❌ No valid Google account found. No file will be created.")
#         return None

#     google_account = unique_accounts[0]
#     output_file = os.path.join(output_folder, f"{google_account}.json")
#     os.makedirs(output_folder, exist_ok=True)

#     with open(output_file, 'w', encoding="utf-8") as json_file:
#         json.dump(df.to_dict(orient="records"), json_file, indent=4)

#     return google_account

# # Function to get JSON files from Downloads
# def get_json_files_from_downloads():
#     return [os.path.join(downloads_folder, file) for file in os.listdir(downloads_folder) if file.endswith(".json")]

# # Function to call generate_map.py
# def run_generate_map():
#     try:
#         result = subprocess.run(["python", generate_map_script], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#         print("✅ generate_map.py executed successfully!")
#         print(result.stdout.decode())
#     except subprocess.CalledProcessError as e:
#         print(f"❌ Error running generate_map.py: {e}")
#         print(e.stderr.decode())

# # Function to call chart.py
# def run_chart():
#     try:
#         result = subprocess.run(["python", chart_script], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#         print("✅ chart.py executed successfully!")
#         print(result.stdout.decode())
#     except subprocess.CalledProcessError as e:
#         print(f"❌ Error running chart.py: {e}")
#         print(e.stderr.decode())

# if __name__ == "__main__":
#     extracted_coordinates = load_extracted_coordinates()
#     file_list = get_json_files_from_downloads()
#     created_file = merge_and_process_files(file_list, extracted_coordinates)

#     if created_file:
#         print(f"✅ Processing complete! Data saved in: {created_file}.json")
#         run_generate_map()
#         run_chart()
#     else:
#         print("⚠️ No valid Google account found. No file created.")



















# #%%
# import os
# import pandas as pd
# import json
# import subprocess
# from datetime import datetime
# import re

# # Paths
# downloads_folder = os.path.expanduser("~/Downloads")
# output_folder = "./locations"
# extracted_coordinates_file = "./json/extracted_coordinates.json"
# generate_map_script = "./generate_map.py"
# chart_script = "./chart.py"

# # Function to load extracted coordinates
# def load_extracted_coordinates():
#     if not os.path.exists(extracted_coordinates_file):
#         print("❌ extracted_coordinates.json not found!")
#         return []
#     with open(extracted_coordinates_file, "r", encoding="utf-8") as f:
#         try:
#             return json.load(f)
#         except json.JSONDecodeError:
#             print("❌ Error decoding extracted_coordinates.json")
#             return []

# # Function to clean and convert time format
# def clean_and_convert_time(time_str):
#     if isinstance(time_str, str):
#         time_str = re.sub(r"\u00e2\u20ac\u00af", "", time_str).strip()  # Remove unwanted characters
#         try:
#             return datetime.strptime(time_str, "%I:%M %p").strftime("%H:%M")
#         except ValueError:
#             return time_str  # Return as is if format is incorrect
#     return time_str

# # Function to merge and process location files
# def merge_and_process_files(file_list, extracted_coordinates):
#     all_data = []
#     for file in file_list:
#         with open(file, 'r', encoding="utf-8") as f:
#             try:
#                 data = json.load(f)
#                 if isinstance(data, list):
#                     all_data.extend(data)
#                 else:
#                     all_data.append(data)
#             except json.JSONDecodeError:
#                 print(f"⚠️ Skipping {file}: JSON Decode Error.")
#             except Exception as e:
#                 print(f"⚠️ Skipping {file}: {str(e)}")

#     if not all_data:
#         print("⚠️ No valid data to process.")
#         return None

#     df = pd.DataFrame(all_data)
#     required_columns = ["googleAccount", "serverTime", "localTime", "longitude", "latitude"]
#     for col in required_columns:
#         if col not in df.columns:
#             df[col] = None

#     # Convert time fields to 24-hour format
#     time_fields = ["localTime", "startLocalTime", "endLocalTime"]
#     for field in time_fields:
#         if field in df.columns:
#             df[field] = df[field].apply(clean_and_convert_time)

#     df.drop_duplicates(subset=["serverTime"], keep="first", inplace=True)
#     df.sort_values(by="serverTime", ascending=False, inplace=True)
#     df = df.groupby("googleAccount").head(100)

#     # Replace longitude & latitude from extracted_coordinates.json
#     if extracted_coordinates:
#         for i, coord in enumerate(extracted_coordinates):
#             if i < len(df):
#                 df.loc[df.index[i], "longitude"] = coord["longitude"]
#                 df.loc[df.index[i], "latitude"] = coord["latitude"]

#     df.drop(columns=["timestamp", "accuracy", "batteryPercentage"], errors='ignore', inplace=True)
#     unique_accounts = df["googleAccount"].dropna().unique()

#     if len(unique_accounts) == 0:
#         print("❌ No valid Google account found. No file will be created.")
#         return None

#     google_account = unique_accounts[0]
#     output_file = os.path.join(output_folder, f"{google_account}.json")
#     os.makedirs(output_folder, exist_ok=True)

#     with open(output_file, 'w', encoding="utf-8") as json_file:
#         json.dump(df.to_dict(orient="records"), json_file, indent=4)

#     return google_account

# # Function to get JSON files from Downloads
# def get_json_files_from_downloads():
#     return [os.path.join(downloads_folder, file) for file in os.listdir(downloads_folder) if file.endswith(".json")]

# # Function to call generate_map.py
# def run_generate_map():
#     try:
#         result = subprocess.run(["python", generate_map_script], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#         print("✅ generate_map.py executed successfully!")
#         print(result.stdout.decode())
#     except subprocess.CalledProcessError as e:
#         print(f"❌ Error running generate_map.py: {e}")
#         print(e.stderr.decode())

# # Function to call chart.py
# def run_chart():
#     try:
#         result = subprocess.run(["python", chart_script], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#         print("✅ chart.py executed successfully!")
#         print(result.stdout.decode())
#     except subprocess.CalledProcessError as e:
#         print(f"❌ Error running chart.py: {e}")
#         print(e.stderr.decode())

# if __name__ == "__main__":
#     extracted_coordinates = load_extracted_coordinates()
#     file_list = get_json_files_from_downloads()
#     created_file = merge_and_process_files(file_list, extracted_coordinates)

#     if created_file:
#         print(f"✅ Processing complete! Data saved in: {created_file}.json")
#         run_generate_map()
#         run_chart()
#     else:
#         print("⚠️ No valid Google account found. No file created.")










# %%
