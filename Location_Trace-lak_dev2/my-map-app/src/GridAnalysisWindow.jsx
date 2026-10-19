import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./GridAnalysisWindow.css";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "/api";

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

const GridAnalysisWindow = () => {
  const now = new Date();
  const prior = new Date(now.getTime() - 48 * 60 * 60 * 1000);
  const formatDateLocal = (date) => {
    return date.toLocaleString("sv-SE", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).replace(" ", "T");
  };

  const [formData, setFormData] = useState({
    center_latitude: "",
    center_longitude: "",
    distance_north: "",
    distance_south: "",
    distance_east: "",
    distance_west: "",
    grid_size: "",
    start_date: formatDateLocal(prior),
    end_date: formatDateLocal(now),
  });
  const [gridData, setGridData] = useState([]);
  const [bounds, setBounds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [isFullScreen, setIsFullScreen] = useState(false);
  const mapRef = useRef(null);

  useEffect(() => {
    const fetchGridParams = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/grid-params`, {
          headers: { Authorization: `Bearer ${localStorage.getItem("token") || ""}` },
        });
        console.log("Raw API response from /grid-params:", response.data);
        const params = response.data;
        if (params && typeof params === "object" && params !== null) {
          setFormData({
            center_latitude: params.center_latitude != null && !isNaN(params.center_latitude) ? params.center_latitude.toString() : "",
            center_longitude: params.center_longitude != null && !isNaN(params.center_longitude) ? params.center_longitude.toString() : "",
            distance_north: params.distance_north != null && !isNaN(params.distance_north) ? params.distance_north.toString() : "",
            distance_south: params.distance_south != null && !isNaN(params.distance_south) ? params.distance_south.toString() : "",
            distance_east: params.distance_east != null && !isNaN(params.distance_east) ? params.distance_east.toString() : "",
            distance_west: params.distance_west != null && !isNaN(params.distance_west) ? params.distance_west.toString() : "",
            grid_size: params.grid_size != null && !isNaN(params.grid_size) ? params.grid_size.toString() : "",
            start_date: params.start_date ? formatDateLocal(new Date(params.start_date)) : formatDateLocal(prior),
            end_date: formatDateLocal(new Date()), // Set to current browser local time
          });
          setMessage("Default parameters loaded from database");
        } else {
          console.warn("Invalid or empty response from /grid-params, using fallback defaults");
          setMessage("No valid parameters from database, using fallback defaults");
        }
      } catch (error) {
        console.error("Error fetching grid parameters:", error.response?.data || error.message);
        setMessage("Error loading default parameters: using fallback defaults");
      }
    };
    fetchGridParams();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleRunAnalysis = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");
    setGridData([]);
    setBounds([]);

    try {
      const startDate = new Date(formData.start_date);
      const endDate = new Date(); // Set end_date to current browser local time
      if (startDate > endDate) {
        setMessage("Error: Start date must be before end date");
        setLoading(false);
        return;
      }

      const numericFields = ["center_latitude", "center_longitude", "distance_north", "distance_south", "distance_east", "distance_west", "grid_size"];
      for (const field of numericFields) {
        if (formData[field] === "" || isNaN(parseFloat(formData[field]))) {
          setMessage(`Error: ${field.replace('_', ' ')} must be a valid number`);
          setLoading(false);
          return;
        }
      }

      const centerLat = parseFloat(formData.center_latitude);
      const centerLon = parseFloat(formData.center_longitude);
      const gridSize = parseFloat(formData.grid_size);

      if (centerLat < -90 || centerLat > 90) {
        setMessage("Error: Center latitude must be between -90 and 90");
        setLoading(false);
        return;
      }
      if (centerLon < -180 || centerLon > 180) {
        setMessage("Error: Center longitude must be between -180 and 180");
        setLoading(false);
        return;
      }
      if (parseFloat(formData.distance_north) < 0 || parseFloat(formData.distance_south) < 0 ||
          parseFloat(formData.distance_east) < 0 || parseFloat(formData.distance_west) < 0) {
        setMessage("Error: Distance values must be non-negative");
        setLoading(false);
        return;
      }
      if (gridSize <= 0) {
        setMessage("Error: Grid size must be positive");
        setLoading(false);
        return;
      }

      const params = {
        center_latitude: centerLat,
        center_longitude: centerLon,
        distance_north: parseFloat(formData.distance_north),
        distance_south: parseFloat(formData.distance_south),
        distance_east: parseFloat(formData.distance_east),
        distance_west: parseFloat(formData.distance_west),
        grid_size: gridSize,
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
      };

      const response = await axios.post(`${API_BASE_URL}/grid-analysis`, params, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token") || ""}` },
      });
      console.log("Raw API response from /grid-analysis:", response.data);

      const data = response.data.grid_visit_counts?.grid_visit_counts;
      if (!Array.isArray(data)) {
        throw new Error("Invalid data format: grid_visit_counts.grid_visit_counts is not an array. Raw response: " + JSON.stringify(response.data));
      }
      setGridData(data || []);

      const newBounds = data.map(row => [row[1], row[2]]); // center_latitude, center_longitude
      setBounds(newBounds.length > 0 ? newBounds : [[centerLat, centerLon]]);

      setMessage("Job Completed Successfully");
    } catch (error) {
      console.error("Error running grid analysis:", error.message);
      setMessage(`Error: ${error.message || "Failed to fetch grid data"}`);
      setGridData([]);
    } finally {
      setLoading(false);
    }
  };

  const getGridDetailsUrl = (row) => {
    const centerLat = row[1]; // center_latitude
    const centerLon = row[2]; // center_longitude
    const startDate = new Date(row[8]).toISOString();
    const endDate = new Date(row[9]).toISOString();
    const gridSize = parseFloat(formData.grid_size) || 1000; // Use grid_size as radius

    const queryParams = new URLSearchParams({
      from: startDate,
      to: endDate,
      latitude: centerLat,
      longitude: centerLon,
      radius: gridSize,
      inCircle: "true",
    }).toString();

    return `/grid-details/${row[0]}?${queryParams}`;
  };

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
        }).catch(err => console.error("Fullscreen request failed:", err));
      } else {
        document.exitFullscreen().then(() => {
          setIsFullScreen(false);
          const map = mapRef.current.querySelector("div.leaflet-container");
          if (map) {
            map.style.width = "";
            map.style.height = "400px";
            window.dispatchEvent(new Event("resize"));
          }
        }).catch(err => console.error("Exit fullscreen failed:", err));
      }
    }
  };

  const maxVisits = gridData.length > 0 ? Math.max(...gridData.map(row => row[7] || 1)) : 1; // visit_count
  const minRadius = 5;
  const maxRadius = 20;

  const validGridData = Array.isArray(gridData) ? gridData.filter(row => 
    row[1] != null && row[2] != null && !isNaN(row[1]) && !isNaN(row[2]) && Array.isArray(row) && row.length >= 8
  ) : [];

  return (
    <div className="grid-analysis-container" ref={mapRef}>
      <h2>Grid Analysis</h2>
      <form onSubmit={handleRunAnalysis} className="grid-form">
        <div className="input-group">
          <label>Center Latitude:</label>
          <input type="number" step="any" name="center_latitude" value={formData.center_latitude} onChange={handleInputChange} placeholder="e.g., 6.9271" required />
        </div>
        <div className="input-group">
          <label>Center Longitude:</label>
          <input type="number" step="any" name="center_longitude" value={formData.center_longitude} onChange={handleInputChange} placeholder="e.g., 79.8612" required />
        </div>
        <div className="input-group">
          <label>Distance North (meters):</label>
          <input type="number" step="any" name="distance_north" value={formData.distance_north} onChange={handleInputChange} placeholder="e.g., 20000" required />
        </div>
        <div className="input-group">
          <label>Distance South (meters):</label>
          <input type="number" step="any" name="distance_south" value={formData.distance_south} onChange={handleInputChange} placeholder="e.g., 20000" required />
        </div>
        <div className="input-group">
          <label>Distance East (meters):</label>
          <input type="number" step="any" name="distance_east" value={formData.distance_east} onChange={handleInputChange} placeholder="e.g., 20000" required />
        </div>
        <div className="input-group">
          <label>Distance West (meters):</label>
          <input type="number" step="any" name="distance_west" value={formData.distance_west} onChange={handleInputChange} placeholder="e.g., 20000" required />
        </div>
        <div className="input-group">
          <label>Grid Size (meters):</label>
          <input type="number" step="any" name="grid_size" value={formData.grid_size} onChange={handleInputChange} placeholder="e.g., 1000" required />
        </div>
        <div className="input-group">
          <label>Start Date:</label>
          <input type="datetime-local" name="start_date" value={formData.start_date} onChange={handleInputChange} required />
        </div>
        <div className="input-group">
          <label>End Date:</label>
          <input type="datetime-local" name="end_date" value={formData.end_date} onChange={handleInputChange} required />
        </div>
        <button type="submit" disabled={loading}>{loading ? "Loading..." : "Run Analysis"}</button>
      </form>
      {message && <p className="message">{message}</p>}
      {Array.isArray(gridData) && gridData.length > 0 && (
        <div className="analysis-results">
          <table className="grid-table">
            <thead>
              <tr>
                <th>Center Latitude</th>
                <th>Center Longitude</th>
                <th>Bottom Left Latitude</th>
                <th>Bottom Left Longitude</th>
                <th>Top Right Latitude</th>
                <th>Top Right Longitude</th>
                <th>Visit Count</th>
                <th>Start Date</th>
                <th>End Date</th>
                <th>Created At</th>
                <th>View Details</th>
              </tr>
            </thead>
            <tbody>
              {gridData.map((row, index) => (
                <tr key={index}>
                  <td>{row[1] || "N/A"}</td>
                  <td>{row[2] || "N/A"}</td>
                  <td>{row[3] || "N/A"}</td>
                  <td>{row[4] || "N/A"}</td>
                  <td>{row[5] || "N/A"}</td>
                  <td>{row[6] || "N/A"}</td>
                  <td>{row[7] || "0"}</td>
                  <td>{row[8] || "N/A"}</td>
                  <td>{row[9] || "N/A"}</td>
                  <td>{row[10] || "N/A"}</td>
                  <td>
                    <a
                      href={getGridDetailsUrl(row)}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ padding: "5px 10px", backgroundColor: "#3498db", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer", textDecoration: "none" }}
                    >
                      View Map
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="map-container">
            <button className="fullscreen-button" onClick={toggleFullScreen}>
              {isFullScreen ? "Exit Full Screen" : "Maximize"}
            </button>
            <MapContainer center={bounds.length > 0 ? bounds[0] : [0, 0]} zoom={13} className="leaflet-map">
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' />
              <FitBounds bounds={bounds} />
              {validGridData.map((row, index) => {
                const radius = minRadius + ((row[7] || 1) / maxVisits) * (maxRadius - minRadius);
                return (
                  <CircleMarker
                    key={index}
                    center={[row[1] || 0, row[2] || 0]}
                    radius={radius}
                    color="blue"
                    fillColor="blue"
                    fillOpacity={0.5}
                  >
                    <Popup>
                      <div>
                        <p><strong>Center Latitude:</strong> {row[1] || "N/A"}</p>
                        <p><strong>Center Longitude:</strong> {row[2] || "N/A"}</p>
                        <p><strong>Visit Count:</strong> {row[7] || "0"}</p>
                        <p><strong>Start Date:</strong> {row[8] || "N/A"}</p>
                        <p><strong>End Date:</strong> {row[9] || "N/A"}</p>
                        <p>
                          <a
                            href={getGridDetailsUrl(row)}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ padding: "5px 10px", backgroundColor: "#3498db", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer", textDecoration: "none" }}
                          >
                            View Map
                          </a>
                        </p>
                      </div>
                    </Popup>
                  </CircleMarker>
                );
              })}
            </MapContainer>
          </div>
        </div>
      )}
    </div>
  );
};

export default GridAnalysisWindow;