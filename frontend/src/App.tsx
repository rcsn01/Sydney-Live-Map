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
        <input type="range" min={0} max={23} value={snapshot ? new Date(snapshot).getUTCHours() : new Date().getUTCHours()} onChange={e => {
          const now = new Date();
          now.setUTCHours(parseInt(e.target.value), 0, 0, 0);
          setSnapshot(now.toISOString());
        }} />
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
