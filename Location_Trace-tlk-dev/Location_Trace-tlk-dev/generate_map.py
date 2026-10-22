# %%
import os
import json
import folium
import pandas as pd
from datetime import datetime
import numpy as np

# Define project folder where processed JSON files are stored
project_folder = r"./locations"

# Find the latest processed location file
def get_latest_processed_file():
    files = [f for f in os.listdir(project_folder) if f.endswith(".json")]
    if not files:
        print("No processed location files found.")
        return None
    files.sort(reverse=True)  # Sort by latest
    return os.path.join(project_folder, files[0])

# Function to parse different datetime formats
def parse_datetime(date_string):
    formats = ["%Y-%m-%dT%H:%M:%S.%fZ", "%d/%m/%Y, %H:%M:%S"]
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unknown date format: {date_string}")

# Function to calculate duration (stay time)
def calculate_duration(start_time, end_time):
    start_dt = parse_datetime(start_time)
    end_dt = parse_datetime(end_time)
    duration = start_dt - end_dt
    return str(duration)

# Function to get the nearest available battery level
def get_nearest_battery(df, index, direction="both"):
    if pd.notna(df.loc[index, "batteryLevel"]) and df.loc[index, "batteryLevel"] != "":
        return df.loc[index, "batteryLevel"]
    if direction in ["both", "forward"]:
        for i in range(index + 1, len(df)):
            if pd.notna(df.loc[i, "batteryLevel"]) and df.loc[i, "batteryLevel"] != "":
                return df.loc[i, "batteryLevel"]
    if direction in ["both", "backward"]:
        for i in range(index - 1, -1, -1):
            if pd.notna(df.loc[i, "batteryLevel"]) and df.loc[i, "batteryLevel"] != "":
                return df.loc[i, "batteryLevel"]
    return "Unknown"

# Generate map with markers & stay duration
def create_map(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        # Try to load the content as a single JSON array
        try:
            data = json.load(f)
        except json.decoder.JSONDecodeError:
            # If error occurs, attempt to load multiple JSON objects line by line
            f.seek(0)  # Rewind the file to the beginning
            data = []
            for line in f:
                try:
                    data.append(json.loads(line.strip()))
                except json.decoder.JSONDecodeError:
                    continue

    if not isinstance(data, list) or len(data) == 0:
        print("No valid data found in the JSON file.")
        return

    df = pd.DataFrame(data)
    required_columns = [
        "latitude", "longitude", "batteryLevel", "address", "localTime",
        "googleAccount", "serverTime", "lastUpdate"
    ]
    for col in required_columns:
        if col not in df.columns:
            print(f"Missing column: {col}")
            return

    # Replace non-numeric values in 'latitude' and 'longitude' with NaN
    df["latitude"] = pd.to_numeric(df["latitude"], errors='coerce')
    df["longitude"] = pd.to_numeric(df["longitude"], errors='coerce')

    # Drop rows with NaN in 'latitude' or 'longitude'
    df = df.dropna(subset=["latitude", "longitude"])

    df = df.sort_values(by="serverTime",
                        ascending=False).reset_index(drop=True)

    first_location = (df.iloc[0]["latitude"], df.iloc[0]["longitude"])
    my_map = folium.Map(location=first_location, zoom_start=14)

    grouped_locations = []
    prev_location = None

    for i, row in df.iterrows():
        lat, lon = row["latitude"], row["longitude"]
        current_location = (lat, lon)

        if prev_location == current_location and grouped_locations:
            grouped_locations[-1]["end_server_time"] = row["serverTime"]
            grouped_locations[-1]["end_local_time"] = row["localTime"]
            grouped_locations[-1]["end_battery"] = get_nearest_battery(
                df, i, direction="forward")
            grouped_locations[-1]["records"].append(row.to_dict())
        else:
            grouped_locations.append({
                "latitude":
                lat,
                "longitude":
                lon,
                "address":
                row["address"],
                "googleAccount":
                row["googleAccount"],
                "start_server_time":
                row["serverTime"],
                "end_server_time":
                row["serverTime"],
                "start_local_time":
                row["localTime"],
                "end_local_time":
                row["localTime"],
                "start_battery":
                get_nearest_battery(df, i, direction="both"),
                "end_battery":
                get_nearest_battery(df, i, direction="both"),
                "lastUpdate":
                row["lastUpdate"],
                "records": [row.to_dict()]
            })

        prev_location = current_location

    locations = []

    for idx, loc in enumerate(grouped_locations):
        lat, lon = loc["latitude"], loc["longitude"]
        locations.append((lat, lon))
        stay_duration = calculate_duration(loc["start_server_time"],
                                           loc["end_server_time"])
        records_json = json.dumps(loc["records"], ensure_ascii=False)
        # Clean the local time fields to remove unwanted marks
        start_local_time = loc["start_local_time"].replace("â€¯", "")
        end_local_time = loc["end_local_time"].replace("â€¯", "")
        popup_text = f"""
        <b>Google Account:</b> {loc["googleAccount"]}<br>
        <b>Address:</b> {loc["address"]}<br>        
        <b>Lat_Long</b> {lat},{lon}<br>
        <b>Start Local Time:</b> {end_local_time}<br>
        <b>End Local Time:</b> {start_local_time}<br>
        <b>Start Battery:</b> {loc["start_battery"]}<br>
        <b>End Battery:</b> {loc["end_battery"]}<br>
        <b>Last Update:</b> {loc["lastUpdate"]}<br>
        <b>Start Server Time:</b> {loc["end_server_time"]}<br>
        <b>End Server Time:</b> {loc["start_server_time"]}<br>
        <b>Stay Duration:</b> {stay_duration}<br>
        <a href="https://www.google.com/maps?q={lat},{lon}" target="_blank">Open in Google Maps</a><br>
        <button onclick='showRecords({json.dumps(loc["records"], ensure_ascii=False)})'>Show All Records</button>
        """
        if idx == 0:
            folium.Marker(
                location=(lat, lon),
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"Location {idx + 1}",
                icon=folium.Icon(color="blue" if idx > 0 else "red",
                                icon="info-sign")
                # radius=1,  # Adjust size of the dot
                # color="blue" if idx > 0 else "red",  # Outline color
                # fill=True,
                # fill_color="blue" if idx > 0 else "red",  # Fill color
                # fill_opacity=0.4,
            ).add_to(my_map)
        else:
            folium.CircleMarker(
                location=(lat, lon),
                radius=5,  # Adjust the size of the dot
                color="blue" if idx > 0 else "red",  # Outline color
                fill=False,
                fill_color="blue" if idx > 0 else "red",  # Fill color
                fill_opacity=0.1,  # Adjust opacity
                tooltip=f"Location {idx + 1}",
                popup=folium.Popup(popup_text, max_width=300),
            ).add_to(my_map)

    folium.PolyLine(locations, color="blue", weight=2.5,
                    opacity=0.7).add_to(my_map)

    # Add JavaScript and CSS to style the table
    my_map.get_root().html.add_child(
        folium.Element("""
    <style>
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 14px;
    }
    th, td {
        padding: 12px;
        text-align: left;
        border: 1px solid #ddd;
    }
    th {
        background-color: #4CAF50;
        color: white;
    }
    tr:nth-child(even) {
        background-color: #f2f2f2;
    }
    tr:hover {
        background-color: #ddd;
    }
    button {
        background-color: #4CAF50;
        color: white;
        padding: 10px 15px;
        border: none;
        cursor: pointer;
        font-size: 14px;
        border-radius: 5px;
    }
    button:hover {
        background-color: #45a049;
    }
    .record-table {
        width: 90%;
        margin: auto;
        margin-top: 30px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    </style>

    <script>
    function showRecords(records) {
        let recordWindow = window.open('', 'Records', 'width=800,height=600');
        if (recordWindow) {
            recordWindow.focus();
        }
        recordWindow.document.write('<h2>Location Records</h2>');
        
        // Create a table to display records
        let table = '<table class="record-table">';
        table += `<tr style="background-color: #4CAF50; color: white;">
        <th>Google Account</th><th>Address</th><th>Local Time</th><th>Battery Level</th>
        <th>Last Update</th><th>Server Time</th><th>Lat_Long</th>
        </tr>`;
        
        records.forEach((record, index) => {
            const rowColor = (index % 2 === 0) ? '#f2f2f2' : '#ffffff';  // Alternate row color
            table += `<tr style="background-color: ${rowColor};">
                <td>${record.googleAccount}</td>
                <td>${record.address}</td>
                <td>${record.localTime.replace("â€¯", "")}</td>
                <td>${record.batteryLevel}</td>
                <td>${record.lastUpdate}</td>
                <td>${record.serverTime}</td>
                <td>${record.latitude},${record.longitude}</td>                
            </tr>`;
        });
        table += '</table>';
        recordWindow.document.write(table);
        recordWindow.document.close();
    }
    </script>
    """))

    # Save the map to an HTML file
    map_filename = filepath.replace(".json", "_map.html")
    my_map.save(map_filename)
    print(f"Map saved as {map_filename}")

# Get the latest processed file
latest_file = get_latest_processed_file()

# If a valid file is found, create the map
if latest_file:
    create_map(latest_file)
