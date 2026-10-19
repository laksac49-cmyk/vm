import os
import json
import time
from datetime import datetime
import requests
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Configuration
DATA_FOLDER = r"C:\Users\lakma\Downloads"
# Change TARGET_URL to the actual URL that displays the full location details.
TARGET_URL = "https://www.google.com/maps/place/5+Orchard+Cct,+Shepparton+VIC+3630,+Australia"

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

def fetch_location_data_via_selenium():
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get(TARGET_URL)
        # Increase sleep time if necessary to let the page load fully.
        time.sleep(8)
        
        js_code = """
        return (function () {
            // Extract old latitude/longitude from URL
            function getOldLocationData() {
                let oldLocationData = {};
                const url = window.location.href;
                const regex = /@(-?\\d+\\.\\d+),(-?\\d+\\.\\d+)/;
                const match = url.match(regex);
                if (match) {
                    oldLocationData.old_latitude = match[1];
                    oldLocationData.old_longitude = match[2];
                } else {
                    oldLocationData.old_latitude = "";
                    oldLocationData.old_longitude = "";
                }
                return oldLocationData;
            }
            
            // Attempt to get address.
            // UPDATE SELECTOR: Use a selector that accurately targets the element containing the address.
            const addressEl = document.querySelector('.DkEaL');
            const address = addressEl ? addressEl.innerText : "";
            
            // Attempt to get local time.
            // UPDATE SELECTOR: Inspect the element that shows the local time.
            const localTimeEl = document.querySelector('[data-local-time]'); 
            const localTime = localTimeEl ? localTimeEl.innerText : "";
            
            // Attempt to get battery level.
            // UPDATE SELECTOR: Adjust if necessary.
            const batteryEl = document.querySelector('div[aria-label*="Battery"]');
            const batteryLevel = batteryEl ? (batteryEl.innerText || batteryEl.getAttribute("aria-label")) : "";
            
            // Attempt to get Google account.
            // UPDATE SELECTOR: The current selector (.DUwDvf.lfPIob) appears to be returning the address.
            // Inspect the page element that contains the account name (e.g. "Thilak Fernando") and update the selector.
            const accountEl = document.querySelector('.DUwDvf.lfPIob');
            const googleAccount = accountEl ? accountEl.innerText.trim() : "";
            
            // Attempt to get last update.
            // UPDATE SELECTOR: Adjust the selector to match the element that shows "Just now" or similar.
            const updateEl = document.querySelector('h2.bwoZTb.fontBodyMedium span');
            const lastUpdate = updateEl ? updateEl.innerText.trim() : "";
            
            // Extract latitude and longitude from the URL.
            let lat = "", lng = "";
            const locRegex = /@(-?\\d+\\.\\d+),(-?\\d+\\.\\d+)/;
            const locMatch = window.location.href.match(locRegex);
            if (locMatch) {
                lat = parseFloat(locMatch[1]);
                lng = parseFloat(locMatch[2]);
            }
            
            const oldData = getOldLocationData();
            return {
                "latitude": lat,
                "longitude": lng,
                "address": address,
                "old_latitude": oldData.old_latitude,
                "old_longitude": oldData.old_longitude,
                "lat,long": lat + ", " + lng,
                "localTime": localTime,
                "batteryLevel": batteryLevel,
                "googleAccount": googleAccount,
                "lastUpdate": lastUpdate,
                "serverTime": new Date().toLocaleString('en-GB', { hour12: false })
            };
        })();
        """
        
        result = driver.execute_script(js_code)
        return result
    finally:
        driver.quit()

def save_to_json(data):
    if not data:
        return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"LatLong_{timestamp}.json"
    filepath = os.path.join(DATA_FOLDER, filename)
    # Save data inside a list to preserve previous format.
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump([data], f, indent=2)
    print(f"Saved data to {filepath}")

def main():
    while True:
        data = fetch_location_data_via_selenium()
        if data:
            print("Fetched Data:")
            print(json.dumps(data, indent=2))
            save_to_json(data)
        else:
            print("No data fetched.")
        time.sleep(60)  # Wait 60 seconds before fetching again

if __name__ == "__main__":
    main()