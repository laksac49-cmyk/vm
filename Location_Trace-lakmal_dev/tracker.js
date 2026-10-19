// tracker.js
const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  try {
    console.log("Launching headless browser...");

    // Launch Puppeteer with extra arguments.
    const browser = await puppeteer.launch({
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-web-security'
      ]
    });
    const page = await browser.newPage();

    // Set a realistic user agent.
    await page.setUserAgent(
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
      "AppleWebKit/537.36 (KHTML, like Gecko) " +
      "Chrome/108.0.0.0 Safari/537.36"
    );

    const mapsURL = "https://www.google.com/maps/@-36.3586675,145.4087833,21z/data=!4m4!7m3!1m1!1s113666807484587751078!2e2?entry=ttu&g_ep=EgoyMDI1MDYwMS4wIKXMDSoASAFQAw%3D%3D";
    await page.goto(mapsURL, { waitUntil: 'networkidle2' });
    console.log("Page loaded, waiting for data...");

    // Use a simple 3-second delay.
    await new Promise(resolve => setTimeout(resolve, 3000));

    // Log a snippet of the raw text.
    const rawText = await page.evaluate(() => document.body.innerText || "");
    console.log("Raw text snippet (first 300 chars):", rawText.substring(0, 300));

    // Extraction in page context
    const locationData = await page.evaluate(() => {
      function safeParse(raw) {
        const xssiPrefix = ")]}'";
        if (raw.startsWith(xssiPrefix)) {
          raw = raw.substring(xssiPrefix.length);
        }
        try {
          return JSON.parse(raw);
        } catch (e) {
          console.error("JSON parse error:", e);
          return null;
        }
      }
      
      function extractLatLongAndAddress(data) {
        if (!data || !Array.isArray(data)) {
          return { latitude: "Not found", longitude: "Not found", address: "Not found" };
        }
        // Try common pattern assumptions
        if (Array.isArray(data[0])) {
          for (let entry of data[0]) {
            if (entry && Array.isArray(entry) && entry[1] && Array.isArray(entry[1])) {
              const possibleLat = entry[1][1];
              const possibleLng = entry[1][2];
              const possibleAddress = entry[1][4] || "Address not available";
              if (!isNaN(parseFloat(possibleLat)) && !isNaN(parseFloat(possibleLng))) {
                return { 
                  latitude: possibleLat.toString(), 
                  longitude: possibleLng.toString(), 
                  address: possibleAddress 
                };
              }
            }
          }
        }
        return { latitude: "Not found", longitude: "Not found", address: "Not found" };
      }
      
      let raw = document.body.innerText || "";
      let parsedData = safeParse(raw.substring(5)); // Adjust this offset if needed.
      let result = extractLatLongAndAddress(parsedData);
      result.serverTime = new Date().toLocaleString('en-GB', { hour12: false });
      return result;
    });

    console.log("Extracted location data:", locationData);

    const timestamp = new Date().toISOString().replace(/[:.-]/g, "_");
    const filename = `LatLong_${timestamp}.json`;
    fs.writeFileSync(filename, JSON.stringify(locationData, null, 2));
    console.log(`Saved location data to ${filename}`);

    await browser.close();
    process.exit(0);
  } catch (error) {
    console.error("Error during tracking:", error);
    process.exit(1);
  }
})();