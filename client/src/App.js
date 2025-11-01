import React, { useEffect, useState } from "react";
import axios from "axios";
import { formatISO, parseISO } from "date-fns";

const BACKEND = process.env.REACT_APP_BACKEND || "http://localhost:8000";

function App() {
  const [phone, setPhone] = useState("");
  const [time, setTime] = useState(""); // local ISO string input
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchSchedules = async () => {
    try {
      const r = await axios.get(`${BACKEND}/schedules`);
      setSchedules(r.data.schedules || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchSchedules();
    // poll every 3s to refresh statuses
    const id = setInterval(fetchSchedules, 3000);
    return () => clearInterval(id);
  }, []);

  const schedule = async (now=false) => {
    if (!phone || phone.length < 10) {
      alert("Enter phone number (>=10 chars).");
      return;
    }
    setLoading(true);
    try {
      const payload = { phone_number: phone };
      if (!now && time) {
        // convert local datetime input to ISO in UTC
        const dt = new Date(time);
        payload.schedule_time = dt.toISOString();
      }
      const r = await axios.post(`${BACKEND}/schedule`, payload);
      console.log("scheduled", r.data);
      setPhone("");
      setTime("");
      fetchSchedules();
    } catch (e) {
      console.error(e);
      alert("Error scheduling. See console.");
    } finally {
      setLoading(false);
    }
  };

  const startNow = async (id) => {
    try {
      await axios.post(`${BACKEND}/schedules/${id}/start`);
      fetchSchedules();
    } catch (e) {
      console.error(e);
      alert("Error starting");
    }
  };

  const getStatus = (s) => {
    if (s.external_call_id) return s.last_status || "unknown";
    return s.started ? "initiated" : (s.schedule_time ? `scheduled (${s.schedule_time})` : "pending");
  };

  return (
    <div style={{ padding: 20, fontFamily: "Arial, sans-serif", maxWidth: 900, margin: "0 auto" }}>
      <h1>Call Scheduler</h1>

      <div style={{ border: "1px solid #ddd", padding: 12, borderRadius: 8, marginBottom: 20 }}>
        <h3>Schedule a call</h3>
        <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
          <input placeholder="+1234567890" value={phone} onChange={e => setPhone(e.target.value)} style={{ flex: 1 }} />
          <input type="datetime-local" value={time} onChange={e => setTime(e.target.value)} />
          <button onClick={() => schedule(true)} disabled={loading}>Start Now</button>
          <button onClick={() => schedule(false)} disabled={loading}>Schedule</button>
        </div>
        <div style={{ fontSize: 12, color: "#666" }}>
          If no date/time is provided, "Start Now" will initiate immediately.
        </div>
      </div>

      <h3>Scheduled Calls</h3>
      <table width="100%" style={{ borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>
            <th style={{ padding: 8 }}>Phone</th>
            <th>Schedule Time (UTC)</th>
            <th>Started</th>
            <th>External ID</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {schedules.map(s => (
            <tr key={s.id} style={{ borderBottom: "1px solid #f0f0f0" }}>
              <td style={{ padding: 8 }}>{s.phone_number}</td>
              <td>{s.schedule_time || "-"}</td>
              <td>{s.started ? "Yes" : "No"}</td>
              <td style={{ maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis" }}>{s.external_call_id || "-"}</td>
              <td>{getStatus(s)}</td>
              <td>
                <button onClick={() => startNow(s.id)} disabled={s.started}>Start Now</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div style={{ marginTop: 16, fontSize: 12, color: "#666" }}>
        Notes: The backend proxies external call status; the mock API will progress a call through initiated → ringing → connected → completed.
      </div>
    </div>
  );
}

export default App;
