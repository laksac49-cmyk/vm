#%%
import os
import json
import pandas as pd
import plotly.express as px
from datetime import datetime

# Define project folder where processed JSON files are stored
project_folder = r"./locations"

# Function to get the latest processed location file
def get_latest_processed_file():
    files = [f for f in os.listdir(project_folder) if f.endswith(".json")]
    if not files:
        print("❌ No processed location files found.")
        return None
    files.sort(reverse=True)  # Sort by latest
    return os.path.join(project_folder, files[0])

# Function to clean and standardize localTime formats
def fix_local_time_format(time_str):
    """ Fixes localTime format issues (convert to 24-hour format) """
    if not time_str:
        return None

    # Skip entries where localTime is a battery percentage (e.g., "94%")
    if "%" in time_str:
        return None

    time_str = time_str.strip()  # Remove unwanted invisible characters

    # Convert time like "19:18" to "YYYY-MM-DD HH:MM:SS"
    current_date = datetime.now().strftime("%Y-%m-%d")  # Get today's date
    try:
        # Try to convert to 24-hour format
        return datetime.strptime(f"{current_date} {time_str}", "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        print(f"⚠️ Unknown localTime format: {time_str}")
        return None

# Function to parse JSON and extract battery data
def prepare_battery_data(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):  # Convert single dictionary to list
            data = [data]

    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        return []

    df = pd.DataFrame(data)

    if "localTime" not in df.columns or "batteryLevel" not in df.columns or "serverTime" not in df.columns:
        print("❌ Missing required columns in JSON file.")
        return []

    valid_data = []
    for _, entry in df.iterrows():
        try:
            # Fix battery level
            battery_level = str(entry.get("batteryLevel", "")).strip().replace("%", "")
            if not battery_level.isdigit():
                continue  # Skip invalid battery levels

            battery_level = int(battery_level)

            # Fix local time, skip if invalid or it's a battery percentage
            local_time = fix_local_time_format(entry.get("localTime", ""))
            if not local_time:
                continue  # Skip if localTime is invalid or contains battery level percentage

            # Fix server time
            server_time = entry.get("serverTime", "").strip()
            if not server_time:
                continue  # Skip if serverTime is missing

            # Add valid entry to data
            valid_data.append({
                "localTime": local_time,
                "serverTime": server_time,
                "batteryLevel": battery_level,
            })
        except Exception as e:
            print(f"⚠️ Error processing entry: {e}")
            continue

    if not valid_data:
        print("⚠️ No valid battery data found.")
        return []

    return sorted(valid_data, key=lambda x: x["serverTime"])  # Sort by serverTime

# Function to generate the battery chart
def create_battery_chart():
    latest_file = get_latest_processed_file()
    if not latest_file:
        return

    battery_data = prepare_battery_data(latest_file)
    if not battery_data:
        print("⚠️ No valid battery data available. Creating an empty chart.")
        return

    df_battery = pd.DataFrame(battery_data)
    df_battery['combinedTime'] = df_battery['localTime'] + ' | ' + df_battery['serverTime']

    # Get the Google account name from the filename (assuming the filename contains the account name)
    google_account_name = os.path.basename(latest_file).split('.')[0]  # Extract name from file name

    # Create the battery chart
    fig = px.line(df_battery, x='combinedTime', y='batteryLevel', title="Battery Level Over Time", markers=True)

    fig.update_layout(
        xaxis_title="Time (LocalTime | ServerTime)",
        yaxis_title="Battery Level (%)",
        template="plotly_dark",
        xaxis_tickangle=-45,
    )

    # Save the chart with dynamic filename based on Google account name
    chart_filename = os.path.join(project_folder, f"{google_account_name}_battery_chart.html")
    fig.write_html(chart_filename)
    print(f"📊 Battery chart saved as {google_account_name}_battery_chart.html")

# Run the process
create_battery_chart()














# #%%
# import os
# import json
# import pandas as pd
# import plotly.express as px
# from datetime import datetime

# # Define project folder where processed JSON files are stored
# project_folder = r"./locations"

# # Function to get the latest processed location file
# def get_latest_processed_file():
#     files = [f for f in os.listdir(project_folder) if f.endswith(".json")]
#     if not files:
#         print("❌ No processed location files found.")
#         return None
#     files.sort(reverse=True)  # Sort by latest
#     return os.path.join(project_folder, files[0])

# # Function to clean and standardize localTime formats
# def fix_local_time_format(time_str):
#     """ Fixes localTime format issues (AM/PM handling, unwanted characters) """
#     if not time_str:
#         return None

#     time_str = time_str.replace("â€¯", "").strip()  # Remove unwanted invisible characters

#     # Convert to 24-hour format
#     for fmt in ["%A, %I:%M %p", "%A, %I:%M%p", "%I:%M %p", "%I:%M%p"]:
#         try:
#             return datetime.strptime(time_str, fmt).strftime("%Y-%m-%d %H:%M:%S")
#         except ValueError:
#             continue

#     print(f"⚠️ Unknown localTime format: {time_str}")
#     return None

# # Function to parse JSON and extract battery data
# def prepare_battery_data(filepath):
#     try:
#         with open(filepath, "r", encoding="utf-8") as f:
#             data = json.load(f)

#         if isinstance(data, dict):  # Convert single dictionary to list
#             data = [data]

#     except json.JSONDecodeError as e:
#         print(f"❌ Error parsing JSON: {e}")
#         return []

#     df = pd.DataFrame(data)

#     if "localTime" not in df.columns or "batteryLevel" not in df.columns or "serverTime" not in df.columns:
#         print("❌ Missing required columns in JSON file.")
#         return []

#     valid_data = []
#     for _, entry in df.iterrows():
#         try:
#             battery_level = str(entry.get("batteryLevel", "")).strip().replace("%", "")

#             if not battery_level.isdigit():
#                 continue  # Skip invalid battery levels

#             local_time = fix_local_time_format(entry.get("localTime", ""))
#             server_time = entry.get("serverTime", "").strip()

#             if local_time and server_time:
#                 valid_data.append({
#                     "localTime": local_time,
#                     "serverTime": server_time,
#                     "batteryLevel": int(battery_level),
#                 })
#         except Exception as e:
#             print(f"⚠️ Error processing entry: {e}")
#             continue

#     if not valid_data:
#         print("⚠️ No valid battery data found.")
#         return []

#     return sorted(valid_data, key=lambda x: x["serverTime"])  # Sort by time

# # Function to generate the battery chart
# def create_battery_chart():
#     latest_file = get_latest_processed_file()
#     if not latest_file:
#         return

#     battery_data = prepare_battery_data(latest_file)
#     if not battery_data:
#         print("⚠️ No valid battery data available. Creating an empty chart.")
#         return

#     df_battery = pd.DataFrame(battery_data)
#     df_battery['combinedTime'] = df_battery['localTime'] + ' | ' + df_battery['serverTime']

#     fig = px.line(df_battery, x='combinedTime', y='batteryLevel', title="Battery Level Over Time", markers=True)

#     fig.update_layout(
#         xaxis_title="Time (LocalTime | ServerTime)",
#         yaxis_title="Battery Level (%)",
#         template="plotly_dark",
#         xaxis_tickangle=-45,
#     )

#     fig.write_html(os.path.join(project_folder, "battery_chart.html"))
#     print("📊 Battery chart saved as battery_chart.html")

# # Run the process
# create_battery_chart()

