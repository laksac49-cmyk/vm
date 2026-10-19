import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { BrowserRouter as Router, Routes, Route, Navigate, useParams, useLocation } from "react-router-dom";
import Login from "./Login";
import BatteryChart from "./BatteryChart";
import MapComponent from "./MapComponent";
import FilterBar from "./FilterBar";
import GridAnalysisWindow from "./GridAnalysisWindow";
import "./App.css";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "/api";
let refreshTimeout;

const setupAxiosInterceptors = (setToken) => {
  axios.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem("token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  axios.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;
        try {
          const username = localStorage.getItem("username");
          const password = localStorage.getItem("password");
          if (!username || !password) {
            console.warn("Username or password not found for token refresh. Redirecting to login.");
            localStorage.clear();
            setToken("");
            window.location.href = "/login";
            return Promise.reject(error);
          }
          console.log("Attempting to refresh token...");
          const newAccessToken = await refreshToken(username, password);
          localStorage.setItem("token", newAccessToken);
          setToken(newAccessToken);
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return axios(originalRequest);
        } catch (refreshError) {
          console.error("Token refresh failed, redirecting to login:", refreshError);
          localStorage.clear();
          setToken("");
          window.location.href = "/login";
          return Promise.reject(refreshError);
        }
      }
      return Promise.reject(error);
    }
  );
};

const refreshToken = async (username, password) => {
  try {
    console.log("API_BASE_URL in refreshToken:", API_BASE_URL);
    const response = await axios.post(
      `${API_BASE_URL}/login`,
      new URLSearchParams({ username, password }),
      { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
    );
    const { access_token } = response.data;
    localStorage.setItem("token", access_token);
    return access_token;
  } catch (error) {
    console.error("Token refresh failed:", error.response?.data || error.message);
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    localStorage.removeItem("password");
    throw error;
  }
};

const HomeContent = ({ initialFilters }) => {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [mapData, setMapData] = useState([]);
  const [batteryData, setBatteryData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [googleAccounts, setGoogleAccounts] = useState([]);
  
  const [filters, setFilters] = useState(initialFilters);

  useEffect(() => {
    setupAxiosInterceptors(setToken);
  }, [setToken]);

  const scheduleTokenRefresh = useCallback(() => {
    if (refreshTimeout) clearTimeout(refreshTimeout);
    const username = localStorage.getItem("username");
    const password = localStorage.getItem("password");
    const refreshInterval = (30 - 2) * 60 * 1000;

    refreshTimeout = setTimeout(async () => {
      console.log("Attempting scheduled token refresh...");
      if (username && password) {
        try {
          const newAccessToken = await refreshToken(username, password);
          setToken(newAccessToken);
          console.log("Scheduled token refreshed successfully.");
          scheduleTokenRefresh();
        } catch (error) {
          console.error("Scheduled token refresh failed:", error);
        }
      } else {
        console.warn("Cannot perform scheduled token refresh: username or password missing.");
        localStorage.clear();
        setToken("");
        window.location.href = "/login";
      }
    }, [refreshInterval]);
  }, [setToken]);

  useEffect(() => {
    if (token) {
      scheduleTokenRefresh();
      fetchAccountsAndData();
    }
    return () => {
      if (refreshTimeout) clearTimeout(refreshTimeout);
    };
  }, [token, scheduleTokenRefresh, filters]);

  const fetchAccountsAndData = useCallback(async () => {
    setLoading(true);
    setMapData([]);
    setBatteryData([]);
    try {
      const { from, to, googleAccount, latitude, longitude, radius, inCircle } = filters;
      if (!from || !to) {
        console.warn("No date range provided, skipping data fetch");
        setLoading(false);
        return;
      }

      const fromDateObj = new Date(from);
      const toDateObj = new Date(to);

      if (isNaN(fromDateObj.getTime()) || isNaN(toDateObj.getTime()) || fromDateObj > toDateObj) {
        console.error("Invalid date range selected:", { from, to });
        setMapData([]);
        setBatteryData([]);
        setLoading(false);
        return;
      }

      const params = { from_time: from, to_time: to };
      if (googleAccount) params.google_account = googleAccount;
      if (latitude !== null) params.latitude = latitude;
      if (longitude !== null) params.longitude = longitude;
      if (radius !== null) params.radius = radius;
      if (latitude !== null && longitude !== null && radius !== null) params.in_circle = inCircle;

      console.log("API Request:", {
        url: `${API_BASE_URL}/location-data`,
        params,
        token: localStorage.getItem("token") || "No token",
      });

      const dataResponse = await axios.get(`${API_BASE_URL}/location-data`, { params });

      console.log("Raw backend response:", JSON.stringify(dataResponse.data, null, 2));

      console.log("Backend response data:", dataResponse.data.map(item => ({
        server_time: item.server_time,
        battery_level: item.battery_level,
        latitude: item.latitude,
        longitude: item.longitude,
        google_account: item.google_account,
        address: item.address,
        local_time: item.local_time,
        last_update: item.last_update,
      })));

      const uniqueAccounts = [...new Set(dataResponse.data.map(item => item.google_account).filter(Boolean))];
      setGoogleAccounts(["", ...uniqueAccounts]);
      setMapData(dataResponse.data);
      setBatteryData(dataResponse.data);
    } catch (error) {
      console.error("Error fetching location data:", {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message,
        url: error.request?.responseURL,
      });
      setMapData([]);
      setBatteryData([]);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const handleApplyFilters = (newFilters) => {
    setFilters(newFilters);
  };

  const handleClearCircle = () => {
    setFilters(prev => ({
      ...prev,
      latitude: null,
      longitude: null,
      radius: null,
      inCircle: true,
    }));
  };

  const onLoginSuccess = (newToken, username, password) => {
    localStorage.setItem("token", newToken);
    localStorage.setItem("username", username);
    localStorage.setItem("password", password);
    setToken(newToken);
  };

  const handleLogout = () => {
    localStorage.clear();
    setToken("");
    window.location.href = "/login";
  };

  return (
    <div className="app-container">
      <div className="navbar">
        <h1>Location Tracker</h1>
        {token && <button onClick={handleLogout} className="logout-button">Logout</button>}
      </div>
      <div className="main-content">
        {token ? (
          <>
            <FilterBar onApply={handleApplyFilters} onClearCircle={handleClearCircle} />
            {loading ? (
              <div className="loading">Loading...</div>
            ) : mapData.length === 0 && batteryData.length === 0 ? (
              <div className="no-data">No Data To Show In Database</div>
            ) : (
              <>
                <h2>Location Tracker Map</h2>
                <MapComponent
                  data={mapData}
                  fromDate={filters.from}
                  toDate={filters.to}
                  latitude={filters.latitude}
                  longitude={filters.longitude}
                  radius={filters.radius}
                  inCircle={filters.inCircle}
                />
                <h2>Battery Level Chart</h2>
                <BatteryChart data={batteryData} fromDate={filters.from} toDate={filters.to} />
              </>
            )}
          </>
        ) : (
          <Navigate to="/login" />
        )}
      </div>
    </div>
  );
};

const GridDetails = () => {
  const { gridId } = useParams();
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);

  const initialFilters = {
    from: queryParams.get("from") || new Date(new Date().getTime() - 48 * 60 * 60 * 1000).toISOString(),
    to: queryParams.get("to") || new Date().toISOString(),
    googleAccount: "",
    latitude: queryParams.get("latitude") ? parseFloat(queryParams.get("latitude")) : null,
    longitude: queryParams.get("longitude") ? parseFloat(queryParams.get("longitude")) : null,
    radius: queryParams.get("radius") ? parseFloat(queryParams.get("radius")) : null,
    inCircle: queryParams.get("inCircle") === "true",
  };

  return <HomeContent initialFilters={initialFilters} />;
};

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login onLoginSuccess={(token, username, password) => {
          localStorage.setItem("token", token);
          localStorage.setItem("username", username);
          localStorage.setItem("password", password);
          window.location.href = "/";
        }} />} />
        <Route path="/grid-analysis" element={<GridAnalysisWindow />} />
        <Route path="/grid-details/:gridId" element={<GridDetails />} />
        <Route path="/" element={<HomeContent initialFilters={{
          from: new Date(new Date().getTime() - 48 * 60 * 60 * 1000).toISOString(),
          to: new Date().toISOString(),
          googleAccount: "",
          latitude: null,
          longitude: null,
          radius: null,
          inCircle: true,
        }} />} />
      </Routes>
    </Router>
  );
}

export default App;