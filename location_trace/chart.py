# %%
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

# %%
processed_file = get_latest_processed_file()
print(processed_file)

# %%
df = pd.read_json(processed_file)

# %%
df["_batteryLevel"] = pd.to_numeric(df["batteryLevel"].str.rstrip("%"), errors="coerce")

# Optionally, handle NaN values (e.g., fill with 0 or drop rows with NaN)
df.dropna(subset=["_batteryLevel"], inplace=True)

# %%
# df.head()

# %%
from pytz import timezone

# server time is given by Melbourne time. Conver that to Sri Lanka time using time zones and daylight savings considetations, Do not hardcode the offset


def convert_to_sri_lanka_time(server_time_str):
    # Parse the server time string into a datetime object
    server_time = datetime.strptime(server_time_str, "%d/%m/%Y, %H:%M:%S")

    # Convert to Sri Lanka time (UTC+5:30)
    # Define time zones
    melbourne_tz = timezone("Australia/Melbourne")
    sri_lanka_tz = timezone("Asia/Colombo")

    # Localize server time to Melbourne time zone
    server_time = melbourne_tz.localize(server_time)

    # Convert to Sri Lanka time zone
    sri_lanka_time = server_time.astimezone(sri_lanka_tz)

    return sri_lanka_time.strftime("%Y-%m-%d %H:%M:%S")


# Apply the conversion function to the 'serverTime' column
df["sriLankaTime"] = df["serverTime"].apply(convert_to_sri_lanka_time)

# %%
# Plot _batteryLevel vs sriLankaTime using plotl
fig = px.line(df, x="sriLankaTime", y="_batteryLevel", title="Battery Level Over Time")
fig.update_traces(mode="lines+markers")
fig.update_layout(
    xaxis_title="Sri Lanka Time",
    yaxis_title="Battery Level (%)",
    xaxis=dict(tickformat="%Y-%m-%d %H:%M:%S"),
    yaxis=dict(range=[0, max(df["_batteryLevel"]) + 10]),
    showlegend=False,
)
# fig.show()
# Save the plot as an HTML file
google_account = df["googleAccount"].iloc[0]  # Assuming all rows have the same Google account
output_file = os.path.join(project_folder, f"{google_account}_battery_chart.html")
fig.write_html(output_file)
print(f"✅ Plot saved as {output_file}")

# %%
