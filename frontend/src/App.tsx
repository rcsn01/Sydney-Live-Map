import React, { useEffect, useState } from 'react';
import { fetchLocations, fetchMetrics, fetchLocation } from './api';
import { LocationWithIntensity, MetricPoint, Location } from './types';
import MapView from './components/MapView';
import LocationDetails from './components/LocationDetails';

const App: React.FC = () => {
  const [locations, setLocations] = useState<LocationWithIntensity[]>([]);
  const [selectedId, setSelectedId] = useState<number | undefined>();
  const [metrics, setMetrics] = useState<MetricPoint[]>([]);
  const [selectedName, setSelectedName] = useState<string>('');
  const [snapshot, setSnapshot] = useState<string>('');
  const [snapshotOffset, setSnapshotOffset] = useState<number>(0); // hours ago

  // compute a Date for the current snapshot (or now) and a friendly UTC label
  const snapshotDate = snapshot ? new Date(snapshot) : new Date();
  const snapshotLabelHours = String(snapshotDate.getUTCHours()).padStart(2, '0');
  const snapshotLabelDate = snapshotDate.toISOString().slice(0, 10);
  const hAgo = snapshotOffset;
  const days = Math.floor(hAgo / 24);
  const hours = hAgo % 24;
  const agoLabel = hAgo === 0 ? 'now' : (days > 0 ? `${days}d ${hours}h ago` : `${hours}h ago`);
  const snapshotLabel = `${snapshotLabelHours}:00 UTC — ${snapshotLabelDate} (${agoLabel})`;

  // Load locations
  useEffect(() => {
    fetchLocations(snapshot).then(setLocations).catch(console.error);
    const interval = setInterval(() => fetchLocations(snapshot).then(setLocations).catch(console.error), 15000);
    return () => clearInterval(interval);
  }, [snapshot]);

  // Load metrics for selected
  useEffect(() => {
    if (selectedId != null) {
      fetchLocation(selectedId).then(l => setSelectedName(l.name));
      fetchMetrics(selectedId, 24).then(setMetrics);
    }
  }, [selectedId]);

  return (
    <div className="layout">
      <div className="sidebar">
        <h1>Sydney Live Map</h1>
        <label>Time (UTC Hour Offset)</label>
        <div className="time-row">
          <input type="range" min={0} max={168} value={snapshotOffset} onChange={e => {
            const offset = parseInt(e.target.value);
            setSnapshotOffset(offset);
            const now = Date.now();
            const snap = new Date(now - offset * 60 * 60 * 1000);
            setSnapshot(snap.toISOString());
          }} />
          <div className="time-display">{snapshotLabel}</div>
        </div>
        {/* moved chart: show recent metrics as bars under the UTC slider when a location is selected */}
        {selectedId != null && metrics.length > 0 && (
          <div className="chart" style={{ marginTop: 12 }}>
            {metrics.slice(-24).map(m => {
              const total = m.pedestrian_count + m.traffic_count;
              return (
                <div key={m.timestamp} className="bar" title={`${m.timestamp}\nPed: ${m.pedestrian_count} Traffic: ${m.traffic_count}`} 
                  style={{ height: Math.min(100, total / 30) + '%' }} />
              );
            })}
          </div>
        )}
        <div className="list">
          {locations.map(l => (
            <div key={l.id} className={`list-item ${l.id === selectedId ? 'active' : ''}`} onClick={() => setSelectedId(l.id)}>
              <span>{l.name}</span>
              <span className="pill">{(l.intensity * 100).toFixed(0)}%</span>
            </div>
          ))}
        </div>
        {selectedId && <LocationDetails name={selectedName} metrics={metrics} />}
      </div>
      <div className="map-container">
        <MapView locations={locations} onSelect={setSelectedId} selectedId={selectedId} />
      </div>
    </div>
  );
};

export default App;
