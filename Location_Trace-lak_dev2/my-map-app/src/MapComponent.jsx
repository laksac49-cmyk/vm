import React, { useState, useEffect, useRef, useCallback, memo } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  Tooltip,
  CircleMarker,
  Circle,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useNavigate } from "react-router-dom";
import "./MapComponent.css";

// Custom icon for red balloon pin (first location)
const redPinIcon = L.icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
  iconSize: [15, 25],
  iconAnchor: [7, 25],
  popupAnchor: [1, -20],
  shadowSize: [25, 25],
});

// Custom icon for green balloon pin (end location)
const greenPinIcon = L.icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
  iconSize: [15, 25],
  iconAnchor: [7, 25],
  popupAnchor: [1, -20],
  shadowSize: [25, 25],
});

const blueLocationIcon = L.divIcon({
  html: '<div style="background-color: rgba(0, 0, 255, 0); width: 7px; height: 7px; border: 2px solid blue; border-radius: 50%;"></div>',
  iconSize: [12, 12],
  iconAnchor: [6, 6],
  className: "",
});

const FitBounds = ({ bounds }) => {
  const map = useMap();
  useEffect(() => {
    if (bounds && bounds.length > 0) {
      try {
        map.fitBounds(bounds, { padding: [50, 50] });
      } catch (error) {
        console.error("fitBounds error: ", error);
      }
    }
  }, [bounds, map]);
  return null;
};

const calculateDuration = (startTime, endTime) => {
  const start = new Date(startTime);
  const end = new Date(endTime);
  const diffMs = start - end;
  const diffSeconds = Math.round(diffMs / 1000);
  return `${diffSeconds} seconds`;
};

const getPointAlongPolyline = (coords, t) => {
  if (!coords || coords.length === 0) return { position: null };
  if (coords.length === 1) return { position: coords[0] };
  let totalDist = 0;
  const segDists = [];
  for (let i = 1; i < coords.length; i++) {
    const d = Math.hypot(coords[i][0] - coords[i - 1][0], coords[i][1] - coords[i - 1][1]);
    segDists.push(d);
    totalDist += d;
  }
  let targetDist = totalDist * t;
  let segIndex = 0;
  while (segIndex < segDists.length && targetDist > segDists[segIndex]) {
    targetDist -= segDists[segIndex];
    segIndex++;
  }
  if (segIndex >= segDists.length) segIndex = segDists.length - 1;
  const ratio = targetDist / segDists[segIndex];
  const lat = coords[segIndex][0] + ratio * (coords[segIndex + 1][0] - coords[segIndex][0]);
  const lng = coords[segIndex][1] + ratio * (coords[segIndex + 1][1] - coords[segIndex][1]);
  return { position: [lat, lng] };
};

const showRecords = (records) => {
  const newWindow = window.open("", "Records", "width=800,height=600");
  if (newWindow) {
    const style = `<style>body { font-family: Arial, sans-serif; margin: 20px; } h1 { text-align: center; } table { width: 100%; border-collapse: collapse; margin-top: 20px; } th, td { border: 1px solid #ccc; padding: 8px; text-align: left; } th { background-color: #f2f2f2; } button { margin-top: 10px; padding: 8px 16px; }</style>`;
    newWindow.document.write(`${style}<h1>Location Records</h1>`);
    let table = `<table><tr><th>Google Account</th><th>Address</th><th>Local Time</th><th>Battery Level</th><th>Last Update</th><th>Server Time</th><th>Coordinates</th></tr>`;
    records.forEach((record) => {
      table += `<tr><td>${record.googleAccount}</td><td>${record.address}</td><td>${record.localTime || "N/A"}</td><td>${record.batteryLevel}</td><td>${record.lastUpdate}</td><td>${record.serverTime}</td><td>${record.latitude}, ${record.longitude}</td></tr>`;
    });
    table += "</table><button onclick='window.close()'>Close</button>";
    newWindow.document.write(table);
    newWindow.document.close();
    newWindow.focus();
  }
};

const MapComponent = memo(({ data, fromDate, toDate, latitude, longitude, radius, inCircle }) => {
  const [groups, setGroups] = useState([]);
  const [bounds, setBounds] = useState([]);
  const [pulseT, setPulseT] = useState(0);
  const [isFullScreen, setIsFullScreen] = useState(false);
  const mapRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!data || data.length === 0 || !fromDate || !toDate) {
      console.warn("No data or invalid date range provided to MapComponent:", { data, fromDate, toDate });
      setGroups([]);
      setBounds([]);
      return;
    }

    // Treat fromDate and toDate as server time (UTC)
    const fromDateObj = new Date(fromDate);
    fromDateObj.setSeconds(0, 0);
    const toDateObj = new Date(toDate);
    toDateObj.setSeconds(0, 0);
    const fromUTC = fromDateObj;
    const toUTC = toDateObj;

    console.log("MapComponent filter boundaries:", {
      fromDate,
      toDate,
      fromUTC: fromUTC.toISOString(),
      toUTC: toUTC.toISOString(),
      latitude,
      longitude,
      radius,
      inCircle,
      inputData: data.map(item => ({
        server_time: item.server_time,
        latitude: item.latitude,
        longitude: item.longitude,
        battery_level: item.battery_level,
      })),
    });

    if (isNaN(fromDateObj.getTime()) || isNaN(toDateObj.getTime()) || fromDateObj > toDateObj) {
      console.error("Invalid date range in MapComponent:", { fromDate, toDate });
      setGroups([]);
      setBounds([]);
      return;
    }

    // Filter data by server_time (already filtered by backend)
    let processedData = data
      .filter((item) => {
        if (!item.server_time) {
          console.log("Filtered out item with missing server_time:", item);
          return false;
        }
        const serverTime = new Date(item.server_time);
        if (isNaN(serverTime.getTime())) {
          console.log("Filtered out invalid server_time:", {
            server_time: item.server_time,
            latitude: item.latitude,
            longitude: item.longitude,
          });
          return false;
        }
        return true;
      })
      .map((item) => {
        const latitude = parseFloat(item.latitude);
        const longitude = parseFloat(item.longitude);
        if (isNaN(latitude) || isNaN(longitude) || latitude === null || longitude === null) {
          console.warn("Invalid coordinates for item:", item);
          return null;
        }
        return {
          latitude,
          longitude,
          batteryLevel: item.battery_level ? item.battery_level.toString() : (item.batteryLevel || ""),
          address: item.address,
          localTime: item.local_time || item.localTime || "N/A",
          googleAccount: item.google_account || item.googleAccount,
          serverTime: item.server_time || item.serverTime,
          lastUpdate: item.last_update || item.lastUpdate,
        };
      })
      .filter(item => item !== null);

    processedData = processedData.filter((item) => {
      const lat = item.latitude;
      const lng = item.longitude;
      return lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180;
    });

    if (processedData.length === 0) {
      console.warn("No valid map data after filtering invalid entries.");
      setGroups([]);
      setBounds([]);
      return;
    }

    processedData.sort((a, b) => new Date(b.serverTime) - new Date(a.serverTime));

    const grouped = [];
    let prevKey = "";
    processedData.forEach((item) => {
      const key = `${item.latitude},${item.longitude}`;
      if (key === prevKey && grouped.length > 0) {
        const lastGroup = grouped[grouped.length - 1];
        lastGroup.endServerTime = item.serverTime;
        lastGroup.endLocalTime = item.localTime;
        lastGroup.records.push(item);
      } else {
        grouped.push({
          latitude: item.latitude,
          longitude: item.longitude,
          address: item.address,
          googleAccount: item.googleAccount,
          startServerTime: item.serverTime,
          endServerTime: item.serverTime,
          startLocalTime: item.localTime,
          endLocalTime: item.localTime,
          batteryLevel: item.batteryLevel,
          records: [item],
        });
      }
      prevKey = key;
    });

    grouped.forEach((group) => {
      group.stayDuration = calculateDuration(group.startServerTime, group.endServerTime);
    });

    setGroups(grouped);
    let filteredBounds = grouped
      .map((group) => [group.latitude, group.longitude])
      .filter(
        (coord) =>
          Array.isArray(coord) &&
          coord.length === 2 &&
          !isNaN(coord[0]) &&
          !isNaN(coord[1])
      );
    
    // Include circle center in bounds if provided
    if (latitude && longitude && radius) {
      filteredBounds.push([latitude, longitude]);
    }
    
    setBounds(filteredBounds);
  }, [data, fromDate, toDate, latitude, longitude, radius, inCircle]);

  useEffect(() => {
    const interval = setInterval(() => {
      setPulseT((prev) => (prev + 0.02 > 1 ? 0 : prev + 0.02));
    }, 100);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const map = mapRef.current?.querySelector("div.leaflet-container");
    if (map) {
      map.style.height = isFullScreen ? "100vh" : "400px";
      window.dispatchEvent(new Event("resize"));
    }
  }, [isFullScreen, bounds]);

  const safeBounds = bounds && bounds.length > 0 ? bounds : [[51.505, -0.09]];
  const polylineCoords = groups.map((group) => [group.latitude, group.longitude]);
  const pulseData = polylineCoords.length > 1 ? getPointAlongPolyline(polylineCoords, pulseT) : { position: null };

  const toggleFullScreen = () => {
    if (mapRef.current) {
      if (!document.fullscreenElement) {
        mapRef.current.requestFullscreen().then(() => {
          setIsFullScreen(true);
          const map = mapRef.current.querySelector("div.leaflet-container");
          if (map) {
            map.style.width = "100vw";
            map.style.height = "100vh";
            window.dispatchEvent(new Event("resize"));
          }
        });
      } else {
        document.exitFullscreen().then(() => {
          setIsFullScreen(false);
          const map = mapRef.current.querySelector("div.leaflet-container");
          if (map) {
            map.style.width = "";
            map.style.height = "400px";
            window.dispatchEvent(new Event("resize"));
          }
        });
      }
    }
  };

  return (
    <div className={`map-container ${isFullScreen ? "fullscreen" : ""}`} ref={mapRef}>
      <button className="fullscreen-button" onClick={toggleFullScreen}>
        {isFullScreen ? "Exit Full Screen" : "Maximize"}
      </button>
      {groups?.length === 0 ? (
        <div className="map-loading">No Data To Show In Database</div>
      ) : (
        <MapContainer bounds={safeBounds} className="leaflet-map">
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          <FitBounds bounds={safeBounds} />
          {groups?.map((group, idx) => {
            const tooltipText = `location ${idx + 1}`;
            const googleMapsUrl = `https://www.google.com/maps?q=${group.latitude},${group.longitude}`;
            const isFirst = idx === 0;
            const isLast = idx === groups.length - 1;
            const markerIcon = isFirst ? redPinIcon : isLast ? greenPinIcon : blueLocationIcon;
            return (
              <Marker
                key={idx}
                position={[group.latitude, group.longitude]}
                icon={markerIcon}
              >
                <Tooltip permanent={false} direction="top" opacity={0.9}>
                  {tooltipText}
                </Tooltip>
                <Popup>
                  <div style={{ margin: 0, padding: 0 }}>
                    <p style={{ margin: 0, padding: "2px 0" }}><strong>Google Account:</strong> {group.googleAccount}</p>
                    <p style={{ margin: 0, padding: "2px 0" }}><strong>Address:</strong> {group.address}</p>
                    <p style={{ margin: 0, padding: "2px 0" }}><strong>Coordinates:</strong> {group.latitude}, {group.longitude}</p>
                    <p style={{ margin: 0, padding: "2px 0" }}><strong>Start Local Time:</strong> {group.startLocalTime || "N/A"}</p>
                    <p style={{ margin: 0, padding: "2px 0" }}><strong>End Local Time:</strong> {group.endLocalTime || "N/A"}</p>
                    <p style={{ margin: 0, padding: "2px 0" }}><strong>Battery Level:</strong> {group.batteryLevel}</p>
                    <p style={{ margin: 0, padding: "2px 0" }}><strong>Start Server Time:</strong> {group.startServerTime}</p>
                    <p style={{ margin: 0, padding: "2px 0" }}><strong>End Server Time:</strong> {group.endServerTime}</p>
                    <p style={{ margin: 0, padding: "2px 0" }}><strong>Stay Duration:</strong> {group.stayDuration}</p>
                    <button
                      onClick={() => showRecords(group.records)}
                      style={{ padding: "6px 12px", backgroundColor: "#4CAF50", color: "white", border: "none", borderRadius: "4px", cursor: "pointer", margin: "4px 0 0 0" }}
                    >
                      Show All Records
                    </button>
                    <br />
                    <a href={googleMapsUrl} target="_blank" rel="noopener noreferrer" style={{ margin: "4px 0 0 0" }}>
                      Open in Google Maps
                    </a>
                  </div>
                </Popup>
              </Marker>
            );
          })}
          {polylineCoords.length > 1 && (
            <Polyline positions={polylineCoords} color="blue" />
          )}
          {pulseData.position && (
            <CircleMarker
              center={pulseData.position}
              radius={5 + 5 * Math.sin(pulseT * 2 * Math.PI)}
              color="blue"
              fillColor="blue"
              fillOpacity={0.5}
            />
          )}
          {latitude && longitude && radius && (
            <Circle
              center={[latitude, longitude]}
              radius={parseFloat(radius)}
              color="red"
              fillColor="red"
              fillOpacity={0.2}
            />
          )}
        </MapContainer>
      )}
    </div>
  );
});

export default MapComponent;