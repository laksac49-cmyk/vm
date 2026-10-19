import React, { useState, useEffect, useRef } from "react";
import Plot from "react-plotly.js";
import axios from "axios";
import "./BatteryChart.css";

const fetchLocalTime = async (serverTime, googleAccount, setHoverLocalTime) => {
  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "/api";
  try {
    const response = await axios.get(`${API_BASE_URL}/local-time`, {
      headers: { Authorization: `Bearer ${localStorage.getItem("token") || ""}` },
      params: { server_time: serverTime, google_account: googleAccount },
    });
    const localTime = response.data.local_time || "N/A";
    setHoverLocalTime((prev) => ({ ...prev, [serverTime]: localTime }));
  } catch (error) {
    console.error("Error fetching local time:", error.response?.data || error.message);
    setHoverLocalTime((prev) => ({ ...prev, [serverTime]: "N/A" }));
  }
};

const BatteryChart = ({ data, fromDate, toDate }) => {
  const [chartData, setChartData] = useState({ x: [], y: [], hover: [], data: [] });
  const [maxBattery, setMaxBattery] = useState(0);
  const [loading, setLoading] = useState(true);
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [hoverLocalTime, setHoverLocalTime] = useState({});
  const chartRef = useRef(null);

  useEffect(() => {
    setLoading(true);
    if (!data || data.length === 0 || !fromDate || !toDate) {
      console.warn("No data or invalid date range provided to BatteryChart:", { data, fromDate, toDate });
      setChartData({ x: [], y: [], hover: [], data: [] });
      setMaxBattery(0);
      setLoading(false);
      return;
    }

    // Treat fromDate and toDate as server time (UTC)
    const fromDateObj = new Date(fromDate);
    fromDateObj.setSeconds(0, 0);
    const toDateObj = new Date(toDate);
    toDateObj.setSeconds(0, 0);
    const fromUTC = fromDateObj;
    const toUTC = toDateObj;

    console.log("BatteryChart filter boundaries:", {
      fromDate,
      toDate,
      fromUTC: fromUTC.toISOString(),
      toUTC: toUTC.toISOString(),
      inputData: data.map(item => ({
        server_time: item.server_time,
        battery_level: item.battery_level,
      })),
    });

    if (isNaN(fromDateObj.getTime()) || isNaN(toDateObj.getTime()) || fromDateObj > toDateObj) {
      console.error("Invalid date range in BatteryChart:", { fromDate, toDate });
      setChartData({ x: [], y: [], hover: [], data: [] });
      setMaxBattery(0);
      setLoading(false);
      return;
    }

    let validData = data
      .filter((item) => {
        if (!item.server_time || !item.battery_level) {
          console.log("Filtered out item with missing server_time or battery_level:", item);
          return false;
        }

        const battStr = item.battery_level.toString().trim().replace("%", "");
        const isValidBattery = battStr !== "Battery info not available" && battStr !== "N/A" && !isNaN(parseFloat(battStr));
        if (!isValidBattery) {
          console.log("Filtered out invalid battery_level:", {
            server_time: item.server_time,
            battery_level: battStr,
          });
          return false;
        }

        const serverTime = new Date(item.server_time);
        if (isNaN(serverTime.getTime())) {
          console.log("Filtered out invalid server_time:", {
            server_time: item.server_time,
            battery_level: battStr,
          });
          return false;
        }

        const isWithinRange = serverTime >= fromUTC && serverTime <= toUTC;
        if (!isWithinRange) {
          console.log("Filtered out data point outside time range:", {
            server_time: item.server_time,
            serverTimeParsed: serverTime.toISOString(),
            fromUTC: fromUTC.toISOString(),
            toUTC: toUTC.toISOString(),
            battery_level: battStr,
          });
        }
        return isWithinRange;
      })
      .map((item) => {
        const battStr = item.battery_level.toString().trim().replace("%", "");
        const numericValue = parseFloat(battStr) || 0;
        return { ...item, _batteryLevel: numericValue };
      })
      .filter((item) => item._batteryLevel >= 0 && item._batteryLevel <= 100);

    if (validData.length === 0) {
      console.warn("No valid battery data after filtering invalid entries or server time range.");
      setChartData({ x: [], y: [], hover: [], data: [] });
      setMaxBattery(0);
      setLoading(false);
      return;
    }

    validData = validData.map((item) => ({
      ...item,
      localTime: item.local_time || item.localTime || "N/A",
      // Use Date object directly for Plotly compatibility
      displayTime: item.server_time ? new Date(item.server_time + "Z") : null,
    }));

    validData.sort((a, b) => new Date(a.server_time) - new Date(b.server_time));

    const xValues = validData.map((item) => item.displayTime).filter((x) => x !== null);
    const yValues = validData.map((item) => item._batteryLevel);
    const hoverText = validData.map((item) => `Server Time: ${item.server_time || "N/A"}`);

    if (yValues.length > 0) {
      setMaxBattery(Math.max(...yValues));
    } else {
      setMaxBattery(0);
    }

    console.log("Valid data after filtering:", validData.map(item => ({
      server_time: item.server_time,
      displayTime: item.displayTime,
      battery_level: item._batteryLevel,
    })));

    setChartData({ x: xValues, y: yValues, hover: hoverText, data: validData });
    setLoading(false);
  }, [data, fromDate, toDate]);

  const toggleFullScreen = () => {
    if (chartRef.current) {
      if (!document.fullscreenElement) {
        chartRef.current.requestFullscreen().then(() => {
          setIsFullScreen(true);
          chartRef.current.style.width = "100vw";
          chartRef.current.style.height = "100vh";
          window.dispatchEvent(new Event("resize"));
        });
      } else {
        document.exitFullscreen().then(() => {
          setIsFullScreen(false);
          chartRef.current.style.width = "";
          chartRef.current.style.height = "400px";
          window.dispatchEvent(new Event("resize"));
        });
      }
    }
  };

  if (loading) {
    return <div className="chart-loading">Loading...</div>;
  }

  if (chartData.x.length === 0 || chartData.y.length === 0) {
    console.warn("Chart not rendered: Empty x or y data - x:", chartData.x, "y:", chartData.y);
    return (
      <div className="chart-loading">
        No Data To Show In Database
      </div>
    );
  }

  console.log("Rendering chart with data - x:", chartData.x, "y:", chartData.y);

  return (
    <div className="battery-chart-container" ref={chartRef}>
      <button className="fullscreen-button" onClick={toggleFullScreen}>
        {isFullScreen ? "Exit Full Screen" : "Maximize"}
      </button>
      <h3 className="chart-title">Battery Level Over Time</h3>
      <Plot
        data={[
          {
            x: chartData.x,
            y: chartData.y,
            type: "scatter",
            mode: "lines+markers",
            marker: { color: "blue" },
            hovertext: chartData.hover.map((text, idx) => {
              const serverTime = chartData.data[idx].server_time || "N/A";
              const localTime = chartData.data[idx].localTime || hoverLocalTime[serverTime] || "N/A";
              return `${text}<br>Local Time: ${localTime}`;
            }),
            hoverinfo: "text+x+y",
            customdata: chartData.data.map((item) => ({
              server_time: item.server_time || "N/A",
              google_account: item.google_account || item.googleAccount || "",
            })),
            hovertemplate: "%{hovertext}<extra></extra>",
          },
        ]}
        layout={{
          xaxis: {
            title: "Time (Local)",
            type: "date",
            tickformat: "%Y-%m-%d %H:%M:%S", // 24-hour format
            automargin: true,
          },
          yaxis: {
            title: "Battery Level (%)",
            range: [0, maxBattery + 10 > 100 ? 110 : 100],
            tick0: 0,
            dtick: 10,
          },
          showlegend: false,
          margin: { t: 50, b: 60, l: 50, r: 50 },
          autosize: true,
        }}
        style={{ width: "100%", height: isFullScreen ? "100vh" : "400px" }}
        config={{ responsive: true }}
        onHover={(data) => {
          const point = data.points[0];
          const { server_time, google_account } = point.customdata;
          if (!hoverLocalTime[server_time] && server_time !== "N/A") {
            fetchLocalTime(server_time, google_account, setHoverLocalTime);
          }
        }}
        onError={(err) => console.error("Plotly error:", err)}
      />
    </div>
  );
};

export default BatteryChart;