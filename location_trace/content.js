// content.js
(async function () {
    console.log("🔍 Google Maps Tracker Active...");

    window.__ltRpc = { latitude: "Not found", longitude: "Not found", address: "Not found" };
    window.addEventListener("message", function (ev) {
        if (!ev.data || ev.data.source !== "LT_RPC_INTERCEPT") return;
        if (ev.data.latitude != null && String(ev.data.latitude) !== "Not found") {
            window.__ltRpc = {
                latitude: ev.data.latitude,
                longitude: ev.data.longitude,
                address: ev.data.address || "Address not available"
            };
            console.log("✅ RPC MAIN:", window.__ltRpc.latitude, window.__ltRpc.longitude, window.__ltRpc.address);
        }
    });
    (function () {
        var s = document.createElement("script");
        s.textContent = [
            "(function(){",
            "function extract(data){",
            "try{",
            "if(!data||!Array.isArray(data)||!Array.isArray(data[0]))return null;",
            "for(var i=0;i<data[0].length;i++){",
            "var e=data[0][i];",
            "if(Array.isArray(e)&&e[1]&&Array.isArray(e[1][1])){",
            "return{latitude:e[1][1][2],longitude:e[1][1][1],address:e[1][4]||'Address not available'};",
            "}}",
            "}catch(err){}",
            "return null;",
            "}",
            "function parseBody(text){",
            "try{",
            "var raw=text;",
            "if(raw.indexOf(\")]}'\")===0){var nl=raw.indexOf(\"\\n\");raw=nl>=0?raw.substring(nl+1):raw.substring(4);}",
            "else if(raw.length>5&&raw.charAt(0)===\")\")raw=raw.substring(5);",
            "return extract(JSON.parse(raw));",
            "}catch(err){return null;}",
            "}",
            "function publish(loc){",
            "if(!loc||loc.latitude==null)return;",
            "window.postMessage({source:'LT_RPC_INTERCEPT',latitude:loc.latitude,longitude:loc.longitude,address:loc.address},'*');",
            "}",
            "var ofetch=window.fetch;",
            "window.fetch=function(){",
            "var args=arguments;",
            "return ofetch.apply(this,args).then(function(response){",
            "try{",
            "var u=typeof args[0]==='string'?args[0]:((args[0]&&args[0].url)||'');",
            "if(u.indexOf('locationsharing/read')!==-1){",
            "response.clone().text().then(function(t){var loc=parseBody(t);if(loc)publish(loc);}).catch(function(){});",
            "}",
            "}catch(err){}",
            "return response;",
            "});",
            "};",
            "var oOpen=XMLHttpRequest.prototype.open;",
            "var oSend=XMLHttpRequest.prototype.send;",
            "XMLHttpRequest.prototype.open=function(m,url){this.__ltUrl=url;return oOpen.apply(this,arguments);};",
            "XMLHttpRequest.prototype.send=function(){",
            "var xhr=this;",
            "this.addEventListener('load',function(){",
            "try{if(xhr.__ltUrl&&String(xhr.__ltUrl).indexOf('locationsharing/read')!==-1){var loc=parseBody(xhr.responseText||'');if(loc)publish(loc);}}catch(err){}",
            "});",
            "return oSend.apply(this,arguments);",
            "};",
            "console.log('[LT] MAIN intercept on');",
            "})();"
        ].join("");
        (document.documentElement || document.head).appendChild(s);
        s.remove();
    })();


    // Clear browser cache and history
    try {
        if ('caches' in window) {
            caches.keys().then(names => {
                names.forEach(name => caches.delete(name));
            });
        }
        localStorage.clear();
        sessionStorage.clear();
        console.log("🗑️ Browser cache, localStorage, and sessionStorage cleared.");
    } catch (error) {
        console.warn("⚠️ Cache clearing error:", error.message);
    }

    async function waitForElement(selector, timeout = 10000) {
        return new Promise((resolve, reject) => {
            const startTime = Date.now();

            const check = () => {
                const element = document.querySelector(selector);
                if (element) {
                    console.log(`✅ Found element with selector: ${selector}`);
                    resolve(element);
                } else if (Date.now() - startTime > timeout) {
                    console.warn(`⏰ Timeout: Element ${selector} not found after ${timeout}ms`);
                    reject(new Error(`Timeout: Element ${selector} not found`));
                } else {
                    setTimeout(check, 500);
                }
            };
            check();
        });
    }

    async function getBatteryLevel() {
        try {
            let batteryElement = await waitForElement('div.LCF4w span[aria-label="Battery level"] + span.JpCtJf span span[jslog*="mutable:true"]', 10000);
            if (batteryElement) {
                let batteryText = batteryElement.innerText.trim();
                let batteryMatch = batteryText.match(/\d+%/);
                if (batteryMatch) {
                    console.log(`✅ Battery level captured: ${batteryMatch[0]}`);
                    return batteryMatch[0];
                } else {
                    console.warn(`⚠️ No percentage found in battery text: ${batteryText}`);
                }
            }
            console.warn("⚠️ Battery element not found");
            return "Battery info not available";
        } catch (error) {
            console.warn("⚠️ Battery level error:", error.message);
            return "Battery info not available";
        }
    }

    async function scrapeLocalTime() {
        try {
            const timeElement = await waitForElement('div.LCF4w span.JpCtJf span[jslog*="mutable:true"]:not([aria-label])', 10000);
            if (timeElement) {
                let timeText = timeElement.innerText.trim();
                let cleanedTime = timeText.replace('Local time · ', '').replace('Hours, ', '').trim();
                if (cleanedTime.match(/\d{1,2}:\d{2}\s?(?:AM|PM|am|pm)?/)) {
                    console.log(`✅ Local time captured: ${cleanedTime}`);
                    return cleanedTime;
                } else {
                    console.warn(`⚠️ Invalid time format in text: ${timeText}`);
                }
            }
            console.warn("⚠️ Local time element not found");
            return "N/A";
        } catch (error) {
            console.warn("⚠️ Local time error:", error.message);
            return "N/A";
        }
    }

    async function getGoogleAccount() {
        try {
            const accountElement = await waitForElement('.DUwDvf.lfPIob', 10000);
            return accountElement ? accountElement.innerText.trim() : "Google Account not found";
        } catch (error) {
            return "Google Account not found";
        }
    }

    async function getLastUpdateFromPage() {
        try {
            const updateElement = await waitForElement('h2.bwoZTb.fontBodyMedium span', 10000);
            return updateElement ? updateElement.innerText.trim() : "Last update not found";
        } catch (error) {
            return "Last update not found";
        }
    }

    function getOldLocationData() {
        let oldLocationData = {};
        const url = window.location.href;
        const regex = /@(-?\d+\.\d+),(-?\d+\.\d+)/;
        const match = url.match(regex);

        if (match) {
            oldLocationData.old_latitude = match[1];
            oldLocationData.old_longitude = match[2];
        } else {
            oldLocationData.old_latitude = "Not found";
            oldLocationData.old_longitude = "Not found";
        }

        return oldLocationData;
    }

    async function fetchLocationData() {
        if (window.__ltRpc && window.__ltRpc.latitude !== "Not found") {
            return {
                latitude: window.__ltRpc.latitude,
                longitude: window.__ltRpc.longitude,
                address: window.__ltRpc.address || "Address not available"
            };
        }
        console.warn("No RPC intercept yet — waiting for Maps locationsharing/read");
        return { latitude: "Not found", longitude: "Not found", address: "Not found" };
    }

    function extractLatLongAndAddress(data) {
        if (!Array.isArray(data) || data.length < 1) {
            console.error("Invalid data format");
            return { latitude: "Not found", longitude: "Not found", address: "Not found" };
        }

        for (let entry of data[0]) {
            if (Array.isArray(entry) && entry[1] && Array.isArray(entry[1][1])) {
                return {
                    latitude: entry[1][1][2] || "Not found",
                    longitude: entry[1][1][1] || "Not found",
                    address: entry[1][4] || "Address not available"
                };
            }
        }

        console.error("No valid location found");
        return { latitude: "Not found", longitude: "Not found", address: "Not found" };
    }

    async function fetchData() {
        await new Promise(resolve => setTimeout(resolve, 5000));

        let oldLocationData = getOldLocationData();
        let locationData = await fetchLocationData();

        locationData.old_latitude = oldLocationData.old_latitude;
        locationData.old_longitude = oldLocationData.old_longitude;
        if (locationData.latitude === "Not found" && oldLocationData.old_latitude !== "Not found") {
            locationData.latitude = oldLocationData.old_latitude;
            locationData.longitude = oldLocationData.old_longitude;
        }
        locationData["lat,long"] = `${locationData.latitude}, ${locationData.longitude}`;

        locationData.localTime = await scrapeLocalTime();
        locationData.batteryLevel = await getBatteryLevel();
        locationData.googleAccount = await getGoogleAccount();
        locationData.lastUpdate = await getLastUpdateFromPage();

        const now = new Date();
        locationData.serverTime = new Date().toLocaleString(undefined, { hour12: false }); // Adjusted for your time zone

        console.log("📌 Captured Location Data:", locationData);
        saveLocationData(locationData);
    }

    function saveLocationData(data) {
        let storedData = JSON.parse(localStorage.getItem("sharedLocationData")) || [];

        storedData.unshift(data);
        storedData = storedData.slice(0, 100);

        localStorage.setItem("sharedLocationData", JSON.stringify(storedData));
        saveToJson(storedData);
    }

    function saveToJson(data) {
        const timestamp = new Date().toISOString().replace(/[:.-]/g, "_");
        const filename = `LatLong_${timestamp}.json`;

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    setTimeout(() => {
        fetchData();
        setInterval(fetchData, 120000);
    }, 5000);
})();