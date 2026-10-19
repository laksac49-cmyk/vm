#%%
import os
import json
import glob
import shutil
import time
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "location_tracker",   
    "user": "postgres",             
    "password": "root"
}

# Directories for input and processed JSON files
DATA_FOLDER = r"C:\Users\lakma\Downloads"
PROCESSED_FOLDER = r"C:\lakmal-code\loctionTrace_with_database\Location_Trace\process"

if not os.path.exists(PROCESSED_FOLDER):
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def connect_db():
    """
    Connect to the PostgreSQL database using the provided credentials.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    return conn

def process_json_file(filepath, conn):
    """
    Reads a JSON file from the given filepath, processes each record with proper data conversions,
    and calls the insert function to load the data.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return

    if not isinstance(data, list):
        print(f"Data format in {filepath} is not a list.")
        return

    records_to_insert = []
    for record in data:
        def conv(val):
            try:
                return float(val)
            except Exception:
                return None

        latitude       = conv(record.get("latitude"))
        longitude      = conv(record.get("longitude"))
        old_latitude   = conv(record.get("old_latitude"))
        old_longitude  = conv(record.get("old_longitude"))

        address        = record.get("address") or None
        lat_long       = record.get("lat,long") or None
        local_time     = record.get("localTime") or None
        battery_level  = record.get("batteryLevel") or None
        # Set default value if googleAccount is missing.
        google_account = record.get("googleAccount") or "Not available"
        last_update    = record.get("lastUpdate") or None

        server_time_str = record.get("serverTime")
        try:
            server_time = datetime.strptime(server_time_str, "%d/%m/%Y, %H:%M:%S")
        except Exception:
            print(f"Skipping record due to invalid server_time: {record}")
            continue

        # We now only check for valid server_time.
        if server_time is None:
            print(f"Skipping record due to missing server_time: {record}")
            continue

        records_to_insert.append((
            latitude, longitude, old_latitude, old_longitude,
            address, lat_long, local_time, battery_level,
            google_account, last_update, server_time
        ))

    if records_to_insert:
        insert_records(records_to_insert, conn)

def insert_records(records, conn):
    """
    Insert data into the 'location_data' table using a composite primary key conflict check.
    The table is assumed to have primary keys on (server_time, google_account).
    """
    sql = """
    INSERT INTO location_data
      (latitude, longitude, old_latitude, old_longitude,
       address, lat_long, local_time, battery_level,
       google_account, last_update, server_time)
    VALUES %s
    ON CONFLICT (server_time, google_account) DO NOTHING;
    """
    try:
        with conn.cursor() as cur:
            execute_values(cur, sql, records)
        print(f"Inserted {len(records)} record(s).")
    except Exception as e:
        print(f"Error inserting records: {e}")

def process_new_files():
    """
    Scan the DATA_FOLDER for JSON files, process each file, and then move it to the PROCESSED_FOLDER.
    """
    conn = None
    try:
        conn = connect_db()
        files = glob.glob(os.path.join(DATA_FOLDER, "*.json"))
        if not files:
            print("No new JSON files found.")
        for filepath in files:
            print(f"Processing file: {filepath}")
            process_json_file(filepath, conn)
            
            dest = os.path.join(PROCESSED_FOLDER, os.path.basename(filepath))
            shutil.move(filepath, dest)
            print(f"Moved {filepath} to {dest}")
    except Exception as e:
        print("Error processing files:", e)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    while True:
        process_new_files()
        time.sleep(60)
#%%