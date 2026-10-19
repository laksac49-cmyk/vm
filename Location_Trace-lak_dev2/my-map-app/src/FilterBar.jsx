import React, { useState, useEffect } from "react";
import axios from "axios";
import "./FilterBar.css";

const FilterBar = ({ onApply, onClearCircle }) => {
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

  const [from, setFrom] = useState(formatDateLocal(prior));
  const [to, setTo] = useState(formatDateLocal(now));
  const [selectedAccount, setSelectedAccount] = useState("All");
  const [accounts, setAccounts] = useState([]);
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [radius, setRadius] = useState("");
  const [inCircle, setInCircle] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "/api";
        const response = await axios.get(`${API_BASE_URL}/location-data`, {
          headers: { Authorization: `Bearer ${localStorage.getItem("token") || ""}` },
        });
        const accounts = [...new Set(response.data.map(item => item.google_account).filter(Boolean))];
        setAccounts(["All", ...accounts]);
      } catch (error) {
        console.error("Error fetching accounts:", error.response?.data || error.message);
        if (error.response && error.response.status === 401) {
          window.location.href = "/"; // Redirect to login
        } else if (error.response && error.response.status === 502) {
          console.error("502 Bad Gateway - Check backend server or proxy configuration:", error);
        }
      }
    };
    fetchData();
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    const fromDate = new Date(from);
    const toDate = new Date(to);
    if (fromDate > toDate) {
      console.warn("Invalid date range: fromDate is after toDate", { fromDate: fromDate.toISOString(), toDate: toDate.toISOString() });
      return;
    }
    const fromUTC = fromDate.toISOString();
    const toUTC = toDate.toISOString();
    const lat = latitude ? parseFloat(latitude) : null;
    const lon = longitude ? parseFloat(longitude) : null;
    const rad = radius ? parseFloat(radius) : null;
    console.log("Applying filters with from_time:", fromUTC, "to_time:", toUTC, "googleAccount:", selectedAccount === "All" ? "" : selectedAccount, "latitude:", lat, "longitude:", lon, "radius:", rad, "inCircle:", inCircle);
    onApply({
      from: fromUTC,
      to: toUTC,
      googleAccount: selectedAccount === "All" ? "" : selectedAccount,
      latitude: lat,
      longitude: lon,
      radius: rad,
      inCircle
    });
  };

  const handleClearCircle = () => {
    setLatitude("");
    setLongitude("");
    setRadius("");
    setInCircle(true);
    onClearCircle();
    console.log("Cleared circle parameters");
  };

  const openGridAnalysisWindow = () => {
    const gridWindow = window.open("/grid-analysis", "GridAnalysis", "width=1000,height=800,resizable=yes");
    if (gridWindow) {
      gridWindow.focus();
    }
  };

  return (
    <div className="filter-bar">
      <form onSubmit={handleSubmit}>
        <div className="filter-group">
          <label>From (Local Time):</label>
          <input type="datetime-local" value={from} onChange={(e) => setFrom(e.target.value)} />
        </div>
        <div className="filter-group">
          <label>To (Local Time):</label>
          <input type="datetime-local" value={to} onChange={(e) => setTo(e.target.value)} />
        </div>
        <div className="filter-group">
          <label>Google Account:</label>
          <select value={selectedAccount} onChange={(e) => setSelectedAccount(e.target.value)}>
            {accounts.map((account, idx) => (
              <option key={idx} value={account}>{account}</option>
            ))}
          </select>
        </div>
        <div className="filter-group">
          <label>Latitude:</label>
          <input type="number" step="any" value={latitude} onChange={(e) => setLatitude(e.target.value)} placeholder="e.g., 6.9271" />
        </div>
        <div className="filter-group">
          <label>Longitude:</label>
          <input type="number" step="any" value={longitude} onChange={(e) => setLongitude(e.target.value)} placeholder="e.g., 79.8612" />
        </div>
        <div className="filter-group">
          <label>Radius (meters):</label>
          <input type="number" step="any" value={radius} onChange={(e) => setRadius(e.target.value)} placeholder="e.g., 1000" />
        </div>
        <div className="filter-group">
          <label><input type="checkbox" checked={inCircle} onChange={(e) => setInCircle(e.target.checked)} /> Inside Circle (unchecked for Outside)</label>
        </div>
        <button type="submit">Check Details</button>
        <button type="button" onClick={handleClearCircle}>Clear Circle</button>
        <button type="button" onClick={openGridAnalysisWindow}>Grid Analysis</button>
      </form>
    </div>
  );
};

export default FilterBar;