import React, { useState, useEffect } from 'react';

const API_URL = "http://127.0.0.1:5000/view";

function App() {
  const [data, setData] = useState({ patients: [], alerts: [] });
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const response = await fetch(API_URL);
      const result = await response.json();
      setData(result);
      setLoading(false);
    } catch (err) {
      console.error("Fetch error:", err);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000); // Auto-refresh every 3s
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="text-center p-20">Initializing System...</div>;

  return (
    <div className="min-h-screen bg-slate-50 p-6 text-slate-800">
      <header className="flex justify-between items-center bg-white p-6 rounded-2xl shadow-sm mb-10">
        <h1 className="text-2xl font-black text-indigo-900 tracking-tight">ICU MULTI-AGENT VIRTUAL ASSISTANT</h1>
        <div className="flex items-center gap-2 text-green-600 font-bold">
          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
          LIVE FEED
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
        <div className="lg:col-span-2">
          <h2 className="text-lg font-bold mb-4">Bedside Monitors</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {data.patients.map((p) => (
              <div key={p.bed_id} className={`bg-white p-6 rounded-2xl shadow-lg border-t-4 ${p.status === 'Critical' ? 'border-red-500' : 'border-indigo-500'}`}>
                <div className="flex justify-between mb-4">
                  <span className="font-black text-xl">{p.bed_id}</span>
                  <span className={`text-xs font-bold px-3 py-1 rounded-full ${p.status === 'Critical' ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-600'}`}>
                    {p.status}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-slate-50 rounded-xl">
                    <p className="text-xs text-slate-400 uppercase">Heart Rate</p>
                    <p className={`text-3xl font-bold ${p.hr > 100 ? 'text-red-500' : 'text-slate-800'}`}>{p.hr}</p>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-xl">
                    <p className="text-xs text-slate-400 uppercase">Temperature</p>
                    <p className={`text-3xl font-bold ${p.temp > 38.0 ? 'text-red-500' : 'text-slate-800'}`}>{p.temp}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h2 className="text-lg font-bold mb-4">Agent Communication Log</h2>
          <div className="bg-slate-900 rounded-2xl p-4 h-[500px] overflow-y-auto shadow-2xl">
            {data.alerts.length === 0 ? (
              <p className="text-slate-500 text-center mt-10 italic">Scanning patient data...</p>
            ) : (
              data.alerts.map((alert) => (
                <div key={alert.id} className="mb-4 p-4 border-l-2 border-red-500 bg-slate-800 rounded-r-lg">
                  <p className="text-red-400 text-xs font-bold uppercase">{alert.bed_id}</p>
                  <p className="text-white text-sm mt-1">{alert.message}</p>
                  <p className="text-slate-500 text-[10px] mt-2">{alert.timestamp}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;