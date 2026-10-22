
#%%
import shutil
import os
import json
import time
import psutil  # To close running Chrome instances
from seleniumwire import webdriver  # Import Selenium Wire to capture network requests
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import subprocess  # Import subprocess to run other scripts

# Function to close all running Chrome instances to avoid profile lock issues
def close_chrome():
    for process in psutil.process_iter(attrs=["pid", "name"]):
        if "chrome" in process.info["name"].lower():
            try:
                process.kill()  # Kill Chrome process
            except psutil.NoSuchProcess:
                pass

# Function to get response data from the target URL
def get_response_data(driver):
    for request in driver.requests:
        if "locationsharing/read" in request.url:  # Find the specific network request
            try:
                if request.response:
                    response_data = request.response.body.decode("utf-8")
                    return json.loads(response_data)  # Convert JSON response to Python dict
            except Exception as e:
                print(f"Error decoding response: {e}")
    return None  # Return None if no response found

# Main function for content1.py
def main():
    # Close all Chrome instances before launching Selenium
    close_chrome()
    time.sleep(2)  # Wait for processes to close

    # Set Chrome options to use your logged-in Google profile
    chrome_options = Options()
    chrome_options.add_argument(r"user-data-dir=C:\Users\g2001\AppData\Local\Google\Chrome\User Data")  # Use Google profile
    chrome_options.add_argument(r"profile-directory=Default")  # Default profile
    chrome_options.add_argument("--start-maximized")  # Maximize window
    chrome_options.add_argument("--remote-debugging-port=9222")  # Avoid permission issues
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])  # Remove automation banner
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # Set up ChromeDriver
    chromedriver_path = r"C:\chromedriver.exe"  # Update with the correct path
    service = Service(chromedriver_path)

    # Start Chrome WebDriver with Selenium Wire (to intercept network requests)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # ✅ Open Google Maps location-sharing directly
    target_url = "https://www.google.com/maps/rpc/locationsharing/read?authuser=0&hl=en&gl=lk&pb=!1e1!2m2!1sjdWtZ7noPOCK4-EPl6Gu-Ak!7e81!3m2!1s113666807484587751078!2sEggHBi03Hi10kQ%3D%3D!7BGmYAhp_Fo9ihdjvw7NiQ5H_FrJKTS7uI0rei6g7yn5Rw55ZHQAfxtFh0YzgSOjOSibOl3pwMkb9VBJGo7Fmzoaiygh-jl5AWWyAQDKSpc4tWEsVbu_quw44FeFx_JleQ4suxIl4C4Ww"
    driver.get(target_url)

    print("🚀 Waiting for network requests...")
    time.sleep(10)  # Wait longer to ensure network requests are captured

    # ✅ Refresh page to ensure request is triggered
    driver.refresh()
    time.sleep(5)

    # ✅ Get response data from the intercepted request
    response_data = get_response_data(driver)

    # ✅ Save response data to JSON file
    if response_data:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(response_data, f, indent=4, ensure_ascii=False)
        print("✅ Response saved to data.json")
    else:
        print("❌ No response data found! Debugging...")

        # Debug: Save all captured request URLs for troubleshooting
        with open("debug_requests.txt", "w", encoding="utf-8") as f:
            for request in driver.requests:
                f.write(request.url + "\n")
        print("🔍 Debugging file saved: debug_requests.txt")

    driver.quit()  # Close Chrome

    # Call content2.py after content1.py finishes
    print("🔄 Calling content2.py...")
    subprocess.run(["python", "content2.py"])  # Run content2.py

    # Call content3.py after content2.py finishes
    print("🔄 Calling content3.py...")
    subprocess.run(["python", "content3.py"])  # Run content3.py

if __name__ == '__main__':
    main()




