// working.js
(function() {
    function checkAndStoreData() {
        // Extract information
        const addressElement = document.querySelector('.DkEaL');
        const address = addressElement ? addressElement.innerText : 'Address not found';

        const batteryElement = document.querySelector('.LCF4w span[jslog*="mutable:true"]');
        const batteryPercentage = batteryElement ? batteryElement.innerText : 'Battery percentage not found';

        const timeElement = document.querySelector('.bwoZTb.fontBodyMedium span');
        const time = timeElement ? timeElement.innerText : 'Time not found';

        const localTimeElement = document.querySelector('span[jslog*="mutable:true"]');
        const localTime = localTimeElement ? localTimeElement.innerText : 'Local time not found';

        const LTime = document.querySelector('div[aria-label*="Hours"]');        
        const LocalTime = LTime ? LTime.getAttribute('aria-label') : 'Local time not found';    

        const batteryDiv = document.querySelector('div[aria-label*="Battery level"]');        
        const batteryLabel = batteryDiv ? batteryDiv.getAttribute('aria-label') : 'Battery label not found';    

        // Log the extracted information to the console
        console.log('Address:', address);
        console.log('Battery Percentage:', batteryPercentage);
        console.log('Time:', time);
        console.log('Local Time:', localTime);
        console.log('LT:', LocalTime);
        console.log('Battery Label:', batteryLabel);

        // Append the result to localStorage
        let data = JSON.parse(localStorage.getItem('data')) || [];
        data.push({ 
            timestamp: new Date().toISOString(), 
            address, 
            batteryPercentage, 
            time, 
            localTime: LocalTime, 
            batteryLabel 
        });
        localStorage.setItem('data', JSON.stringify(data));
    }

    // Run the function immediately
    checkAndStoreData();
    
    // Set interval to run the function every 2 minutes (120000 milliseconds)
    setInterval(checkAndStoreData, 120000);
})();

let batteryData = JSON.parse(localStorage.getItem('data'));
console.log(batteryData);

let batteryData = JSON.parse(localStorage.getItem('data'));
console.log(batteryData);

// Create a JSON string from the data
let dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(batteryData));

// Create a download link
let downloadAnchorNode = document.createElement('a');
downloadAnchorNode.setAttribute("href", dataStr);
downloadAnchorNode.setAttribute("download", "batteryData.json");

// Append the download link to the document body (necessary for Firefox)
document.body.appendChild(downloadAnchorNode);

// Trigger the download by simulating a click on the download link
downloadAnchorNode.click();

// Remove the download link from the document
downloadAnchorNode.remove();